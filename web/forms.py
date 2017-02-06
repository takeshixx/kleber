from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from .models import Paste, File

LIFETIMES = [(0, 'Never expires'),
             (1, 'Burn after reading'),
             (60, 'Expires after 1 minutes'),
             (600, 'Expires after 10 minutes'),
             (43200, 'Expires after 12 hours'),
             (604800, 'Expires after 1 week')]


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
