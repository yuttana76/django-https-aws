from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response

from .models import *
from .serializers import *

from movierater.utils import *
from mitmaster.models import mit_client

from django.utils import timezone
from datetime import datetime, timezone as dt_timezone

def calculateSuitLevel(score):
    print("*** calculateSuitLevel: %s"%(score))
    try:
        if int(score) <15:
            return '1'
        elif int(score) >=15 and int(score) <=21:
            return '2'
        elif int(score) >=22 and int(score) <=29:
            return '3'
        elif int(score) >=30 and int(score) <=36:
            return '4'
        elif int(score) >=37:
            return '5'
        else:
            return 'N/A'
    except Exception as e:
        print(str(e))
        return 'N/A'
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_suit(request):


    user = request.user
    filters = {}
    client = mit_client.objects.filter(user=user).first()
    filters['cardNumber'] = client.cardNumber
    suit = suitability.objects.filter(**filters).order_by('status','-createDT')

    if not suit:
        return Response([], status=status.HTTP_404_NOT_FOUND)
    
    serializer = suitabilitySerializerCustomV2(suit, many=True)
    return Response({"results":serializer.data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createSuit(request):

    user = request.user
    client = mit_client.objects.filter(user=user).first()

    compCode = ''
    if 'compCode' in request.data:
        compCode = request.data['compCode']
    else:
        return Response({'message': 'Request comp code.'}, status=status.HTTP_400_BAD_REQUEST)

    cardNumber = client.cardNumber

    custType = ''
    if 'custType' in request.data:
        custType = request.data['custType']

    docVersion = ''
    if 'docVersion' in request.data:
        docVersion = request.data['docVersion']

    score = ''
    if 'score' in request.data:
        score = request.data['score']

    suitLevel = ''
    if 'suitLevel' in request.data:
        suitLevel = request.data['suitLevel']

    jsonData = ''
    if 'jsonData' in request.data:
        jsonData = request.data['jsonData']

    channel = ''
    if 'channel' in request.data:
        channel = request.data['channel']

    actionBy = ''
    if 'actionBy' in request.data:
        actionBy = request.data['actionBy']

    evaluateDate = timezone.now()
    if 'evaluateDate' in request.data:
        try:
            
            evaluateDate = datetime.strptime(request.data['evaluateDate'],'%d-%m-%Y')
            
        except Exception as e:
            print(e)
            return Response({'message': 'evaluateDate invalid format dd-mm-yyyy'}, status=status.HTTP_400_BAD_REQUEST)


    # Update suit to inactive
    _status='A'  
    gwRS="N/A"
    try:
        
        dataList = suitability.objects.filter(compCode__iexact=compCode, cardNumber=cardNumber,status='A')
        
        for data in dataList:

            # New evaludate is equal or greater STATUS will be 'A'
            # exist evaludate is less STATUS will be 'I'
            data_evaluateDate = data.evaluateDate.replace(tzinfo=None)
            days = abs((data_evaluateDate - evaluateDate).days)
        
            # if   evaluateDate >= data.evaluateDate:
            if days <= 1:
                _status = 'A'
                data.status='I'
                data.updateBy=actionBy
                data.updateDT=timezone.now()
                data.save()
                       
            else:
                _status = 'I'
        
    except exception as e:
        print ('!ERROR: data more than one rec.',e)
        pass
    
    # Caculate suit level (no suit level value)
    if score and not suitLevel:
        suitLevel = calculateSuitLevel(score)

    # Create new suit data
    newData = suitability.objects.create(compCode=compCode
            ,cardNumber=cardNumber
            ,custType=custType
            ,docVersion=docVersion
            ,status=_status
            ,score=score
            ,suitLevel=suitLevel
            ,evaluateDate=evaluateDate
            ,jsonData=jsonData
            ,channel=channel
            ,createBy=actionBy
            )
    
    # Update suit fundConnext pass MIT gatway
    if channel!="MIT-API":
        suitJSON={
                "identificationCardType": "CITIZEN_CARD",
                "cardNumber": cardNumber,
                "suitabilityRiskLevel":suitLevel,
                "suitabilityEvaluationDate":evaluateDate.strftime('%Y%m%d'),
                "suitabilityForm":jsonData
                }

        gwRS = utils.updateSuit_MITGW(compCode,suitJSON)

    # Return data
    serializerData = suitabilitySerializerCustom(newData, many=False)
    responsMsg = serializerData.data

    # Add reponse FCN Suit MIT API
    responsMsg['MIT_FCN_API'] = gwRS

    return Response(responsMsg, status=status.HTTP_200_OK)
