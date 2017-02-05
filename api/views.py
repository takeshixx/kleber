from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import UserSerializer, GroupSerializer, PasteSerializer, FileSerializer, UploadSerializer

from web.models import KleberInput, Paste, File
from mal.shortcuts import remove_metadata, retrieve_metadata


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class PasteViewSet(viewsets.ModelViewSet):
    serializer_class = PasteSerializer

    def get_queryset(self):
        return Paste.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        paste = serializer.save()
        paste.set_lifetime(serializer.data.get('lifetime'))
        if serializer.data.get('secure_shortcut') == 'on':
            paste.secure_shortcut = True
        if self.request.user.is_authenticated:
            paste.owner = self.request.user
        paste.save()


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            return
        file = serializer.save()
        file.set_lifetime(serializer.data.get('lifetime'))
        if serializer.data.get('secure_shortcut') == 'on':
            file.secure_shortcut = True
        file.owner = self.request.user
        file.checksum = file.calc_checksum_from_file()
        remove_meta = serializer.data.get('remove_meta')
        try:
            remove_meta = int(remove_meta)
        except (ValueError, TypeError):
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


class UploadViewSet(viewsets.ModelViewSet):
    serializer_class = UploadSerializer

    def get_queryset(self):
        return KleberInput.objects.filter(owner=self.request.user)
