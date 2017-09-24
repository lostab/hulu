# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
from django.conf import settings
import shutil
import re
from hulu import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta

def deletedir(dir):
    try:
        shutil.rmtree(dir)
    except:
        deletedir(dir)

def img2svg(contentattachment):
    if 'image' in contentattachment.contenttype and checkmodule('PIL'):
        from PIL import Image
        contentattachmentfile = os.path.join(settings.MEDIA_ROOT, str(contentattachment.file))
        contentattachment.contenttype = 'svg'
        contentattachment.file = None
        contentattachment.save()
        im = Image.open(contentattachmentfile)
        im = im.convert('RGB')
        im.save(contentattachmentfile + '.pgm')
        im.close()
        os.system('chmod +x ' + os.path.join(settings.MEDIA_ROOT, 'tool', 'potrace', 'potrace'))
        os.system(os.path.join(settings.MEDIA_ROOT, 'tool', 'potrace', 'potrace ') + contentattachmentfile + '.pgm -s -o ' + contentattachmentfile + '.svg')
        fo = open(contentattachmentfile + '.svg')
        contentattachment.content = re.sub('<metadata>[\s\S]*</metadata>', '', fo.read())
        fo.close()
        contentattachment.save()
        #deletedir(os.path.dirname(contentattachmentfile))
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'file'))
        except:
            pass

def sort_items(items, page):
    itemlist = []

    for item in items:
        #itemcontent = ItemContent.objects.filter(item=item)
        itemcontent = item.itemcontent_set.all()
        if itemcontent:
            item.create = itemcontent[0].create
            #取第一个内容首行作为标题
            #if itemcontent[0].content:
            #    item.title = itemcontent[0].content.strip().splitlines()[0]
            #else:
            #    contentattachment = itemcontent[0].contentattachment_set.all()
            #    if contentattachment:
            #        item.title = contentattachment[0].title
            #    else:
            #        item.title = str(item.id)

            #取最后一个内容首行作为标题
            if itemcontent.last().content:
                item.title = itemcontent.last().content.strip().splitlines()[0]
            else:
                contentattachment = itemcontent.last().contentattachment_set.all()
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
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    return items
