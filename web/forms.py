from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template.defaultfilters import filesizeformat
from django.contrib.auth.models import Group

from .models import Paste, File, Voucher

LIFETIMES = [(0, 'Never expires'),
             (1, 'Burn after reading'),
             (60, 'Expires after 1 minutes'),
             (600, 'Expires after 10 minutes'),
             (43200, 'Expires after 12 hours'),
             (604800, 'Expires after 1 week')]

MAX_UPLOAD_SIZE = 262144000 # 250 MB


class CreatePasteForm(forms.ModelForm):
    name = forms.CharField(label=_('Name (optional)'),
                           required=False)
    lifetime = forms.ChoiceField(choices=LIFETIMES,
                                 widget=forms.Select(),
                                 required=True)
    secure_url = forms.BooleanField(required=False,
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


class UploadFileForm(forms.ModelForm):
    name = forms.CharField(label=_('Name (optional)'),
                           required=False)
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
                                 required=True)
    secure_url = forms.BooleanField(required=False,
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
