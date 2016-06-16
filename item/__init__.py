import os
from django.conf import settings
import shutil
import re
from hulu import *

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
