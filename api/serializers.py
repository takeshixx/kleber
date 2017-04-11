import logging

from django.utils import timezone
from rest_framework import serializers
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from web.models import KleberInput, Paste, File

LOGGER = logging.getLogger(__name__)

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
        try:
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
        except Exception as e:
            LOGGER.exception(e)

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
        try:
            file = File(**validated_data)
            path = default_storage.save(settings.UPLOAD_PATH,
                                        ContentFile(validated_data.get('uploaded_file').read()))
            file.uploaded_file = path
            file.name = validated_data.get('name') or validated_data.get('uploaded_file').name
            file.set_lifetime(validated_data.get('lifetime'))
            if validated_data.get('secure_shortcut') == 'on':
                file.secure_shortcut = True
            file.set_shortcut()
            return file
        except Exception as e:
            LOGGER.exception(e)
            raise

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
