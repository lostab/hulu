# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect
from datetime import datetime, timedelta
from django.utils.timezone import utc
import urllib2
import json
import re
import os
import time
import HTMLParser
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from hulu import *
from main.forms import *
from user.models import *
from user.forms import *
from item.models import *
from item.forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from main.__init__ import *
from django.db.models import Q
from django.utils.translation import ugettext
from collections import namedtuple
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder

def index(request):
    try:
        if Site.objects.all():
            site = Site.objects.all()[0]
            if site.domain != request.get_host():
                site.domain = request.get_host()
                site.save()
        else:
            site = Site()
            site.domain = request.get_host()
            site.save()
    except Site.DoesNotExist:
        site = None
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = request.META['REMOTE_ADDR']
    if x_forwarded_for:
        ip = x_forwarded_for.split(', ')[-1]
    
    try:
        items = Item.objects.select_related('user').filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).filter(Q(status__isnull=True) | Q(status__exact='')).all()
        itemlist = []
        for item in items:
            itemcontent = ItemContent.objects.filter(item=item)
            item.create = itemcontent[0].create
            if itemcontent[0].content:
                item.title = itemcontent[0].content.strip().splitlines()[0]
            else:
                contentattachment = ContentAttachment.objects.filter(itemcontent=itemcontent[0])
                item.title = contentattachment[0].title
            
            subitem = item.get_all_items(include_self=False)
            if subitem:
                subitem.sort(key=lambda item:item.create, reverse=True)
                itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                item.subitemcount = len(subitem)
                item.lastsubitem = subitem[0]
            else:
                item.lastsubitem = itemcontent[0]
            itemlist.append(item)
        
        
        fetchitems = []
        fetchitem = namedtuple('fetchitem', 'user title url lastsubitem')
        fetchuser=namedtuple('fetchuser', 'username userprofile')
        fetchprofile=namedtuple('fetchprofile', 'openid avatar')
        fetchcreate=namedtuple('fetchcreate', 'create')
        
        cacheitems = cache.get('cacheitems')
        if cacheitems and not request.GET.get('nocache'):
            cacheitems = json.loads(cacheitems)
            if cacheitems and cacheitems.has_key('datetime') and cacheitems.has_key('items') and cacheitems['datetime']:
                cacheitems['datetime'] = datetime.datetime.strptime(cacheitems['datetime'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                if cacheitems['datetime'] + timedelta(hours=1) > datetime.datetime.now():
                    for item in cacheitems['items']:
                        item['lastsubitem']['create'] = datetime.datetime.strptime(item['lastsubitem']['create'].split('+')[0], '%Y-%m-%d %H:%M:%S')
                        cacheitem = fetchitem(user=fetchuser(username=item['user']['username'], userprofile=fetchprofile(openid=item['user']['userprofile']['openid'], avatar=item['user']['userprofile']['avatar'])), title=item['title'], url=item['url'], lastsubitem=fetchcreate(create=timezone.make_aware(item['lastsubitem']['create'], timezone.get_default_timezone())))
                        itemlist.append(cacheitem)
        else:
            def updatecache():
                cacheitems = {
                    "datetime": str(timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())),
                    "items": []
                }
                for item in fetchitems:
                    cacheitems['items'].append({
                        'title': item.title.decode().encode('utf-8'),
                        'url': item.url.encode('utf-8'),
                        'user': {
                            'username': item.user.username.encode('utf-8'),
                            'userprofile': {
                                'openid': item.user.userprofile.openid.encode('utf-8'),
                                'avatar': item.user.userprofile.avatar.encode('utf-8')
                            }
                        },
                        'lastsubitem': {
                            'create': str(item.lastsubitem.create)
                        }
                    })
                cache.set('cacheitems', json.dumps(cacheitems, encoding='utf-8', ensure_ascii=False, indent=4), 3600)
            
            try:
                #Zhihu
                for fetchdate in [[str((datetime.datetime.now() + timedelta(days=1)).strftime('%Y%m%d')), str(datetime.datetime.now().strftime('%Y%m%d'))], [str(datetime.datetime.now().strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))], [str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=2)).strftime('%Y%m%d'))]]:
                    zhihuurl = 'http://news.at.zhihu.com/api/3/news/before/' + fetchdate[0]
                    hdr = {
                        'User-Agent': ''
                    }
                    req = urllib2.Request(zhihuurl, headers=hdr)
                    zhihujson = json.loads(urllib2.urlopen(req).read())
                    zhihudate = zhihujson['date']
                    if int(zhihudate) == int(fetchdate[1]):
                        zhihucontent = zhihujson['stories']
                        for i in zhihucontent:
                            zhihuitem = fetchitem(user=fetchuser(username=u'知乎日报', userprofile=fetchprofile(openid='Zhihu', avatar='http://www.zhihu.com/favicon.ico')), title=i['title'], url='http://daily.zhihu.com/story/'+str(i['id']), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(str(datetime.datetime.now().strftime('%Y')) + i['ga_prefix'], '%Y%m%d%H'), timezone.get_default_timezone())))
                            itemlist.append(zhihuitem)
                            fetchitems.append(zhihuitem)
                #V2EX
                v2exurl = 'https://www.v2ex.com/api/topics/hot.json'
                v2exjson = json.loads(urllib2.urlopen(v2exurl).read())
                for i in v2exjson:
                    v2exitem = fetchitem(user=fetchuser(username='V2EX', userprofile=fetchprofile(openid='V2EX', avatar='https://v2ex.com/favicon.ico')), title=i['title'], url=i['url'].replace('http://', 'https://'), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.fromtimestamp(int(i['created'])), timezone.get_default_timezone())))
                    itemlist.append(v2exitem)
                    fetchitems.append(v2exitem)
                
                #Google News
                newsurl = 'https://news.google.com/news?output=rss&hl=zh-CN'
                req = urllib2.Request(newsurl)
                result = urllib2.urlopen(req).read()
                items = re.split('<item>|</item> <item>|</item>', result)
                items.pop(0)
                items.pop(-1)
                for item in items:
                    hp = HTMLParser.HTMLParser()
                    title = hp.unescape(re.split('<title>|</title> <title>|</title>', item)[1])
                    newstime = re.split('<pubDate>|</pubDate> <pubDate>|</pubDate>', item)[1]
                    url = re.split('<link>|</link> <link>|</link>', item)[1].split('url=')[1]
                    newsitem = fetchitem(user=fetchuser(username='Google News', userprofile=fetchprofile(openid='Google News', avatar='http://www.google.cn/favicon.ico')), title=title, url=url, lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(newstime, '%a, %d %b %Y %H:%M:%S GMT'), timezone.get_default_timezone())))
                    itemlist.append(newsitem)
                    fetchitems.append(newsitem)
                                
                updatecache()
            except:
                updatecache()
        
        items = itemlist
        
        items = sorted(items, key=lambda item:item.lastsubitem.create, reverse=True)
        paginator = Paginator(items, 30)
        page = request.GET.get('page')
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
    except Item.DoesNotExist:
        items = None
    
    content = {
        'items': items
    }
    if request.GET.get('type') == 'json':
        content = {
            'page': items.number,
            'items': []
        }
        
        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    return render_to_response('main/index.html', content , context_instance=RequestContext(request))

def ttt(request):
    return render_to_response('other/ttt.html', {} , context_instance=RequestContext(request))

@csrf_exempt
def sq(request):
    if request.method == 'GET':
        content = {
            
        }
        if os.path.isfile(os.path.join(settings.MEDIA_ROOT, 'sq.jpg')):
            mtime_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(settings.MEDIA_ROOT, 'sq.jpg')))
            if request.GET.get('type') == 'json':
                content = {
                    'mtime': mtime_delta.total_seconds()
                }
                
                return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
            content['mtime'] = mtime_delta.total_seconds()
        return render_to_response('other/sq.html', content , context_instance=RequestContext(request))
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with open(os.path.join(settings.MEDIA_ROOT, 'sq.jpg'), 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)
        return render_to_response('other/sq.html', {} , context_instance=RequestContext(request))

def app(request):
    if request.user.is_authenticated():
        content = {
            
        }
        if request.method == 'GET':
            if request.GET.get('type') == 'json':
                messagelist = []
                ursession = []
                
                def getuir():
                    if request.GET.get('uirid'):
                        useritemrelationship = UserItemRelationship.objects.filter(type="message").filter(user=request.user).filter(id__gt=request.GET.get('uirid')).prefetch_related('item_set').order_by('id')
                    else:
                        useritemrelationship = UserItemRelationship.objects.filter(type="message").filter(user=request.user).prefetch_related('item_set').order_by('id')
                    for ur in useritemrelationship:
                        for message in ur.item_set.all():
                            urusers = []
                            murs = message.useritemrelationship.all()
                            for mur in murs:
                                if mur.user not in urusers:
                                    urusers.append(mur.user)
                            if len(urusers) != len(murs):
                                useritemrelationship = None
                                break
                    return useritemrelationship
                
                useritemrelationship = getuir()
                
                for i in range(30):
                    if not useritemrelationship:
                        time.sleep(1)
                        useritemrelationship = getuir()
                
                for ur in useritemrelationship:
                    for message in ur.item_set.all():
                        urusers = []
                        for mur in message.useritemrelationship.all():
                            if mur.user not in urusers:
                                urusers.append(mur.user)
                        if len(urusers) == 2 and request.user in urusers:
                            urusers.remove(request.user)
                        urusers = sorted(urusers, key=lambda user: user.username)
                        
                        itemcontent = ItemContent.objects.filter(item=message)
                        message.create = itemcontent[0].create
                        message.title = itemcontent[0].content.strip().splitlines()[0]
                        
                        subitem = message.get_all_items(include_self=False)
                        if subitem:
                            subitem.sort(key=lambda item:item.create, reverse=True)
                            itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                            message.subitemcount = len(subitem)
                            message.lastsubitem = subitem[0]
                        else:
                            message.lastsubitem = itemcontent[0]
                        
                        messagesession = {
                            'urusers': urusers
                        }
                        if urusers not in ursession:
                            ursession.append(urusers)
                            messagesession['messages'] = [message]
                            messagelist.append(messagesession)
                        else:
                            for ms in messagelist:
                                if ms['urusers'] == urusers:
                                    if message not in ms['messages']:
                                        ms['messages'].append(message)
                
                messagelist = sorted(messagelist, key=lambda item:item['messages'][-1].lastsubitem.create, reverse=False)
                
                messagesessions = []
                for ms in messagelist:
                    urusers = []
                    for uruser in ms['urusers']:
                        urusers.append({
                            'username': uruser.username,
                            'info': uruser.userprofile.info,
                            'avatar': (uruser.userprofile.openid) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
                            'profile': uruser.userprofile.profile,
                            'page': uruser.userprofile.page,
                        })
                    
                    lastmessage = {
                        'content': ms['messages'][-1].lastsubitem.content,
                        'datetime': str(ms['messages'][-1].lastsubitem.create)
                    }
                    
                    messages = []
                    for message in sorted(ms['messages'], key=lambda item:item.lastsubitem.create, reverse=False)[-100:]:
                        messages.append({
                            'id': str(message.id),
                            'user': {
                                'username': message.user.username,
                                'info': message.user.userprofile.info,
                                'avatar': (message.user.userprofile.openid) and str(message.user.userprofile.avatar) or ((message.user.userprofile.avatar) and '/s/' + str(message.user.userprofile.avatar) or '/s/avatar/n.png'),
                                'profile': message.user.userprofile.profile,
                                'page': message.user.userprofile.page,
                            },
                            'create': str(message.lastsubitem.create),
                            'content': message.lastsubitem.content
                        })
                    
                    messagesession = {
                        'urusers': urusers,
                        'lastmessage': lastmessage,
                        'messages': messages
                    }
                    messagesessions.append(messagesession)
                
                uirid = request.GET.get('uirid')
                if useritemrelationship:
                    uirid = str(useritemrelationship.reverse()[0].id)
                
                content = {
                    'status': 'success',
                    'messagesessions': messagesessions,
                    'uirid': uirid
                }
                return jsonp(request, content)
            
        if request.method == 'POST':
            if request.POST.get('usernames'):
                usernames = request.POST.get('usernames').split(',')
                users = []
                for username in usernames:
                    try:
                        user = User.objects.get(username=username)
                        if user not in users:
                            users.append(user)
                    except User.DoesNotExist:
                        user = None
                if not users:
                    return redirect('/')
                if len(users) > 1 and request.user not in users:
                    return redirect('/')
                if request.user not in users:
                    users.append(User.objects.get(username=request.user))
                users = sorted(users, key=lambda user: user.username)
                if request.POST.get('content').strip():
                    form = ItemContentForm(request.POST)
                    if form.is_valid():
                        item = Item(user=request.user)
                        item.save()
                        
                        itemcontent = ItemContent(item=item)
                        itemcontentform = ItemContentForm(request.POST, instance=itemcontent)
                        itemcontent = itemcontentform.save()
                        
                        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                        ip = request.META['REMOTE_ADDR']
                        if x_forwarded_for:
                            ip = x_forwarded_for.split(', ')[-1]
                        
                        itemcontent.ip = ip
                        itemcontent.ua = request.META['HTTP_USER_AGENT']
                        itemcontent.save()
                        
                        uirs = []
                        for user in users:
                            useritemrelationship = UserItemRelationship(user=user)
                            useritemrelationship.type = 'message'
                            useritemrelationship.save()
                            uirs.append(useritemrelationship)
                        item.useritemrelationship.add(*uirs)
                        item.save()
            
            if request.POST.get('newusernames'):
                newusernames = request.POST.get('newusernames').split(',')
                newusers = []
                for newusername in newusernames:
                    try:
                        newuser = User.objects.get(username=newusername)
                        if newuser not in newusers:
                            newusers.append(newuser)
                    except User.DoesNotExist:
                        newuser = None
                if not newusers:
                    return redirect('/')
                if len(newusers) > 1 and request.user not in newusers:
                    return redirect('/')
                if request.user not in newusers:
                    newusers.append(User.objects.get(username=request.user))
                if len(newusers) == 2 and request.user in newusers:
                    newusers.remove(request.user)
                newusers = sorted(newusers, key=lambda newuser: newuser.username)
                
                newurusers = []
                for uruser in newusers:
                    newurusers.append({
                        'username': uruser.username,
                        'info': uruser.userprofile.info,
                        'avatar': (uruser.userprofile.openid) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
                        'profile': uruser.userprofile.profile,
                        'page': uruser.userprofile.page,
                    })
                    
                newmessagesession = {
                    'urusers': newurusers,
                    'lastmessage': {
                        'content': '',
                        'datetime': ''
                    },
                    'messages': []
                }
                content['newmessagesession'] = json.dumps(newmessagesession, encoding='utf-8', ensure_ascii=False, indent=4)
        return render_to_response('main/app.html', content , context_instance=RequestContext(request))
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return jsonp(request, content)
        return redirect('/u/login/?next=' + request.path + '?' + request.META['QUERY_STRING'])