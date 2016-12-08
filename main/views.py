# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
# Create your views here.

from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect, render
from datetime import datetime, timedelta
from django.utils.timezone import utc
import urllib2
import urllib
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
from tag.models import *
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
from django.utils.html import escape
from django.core.mail import EmailMessage
import hashlib
import ssl

def index(request):
    #try:
    #    if Site.objects.all():
    #        site = Site.objects.get_current()
    #        if site.domain != request.get_host():
    #            site.domain = request.get_host()
    #            site.save()
    #    else:
    #        site = Site()
    #        site.domain = request.get_host()
    #        site.save()
    #except Site.DoesNotExist:
    #    pass

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = request.META['REMOTE_ADDR']
    if x_forwarded_for:
        ip = x_forwarded_for.split(', ')[-1]

    q = request.GET.get('q')
    if q == '':
        return redirect('/')
    if q:
        if q != q.strip():
            q = q.strip()
            if q == '':
                return redirect('/')
            else:
                return redirect('/?q=' + q)

    try:
        items = Item.objects.select_related('user').filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).filter(Q(status__isnull=True) | Q(status__exact='') | (Q(status__exact='private') & Q(user__id=request.user.id))).all().prefetch_related('itemcontent_set', 'itemcontent_set__contentattachment_set')
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
        pitems = items

        for item in items:
            itemlist.append(item)

        fetchitems = []
        fetchitem = namedtuple('fetchitem', 'user title url lastsubitem tags')
        fetchuser = namedtuple('fetchuser', 'username userprofile')
        fetchprofile = namedtuple('fetchprofile', 'openid avatar')
        fetchcreate = namedtuple('fetchcreate', 'create')

        cacheitems = cache.get('cacheitems')
        if cacheitems and not request.GET.get('nocache') and not request.GET.get('page'):
            cacheitems = json.loads(cacheitems)
            if cacheitems and cacheitems.has_key('datetime') and cacheitems.has_key('items') and cacheitems['datetime']:
                cacheitems['datetime'] = datetime.datetime.strptime(cacheitems['datetime'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                if cacheitems['datetime'] + timedelta(hours=1) > datetime.datetime.now():
                    for item in cacheitems['items']:
                        item['lastsubitem']['create'] = datetime.datetime.strptime(item['lastsubitem']['create'].split('+')[0], '%Y-%m-%d %H:%M:%S')
                        cacheitem = fetchitem(user=fetchuser(username=item['user']['username'], userprofile=fetchprofile(openid=item['user']['userprofile']['openid'], avatar=item['user']['userprofile']['avatar'])), title=item['title'], url=item['url'], lastsubitem=fetchcreate(create=timezone.make_aware(item['lastsubitem']['create'], timezone.get_default_timezone())), tags=item['tags'])
                        itemlist.append(cacheitem)
        else:
            def updatecache():
                cache.delete('cacheitems')
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

            #try:
            if request.user.id == 1 and 'VCAP_SERVICES' in os.environ:
            #if 'VCAP_SERVICES' in os.environ:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                #Zhihu
                #for fetchdate in [[str((datetime.datetime.now() + timedelta(days=1)).strftime('%Y%m%d')), str(datetime.datetime.now().strftime('%Y%m%d'))], [str(datetime.datetime.now().strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))], [str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=2)).strftime('%Y%m%d'))]]:
                #    zhihuurl = 'http://news.at.zhihu.com/api/3/news/before/' + fetchdate[0]
                if request.GET.get('page') and request.GET.get('page').isdigit():
                    page = int(request.GET.get('page'))
                else:
                    page = 1
                fetchdate = datetime.datetime.now() + timedelta(days=(2 - page))
                #fetchdate = datetime.datetime.now() + timedelta(hours=(8 + (1 - page) * 24))
                zhihuurl = 'http://news.at.zhihu.com/api/3/news/before/' + str(fetchdate.strftime('%Y%m%d'))
                print(str(datetime.datetime.now()))
                print(zhihuurl)
                hdr = {
                    'User-Agent': 'hulu'
                }
                req = urllib2.Request(zhihuurl, headers=hdr)
                zhihujson = json.loads(urllib2.urlopen(req, context=ctx).read())
                zhihudate = zhihujson['date']
                #if int(zhihudate) == int(fetchdate[1]):
                zhihucontent = zhihujson['stories']
                for i in zhihucontent:
                    zhihuitem = fetchitem(user=fetchuser(username=u'知乎日报', userprofile=fetchprofile(openid='Zhihu', avatar='https://www.zhihu.com/favicon.ico')), title=i['title'], url='http://daily.zhihu.com/story/'+str(i['id']), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(zhihudate[:4] + i['ga_prefix'], '%Y%m%d%H'), timezone.get_default_timezone())), tags=None)
                    itemlist.append(zhihuitem)
                    fetchitems.append(zhihuitem)

                if not request.GET.get('page'):
                    #V2EX
                    v2exurl = 'https://www.v2ex.com/api/topics/hot.json'
                    v2exjson = json.loads(urllib2.urlopen(v2exurl, context=ctx).read())
                    for i in v2exjson:
                        v2exitem = fetchitem(user=fetchuser(username='V2EX', userprofile=fetchprofile(openid='V2EX', avatar='https://www.v2ex.com/static/img/icon_rayps_64.png')), title=i['title'], url=i['url'].replace('http://', 'https://'), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.fromtimestamp(int(i['created'])), timezone.get_default_timezone())), tags=None)
                        itemlist.append(v2exitem)
                        fetchitems.append(v2exitem)

                    #Google News
                    newsurl = 'https://news.google.com/news?output=rss&hl=zh-CN'
                    req = urllib2.Request(newsurl)
                    result = urllib2.urlopen(req, context=ctx).read()
                    items = re.split('<item>|</item> <item>|</item>', result)
                    items.pop(0)
                    items.pop(-1)
                    for item in items:
                        hp = HTMLParser.HTMLParser()
                        title = hp.unescape(re.split('<title>|</title> <title>|</title>', item)[1])
                        newstime = re.split('<pubDate>|</pubDate> <pubDate>|</pubDate>', item)[1]
                        url = re.split('<link>|</link> <link>|</link>', item)[1].split('url=')[1]
                        newsitem = fetchitem(user=fetchuser(username='Google News', userprofile=fetchprofile(openid='Google News', avatar='https://mail.qq.com/favicon.ico')), title=title, url=url, lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(newstime, '%a, %d %b %Y %H:%M:%S GMT'), timezone.get_default_timezone())), tags=None)
                        itemlist.append(newsitem)
                        fetchitems.append(newsitem)

            #    if not request.GET.get('page'):
            #        updatecache()
            #    else:
            #        pass
            #except:
            #    if not request.GET.get('page'):
            #        updatecache()
            #    else:
            #        pass
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
        'tags': tags,
        'pitems': pitems,
        'bluemix': 'True' if 'VCAP_SERVICES' in os.environ else None
    }
    if request.GET.get('type') == 'json':
        content = {
            'page': currentpage,
            'items': []
        }

        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    return render(request, 'main/index.html', content)

def ttt(request):
    return render(request, 'other/ttt.html', {})

def sitemap(request):
    try:
        tags = Tag.objects.all().order_by('?')[:10]
    except Tag.DoesNotExist:
        tags = None
    content = {
        'tags': tags
    }
    return render(request, 'main/sitemap.txt', content)

@csrf_exempt
def jk(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
        return redirect('/')

    jkimg = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jk', username, username + '.jpg')

    if request.method == 'GET':
        if request.user.is_authenticated():
            if request.user.username == username:
                content = {

                }
                if os.path.isfile(jkimg):
                    mtime_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(jkimg))
                    if request.GET.get('type') == 'json':
                        content = {
                            'mtime': mtime_delta.total_seconds()
                        }

                        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                    if request.GET.get('type') == 'jkimg':
                        try:
                            with open(jkimg, "rb") as destination:
                                return HttpResponse(destination.read(), content_type="image/jpeg")
                        except:
                            return HttpResponse()
                    content['mtime'] = mtime_delta.total_seconds()
                return render(request, 'other/jk.html', content)
            else:
                return redirect('/')
        else:
            return redirectlogin(request)
    if request.method == 'POST':
        try:
            os.system('chmod +x ' + os.path.join(settings.MEDIA_ROOT, 'avatar'))
            os.system('mkdir -p ' + os.path.dirname(jkimg))
            os.system('chmod +x ' + os.path.dirname(jkimg))
        except:
            pass
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with open(jkimg, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)

            monitoremail = EmailMessage(
                '[Hulu Monitor] - ' + username + ' - ' + str(datetime.datetime.now()),
                '',
                os.environ['system_mail_username'],
                [os.environ['receive_mail']],
                [],
                reply_to=[],
                headers={},
            )
            monitoremail.attach_file(jkimg)
            monitoremail.send(fail_silently=False)

        return render(request, 'other/jk.html', {})

def app(request):
    if request.user.is_authenticated():
        content = {

        }
        if request.method == 'GET':
            if request.GET.get('type') == 'json':
                messagelist = []
                ursession = []

                def getuir():
                    useritemrelationship = None
                    if request.GET.get('uirid'):
                        try:
                            useritemrelationship = UserItemRelationship.objects.filter(type="message").filter(user=request.user).filter(id__gt=request.GET.get('uirid')).order_by('-id').prefetch_related('item_set', 'item_set__useritemrelationship', 'item_set__useritemrelationship__user', 'item_set__itemcontent_set')
                        except Object.DoesNotExist:
                            useritemrelationship = None
                    else:
                        try:
                            useritemrelationship = UserItemRelationship.objects.filter(type="message").filter(user=request.user).order_by('-id').prefetch_related('item_set', 'item_set__useritemrelationship', 'item_set__useritemrelationship__user', 'item_set__itemcontent_set')
                        except Object.DoesNotExist:
                            useritemrelationship = None

                    if useritemrelationship:
                        paginator = Paginator(useritemrelationship, 100)
                        page = request.GET.get('page')
                        try:
                            useritemrelationship = paginator.page(page).object_list
                        except PageNotAnInteger:
                            useritemrelationship = paginator.page(1).object_list
                        except EmptyPage:
                            useritemrelationship = paginator.page(paginator.num_pages).object_list

                        for ur in useritemrelationship:
                            if not ur:
                                return None
                            for message in ur.item_set.all():
                                if not message:
                                    return None
                                urusers = []
                                murs = message.useritemrelationship.all()
                                for mur in murs:
                                    if mur.user not in urusers:
                                        urusers.append(mur.user)
                                if len(urusers) != len(murs):
                                    return None
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

                        #itemcontent = ItemContent.objects.filter(item=message)
                        itemcontent = message. itemcontent_set.all()
                        message.create = itemcontent[0].create
                        message.title = itemcontent[0].content.strip().splitlines()[0]
                        message.lastsubitem = itemcontent[0]

                        #subitem = message.get_all_items(include_self=False)
                        #if subitem:
                        #    subitem.sort(key=lambda item:item.create, reverse=True)
                        #    #itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                        #    itemcontent = subitem[0].itemcontent_set.all().reverse()
                        #    message.subitemcount = len(subitem)
                        #    message.lastsubitem = subitem[0]
                        #else:
                        #    message.lastsubitem = itemcontent[0]

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

                messagelist = sorted(messagelist, key=lambda item:item['messages'][0].lastsubitem.create, reverse=False)

                messagesessions = []
                for ms in messagelist:
                    urusers = []
                    for uruser in ms['urusers']:
                        urusers.append({
                            'username': uruser.username,
                            'info': escape(uruser.userprofile.info),
                            'avatar': (uruser.userprofile.openid) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
                            'profile': escape(uruser.userprofile.profile),
                            'page': escape(uruser.userprofile.page),
                        })

                    lastmessage = {
                        'content': escape(ms['messages'][0].lastsubitem.content),
                        'datetime': str(ms['messages'][0].lastsubitem.create + timedelta(hours=8))
                    }

                    messages = []
                    for message in sorted(ms['messages'], key=lambda item:item.lastsubitem.create, reverse=False)[-100:]:
                        clientcreate = ''
                        if cache.get('cachemessages' + str(message.id)):
                            clientcreate = cache.get('cachemessages' + str(message.id))

                        messages.append({
                            'id': str(message.id),
                            'user': {
                                'username': message.user.username,
                                'info': escape(message.user.userprofile.info),
                                'avatar': (message.user.userprofile.openid) and str(message.user.userprofile.avatar) or ((message.user.userprofile.avatar) and '/s/' + str(message.user.userprofile.avatar) or '/s/avatar/n.png'),
                                'profile': escape(message.user.userprofile.profile),
                                'page': escape(message.user.userprofile.page),
                            },
                            'create': str(message.lastsubitem.create + timedelta(hours=8)),
                            'content': escape(message.lastsubitem.content),
                            'clientcreate': clientcreate
                        })

                    messagesession = {
                        'urusers': urusers,
                        'lastmessage': lastmessage,
                        'messages': messages
                    }
                    messagesessions.append(messagesession)

                uirid = request.GET.get('uirid')
                if useritemrelationship:
                    uirid = str(useritemrelationship[0].id)

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

                        cache.set('cachemessages' + str(item.id), request.POST.get('clientcreate').strip())

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

                        content = {
                            'status': 'success',
                            'id': str(item.id)
                        }
                        return jsonp(request, content)

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
                        'info': escape(uruser.userprofile.info),
                        'avatar': (uruser.userprofile.openid) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
                        'profile': escape(uruser.userprofile.profile),
                        'page': escape(uruser.userprofile.page),
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
        return render(request, 'main/app.html', content)
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return jsonp(request, content)
        return redirectlogin(request)

def weixin(request):
    if request.method == 'GET':
        signature = request.GET.get('signature')
        timestamp = request.GET.get('timestamp')
        nonce = request.GET.get('nonce')
        echostr = request.GET.get('echostr')
        token = 'weixin'

        if signature and timestamp and nonce and echostr:
            tmparray = [token, timestamp, nonce]
            tmparray.sort()
            tmpstr = ''.join(tmparray)
            tmpstr = hashlib.sha1(tmpstr).hexdigest()
            if tmpstr == signature:
                return HttpResponse(echostr)
            else:
                return redirect('/')
        else:
            return redirect('/')
