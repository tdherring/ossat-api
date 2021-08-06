from django.db import models
from users.models import CustomUser

# Create your models here.


class Organisation(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    invite_code = models.CharField(max_length=10)
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True)
    managers = models.ManyToManyField(CustomUser, related_name="manager_of", blank=True)
    members = models.ManyToManyField(CustomUser, related_name="member_of", blank=True)
