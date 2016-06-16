from django.http import HttpResponse
import json

def jsonp(request, content):
    if request.GET.get('callback'):
        callback = request.GET.get('callback').strip()
        return HttpResponse(callback + '(' + json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4) + ')', content_type="application/json; charset=utf-8")
    else:
        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")

def resetdb():
    from django.db import connection
    try:
        conn = connection.cursor()
    except OperationalError:
        connected = False
        connection.close()
    else:
        connected = True

def checkmodule(module):
    import imp
    try:
        imp.find_module(module)
        return True
    except ImportError:
        return False
