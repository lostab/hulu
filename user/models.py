from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from item.models import *

User._meta.get_field('email')._unique = True

def avatar_file(instance, filename):
    return os.path.join('avatar', str(instance.user.username) + '.png')

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name

class UserRelationship(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(max_length=30)

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    create = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)
    credit = models.BigIntegerField(default=0)
    openid = models.CharField(max_length=128)
    info = models.CharField(max_length=255)
    profile = models.TextField()
    page = models.TextField()
    avatar = models.FileField(storage=OverwriteStorage(), upload_to=avatar_file)
    userrelationship = models.ManyToManyField(UserRelationship)

class UserNotify(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)
    type = models.CharField(max_length=30)
    item = models.ForeignKey(Item)