from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

@admin.register(mit_cmp_consentmas)
class mit_cmp_consentmasAdmin(ImportExportModelAdmin):
    list_display = ('compCode','title', 'consStatus', 'description')
    list_filter = ('compCode',)
    ordering = ['compCode','seq' ]
    search_fields = ['compCode','title']

@admin.register(mit_cmp_Response)
class mit_cmp_ResponseAdmin(ImportExportModelAdmin):
    list_display = ('compCode', 'custCode', 'consent', 'respStatus','createDate','updateDate')
    list_filter = ('compCode','consent','respStatus')
    ordering = ['createDate', ]
    search_fields = ['custCode__cardNumber','custCode__thFirstName','custCode__thLastName']

@admin.register(mit_cmp_request)
class mit_cmp_requestAdmin(ImportExportModelAdmin):
    list_display = ('compCode','reqRef', 'custCode', 'reqCode', 'reqStatus','createDate')
    list_filter = ('compCode','reqCode','reqStatus')
    ordering = ['createDate', ]
    search_fields = ['reqRef','custCode__cardNumber','custCode__thFirstName','custCode__thLastName']


# # admin.site.register(mit_cmp_consentmas)
# # admin.site.register(mit_cmp_requestCFG)
# # admin.site.register(mit_cmp_Response)
# admin.site.register(mit_cmp_request)

# @admin.register(mit_cmp_consentmas, mit_cmp_requestCFG,mit_cmp_Response,mit_cmp_request)
# class ViewAdmin(ImportExportModelAdmin):
#   pass