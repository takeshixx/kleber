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

    def create(self, validated_data):
        paste = Paste(**validated_data)
        paste.set_lifetime(validated_data.get('lifetime'))
        if validated_data.get('secure_shortcut') == 'on':
            paste.secure_shortcut = True
        paste.set_shortcut()
        paste.set_size()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if request.user.is_authenticated:
                paste.owner = request.user
                if not paste.check_quota():
                    return ValueError('No quota left')
        paste.save()
        return paste

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

    def create(self, validated_data):
        file = File(**validated_data)
        file.set_lifetime(validated_data.get('lifetime'))
        if validated_data.get('secure_shortcut') == 'on':
            file.secure_shortcut = True
        file.set_shortcut()
        return file

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
