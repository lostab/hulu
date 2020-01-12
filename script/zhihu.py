# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
from datetime import datetime, timedelta
import urllib2
import urllib
import json
import ssl
import hashlib

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(basedir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hulu.settings")
import django
django.setup()
from hulu import *
from django.contrib.auth.models import User
from item.models import *

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hdr = {
    'User-Agent': 'hulu'
}

fetchdate = datetime.datetime.now() + timedelta(days=1)

zhihuurl = 'http://news-at.zhihu.com/api/4/news/before/' + str(fetchdate.strftime('%Y%m%d'))

#try:
req = urllib2.Request(zhihuurl, headers=hdr)
zhihujson = json.loads(urllib2.urlopen(req, context=ctx).read())
zhihudate = zhihujson['date']
zhihucontent = zhihujson['stories']
for i in zhihucontent:
    storytitle = i['title'].encode('utf-8')
    storyid = i['id']
    storyurl = 'http://news-at.zhihu.com/api/4/news/' + str(i['id'])
    #print(storytitle)
    print(storyid)
    print(storyurl)

    ifexist = False
    # remove old file
    if os.path.isfile(basedir + '/script/zhihu-' + str(datetime.datetime.now().strftime('%Y%m%d')) + '.txt'):
        os.remove(basedir + '/script/zhihu-' + str(datetime.datetime.now().strftime('%Y%m%d')) + '.txt')
    # check new file
    zhihufile = basedir + '/script/zhihu-' + str(fetchdate.strftime('%Y%m%d')) + '.txt'
    if os.path.isfile(zhihufile):
        fo = open(zhihufile, 'r')
        for line in fo.readlines():
            if str(storyid) in line:
                ifexist = True
        fo.close()

    if not ifexist:
        storyreq = urllib2.Request(storyurl, headers=hdr)
        storyjson = json.loads(urllib2.urlopen(storyreq, context=ctx).read())
        storycontent = storyjson['body'].split('<div class=\"content\">')[1].split('<div class=\"view-more\">')[0].strip()

        fo = open(basedir + '/script/transaccount.txt', 'r')
        transaccount = fo.read().split(' ')
        fo.close()
        transappid = transaccount[0]
        transsalt = 'hulu'
        transsign = transappid + storytitle + storycontent + transsalt + transaccount[1]
        hl = hashlib.md5()
        hl.update(transsign.encode(encoding='utf-8'))
        transsign = hl.hexdigest()

        transurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
        transdata = {
            'appid': transappid,
            'salt': transsalt,
            'sign': transsign,
            'from': 'auto',
            'to': 'en',
            'q': storytitle + storycontent
        }
        transreq = urllib2.Request(transurl, data=urllib.urlencode(transdata), headers=hdr)
        transjson = json.loads(urllib2.urlopen(transreq, context=ctx).read())
        transcontent = ''
        for i in transjson['trans_result']:
            transcontent += i['dst'].encode('utf-8')
        #print(transcontent)
        
        # save to db
        user = User.objects.get(username='way')
        item = Item(user=user)
        item.save()
        itemcontent = ItemContent(item=item, content=transcontent)
        itemcontent.save()

        # save to file
        fo = open(zhihufile, 'a')
        fo.write(str(storyid) + '\n')
        fo.close()
#except:
#    pass