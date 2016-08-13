from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import datetime

class TagRelationship(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(max_length=30)

class Tag(models.Model):
    status = models.CharField(max_length=30)
    credit = models.BigIntegerField(default=0)
    name = models.CharField(max_length=128, unique=True)
    info = models.CharField(max_length=255)
    itemrelationship = models.ManyToManyField(TagRelationship)
