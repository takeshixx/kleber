from .core import MetaDataInterface

def remove_metadata(file_path,):
    meta = MetaDataInterface(file_path)
    status, message = meta.remove_metadata()
    if status:
        return True, 'Metadata successfully removed'
    else:
        if message == 'Unchanged':
            return True, 'No metadata found, file unchanged'
        if 'Unknown file type' in message:
            return False, 'File type not supported'
        return False, 'File unchanged'


def retrieve_metadata(file_path):
    meta = MetaDataInterface(file_path)
    return meta.get_metadata()
