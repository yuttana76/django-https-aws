from django.conf import settings
from django.http import FileResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response

from .models import mit_master_value
from cmpapi.views import CmpConsentViewSet
from .serializers import *

from movierater.utils import *

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clientinfo(request):
    
    print("*** get_clientinfo with user:" , request.user)
    user = request.user
    
    client = mit_client.objects.filter(user=user).first()
    serializer = MitClientSerializerShort(client, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cmpSubjectRequest(request):
    print("*** cmpSubjectRequest user:", request.user)
    print("cmpSubjectRequest data:", request.data)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submitrequest(request):

    print("*** cmpSubjectRequest user:", request.user)
    print("cmpSubjectRequest data:", request.data)

    if 'compcode' in request.data :

        user = request.user    
        client = mit_client.objects.filter(user=user).first()
        pk = client.id

        compcode = request.data['compcode']
        reqCode = request.data['reqcode']
        reqDetail = request.data['reqDetail']

        reqReasonText = ''
        if 'reqReasonText' in request.data:
            reqReasonText = request.data['reqReasonText']

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gettaxlatest(request):
    print(request.query_params)

    try:
        user = request.user
        client = mit_client.objects.get(user=user)
    except ObjectDoesNotExist:
        return Response("Not found client.", status=status.HTTP_200_OK)

    taxRequest = mit_cmp_request.objects.filter(
        reqCode='taxrefund', reqStatus__in=(('finish'), ('onprocess')), custCode=client).order_by('-createDate')[:1]
    # taxRequest = mit_cmp_request.objects.filter(
    #     reqCode='taxrefund', custCode=client, reqStatus='finish').order_by('-updateDate')[:1]

    print(taxRequest)

    return Response(taxRequest[0].reqDetail if len(taxRequest) > 0 else "0", status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def getPFreportsbycid(request):
    import json

    try:
        user = request.user

        client = mit_client.objects.get(user=user)
        cid = client.cardNumber

        client = DirectoryClient(CONNECTION_STRING, CONTAINER_NAME)
        files = client.ls_files(cid)

        json_object = [{"name": item} for item in files]

        return Response(json_object, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        response = {'code': '999', 'message': 'Application exception'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def downloadPFreport(request):
    try:

        user = request.user
        client = mit_client.objects.get(user=user)


        cid = client.cardNumber
        fileName = request.data.get('fileName')

        client_drv = DirectoryClient(CONNECTION_STRING, CONTAINER_NAME)
        # print(f'*** CID:{cid} ; FILE NAME:{fileName}')
        # Download file form Azuer and store in /downloads folder.
        client_drv.download(f'{cid}/{fileName}', f'downloads/{fileName}')

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
def getShowPortReports(request):
    try:

        compCode = request.query_params.get('compCode')

        print(f' **getShowPortReports() compCode ={compCode}')
        queryset = mit_master_value.objects.filter(
            compCode__iexact=compCode, refType='PORTFOLIO',refCode='SHOW_PORTFOLIO_APP')
        
        serializer = MasterValueSerializer(queryset, many=True, read_only=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        response = {'code': '999', 'message': 'Application exception'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
