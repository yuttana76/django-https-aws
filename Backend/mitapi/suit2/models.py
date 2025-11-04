from django.db import models
from mitmaster.models import mit_client

# Create your models here.
class suitability(models.Model):
    compCode = models.CharField(max_length=50)
    cardNumber = models.CharField(max_length=13)
    custType = models.CharField(max_length=5,null=True,blank=True)
    # custCode = models.ForeignKey(mit_client, related_name='suitability', on_delete=models.CASCADE, null=True, blank=True)
    docVersion = models.CharField(null=True,blank=True,max_length=3)
    status = models.CharField(null=True,blank=True,max_length=1)
    score = models.CharField(null=True,blank=True,max_length=2)
    suitLevel = models.CharField(null=True,blank=True,max_length=2)
    jsonData = models.TextField(null=True,blank=True,)
    channel = models.CharField(null=True,blank=True,max_length=50)
    evaluateDate = models.DateTimeField(null=True,blank=True)
    createBy = models.CharField(max_length=50,null=True,blank=True)
    createDT = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateBy = models.CharField(max_length=50,null=True,blank=True)
    updateDT = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.compCode + "-" + self.cardNumber
    
    # @property
    # def custCode_cardNumber(self):
    #     return self.custCode.cardNumber

    # @property
    # def custCode_name(self):
    #     return self.custCode.thFirstName +" "+ self.custCode.thLastName