from datetime import datetime
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.core.exceptions import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse


from rest_framework.decorators import api_view, permission_classes

# from django.utils import timezone
import datetime
import pytz

from django.conf import settings

import pyotp
import json

from rest_framework import viewsets, status, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.authentication import JWTAuthentication


from django_filters.rest_framework import DjangoFilterBackend

import base64
from random import choice
import requests

from .models import *
from .serializers import *
from cmpapi.views import CmpConsentViewSet
from movierater.utils import smsGateWay
from movierater.utils import DirectoryClient
from movierater.utils import *

from .paginations import CustomPagination

import sys
try:

    CONNECTION_STRING = settings.AZURE_CONTAINER_CONNECTION_STRING
except KeyError:
    print('AZURE_STORAGE_CONNECTION_STRING must be set')
    sys.exit(1)

try:

    CONTAINER_NAME = settings.AZURE_CONTAINER_NAME
except IndexError:
    print('usage: directory_interface.py CONTAINER_NAME')
    print('error: the following arguments are required: CONTAINER_NAME')
    sys.exit(1)

# This class returns the string needed to generate the key
class generateKey:
    @staticmethod
    def generateOTP(phone, refCode):
        return str(phone) + refCode

    def generate_ref(self):
        # Generate 6 Digit verification code , Prevent cracking
        # :return:
        seeds = "1234567890abcdefghijklmnopqrstuvwxyz"
        random_str = []
        for i in range(6):
            random_str.append(choice(seeds))
        return "".join(random_str)


class mitClientPageViewSet(viewsets.ModelViewSet):
    queryset = mit_client.objects.all()
    serializer_class = MitClientSerializerShort

    # search_fields = ['cardNumber', 'thFirstName', 'thLastName']
    # filter_backends = [filters.SearchFilter]

    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # def get_object(self):
    #     return get_object_or_404(mit_client, id=self.request.query_params.get("id"))

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode

        for key, value in self.request.query_params.items():
            if value != '':
                if key == 'cardNumber':
                    filters['cardNumber'] = value
                elif key == 'thFirstName':
                    filters['thFirstName__contains'] = value
                elif key == 'thLastName':
                    filters['thLastName__contains'] = value

        print(filters)
        return mit_client.objects.filter(**filters).order_by('-createDate')


class mitClientViewSet(viewsets.ModelViewSet):
    queryset = mit_client.objects.all().order_by('-createDate')
    serializer_class = MitClientSerializerShort
    # serializer_class = MitClientSerializer
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # def get_queryset(self):

    #     queryset = mit_client.objects.all().order_by('-createDate')

    #     compCode = self.request.query_params.get('compCode')
    #     if compCode is not None:
    #         queryset = queryset.filter(compCode__iexact=compCode)

    #     return mit_client.objects.filter(compCode__iexact=compCode).order_by('-createDate')

    @action(detail=True, methods=['POST'])
    def resentConsentMail(self, request, pk=None):
        # compCode = request.data['compCode']
        # custId = request.data['custId']
        try:
            # custObject = mit_client.objects.get(
            #     compCode__iexact=compCode, id=custId)
            client = mit_client.objects.get(id=pk)
            utils.sendMail_ConsentRepose(client.compCode, client)

            response = {'code': '000', 'message': 'Succesful '}
            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            response = {'code': '001', 'message': 'Client Not Found'}
            return Response(response, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['POST'])
    def cidmobOtp(self, request, pk=None):
        print(request.data)
        if 'compcode' in request.data and 'cid' in request.data and 'mobile' in request.data:
            compcode = request.data['compcode']
            cid = request.data['cid']
            mobile = request.data['mobile']

            try:
                clientObject = mit_client.objects.get(
                    compCode__iexact=compcode, cardNumber__exact=cid, phone__exact=mobile)

                # Generate OTP & OTP Reference
                keygen = generateKey()
                otpRef = keygen.generate_ref()
                key = base64.b32encode(keygen.generateOTP(
                    clientObject.phone, otpRef).encode())  # Key is generated
                OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                otpCode = OTP.at(6)
                otp_alive = 5

                # Send SMS
                try:
                    # print('DEBUG>>',settings.DEBUG)
                    msg = '%s is your OTP for Login with ref %s, This OTP is valid for %s minutes' % (
                        otpCode, otpRef, otp_alive)

                    if(not settings.PROD):
                        msg = '[Develop]' + msg

                    print('!%s'%(otpCode))
                    sms = smsGateWay(mobile, msg)
                    smsRs = sms.MpamSmsGW()
                    
                except Exception as e:
                    print(e)
                    raise

                # Save to db.
                # now = timezone.now()
                now = datetime.now()

                # now = timezone.localtime()

                clientObject.otpExpire = now + timedelta(minutes=otp_alive)
                print(clientObject.otpExpire)
                clientObject.otpRef = otpRef
                clientObject.otpCode = otpCode
                clientObject.otpCounter += 1  # Update Counter At every Call
                clientObject.save()  # Save the data

                response = {'otp': otpCode,
                            'otpref': otpRef, 'otpAlive': otp_alive}
                return Response(response, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)

        else:
            response = {'message': 'You need to provide response data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def cidmobOtpVerify(self, request, pk=None):

        if 'compcode' in request.data and 'cid' in request.data and 'mobile' in request.data and 'otp' in request.data and 'otpref' in request.data:
            compcode = request.data['compcode']
            cid = request.data['cid']
            mobile = request.data['mobile']
            otp = request.data['otp']
            otpref = request.data['otpref']
            try:

                clientObject = mit_client.objects.get(
                    compCode__iexact=compcode, cardNumber__exact=cid, phone__exact=mobile)
                # now = timezone.now()
                utc = pytz.UTC

                now = datetime.now().replace(tzinfo=utc)
                otpExpire = clientObject.otpExpire.replace(tzinfo=utc)

                # if now > clientObject.otpExpire:
                if now > otpExpire:
                    response = {'code': '002', 'message': 'OTP Expired'}
                    return Response(response, status=status.HTTP_202_ACCEPTED)

                if clientObject.otpCode != otp or clientObject.otpRef != otpref:
                    response = {'code': '003', 'message': 'OTP Incorrect'}
                    return Response(response, status=status.HTTP_202_ACCEPTED)

                clientObject.otpMethod = mobile
                clientObject.otpIsVerified = True
                clientObject.otpIsVerifiedDT = datetime.now()
                clientObject.otpCounter = 0
                clientObject.save()
                # Save

                response = {'userId': clientObject.id, 'Name': clientObject.enFirstName +
                            ' ' + clientObject.enLastName,'cardNumber':clientObject.cardNumber, 'VerifyDT': datetime.now()}
                return Response(response, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)

        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # (Develop) Update consent cross company
    # 1. check client exist ?
    # 2. update consent
    # 3. create request, status = finish , has memo from cross company
    # 4. send mail to DPO/OP.
    @action(detail=False, methods=['POST'])
    def consentCrossCompReceiver(self, request, pk=None):
        if 'compCode' in request.data and 'source_cardNumber' in request.data:
            compCode = request.data['compCode']
            # source_compCode = request.data['source_compCode']
            source_cardNumber = request.data['source_cardNumber']
            source_reqRef = request.data['source_reqRef']
            source_consent_result = request.data['source_consent_result']

            try:
                # 1. check client exist ?
                clientObj = mit_client.objects.get(
                    compCode__iexact=compCode, cardNumber=source_cardNumber)
                _fullName = clientObj.thFirstName + ' '+clientObj.thLastName

                # 2. update consent
                # 2.1 get consent is follow cross company
                consentTag = ''
                consentCrossComp = mit_cmp_consentmas.objects.filter(
                    compCode__iexact=compCode, consStatus='A', crossCompFollow='Y')

                if len(consentCrossComp) <= 0:
                    response = {
                        'code': '003', 'message': 'Not found cosent config crossCompFollow of ' + compCode}
                    return Response(response, status=status.HTTP_200_OK)

                for consentObj in consentCrossComp:
                    consentTag = consentTag + \
                        str(consentObj.id)+':'+source_consent_result

                    try:
                        consent = mit_cmp_Response.objects.get(
                            compCode__iexact=compCode, custCode=clientObj, consent=consentObj)
                        consent.respStatus = source_consent_result
                        consent.save()
                    except ObjectDoesNotExist:
                        # Create consent
                        response = mit_cmp_Response.objects.create(
                            compCode=compCode, consent=consentObj, custCode=clientObj, respStatus=source_consent_result)

                # 3. create request, status = finish , has memo from cross company
                reqDetail = 'Consent cross company :' + source_reqRef + \
                    ' ;Auto change consent to '+consentTag
                reqCode = 'consent'
                reqStatus = 'finish'

                request = mit_cmp_request.objects.create(
                    compCode=compCode, custCode=clientObj, reqCode=reqCode, reqDetail=reqDetail, reqStatus=reqStatus)

                _ref = utils.getReqRef(compCode, reqCode, request.id)
                request.reqRef = _ref
                request.save()

                # 4. send mail to DPO.
                reqDesc = 'Consent of ' + _fullName + \
                    ' changed by cross company rule. Reference by request number ' + _ref + ' :' + reqDetail

                utils.sendMail_ConsentCrossComp(compCode, reqDesc)

                response = {'code': '000', 'message': 'Succesful'}
                return Response(response, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                response = {'code': '002', 'message': 'Not found client'}
                return Response(response, status=status.HTTP_200_OK)

            except Exception as e:
                print(str(e))
                response = {'code': '999', 'message': 'Application exception'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # 1. Create request code = consent,
    # 2. Set status= waitApprove,
    # 3. send mail to DPO for approve

    @action(detail=True, methods=['POST'])
    def consentReq(self, request, pk=None):
        if 'compcode' in request.data and pk != None:
            compcode = request.data['compcode']
            actionBy = request.data['actionBy']
            channel = request.data['channel']
            client = mit_client.objects.get(id=pk)
            consents = request.data['consents']

            if (consentCrossComp := request.data.get("consentCrossComp")):
                pass

            # Initial value
            reqCode = 'consent'
            reqStatus = 'waitApprove'
            consentJSON = json.dumps(consents)
            # reqReasonText = str(consentJSON)
            consentArray = json.loads(consentJSON)

            # Validate duplicate consent request
            consentRequestList = mit_cmp_request.objects.filter(
                compCode=compcode, custCode=client, reqCode=reqCode, reqStatus='waitApprove')
            if len(consentRequestList) > 0:
                response = {
                    'code': '001', 'message': 'Has consent request not approve. Please finish the exist before add new request.'}
                return Response(response, status=status.HTTP_200_OK)

            requestDate = None
            if 'requestDate' in request.data:
                try:
                    requestDate = request.data['requestDate']
                    requestDate = datetime.strptime(
                        requestDate, "%Y-%m-%d").date()
                    # print('req date> %s' % (str(requestDate)))
                except Exception as e:
                    print(e)
                    return Response({'message': 'requestDate: does not match format %Y-%m-%d'}, status=status.HTTP_400_BAD_REQUEST)

            reqDetail = ''
            for cosentObj in consentArray:
                if reqDetail != '':
                    reqDetail = reqDetail+","

                reqDetail = reqDetail + \
                    str(cosentObj.get("consentId")) + ":" + \
                    cosentObj.get("respStatus")

            # 1 Create request, status = waitApprove
            cmp_request = mit_cmp_request.objects.create(compCode=compcode, custCode=client, reqCode=reqCode, reqDetail=reqDetail,
                                                         reqStatus=reqStatus, createBy=actionBy, channel=channel, requestDate=requestDate)

            # Get request reference code.
            _ref = utils.getReqRef(compcode, reqCode, cmp_request.id, channel)

            # Update reqRef
            cmp_request.reqRef = _ref
            cmp_request.consentCrossComp = consentCrossComp
            cmp_request.save()

            utils.sendMailInternalProcess(cmp_request, 'DPO')

            # Mail to cust
            if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y')):
                if ('consentMail' not in request.data):
                    utils.sendMailPDPARequest_ToClientOnCreate(cmp_request)
                elif (request.data['consentMail'] == 'Y'):
                    utils.sendMailPDPARequest_ToClientOnCreate(cmp_request)

            response = {'code': '000', 'message': 'Succesful'}
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide response data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def consentresp(self, request, pk=None):
        if 'compcode' in request.data and pk != None:
            compcode = request.data['compcode']
            consents = request.data['consents']

            from datetime import datetime, timezone
            from datetime import date
            requestDate = datetime.now().strftime("%Y-%m-%d")
            if 'requestDate' in request.data:
                requestDate = request.data['requestDate']

            actionBy = ''
            if 'actionBy' in request.data:
                actionBy = request.data['actionBy']

            channel = 'Online'
            if 'channel' in request.data:
                channel = request.data['channel']

            # Action by Online
            mianRs = {}
            msg_resp = ''
            # crossCompRS = {"crossComp": []}
            crossCompRS = {}

            try:
                s1 = json.dumps(consents)
                jsonObject = json.loads(s1)
                for obj in jsonObject:
                    CmpConsentViewSet.custResponseFunc(
                        compcode, pk, obj.get('consentId'), obj.get('respStatus'), actionBy=actionBy, requestDate=requestDate)

                msg_resp = "Add/Update consent complete."
                mianRs.update(
                    {"code": 000, "message": "Add/Update consent complete."})

                # Update Consent cross comp
                # try:
                #     _reqRef = 'REQ-XXXX'
                #     crossCompRS = utils.consentCrossComp(
                #         compcode, pk, jsonObject, _reqRef)
                #     print(crossCompRS)
                #     mianRs.update(crossCompRS)

                # except Exception as e:
                #     print(e)

                # Consent Mail to client
                client = mit_client.objects.get(id=pk)
                if (consentMail := request.data.get("consentMail")):
                    if consentMail == 'Y' and (client.email != None):
                        utils.sendMail_ConsentRepose(compcode, client)
                        msg_resp = msg_resp + ' ; Email complete.'

                    elif consentMail == 'Y' and (client.phone != None):
                        # Send SMS

                        compName = '-'
                        try:
                            obj = mit_master_value.objects.get(
                                compCode__iexact=compcode, refType='COMP_NAME', refCode=compcode, status='A')
                            compName = obj.nameTh
                        except Exception:
                            print('Get Master COMP_NAME Not found')

                        try:
                            obj = mit_master_value.objects.get(
                                compCode__iexact=compcode, refType='CMP_SMS', refCode='SMS_CONSENT_SUCC', status='A')
                            sms_msg = compName + " " + obj.nameTh

                            if(not settings.PROD):
                                sms_msg = '[Develop]' + sms_msg
                            sms = smsGateWay(client.phone, sms_msg)
                            smsRs = sms.MpamSmsGW()
                            msg_resp = msg_resp + ' ; SMS complete.'
                        except Exception as e:
                            print(e)
                            raise

                response = mianRs

                return Response(response, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                # logger.error('Failed to upload to ftp: '+ str(e))
                print(str(e))
                response = {'code': '999', 'message': 'Application exception'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'])
    def gettaxlatest(self, request, pk=None):
        print(request.query_params)

        try:
            client = mit_client.objects.get(id=pk)
        except ObjectDoesNotExist:
            return Response("Not found client.", status=status.HTTP_200_OK)

        taxRequest = mit_cmp_request.objects.filter(
            reqCode='taxrefund', reqStatus__in=(('finish'), ('onprocess')), custCode=client).order_by('-createDate')[:1]
        # taxRequest = mit_cmp_request.objects.filter(
        #     reqCode='taxrefund', custCode=client, reqStatus='finish').order_by('-updateDate')[:1]

        print(taxRequest)

        return Response(taxRequest[0].reqDetail if len(taxRequest) > 0 else "0", status=status.HTTP_200_OK)

    # from datetime import tzinfo, timedelta, datetime
    # reqCode = taxrefund
    @action(detail=True, methods=['POST'])
    def submitTaxrequest(self, request, pk=None):
        print(request.data)
        response = {'code': '000', 'message': "Succesful"}

        if 'compcode' in request.data and pk != None:

            compcode = request.data['compcode']
            reqCode = request.data['reqcode']
            reqDetail = request.data['reqDetail']

            channel = 'Online'
            if 'channel' in request.data:
                channel = request.data['channel']

            actionBy = ''
            if 'actionBy' in request.data:
                actionBy = request.data['actionBy']

            from datetime import datetime, timezone
            from datetime import date
            requestDate = datetime.now().strftime("%Y-%m-%d")
            if 'requestDate' in request.data:
                try:
                    requestDate = request.data['requestDate']
                    requestDate = datetime.strptime(
                        requestDate, "%Y-%m-%d").date()
                except Exception as e:
                    print(e)
                    return Response({'message': 'requestDate: does not match format %Y-%m-%d'}, status=status.HTTP_400_BAD_REQUEST)

                reqStatus = 'onprocess'
                try:
                    client = mit_client.objects.get(
                        compCode__iexact=compcode, id=pk)

                    request = mit_cmp_request.objects.create(
                        compCode=compcode, custCode=client, reqCode=reqCode, reqDetail=reqDetail, reqStatus=reqStatus, channel=channel, createBy=actionBy, requestDate=requestDate)

                    # Update reqRef
                    _ref = utils.getReqRef(
                        compcode, reqCode, request.id, channel)
                    # Update reqRef
                    request.reqRef = _ref
                    request.save()

                    # Mail to oper
                    utils.sendMailTaxInternalProcess(request, 'OP')

                    # serializer = CmpRequestSerializer(request, many=False)
                    # response = {'message': 'Request created', 'result': serializer.data}
                    # return Response(response, status=status.HTTP_200_OK)

                    return Response(response, status=status.HTTP_200_OK)
                except Exception as e:
                    print(type(e))
                    response = {'message': "Some went wrong."}
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            print('HERE!!')
            response = {'message': 'You need to provide complete data'}

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def submitrequest(self, request, pk=None):
        if 'compcode' in request.data and pk != None:
            compcode = request.data['compcode']
            reqCode = request.data['reqcode']
            reqDetail = request.data['reqDetail']

            # reqReasonText = request.data['reqReasonText']
            reqReasonText = ''
            if 'reqReasonText' in request.data:
                reqReasonText = request.data['reqReasonText']

            # reqReasonChoice = request.data['reqReasonChoice']
            # reqAccounts = request.data['reqAccounts']

            reqReasonChoice = ''
            if 'reqReasonChoice' in request.data:
                reqReasonChoice = request.data['reqReasonChoice']

            reqAccounts = ''
            if 'reqAccounts' in request.data:
                reqAccounts = request.data['reqAccounts']

            channel = 'Online'
            if 'channel' in request.data:
                channel = request.data['channel']

            actionBy = ''
            if 'actionBy' in request.data:
                actionBy = request.data['actionBy']

            from datetime import datetime, timezone
            from datetime import date
            requestDate = datetime.now().strftime("%Y-%m-%d")
            if 'requestDate' in request.data:
                try:
                    requestDate = request.data['requestDate']
                    requestDate = datetime.strptime(
                        requestDate, "%Y-%m-%d").date()
                except Exception as e:
                    print(e)
                    return Response({'message': 'requestDate: does not match format %Y-%m-%d'}, status=status.HTTP_400_BAD_REQUEST)

            try:

                reqRef = CmpConsentViewSet.custRequestFunc(
                    compcode, pk, reqCode, reqDetail, reqReasonText, reqReasonChoice, reqAccounts, actionBy, channel, requestDate)
                response = {'code': '000', 'message': "Succesful"}

                if (channel == 'BE' and not(str(reqCode) in ['wealthRegister'])):
                    reqObj = mit_cmp_request.objects.get(reqRef=reqRef)
                    client = mit_client.objects.get(
                        compCode__iexact=compcode, id=pk)

                    # Send Mail
                    if (sendMail := request.data.get("sendMail")):
                        # Email
                        if sendMail == 'Y' and (client.email != None) and (client.email != '') and (settings.ENABLE_APP_MAIL_EXTERNAL == 'Y'):
                            try:
                                # PDPA Request
                                utils.sendMailPDPARequest_ToClientOnCreate(
                                    reqObj)

                            except Exception as e:
                                print(e)
                                pass

                        # SMS
                        elif sendMail == 'Y' and (client.phone != None) and (client.phone != '') and (settings.ENABLE_APP_SMS_EXTERNAL == 'Y'):
                            # Send SMS
                            print('SMS')

                            try:
                                obj = mit_master_value.objects.get(
                                    compCode__iexact=client.compCode, refType='CMP_SMS', refCode='SMS_REQUEST_CREATE', status='A')
                                sms_msg = obj.nameTh

                                appLink = '<CMP_APP_LINK>'
                                try:
                                    obj = mit_master_value.objects.get(
                                        compCode__iexact=client.compCode, refCode='CMP_APP_LINK', status='A')
                                    appLink = obj.nameTh
                                    sms_msg = sms_msg + ' ตรวจสอบข้อมูล คลิก ' + appLink
                                except Exception:
                                    print(
                                        'Get Master CMP_APP_LINK Not found')

                                if(not settings.PROD):
                                    sms_msg = '[Develop]' + sms_msg
                                sms = smsGateWay(client.phone, sms_msg)
                                smsRs = sms.MpamSmsGW()
                                # msg_resp = msg_resp + ' ; SMS complete.'
                            except Exception as e:
                                print(e)
                                raise
                        else:
                            print('None')

                return Response(response, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                print(str(e))
                response = {'code': '999', 'message': 'Application exception'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'])
    def getConsent(self, request, pk=None):
        if pk != None:
            try:
                response = mit_cmp_Response.objects.filter(custCode__id=pk)
                serializer = CmpResponseSerializer(
                    response, many=True, read_only=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                # logger.error('Failed to upload to ftp: '+ str(e))
                print(str(e))
                response = {'code': '999', 'message': 'Application exception'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def newClientList(self, request, pk=None):
        if 'compCode' in request.data and 'clients' in request.data:
            # print('compCode:%s ;action by:%s' %
            #       (request.data['compCode'], request.data['actionBy']))

            compCode = request.data['compCode']
            clients = request.data['clients']
            clientsJSON = json.dumps(clients)
            clientsArray = json.loads(clientsJSON)
            clientListRs = []
            actionBy = request.data['actionBy']
            clientExecute =0

            for obj in clientsArray:
                if(obj.get('cardNumber'))and not(obj.get('cardNumber') ==''):
                    
                    _cardNumber = obj.get('cardNumber')
                    clientExecute=clientExecute+1

                    print('*** _cardNumber:%s ;' % (_cardNumber))

                    try:
                        
                        # check exist
                        clent = mit_client.objects.get(
                            cardNumber=obj.get('cardNumber'))

                        clientListRs.append({"cardNumber": obj.get(
                            'cardNumber'), "status": "duplicate", "msg": "Already has data"})
                    except ObjectDoesNotExist:
                        # add new client
                        responseClient = mit_client.objects.create(compCode=compCode, thFirstName=obj.get('thFirstName'), thLastName=obj.get('thLastName'),
                                                                cardNumber=obj.get('cardNumber'), products=obj.get('products'), phone=obj.get('phone'), email=obj.get('email'), createBy=actionBy, channel=request.data['channel'])
                        
                        # Response message
                        clientListRs.append({"cardNumber": obj.get(
                            'cardNumber'), "status": "finish", "msg": "Add new client complete."})
                    except Exception as e:
                        # Error
                        clientListRs.append(
                            {"cardNumber": obj.get('cardNumber'), "status": "error", "msg": e})

                    if obj.get('consents'):
                        reqDetailTxt = ''
                        client = mit_client.objects.get(
                            cardNumber=obj.get('cardNumber'))

                        # consentArray = json.loads(obj.get('consents'))
                        for consentObj in obj.get('consents'):

                            consentMas = mit_cmp_consentmas.objects.get(compCode__iexact=compCode, consStatus="A", custCategory=consentObj.get(
                                'consentId'))

                            CmpConsentViewSet.custResponseFunc(
                                compCode, client.id, consentMas.id, consentObj.get('respStatus'), actionBy)

                            if reqDetailTxt != '':
                                reqDetailTxt = reqDetailTxt+","

                            reqDetailTxt = reqDetailTxt + str(consentMas.id)+":"+consentObj.get(
                                'respStatus')
                        # add request
                        reqCode = "consent"
                        requestObj = mit_cmp_request.objects.create(
                            compCode=compCode,  custCode=client, reqCode=reqCode, reqDetail=reqDetailTxt, reqStatus="finish", createBy=request.data['actionBy'], channel=request.data['channel'])

                        # # get reqRef
                        _ref = utils.getReqRef(
                            compCode, reqCode, requestObj.id, request.data['channel'])
                        # Update reqRef
                        requestObj.reqRef = _ref
                        requestObj.requestDate = datetime.now()
                        requestObj.save()

            response = {'code': '000', 'msg': clientListRs,
                        'result': ' client added '+str(clientExecute) + ' records. /' + str(len(clientsArray))}

            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def updateNewClientList(self, request, pk=None):
        print('%s' % (request.data))

        if 'compCode' in request.data and 'clients' in request.data:
            # print('compCode:%s ;action by:%s' %
            #       (request.data['compCode'], request.data['actionBy']))

            compCode = request.data['compCode']
            clients = request.data['clients']
            clientsJSON = json.dumps(clients)
            clientsArray = json.loads(clientsJSON)
            clientListRs = []
            for obj in clientsArray:
                client = None
                try:
                    # check exist & Update
                    clientObj = mit_client.objects.get(
                        cardNumber=obj.get('cardNumber'))
                    # clientObj.thFirstName = obj.get('thFirstName')
                    # clientObj.thLastName = obj.get('thLastName')
                    clientObj.email = obj.get('email')
                    clientObj.phone = obj.get('phone')
                    clientObj.products = obj.get('products')
                    clientObj.updateBy = request.data['actionBy']
                    clientObj.channel = request.data['channel']
                    clientObj.save()

                    client = clientObj

                    clientListRs.append({"cardNumber": obj.get(
                        'cardNumber'), "status": "update", "msg": "Client profile updated. "})
                except ObjectDoesNotExist:
                    # ADD NEW CLIENT
                    responseClient = mit_client.objects.create(compCode=compCode, thFirstName=obj.get('thFirstName'), thLastName=obj.get('thLastName'),
                                                               cardNumber=obj.get('cardNumber'), products=obj.get('products'), phone=obj.get('phone'), email=obj.get('email'), createBy=request.data['actionBy'], channel=request.data['channel'])
                    client = responseClient

                    # # ADD CONSENT
                    # reqDetailTxt = ''

                    # # Change to New implement consent E-Open
                    # consents = mit_cmp_consentmas.objects.filter(
                    #     compCode__iexact=compCode, consStatus='A')

                    # for consentObj in consents:
                    #     consentRs = consentObj.respStatus
                    #     CmpConsentViewSet.custResponseFunc(
                    #         compCode, responseClient.id, consentObj.id, consentRs, request.data['actionBy'])

                    #     if reqDetailTxt != '':
                    #         reqDetailTxt = reqDetailTxt+","

                    #     reqDetailTxt = reqDetailTxt + \
                    #         str(consentObj.id)+":"+consentRs

                    # respDescription = '<BR>Initial data default '
                    # reqCode = "consent"
                    # requestObj = mit_cmp_request.objects.create(
                    #     compCode=compCode,  custCode=responseClient, reqCode=reqCode, reqDetail=reqDetailTxt, reqStatus="finish", createBy=request.data['actionBy'], channel=request.data['channel'], respDescription=respDescription)

                    # # get reqRef
                    # _ref = utils.getReqRef(
                    #     compCode, reqCode, requestObj.id, request.data['channel'])
                    # # Update reqRef
                    # requestObj.reqRef = _ref
                    # requestObj.requestDate = datetime.now()
                    # requestObj.save()

                    clientListRs.append({"cardNumber": obj.get(
                        'cardNumber'), "status": "insert", "msg": "New client profile created."})
                except Exception as e:
                    # Error
                    clientListRs.append(
                        {"cardNumber": obj.get('cardNumber'), "status": "error", "msg": e})

                # New implement consent E-Open

                # consentSize = len(obj.get('pdpaAnswers'))
                # if(obj.get('status') == 'APPROVED' and consentSize > 0):
                # if(obj.get('status') == 'APPROVED' and obj.get('pdpaAnswers')):
                if(obj.get('pdpaAnswers')):

                    consentList = obj.get('pdpaAnswers')

                    # Create consent response
                    reqDetailTxt = ''
                    consent1 = mit_cmp_consentmas.objects.get(
                        compCode__iexact=compCode, consStatus='A', seq=1)
                    consent2 = mit_cmp_consentmas.objects.get(
                        compCode__iexact=compCode, consStatus='A', seq=2)

                    for consentObj in consentList:
                        # print("consent id : %s ans: %s" %
                        #       (consentObj['questionId'], consentObj['answer'][0]['id']))

                        _consentId = consentObj['questionId']
                        # _consentRs = consentObj['answer'][0]['id']
                        _consentRs = '1' if consentObj['answer'][0]['id'] == 'Y' else '0'
                        CONSENT_ID = ''

                        # Create consent response
                        if(_consentId.__contains__('Q1')):
                            CONSENT_ID = consent1.id
                            CmpConsentViewSet.custResponseFunc(
                                compCode, client.id, CONSENT_ID, _consentRs, request.data['actionBy'])

                        # Create consent response
                        if(_consentId.__contains__('Q2')):
                            CONSENT_ID = consent2.id
                            CmpConsentViewSet.custResponseFunc(
                                compCode, client.id, CONSENT_ID, _consentRs, request.data['actionBy'])

                        if reqDetailTxt != '':
                            reqDetailTxt = reqDetailTxt+","

                        reqDetailTxt = reqDetailTxt + \
                            str(CONSENT_ID) + ":" + _consentRs

                    # Create consent request
                    reqCode = "consent"
                    _reqStatus = 'finish'
                    respDescription = '<BR>Set consent by api. '

                    requestObj = mit_cmp_request.objects.create(
                        compCode=compCode,  custCode=client, reqCode=reqCode, reqDetail=reqDetailTxt, reqStatus=_reqStatus, createBy=request.data['actionBy'], channel=request.data['channel'], respDescription=respDescription)

                    # get req Ref.
                    _ref = utils.getReqRef(
                        compCode, reqCode, requestObj.id, request.data['channel'])
                    # Update request
                    requestObj.reqRef = _ref
                    requestObj.requestDate = datetime.now()
                    requestObj.save()

                # WEALTH REGISTER
                if(obj.get('status') == 'SUBMITTED' and obj.get('wealthAccount') and obj.get('wealthAccount') > 0):
                    reqCode = "wealthRegister"
                    try:
                        # UPDATE WEALTH Request
                        requestObj = mit_cmp_request.objects.get(
                            compCode=compCode,  custCode=client, reqCode=reqCode, reqStatus="waitApprove", createBy=request.data['actionBy'], channel=request.data['channel'])
                        # requestObj.reqAccounts = obj.get('wealthAccount')
                        # requestObj.save()
                        clientListRs.append({"cardNumber": client.cardNumber, "reqRef": requestObj.reqRef,
                                            "status": requestObj.reqStatus,  "msg": "Already have wealth request."})

                    except ObjectDoesNotExist:
                        # CREATE WEALTH Request
                        requestObj = mit_cmp_request.objects.create(
                            compCode=compCode,  custCode=client, reqCode=reqCode, reqAccounts=obj.get('wealthAccount'), reqStatus="waitApprove", createBy=request.data['actionBy'], channel=request.data['channel'])

                        # get reqRef
                        _ref = utils.getReqRef(
                            compCode, reqCode, requestObj.id, request.data['channel'])
                        # Update reqRef
                        requestObj.reqRef = _ref
                        requestObj.requestDate = datetime.now()
                        requestObj.save()
                        clientListRs.append({"cardNumber": client.cardNumber, "reqRef": requestObj.reqRef,
                                            "status": requestObj.reqStatus,  "msg": "Wealth request created."})

                        # SEND WEALTH MAIL TO RESPONDOR
                        _rs = utils.sendWealthRegister(requestObj)

            response = {'code': '000', 'msg': clientListRs,
                        'result': ' client '+str(len(clientsArray)) + ' records.'}

            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def newClientWithConsent(self, request, pk=None):
        if 'compCode' in request.data:
            compCode = request.data['compCode']
            thFirstName = request.data['thFirstName']
            thLastName = request.data['thLastName']
            cardNumber = request.data['cardNumber']
            email = request.data['email']
            phone = request.data['phone']
            products = request.data['products']
            consents = request.data['consents']
            actionBy = request.data['actionBy']
            msg_resp = ''
            crossCompDesc = ''

            try:

                # Create new client
                # response = mit_client.objects.create(compCode=compCode,thFirstName=thFirstName,thLastName=thLastName , \
                #     cardNumber=cardNumber,products=products)
                client_id = 0
                # serializer=''
                responseClient = ''
                channel = ' '
                if 'channel' in request.data:
                    channel = request.data['channel']

                try:

                    responseClient = mit_client.objects.get(
                        compCode=compCode, cardNumber=cardNumber)
                    response = {
                        'code': '001', 'msg': 'This customer already have', 'result': responseClient.pk}

                    return Response(response, status=status.HTTP_200_OK)

                except:
                    # Create new client
                    responseClient = mit_client.objects.create(compCode=compCode, thFirstName=thFirstName, thLastName=thLastName,
                                                               cardNumber=cardNumber, products=products, phone=phone, email=email, createBy=actionBy, channel=channel)
                    client_id = responseClient.pk
                    # serializer= MitClientSerializer(response,many=False)

                msg_resp = 'Client complete.'
                # Create/Update consents response
                _consent = json.dumps(consents)
                jsonObject = json.loads(_consent)
                for obj in jsonObject:
                    CmpConsentViewSet.custResponseFunc(compCode, client_id, obj.get(
                        'consentId'), obj.get('respStatus'), actionBy)

                    # crossCompDesc = crossCompDesc + "," + str(obj.get(
                    #     'consentId')) + ":"+str(obj.get('respStatus'))

                # Update Consent cross comp
                # crossCompRS = {}
                # try:
                #     _reqRef = 'XXX'
                #     crossCompRS = utils.consentCrossComp(
                #         compCode, responseClient.pk, jsonObject, _reqRef)

                # except Exception as e:
                #     print(e)

                print('Go to Send mail.')
                msg_resp = msg_resp + '; Consent complete.'
                # Consent Mail to client
                if (consentMail := request.data.get("consentMail")):
                    if consentMail == 'Y' and (responseClient.email != None) and (responseClient.email != ''):
                        print('Email is> %s' % (responseClient.email))
                        utils.sendMail_ConsentRepose(compCode, responseClient)

                        msg_resp = msg_resp + ' ; Email complete.'

                    elif consentMail == 'Y' and (responseClient.phone != None) and (responseClient.phone != ''):
                        # Send SMS

                        compName = '-'
                        try:
                            obj = mit_master_value.objects.get(
                                compCode__iexact=compCode, refType='COMP_NAME', refCode=compCode, status='A')
                            compName = obj.nameTh
                        except Exception:
                            print('Get Master COMP_NAME Not found')

                        try:
                            # print('DEBUG>>',settings.DEBUG)
                            obj = mit_master_value.objects.get(
                                compCode__iexact=compCode, refType='CMP_SMS', refCode='SMS_CONSENT_SUCC', status='A')
                            sms_msg = compName + " " + obj.nameTh

                            if(not settings.PROD):
                                sms_msg = '[Develop]' + sms_msg
                            sms = smsGateWay(responseClient.phone, sms_msg)
                            smsRs = sms.MpamSmsGW()
                            msg_resp = msg_resp + ' ; SMS complete.'
                        except Exception as e:
                            print(e)
                            raise

                    else:
                        print('None')

                response = {'code': '000', 'result': responseClient.pk}
                response.update(crossCompRS)

                return Response(response, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                # logger.error('Failed to upload to ftp: '+ str(e))
                # print(str(e))
                response = {'code': '999', 'message': str(e)}
                return Response(response, status=status.HTTP_202_ACCEPTED)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class MasterValueViewSet(viewsets.ModelViewSet):
    queryset = mit_master_value.objects.all()
    serializer_class = MasterValueSerializer
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # 127.0.0.1:8000/model/?radius=5&longitude=50&latitude=55.1214
    # http://localhost:8000/mit/masterValue/getRequestRejectMsgTemplate/?compCode=mpam
    @action(detail=False, methods=['GET'])
    def getRequestRejectMsgTemplate(self, request, pk=None):
        try:

            compCode = self.request.query_params.get('compCode')

            queryset = mit_master_value.objects.filter(
                compCode__iexact=compCode, refType='CMP_REQ_REJECT_TMP', status='A').order_by('seq')
            serializer = MasterValueShortSerializer(
                queryset, many=True, read_only=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['GET'])
    def getShowPortReports(self, request, pk=None):
        try:

            compCode = self.request.query_params.get('compCode')

            print(f' **getShowPortReports() compCode ={compCode}')
            queryset = mit_master_value.objects.filter(
                compCode__iexact=compCode, refType='PORTFOLIO',refCode='SHOW_PORTFOLIO_APP')
            
            serializer = MasterValueSerializer(queryset, many=True, read_only=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def cmpSubjectRequest(self, request, pk=None):


        user = request.user
        print(f'*** cmpSubjectRequest() user={user}')
        if not user.is_authenticated:
            return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        client = mit_client.objects.filter(user=user).first()
        print(f'*** cmpSubjectRequest() client={client}')



        if 'compCode' in request.data:
            compcode = request.data['compCode']
            refType = 'cmp_reqCategory'
            try:
                queryset = mit_master_value.objects.filter(
                    compCode__iexact=compcode, refType__exact=refType).order_by('seq')
                serializer = MasterValueShortSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)
        else:
            response = {'message': 'Bad request'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def callSch(self, request, pk=None):
        from .mit_scheduler import mit_sch
        msg = mit_sch.job_function()
        return Response({'message': msg}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['GET'])
    def getPFreportsbycid(self, request, pk=None):
        import json

        try:

            cid = self.request.query_params.get('cid')

            client = DirectoryClient(CONNECTION_STRING, CONTAINER_NAME)
            files = client.ls_files(cid)

            json_object = [{"name": item} for item in files]

            return Response(json_object, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def downloadPFreport(self, request, pk=None):
        try:

            cid = self.request.query_params.get('cid')
            fileName = self.request.query_params.get('fileName')
            client = DirectoryClient(CONNECTION_STRING, CONTAINER_NAME)
            # print(f'*** CID:{cid} ; FILE NAME:{fileName}')
            # Download file form Azuer and store in /downloads folder.
            client.download(f'{cid}/{fileName}', f'downloads/{fileName}')

           # Set the path to your files directory
            file_path = f'./downloads/{fileName}'  # Update this path accordingly
            
            # Check if file exists
            if os.path.exists(file_path):
                # Serve the file as a response
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                
                # Delete the file after it has been served
                os.remove(file_path)
                
                return response
            else:
                return Response({"error": "File not found"}, status=404)
        
        except Exception as e:
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clientinfo(request):
    print("*** get_clientinfo")

    user = request.user
    if not user.is_authenticated:
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    client = mit_client.objects.filter(user=user).first()

    serializer = MitClientTokenSerializer(client, many=False)
    return Response(serializer.data)