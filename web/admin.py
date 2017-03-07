from django.contrib import admin
from .models import Paste, File, Voucher


admin.site.register(Paste)
admin.site.register(File)
admin.site.register(Voucher)