import os
import magic

from . import exceptions
from . import mimetypes
from . import exiftool


class MetaDataInterface(object):
    READABLE = False
    METADATA = False

    def __init__(self, file):
        self.input_file_name = file
        self.READABLE = self._is_file_readable()

    def __str__(self):
        return self.input_file_name

    def _is_file_readable(self):
        return os.path.isfile(self.input_file_name) and os.access(self.input_file_name, os.R_OK)

    def _determine_mimetype(self):
        try:
            self.mime_type = magic.from_file(self.input_file_name, mime=True)
            (self.mime_type_minor, self.mime_type_major) = self.mime_type.split('/')
        except Exception as e:
            self.mime_type = 'data'

    def _determine_mimetype_long(self):
        try:
            self.mime_type_long = magic.from_file(self.input_file_name)
        except Exception as e:
            self.mime_type_long = self.mime_type

    def _is_file_supported(self):
        return self.mime_type in mimetypes.SUPPORTED_MIMETYPES

    @staticmethod
    def _canonicalize_metadata(metadata):
        for key in list(metadata):
            if 'File' in key:
                del metadata[key]
                continue
            elif 'SourceFile' in key:
                del metadata[key]
                continue
            elif 'ExifTool' in key:
                del metadata[key]
                continue
            try:
                if 'option to extract' in metadata[key]:
                    del metadata[key]
                    continue
            except:
                continue
            try:
                _key = key.split(':')
                _key.pop(0)
                metadata[''.join(_key)] = metadata[key]
                del metadata[key]
            except:
                pass
        return metadata

    def get_metadata(self):
        if not self.READABLE:
            return False

        with exiftool.ExifTool() as et:
            output = et.get_metadata(self.input_file_name)

        if 'Error' in output:
            return False
        else:
            self.METADATA = self._canonicalize_metadata(output)
            return self.METADATA

    def remove_metadata(self):
        if not self.READABLE:
            return False, ''

        with exiftool.ExifTool() as et:
            output = et.remove_metadata(self.input_file_name)

        print(output)

        if b'nknown file type' in output or \
                b'not supported' in output or \
                b'files weren\'t updated due to errors' in output:
            return False, 'Unknown file type'
        elif b'files unchanged' in output or \
                b'0 image files updated' in output:
            return False, 'Unchanged'
        elif b' files updated' in output and not \
                b'image files unchanged' in output:
            return True, 'Success'
        else:
            return False, 'Unknown'
