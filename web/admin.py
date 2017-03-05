from django.contrib import admin
from .models import Paste, File, Invite


admin.site.register(Paste)
admin.site.register(File)
admin.site.register(Invite)