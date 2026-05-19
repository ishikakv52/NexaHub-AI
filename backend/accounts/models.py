from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class OTPModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)