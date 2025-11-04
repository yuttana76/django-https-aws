from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path
from .views import get_notes,CustomTokenObtainPairView ,CustomTokenRefreshView,testApi,logout,is_authenticated,ClientOTPView,VerifyOTPView

# from mitmaster.views import get_clientinfo
from mitmaster.viewToken import cmpSubjectRequest,get_clientinfo,submitrequest,gettaxlatest,getPFreportsbycid,downloadPFreport,getShowPortReports
from cmpapi.viewsToken import getconsent

from suit2.viewsToken import get_suit,createSuit

urlpatterns = [
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('testapi/', testApi, name='testapi'),

    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout, name='logout'),
    path('authenticated/', is_authenticated, name='is_authenticated'),
    path('notes/', get_notes, name='get_notes'),
    path('clientlogin/', ClientOTPView.as_view(), name='api_clientotp'),
    path('verifyotp/', VerifyOTPView.as_view(), name='api_verifyotp'),

    path('clientinfo/', get_clientinfo, name='api_get_clientinfo'),
    path('tk_cmpSubjectRequest/', cmpSubjectRequest, name='tk_cmpSubjectRequest'),

    path('tk_getconsent/', getconsent, name='tk_getconsent'),
    path('tk_getconsent/', getconsent, name='tk_getconsent'),
    path('tk_submitrequest/', submitrequest, name='tk_submitrequest'),
    path('tk_gettaxlatest/', gettaxlatest, name='tk_gettaxlatest'),

    path('tk_getPFreportsbycid/', getPFreportsbycid, name='tk_getPFreportsbycid'),
    path('tk_downloadPFreport/', downloadPFreport, name='tk_downloadPFreport'),

    path('tk_getShowPortReports/', getShowPortReports, name='tk_getShowPortReports'),

    path('tk_get_suit/', get_suit, name='tk_get_suit'),
    path('tk_createSuit/', createSuit, name='tk_get_suit'),
]