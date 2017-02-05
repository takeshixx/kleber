from django import template

register = template.Library()

def print_unit(size):
    kib = 1024
    mib = kib * kib
    gib = kib * mib
    if size > gib:
        return '{} GiB'.format(round(size / gib, 2))
    elif size > mib:
        return '{} MiB'.format(round(size / mib, 2))
    elif size > kib:
        return '{} KiB'.format(round(size / kib, 2))
    elif size < 1024:
        return '{} B'.format(round(size, 2))

register.filter('print_unit', print_unit)
