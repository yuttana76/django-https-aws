from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.authtoken.models import Token

from cmpapi.models import mit_cmp_Response
from cmpapi.serializers import *


class MitClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = mit_client
        fields = '__all__'

class MitClientTokenSerializer(serializers.ModelSerializer):
    class  Meta:
        model = mit_client
        fields = ('compCode','enFirstName','enLastName')


class MitClientSerializerShort(serializers.ModelSerializer):

    consentResponse = CmpResponseSerializer(many=True, read_only=True)
    # clientRequest = CmpRequestSerializer(many=True, read_only=True)
    clientRequest = serializers.SerializerMethodField("getClientRequest")
    hasConsentReq = serializers.SerializerMethodField("getConsentReq")

    class Meta:
        model = mit_client
        fields = ('compCode', 'id', 'cardNumber', 'title', 'titleOther', 'enFirstName', 'enLastName', 'thFirstName', 'thLastName', 'email',
                  'phone', 'products', 'channel', 'createBy', 'createDate', 'updateBy', 'updateDate', 'hasConsentReq', 'consentResponse', 'clientRequest')
        # fields = ('compCode','id','title','titleOther','enFirstName','enLastName','thFirstName','thLastName','products','clientRequest')
        # fields = '__all__'

    def getClientRequest(self, mit_client):
        try:
            reqCode = ['consent', 'access', 'rectification', 'erasure',
                       'dataportability', 'rightToObject', 'restrictProcess']
            requestRs = mit_cmp_request.objects.filter(
                custCode=mit_client, reqCode__in=reqCode).order_by('createDate')

            return CmpRequestSerializer(requestRs, many=True).data
        except Exception as e:
            print(e)
            return None

    def getConsentReq(self, mit_client):
        try:
            requestRs = mit_cmp_request.objects.filter(
                compCode__iexact=mit_client.compCode, custCode=mit_client, reqCode='consent', reqStatus='waitApprove')

            return len(requestRs)
        except Exception as e:
            print(e)
            return 'N'


class MasterValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = mit_master_value
        fields = '__all__'


class MasterValueShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = mit_master_value
        fields = ('refCode', 'nameTh', 'nameEn', 'seq')
