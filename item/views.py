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
import ssl
import HTMLParser
import threading

def Index(request):
    if request.user.is_authenticated():
        items, belongitems = get_item_by_user(request.user, request)

        content = {
            'items': items,
            'belongitems': belongitems
        }
        if request.GET.get('type') == 'json':
            content = {
                'page': items.number,
                'items': []
            }
            for item in items:
                content['items'].append({
                    'id': item.id
                })
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render(request, 'item/index.html', content)
    else:
        return redirectlogin(request)

def Create(request):
    if request.user.is_authenticated():
        if request.GET.get('t'):
            tagname = request.GET.get('t').strip()
            if tagname:
                try:
                    tag = Tag.objects.filter(name=tagname)[:1].get()
                except Tag.DoesNotExist:
                    tag = None
            else:
                tag = None
        else:
            tagname = None
            tag = None

        if request.method == 'GET':
            if request.GET.get('t') == '':
                return redirect('/i/create/')

            content = {
                'tagname': tagname
            }
            return render(request, 'item/create.html', content)

        if request.method == 'POST':
            if ((not request.POST.get('content') or request.POST.get('content').strip() == '') and (not request.FILES or 'VCAP_SERVICES' in os.environ)):
                content = {

                }
                return render(request, 'item/create.html', content)

            form = ItemContentForm(request.POST)
            if form.is_valid():
                ItemContentInlineFormSet = inlineformset_factory(ItemContent, ContentAttachment, form=ItemContentForm)
                for attachmentfile in request.FILES.getlist('file'):
                    attachmentform = ContentAttachmentForm(request.POST, request.FILES)
                    if attachmentform.is_valid():
                        pass
                    else:
                        content = {
                            'form': form
                        }
                        return render(request, 'item/create.html', content)

                item = Item(user=request.user)
                item.save()
                itemcontent = ItemContent(item=item)
                itemcontentform = ItemContentForm(request.POST, instance=itemcontent)
                itemcontent = itemcontentform.save()
                itemcontent.save()

                if tagname:
                    if not tag:
                        tag = Tag()
                        tag.name = tagname
                        tag.save()
                    item.tag.add(tag)
                    item.save()


                if 'VCAP_SERVICES' not in os.environ:
                    #attach save
                    for attachmentfile in request.FILES.getlist('file'):
                        attachment = ContentAttachment(itemcontent=itemcontent)
                        attachmentform = ContentAttachmentForm(request.POST, request.FILES, instance=attachment)
                        if attachmentform.is_valid():
                            contentattachment = attachmentform.save()
                            contentattachment.title = attachmentfile.name
                            contentattachment.contenttype = str(attachmentfile.content_type)
                            contentattachment.save()

                            #convert img to svg
                            img2svg(contentattachment)

                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = request.META['REMOTE_ADDR']
                if x_forwarded_for:
                    ip = x_forwarded_for.split(', ')[-1]

                itemcontent.ip = ip
                itemcontent.ua = request.META['HTTP_USER_AGENT']

                itemcontent.save()
            else:
                content = {
                    'item': item,
                    'reply': reply,
                    'form': form
                }
                return render(request, 'item/create.html', content)

            return redirect('/i/' + str(item.id) + '/')
    else:
        return redirectlogin(request)

def View(request, id):
    try:
        item = Item.objects.filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).get(id=id)
        #itemcontent = ItemContent.objects.filter(item=item)
        itemcontent = item.itemcontent_set.all()
        #取第一个内容首行作为标题
        #if itemcontent[0].content:
        #    item.title = itemcontent[0].content.strip().splitlines()[0]
        #else:
        #    contentattachment = itemcontent[0].contentattachment_set.all()
        #    if contentattachment:
        #        item.title = contentattachment[0].title
        #    else:
        #        item.title = str(item.id)
        #item.firstcontent = ''.join(itemcontent[0].content.strip().splitlines(True)[1:])

        #取最后一个内容首行作为标题
        if itemcontent.last().content:
            item.title = itemcontent.last().content.strip().splitlines()[0]
        else:
            contentattachment = itemcontent.last().contentattachment_set.all()
            if contentattachment:
                item.title = contentattachment[0].title
            else:
                item.title = str(item.id)
        item.firstcontent = ''.join(itemcontent.last().content.strip().splitlines(True)[1:])
    except Item.DoesNotExist:
        item = None
    if not item:
        return redirect('/')

    try:
        items = item.get_all_items(include_self=False)
        items.sort(key=lambda item:item.create, reverse=False)
        paginator = Paginator(items, 100)
        page = request.GET.get('page')
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
    except Item.DoesNotExist:
        items = None

    if request.method == 'GET':
        try:
            UserNotify.objects.filter(user=request.user.id).filter(item=item).delete()
            UserNotify.objects.filter(user=request.user.id).filter(item__in=set(item.id for item in items)).delete()
        except UserNotify.DoesNotExist:
            pass

        reply = None
        if request.GET.get('reply'):
            replyid = str(request.GET.get('reply'))
            try:
                reply = Item.objects.get(id=replyid)
            except UserNotify.DoesNotExist:
                pass

        if not item or (item.status == 'private' and item.user != request.user):
            content = {
                'item': None
            }
            return render(request, 'item/view.html', content)

        try:
            tags = Tag.objects.all().order_by('?')[:10]
        except Tag.DoesNotExist:
            tags = None

        content = {
            'item': item,
            'items': items,
            'reply': reply,
            'tags': tags
        }
        return render(request, 'item/view.html', content)
    if request.method == 'POST':
        if not item or (item.status == 'private' and item.user != request.user):
            content = {
                'item': None
            }
            return render(request, 'item/view.html', content)
        if request.user.is_authenticated():
            #把信息改为只有私有
            if request.user.id == 1 and request.POST.get('status') == 'private':
                item.status = 'private'
                item.save()
                return redirect('/')

            if item.user == request.user and request.POST.get('tagname'):
                tagname = request.POST.get('tagname').strip()
                if tagname != '':
                    if request.POST.get('operate') == 'remove':
                        try:
                            tags = Tag.objects.filter(name=tagname).all()
                            for tag in tags:
                                item.tag.remove(tag)
                                item.save()
                        except:
                            pass
                    else:
                        try:
                            tag = Tag.objects.filter(name=tagname)[:1].get()
                        except Tag.DoesNotExist:
                            tag = Tag()
                            tag.name = tagname
                            tag.save()
                        if tag not in item.tag.all():
                            item.tag.add(tag)
                            item.save()
                        if request.POST.get('type') == 'json':
                            content = str(tag.id)
                            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                return redirect('/i/' + id + '/')

            reply = None
            if request.POST.get('reply'):
                replyid = str(request.POST.get('reply'))
                try:
                    reply = Item.objects.get(id=replyid)
                except UserNotify.DoesNotExist:
                    pass

            if (not request.POST.get('content') or request.POST.get('content').strip() == '') and (not request.FILES or 'VCAP_SERVICES' in os.environ):
                content = {
                    'item': item,
                    'items': items,
                    'reply': reply
                }
                return render(request, 'item/view.html', content)

            form = ItemContentForm(request.POST)
            if form.is_valid():
                ItemContentInlineFormSet = inlineformset_factory(ItemContent, ContentAttachment, form=ItemContentForm)
                for attachmentfile in request.FILES.getlist('file'):
                    attachmentform = ContentAttachmentForm(request.POST, request.FILES)
                    if attachmentform.is_valid():
                        pass
                    else:
                        content = {
                            'item': item,
                            'items': items,
                            'reply': reply,
                            'form': form
                        }
                        return render(request, 'item/view.html', content)

                new_item = Item(user=request.user)
                new_item.save()
                if reply:
                    new_item.belong.add(reply)
                else:
                    new_item.belong.add(item)

                itemcontent = ItemContent(item=new_item)
                itemcontentform = ItemContentForm(request.POST, instance=itemcontent)
                itemcontent = itemcontentform.save()
                itemcontent.save()

                if 'VCAP_SERVICES' not in os.environ:
                    #attach save
                    for attachmentfile in request.FILES.getlist('file'):
                        attachment = ContentAttachment(itemcontent=itemcontent)
                        attachmentform = ContentAttachmentForm(request.POST, request.FILES, instance=attachment)
                        if attachmentform.is_valid():
                            contentattachment = attachmentform.save()
                            contentattachment.title = attachmentfile.name
                            contentattachment.contenttype = str(attachmentfile.content_type)
                            contentattachment.save()

                            #convert img to svg
                            img2svg(contentattachment)

                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = request.META['REMOTE_ADDR']
                if x_forwarded_for:
                    ip = x_forwarded_for.split(', ')[-1]

                itemcontent.ip = ip

                itemcontent.ua = request.META['HTTP_USER_AGENT']

                itemcontent.save()

                if reply:
                    if request.user != reply.user:
                        notify = UserNotify(user=reply.user, item=new_item)
                        notify.save()
                else:
                    if request.user != item.user:
                        notify = UserNotify(user=item.user, item=new_item)
                        notify.save()

                return redirect('/i/' + id + '/#' + str(new_item.id))
            else:
                content = {
                    'item': item,
                    'reply': reply,
                    'form': form
                }
                return render(request, 'item/view.html', content)
        else:
            return redirectlogin(request)

def Update(request, id):
    if request.user.is_authenticated():
        try:
            item = Item.objects.filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).get(id=id)
            if item.user.username != request.user.username:
                item = None
            else:
                itemcontent = item.itemcontent_set.all()
                #取第一个内容首行作为标题
                #if itemcontent[0].content:
                #    item.title = itemcontent[0].content.strip().splitlines()[0]
                #else:
                #    contentattachment = itemcontent[0].contentattachment_set.all()
                #    if contentattachment:
                #        item.title = contentattachment[0].title
                #    else:
                #        item.title = str(item.id)
                #item.firstcontent = ''.join(itemcontent[0].content.strip().splitlines(True)[1:])
                #取最后一个内容首行作为标题

                if itemcontent.last().content:
                    item.title = itemcontent.last().content.strip().splitlines()[0]
                else:
                    contentattachment = itemcontent.last().contentattachment_set.all()
                    if contentattachment:
                        item.title = contentattachment[0].title
                    else:
                        item.title = str(item.id)
                item.firstcontent = ''.join(itemcontent.last().content.strip().splitlines(True)[1:])
        except Item.DoesNotExist:
            item = None
        if not item:
            return redirect('/i/' + id)
        if request.method == 'GET':
            content = {
                'item': item
            }
            return render(request, 'item/update.html', content)
        if request.method == 'POST':
            if item:
                if request.POST.get('content').strip() == '' and (not request.FILES or 'VCAP_SERVICES' in os.environ):
                    content = {
                        'item': item
                    }
                    return render(request, 'item/update.html', content)

                form = ItemContentForm(request.POST)
                if form.is_valid():
                    ItemContentInlineFormSet = inlineformset_factory(ItemContent, ContentAttachment, form=ItemContentForm)
                    for attachmentfile in request.FILES.getlist('file'):
                        attachmentform = ContentAttachmentForm(request.POST, request.FILES)
                        if attachmentform.is_valid():
                            pass
                        else:
                            content = {
                                'item': item,
                                'form': form
                            }
                            return render(request,'item/update.html', content)

                    itemcontent = ItemContent(item=item)
                    itemcontentform = ItemContentForm(request.POST, instance=itemcontent)
                    itemcontent = itemcontentform.save()
                    itemcontent.save()

                    if 'VCAP_SERVICES' not in os.environ:
                        #attach save
                        for attachmentfile in request.FILES.getlist('file'):
                            attachment = ContentAttachment(itemcontent=itemcontent)
                            attachmentform = ContentAttachmentForm(request.POST, request.FILES, instance=attachment)
                            if attachmentform.is_valid():
                                contentattachment = attachmentform.save()
                                contentattachment.title = attachmentfile.name
                                contentattachment.contenttype = str(attachmentfile.content_type)
                                contentattachment.save()

                                #convert img to svg
                                img2svg(contentattachment)

                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    ip = request.META['REMOTE_ADDR']
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(', ')[-1]

                    itemcontent.ip = ip

                    itemcontent.ua = request.META['HTTP_USER_AGENT']

                    itemcontent.save()

                    return redirect('/i/' + id)

                else:
                    content = {
                        'form': form
                    }
                    return render(request,'item/update.html', content)
            else:
                return redirect('/i/' + id)
    else:
        return redirect('/u/login/?next=/i/update/' + id)

def Cancel(request, id):
    if request.user.is_authenticated():
        try:
            item = Item.objects.get(id=id)
            if item.user.username == request.user.username:
                item.status = 'cancel'
                item.save()
        except Item.DoesNotExist:
            pass
        return redirect('/i/' + id)
    else:
        return redirect('/u/login/?next=/i/update/' + id)

if 'weibo_username' in os.environ:
    from weibo import Client

def wbimg(request):
    if 'weibo_username' in os.environ:
        if request.method == 'POST':
            url = 'https://upload.api.weibo.com/2/statuses/upload.json'
            weiboclient = Client(os.environ['weibo_appkey'], os.environ['weibo_appsecret'], 'hulu.im', username=os.environ['weibo_username'], password=os.environ['weibo_password'])
            content = weiboclient.post('statuses/upload', status='http://hulu.im', pic=request.FILES['file'])
            return jsonp(request, content)
    else:
        return redirect('/')

regex = re.compile(
r'^(?:http|ftp)s?://'
r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
r'localhost|'
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
r'(?::\d+)?'
r'(?:\/?)$', re.IGNORECASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hdr = {
    'User-Agent': 'hulu'
}

urlblist = []

def checklink(url, checktimes):
    try:
        links = Link.objects.filter(url=url).all()
    except:
        links = None
    for link in links:
        if link.url[-1] == '/':
            link.url = link.url[:-1]
            link.save()

        if link.url.split('://')[1] in urlblist:
            link.delete()
            continue

        #if link.logo and not re.match(regex, link.logo):
        #    link.logo = ''
        #    link.save()

        title = ''
        logo = ''
        try:
            req = urllib2.Request(link.url, headers=hdr)
            content = urllib2.urlopen(req, context=ctx, timeout=10).read()
            hp = HTMLParser.HTMLParser()
            title = hp.unescape(content.split('<title>')[1].split('</title>')[0]).encode("utf-8")
            if '<link rel="icon"' in content:
                logo = hp.unescape(content.split('<link rel="icon"')[1].split('>')[0].split('href="')[1].split('"')[0]).encode("utf-8")
            elif '<link rel="shortcut icon"' in content:
                logo = hp.unescape(content.split('<link rel="shortcut icon"')[1].split('>')[0].split('href="')[1].split('"')[0]).encode("utf-8")
            else:
                logo = ''
            if logo != '':
                if logo[0] == '/':
                    if logo[1] != '/':
                        logo = url + logo
                else:
                    logo = url + '/' + logo
                if 'data:' in logo:
                    logo = ''
            else:
                req = urllib2.Request(url + '/favicon.ico', headers=hdr)
                status = urllib2.urlopen(req, context=ctx, timeout=10).getcode()
                if status == 200:
                    logo = url + '/favicon.ico'
            if title:
                link.title = title
                if 'data:' in logo:
                    logo = ''
                link.logo = logo
                link.unreachable = 0
                link.save()
            else:
                link.delete()
        except:
            if checktimes < 3:
                checklink(url, checktimes + 1)
            else:
                if not link.unreachable:
                    link.unreachable = 1
                else:
                    link.unreachable = int(link.unreachable) + 1
                link.save()
                if int(link.unreachable) > 10:
                    link.delete()

def LinkClass(request):
    try:
        links = Link.objects.all().order_by('?')[:100]
    except Link.DoesNotExist:
        links = None

    if request.method == 'GET':
        if request.GET.get('type') == 'fetch':
            if request.GET.get('url'):
                url = request.GET.get('url').strip()
                if re.match(regex, url):
                    title = ''
                    logo = ''
                    try:
                        req = urllib2.Request(url, headers=hdr)
                        content = urllib2.urlopen(req, context=ctx, timeout=10).read()
                        hp = HTMLParser.HTMLParser()
                        title = hp.unescape(content.split('<title>')[1].split('</title>')[0]).encode("utf-8")
                        if '<link rel="icon"' in content:
                            logo = hp.unescape(content.split('<link rel="icon"')[1].split('>')[0].split('href="')[1].split('"')[0]).encode("utf-8")
                        elif '<link rel="shortcut icon"' in content:
                            logo = hp.unescape(content.split('<link rel="shortcut icon"')[1].split('>')[0].split('href="')[1].split('"')[0]).encode("utf-8")
                        else:
                            logo = ''
                        if logo != '':
                            if logo[0] == '/':
                                if logo[1] != '/':
                                    logo = url + logo
                            else:
                                logo = url + '/' + logo
                            if 'data:' in logo:
                                logo = ''
                        else:
                            req = urllib2.Request(url + '/favicon.ico', headers=hdr)
                            status = urllib2.urlopen(req, context=ctx, timeout=10).getcode()
                            if status == 200:
                                logo = url + '/favicon.ico'
                    except:
                        pass
                    content = {
                        'title': title,
                        'logo': logo
                    }
                    return jsonp(request, content)
                else:
                    return redirect('/i/link/')
            else:
                return redirect('/i/link/')

        if request.GET.get('f'):
            url = request.GET.get('f').strip()
            if request.GET.get('check') == 'true':
                checklink(url, 0)
            if re.match(regex, url):
                return redirect(url)
            else:
                return redirect('/i/link/')

        content = {
            'links': links
        }
        return render(request, 'item/link.html', content)

    if request.method == 'POST':
        form = LinkForm(request.POST)

        if form.is_valid() and re.match(regex, form.cleaned_data['url']):
            url = request.POST.get('url').strip()
            if url[-1] == '/':
                url = url[:-1]
            hostname = url.split('://')[1].split('/')[0]
            if not Link.objects.all().filter(Q(url__icontains=hostname)):
                link = form.save(commit=False)
                #link.lastcheck = timezone.now()
                link.save()

            return redirect('/i/link/')
        else:
            return render(request, 'item/link.html', { 'links': links, 'form': form })
