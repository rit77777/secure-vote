from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


class UniqueID(models.Model):
    unique_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=200,)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, unique=True)
    age = models.IntegerField()
    address = models.CharField(max_length = 100)
    pincode = models.CharField(max_length = 6)
    country = models.CharField(max_length = 100)
    city = models.CharField(max_length = 100)
    state = models.CharField(max_length = 100)
    c_id = models.CharField(max_length=10, null=True)
    
    def __str__(self):
        return self.unique_id


class Constituency(models.Model):
    c_id = models.CharField(max_length=10, primary_key=True)
    c_name = models.CharField(max_length=100, null=True)
    pub_date = models.DateTimeField('date published', default=now)
    is_active = models.BooleanField(default=False)
    node_address = models.URLField(max_length=200, null=True)

    def __str__(self):
        return self.c_name


class Party(models.Model):
    party_id = models.CharField(max_length=10, primary_key=True)
    candidate = models.CharField(max_length=100, null=True)
    party_name = models.CharField(max_length=100, null=True)
    party_pic = models.CharField(max_length=500, blank=True)
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.candidate} | {self.party_name}"


class RegisteredVoters(AbstractUser):
    username = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=10, unique=True, null=True)
    age = models.IntegerField(default=0)
    otp = models.CharField(max_length=6)
    account_verified = models.BooleanField(default=False)
    vote_done = models.BooleanField(default=False)
    c_id = models.CharField(max_length=10, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELD = []

    def __str__(self):
        return self.username