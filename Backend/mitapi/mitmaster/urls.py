
from django.urls import path
from rest_framework import routers
from django.urls import include
from .views  import *
from .sn.snViews import *

router = routers.DefaultRouter()
router.register('client', mitClientViewSet, basename='client')
router.register('clientPage', mitClientPageViewSet, basename='clientpage')
router.register('masterValue', MasterValueViewSet, basename='mastervalue')
router.register('sn', structureNoteViewSet,basename='structure-note')



urlpatterns = [
    path('', include(router.urls)),
    
]
