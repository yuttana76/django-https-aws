
from django.urls import path
from rest_framework import routers
from django.urls import include
from .views import *

# router = routers.DefaultRouter()
# router.register('consents', CmpConsentViewSet)
# router.register('custResponse', CmpReponseViewSet)
# router.register('custRequest', CmpRequestViewSet)
# router.register('consentHisPage', consentHisPageViewSet)

# router.register('requestHisPage', requestHisPageViewSet)
# router.register('wealthHisPage', wealthHisPageViewSet)
# router.register('taxHisPage', taxHisPageViewSet)
# router.register('taxHisNoPage', taxHisNoPageViewSet)
# router.register('requestCFG', CmpRequestCFGViewSet)
# router.register('consentResp', CmpConsentRespViewSet)

router = routers.DefaultRouter()
router.register('consents', CmpConsentViewSet, basename='consents')
router.register('custResponse', CmpReponseViewSet, basename='custResponse')
router.register('custRequest', CmpRequestViewSet, basename='custRequest')
router.register('consentHisPage', consentHisPageViewSet, basename='consentHisPage')
router.register('requestHisPage', requestHisPageViewSet, basename='requestHisPage')
router.register('wealthHisPage', wealthHisPageViewSet, basename='wealthHisPage')
router.register('taxHisPage', taxHisPageViewSet, basename='taxHisPage')
router.register('taxHisNoPage', taxHisNoPageViewSet, basename='taxHisNoPage')
router.register('requestCFG', CmpRequestCFGViewSet, basename='requestCFG')
router.register('consentResp', CmpConsentRespViewSet, basename='consentResp')


urlpatterns = [
    path('', include(router.urls)),

]
