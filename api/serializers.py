from django.contrib.auth.models import User, Group
from django.utils import timezone
from rest_framework import serializers

from web.models import KleberInput, Paste, File

LIFETIMES = [(0, 'Never expires'),
             (1, 'Burn after reading'),
             (60, 'Expires after 1 minutes'),
             (600, 'Expires after 10 minutes'),
             (43200, 'Expires after 12 hours'),
             (604800, 'Expires after 1 week')]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url',
                  'username',
                  'email',
                  'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url',
                  'name')


class PasteSerializer(serializers.HyperlinkedModelSerializer):
    shortcut = serializers.ReadOnlyField()
    size = serializers.ReadOnlyField()
    mimetype = serializers.ReadOnlyField()
    mimetype_long = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
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

    def validate_lifetime(self, lifetime):
        try:
            lifetime = int(lifetime)
            if lifetime > 1:
                return timezone.now() + \
                       timezone.timedelta(0, lifetime)
        except ValueError:
            pass
        return None


class FileSerializer(serializers.HyperlinkedModelSerializer):
    shortcut = serializers.ReadOnlyField()
    size = serializers.ReadOnlyField()
    mimetype = serializers.ReadOnlyField()
    mimetype_long = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    checksum = serializers.ReadOnlyField()
    clean_checmsum = serializers.ReadOnlyField()
    metadata = serializers.ReadOnlyField()
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
                  'metadata')

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
        fields = ('shortcut',
                  'name',
                  'lifetime',
                  'is_file')
