from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def settings_value(name):
    return getattr(settings, name, '')

register.filter('settings_value', settings_value)
