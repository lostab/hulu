import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hulu.settings")
from django.conf import settings
django.setup()

from item.views import checklink

checklinks()
