from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import *
# from movierater.utils import *
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from mitmaster.models import mit_master_value
import pytz
from movierater.const import *
# from movierater.utils import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
        depth = 2

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user


class CmprequestCFGSerializer(serializers.ModelSerializer):
    class Meta:
        model = mit_cmp_requestCFG
        fields = '__all__'


class CmpConsentMasSerializer(serializers.ModelSerializer):
    # subjectRights = CmprequestCFGSerializer(many=True, read_only=True)

    class Meta:
        model = mit_cmp_consentmas
        fields = '__all__'


class CmpConsentMasSerializerShort(serializers.ModelSerializer):

    class Meta:
        model = mit_cmp_consentmas
        fields = ('id', 'custCategory', 'title',
                  'description', 'defaultValues', 'canChanges')


# class CmpResponseDetailSerializer(serializers.ModelSerializer):
#     # consent = CmpConsentMasSerializerShort(many=False, read_only=True)
#     # custCode = MitClientSerializerShort(many=False, read_only=True)

#     class  Meta:
#         model = mit_cmp_Response
#         fields = ('id','compCode','respStatus','respMethod','respReference','reasonNotAgree','consent','consentTitle','custCode','custCodeName')
#         # fields = '__all__'

class CmpResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = mit_cmp_Response
        fields = ('id', 'consent', 'custCategory', 'consentTitle', 'respStatus', 'respMethod',
                  'respReference', 'reasonNotAgree', 'custCode', 'custCodeName', 'consentCrossComp')
        # fields = '__all__'


class CmpConsentMasDialyReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = mit_cmp_consentmas
        fields = ('description',)


class CmpResponseDialyReportSerializer(serializers.ModelSerializer):
    # consent_description = serializers.ReadOnlyField(source='consent.description')
    consent_description = serializers.SerializerMethodField("consentDescrip")
    maskedName = serializers.SerializerMethodField("maskedCustName")

    custCode = serializers.StringRelatedField(many=False, read_only=True)
    custCode_cardNumber = serializers.ReadOnlyField(
        source='custCode.cardNumber')

    createDate = serializers.DateTimeField(
        format="%d-%m-%Y", required=False, read_only=True)

    updateDate = serializers.DateTimeField(
        format="%d-%m-%Y", required=False, read_only=True)

    class Meta:
        model = mit_cmp_Response
        fields = ('custCode', 'custCode_cardNumber', 'consent_description', 'respStatus',
                  'createBy', 'createDate', 'updateBy', 'updateDate', 'maskedName')

    def limitDescrip(self, mit_cmp_Response):

        try:
            _description = mit_cmp_Response.consent.description[:80]
            # _description =  serializers.ReadOnlyField(source='consent.description')
            return _description + ' ...'
        except ObjectDoesNotExist:
            return ''

    def consentDescrip(self, mit_cmp_ResponseObj):
        try:
            description = ''
            consents = mit_cmp_Response.objects.filter(
                custCode=mit_cmp_ResponseObj.custCode)
            # print('Consent desc:%s' % (consents))
            for cons in consents:
                if('2' in str(cons.consent)):
                    consentFlag = "Y" if (str(cons.respStatus) ==
                                          '1') else "N"
                    description = description + str(cons.consent) + \
                        " = " + consentFlag + "   ;"
            return description
        except ObjectDoesNotExist:
            return ''

    def maskedCustName(self, mit_cmp_ResponseObj):
        try:
            fullName = const.maskingTxt(mit_cmp_ResponseObj.custCode.thFirstName) + \
                ' ' + const.maskingTxt(mit_cmp_ResponseObj.custCode.thLastName)
            return fullName
        except Exception as e:
            print('EX:'+str(e))
            return ''


class CmpRequestSerializer(serializers.ModelSerializer):
    reqid = serializers.SerializerMethodField("get_request_id")

    reqTopic = serializers.SerializerMethodField("get_request_topic")
    reqStatusTxt = serializers.SerializerMethodField("get_reqStatusTxt")
    reqCodeGroup = serializers.SerializerMethodField("get_reqCodeGroup")
    deltaCreateDate = serializers.SerializerMethodField("get_deltaCreateDate")
    maskedName = serializers.SerializerMethodField("maskedCustName")

    custCode = serializers.StringRelatedField(many=False, read_only=True)
    custCode_cardNumber = serializers.ReadOnlyField(
        source='custCode.cardNumber')
    createDateFormated = serializers.DateTimeField(source='createDate',
                                                   format="%Y-%m-%d", required=False, read_only=True)
    requestDate = serializers.DateTimeField(
        format="%d-%m-%Y", required=False, read_only=True)
    updateDate = serializers.DateTimeField(
        format="%d-%m-%Y", required=False, read_only=True)

    createDate = serializers.DateTimeField(
        format="%d-%m-%Y", required=False, read_only=True)

    class Meta:
        model = mit_cmp_request
        fields = (
            'reqid',
            'compCode',
            'maskedName',
            'reqRef',
            'custCode_cardNumber',
            'custCode',
            'reqCode',
            'reqCodeGroup',
            'reqTopic',
            'reqDetail',
            'reqReasonText',
            'reqReasonChoice',
            'workFlowProcess_Ref',
            'reqStatus',
            'reqStatusTxt',
            'reqAccounts',
            'createDate',
            'createDateFormated',
            'updateDate',
            'deltaCreateDate',
            'respDescription',
            'respMailText',
            'channel',
            'requestDate',
            'consentCrossComp',
        )

    def get_request_id(self, mit_cmp_request):
        return mit_cmp_request.id

    def to_representation(self, instance):
        representation = super(CmpRequestSerializer,
                               self).to_representation(instance)
        # representation['createDate'] = instance.createDate.strftime("%d-%m-%Y")
        return representation

    def get_deltaCreateDate(self, mit_cmp_request):

        try:
            from datetime import datetime, timezone
            utc = pytz.UTC
            now = datetime.now().replace(tzinfo=utc)
            # delta = datetime.now(timezone.utc)- mit_cmp_request.createDate
            delta = now - mit_cmp_request.createDate.replace(tzinfo=utc)

            return delta.days
        except ObjectDoesNotExist:
            return 0

    def get_request_topic(self, mit_cmp_request):
        try:
            request = mit_master_value.objects.get(
                compCode__iexact=mit_cmp_request.compCode, refCode=mit_cmp_request.reqCode)
        except ObjectDoesNotExist:
            return mit_cmp_request.reqCode+'[ObjectDoesNotExist]'

        return request.nameEn

    def get_reqStatusTxt(self, mit_cmp_request):
        return const.getStatusTxt(mit_cmp_request.compCode, mit_cmp_request.reqStatus)

    def get_reqCodeGroup(self, mit_cmp_request):
        # wealthRegister
        # consent
        txt = ''
        if mit_cmp_request.reqCode == 'wealthRegister':
            txt = 'Wealth Register'
        elif mit_cmp_request.reqCode == 'consent':
            txt = 'Consent'
        else:
            txt = 'Request'

        return txt

    def maskedCustName(self, mit_cmp_request):
        try:
            fullName = const.maskingTxt(mit_cmp_request.custCode.thFirstName) + \
                ' ' + const.maskingTxt(mit_cmp_request.custCode.thLastName)
            return fullName
        except Exception as e:
            print('EX:'+str(e))
            return ''


class CmpRequestSerializerWithConsent(serializers.ModelSerializer):
    consent = CmpConsentMasSerializerShort(many=True)

    class Meta:
        model = mit_cmp_request
        fields = '__all__'


class CmpRequestSerializerByOwner(serializers.ModelSerializer):
    reqTopic = serializers.SerializerMethodField("get_request_topic")
    reqid = serializers.SerializerMethodField("get_request_id")
    reqStatusTxt = serializers.SerializerMethodField("get_reqStatusTxt")
    custCode = serializers.StringRelatedField(many=False, read_only=True)
    custCode_cardNumber = serializers.ReadOnlyField(
        source='custCode.cardNumber')
    custCode_id = serializers.ReadOnlyField(source='custCode.id')

    class Meta:
        model = mit_cmp_request
        fields = (
            'compCode',
            'custCode_id',
            'custCode_cardNumber',
            'custCode',
            'reqid',
            'reqRef',
            'reqCode',
            'channel',
            'reqTopic',
            'reqDetail',
            'reqReasonText',
            'reqReasonChoice',
            'workFlowProcess_Ref',
            'reqStatus',
            'reqStatusTxt',
            'reqAccounts',
            'createDate',
            'createBy',
            'createBy',
            'updateDate',
            'updateBy',
            'respDescription',
            'requestDate',
            'consentCrossComp',
        )
    # def get_queryset(self):
    #     return mit_cmp_request.objects.filter(createBy=mit_client.pk , reqStatus='onprocess').order_by('createDate')

    def get_request_topic(self, mit_cmp_request):
        try:
            request = mit_master_value.objects.get(
                compCode__iexact=mit_cmp_request.compCode, refCode=mit_cmp_request.reqCode)
            return request.nameTh
        except Exception as e:
            return mit_cmp_request.reqCode

    def get_request_id(self, mit_cmp_request):
        return mit_cmp_request.id

    def get_reqStatusTxt(self, mit_cmp_request):
        return const.getStatusTxt(mit_cmp_request.compCode, mit_cmp_request.reqStatus)
