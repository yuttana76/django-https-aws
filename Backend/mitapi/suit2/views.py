from django.shortcuts import render
from django.conf import settings

from django.db import DatabaseError, transaction
from datetime import datetime,timedelta
 
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView, exception_handler
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import *
from .serializers import *

from mitmaster.models import mit_client

# from movierater.utils import updateSuit_MITGW
from movierater.utils import *

from django.utils import timezone

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

# (mixins.CreateModelMixin, 
#                    mixins.RetrieveModelMixin, 
#                    mixins.UpdateModelMixin,
#                    mixins.DestroyModelMixin,
#                    mixins.ListModelMixin,
#                    GenericViewSet)

# class suitViewSet(viewsets.ModelViewSet):
class suitViewSet(mixins.RetrieveModelMixin,mixins.ListModelMixin,
viewsets.GenericViewSet):
    queryset = suitability.objects.all()
    serializer_class = suitabilitySerializerCustomV2
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['GET'])
    def test(self, request, pk=None):

        custList = suitability.objects.filter().exclude(score__isnull=True)
        for cust in custList:
            _suitLevel = calculateSuitLevel(cust.score)
            print("** %s %s %s" % (cust.cardNumber,cust.score,_suitLevel))

        print(custList.count())

        return Response({"ok"}, status=status.HTTP_200_OK)


    # Override 
    # List by evaludate date
    def get_queryset(self):

        filters = {}
        compCode = self.request.query_params.get('compCode')
        cardNumber = self.request.query_params.get('cardNumber')
        custType = self.request.query_params.get('custType')

        filters['compCode__iexact'] = compCode
        filters['cardNumber'] = cardNumber
        filters['custType'] = custType

        return suitability.objects.filter(**filters).order_by('status','-createDT')

    
    def create(self, request):
        print('***Create here!')

        compCode = ''
        if 'compCode' in request.data:
            compCode = request.data['compCode']
        else:
            return Response({'message': 'Request comp code.'}, status=status.HTTP_400_BAD_REQUEST)

        cardNumber = ''
        if 'cardNumber' in request.data:
            cardNumber = request.data['cardNumber']
        else:
            return Response({'message': 'Request card number.'}, status=status.HTTP_400_BAD_REQUEST)

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
        _status='A'  # Not define
        gwRS="N/A"
        try:
            
            print("*** DATA  %s:%s",(compCode,cardNumber) )

            data = suitability.objects.get(compCode__iexact=compCode, cardNumber=cardNumber,status='A')

            # New evaludate is equal or greater STATUS will be 'A'
            # exist evaludate is less STATUS will be 'I'
            if   evaluateDate >= data.evaluateDate:
                _status = 'A'
                data.status='I'
                data.updateBy=actionBy
                data.updateDT=timezone.now()
                data.save()

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
                    print(" *** MIT API >%s"%(gwRS))        

            else:
                _status = 'I'
            
        except:
            print ('!ERROR: data more than one rec.')
            pass
        
        # Caculate suit level (no suit level value)
        if score and not suitLevel:
            suitLevel = calculateSuitLevel(score)

        print('***evaluateDate:'+request.data['evaluateDate'])
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

        # Return data
        serializerData = suitabilitySerializerCustom(newData, many=False)
        responsMsg = serializerData.data

        # Add reponse FCN Suit MIT API
        responsMsg['MIT_FCN_API'] = gwRS

        return Response(responsMsg, status=status.HTTP_200_OK)
        # return Response({}, status=status.HTTP_200_OK)


class suitListViewSet(viewsets.ModelViewSet):
    queryset = suitability.objects.all()
    serializer_class = suitabilitySerializerCustom
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override 
    # List by evaludate date
    def get_queryset(self):

        compCode = self.request.query_params.get('compCode')

        filters = {}
        filters['compCode__iexact'] = compCode
        filters['status__exact'] = 'A'
        if((self.request.query_params.get('startDate') != None) and (self.request.query_params.get('endDate') != None)):
            try:
                from datetime import datetime, timedelta

                fromDate = datetime.strptime(
                    self.request.query_params.get('startDate'), '%d-%m-%Y').date()
                toDate = datetime.strptime(
                    self.request.query_params.get('endDate'), '%d-%m-%Y').date()
                toDate = toDate + timedelta(days=1)

                filters['createDT__range'] = (fromDate, toDate)
            except Exception as e:
                filters['id'] = 0
        else:
            filters['id'] = 0

        print('filters=%s ' %(filters))

        return suitability.objects.filter(**filters).order_by('createDT')


class suitExpireViewSet(viewsets.ModelViewSet):
    queryset = suitability.objects.all()
    serializer_class = suitabilitySerializerCustom
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    # Override 
    def get_queryset(self):

        compCode = self.request.query_params.get('compCode')
        expday = self.request.query_params.get('expday')
        
        return suitability.objects.filter(compCode__iexact=compCode,status__exact='A',evaluateDate__lte=datetime.now()-timedelta(days=int(expday))).order_by('-evaluateDate')