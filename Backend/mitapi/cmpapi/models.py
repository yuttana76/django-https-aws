from django.db import models
from django.contrib.auth.models import User
from mitmaster.models import mit_client
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
from mitmaster.models import mit_master_value

_AGREE = 'agree'
_DISAGREE = 'disagree'

_ONPROC = 'onprocess'
_APPROVE = 'approve'
_REJECT = 'reject'
_FINISH = 'finish'

ACTIVE_CHOICES = [
    ('A', 'Active'),
    ('I', 'Inactive'),
]

# Create your models here.


class mit_cmp_consentmas(models.Model):
    compCode = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    consStatus = models.CharField(max_length=1, null=True, blank=True,
                                  choices=ACTIVE_CHOICES,
                                  default='A',
                                  )
    custCategory = models.CharField(max_length=10, null=True, blank=True)
    requestData = models.TextField(max_length=500, null=True, blank=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    effectFromDate = models.DateField(null=True, blank=True)
    effectToDate = models.DateField(null=True, blank=True)
    publishDate = models.DateField(null=True, blank=True)
    defaultValues = models.CharField(max_length=10, null=True, blank=True)
    canChanges = models.CharField(max_length=1, null=True, blank=True)
    seq = models.IntegerField(default=0)
    createBy = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                                 related_name='%(class)s_created', null=True, blank=True)
    createDate = models.DateTimeField(auto_now_add=True)
    updateBy = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                                 related_name='%(class)s_updated', null=True, blank=True)
    updateDate = models.DateTimeField(auto_now=True)
    crossCompTriger = models.CharField(max_length=1, null=True, blank=True)
    crossCompFollow = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return '%s' % (self.title)

    def no_resp_agree(self):
        global _AGREE
        response = mit_cmp_Response.objects.filter(
            consent=self, respStatus=_AGREE)
        return len(response)

    def no_resp_disagree(self):
        global _DISAGREE
        response = mit_cmp_Response.objects.filter(
            consent=self, respStatus=_DISAGREE)
        return len(response)

    def no_req_onprocess(self):
        global _ONPROC
        req = mit_cmp_request.objects.filter(
            consent=self, approveStatus=_ONPROC)
        return len(req)

    def no_req_approve(self):
        global _APPROVE
        req = mit_cmp_request.objects.filter(
            consent=self, approveStatus=_APPROVE)
        return len(req)

    def no_req_finish(self):
        global _FINISH
        req = mit_cmp_request.objects.filter(
            consent=self, approveStatus=_FINISH)
        return len(req)

    def no_req_reject(self):
        global _REJECT
        req = mit_cmp_request.objects.filter(
            consent=self, approveStatus=_REJECT)
        return len(req)


class mit_cmp_Response(models.Model):
    compCode = models.CharField(max_length=50)
    consent = models.ForeignKey(mit_cmp_consentmas, related_name='consentMaster',
                                on_delete=models.CASCADE, null=True, blank=True)
    custCode = models.ForeignKey(
        mit_client, related_name='consentResponse', on_delete=models.CASCADE, null=True, blank=True)
    respMethod = models.CharField(max_length=10, null=True, blank=True)
    respStatus = models.CharField(max_length=1, null=True, blank=True)
    # respDate = models.DateField(auto_now_add=True, null=True,blank=True)
    # reasonNotAgree = models.TextField(max_length=500,null=True,blank=True)
    reasonNotAgree = models.TextField(null=True, blank=True)
    respReference = models.CharField(max_length=1000, null=True, blank=True)
    createBy = models.CharField(max_length=50, null=True, blank=True)
    createDate = models.DateTimeField(auto_now_add=True, blank=True)
    updateBy = models.CharField(max_length=50, null=True, blank=True)
    updateDate = models.DateTimeField(auto_now=True)
    requestDate = models.DateTimeField(blank=True, null=True)
    consentCrossComp = models.CharField(max_length=1, null=True, blank=True)
    history = HistoricalRecords()

    # class Meta:
    #   # unique_together = (('consent','custCode'),)
    #   index_together = (('consent','custCode'),)

    def __str__(self):
        return '%s; %s; %s; %s ' % (self.compCode, self.custCode, self.consent, self.respStatus)

    def consentTitle(self):
        response = mit_cmp_consentmas.objects.get(pk=self.consent.id)
        return response.title

    def custCategory(self):
        response = mit_cmp_consentmas.objects.get(pk=self.consent.id)
        return response.custCategory

    def custCodeName(self):
        response = mit_client.objects.get(pk=self.custCode.id)
        return response.thFirstName + " " + response.thLastName


class mit_cmp_request(models.Model):
    compCode = models.CharField(max_length=50)
    consent = models.ForeignKey(
        mit_cmp_consentmas, on_delete=models.CASCADE, null=True, blank=True)
    custCode = models.ForeignKey(
        mit_client, related_name='clientRequest', on_delete=models.CASCADE, null=True, blank=True)
    reqRef = models.CharField(max_length=50, null=True, blank=True)
    reqCode = models.CharField(max_length=50)
    reqChannel = models.CharField(max_length=50, null=True, blank=True)
    reqDetail = models.TextField(null=True, blank=True)
    reqReasonText = models.TextField(null=True, blank=True)
    reqReasonChoice = models.CharField(max_length=100, null=True, blank=True)
    workFlowProcess_Ref = models.CharField(
        max_length=100, null=True, blank=True)
    reqStatus = models.CharField(max_length=50, null=True, blank=True)
    respDescription = models.TextField(null=True, blank=True)
    respMailText = models.TextField(null=True, blank=True)
    reqAccounts = models.CharField(max_length=100, null=True, blank=True)
    createBy = models.CharField(max_length=50, null=True, blank=True)
    createDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateBy = models.CharField(max_length=50, null=True, blank=True)
    updateDate = models.DateTimeField(auto_now=True, blank=True, null=True)
    channel = models.CharField(max_length=50, null=True, blank=True)
    requestDate = models.DateTimeField(blank=True, null=True)
    consentCrossComp = models.CharField(max_length=1, null=True, blank=True)

    history = HistoricalRecords()

    # class Meta:
    #     indexes = [models.Index(fields=("consent"))]

    def __str__(self):
        return '%s; %s; %s; %s; %s' % (self.reqRef, self.compCode, self.custCode, self.reqCode, self.reqStatus)

    # def save(self, *args, **kwargs):
    #     self.reqRef = "REQ-PDPA-{0}".format(str(self.id).zfill(6))
    #     super(mit_cmp_request, self).save(*args, **kwargs)


class mit_cmp_requestCFG(models.Model):
    compCode = models.CharField(max_length=50)
    consent = models.ForeignKey(
        mit_cmp_consentmas, related_name='subjectRights', on_delete=models.CASCADE)
    reqCode = models.CharField(max_length=50)
    reqTopic = models.CharField(max_length=100)
    reqDescription = models.CharField(max_length=500)
    showReqDetail = models.BooleanField(null=True, blank=True)
    showReqReason = models.BooleanField(null=True, blank=True)
    reqResonChoice = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.reqCode, self.reqTopic)

# Signals

# @receiver(pre_save,sender=mit_cmp_request)
# def print_req_presave(sender,instance,**kwargs):
#   print('PRE_SAVE')
#   print(sender.objects.get(id=instance.id).reqStatus)
#   print(instance.reqStatus)

# @receiver(pre_save,sender=mit_cmp_request)
# def update_reqRef_postsave(sender,instance,**kwargs):
#   print('PRE_SAVE')
        # On create only
    # if instance.id is None:
