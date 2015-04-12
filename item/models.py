from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import datetime

from tag.models import *

def attachment_file(instance, filename):
    if len(filename.split('.')) > 1:
        return os.path.join('file', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')) + '.' + filename.split('.')[-1])
    else:
        return os.path.join('file', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))

class UserItemRelationship(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(max_length=30)

class Item(models.Model):
    user = models.ForeignKey(User)
    status = models.CharField(max_length=30)
    credit = models.BigIntegerField(default=0)
    useritemrelationship = models.ManyToManyField(UserItemRelationship)
    belong = models.ManyToManyField('self', symmetrical=False, null=True, blank=True)
    tag = models.ManyToManyField(Tag)
    
    def get_all_items(self, include_self=True):
        items = []
        if include_self:
            items.append(self)
        for item in Item.objects.filter(belong=self):
            items.append(item)
            for subitem in item.get_all_items(include_self=False):
                items.append(subitem)
        for item in items:
            itemcontent = ItemContent.objects.filter(item=item)
            item.create = itemcontent[0].create
            item.update = itemcontent.reverse().create
        return items

class ItemContent(models.Model):
    item = models.ForeignKey(Item)
    create = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    ip = models.CharField(max_length=255)
    ua = models.CharField(max_length=255)

class ContentAttachment(models.Model):
    itemcontent = models.ForeignKey(ItemContent)
    title = models.CharField(max_length=30)
    file = models.FileField(storage=FileSystemStorage(location=settings.MEDIA_ROOT), upload_to=attachment_file)
    contenttype = models.CharField(max_length=30)
