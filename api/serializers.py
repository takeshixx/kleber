from django.utils import timezone
from rest_framework import serializers

from web.models import KleberInput, Paste, File

LIFETIMES = [(0, 'Never expires'),
             (1, 'Burn after reading'),
             (60, 'Expires after 1 minutes'),
             (600, 'Expires after 10 minutes'),
             (43200, 'Expires after 12 hours'),
             (604800, 'Expires after 1 week')]


class PasteSerializer(serializers.ModelSerializer):
    lifetime = serializers.ChoiceField(choices=LIFETIMES)

    class Meta:
        model = Paste
        fields = ('content',
                  'name',
                  'size',
                  'mimetype',
                  'mimetype_long',
                  'created',
                  'lifetime',
                  'shortcut',
                  'secure_shortcut',
                  'is_encrypted')
        read_only_fields = ('shortcut',
                            'size',
                            'mimetype',
                            'mimetype_long',
                            'created')

    def validate_lifetime(self, lifetime):
        try:
            lifetime = int(lifetime)
            if lifetime > 1:
                return timezone.now() + \
                       timezone.timedelta(0, lifetime)
        except ValueError:
            pass
        return None


class FileSerializer(serializers.ModelSerializer):
    lifetime = serializers.ChoiceField(choices=LIFETIMES)

    class Meta:
        model = File
        fields = ('uploaded_file',
                  'name',
                  'size',
                  'mimetype',
                  'mimetype_long',
                  'created',
                  'lifetime',
                  'shortcut',
                  'secure_shortcut',
                  'checksum',
                  'clean_checksum',
                  'metadata',
                  'password')
        read_only_fields = ('shortcut',
                            'size',
                            'mimetype',
                            'mimetype_long',
                            'created',
                            'checksum',
                            'clean_checksum',
                            'metadata')
        extra_kwargs = {'password': {'write_only': True},
                        'uploaded_file': {'write_only': True}}

    def validate_lifetime(self, lifetime):
        try:
            lifetime = int(lifetime)
            if lifetime > 1:
                return timezone.now() + \
                       timezone.timedelta(0, lifetime)
        except ValueError:
            pass
        return None


class UploadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = KleberInput
        fields = ('name',
                  'size',
                  'mimetype',
                  'mimetype_long',
                  'created',
                  'lifetime',
                  'shortcut',
                  'secure_shortcut',
                  'is_file')
