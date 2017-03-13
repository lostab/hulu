# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from item.models import *
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from item.__init__ import *

User._meta.get_field('email')._unique = True

def avatar_file(instance, filename):
    return os.path.join('avatar', str(instance.user.username) + '.png')

def get_item_by_user(user, request):
    try:
        if request.user.is_authenticated():
            items = Item.objects.select_related('user').filter(user=user).filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).filter(~Q(status__exact='private') | Q(user=request.user)).order_by('-id').prefetch_related('itemcontent_set')
        else:
            items = Item.objects.select_related('user').filter(user=user).filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).filter(~Q(status__exact='private')).order_by('-id').prefetch_related('itemcontent_set')
        items = sorted(items, key=lambda item:item.id, reverse=True)

        subitems = Item.objects.filter(user=user).filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=False)).order_by('-id').prefetch_related('itemcontent_set')
        belongitems = []
        for subitem in subitems:
            rootitems = subitem.get_root_items()
            for rootitem in rootitems:
                #过滤掉重复的、自己发的、私有的信息
                if rootitem not in belongitems and rootitem.user != user and rootitem.status != 'private':
                    belongitems.append(rootitem)
        belongitems = sorted(belongitems, key=lambda belongitem:belongitem.id, reverse=True)

        for item in items:
            itemcontent = item.itemcontent_set.all()
            if itemcontent:
                item.create = itemcontent[0].create
                if itemcontent[0].content:
                    item.title = itemcontent[0].content.strip().splitlines()[0]
                else:
                    contentattachment = itemcontent[0].contentattachment_set.all()
                    if contentattachment:
                        item.title = contentattachment[0].title
                    else:
                        item.title = str(item.id)

        for item in belongitems:
            itemcontent = item.itemcontent_set.all()
            if itemcontent:
                item.create = itemcontent[0].create
                if itemcontent[0].content:
                    item.title = itemcontent[0].content.strip().splitlines()[0]
                else:
                    contentattachment = itemcontent[0].contentattachment_set.all()
                    if contentattachment:
                        item.title = contentattachment[0].title
                    else:
                        item.title = str(item.id)

        items = sort_items(items, request.GET.get('page'))
        belongitems = sort_items(belongitems, request.GET.get('page'))
    except Item.DoesNotExist:
        items = None
        belongitems = None

    return items, belongitems

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
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
