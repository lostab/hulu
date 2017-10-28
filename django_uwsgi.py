#!/usr/bin/env python
# coding: utf-8
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hulu.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
