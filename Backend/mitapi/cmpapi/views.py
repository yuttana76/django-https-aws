# Create your views here.
import re
import time

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q


from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny


# import socket, sys

from .models import *
from .serializers import *

from mitmaster.models import *
from mitmaster.paginations import *
from movierater.utils import *

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from movierater.utils import smsGateWay


class cmpSendMail:
    def __init__(self, compCode, requestor, reqTopic, status, reqDetail, reqReasonText, reqReasonChoice, reqAccounts, createDate, reqRef):
        self.compCode = compCode
        self.requestor = requestor
        self.reqTopic = reqTopic
        self.status = status
        self.reqDetail = reqDetail
        self.reqReasonText = reqReasonText
        self.reqReasonChoice = reqReasonChoice
        self.reqAccounts = reqAccounts
        self.createDate = createDate
        self.reqRef = reqRef

    def sendCreateRequest(self):
        try:
            # Initial value
            mFrom = settings.EMAIL_CMP_FROM
            # mTo= [settings.EMAIL_CMP_DPO]

            request = mit_master_value.objects.get(
                compCode__iexact=self.compCode, refType='EMAIL_CMP_DPO')
            mTo = str(request.nameEn).split(',')

            # request = mit_master_value.objects.get(compCode__iexact=self.compCode, refType='EMAIL_CMP_FROM')
            # mFrom = request.nameEn

            c_data = {
                'requestor': self.requestor,
                'reqTopic':  self.reqTopic,
                'reqDetail': self.reqDetail,
                'reqReasonText': self.reqReasonText,
                'reqReasonChoice': self.reqReasonChoice,
                'reqAccounts': self.reqAccounts,
                'createDate': self.createDate,
                'reqRef': self.reqRef,
            }

            _subject = 'Ref:' + self.reqRef + \
                '[C-Portal]'+self.reqTopic + ' (' + self.status + ')'
            if(not settings.PROD):
                _subject = '[Develop]' + _subject

            html_body = render_to_string('mail/cmp_request_tmp.html', c_data)
            message = EmailMultiAlternatives(
                subject=_subject,
                body="mail testing",
                from_email=mFrom,
                to=mTo,
            )
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)

            return True
        except Exception as e:
            print('%s' % type(e))
            raise e

    # def sendWealthRegister(self):
    #     try:
    #         # Initial value
    #         # mFrom = settings.EMAIL_CLIENT_FROM
    #         mFrom = utils.getMasterValue(self.compCode, "SYSTEM_SERVICE_EMAIL")

    #         request = mit_master_value.objects.get(
    #             compCode__iexact=self.compCode, refType='EMAIL_WEALTH_REGIS_TO')
    #         mTo = str(request.nameEn).split(',')

    #         c_data = {
    #             'requestor': self.requestor,
    #             'reqTopic':  self.reqTopic,
    #             'reqDetail': self.reqDetail,
    #             'reqReasonText': self.reqReasonText,
    #             'reqReasonChoice': self.reqReasonChoice,
    #             'reqAccounts': self.reqAccounts,
    #             'createDate': self.createDate,
    #             'reqRef': self.reqRef,
    #         }

    #         _subject = 'Ref:' + self.reqRef + \
    #             ' [C-Portal] Merchant smart invest register.'
    #         if(not settings.PROD):
    #             _subject = '[Develop]' + _subject

    #         html_body = render_to_string('mail/wealth_regis_tmp.html', c_data)
    #         message = EmailMultiAlternatives(
    #             subject=_subject,
    #             body="mail testing",
    #             from_email=mFrom,
    #             to=mTo,
    #         )
    #         message.attach_alternative(html_body, "text/html")
    #         message.send(fail_silently=False)

    #         return True
    #     except Exception as e:
    #         print('%s' % type(e))
    #         raise e


class CmpConsentViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_consentmas.objects.all()
    serializer_class = CmpConsentMasSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        response = {'message': 'You cant get consent'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # def create(self,request, *args, **kwargs):
    #     response = {'message':'You cant create consent'}
    #     return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def getconsent(self, request, pk=None):
        if 'compCode' in request.data:
            compCode = request.data['compCode']
            response = mit_cmp_consentmas.objects.filter(
                compCode__iexact=compCode, consStatus="A").order_by("seq")
            serializer = CmpConsentMasSerializerShort(response, many=True)
            response = {'code': '000', 'message': 'Succesful',
                        'result': serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide response data'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def custResponse(self, request, pk=None):
        if 'respStatus' in request.data:
            compCode = request.data['compCode']
            consent = mit_cmp_consentmas.objects.get(id=pk)
            respStatus = request.data['respStatus']
            custCode = request.data['custCode']
            # user = request.user

            try:
                response = mit_cmp_Response.objects.get(
                    compCode=compCode, consent=consent, custCode=custCode)
                response.respStatus = respStatus
                response.save()
                serializer = CmpResponseSerializer(response, many=False)
                response = {'message': 'Response updated',
                            'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                response = mit_cmp_Response.objects.create(
                    compCode=compCode, consent=consent, custCode=custCode, respStatus=respStatus)
                serializer = CmpResponseSerializer(response, many=False)
                response = {'message': 'Response created',
                            'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)

        else:
            response = {'message': 'You need to provide response data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def custResponseFunc(compCode, custCode, consent_id, respStatus, actionBy='', requestDate=None, consentCrossComp=None):
        try:
            if requestDate == None:
                requestDate = datetime.now()

            consent = mit_cmp_consentmas.objects.get(
                compCode__iexact=compCode, id=consent_id)

            client = mit_client.objects.get(
                compCode__iexact=compCode, id=custCode)

            try:
                response = mit_cmp_Response.objects.get(
                    compCode__iexact=compCode, consent=consent, custCode=client)
                response.respStatus = respStatus
                response.updateBy = actionBy
                response.requestDate = requestDate
                response.consentCrossComp = consentCrossComp
                response.save()
                return True
            except:
                response = mit_cmp_Response.objects.create(
                    compCode=compCode, consent=consent, custCode=client, respStatus=respStatus, createBy=actionBy)
                return True

        except ObjectDoesNotExist:
            raise

    @action(detail=True, methods=['POST'])
    def custRequest(self, request, pk=None):
        if 'reqCategory' in request.data:
            compCode = request.data['compCode']
            consent = mit_cmp_consentmas.objects.get(id=pk)
            custCode = request.data['custCode']
            reqCode = request.data['reqCode']
            reqDesc = request.data['reqDesc']
            # approveStatus = request.data['approveStatus']
            reqStatus = "onprocess"

            if reqCode == "consent":
                reqStatus = "finish"

            if 'reqStatus' in request.data:
                reqStatus = request.data['reqStatus']

            try:
                request = mit_cmp_request.objects.create(
                    compCode=compCode, consent=consent, custCode=custCode, reqCode=reqCode, reqDetail=reqDesc, reqStatus=reqStatus)

                # Update reqRef
                _ref = utils.getReqRef(compCode, reqCode, request.id)
                # Update reqRef
                request.reqRef = _ref
                request.save()

                serializer = CmpRequestSerializer(request, many=False)
                response = {'message': 'Request created',
                            'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                response = {'message': 'You need to provide request data'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {'message': 'You need to provide request data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    from datetime import tzinfo, timedelta, datetime

    def custRequestFunc(compCode, custCode, reqCode, reqDetail, reqReasonText, reqReasonChoice, reqAccounts, actionBy='', channel='', requestDate=None):
        try:

            client = mit_client.objects.get(
                compCode__iexact=compCode, id=custCode)

            reqStatus = "waitApprove"
            if reqCode == 'consent' and channel == 'Online':
                reqStatus = "finish"

            # Create new request
            try:
                request = mit_cmp_request.objects.create(compCode=compCode, custCode=client, reqCode=reqCode, reqDetail=reqDetail, reqReasonText=reqReasonText,
                                                         reqReasonChoice=reqReasonChoice, reqAccounts=reqAccounts, reqStatus=reqStatus, createBy=actionBy, channel=channel, requestDate=requestDate)

                # Call function
                _ref = utils.getReqRef(compCode, reqCode, request.id, channel)
                # Update reqRef
                request.reqRef = _ref
                request.save()

                # Send mail to operation
                requestor = client.thFirstName + ' ' + client.thLastName

                try:
                    # Get subject request data
                    masterValue = mit_master_value.objects.get(
                        compCode__iexact=compCode, refCode__iexact=reqCode)

                    if reqStatus == "waitApprove":
                        # Send mail to who should know.(Internal email config master value)
                        cmpMail = cmpSendMail(compCode, requestor, masterValue.nameTh, reqStatus, reqDetail,
                                              reqReasonText, reqReasonChoice, reqAccounts, request.createDate, request.reqRef)

                        if masterValue.refType == "wealth" and reqCode == "wealthRegister":
                            cmpMailRs = utils.sendWealthRegister(request)

                        elif masterValue.refType == "cmp_reqCategory":
                            # cmpMailRs = cmpMail.sendCreateRequest()
                            utils.sendMailInternalProcess(request, 'DPO')

                        # # Not implemtn yet
                        # elif reqCode == "consent":
                        #     cmpMailRs = cmpMail.sendCreateConsentRequest()

                except ObjectDoesNotExist as e:
                    print(str(e))

                return request.reqRef
            except Exception as e:
                print(str(e))
                raise e
        except ObjectDoesNotExist:
            raise


class CmpReponseViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_Response.objects.all()
    serializer_class = CmpResponseSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )


class consentHisPageViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializerByOwner
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode
        filters['reqCode'] = 'consent'

        for key, value in self.request.query_params.items():
            if value != '':
                if key == 'proc':
                    if value == 'dpo':
                        filters['reqStatus__in'] = [
                            'waitApprove', 'fail', 'success']
                    elif value == 'op':
                        filters['reqStatus'] = 'onprocess'

                elif key == 'cardNumber':
                    filters['custCode__cardNumber'] = value
                elif key == 'thFirstName':
                    filters['custCode__thFirstName__contains'] = value
                elif key == 'thLastName':
                    filters['custCode__thLastName__contains'] = value

        if((self.request.query_params.get('fromDate') != None) and (self.request.query_params.get('toDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('fromDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('toDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['updateDate__range'] = (fromDate, toDate)
            except Exception as e:
                print(e)

        # Condition proc != all will retrive all range
        if ((self.request.query_params.get('proc') != None) and (self.request.query_params.get('proc') != 'all')):
            if 'updateDate__range' in filters:
                del filters['updateDate__range']

        print(filters)
        return mit_cmp_request.objects.filter(**filters).order_by('-updateDate')


class requestHisPageViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializerByOwner
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode

        for key, value in self.request.query_params.items():
            # print('KEY: {} : {}', (key, value))
            # if value != '':
            if key == 'proc':
                if value == 'dpo':
                    filters['reqStatus__in'] = [
                        'waitApprove', 'fail', 'success']
                elif value == 'op':
                    # onprocess
                    filters['reqStatus'] = 'onprocess'

            elif key == 'cardNumber':
                filters['custCode__cardNumber'] = value
            elif key == 'thFirstName':
                filters['custCode__thFirstName__contains'] = value
            elif key == 'thLastName':
                filters['custCode__thLastName__contains'] = value

        if((self.request.query_params.get('fromDate') != None) and (self.request.query_params.get('toDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('fromDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('toDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['updateDate__range'] = (fromDate, toDate)

            except Exception as e:
                print(e)

        # Condition proc != all will retrive all range
        if ((self.request.query_params.get('proc') != None) and (self.request.query_params.get('proc') != 'all')):
            if 'updateDate__range' in filters:
                del filters['updateDate__range']

        req_exclude = [('consent'), ('wealthRegister'), ('taxrefund')]

        return mit_cmp_request.objects.filter(**filters).exclude(reqCode__in=req_exclude).order_by('-updateDate')


class taxHisPageViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializerByOwner
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode
        filters['reqCode'] = 'taxrefund'

        for key, value in self.request.query_params.items():
            # print('KEY: {} : {}', (key, value))
            # if value != '':
            if key == 'proc':
                if value == 'onprocess':
                    filters['reqStatus'] = 'onprocess'
                elif value == 'finish':
                    filters['reqStatus'] = 'finish'

            elif key == 'cardNumber':
                filters['custCode__cardNumber'] = value
            elif key == 'thFirstName':
                filters['custCode__thFirstName__contains'] = value
            elif key == 'thLastName':
                filters['custCode__thLastName__contains'] = value

        if((self.request.query_params.get('fromDate') != None) and (self.request.query_params.get('toDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('fromDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('toDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['updateDate__range'] = (fromDate, toDate)

            except Exception as e:
                print(e)

        # Condition proc != all will retrive all range
        if ((self.request.query_params.get('proc') != None) and (self.request.query_params.get('proc') != 'all')):
            if 'updateDate__range' in filters:
                del filters['updateDate__range']

        # req_exclude = [('consent'), ('access'), ('rectification'), ('erasure'),
        #                ('dataportability'), ('rightToObject'), ('restrictProcess'), ('wealthRegister')]

        print(filters)
        # return mit_cmp_request.objects.filter(**filters).exclude(reqCode__in=req_exclude).order_by('-updateDate')
        return mit_cmp_request.objects.filter(**filters).order_by('-updateDate')


class taxHisNoPageViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializerByOwner
    # pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode
        filters['reqCode'] = 'taxrefund'

        for key, value in self.request.query_params.items():
            # print('KEY: {} : {}', (key, value))
            # if value != '':
            if key == 'proc':
                if value == 'onprocess':
                    filters['reqStatus'] = 'onprocess'
                elif value == 'finish':
                    filters['reqStatus'] = 'finish'

            elif key == 'cardNumber':
                filters['custCode__cardNumber'] = value
            elif key == 'thFirstName':
                filters['custCode__thFirstName__contains'] = value
            elif key == 'thLastName':
                filters['custCode__thLastName__contains'] = value

        if((self.request.query_params.get('fromDate') != None) and (self.request.query_params.get('toDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('fromDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('toDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['updateDate__range'] = (fromDate, toDate)

            except Exception as e:
                print(e)

        # Condition proc != all will retrive all range
        if ((self.request.query_params.get('proc') != None) and (self.request.query_params.get('proc') != 'all')):
            if 'updateDate__range' in filters:
                del filters['updateDate__range']

        # req_exclude = [('consent'), ('access'), ('rectification'), ('erasure'),
        #                ('dataportability'), ('rightToObject'), ('restrictProcess'), ('wealthRegister')]

        print(filters)
        # return mit_cmp_request.objects.filter(**filters).exclude(reqCode__in=req_exclude).order_by('-updateDate')
        return mit_cmp_request.objects.filter(**filters).order_by('-updateDate')


class wealthHisPageViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializerByOwner
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override
    def get_queryset(self):

        filters = {}

        if (compCode := self.request.query_params.get('compCode')):
            pass
        else:
            compCode = settings.COMP_CODE
        filters['compCode__iexact'] = compCode
        filters['reqCode'] = 'wealthRegister'
        for key, value in self.request.query_params.items():
            # print('KEY: {} : {}', (key, value))
            # if value != '':
            if key == 'proc':
                if value == 'waitApprove':
                    filters['reqStatus'] = 'waitApprove'
                elif value == 'finish':
                    filters['reqStatus'] = 'finish'
                elif value == 'reject':
                    filters['reqStatus'] = 'reject'

            elif key == 'cardNumber':
                filters['custCode__cardNumber'] = value
            elif key == 'thFirstName':
                filters['custCode__thFirstName__contains'] = value
            elif key == 'thLastName':
                filters['custCode__thLastName__contains'] = value

        if((self.request.query_params.get('fromDate') != None) and (self.request.query_params.get('toDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('fromDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('toDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['updateDate__range'] = (fromDate, toDate)

            except Exception as e:
                print(e)

        # Condition proc != all will retrive all range
        if ((self.request.query_params.get('proc') != None) and (self.request.query_params.get('proc') != 'all')):
            if 'updateDate__range' in filters:
                del filters['updateDate__range']

        # req_exclude = [('consent'), ('access'), ('rectification'), ('erasure'),
        #                ('dataportability'), ('rightToObject'), ('restrictProcess'),('taxrefund')]

        print(filters)
        # return mit_cmp_request.objects.filter(**filters).exclude(reqCode__in=req_exclude).order_by('-updateDate')
        return mit_cmp_request.objects.filter(**filters).order_by('-updateDate')


class CmpRequestViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializer
    pagination_class = CustomPagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['GET'])
    def consentHis(self, request, pk=None):
        try:

            queryset = mit_cmp_request.objects.filter(
                reqCode='consent').order_by('-createDate')
            serializer = CmpRequestSerializerByOwner(
                queryset, many=True, read_only=True)
            pagination_class = CustomPagination

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error('Failed to upload to ftp: '+ str(e))
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def requestHis(self, request, pk=None):
        try:
            reqCod_list = [('consent'), ('wealthRegister')]
            queryset = mit_cmp_request.objects.exclude(
                reqCode__in=reqCod_list).order_by('-createDate')

            serializer = CmpRequestSerializerByOwner(
                queryset, many=True, read_only=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error('Failed to upload to ftp: '+ str(e))
            print(str(e))
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def resentRequestMail(self, request, pk=None):
        reqRef = request.data['reqRef']
        try:
            reqObj = mit_cmp_request.objects.get(reqRef__iexact=reqRef)

            if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y') and (reqObj.custCode.email != None) and (reqObj.custCode.email != '')):
                # SEND MAIL
                print('MAIL to %s' % (reqObj.custCode.email))
                if(reqObj.reqStatus == 'reject'):
                    utils.sendMailPDPARequestRSP_reject(reqObj)
                else:
                    utils.sendMailPDPARequestRSP(reqObj)
            if((settings.ENABLE_APP_SMS_EXTERNAL == 'Y') and (reqObj.custCode.phone != None) and (reqObj.custCode.phone != '')):
                # SEND SMS
                print('SMS to %s' % (reqObj.custCode.phone))
                try:
                    obj = mit_master_value.objects.get(
                        compCode__iexact=reqObj.compCode, refCode='CMP_APP_LINK', status='A')
                    compAppLink = obj.nameTh
                except Exception:
                    print('Get Master compAppLink Not found')

                # if(reqObj.reqStatus=='reject'):
                if reqObj.reqStatus == 'finish':
                    try:
                        obj = mit_master_value.objects.get(
                            compCode__iexact=reqObj.compCode, refType='CMP_SMS', refCode='SMS_REQUEST_FINISH', status='A')
                        sms_msg = obj.nameTh + " ตรวจสอบข้อมูล คลิก " + compAppLink

                        if(not settings.PROD):
                            sms_msg = '[Develop]' + sms_msg
                        sms = smsGateWay(reqObj.custCode.phone, sms_msg)
                        smsRs = sms.MpamSmsGW()
                    except Exception as e:
                        print(e)
                        pass

                elif reqObj.reqStatus == 'reject':
                    try:
                        obj = mit_master_value.objects.get(
                            compCode__iexact=reqObj.compCode, refType='CMP_SMS', refCode='SMS_REQUEST_REJECT', status='A')
                        sms_msg = obj.nameTh + " ตรวจสอบข้อมูล คลิก " + compAppLink

                        if(not settings.PROD):
                            sms_msg = '[Develop]' + sms_msg
                        sms = smsGateWay(reqObj.custCode.phone, sms_msg)
                        smsRs = sms.MpamSmsGW()
                    except Exception as e:
                        print(e)
                        pass

                else:
                    print('reqStatus not match')

            response = {'code': '000', 'message': 'Succesful '}
            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            response = {'code': '001', 'message': 'Data Not Found'}
            return Response(response, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['POST'])
    def resentWealthtMail(self, request, pk=None):
        reqRef = request.data['reqRef']
        rspMsg = ""
        try:
            reqObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqRef, reqCode='wealthRegister')

            if(reqObj.reqStatus != 'finish'):
                response = {'code': '002',
                            'message': 'request status not finish.'}
                return Response(response, status=status.HTTP_200_OK)

            if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y') and (reqObj.custCode.email != None) and (reqObj.custCode.email != '')):
                #   if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y') and (reqObj.custCode.email != None) and (reqObj.custCode.email != '')and (reqObj.custCode.email != '-')):
                # SEND MAIL
                print('MAIL to %s' % (reqObj.custCode.email))
                if(reqObj.reqStatus == 'finish'):
                    try:
                        utils.sendMailRegisterResult_Finish(reqObj)
                        rspMsg = 'Send Email complete.'
                    except Exception as e:
                        # print(f'caught {type(e)}: e')
                        rspMsg = f'caught {type(e)}: '

            elif((settings.ENABLE_APP_SMS_EXTERNAL == 'Y') and (reqObj.custCode.phone != None) and (reqObj.custCode.phone != '')):
                # SEND SMS
                print('SMS to %s' % (reqObj.custCode.phone))

                if reqObj.reqStatus == 'finish':
                    try:
                        # print('DEBUG>>',settings.DEBUG)
                        obj = mit_master_value.objects.get(
                            compCode__iexact=reqObj.compCode, refType='WEALTH_SMS', refCode='SMS_REGISTOR_FINISH', status='A')
                        sms_msg = obj.nameTh

                        if(not settings.PROD):
                            sms_msg = '[Develop]' + sms_msg
                        sms = smsGateWay(reqObj.custCode.phone, sms_msg)
                        smsRs = sms.MpamSmsGW()
                        # msg_resp = msg_resp + ' ; SMS complete.'
                        rspMsg = 'Send SMS complete'
                    except Exception as e:
                        print(e)
                        raise

            else:
                rspMsg = 'No configuration for send email/SMS .'

            response = {'code': '000', 'message': rspMsg}
            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            response = {'code': '001',
                        'message': 'Not Found wealth request for ' + reqRef}
            return Response(response, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['POST'])
    def resentTaxMail(self, request, pk=None):
        reqRef = request.data['reqRef']
        rspMsg = ""
        try:
            reqObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqRef, reqCode='taxrefund')

            if(reqObj.reqStatus != 'finish'):
                response = {'code': '002',
                            'message': 'request status not finish.'}
                return Response(response, status=status.HTTP_200_OK)

            if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y') and (reqObj.custCode.email != None) and (reqObj.custCode.email != '')):
                #   if((settings.ENABLE_APP_MAIL_EXTERNAL == 'Y') and (reqObj.custCode.email != None) and (reqObj.custCode.email != '')and (reqObj.custCode.email != '-')):
                # SEND MAIL
                print('MAIL to %s' % (reqObj.custCode.email))
                if(reqObj.reqStatus == 'finish'):
                    try:
                        utils.sendMailTaxResult_Finish(reqObj)
                        rspMsg = 'Send Email complete.'
                    except Exception as e:
                        # print(f'caught {type(e)}: e')
                        rspMsg = f'caught {type(e)}: '

            elif((settings.ENABLE_APP_SMS_EXTERNAL == 'Y') and (reqObj.custCode.phone != None) and (reqObj.custCode.phone != '')):
                # SEND SMS
                print('SMS to %s' % (reqObj.custCode.phone))

                if reqObj.reqStatus == 'finish':
                    try:
                        # print('DEBUG>>',settings.DEBUG)
                        obj = mit_master_value.objects.get(
                            compCode__iexact=reqObj.compCode, refType='TAX_SMS', refCode='SMS_REFUND_FINISH', status='A')
                        sms_msg = obj.nameTh

                        if(not settings.PROD):
                            sms_msg = '[Develop]' + sms_msg
                        sms = smsGateWay(reqObj.custCode.phone, sms_msg)
                        smsRs = sms.MpamSmsGW()
                        # msg_resp = msg_resp + ' ; SMS complete.'
                        rspMsg = 'Send SMS complete'
                    except Exception as e:
                        print(e)
                        raise

            else:
                rspMsg = 'No configuration for send email/SMS .'

            response = {'code': '000', 'message': rspMsg}
            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            response = {'code': '001',
                        'message': 'Not Found wealth request for ' + reqRef}
            return Response(response, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['POST'])
    def updateStatus(self, request, pk=None):

        if 'actionBy' in request.data and 'reqRef' in request.data and 'reqStatus' in request.data:

            updateBy = request.data['actionBy']
            reqRef = request.data['reqRef']
            reqStatus = request.data['reqStatus']
            clientId = ''
            try:
                if (respDescription := request.data.get("respDescription")):
                    pass

                if (respMailText := request.data.get("respMailText")):
                    pass

                reqObj = mit_cmp_request.objects.get(reqRef__iexact=reqRef)

                clientId = reqObj.custCode.id

                # Update now
                reqObj.reqStatus = reqStatus
                reqObj.respDescription = respDescription
                reqObj.respMailText = respMailText
                reqObj.updateBy = updateBy
                reqObj.save()

                # Update consent
                if (reqObj.reqCode.lower() == 'consent') and (str(reqStatus.lower()) in ("finish")):
                    actionBy = reqObj.createBy
                    reqDetail = str(reqObj.reqDetail)
                    reqDetailArray = reqDetail.split(",")

                    for consObj in reqDetailArray:
                        if len(consObj) > 0 and consObj[0] != '':
                            CmpConsentViewSet.custResponseFunc(
                                reqObj.compCode, reqObj.custCode.id, str(consObj[0]), str(consObj[2]), actionBy, reqObj.requestDate, reqObj.consentCrossComp)

                if str(reqStatus).lower() in ("waitApprove", "fail", "success"):
                    # (waitApprove,fail,success) MAIL TO DPO
                    utils.sendMailInternalProcess(reqObj, 'DPO')

                elif str(reqStatus).lower() in ("onprocess"):
                    # (onprocess) MAIL TO OP
                    utils.sendMailInternalProcess(reqObj, 'OP')

                # Mail to client
                elif str(reqStatus).lower() in ("finish", "reject"):

                    # SEND MAIL TO Internal (OP)
                    utils.sendMailInternalProcess(reqObj, 'OP')

                    # SEND MAIL TO Client(Customer)
                    client = mit_client.objects.get(id=clientId)
                    if ((sendMail := request.data.get("sendMail")) and (settings.ENABLE_APP_MAIL_EXTERNAL == 'Y')):
                        # Email
                        if ((str(sendMail).upper() == 'Y') and (client.email != None) and (client.email != '')):
                            print('Send mail')

                            # Wealth registration
                            if reqObj.reqCode.lower() == 'wealthRegister'.lower():
                                # Send Mail;
                                try:
                                    # Wealth registration
                                    if str(reqStatus).lower() == 'finish' and (settings.ENABLE_APP_MAIL_EXTERNAL == 'Y'):
                                        utils.sendMailRegisterResult_Finish(
                                            reqObj)
                                except Exception as e:
                                    print(e)
                                    pass

                            else:
                                # ("finish", "reject"):
                                if str(reqStatus).lower() == "finish" and (settings.ENABLE_APP_MAIL_EXTERNAL == 'Y'):
                                    try:
                                        # PDPA Request & Consent :To customer was created (Not sent tempolary )
                                        utils.sendMailPDPARequestRSP(reqObj)

                                    except Exception as e:
                                        print(e)
                                        pass
                                elif str(reqStatus).lower() == "reject" and (settings.ENABLE_APP_MAIL_EXTERNAL == 'Y'):
                                    try:
                                        # PDPA Request & Consent :To customer was created (Not sent tempolary )
                                        utils.sendMailPDPARequestRSP_reject(
                                            reqObj)

                                    except Exception as e:
                                        print(e)
                                        pass
                                else:
                                    pass

                        # SMS
                        elif ((str(sendMail).upper() == 'Y') and (client.phone != None) and (client.phone != '') and (settings.ENABLE_APP_SMS_EXTERNAL == 'Y')):
                            # Send SMS
                            print('SMS')

                            compAppLink = '<compAppLink>'
                            try:
                                obj = mit_master_value.objects.get(
                                    compCode__iexact=client.compCode, refCode='CMP_APP_LINK', status='A')
                                compAppLink = obj.nameTh
                            except Exception:
                                print('Get Master compAppLink Not found')

                            if reqObj.reqCode == 'wealthRegister':
                                pass
                                try:
                                    # print('DEBUG>>',settings.DEBUG)
                                    obj = mit_master_value.objects.get(
                                        compCode__iexact=client.compCode, refType='WEALTH_SMS', refCode='SMS_REGISTOR_FINISH', status='A')
                                    sms_msg = obj.nameTh

                                    if(not settings.PROD):
                                        sms_msg = '[Develop]' + sms_msg
                                    sms = smsGateWay(client.phone, sms_msg)
                                    smsRs = sms.MpamSmsGW()
                                    # msg_resp = msg_resp + ' ; SMS complete.'
                                except Exception as e:
                                    print(e)
                                    raise
                            else:
                                # FINISH
                                # REJECT
                                if reqStatus == 'finish':
                                    try:
                                        obj = mit_master_value.objects.get(
                                            compCode__iexact=client.compCode, refType='CMP_SMS', refCode='SMS_REQUEST_FINISH', status='A')
                                        sms_msg = obj.nameTh + " ตรวจสอบข้อมูล คลิก " + compAppLink

                                        if(not settings.PROD):
                                            sms_msg = '[Develop]' + sms_msg
                                        sms = smsGateWay(client.phone, sms_msg)
                                        smsRs = sms.MpamSmsGW()
                                    except Exception as e:
                                        print(e)
                                        pass

                                elif reqStatus == 'reject':
                                    try:
                                        obj = mit_master_value.objects.get(
                                            compCode__iexact=client.compCode, refType='CMP_SMS', refCode='SMS_REQUEST_REJECT', status='A')
                                        sms_msg = obj.nameTh + " ตรวจสอบข้อมูล คลิก " + compAppLink

                                        if(not settings.PROD):
                                            sms_msg = '[Develop]' + sms_msg
                                        sms = smsGateWay(client.phone, sms_msg)
                                        smsRs = sms.MpamSmsGW()
                                    except Exception as e:
                                        print(e)
                                        pass

                                else:
                                    print('reqStatus not match')

                        else:
                            print('Req. code not match')

                # Save to db.
                response = {'msg': 'Change data complete.'}
                return Response(response, status=status.HTTP_200_OK)

            except ObjectDoesNotExist as e:
                print(str(e))
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)

        else:
            response = {'message': 'You need to provide response data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def taxUpdateStatus(self, request, pk=None):
        print('taxUpdateStatus() ')
        if 'actionBy' in request.data and 'reqRef' in request.data and 'reqStatus' in request.data:

            updateBy = request.data['actionBy']
            reqRef = request.data['reqRef']
            reqStatus = request.data['reqStatus']
            clientId = ''
            try:
                if (respDescription := request.data.get("respDescription")):
                    pass

                reqObj = mit_cmp_request.objects.get(reqRef__iexact=reqRef)

                clientId = reqObj.custCode.id

                # Update now
                reqObj.reqStatus = reqStatus
                reqObj.respDescription = respDescription
                reqObj.updateBy = updateBy
                reqObj.save()

                # Mail to client
                if str(reqStatus).lower() in ("finish"):

                    # SEND MAIL TO Internal (OP)
                    utils.sendMailTaxInternalProcess(reqObj, 'OP')

                    # SEND MAIL TO Client(Customer)
                    client = mit_client.objects.get(id=clientId)
                    if ((sendMail := request.data.get("sendMail")) and (settings.ENABLE_TAX_MAIL_EXTERNAL == 'Y')):
                        # Email
                        if ((str(sendMail).upper() == 'Y') and (client.email != None) and (client.email != '')):
                            print('Send mail')
                            utils.sendMailTaxResult_Finish(reqObj)

                        # SMS
                        elif ((str(sendMail).upper() == 'Y') and (client.phone != None) and (client.phone != '') and (settings.ENABLE_TAX_SMS_EXTERNAL == 'Y')):
                            # Send SMS
                            print('SMS')
                            if reqObj.reqCode == 'taxrefund':
                                pass
                                try:
                                    obj = mit_master_value.objects.get(
                                        compCode__iexact=client.compCode, refType='TAX_SMS', refCode='SMS_REFUND_FINISH', status='A')
                                    sms_msg = obj.nameTh

                                    if(not settings.PROD):
                                        sms_msg = '[Develop]' + sms_msg
                                    sms = smsGateWay(client.phone, sms_msg)
                                    smsRs = sms.MpamSmsGW()
                                    # msg_resp = msg_resp + ' ; SMS complete.'
                                except Exception as e:
                                    print(e)
                                    raise

                        else:
                            print('Req. code not match')

                response = {'msg': 'Change data complete.'}
                return Response(response, status=status.HTTP_200_OK)

            except ObjectDoesNotExist as e:
                print(str(e))
                response = {'code': '001', 'message': 'Data Not Found'}
                return Response(response, status=status.HTTP_202_ACCEPTED)

        else:
            response = {'message': 'You need to provide response data'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CmpRequestCFGViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_requestCFG.objects.all()
    serializer_class = CmprequestCFGSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['GET'])
    def cntConsent(self, request, pk=None):

        request.query_params.get('src')
        result = {}
        result['src'] = request.query_params.get('src')

        if (src := self.request.query_params.get('src')):
            pass
        else:
            response = {'code': '999', 'message': 'Not found parameter.'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        try:

            dpo_status = [('waitApprove'), ('fail'), ('success')]
            if src == 'consent':
                consent_dpo = mit_cmp_request.objects.filter(
                    reqCode='consent', reqStatus__in=dpo_status)
                result['cnt_dpo'] = len(consent_dpo)

                consent_op = mit_cmp_request.objects.filter(
                    reqCode='consent', reqStatus='onprocess')
                result['cnt_op'] = len(consent_op)

            elif src == 'request':

                req_exclude = [('consent'), ('wealthRegister'), ('taxrefund')]

                consent_dpo = mit_cmp_request.objects.filter(
                    reqStatus__in=dpo_status).exclude(reqCode__in=req_exclude)
                result['cnt_dpo'] = len(consent_dpo)

                consent_op = mit_cmp_request.objects.filter(
                    reqStatus='onprocess').exclude(reqCode__in=req_exclude)
                result['cnt_op'] = len(consent_op)

            elif src == 'wealthRegister':

                consent_op = mit_cmp_request.objects.filter(reqCode='wealthRegister',
                                                            reqStatus='waitApprove')
                result['cnt_op'] = len(consent_op)

            elif src == 'taxrefund':

                consent_op = mit_cmp_request.objects.filter(reqCode='taxrefund',
                                                            reqStatus='onprocess')
                result['cnt_op'] = len(consent_op)

            response = {'code': '000', 'result': result}
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            response = {'code': '999', 'message': 'Application exception'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CmpConsentRespViewSet(viewsets.ModelViewSet):
    queryset = mit_cmp_request.objects.all()
    serializer_class = CmpRequestSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['GET'])
    def consentAutoApprove(self, request, pk=None):
        
        print("cmpAutoApprove:",self.request.query_params.get('compCode'))
        import datetime


        if (src := self.request.query_params.get('compCode')):
            try:

                transferRequestList = mit_cmp_request.objects.filter(compCode__iexact=self.request.query_params.get('compCode'),
                                                              reqCode__iexact='dataportability',reqStatus__iexact='waitApprove')

                allData=transferRequestList.count()
                numEmail=0
                numMobile=0
                numNodata=0

                for reqObj in transferRequestList:
                    
                    # SEND E-MAIL
                    if reqObj.custCode.email :
                        numEmail+=1

                        try:
                            # PDPA Request & Consent :To customer was created (Not sent tempolary )
                            utils.sendMailPDPARequestRSP_Autoapprove(reqObj)
                            reqObj.respDescription = 'Update by system. response by email on ' +datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


                        except Exception as e:
                            print(e)
                            pass
                    # SMS
                    elif reqObj.custCode.phone:

                        numMobile+=1 

                        compAppLink = '<compAppLink>'
                        try:
                            obj = mit_master_value.objects.get(
                                compCode__iexact=reqObj.custCode.compCode, refCode='CMP_APP_LINK', status='A')
                            compAppLink = obj.nameTh
                        except Exception:
                            print('Get Master compAppLink Not found')

                        try:
                            obj = mit_master_value.objects.get(
                                compCode__iexact=reqObj.custCode.compCode, refType='CMP_SMS', refCode='AUTOAPPROVE_SMS_REQUEST_FINISH', status='A')
                            sms_msg = obj.nameTh + " ตรวจสอบข้อมูล คลิก " + compAppLink

                            if(not settings.PROD):
                                sms_msg = '[Develop]' + sms_msg

                            sms = smsGateWay(reqObj.custCode.phone, sms_msg)
                            smsRs = sms.MpamSmsGW()

                            reqObj.respDescription = 'Update by system. response by SMS on ' +datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        except Exception as e:
                            print(e)

                    else:
                        numNodata+=1
                        reqObj.respDescription = 'Update by system. No channel to response  on ' +datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # # Update now
                    reqObj.reqStatus = 'finish'
                    # reqObj.respDescription = 'change status by system.'
                    reqObj.updateBy = 'System'
                    reqObj.save()

                    time.sleep(1)  # Delay for 1 seconds

                    
                response = {'allData': str(allData),'numEmail':str(numEmail), 'numMobile':str(numMobile), 'numNodata':str(numNodata)}

                return Response(response, status=status.HTTP_200_OK)
            
            except Exception as e:
                response = {'code': '999', 'message': 'Application exception'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            response = {'code': '999', 'message': 'Not found parameter.'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
