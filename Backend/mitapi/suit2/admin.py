from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# Register your models here.
# admin.site.register(suitability)

@admin.register(suitability)
class suitabilityAdmin(ImportExportModelAdmin):
    list_display = ('compCode','cardNumber','custType', 'docVersion','status', 'score','suitLevel','evaluateDate','createDT')
    list_filter = ('status',)
    ordering = ['createDT']
    search_fields = ['cardNumber']
