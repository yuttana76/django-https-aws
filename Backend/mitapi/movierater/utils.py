
# Python Data Anonymization & Masking Guide
# https://levelup.gitconnected.com/python-data-anonymization-masking-guide-de0b0aa0ca82

from logging import exception
from django.conf import settings
import json
import requests
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string, get_template
from django.db.models import Q

from mitmaster.models import *
from cmpapi.models import *
from cmpapi.serializers import *

from suit2.models import *
from suit2.serializers import *

from datetime import datetime, timezone, timedelta

# class MpamAPI:

#     def mpamApi(payload):
#         try:
#             api_url = settings.MPAM_API_URL
#             authCode = settings.MPAM_API_TOKEN
#             headers = {
#                 'Content-Type': 'application/json',
#                 'Authorization': authCode
#             }
            
#             res = requests.post(api_url, headers=headers,
#                                 data=json.dumps(payload), verify=False)
#             return res.json()
#         except Exception as e:
#             print(e)
#             raise
import os
from azure.storage.blob import BlobServiceClient

class DirectoryClient:
  def __init__(self, connection_string, container_name):
    service_client = BlobServiceClient.from_connection_string(connection_string)
    self.client = service_client.get_container_client(container_name)

  def upload(self, source, dest):
    '''
    Upload a file or directory to a path inside the container
    '''
    if (os.path.isdir(source)):
      self.upload_dir(source, dest)
    else:
      self.upload_file(source, dest)

  def upload_file(self, source, dest):
    '''
    Upload a single file to a path inside the container
    '''
    print(f'Uploading {source} to {dest}')
    with open(source, 'rb') as data:
      self.client.upload_blob(name=dest, data=data)

  def upload_dir(self, source, dest):
    '''
    Upload a directory to a path inside the container
    '''
    prefix = '' if dest == '' else dest + '/'
    prefix += os.path.basename(source) + '/'
    for root, dirs, files in os.walk(source):
      for name in files:
        dir_part = os.path.relpath(root, source)
        dir_part = '' if dir_part == '.' else dir_part + '/'
        file_path = os.path.join(root, name)
        blob_path = prefix + dir_part + name
        self.upload_file(file_path, blob_path)

  def download(self, source, dest):
    '''
    Download a file or directory to a path on the local filesystem
    '''
    if not dest:
      raise Exception('A destination must be provided')

    blobs = self.ls_files(source, recursive=True)
    if blobs:
      # if source is a directory, dest must also be a directory
      if not source == '' and not source.endswith('/'):
        source += '/'
      if not dest.endswith('/'):
        dest += '/'
      # append the directory name from source to the destination
      dest += os.path.basename(os.path.normpath(source)) + '/'

      blobs = [source + blob for blob in blobs]
      for blob in blobs:
        blob_dest = dest + os.path.relpath(blob, source)
        self.download_file(blob, blob_dest)
    else:
      self.download_file(source, dest)

  def download_file(self, source, dest):
    '''
    Download a single file to a path on the local filesystem
    '''
    # dest is a directory if ending with '/' or '.', otherwise it's a file
    if dest.endswith('.'):
      dest += '/'
    blob_dest = dest + os.path.basename(source) if dest.endswith('/') else dest

    print(f'Downloading {source} to {blob_dest}')
    os.makedirs(os.path.dirname(blob_dest), exist_ok=True)
    bc = self.client.get_blob_client(blob=source)
    if not dest.endswith('/'):
        with open(blob_dest, 'wb') as file:
          data = bc.download_blob()
          file.write(data.readall())

  def ls_files(self, path, recursive=False):
    '''
    List files under a path, optionally recursively
    '''
    if not path == '' and not path.endswith('/'):
      path += '/'

    blob_iter = self.client.list_blobs(name_starts_with=path)
    files = []
    for blob in blob_iter:
      relative_path = os.path.relpath(blob.name, path)
      if recursive or not '/' in relative_path:
        files.append(relative_path)
    return files

  def ls_dirs(self, path, recursive=False):
    '''
    List directories under a path, optionally recursively
    '''
    if not path == '' and not path.endswith('/'):
      path += '/'

    blob_iter = self.client.list_blobs(name_starts_with=path)
    dirs = []
    for blob in blob_iter:
      relative_dir = os.path.dirname(os.path.relpath(blob.name, path))
      if relative_dir and (recursive or not '/' in relative_dir) and not relative_dir in dirs:
        dirs.append(relative_dir)

    return dirs

  def rm(self, path, recursive=False):
    '''
    Remove a single file, or remove a path recursively
    '''
    if recursive:
      self.rmdir(path)
    else:
      print(f'Deleting {path}')
      self.client.delete_blob(path)

  def rmdir(self, path):
    '''
    Remove a directory and its contents recursively
    '''
    blobs = self.ls_files(path, recursive=True)
    if not blobs:
      return

    if not path == '' and not path.endswith('/'):
      path += '/'
    blobs = [path + blob for blob in blobs]
    print(f'Deleting {", ".join(blobs)}')
    self.client.delete_blobs(*blobs)


class smsGateWay:

    def __init__(self, msn, msg):
        self.msn = msn
        self.msg = msg

    def converMobileNumbe(self):
        return '66'+self.msn[1:]

    def MpamSmsGW(self):
        try:
            api_url = settings.MPAM_SMSGW_URL
            authCode = settings.MPAM_SMSGW_TOKEN
            headers = {
                'Content-Type': 'application/json',
                'Authorization': authCode
            }
            payload = {
                'client_code': 'mpam01',
                'Msn': self.converMobileNumbe(),
                'Msg': self.msg
            }
            print('SmsGW() > api_url: %s' % (api_url))
            res = requests.post(api_url, headers=headers,
                                data=json.dumps(payload), verify=False,timeout=5)
            return res.json()
        except Exception as e:
            print(e)
            raise


class utils:

    @staticmethod
    def getMasterValue(compCode, refCode):
        try:
            obj = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode=refCode, status='A')
            return obj.nameTh
        except Exception as e:
            print(e)
            return None

    def updateSuit_MITGW(compCode, suitObject):
        print('updateSuit_MITGW()')
        msgRsJSON = {}

        try:

            # # get URL
            api_url = ''
            obj = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='SUIT_API_URL', status='A')
            api_url = obj.nameTh
            cross_compCode = obj.refType

            # # get auth token
            token = ''
            obj = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='SUIT_API_TOKEN',  status='A')
            token = obj.nameTh

            msgRsJSON = utils.patchURL(api_url, token, suitObject)

        except Exception as e:
            return {"code": "999", "message": str(e)}

        return msgRsJSON


    def consentCrossComp(compCode, pk, jsonObject, source_reqRef):
        print('consentCrossComp()')
        msgRsJSON = {"crossComp": []}
        try:

            consentMasObj = mit_cmp_consentmas.objects.filter(
                compCode__iexact=compCode, consStatus='A', crossCompTriger='Y')
            if len(consentMasObj) <= 0:
                msgRsJSON["crossComp"].append(
                    {"code": "003", "message": "No configuration consent cross company role."})

            for obj in jsonObject:
                # Consent master = consent request
                if ((len(consentMasObj) > 0) and consentMasObj[0].id == obj['consentId']) and (obj['respStatus'] == "0"):
                    # if consentMasObj[0].id == obj['consentId']:
                    try:

                        source_consent_result = obj['respStatus']
                        clientObj = mit_client.objects.get(id=pk)
                        cardNumber = clientObj.cardNumber

                        # # get URL
                        api_url = ''
                        obj = mit_master_value.objects.get(
                            compCode__iexact=compCode, refCode='CMP_CONSENT_CROSS_COMP_URL', status='A')
                        api_url = obj.nameTh
                        cross_compCode = obj.refType

                        # # get auth token
                        token = ''
                        obj = mit_master_value.objects.get(
                            compCode__iexact=compCode, refCode='CMP_CONSENT_CROSS_COMP_TOKEN',  status='A')
                        token = obj.nameTh

                        # create payload
                        payload = {
                            "compCode": cross_compCode,
                            "source_compCode": compCode,
                            "source_cardNumber": cardNumber,
                            "source_reqRef": source_reqRef,
                            "source_consent_result": source_consent_result
                        }

                        rsURL = utils.postURL(api_url, token, payload)
                        rsURL.update({"cross_compCode": cross_compCode})

                        msgRsJSON["crossComp"].append(rsURL)

                        # msgRsJSON["crossComp"].append(
                        #     {"code": "0", "cross_compCode": cross_compCode, "message": "Update consent cross comp success"})

                    except Exception as e:
                        msgRsJSON["crossComp"].append(
                            {"code": "999", "cross_compCode": cross_compCode, "message": str(e)})
                        return msgRsJSON

            if len(msgRsJSON['crossComp']) == 0:
                msgRsJSON["crossComp"].append(
                    {"code": "001", "message": "No consent cross company role."})

            return msgRsJSON

        except ObjectDoesNotExist:
            msgRsJSON["crossComp"].append(
                {"code": "003", "message": "Not found config consent cross company role."})
            return msgRsJSON

        except Exception as e:
            msgRsJSON["crossComp"].append(
                {"code": "999", "message": str(e)})
            return msgRsJSON

    def postURL(api_url, token, payload):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token
            }

            res = requests.post(api_url, headers=headers,
                                data=json.dumps(payload), verify=False)

            return res.json()
        except Exception as e:
            print(e)
            raise

    def patchURL(api_url, token, payload):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token
            }

            res = requests.patch(api_url, headers=headers,
                                data=json.dumps(payload), verify=False)

            return res.json()
        except Exception as e:
            print(e)
            raise

    def maskingTxt(text):
        text1 = text[:int(len(text)/2)] + "****"
        return text1

    def getProdEnv():
        PROD_ENV = False

        # Check 1
        try:
            if(settings.PROD):
                # PROD_ENV=True
                # print('getProdEnv(1.1)> %s' %(PROD_ENV))
                return True
        except Exception as e:
            pass

        # Check 2
        if(not PROD_ENV):
            try:
                obj = mit_master_value.objects.get(
                    refCode='SYSTEM_ONPROD', status='A')
                if(obj.nameTh == 'True'):
                    # PROD_ENV=True
                    # print('getProdEnv(2.)> %s' %(obj.nameTh))
                    return True
            except Exception as e:
                print(" SYSTEM_ONPROD %s" % (e))
                return PROD_ENV
        # print('getProdEnv(2)> %s' %(PROD_ENV))
        return PROD_ENV

    def getReqRef(compCode, reqCode, id, channel=''):
        _str1 = 'NONE'
        try:

            # First
            if reqCode.strip().lower() == 'taxrefund':
                _str1 = 'T'
            elif reqCode.strip().lower() == 'consent':
                _str1 = 'C'
            else:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode=reqCode, status='A')

                if obj.refType.strip().lower() == 'cmp_reqCategory'.lower():
                    _str1 = 'R'

                elif obj.refType.strip().lower() == 'wealth'.lower():
                    _str1 = 'W'

            # Second

            if channel.strip().lower() == 'be':
                _str1 = _str1 + '-E-'
            elif channel.strip().lower() == 'api':
                _str1 = _str1 + '-I-'
            else:
                _str1 = _str1 + '-O-'

            return _str1 + str(id).zfill(6)

        except ObjectDoesNotExist:
            pass

        return _str1 + str(id).zfill(6)

    def sendMailInternalProcess(reqObj, sender):
        print('sendMailInternalProcess > %s' % (sender))
        try:

            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(
                reqObj.compCode, "SYSTEM_SERVICE_EMAIL")

            # _refTYpe = "EMAIL_CMP_DPO" if (sender == 'DPO') else 'EMAIL_CMP_OP'
            dear = ''
            _refTYpe = ''
            if sender == 'DPO':
                dear = 'To DPO.'
                _refTYpe = 'EMAIL_CMP_DPO'
            elif sender == 'OP':
                dear = 'To Operation'
                _refTYpe = 'EMAIL_CMP_OP'

            mit_master_valueRs = mit_master_value.objects.get(
                compCode__iexact=reqObj.compCode, refType=_refTYpe, status='A')
            mTo = str(mit_master_valueRs.nameTh).split(',')
            print('mTo:'+str(mTo))

            requestObj = mit_cmp_request.objects.get(reqRef=reqObj.reqRef)
            serializer = CmpRequestSerializer(
                requestObj, many=False, read_only=True)

            c_data = {
                'data': serializer.data,
                'dear': dear
            }

            _subjectTxt = 'PDPA request  เลขที่ '
            if reqObj.reqCode == 'wealthRegister':
                _subjectTxt = 'Merchant Smart Invest register request  เลขที่ '

            _subject = _subjectTxt + \
                reqObj.reqRef + ' '+serializer.data['reqStatusTxt']
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/pdpa_request_process.html', c_data)

            message = EmailMultiAlternatives(
                subject=_subject,
                body="<br> 1 <br>2 <br>3",
                from_email=mFrom,
                to=mTo,
            )
            message.attach_alternative(html_body, "text/html")
            message.send()

            return True
        except Exception as e:
            print('%s' % type(e))
            raise e

    def sendMailTaxInternalProcess(reqObj, sender):
        print('sendMailInternalProcess > %s' % (sender))
        try:

            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(
                reqObj.compCode, "SYSTEM_SERVICE_EMAIL")

            # _refTYpe = "EMAIL_CMP_DPO" if (sender == 'DPO') else 'EMAIL_CMP_OP'
            dear = 'None'
            _refTYpe = 'EMAIL_TAX_OP'
            if sender == 'OP':
                dear = 'To Operation'

            mit_master_valueRs = mit_master_value.objects.get(
                compCode__iexact=reqObj.compCode, refType=_refTYpe, status='A')
            mTo = str(mit_master_valueRs.nameTh).split(',')

            requestObj = mit_cmp_request.objects.get(reqRef=reqObj.reqRef)
            serializer = CmpRequestSerializer(
                requestObj, many=False, read_only=True)

            c_data = {
                'data': serializer.data,
                'dear': dear
            }

            _subject = 'TAX consent เลขที่ ' + \
                reqObj.reqRef + ' '+serializer.data['reqStatusTxt']

            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/pdpa_request_process.html', c_data)

            message = EmailMultiAlternatives(
                subject=_subject,
                body="<br> 1 <br>2 <br>3",
                from_email=mFrom,
                to=mTo,
            )
            message.attach_alternative(html_body, "text/html")
            message.send()

            return True
        except Exception as e:
            print('%s' % type(e))
            raise e

    def sendMailRegisterResult_Finish(reqObj):
        print('sendMailRegisterResult_Finish() %s' % (reqObj.reqRef))
        try:
            # Initial value
            # mFrom = settings.WEALTH_SERVICE_EMAIL
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            # Get request data
            # mit_cmp_requestRs = mit_cmp_request.objects.get(reqRef=reqRef)

            # Get mail from
            # mit_master_valueRs = mit_master_value.objects.get(
            #     compCode__iexact=reqObj.compCode, refType='EMAIL_WEALTH_REGIS_TO')
            # mFrom= mit_master_valueRs.nameTh
            mTo = str(reqObj.custCode.email).split(',')

            compName = 'บลจ.เมอร์ชั่น พาร์ทเนอร์ จำกัด'
            compContact = '02-660-6677'
            appLink = 'https://cpt.merchant.co.th/verifyCID/'+reqObj.compCode+'/consent'

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=reqObj.compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=reqObj.compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            appName = 'Merchant Smart Invest'
            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)
            c_data = {
                'compName': compName,
                'compContact': compContact,
                'compLogoLink': compLogoLink,
                'custName': custFullName,
                'reqRef': reqObj.reqRef,
                'appName': appName,
                'compAddr': compAddr
            }

            # _subject = 'แจ้งผลการการเปิดใช้ระบบ '+appName + ' สำเร็จ'
            _subject = 'บัญชี Merchant Smart Invest ของท่านพร้อมเริ่มลงทุน'

            html_body = render_to_string(
                'mail/wealth_regis_finish_tmp.html', c_data)
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

    def sendMailTaxResult_Finish(reqObj):
        print('sendMailTaxResult_Finish() %s' % (reqObj.reqRef))
        try:
            # Initial value
            # mFrom = settings.WEALTH_SERVICE_EMAIL
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            # Get request data
            # mit_cmp_requestRs = mit_cmp_request.objects.get(reqRef=reqRef)

            # Get mail from
            # mit_master_valueRs = mit_master_value.objects.get(
            #     compCode__iexact=reqObj.compCode, refType='EMAIL_WEALTH_REGIS_TO')
            # mFrom= mit_master_valueRs.nameTh
            mTo = str(reqObj.custCode.email).split(',')

            compName = 'บลจ.เมอร์ชั่น พาร์ทเนอร์ จำกัด'
            compContact = '02-660-6677'
            appLink = 'https://cpt.merchant.co.th/verifyCID/'+reqObj.compCode+'/consent'

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=reqObj.compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=reqObj.compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            appName = 'Merchant Smart Invest'
            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)
            c_data = {
                'compName': compName,
                'compContact': compContact,
                'compLogoLink': compLogoLink,
                'custName': custFullName,
                'reqRef': reqObj.reqRef,
                'appName': appName,
                'compAddr': compAddr
            }

            _subject = 'การแจ้งความประสงค์ขอใช้สิทธิลดหย่อนภาษี'

            html_body = render_to_string(
                'mail/taxConsent_finish.html', c_data)
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

    def sendMail_reminderRequestOnporcess(compCode):
        print('sendMail_reminderRequestOnporcess() %s ' % (compCode))
        try:

            mit_cmp_requestQueryset = mit_cmp_request.objects.filter(compCode__iexact=compCode) \
                .filter(Q(reqCode='access') | Q(reqCode='rectification') | Q(reqCode='erasure') |
                        Q(reqCode='dataportability') | Q(reqCode='rightToObject') | Q(reqCode='restrictProcess') | Q(reqCode='consent')) \
                .filter(~Q(reqStatus='finish'))\
                .filter(~Q(reqStatus='reject'))\
                .order_by('createDate')

            serializer = CmpRequestSerializer(
                mit_cmp_requestQueryset, many=True)

            # Data = 0 no need send mail
            # if (len(serializer.data) <= 0):
            #     return 0

            # from datetime import datetime, timezone
            currentDateFormat = datetime.now().strftime("%d/%m/%Y")

            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            # Get mail
            _toMail_dpo = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')

            _toMail_op = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_OP', status='A')

            _toMail = ",".join([_toMail_dpo.nameTh, _toMail_op.nameTh])
            print("TO:"+_toMail)
            mTo = str(_toMail).split(',')

            appName = compCode+':PDPA Reminder Request report on ' + currentDateFormat
            data = {
                'compCode': compCode,
                'currentDate': currentDateFormat,
                'appName': appName,
                'dataList': serializer.data,
            }
            _subject = appName
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/pdpa_reminder_request_report.html', data)
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
            print('%s' % e)
            raise e

    def sendMail_reminderWealthRegitration(compCode):
        print('sendMail_reminderWealthRegitration %s ' % (compCode))
        try:

            excludeList = ['finish', 'reject']
            queryset = mit_cmp_request.objects.filter(compCode__iexact=compCode).filter(
                reqCode='wealthRegister').exclude(reqStatus__in=excludeList).order_by('createDate')
            serializer = CmpRequestSerializer(queryset, many=True)

            # No data. Don't send mail
            if (len(serializer.data) <= 0):
                return 0

            # from datetime import datetime, timezone
            currentDateFormat = datetime.now().strftime("%d/%m/%Y")

            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            # Get mail from
            _toMail = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_WEALTH_REGIS_TO', status='A')
            mTo = str(_toMail.nameTh).split(',')

            appName = compCode+' :Merchant Smart Wealth Registration report on ' + currentDateFormat
            data = {
                'compCode': compCode,
                'currentDate': currentDateFormat,
                'appName': appName,
                'dataList': serializer.data,
            }
            _subject = appName
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string('mail/wealth_regis_report.html', data)
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

    def reminderTaxConsent(compCode):
        print('reminderTaxConsent %s ' % (compCode))
        try:

            queryset = mit_cmp_request.objects.filter(compCode__iexact=compCode).filter(
                reqCode='taxrefund', reqStatus='onprocess').order_by('createDate')
            serializer = CmpRequestSerializer(queryset, many=True)

            # No data. Don't send mail
            if (len(serializer.data) <= 0):
                return 0

            # from datetime import datetime, timezone
            currentDateFormat = datetime.now().strftime("%d/%m/%Y")

            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            # Get mail from
            _toMail = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_TAX_OP', status='A')
            mTo = str(_toMail.nameTh).split(',')

            _subject = compCode+' :Tax consent remind on ' + currentDateFormat
            data = {
                'compCode': compCode,
                'currentDate': currentDateFormat,
                'dataList': serializer.data,
            }
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/taxConsent_remind_report.html', data)
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

    def sendMail_ConsentDialy(compCode):
        print('sendMail_ConsentDialy %s ' % (compCode))
        try:
            from django.db.models import Count

            # T-1
            today = datetime.now()
            n_days_ago = today - timedelta(days=1)

            # # Get request data
            req_exclude = [('wealthRegister')]
            requestsSet = mit_cmp_request.objects.filter(Q(createDate__date=n_days_ago.date()) | Q(updateDate__date=n_days_ago.date())).exclude(reqCode__in=req_exclude)\
                .order_by('createDate', 'updateDate')
            requests_serializer = CmpRequestSerializer(
                requestsSet, many=True)

            # Get  consent data (No2 only)
            consentQueryset = mit_cmp_Response.objects.filter(Q(createDate__date=n_days_ago.date()) | Q(updateDate__date=n_days_ago.date()))\
                .distinct('custCode_id')
            consentsLast_serializer = CmpResponseDialyReportSerializer(
                consentQueryset, many=True)

            # from datetime import datetime, timezone
            currentDateFormat = datetime.now().strftime("%d/%m/%Y")

            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            # Get mail
            _toMail_dpo = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')

            _toMail_op = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_OP', status='A')

            _toMail = ",".join([_toMail_dpo.nameTh, _toMail_op.nameTh])
            print('TO=' + _toMail)
            mTo = str(_toMail).split(',')

            appName = compCode + \
                ' :PDPA Consent Dialy report(T-1) on ' + currentDateFormat
            data = {
                'compCode': compCode,
                'currentDate': currentDateFormat,
                'appName': appName,

                'consentsLast': consentsLast_serializer.data,
                'consentsNo2': consentsLast_serializer.data,
                'requests': requests_serializer.data,

            }
            _subject = appName
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/pdpa_consent_dialy_report.html', data)
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

    def sendMailPDPARequestRSP_Autoapprove(reqObj):
        print('sendMailPDPARequestRSP() %s' % (reqObj))
        try:
            # Initial value
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            mTo = str(reqObj.custCode.email).split(',')
            print(str(mTo))

            # compAppLink = 'https://cpt.merchant.co.th/verifyCID/'+reqObj.compCode+'/consent'

            compCode = reqObj.compCode

            # Get application link
            compAppLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='CMP_APP_LINK', status='A')
                compAppLink = obj.nameTh
            except Exception:
                print('Get Master compAppLink Not found')

            # Get company name (th)
            compName = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception:
                print('Get Master COMP_NAME Not found')

            # Get DPO email address
            compContact_dpo_mail = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
                compContact_dpo_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_DPO Not found')

            # Get DPO tel
            compContact_dpo_tel = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_DPO_TEL', status='A')
                compContact_dpo_tel = obj.nameTh
            except Exception:
                print('Get Master COMP_DPO_TEL Not found')

            # Get company address
            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            # Get company logo
            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            # Get customer name
            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)

            reportObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqObj.reqRef)
            serializer = CmpRequestSerializer(reportObj, many=False)

            _subject = 'แจ้งผลการให้ความยินยอมของลูกค้า'
            c_data = {
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'compContact_dpo_mail': compContact_dpo_mail,
                'compContact_dpo_tel': compContact_dpo_tel,
                'compAppLink': compAppLink,
                'custName': custFullName,
                'reqObj': serializer.data,
                'subject': _subject,
            }

            html_body = render_to_string(
                'mail/pdpaRequest_ResponseAutoapprove.html', c_data)
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
        

    def sendMailPDPARequestRSP(reqObj):
        print('sendMailPDPARequestRSP() %s' % (reqObj))
        try:
            # Initial value
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            mTo = str(reqObj.custCode.email).split(',')
            print(str(mTo))

            # compAppLink = 'https://cpt.merchant.co.th/verifyCID/'+reqObj.compCode+'/consent'

            compCode = reqObj.compCode

            compAppLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='CMP_APP_LINK', status='A')
                compAppLink = obj.nameTh
            except Exception:
                print('Get Master compAppLink Not found')

            compName = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception:
                print('Get Master COMP_NAME Not found')

            compContact_dpo_mail = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
                compContact_dpo_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_DPO Not found')

            compContact_dpo_tel = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_DPO_TEL', status='A')
                compContact_dpo_tel = obj.nameTh
            except Exception:
                print('Get Master COMP_DPO_TEL Not found')

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)

            reportObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqObj.reqRef)
            serializer = CmpRequestSerializer(reportObj, many=False)

            _subject = 'แจ้งผลการขอใช้สิทธิในข้อมูลส่วนบุคคล'
            c_data = {
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'compContact_dpo_mail': compContact_dpo_mail,
                'compContact_dpo_tel': compContact_dpo_tel,
                'compAppLink': compAppLink,
                'custName': custFullName,
                'reqObj': serializer.data,
                'subject': _subject,
            }

            html_body = render_to_string(
                'mail/pdpaRequest_Response.html', c_data)
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

    def sendMailPDPARequestRSP_reject(reqObj):
        print('sendMailPDPARequestRSP_reject() %s' % (reqObj))
        try:
            # Initial value
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            mTo = str(reqObj.custCode.email).split(',')
            print(str(mTo))

            # compAppLink = 'https://cpt.merchant.co.th/verifyCID/'+reqObj.compCode+'/consent'

            compCode = reqObj.compCode

            compAppLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='CMP_APP_LINK', status='A')
                compAppLink = obj.nameTh
            except Exception:
                print('Get Master compAppLink Not found')

            compName = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception:
                print('Get Master COMP_NAME Not found')

            compContact_dpo_mail = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
                compContact_dpo_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_DPO Not found')

            compContact_dpo_tel = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_DPO_TEL', status='A')
                compContact_dpo_tel = obj.nameTh
            except Exception:
                print('Get Master COMP_DPO_TEL Not found')

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)

            reportObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqObj.reqRef)
            serializer = CmpRequestSerializer(reportObj, many=False)

            respMailText = reqObj.respMailText
            if not respMailText or respMailText == "":
                if reportObj.reqCode == 'erasure':
                    tmpid = 'TMP7'
                else:
                    tmpid = 'TMP1-6'

                try:
                    obj = mit_master_value.objects.get(
                        compCode__iexact=compCode, refType='CMP_REQ_REJECT_TMP', refCode=tmpid, status='A')
                    respMailText = obj.nameTh
                except Exception:
                    pass

            _subject = 'การปฏิเสธคำขอใช้สิทธิของลูกค้า'
            c_data = {
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'compContact_dpo_mail': compContact_dpo_mail,
                'compContact_dpo_tel': compContact_dpo_tel,
                'compAppLink': compAppLink,
                'custName': custFullName,
                'reqObj': serializer.data,
                'subject': _subject,
                'respMailText': respMailText
            }

            html_body = render_to_string(
                'mail/pdpaRequest_ResponseReject.html', c_data)
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

    def sendMailPDPARequest_ToClientOnCreate(reqObj):
        print('sendMailPDPARequest() %s' % (reqObj))
        try:
            # Initial value
            # mFrom = settings.WEALTH_SERVICE_EMAIL
            mFrom = utils.getMasterValue(
                reqObj.compCode, "WEALTH_SERVICE_EMAIL")

            # Get request data
            # mit_cmp_requestRs = mit_cmp_request.objects.get(reqRef=reqRef)

            # Get mail from
            # mit_master_valueRs = mit_master_value.objects.get(compCode__iexact=reqObj.compCode, refType='EMAIL_WEALTH_REGIS_TO')
            # mFrom= mit_master_valueRs.nameTh
            mTo = str(reqObj.custCode.email).split(',')

            compCode = reqObj.compCode
            # compAppLink = 'https://cpt.merchant.co.th/verifyCID/'+compCode+'/consent'

            compName = '<COMP_NAME>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception as e:
                print(e)
                print('Get Master COMP_NAME Not found ')

            compAppLink = '<CMP_APP_LINK>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='CMP_APP_LINK', status='A')
                compAppLink = obj.nameTh
            except Exception as e:
                print(e)
                print('Get Master CMP_APP_LINK Not found ')

            compContact_dpo_mail = '<EMAIL_CMP_DPO>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
                compContact_dpo_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_DPO Not found')

            compContact_dpo_tel = '<COMP_DPO_TEL>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_DPO_TEL', status='A')
                compContact_dpo_tel = obj.nameTh
            except Exception:
                print('Get Master COMP_DPO_TEL Not found')

            compAddr = '<COMP_ADDR>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '<COMP_LOGO_LINK>'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            custFullName = utils.maskingTxt(
                reqObj.custCode.thFirstName) + ' ' + utils.maskingTxt(reqObj.custCode.thLastName)

            reportObj = mit_cmp_request.objects.get(
                reqRef__iexact=reqObj.reqRef)
            serializer = CmpRequestSerializer(reportObj, many=False)

            proc_day = '30'
            if str(reportObj.reqCode).lower() == 'consent':
                proc_day = '15'

            _subject = 'แจ้งสถานะการขอใช้สิทธิในข้อมูลส่วนบุคคล '
            c_data = {
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'compContact_dpo_mail': compContact_dpo_mail,
                'compContact_dpo_tel': compContact_dpo_tel,
                'compAppLink': compAppLink,
                'custName': custFullName,
                'reqObj': serializer.data,
                'proc_day': proc_day,
                'subject': _subject,
            }

            html_body = render_to_string(
                'mail/pdpaRequest_ToClientOnCreate.html', c_data)
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

    def sendMail_ConsentRepose(compCode, data):
        print('sendMail_ConsentRepose %s' % (data))

        try:

            # from datetime import datetime, timezone
            currentDateFormat = datetime.now().strftime("%d/%m/%Y")

            compName = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception:
                print('Get Master COMP_NAME Not found')

            compContact_dpo_mail = ''
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
                compContact_dpo_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_DPO Not found')

            op_mail = ''
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='EMAIL_CMP_OP', status='A')
                op_mail = obj.nameTh
            except Exception:
                print('Get Master EMAIL_CMP_OP Not found')

            compContact_dpo_tel = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_DPO_TEL', status='A')
                compContact_dpo_tel = obj.nameTh
            except Exception:
                print('Get Master COMP_DPO_TEL Not found')

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            custFullName = utils.maskingTxt(
                data.thFirstName) + ' ' + utils.maskingTxt(data.thLastName)

            # Initial value
            # mFrom = settings.WEALTH_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "WEALTH_SERVICE_EMAIL")
            mTo = str(data.email).split(',')
            bccTo = []
            compAppLink = 'https://cpt.merchant.co.th/verifyCID/'+compCode+'/consent'

            # if len(compContact_dpo_mail) > 0:
            #     dpo_mail_list = compContact_dpo_mail.split(",")
            #     bccTo += dpo_mail_list

            # if len(op_mail) > 0:
            #     op_mail_list = op_mail.split(",")
            #     bccTo += op_mail_list

            _subject = 'แจ้งผลการขอใช้สิทธิในข้อมูลส่วนบุคคล'
            mailContext = {
                'compCode': compCode,
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'compAppLink': compAppLink,
                'compContact_dpo_mail': compContact_dpo_mail,
                'compContact_dpo_tel': compContact_dpo_tel,
                'currentDate': currentDateFormat,
                'custName': custFullName,
                'data': data,
                'subject': _subject,
            }

            html_body = render_to_string(
                'mail/pdpaRequest_Response.html', mailContext)

            message = EmailMultiAlternatives(
                subject=_subject,
                body="mail testing",
                from_email=mFrom,
                to=mTo,
                bcc=bccTo
            )
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)

            return True
        except Exception as e:
            print('%s' % type(e))
            raise e

    def sendMail_ConsentCrossComp(compCode, message):
        print('sendMail_ConsentCrossComp() >' + message)

        try:
            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            compName = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refType='COMP_NAME', refCode__iexact=compCode, status='A')
                compName = obj.nameTh
            except Exception:
                print('Get Master COMP_NAME Not found')

            compAddr = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_ADDR', status='A')
                compAddr = obj.nameTh
            except Exception:
                print('Get Master COMP_ADDR Not found')

            compLogoLink = '-'
            try:
                obj = mit_master_value.objects.get(
                    compCode__iexact=compCode, refCode='COMP_LOGO_LINK', status='A')
                compLogoLink = obj.nameTh
            except Exception:
                print('Get Master COMP_LOGO_LINK Not found')

            # Get mail from
            _toMail = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_DPO', status='A')
            mTo = str(_toMail.nameTh).split(',')

            _toMail = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='EMAIL_CMP_OP', status='A')
            mTo = mTo+str(_toMail.nameTh).split(',')

            data = {
                'compCode': compCode,
                'compName': compName,
                'compAddr': compAddr,
                'compLogoLink': compLogoLink,
                'message': message,
            }
            _subject = 'PDPA:Consent was change by cross company rule.'
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/pdpa_consent_cross_comp.html', data)
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

    def sendWealthRegister(obj):
        try:
            # Initial value
            # mFrom = settings.EMAIL_CLIENT_FROM
            mFrom = utils.getMasterValue(obj.compCode, "SYSTEM_SERVICE_EMAIL")

            request = mit_master_value.objects.get(
                compCode__iexact=obj.compCode, refType='EMAIL_WEALTH_REGIS_TO')
            mTo = str(request.nameEn).split(',')
            bccTo = []

            c_data = {
                'requestor': obj.custCode,
                # 'reqTopic':  obj.reqTopic,
                'reqDetail': obj.reqDetail,
                'reqReasonText': obj.reqReasonText,
                'reqReasonChoice': obj.reqReasonChoice,
                'reqAccounts': obj.reqAccounts,
                'createDate': obj.createDate,
                'reqRef': obj.reqRef,
            }

            _subject = 'Ref:' + obj.reqRef + \
                ' [C-Portal] Merchant smart invest register.'
            if(not settings.PROD):
                _subject = '[Develop]' + _subject

            html_body = render_to_string('mail/wealth_regis.html', c_data)
            message = EmailMultiAlternatives(
                subject=_subject,
                body="mail testing",
                from_email=mFrom,
                to=mTo,
                bcc=bccTo,
            )
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)

            return True
        except Exception as e:
            print('%s' % type(e))
            raise e

    def sendMail_SuitDialyReport(compCode):
        print('sendMail_SuitDialyReport %s ' % (compCode))
        try:

            today = datetime.now()
            n_days_ago = today - timedelta(days=1)

            # # Get data
            suitDataSet = suitability.objects.filter(compCode__iexact=compCode,status__iexact='A').filter(Q(createDT__date=n_days_ago.date())).order_by('createDT')
            suitData_serializer = suitabilitySerializerCustomV3(suitDataSet, many=True)

            # E-mail parameter
            # from datetime import datetime, timezone
            # currentDateFormat = datetime.now().strftime("%d/%m/%Y")
            currentDateFormat = n_days_ago.strftime("%d/%m/%Y")

            # Initial value
            # mFrom = settings.SYSTEM_SERVICE_EMAIL
            mFrom = utils.getMasterValue(compCode, "SYSTEM_SERVICE_EMAIL")

            # Get mail
            mail_to = mit_master_value.objects.get(
                compCode__iexact=compCode, refCode='SUIT_DIALY_REPRT_EMAIL_TO', status='A')

            
            _toMail = ",".join([mail_to.nameTh])
            print('TO=' + _toMail)
            mTo = str(_toMail).split(',')

            appName = compCode + \
                ' Suitability Dialy report(T-1) on ' + currentDateFormat
            data = {
                'compCode': compCode,
                'currentDate': currentDateFormat,
                'appName': appName,
                'suitDialyList': suitData_serializer.data,
            }
            _subject = appName
            if(not utils.getProdEnv()):
                _subject = '[Develop]' + _subject

            html_body = render_to_string(
                'mail/suit_dialy_report.html', data)
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