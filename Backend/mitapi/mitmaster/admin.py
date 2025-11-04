from django.contrib import admin

from .models import *
from import_export.admin import ImportExportModelAdmin

# admin.site.register(mit_client)
# admin.site.register(mit_master_value)

# class mit_clientAdmin(admin.ModelAdmin):
@admin.register(mit_client)
class mit_clientAdmin(ImportExportModelAdmin):
    list_display = ('compCode','cardNumber', 'thFirstName','thLastName', 'email','phone')
    list_filter = ('compCode',)
    ordering = ['enFirstName', 'thFirstName']
    search_fields = ['cardNumber', 'thFirstName', 'thLastName', 'email','phone']

# class mit_master_valueAdmin(admin.ModelAdmin):
@admin.register(mit_master_value)
class mit_master_valueAdmin(ImportExportModelAdmin):
    list_display = ('compCode','refType', 'refCode','status','seq', 'nameTh', 'nameEn')
    list_filter = ('compCode','refType')
    ordering = ['compCode','refType', 'seq']
    search_fields = ['refType','refCode', 'nameTh', 'nameEn']


# @admin.register(mit_master_value,mit_client)
# @admin.register(mit_master_value)
# class ViewAdmin(ImportExportModelAdmin):
#   pass