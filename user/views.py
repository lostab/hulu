# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect
import datetime
import urllib2
import json
from django.contrib.auth.models import User
from django.contrib.auth import *
from django.contrib.auth.forms import *
from django.core.mail import send_mail
from user.models import *
from user.forms import *
from django.forms.util import ErrorList
from django.core.context_processors import csrf

from item.models import *

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
                    'name': user.userprofile.name,
                    'avatar': (user.userprofile.openid) and str(user.userprofile.avatar) or ((user.userprofile.avatar) and '/s/' + str(user.userprofile.avatar) or '/s/avatar/n.png'),
                    'phone': user.userprofile.phone,
                    'address': user.userprofile.address,
                    'description': user.userprofile.description
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
        next = request.GET.get('next')
    if next and (next[0] != '/' or next in ['', '/', '/u/login/', '/u/signup/']):
        return redirect('/u/signup/')
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
        next = request.GET.get('next')
    
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
    
    
    if next and (next[0] != '/' or next in ['', '/', '/u/login/', '/u/signup/']):
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
        next = request.GET.get('next')
    if next and (next[0] != '/' or next in ['', '/', '/u/login/', '/u/signup/']):
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