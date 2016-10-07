# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
# Create your views here.

from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect, render
import datetime
from django.utils.timezone import utc
import urllib2
import json
from item.models import *
from item.forms import *
from tag.models import *
from django.forms.utils import ErrorList
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user.models import *
from hulu import *
from main.__init__ import *
from item.__init__ import *
from django.forms.models import inlineformset_factory
from django.db.models import Q

def Index(request):
    if request.user.is_authenticated():
        return redirect('/')

def View(request, id):
    try:
        tag = Tag.objects.get(id=id)
    except:
        tag = None
    try:
        items = Item.objects.select_related('user').filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).filter(Q(status__isnull=True) | Q(status__exact='')).filter(Q(tag__id=id)).all().prefetch_related('itemcontent_set', 'itemcontent_set__contentattachment_set', 'tag')
        itemlist = []
        for item in items:
            #itemcontent = ItemContent.objects.filter(item=item)
            itemcontent = item.itemcontent_set.all()
            if itemcontent:
                item.create = itemcontent[0].create
                if itemcontent[0].content:
                    item.title = itemcontent[0].content.strip().splitlines()[0]
                else:
                    #contentattachment = ContentAttachment.objects.filter(itemcontent=itemcontent[0])
                    contentattachment = itemcontent[0].contentattachment_set.all()
                    if contentattachment:
                        item.title = contentattachment[0].title
                    else:
                        item.title = str(item.id)

                subitem = item.get_all_items(include_self=False)
                if subitem:
                    subitem.sort(key=lambda item:item.create, reverse=True)
                    #itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                    itemcontent = subitem[0].itemcontent_set.all().reverse()
                    item.subitemcount = len(subitem)
                    item.lastsubitem = subitem[0]
                else:
                    item.lastsubitem = itemcontent.last()
                itemlist.append(item)

        itemlist = sorted(itemlist, key=lambda item:item.lastsubitem.create, reverse=True)

        paginator = Paginator(itemlist, 30)
        itemlist = []
        page = request.GET.get('page')
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        currentpage = items.number

        for item in items:
            itemlist.append(item)

        items = itemlist
        items = sorted(items, key=lambda item:item.lastsubitem.create, reverse=True)
    except Item.DoesNotExist:
        items = None

    try:
        tags = Tag.objects.all().order_by('?')[:10]
    except Tag.DoesNotExist:
        tags = None

    content = {
        'items': items,
        'tag': tag,
        'tags': tags
    }
    if request.GET.get('type') == 'json':
        content = {
            'page': currentpage,
            'items': []
        }

        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    return render(request, 'tag/index.html', content)

def Update(request, id):
    if request.user.is_authenticated():
        return None
