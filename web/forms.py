from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template.defaultfilters import filesizeformat
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import Paste, File, Voucher
from mal.shortcuts import remove_metadata, retrieve_metadata

LIFETIMES = [(0, 'Never expires'),
             (1, 'Burn after reading'),
             (60, 'Expires after 1 minutes'),
             (600, 'Expires after 10 minutes'),
             (43200, 'Expires after 12 hours'),
             (604800, 'Expires after 1 week')]

MAX_UPLOAD_SIZE = 262144000 # 250 MB


class CreatePasteForm(forms.ModelForm):
    name = forms.CharField(label=_('Name (optional)'),
                           required=False,
                           help_text=_('Choosing a proper file extension for a paste name allows '
                                       'to influence syntax highlighting (e.g. use \'test.py\' '
                                       'to use syntax highlighting for Python snippets).'))
    lifetime = forms.ChoiceField(choices=LIFETIMES,
                                 widget=forms.Select(),
                                 required=True,
                                 help_text='Pastes will be deleted after 10 days automatically unless they are smaller than 1 MB.')
    secure_shortcut = forms.BooleanField(required=False,
                                    label=_('Generate a long shortcut'),
                                    help_text=_('Longer shortcuts will be harder to guess. So with '
                                                'this option it will be harder to find this upload '
                                                'by guessing URLs.'))
    is_encrypted = forms.BooleanField(required=False,
                                      label=_('Encrypt paste'),
                                      help_text=_('The content of pastes will be encrypted in on '
                                                  'the client side. The key will only be available '
                                                  'in the URL and will never be sent to the server. '
                                                  'Make sure to copy the link with the key or else '
                                                  'the content will not be accessible in clear!'))

    class Meta:
        model = Paste
        fields = ['content',
                  'name',
                  'lifetime']

    def clean_lifetime(self):
        try:
            lifetime = int(self.cleaned_data['lifetime'])
            if lifetime > 1:
                return timezone.now() + \
                       timezone.timedelta(0, lifetime)
        except ValueError:
            pass
        return None

    def save(self, commit=True, request=None, *args, **kwargs):
        password = self.cleaned_data.get('password')
        paste = Paste()
        paste.content = self.cleaned_data['content']
        paste.set_size()
        if request.user.is_authenticated:
            paste.owner = request.user
            if not paste.check_quota():
                self.add_error('content', 'No quota left')
        paste.name = self.cleaned_data['name']
        paste.set_mimetype()
        paste.set_lexer()
        paste.set_lifetime(self.cleaned_data['lifetime'])
        if self.cleaned_data['secure_shortcut']:
            paste.secure_shortcut = True
        paste.set_shortcut()
        if password:
            paste.set_password(password)
        paste.save()
        return paste


class UploadFileForm(forms.ModelForm):
    name = forms.CharField(label=_('Name (optional)'),
                           required=False,
                           help_text=_('Choosing a proper file extension for a file name allows '
                                       'to influence syntax highlighting (e.g. use \'test.py\' '
                                       'to use syntax highlighting for Python files).'))
    remove_meta = forms.ChoiceField(choices=[(2, 'Remove metadata'),
                                             (1, 'Do not remove metadata'),
                                             (0, 'Do not touch this file')],
                                    label=_('What to do with the metadata?'),
                                    help_text=_('Controls what should be done with metadata in '
                                                'uploaded files.'),
                                    widget=forms.Select(),
                                    required=True)
    lifetime = forms.ChoiceField(choices=LIFETIMES,
                                 widget=forms.Select(),
                                 required=True,
                                 help_text='Pastes over 1MB in size will be automatically deleted after 10 days.')
    secure_shortcut = forms.BooleanField(required=False,
                                    label=_('Generate a long shortcut'),
                                    help_text=_('Longer shortcuts will be harder to guess. So with '
                                                'this option it will be harder to find this upload '
                                                'by guessing URLs.'))
    password_protect = forms.BooleanField(required=False,
                                          label=_('Password protect'),
                                          help_text=_('Password protected uploads will only be accessible '
                                                      'for users that have access to the password.'),
                                          widget=forms.CheckboxInput(attrs={'onclick': 'return protect()'}))
    password = forms.CharField(required=False,
                               label='',
                               max_length=50,
                               widget=forms.TextInput(attrs={'class': 'hidden'}))

    class Meta:
        model = File
        fields = ['uploaded_file',
                  'name',
                  'lifetime']

    def clean_lifetime(self):
        try:
            lifetime = int(self.cleaned_data['lifetime'])
            if lifetime > 1:
                return timezone.now() + \
                       timezone.timedelta(0, lifetime)
        except ValueError:
            pass
        return None

    def clean_uploaded_file(self):
        if self.cleaned_data['uploaded_file'].size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(_('File uploads must be %s or less.' %
                                          filesizeformat(MAX_UPLOAD_SIZE)))
        return self.cleaned_data['uploaded_file']

    def save(self, commit=True, request=None, *args, **kwargs):
        password = self.cleaned_data['password']
        file = File()
        path = default_storage.save(settings.UPLOAD_PATH,
                                    ContentFile(self.cleaned_data['uploaded_file'].read()))
        file.uploaded_file = path
        file.name = self.cleaned_data['name'] or self.cleaned_data['uploaded_file'].name
        file.set_size()
        file.owner = request.user
        if not file.check_quota():
            self.add_error('uploaded_file', 'No quota left')
        file.set_mimetype()
        file.set_lexer()
        file.set_lifetime(self.cleaned_data['lifetime'])
        if self.cleaned_data['secure_shortcut']:
            file.secure_shortcut = True
        file.set_shortcut()
        if password:
            file.set_password(password)
        file.checksum = file.calc_checksum_from_file()
        remove_meta = self.cleaned_data['remove_meta']
        try:
            remove_meta = int(remove_meta)
        except ValueError:
            remove_meta = 0
        if remove_meta and remove_meta > 1:
            meta_status, meta_message = remove_metadata(file.uploaded_file.url)
            file.remove_meta = meta_status
            file.remove_meta_message = meta_message
            if meta_status:
                file.clean_checksum = file.calc_checksum_from_file()
        elif remove_meta == 1:
            file.store_metadata_dict(
                retrieve_metadata(file.uploaded_file.url))
            file.remove_meta = False
            file.remove_meta_message = 'Metadata stored, but not removed'
        file.save()
        return file


class SignupForm(forms.Form):
    username = forms.CharField(max_length=30,
                               label='Username')
    email = forms.EmailField(label='Email Address')
    voucher_code = forms.CharField(max_length=32,
                                   label='Voucher',
                                   required=False)

    def clean_voucher_code(self):
        code = self.cleaned_data['voucher_code']
        voucher = Voucher.objects.filter(code=code).first()
        if voucher:
            return code
        else:
            return None

    def signup(self, request, user):
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        user.save()
        voucher_code = self.cleaned_data['voucher_code']
        if voucher_code:
            voucher = Voucher.objects.filter(code=voucher_code,
                                            used=False).first()
            if voucher and isinstance(voucher, Voucher):
                group = Group.objects.get(name='Can upload files')
                group.user_set.add(user)
                voucher.receiver = user
                voucher.used = True
                voucher.save()
