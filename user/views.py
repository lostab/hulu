# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect
import datetime
import urllib2
import json
import time
from django.contrib.auth.models import User
from django.contrib.auth import *
from django.contrib.auth.forms import *
from django.core.mail import send_mail
from hulu import *
from user.models import *
from user.forms import *
from item.models import *
from item.forms import *
from django.db.models import Q
from django.forms.util import ErrorList
from django.core.context_processors import csrf

def Main(request):
    user = request.user
    if user.is_authenticated():
        content = {}
        if request.GET.get('type') == 'json':
            content = {
                'status': 'success',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'name': user.userprofile.info,
                    'avatar': (user.userprofile.openid) and str(user.userprofile.avatar) or ((user.userprofile.avatar) and '/s/' + str(user.userprofile.avatar) or '/s/avatar/n.png'),
                    'page': user.userprofile.page,
                    'create': str(user.userprofile.create),
                }
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render_to_response('user/index.html', content, context_instance=RequestContext(request))
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return redirect('/u/login/?next=/u/')

def Signup(request):
    next = None
    if request.GET.get('next'):
        next = request.META['QUERY_STRING'].split('next=')[1]
        if request.GET.get('next'):
            if request.GET.get('next')[0] != '/':
                return redirect('/u/login/')
            else:
                nextpath = request.GET.get('next').split('?')[0]
                if nextpath[0] != '/' or nextpath in ['', '/', '/u/login/', '/u/signup/']:
                    return redirect('/u/login/')
    if request.user.is_authenticated():
        if request.GET.get('type') == 'json':
            content = {
                'status': 'success'
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        if next:
            return redirect(next)
        else:
            return redirect('/')
    if request.method == 'GET':
        if request.GET.get('type') == 'json':
            content = {
                'csrf_token': unicode(csrf(request)['csrf_token'])
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render_to_response('user/signup.html', {}, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1'] = form.cleaned_data['password2']
            user = User.objects.get(username=username)
            userprofile = UserProfile(user=user)
            userprofile.coin = 10
            userprofile.save()
            user = authenticate(username=username, password=password)
            login(request, user)
            if request.GET.get('type') == 'json':
                content = {
                    'status': 'success'
                }
                return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
            if next:
                return redirect('/u/settings/?prev=signup&next=' + next)
            else:
                return redirect('/u/settings/?prev=signup')
        else:
            if request.GET.get('type') == 'json':
                content = {
                    'status': 'error',
                    'csrf_token': unicode(csrf(request)['csrf_token']),
                    'errors': [(k, map(unicode, v)) for k, v in form.errors.items()]
                }
                return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
            return render_to_response('user/signup.html', { 'form': form }, context_instance=RequestContext(request))

def Login(request):
    next = None
    if request.GET.get('next'):
        next = request.META['QUERY_STRING'].split('next=')[1].split("&type=qq")[0]
    
    if request.GET.get('type') == 'qq':
        qq_app_id = '101192703'
        qq_app_key = '639215ae3f5947c4a5012fab25e0345f'
        if request.GET.get('code'):
            openid = None
            try:
                access_token = str(urllib2.urlopen('https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id=' + qq_app_id + '&client_secret=' + qq_app_key + '&code=' + request.GET.get('code').strip() + '&redirect_uri=' + urllib2.quote('http://' + request.get_host() + '/u/login/?type=qq')).read().split('&')[0].split('access_token=')[1]).strip()
                openid = str(urllib2.urlopen('https://graph.qq.com/oauth2.0/me?access_token=' + access_token).read().split('"openid":"')[1].split('"')[0])
            except:
                pass
            if openid:
                try:
                    user = User.objects.get(userprofile__openid='QQ' + openid)
                except User.DoesNotExist:
                    user = None
                if user:
                    if user.is_active:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        if next:
                            return redirect(next)
                        else:
                            return redirect('/')
                    else:
                        if next:
                            return redirect('/u/login/?next=' + next)
                        else:
                            return redirect('/u/login/')
                else:
                    try:
                        user_info = str(urllib2.urlopen('https://graph.qq.com/user/get_user_info?access_token=' + access_token + '&oauth_consumer_key=' + qq_app_id + '&openid=' + openid).read()).strip()
                        user_info = json.loads(user_info)
                        
                        def getrandomusername(randomusernameplus):
                            randomusernametime = 'QQ' + str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
                            if randomusernameplus == 0:
                                try:
                                    if User.objects.get(username=randomusernametime):
                                        randomusernameplus += 1
                                        return getrandomusername(randomusernameplus)
                                except User.DoesNotExist:
                                    return randomusernametime
                            else:
                                try:
                                    if User.objects.get(username=randomusernametime + str(randomusernameplus)):
                                        randomusernameplus += 1
                                        return getrandomusername(randomusernameplus)
                                except User.DoesNotExist:
                                    return randomusernametime + str(randomusernameplus)
                        
                        user = User.objects.create_user(username=getrandomusername(0), email=openid + '@qq.com')
                        user.save()
                        userprofile = UserProfile(user=user)
                        userprofile.openid = 'QQ' + openid
                        userprofile.info = str(user_info['nickname'].encode('utf-8', 'ignore')).strip()
                        userprofile.avatar = str(user_info['figureurl_qq_2'].strip().replace('http://', 'https://'))
                        userprofile.save()
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        if next:
                            return redirect(next)
                        else:
                            return redirect('/')
                    except:
                        if next:
                            return redirect('/u/login/?next=' + next)
                        else:
                            return redirect('/u/login/')
            else:
                if next:
                    return redirect('/u/login/?next=' + next)
                else:
                    return redirect('/u/login/')
        else:
            if next:
                return redirect('https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=' + qq_app_id + '&redirect_uri=' + urllib2.quote('http://' + request.get_host() + '/u/login/?next=' + next + '&type=qq'))
            else:
                return redirect('https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=' + qq_app_id + '&redirect_uri=' + urllib2.quote('http://' + request.get_host() + '/u/login/?type=qq'))
    
    if request.GET.get('next'):
        if request.GET.get('next')[0] != '/':
            return redirect('/u/login/')
        else:
            nextpath = request.GET.get('next').split('?')[0]
            if nextpath[0] != '/' or nextpath in ['', '/', '/u/login/', '/u/signup/']:
                return redirect('/u/login/')
    if request.user.is_authenticated():
        if request.GET.get('type') == 'json':
            content = {
                'status': 'success'
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        if next:
            return redirect(next)
        else:
            return redirect('/')
    if request.method == 'GET':
        if request.GET.get('type') == 'json':
            content = {
                'csrf_token': unicode(csrf(request)['csrf_token'])
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render_to_response('registration/login.html', { 'next': next }, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.GET.get('type') == 'json':
                        content = {
                            'status': 'success'
                        }
                        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                    if next:
                        return redirect(next)
                    else:
                        return redirect('/')
                else:
                    if request.GET.get('type') == 'json':
                        content = {
                            'status': 'error',
                            'csrf_token': unicode(csrf(request)['csrf_token']),
                            'errors': [(k, map(unicode, v)) for k, v in form.errors.items()]
                        }
                        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                    return render_to_response('registration/login.html', { 'form': form, 'next': next }, context_instance=RequestContext(request))
            else:
                if request.GET.get('type') == 'json':
                    content = {
                        'status': 'error',
                        'csrf_token': unicode(csrf(request)['csrf_token']),
                        'errors': [(k, map(unicode, v)) for k, v in form.errors.items()]
                    }
                    return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                return render_to_response('registration/login.html', { 'form': form, 'next': next }, context_instance=RequestContext(request))
        else:
            if request.GET.get('type') == 'json':
                content = {
                    'status': 'error',
                    'csrf_token': unicode(csrf(request)['csrf_token']),
                    'errors': [(k, map(unicode, v)) for k, v in form.errors.items()]
                }
                return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
            return render_to_response('registration/login.html', { 'form': form, 'next': next }, context_instance=RequestContext(request))

def Logout(request):
    next = None
    if request.GET.get('next'):
        next = request.META['QUERY_STRING'].split('next=')[1]
        if request.GET.get('next')[0] != '/':
            return redirect('/u/login/')
        else:
            nextpath = request.GET.get('next').split('?')[0]
            if nextpath[0] != '/' or nextpath in ['', '/', '/u/login/', '/u/signup/']:
                return redirect('/u/login/')
    logout(request)
    if request.GET.get('type') == 'json':
        content = {
            'status': 'success'
        }
        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    if next:
        return redirect(next)
    else:
        return redirect('/')

def Settings(request):
    prev = None
    if request.GET.get('prev'):
        prev = request.GET.get('prev')
    next = None
    if request.GET.get('next'):
        next = request.GET.get('next')
    if prev and next and (next == '' or next[0] != '/' or next == '/u/login/' or next == '/u/signup/'):
        return redirect('/u/settings/?prev=' + prev)
    if request.user.is_authenticated():
        if request.method == 'GET':
            if request.GET.get('type') == 'json':
                content = {
                    'csrf_token': unicode(csrf(request)['csrf_token']),
                    'prev': prev,
                    'next': next
                }
                return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
            content = {
                'prev': prev,
                'next': next
            }
            return render_to_response('user/settings.html', content, context_instance=RequestContext(request))
        if request.method == 'POST':
            userprofile = UserProfile.objects.get(user=request.user)
            form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
            if form.is_valid():
                userprofile = form.save()
                
                if userprofile.avatar:
                    avatar_file = os.path.join(settings.MEDIA_ROOT, 'avatar', str(request.user.username) + '.png')
                    if os.path.isfile(avatar_file):
                        avatar = Image.open(avatar_file)
                        max_size = 64
                        if avatar.size[0] > avatar.size[1]:
                            size = (max_size, int(max_size * avatar.size[1] / avatar.size[0]))
                        else:
                            size = (int(max_size * avatar.size[0] / avatar.size[1]), max_size)
                        avatar.thumbnail(size, Image.ANTIALIAS)
                        
                        def resize_avatar(avatar, p):
                            if os.path.getsize(avatar_file) > 5 * 1024 and avatar.size[0] > 1 and avatar.size[1] > 1:
                                p = p * 0.75
                                avatar.thumbnail([int(p * s) for s in avatar.size], Image.ANTIALIAS)
                                avatar = avatar.resize(size)
                                avatar.save(avatar_file, optimize=True)
                                resize_avatar(avatar, p)
                        resize_avatar(avatar, 1)
                
                if request.GET.get('type') == 'json':
                    content = {
                        'status': 'success'
                    }
                    return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                if next:
                    return redirect(next)
                else:
                    return redirect(Main)
            else:
                if request.GET.get('type') == 'json':
                    content = {
                        'status': 'error',
                        'csrf_token': unicode(csrf(request)['csrf_token']),
                        'errors': [(k, map(unicode, v)) for k, v in form.errors.items()]
                    }
                    return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
                content = {
                    'prev': prev,
                    'next': next,
                    'form': form
                }
                return render_to_response('user/settings.html', content, context_instance=RequestContext(request))
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return redirect('/u/login/?next=/u/settings/')

def UserPage(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if request.GET.get('type') == 'json':
        if user:
            content = {
                'status': 'success',
                'user': {
                    'username': user.username,
                    'info': user.userprofile.info,
                    'avatar': (user.userprofile.openid) and str(user.userprofile.avatar) or ((user.userprofile.avatar) and '/s/' + str(user.userprofile.avatar) or '/s/avatar/n.png'),
                    'profile': user.userprofile.profile,
                    'page': user.userprofile.page,
                }
            }
        else:
            content = {
                'status': 'error'
            }
        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    content = {
        'viewuser': user
    }
    return render_to_response('user/defaultpage.html', content, context_instance=RequestContext(request))

def Page(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if request.GET.get('type') == 'json':
        if user:
            content = {
                'status': 'success',
                'user': {
                    'username': user.username,
                    'info': user.userprofile.info,
                    'avatar': (user.userprofile.openid) and str(user.userprofile.avatar) or ((user.userprofile.avatar) and '/s/' + str(user.userprofile.avatar) or '/s/avatar/n.png'),
                    'profile': user.userprofile.profile,
                    'page': user.userprofile.page,
                }
            }
        else:
            content = {
                'status': 'error'
            }
        return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
    content = {
        'user': user
    }
    if user and user.userprofile.page:
        return render_to_response('user/page.html', content, context_instance=RequestContext(request))
    else:
        return render_to_response('user/defaultpage.html', content, context_instance=RequestContext(request))

def Notify(request):
    user = request.user
    if user.is_authenticated():
        try:
            notify = UserNotify.objects.all().filter(user=request.user).order_by('-created')
        except User.DoesNotExist:
            notify = None
        #notify = None
        content = {
            'notify': notify
        }
        if request.GET.get('type') == 'json':
            content = {
                'status': 'success',
                'notify': {
                    'count': len(notify)
                }
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render_to_response('user/notify.html', content, context_instance=RequestContext(request))
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return redirect('/u/login/?next=/u/notify/')

def Feedback(request):
    if request.method == 'GET':
        return render_to_response('user/feedback.html', {}, context_instance=RequestContext(request))
    if request.method == 'POST':
        if request.POST.get('feedback'):
            feedback = request.POST['feedback']
            send_mail('Feedback to hulu.im', request.user.username + ': ' + feedback, 'w@sadpast.com',['lostab@gmail.com'], fail_silently=False)
            return render_to_response('user/feedback.html', { 'submit': 'true' }, context_instance=RequestContext(request))
        else:
            return redirect('/u/feedback/')

def List(request):
    try:
        users = User.objects.all().order_by('-date_joined')
    except User.DoesNotExist:
        users = None
    content = {
        'users': users
    }
    return render_to_response('user/list.html', content, context_instance=RequestContext(request))

def Message(request, username):
    usernames = username.split(',')
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
    
    if request.user.is_authenticated():
        if len(users) > 1 and request.user not in users:
            return redirect('/')
        if request.user not in users:
            users.append(User.objects.get(username=request.user))
        users = sorted(users, key=lambda user: user.username)
        def getmessages():
            try:
                if request.GET.get('messageid'):
                    items = Item.objects.select_related('useritemrelationship').filter(user__in=users).filter(id__gt=request.GET.get('messageid')).all()
                else:
                    items = Item.objects.select_related('useritemrelationship').filter(user__in=users).all()
                
                messages = []
                for item in items:
                    useritemrelationship = UserItemRelationship.objects.filter(item=item)
                    urusers = []
                    for ur in useritemrelationship:
                        if ur.type == 'message':
                            urusers.append(ur.user)
                    urusers = sorted(urusers, key=lambda user: user.username)
                    if (urusers == users):
                        itemcontent = ItemContent.objects.filter(item=item)
                        item.create = itemcontent[0].create
                        item.title = itemcontent[0].content.strip().splitlines()[0]
                        
                        subitem = item.get_all_items(include_self=False)
                        if subitem:
                            subitem.sort(key=lambda item:item.create, reverse=True)
                            itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                            item.subitemcount = len(subitem)
                            item.lastsubitem = subitem[0]
                        else:
                            item.lastsubitem = itemcontent[0]
                        messages.append(item)
                
                messages = sorted(messages, key=lambda item:item.lastsubitem.create, reverse=False)[-100:]
                
            except Item.DoesNotExist:
                messages = None
            
            return messages
        
        messages = getmessages()
        
        if request.method == 'GET':
            if request.GET.get('type') == 'json':
                for i in range(30):
                    if not messages:
                        time.sleep(1)
                        messages = getmessages()
                messagelist = []
                for item in messages:
                    message = {
                        'id': str(item.id),
                        'user': {
                            'username': item.user.username,
                            'info': item.user.userprofile.info,
                            'avatar': (item.user.userprofile.openid) and str(item.user.userprofile.avatar) or ((item.user.userprofile.avatar) and '/s/' + str(item.user.userprofile.avatar) or '/s/avatar/n.png'),
                            'profile': item.user.userprofile.profile,
                            'page': item.user.userprofile.page,
                        },
                        'create': str(item.lastsubitem.create),
                        'content': item.lastsubitem.content
                    }
                    messagelist.append(message)
                
                content = {
                    'status': 'success',
                    'messages': messagelist
                }
                return jsonp(request, content)
            
            tousers = users
            if len(tousers) == 2 and request.user in tousers:
                tousers.remove(request.user)
            content = {
                'tousers': tousers,
                'messages': messages
            }
            return render_to_response('user/message.html', content, context_instance=RequestContext(request))
        
        if request.method == 'POST':
            if request.POST.get('content').strip() == '' and not request.FILES:
                tousers = users
                if len(tousers) == 2 and request.user in tousers:
                    tousers.remove(request.user)
                content = {
                    'tousers': tousers,
                    'messages': messages
                }
                return render_to_response('user/message.html', content, context_instance=RequestContext(request))
            
            form = ItemContentForm(request.POST)
            if form.is_valid():
                item = Item(user=request.user)
                item.save()
                
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
                
                for user in users:
                    useritemrelationship = UserItemRelationship(user=user)
                    useritemrelationship.type = 'message'
                    useritemrelationship.save()
                    item.useritemrelationship.add(useritemrelationship)
                
            else:
                if len(tousers) == 2 and request.user in tousers:
                    tousers.remove(request.user)
                content = {
                    'tousers': tousers,
                    'item': item,
                    'reply': reply,
                    'form': form
                }
                return render_to_response('user/message.html', content, context_instance=RequestContext(request))
            
            return redirect('/u/m/' + username)
    else:
        return redirect('/u/login/?next=/u/m/' + username + '/')

def MessageList(request):
    if request.user.is_authenticated():
        messagelist = []
        ursession = []
        useritemrelationship = UserItemRelationship.objects.filter(type="message").filter(user=request.user).prefetch_related('item_set').order_by('-id')
        for ur in useritemrelationship:
            for message in ur.item_set.all():
                urusers = []
                for mur in message.useritemrelationship.all():
                    if mur.user not in urusers:
                        urusers.append(mur.user)
                if len(urusers) == 2 and request.user in urusers:
                    urusers.remove(request.user)
                urusers = sorted(urusers, key=lambda user: user.username)
                
                messagesession = {
                    'urusers': urusers,
                    'message': message
                }
                if urusers not in ursession:
                    ursession.append(urusers)
                    messagelist.append(messagesession)
        
        if request.GET.get('type') == 'json':
            messages = []
            for ms in messagelist:
                urusers = []
                for uruser in ms['urusers']:
                    urusers.append({
                        'username': uruser.username,
                        'info': uruser.userprofile.info,
                        'avatar': (uruser.userprofile.openid) and str(uruser.userprofile.avatar) or ((uruser.userprofile.avatar) and '/s/' + str(uruser.userprofile.avatar) or '/s/avatar/n.png'),
                        'profile': uruser.userprofile.profile,
                        'page': uruser.userprofile.page,
                    })
                
                message = ms['message']
                itemcontent = ItemContent.objects.filter(item=message)
                message.create = itemcontent[0].create
                message.title = itemcontent[0].content.strip().splitlines()[0]
                subitem = message.get_all_items(include_self=False)
                if subitem:
                    subitem.sort(key=lambda item:item.create, reverse=True)
                    itemcontent = ItemContent.objects.filter(item=subitem[0]).reverse()
                    message.subitemcount = len(subitem)
                    message.lastsubitem = subitem[0]
                else:
                    message.lastsubitem = itemcontent[0]
                lastmessage = {
                    'content': message.lastsubitem.content,
                    'datetime': str(message.lastsubitem.create)
                }
                
                messagesession = {
                    'urusers': urusers,
                    'lastmessage': lastmessage
                }
                messages.append(messagesession)
            
            content = {
                'status': 'success',
                'messages': messages
            }
            return jsonp(request, content)
        
        content = {
            'messagelist': messagelist
        }
        return render_to_response('user/messagelist.html', content, context_instance=RequestContext(request))
    else:
        if request.GET.get('type') == 'json':
            content = {
                'status': 'error'
            }
            return jsonp(request, content)
        return redirect('/u/login/?next=' + request.path + '?' + request.META['QUERY_STRING'])