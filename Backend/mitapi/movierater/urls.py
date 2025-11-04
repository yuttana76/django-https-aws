
from django.contrib import admin
from django.urls import path
from django.urls import include
from rest_framework.authtoken.views import obtain_auth_token

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('api.urls')),
    path('cmp/', include('cmpapi.urls')),
    path('mit/', include('mitmaster.urls')),
    path('suitability/', include('suit2.urls')),
    path('auth/', obtain_auth_token),
    # JWT Authentication (MARZ)
    path('api/', include('base.urls')),
]