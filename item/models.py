from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import datetime

from tag.models import *

def attachment_file(instance, filename):
    return os.path.join('file', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')), filename)
    #if len(filename.split('.')) > 1:
    #    return os.path.join('file', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')) + '.' + filename.split('.')[-1])
    #else:
    #    return os.path.join('file', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))

class UserItemRelationship(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(max_length=30)

class Item(models.Model):
    user = models.ForeignKey(User)
    status = models.CharField(max_length=30)
    credit = models.BigIntegerField(default=0)
    useritemrelationship = models.ManyToManyField(UserItemRelationship)
    belong = models.ManyToManyField('self', symmetrical=False, blank=True)
    tag = models.ManyToManyField(Tag)

    def get_all_items_old(self, include_self=True):
        items = []
        if include_self:
            item = self
            itemcontent = item.itemcontent_set.all()
            item.create = itemcontent[0].create
            item.update = itemcontent.reverse().create
            items.append(item)
        #for item in Item.objects.filter(belong=self).prefetch_related('itemcontent_set'):
        for item in self.item_set.prefetch_related('itemcontent_set'):
            itemcontent = item.itemcontent_set.all()
            item.create = itemcontent[0].create
            item.update = itemcontent.reverse().create
            if item not in items:
                items.append(item)
            for subitem in item.get_all_items(include_self=False):
                itemcontent = subitem.itemcontent_set.all()
                subitem.create = itemcontent[0].create
                subitem.update = itemcontent.reverse().create
                if subitem not in items:
                    items.append(subitem)
        return items

    def get_all_items(self, include_self=True):
        items = []
        queue = []
        queue.append(self)
        while queue:
            node = queue.pop(0)
            if include_self:
                item = node
                itemcontent = item.itemcontent_set.all()
                item.create = itemcontent[0].create
                item.update = itemcontent.reverse().create
                if item not in items:
                    items.append(item)
            for item in node.item_set.all():
                queue.append(item)
                itemcontent = item.itemcontent_set.all()
                item.create = itemcontent[0].create
                item.update = itemcontent.reverse().create
                if item not in items:
                    items.append(item)
        return items

    def get_root_items_old(self):
        rootitems = []
        if self.belong.all():
            for belongitem in self.belong.all().prefetch_related('itemcontent_set'):
                for rootitem in belongitem.get_root_items():
                    if rootitem not in rootitems:
                        rootitems.append(rootitem)
        else:
            rootitems.append(self)
        return rootitems

    def get_root_items(self):
        rootitems = []
        queue = []
        queue.append(self)
        while queue:
            node = queue.pop(0)
            if node.belong.all():
                for belongitem in node.belong.all().prefetch_related('itemcontent_set'):
                    queue.append(belongitem)
            else:
                if node not in rootitems:
                    rootitems.append(node)
        return rootitems

class ItemContent(models.Model):
    item = models.ForeignKey(Item)
    create = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    ip = models.CharField(max_length=255)
    ua = models.CharField(max_length=255)

    class Meta:
        ordering = ['id']

class ContentAttachment(models.Model):
    itemcontent = models.ForeignKey(ItemContent)
    title = models.CharField(max_length=30)
    file = models.FileField(storage=FileSystemStorage(location=settings.MEDIA_ROOT), upload_to=attachment_file)
    content = models.TextField()
    contenttype = models.CharField(max_length=30)

class Link(models.Model):
    url = models.TextField()
    logo = models.TextField()
    title = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=30)
    unreachable = models.BigIntegerField(default=0)
    lastcheck = models.DateTimeField(auto_now=True)

class Coin(models.Model):
    user = models.ForeignKey(User)
    cointype = models.TextField()
    coinhold = models.TextField()
