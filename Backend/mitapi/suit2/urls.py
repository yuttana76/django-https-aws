
from django.urls import path
from rest_framework import routers
from django.urls import include
from .views import *

router = routers.DefaultRouter()
router.register('suit', suitViewSet, basename='suit')
router.register('suitlist', suitListViewSet, basename='suitlist')
router.register('suitExpire', suitExpireViewSet, basename='suitexpire')

urlpatterns = [
    path('', include(router.urls)),
]
