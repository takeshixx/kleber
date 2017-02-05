from django import template

register = template.Library()

def print_metadata(metadata):
    if not metadata:
        return
    _metadata = {}
    for line in metadata.split('\n'):
        try:
            meta, data = line.split(':\t')
        except ValueError:
            continue
        _metadata[meta] = data
    return _metadata

register.filter('print_metadata', print_metadata)
