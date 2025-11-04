from django.db import models
from django.contrib.auth.models import User
# from cmpapi.models import mit_cmp_Response
import cmpapi.models
# from cmpapi.models import mit_cmp_request
from simple_history.models import HistoricalRecords


# Create your models here.
class mit_client(models.Model):
  compCode = models.CharField(max_length=50)
  cardNumber = models.CharField(max_length=13)
  identificationCardType = models.CharField(max_length=15)
  passportCountry = models.CharField(max_length=2,null=True,blank=True)
  cardExpiryDate = models.DateField(null=True,blank=True)
  title = models.CharField(max_length=5,null=True,blank=True)
  titleOther = models.CharField(max_length=50,null=True,blank=True)
  enFirstName = models.CharField(max_length=100)
  enLastName = models.CharField(max_length=100)
  thFirstName = models.CharField(max_length=100,null=True,blank=True)
  thLastName = models.CharField(max_length=100,null=True,blank=True)
  email = models.CharField(max_length=100,null=True,blank=True)
  phone = models.CharField(max_length=20)
  products =models.CharField(max_length=50,null=True,blank=True)
  otpMethod = models.CharField(max_length=100, null=True,blank=True)
  otpIsVerified = models.BooleanField(blank=False, default=False)
  otpIsVerifiedDT = models.DateTimeField(null=True,blank=True)
  otpCounter = models.IntegerField(default=0, blank=False)
  otpExpire = models.DateTimeField(null=True,blank=True)
  otpRef = models.CharField(max_length=6, null=True,blank=True)
  otpCode = models.CharField(max_length=6,null=True,blank=True)
# Auth (MARZ)v.2
  otp = models.CharField(max_length=6, null=True, blank=True)
  otp_ref = models.CharField(max_length=6, null=True, blank=True)
  otp_expiry = models.DateTimeField(blank=True, null=True)
  max_otp_try = models.IntegerField(default=3)  # Max OTP tries
  otp_max_out = models.DateTimeField(blank=True, null=True)
  user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mitclient_user')

  # Auth (MARZ)v.2

  add_time = models.DateTimeField(verbose_name=' Generation time ', auto_now_add=True)
  createBy = models.CharField(max_length=50,null=True,blank=True)
  createDate = models.DateTimeField(auto_now_add=True,blank=True,null=True)
  updateBy = models.CharField(max_length=50,null=True,blank=True)
  updateDate = models.DateTimeField(null=True,blank=True)
  history = HistoricalRecords()
  channel = models.CharField(max_length=50,null=True,blank=True)

  class Meta:
    unique_together = (('compCode','cardNumber'),)
    indexes = [models.Index(fields=("compCode", "cardNumber"))]
    ordering = ['thFirstName','thLastName']

  def __str__(self):
    return '%s %s' % (self.thFirstName, self.thLastName)


class mit_master_value(models.Model):
  compCode = models.CharField(max_length=50)
  refType = models.CharField(max_length=50)
  refCode = models.CharField(max_length=50)
  nameTh = models.CharField(max_length=500)
  nameEn = models.CharField(max_length=500)
  status = models.CharField(max_length=1)
  seq = models.CharField(max_length=50)

  class Meta:
    indexes = [models.Index(fields=("compCode", "refType", "refCode"))]

  def __str__(self):
        return '%s; %s; %s; %s' % (self.compCode, self.refType, self.refCode, self.nameTh)
