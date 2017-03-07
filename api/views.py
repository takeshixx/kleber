from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotFound, ValidationError
from rest_framework.response import Response
from .serializers import PasteSerializer, FileSerializer, UploadSerializer

from web.models import KleberInput, Paste, File
from mal.shortcuts import remove_metadata, retrieve_metadata


class PasteViewSet(viewsets.ModelViewSet):
    serializer_class = PasteSerializer
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)

    def get_queryset(self):
        return Paste.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        paste = serializer.save()
        paste.set_lifetime(serializer.data.get('lifetime'))
        if serializer.data.get('secure_shortcut') == 'on':
            paste.secure_shortcut = True
        if self.request.user.is_authenticated:
            paste.owner = self.request.user
            if not paste.check_quota():
                return ValueError('No quota left')
        paste.save()


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user,
                                   password__isnull=True)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            return
        self.check_permissions(self.request)
        file = serializer.save()
        file.owner = self.request.user
        if not file.check_quota():
            return ValueError('No quota left')
        file.set_lifetime(serializer.data.get('lifetime'))
        if serializer.data.get('secure_shortcut') == 'on':
            file.secure_shortcut = True
        if serializer.data.get('password'):
            file.password = serializer.data.get('password')
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

    def retrieve(self, request, *args, **kwargs):
        shortcut = self.kwargs['pk']
        password = self.request.query_params.get('password', None)
        file = File.objects.filter(shortcut=shortcut).first()
        if not file:
            raise NotFound
        if file.password and file.password != password:
            raise AuthenticationFailed(detail='Invalid password')
        serializer = self.get_serializer(file)
        return Response(serializer.data)


class UploadViewSet(mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = UploadSerializer

    def get_queryset(self):
        uploads = KleberInput.objects.filter(owner=self.request.user)
        _uploads = []
        for u in uploads:
            _uploads.append(u.cast())
        return _uploads

    def retrieve(self, request, *args, **kwargs):
        shortcut = self.kwargs['pk']
        password = self.request.query_params.get('password', None)
        upload = File.objects.filter(shortcut=shortcut).first()
        if not upload:
            raise NotFound
        if upload.is_file and upload.password and \
                upload.password != password:
            raise AuthenticationFailed(detail='Invalid password')
        serializer = self.get_serializer(upload.cast())
        return Response(serializer.data)
