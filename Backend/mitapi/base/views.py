from django.contrib.auth.models import User
from mitmaster.views import generateKey
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from rest_framework.views import APIView
from rest_framework import status

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import login, get_user_model

import pyotp
import base64
from django.utils import timezone
from django.conf import settings
from .models import Note
from mitmaster.models import mit_client
from mitmaster.serializers import MitClientTokenSerializer

from movierater.utils import smsGateWay

from .serializers import NoteSerializer

import datetime

@api_view(['GET'])
@permission_classes([])
def testApi(request):
    print("*** testApi")
    return Response({'connect api ': True})


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            print("***CustomTokenObtainPairView called")
            print("***",request.data)

            response = super().post(request, *args, **kwargs)

            tokens = response.data

            access_token = tokens['access']
            refresh_token = tokens['refresh']

            # seriliazer = UserSerializer(request.user, many=False)

            res = Response()

            res.data = {'success':True}

            res.set_cookie(
                key='access_token',
                value=str(access_token),
                httponly=True,
                secure=True,
                samesite='None',
                path='/'
            )

            res.set_cookie(
                key='refresh_token',
                value=str(refresh_token),
                httponly=True,
                secure=True,
                samesite='None',
                path='/'
            )

            res.data.update(tokens)

            return res
        
        except Exception as e:
            print(e)
            return Response({'success':False})
        
        
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            print("***CustomTokenRefreshView called")
            print("***",request.data)

            refresh_token = request.COOKIES.get('refresh_token')

            request.data['refresh'] = refresh_token

            response = super().post(request, *args, **kwargs)
            
            tokens = response.data
            access_token = tokens['access']

            res = Response()

            res.data = {'refreshed': True}

            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite='None',
                path='/'
            )
            return res

        except Exception as e:
            print(e)
            return Response({'refreshed': False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):

    try:

        res = Response()
        res.data = {'success':True}
        res.delete_cookie('access_token', path='/', samesite='None')
        res.delete_cookie('refresh_token', path='/', samesite='None')

        return res

    except Exception as e:
        print(e)
        return Response({'success':False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def is_authenticated(request):
    print("***is_authenticated called")
    print("*** user:", request.user)
    return Response({'authenticated': True})
            
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notes(request):
    print("***get_notes called")
    print("*** user:", request.user)

    user = request.user
    notes = Note.objects.filter(owner=user)
    # notes = user.note.all()
    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)


# class ClientOTPView(APIView):
class ClientOTPView(TokenObtainPairView):
    permission_classes = [AllowAny]
 
    def post(self, request, *args, **kwargs):

        phone = request.data.get('mobile')
        cid = request.data.get('cid')
        compcode = request.data.get('compcode')

        print("***ClientOTPView called", request.data)        
        try:
            client = mit_client.objects.get(phone=phone, cardNumber=cid , compCode__iexact=compcode)
            print(f" *** Client {client}")

            # user = client.user# Update client with OTP details
            # print(f" *** User {user}")
            # if not user:
            #     return Response("User not found for this client", status=status.HTTP_404_NOT_FOUND)
            
            
            # Check for max OTP attempts
            if int(client.max_otp_try) == 0 and client.otp_max_out and (timezone.now() < client.otp_max_out):
                print( f"OTP Maximum request is TRUE ")
                _tryagain = client.otp_max_out - timezone.now()
                tryagain_min = int(_tryagain.total_seconds()  / 60) + 1
                return Response({'success':False, 
                                 'msg':f'Max OTP try reached, try after an hour. {tryagain_min} min. '}
                    ,status=status.HTTP_400_BAD_REQUEST,)
            
            # Generate OTP & OTP Reference
            OTP_LIFE_MIN=10  # OTP life in 10 minutes
            MAX_OTP_TRY=3

            keygen = generateKey()
            OTP_Ref = keygen.generate_ref()
            
            key = base64.b32encode(keygen.generateOTP(client.phone, OTP_Ref).encode())  # Key is generated
            OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
            OTP_Code = OTP.at(6)  # OTP Code length 6 digit
            OTP_expiry = timezone.now() + datetime.timedelta(minutes=OTP_LIFE_MIN)
            max_otp_try = int(client.max_otp_try) - 1
            
            client.otp = OTP_Code
            client.otp_ref = OTP_Ref
            client.otp_expiry = OTP_expiry
            client.max_otp_try = max_otp_try

            if max_otp_try == 0:
                client.otp_max_out = timezone.now() + datetime.timedelta(hours=1)
            elif max_otp_try == -1:
                client.max_otp_try = MAX_OTP_TRY
            else:
                client.otp_max_out = None
                client.max_otp_try = max_otp_try

            client.save()

            # Send OTP message to mobile
            try:
                msg = f'{client.otp} is your OTP for Login with ref {client.otp_ref}, This OTP is valid for {OTP_LIFE_MIN} minutes' 
                
                if(not settings.PROD):
                    msg = '[Develop]  ' + msg

                print('MSG>>'+msg)

                if(settings.SEND_SMS):
                    sms = smsGateWay(client.phone, msg)
                    smsRs = sms.MpamSmsGW()
                
            except Exception as e:
                print(e)
                raise

            return  Response({'success':True,'otpref': {client.otp_ref},}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'success':False, 'msg':'Not found data. Please try again'}, status=status.HTTP_400_BAD_REQUEST)




class VerifyOTPView(TokenObtainPairView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):


        otp = request.data['otp']
        otpref = request.data['otpref']
        compcode = request.data['compcode']

        print("***VerifyOTPView called",request.data)
        if not otp or not otpref:
            return Response({'success':False, 'msg':"Please enter the OTP and OTP Reference"}, status=status.HTTP_400_BAD_REQUEST)

        if type(otpref) is not str:
            try:
                otpref = otpref[0]
            except Exception as e:
                otpref = str(otpref)
                print(f"To convert OTP reference to string: {e}")

        print(f"OTP: {otp}, OTP Reference: {otpref}, CompCode: {compcode}")

        try:

            client = mit_client.objects.get(otp=otp, otp_ref=otpref,compCode__iexact=compcode)
            serializer = MitClientTokenSerializer(client, many=False)

            if client:

                if not client.user:
                    User = get_user_model()

                    # Create a new user
                    username = client.cardNumber  # or any unique identifier
                    email = client.email if client.email else f"{client.cardNumber}@xxx.com"
                    password = "strongpassword123"

                    try:
                        _user = User.objects.create_user(username, email, password)
                        _user.first_name = client.thFirstName if client.thFirstName else client.enFirstName 
                        _user.last_name = client.thLastName if client.thLastName else client.enLastName
                        _user.save() # Remember to save if you modify attributes after creation

                        client.user = _user
                    except Exception as e:
                        print(f"Error creating user: {e}")

                # Authenticate user
                login(request, client.user)

                refresh = RefreshToken.for_user(client.user)

                client.otp = None
                client.otp_ref = None
                client.otp_expiry = None
                client.max_otp_try = 3
                client.otp_max_out = None
                client.save()


                info = {
                        'refresh_token': str(refresh),
                        'access_token': str(refresh.access_token),
                        'userId': client.id, 
                        'Name': client.enFirstName +' ' + client.enLastName,
                        # 'cardNumber':client.cardNumber, 
                        # 'VerifyDT': datetime.now()
                        }

                res = Response()
                res.data = {'success':True}
                res.set_cookie(
                    key='access_token',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    path='/'
                )

                res.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    path='/'
                )

                res.data.update(info)

                return res
            else:
                return Response({'success':False, 'msg':"Please enter the correct OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
        except ObjectDoesNotExist:
            return Response({'success':False, 'msg':"Please enter the correct OTP"}, status=status.HTTP_400_BAD_REQUEST)