from rest_framework import serializers
from .models import *
from mitmaster.models import mit_client
from movierater.const import *


class suitabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = suitability
        fields = '__all__'

class suitabilitySerializerCustom(serializers.ModelSerializer):
    # suitHistory = serializers.SerializerMethodField("getSuitHistory")
    # custCode_cardNumber = serializers.RelatedField(source='custCode', read_only=True)
    evaluateDate = serializers.DateTimeField(format="%d-%m-%Y")
    createDT = serializers.DateTimeField(format="%d-%m-%Y")
    class Meta:
        model = suitability
        fields = ('compCode', 'cardNumber','custType','status',
                  'score', 'suitLevel', 'evaluateDate','channel','createDT','jsonData')

class suitabilitySerializerCustomV2(serializers.ModelSerializer):
    evaluateDate = serializers.DateTimeField(format="%d-%m-%Y")
    createDT = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        model = suitability
        fields = ('compCode', 'cardNumber','custType','status',
                  'score', 'suitLevel', 'evaluateDate','channel','createDT','jsonData')

class suitabilitySerializerCustomV3(serializers.ModelSerializer):
    custName = serializers.SerializerMethodField("getClientName")
    evaluateDate = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        model = suitability
        fields = ('compCode', 'cardNumber','custName','custType','status',
                  'score', 'suitLevel', 'evaluateDate')

    def getClientName(self, suit):
        try:

            print('*** Get client id:  '+ suit.cardNumber) 

            objectData = mit_client.objects.get(compCode__iexact=suit.compCode,
                cardNumber=suit.cardNumber)

            fullName = const.maskingTxt(objectData.thFirstName) + \
                ' ' + const.maskingTxt(objectData.thLastName)

            return fullName
        except Exception as e:
            print(e)
            return ''