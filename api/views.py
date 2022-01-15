import logging

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.response import Response
from .serializers import PasteSerializer, FileSerializer, UploadSerializer
from django.contrib.auth.models import AnonymousUser

from web.models import KleberInput, Paste, File
from mal.shortcuts import remove_metadata, retrieve_metadata

LOGGER = logging.getLogger(__name__)


class PasteViewSet(viewsets.ModelViewSet):
    serializer_class = PasteSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (SessionAuthentication,
                              TokenAuthentication)

    def get_queryset(self):
        if self.request.user and \
                not isinstance(self.request.user, AnonymousUser):
            return Paste.objects.filter(owner=self.request.user)
        else:
            return Paste.objects.none()


class ApiFilePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.has_perm('web.add_file')


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = (IsAuthenticated,
                          ApiFilePermission)

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user,
                                   password__isnull=True)

    def perform_create(self, serializer):
        try:
            if not self.request.user.is_authenticated:
                return
            self.check_permissions(self.request)
            file = serializer.save()
            file.set_size()
            file.owner = self.request.user
            if not file.check_quota():
                return ValueError('No quota left')
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
            return Response(status=204)
        except Exception as e:
            LOGGER.exception(e)
            raise

    def retrieve(self, request, *args, **kwargs):
        try:
            shortcut = self.kwargs['pk']
            password = self.request.query_params.get('password', None)
            file = File.objects.filter(shortcut=shortcut).first()
            if not file:
                raise NotFound
            if file.password and file.password != password:
                raise AuthenticationFailed(detail='Invalid password')
            serializer = self.get_serializer(file)
            return Response(serializer.data)
        except Exception as e:
            LOGGER.exception(e)
            raise


class UploadViewSet(mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,
                          ApiFilePermission)

    def get_queryset(self):
        try:
            uploads = KleberInput.objects.filter(owner=self.request.user)
            _uploads = []
            for u in uploads:
                _uploads.append(u.cast())
            return _uploads
        except Exception as e:
            LOGGER.exception(e)
            raise

    def retrieve(self, request, *args, **kwargs):
        try:
            shortcut = self.kwargs['pk']
            password = self.request.query_params.get('password', None)
            upload = KleberInput.objects.filter(shortcut=shortcut).first()
            if not upload:
                raise NotFound
            if upload.is_file and upload.password and \
                    upload.password != password:
                raise AuthenticationFailed(detail='Invalid password')
            serializer = self.get_serializer(upload.cast())
            return Response(serializer.data)
        except Exception as e:
            LOGGER.exception(e)
            raise

    def destroy(self, request, *args, **kwargs):
        try:
            shortcut = self.kwargs['pk']
            upload = KleberInput.objects.filter(shortcut=shortcut).first()
            if not upload:
                raise NotFound
            upload.delete()
            return Response(status=204)
        except Exception as e:
            LOGGER.exception(e)
            raise
