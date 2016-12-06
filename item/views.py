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
        try:
            items = Item.objects.select_related('user').filter(user=request.user).filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=True)).order_by('-id').prefetch_related('itemcontent_set')
            items = sorted(items, key=lambda item:item.id, reverse=True)

            subitems = Item.objects.filter(user=request.user).filter(useritemrelationship__isnull=True).filter(Q(belong__isnull=False)).order_by('-id').prefetch_related('itemcontent_set')
            belongitems = []
            for subitem in subitems:
                rootitems = subitem.get_root_items()
                for rootitem in rootitems:
                    if rootitem not in belongitems and rootitem.user != request.user:
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

            paginator = Paginator(items, 10)
            page = request.GET.get('page')
            try:
                items = paginator.page(page)
            except PageNotAnInteger:
                items = paginator.page(1)
            except EmptyPage:
                items = paginator.page(paginator.num_pages)

            paginator_belong = Paginator(belongitems, 10)
            page = request.GET.get('page')
            try:
                belongitems = paginator_belong.page(page)
            except PageNotAnInteger:
                belongitems = paginator_belong.page(1)
            except EmptyPage:
                belongitems = paginator_belong.page(paginator_belong.num_pages)
        except Item.DoesNotExist:
            items = None
            belongitems = None
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
            if request.POST.get('content').strip() == '' and (not request.FILES or 'VCAP_SERVICES' in os.environ):
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
        if itemcontent[0].content:
            item.title = itemcontent[0].content.strip().splitlines()[0]
        else:
            contentattachment = itemcontent[0].contentattachment_set.all()
            if contentattachment:
                item.title = contentattachment[0].title
            else:
                item.title = str(item.id)
        item.firstcontent = ''.join(itemcontent[0].content.strip().splitlines(True)[1:])
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
        #把信息改为只有作者可见
        if request.user.id == 1 and request.GET.get('status') == 'private':
            item.status = 'private'
            item.save()
            return redirect('/')

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
                if itemcontent[0].content:
                    item.title = itemcontent[0].content.strip().splitlines()[0]
                else:
                    contentattachment = itemcontent[0].contentattachment_set.all()
                    if contentattachment:
                        item.title = contentattachment[0].title
                    else:
                        item.title = str(item.id)
                item.firstcontent = ''.join(itemcontent[0].content.strip().splitlines(True)[1:])
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
            weiboclient = Client('4157302825', '517583a4b3197943dda94a45c5823c61', 'hulu.im', username=os.environ['weibo_username'], password=os.environ['weibo_password'])
            content = weiboclient.post('statuses/upload', status='https://hulu.im', pic=request.FILES['file'])
            return jsonp(request, content)
    else:
        return redirect('/')
