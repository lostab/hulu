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
from django.contrib.sites.shortcuts import get_current_site

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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
        if q:
            items = items.filter(Q(itemcontent__content__icontains=q)).distinct()

        items = sort_items(items, request.GET.get('page'))

        currentpage = items.number
        pitems = items

        itemlist = []
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
            if request.user.id == 1 and ('VCAP_SERVICES' in os.environ or 'getnews' in os.environ):
            #if 'VCAP_SERVICES' in os.environ:
                hdr = {
                    'User-Agent': 'hulu'
                }
                #Zhihu
                #for fetchdate in [[str((datetime.datetime.now() + timedelta(days=1)).strftime('%Y%m%d')), str(datetime.datetime.now().strftime('%Y%m%d'))], [str(datetime.datetime.now().strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))], [str((datetime.datetime.now() - timedelta(days=1)).strftime('%Y%m%d')), str((datetime.datetime.now() - timedelta(days=2)).strftime('%Y%m%d'))]]:
                #    zhihuurl = 'http://news.at.zhihu.com/api/3/news/before/' + fetchdate[0]
                if request.GET.get('page') and request.GET.get('page').isdigit():
                    page = int(request.GET.get('page'))
                else:
                    page = 1
                fetchdate = datetime.datetime.now() + timedelta(days=(2 - page))
                #fetchdate = datetime.datetime.now() + timedelta(hours=(8 + (1 - page) * 24))
                #zhihuurl = 'http://news.at.zhihu.com/api/3/news/before/' + str(fetchdate.strftime('%Y%m%d'))
                zhihuurl = 'http://news-at.zhihu.com/api/4/news/before/' + str(fetchdate.strftime('%Y%m%d'))
                #print(str(datetime.datetime.now()))
                #print(zhihuurl)
                try:
                    req = urllib2.Request(zhihuurl, headers=hdr)
                    zhihujson = json.loads(urllib2.urlopen(req, context=ctx).read())
                    zhihudate = zhihujson['date']
                    #if int(zhihudate) == int(fetchdate[1]):
                    zhihucontent = zhihujson['stories']
                    for i in zhihucontent:
                        zhihuitem = fetchitem(user=fetchuser(username=u'知乎日报', userprofile=fetchprofile(openid='Zhihu', avatar='https://www.zhihu.com/favicon.ico')), title=i['title'], url='http://daily.zhihu.com/story/'+str(i['id']), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(zhihudate[:4] + i['ga_prefix'], '%Y%m%d%H'), timezone.get_default_timezone())), tags=None)
                        itemlist.append(zhihuitem)
                        fetchitems.append(zhihuitem)
                except:
                    pass

                if not request.GET.get('page'):
                    #V2EX
                    v2exurl = 'https://www.v2ex.com/api/topics/hot.json'
                    try:
                        req = urllib2.Request(v2exurl, headers=hdr)
                        v2exjson = json.loads(urllib2.urlopen(req, context=ctx).read())
                        for i in v2exjson:
                            v2exitem = fetchitem(user=fetchuser(username='V2EX', userprofile=fetchprofile(openid='V2EX', avatar='https://www.v2ex.com/static/img/v2ex_192.png')), title=i['title'], url=i['url'].replace('http://', 'https://'), lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.fromtimestamp(int(i['created'])), timezone.get_default_timezone())), tags=None)
                            itemlist.append(v2exitem)
                            fetchitems.append(v2exitem)
                    except:
                        pass

                    #Google News
                    newsurl = 'https://news.google.com/news?output=rss&hl=zh-CN'
                    try:
                        req = urllib2.Request(newsurl)
                        result = urllib2.urlopen(req, context=ctx).read()
                        items = re.split('<item>|</item> <item>|</item>', result)
                        items.pop(0)
                        items.pop(-1)
                        for item in items:
                            hp = HTMLParser.HTMLParser()
                            title = hp.unescape(re.split('<title>|</title> <title>|</title>', item)[1]).encode("utf-8")
                            newstime = re.split('<pubDate>|</pubDate> <pubDate>|</pubDate>', item)[1]
                            url = re.split('<link>|</link> <link>|</link>', item)[1].split('url=')[1]
                            newsitem = fetchitem(user=fetchuser(username='Google News', userprofile=fetchprofile(openid='Google News', avatar='https://mail.qq.com/favicon.ico')), title=title, url=url, lastsubitem=fetchcreate(create=timezone.make_aware(datetime.datetime.strptime(newstime, '%a, %d %b %Y %H:%M:%S GMT'), timezone.get_default_timezone())), tags=None)
                            itemlist.append(newsitem)
                            fetchitems.append(newsitem)
                    except:
                        pass

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
        'getnews': 'True' if ('VCAP_SERVICES' in os.environ or 'getnews' in os.environ) else None
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
    content = ''
    for tag in tags:
        content += ('https://' if request.is_secure else 'http://') + request.get_host() + '/t/' + str(tag.id) + '/\r\n'
    return HttpResponse(content)

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
            try:
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
            except:
                pass

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
                            'avatar': (uruser.userprofile.openid and '//' in str(uruser.userprofile.avatar)) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
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
                                'avatar': (message.user.userprofile.openid and '//' in str(message.user.userprofile.avatar)) and str(message.user.userprofile.avatar) or ((message.user.userprofile.avatar) and '/s/' + str(message.user.userprofile.avatar) or '/s/avatar/n.png'),
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
                        'avatar': (uruser.userprofile.openid and '//' in str(uruser.userprofile.avatar)) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
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

@csrf_exempt
def weixin(request):
    def get_access_token():
        apiurl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' + os.environ['weixin_appid_yh'] + '&secret=' + os.environ['weixin_secret_yh']
        print(apiurl)
        access_token_result = json.loads(urllib2.urlopen(apiurl, context=ctx).read())
        if 'access_token' in access_token_result:
            return access_token_result['access_token']
        else:
            return get_access_token()

    def get_user_info(openid):
        if cache.get('access_token'):
            apiurl = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=' + cache.get('access_token') + '&openid=' + openid + '&lang=zh_CN'
            print(apiurl)
            user_info_result = json.loads(urllib2.urlopen(apiurl, context=ctx).read())
            if 'openid' in user_info_result:
                return user_info_result
            else:
                cache.set('access_token', get_access_token(), 7200)
                return get_user_info(openid)
        else:
            cache.set('access_token', get_access_token(), 7200)
            return get_user_info(openid)

    token = 'weixin'

    if request.method == 'GET':
        signature = request.GET.get('signature')
        timestamp = request.GET.get('timestamp')
        nonce = request.GET.get('nonce')
        echostr = request.GET.get('echostr')

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
            if request.user.is_authenticated() and request.user.id == 1:
                if cache.get('last_msg'):
                    return HttpResponse(cache.get('last_msg'))
                else:
                    return HttpResponse('')
            else:
                return redirect('/')

    if request.method == 'POST':
        body = request.body
        if body:
            fromuser = body.split('<FromUserName><![CDATA[')[1].split(']]></FromUserName>')[0]
            msgtype = body.split('<MsgType><![CDATA[')[1].split(']]></MsgType>')[0]
            msgid = body.split('<MsgId>')[1].split('</MsgId>')[0]

            if fromuser:
                #user_info_result = get_user_info(fromuser)
                #if 'openid' in user_info_result:
                #    nickname = user_info_result['nickname']
                #    headimgurl = user_info_result['headimgurl']

                if msgtype == 'text':
                    content = body.split('<Content><![CDATA[')[1].split(']]></Content>')[0]
                    #cache.set('last_msg', nickname + headimgurl + content, 3600)
                    cache.set('last_msg', content, 3600)
                elif msgtype == 'image':
                    pilurl = body.split('<PicUrl><![CDATA[')[1].split(']]></PicUrl>')[0]
                    mediaid = body.split('<MediaId><![CDATA[')[1].split(']]></MediaId>')[0]
                    cache.set('last_msg', pilurl, 3600)

        return HttpResponse('')

def coin(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            try:
                coins = Coin.objects.filter(user=request.user).all()
            except Coin.DoesNotExist:
                coins = None
        else:
            coins = None

        apiurl = 'https://api.coinmarketcap.com/v1/ticker/?convert=CNY'
        try:
            req = urllib2.Request(apiurl)
            markets = json.loads(urllib2.urlopen(req, context=ctx).read())
        except:
            markets = None

        content = {
            'coins': coins,
            'markets': markets
        }
        if request.GET.get('type') == 'json':
            coinlist = []
            if coins:
                for coin in coins:
                    coinlist.append({
                        'type': coin.cointype,
                        'hold': coin.coinhold
                    })
            content = {
                'coins': coinlist,
                'markets': markets
            }
            return jsonp(request, content)
        return render(request, 'other/coin.html', content)
    if request.method == 'POST':
        if request.user.is_authenticated():
            if request.POST.get('cointype'):
                cointype = request.POST.get('cointype')
                if request.POST.get('operate') == 'add' and request.POST.get('coinhold'):
                    coinhold = request.POST.get('coinhold')
                    try:
                        coin = Coin.objects.get(user=request.user, cointype=cointype)
                    except Coin.DoesNotExist:
                        coin = Coin(user=request.user)
                    coin.cointype = cointype
                    coin.coinhold = coinhold
                    coin.save()
                if request.POST.get('operate') == 'del':
                    try:
                        coin = Coin.objects.get(user=request.user, cointype=cointype)
                        coin.delete()
                    except Coin.DoesNotExist:
                        pass
        return render(request, 'other/coin.html', {})
