# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import redirect
import datetime
from django.utils.timezone import utc
import urllib2
import json
from tag.models import *
from tag.forms import *
from django.forms.util import ErrorList
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user.models import *
from main.__init__ import *
from django.forms.models import inlineformset_factory

def Index(request):
    if request.user.is_authenticated():
        try:
            tasks = Task.objects.all().filter(user=request.user).order_by('-created')
            paginator = Paginator(tasks, 100)
            page = request.GET.get('page')
            try:
                tasks = paginator.page(page)
            except PageNotAnInteger:
                tasks = paginator.page(1)
            except EmptyPage:
                tasks = paginator.page(paginator.num_pages)
        except Task.DoesNotExist:
            tasks = None
        content = {
            'tasks': tasks
        }
        if request.GET.get('type') == 'json':
            content = {
                'page': tasks.number,
                'tasks': []
            }
            for task in tasks:
                content['tasks'].append({
                    'id': task.id,
                    'title': task.title,
                    'content': task.content,
                    'created': deltatime2second(datetime.datetime.utcnow().replace(tzinfo=utc) - task.created.replace(tzinfo=utc))
                })
            return HttpResponse(json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4), content_type="application/json; charset=utf-8")
        return render_to_response('tasks/index.html', content, context_instance=RequestContext(request))
    else:
        return redirect('/accounts/login/?next=/tasks/')

def Create(request):
    if request.user.is_authenticated():
        if request.method == 'GET':
            content = {
                'aweeklater': datetime.datetime.now() + datetime.timedelta(days=7)
            }
            return render_to_response('tasks/create.html', content, context_instance=RequestContext(request))
        
        if request.method == 'POST':
            task = Task(user=request.user)
            form = TaskForm(request.POST, instance=task)
            if form.is_valid():
                TaskInlineFormSet = inlineformset_factory(Task, TaskAttachment, form=TaskForm)
                for attachmentfile in request.FILES.getlist('file'):
                    attachmentform = TaskAttachmentForm(request.POST, request.FILES)
                    if attachmentform.is_valid():
                        pass
                    else:
                        content = {
                            'form': form
                        }
                        return render_to_response('tasks/create.html', content, context_instance=RequestContext(request))
                
                task = form.save()
                
                for attachmentfile in request.FILES.getlist('file'):
                    attachment = TaskAttachment(task=task)
                    attachmentform = TaskAttachmentForm(request.POST, request.FILES, instance=attachment)
                    if attachmentform.is_valid():
                        taskattachment = attachmentform.save()
                        taskattachment.title = attachmentfile.name
                        taskattachment.contenttype = str(attachmentfile.content_type)
                        taskattachment.save()
                
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = request.META['REMOTE_ADDR']
                if x_forwarded_for:
                    ip = x_forwarded_for.split(', ')[-1]
                
                task.ip = ip
                
                if request.POST.get('longitude') and request.POST.get('latitude'):
                    task.longitude = request.POST.get('longitude')
                    task.latitude = request.POST.get('latitude')
                else:
                    try:
                        iptogeo = 'http://api.map.baidu.com/location/ip?ak=XNOxN1DRZGZFVFkHTEIhxGDt&coor=bd09ll&ip=' + ip
                        ipreturn = json.loads(urllib2.urlopen(iptogeo).read())
                        longitude = ''
                        latitude = ''
                        if ipreturn['status'] == 0:
                            longitude = ipreturn['content']['point']['x']
                            latitude = ipreturn['content']['point']['y']
                            
                            task.longitude = longitude
                            task.latitude = latitude
                    except:
                        pass
                
                task.save()
                
                return redirect('/tasks/' + str(task.id))
            else:
                content = {
                    'form': form
                }
                return render_to_response('tasks/create.html', content, context_instance=RequestContext(request))
    else:
        return redirect('/accounts/login/?next=/tasks/create/')

def View(request, id):
    try:
        task = Task.objects.get(id=id)
    except Task.DoesNotExist:
        task = None
    if not task:
        return redirect('/')
    
    if task:
        try:
            attachmentfiles = TaskAttachment.objects.all().filter(task=task)
            for attachmentfile in attachmentfiles:
                if attachmentfile.contenttype:
                    if len(attachmentfile.contenttype.split('/')) > 1:
                        attachmentfile.contenttype = attachmentfile.contenttype.split('/')[0]
        except TaskAttachment.DoesNotExist:
            attachmentfiles = None
        task.attachmentfiles = attachmentfiles
    
    try:
        comments = TaskComment.objects.all().filter(task=task).order_by('created')
        paginator = Paginator(comments, 100)
        page = request.GET.get('page')
        try:
            comments = paginator.page(page)
        except PageNotAnInteger:
            comments = paginator.page(1)
        except EmptyPage:
            comments = paginator.page(paginator.num_pages)
    except TaskComment.DoesNotExist:
        comments = None
    
    if comments:
        for comment in comments:
            try:
                attachmentfiles = TaskCommentAttachment.objects.all().filter(taskcomment=comment)
                for attachmentfile in attachmentfiles:
                    if attachmentfile.contenttype:
                        if len(attachmentfile.contenttype.split('/')) > 1:
                            attachmentfile.contenttype = attachmentfile.contenttype.split('/')[0]
            except TaskCommentAttachment.DoesNotExist:
                attachmentfiles = None
            comment.attachmentfiles = attachmentfiles
    
    if request.method == 'GET':
        try:
            UserNotify.objects.filter(user=request.user.id).filter(type='taskcomment').filter(object__in=set(comment.id for comment in comments)).delete()
        except UserNotify.DoesNotExist:
            pass
        
        reply = None
        if request.GET.get('reply'):
            replyid = str(request.GET.get('reply'))
            try:
                reply = TaskComment.objects.get(id=replyid)
            except UserNotify.DoesNotExist:
                pass
        
        if task.user != request.user:
            if not task or task.status or (task.expired and task.expired.replace(tzinfo=utc) < datetime.datetime.utcnow().replace(tzinfo=utc)):
                content = {
                    'task': None
                }
                return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
        
        content = {
            'task': task,
            'comments': comments,
            'reply': reply
        }
        return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
    if request.method == 'POST':
        if not task or task.status or (task.expired and task.expired.replace(tzinfo=utc) < datetime.datetime.utcnow().replace(tzinfo=utc)):
            content = {
                'task': None
            }
            return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
        if request.user.is_authenticated():
            reply = None
            if request.POST.get('reply'):
                replyid = str(request.POST.get('reply'))
                try:
                    reply = TaskComment.objects.get(id=replyid)
                except UserNotify.DoesNotExist:
                    pass
            if reply:
                taskcomment = TaskComment(user=request.user, task=task, parent=reply)
            else:
                taskcomment = TaskComment(user=request.user, task=task)
            
            if request.POST.get('content').strip() == '' and not request.FILES:
                content = {
                    'task': task,
                    'comments': comments,
                    'reply': reply
                }
                return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
            
            form = TaskCommentForm(request.POST, instance=taskcomment)
            if form.is_valid():
                TaskCommentInlineFormSet = inlineformset_factory(TaskComment, TaskCommentAttachment, form=TaskCommentForm)
                for attachmentfile in request.FILES.getlist('file'):
                    #if attachmentfile and attachmentfile._size <= 2*1024*1024:
                    attachmentform = TaskCommentAttachmentForm(request.POST, request.FILES)
                    if attachmentform.is_valid():
                        pass
                    else:
                        content = {
                            'task': task,
                            'comments': comments,
                            'reply': reply,
                            'form': form,
                            'attachmentlist': request.FILES.getlist('file')
                        }
                        return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
                
                taskcomment = form.save()
                
                for attachmentfile in request.FILES.getlist('file'):
                    attachment = TaskCommentAttachment(taskcomment=taskcomment)
                    attachmentform = TaskCommentAttachmentForm(request.POST, request.FILES, instance=attachment)
                    if attachmentform.is_valid():
                        taskcommentattachment = attachmentform.save()
                        taskcommentattachment.title = attachmentfile.name
                        taskcommentattachment.contenttype = str(attachmentfile.content_type)
                        taskcommentattachment.save()
                
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = request.META['REMOTE_ADDR']
                if x_forwarded_for:
                    ip = x_forwarded_for.split(', ')[-1]
                
                taskcomment.ip = ip
                
                if request.POST.get('longitude') and request.POST.get('latitude'):
                    taskcomment.longitude = request.POST.get('longitude')
                    taskcomment.latitude = request.POST.get('latitude')
                else:
                    try:
                        iptogeo = 'http://api.map.baidu.com/location/ip?ak=XNOxN1DRZGZFVFkHTEIhxGDt&coor=bd09ll&ip=' + ip
                        ipreturn = json.loads(urllib2.urlopen(iptogeo).read())
                        longitude = ''
                        latitude = ''
                        if ipreturn['status'] == 0:
                            longitude = ipreturn['content']['point']['x']
                            latitude = ipreturn['content']['point']['y']
                            
                            taskcomment.longitude = longitude
                            taskcomment.latitude = latitude
                    except:
                        pass
                
                taskcomment.save()
                
                if reply:
                    if request.user != reply.user:
                        notify = UserNotify(user=reply.user, type='taskcomment', object=taskcomment.id)
                        notify.save()
                else:
                    if request.user != task.user:
                        notify = UserNotify(user=task.user, type='taskcomment', object=taskcomment.id)
                        notify.save()
                
                return redirect('/tasks/' + id + '#' + str(taskcomment.id))
            else:
                content = {
                    'task': task,
                    'comments': comments,
                    'reply': reply,
                    'form': form
                }
                return render_to_response('tasks/view.html', content, context_instance=RequestContext(request))
        else:
            return redirect('/accounts/login/?next=/tasks/create/')

def Update(request, id):
    if request.user.is_authenticated():
        try:
            task = Task.objects.get(id=id)
            if task.user.username != request.user.username:
                task = None
        except Task.DoesNotExist:
            task = None
        if request.method == 'GET':
            content = {
                'task': task
            }
            return render_to_response('tasks/update.html', content, context_instance=RequestContext(request))
        if request.method == 'POST':
            if task:
                form = TaskForm(request.POST, instance=task)
                if form.is_valid():
                    TaskInlineFormSet = inlineformset_factory(Task, TaskAttachment, form=TaskForm)
                    for attachmentfile in request.FILES.getlist('file'):
                        attachmentform = TaskAttachmentForm(request.POST, request.FILES)
                        if attachmentform.is_valid():
                            pass
                        else:
                            content = {
                                'form': form
                            }
                            return render_to_response('tasks/create.html', content, context_instance=RequestContext(request))
                    
                    task = form.save()
                    
                    for attachmentfile in request.FILES.getlist('file'):
                        attachment = TaskAttachment(task=task)
                        attachmentform = TaskAttachmentForm(request.POST, request.FILES, instance=attachment)
                        if attachmentform.is_valid():
                            taskattachment = attachmentform.save()
                            taskattachment.title = attachmentfile.name
                            taskattachment.contenttype = str(attachmentfile.content_type)
                            taskattachment.save()
                    
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    ip = request.META['REMOTE_ADDR']
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(', ')[-1]
                    
                    if task.ip != ip:
                        task.ip = ip
                    
                    if request.POST.get('longitude') and request.POST.get('latitude'):
                        task.longitude = request.POST.get('longitude')
                        task.latitude = request.POST.get('latitude')
                    else:
                        try:
                            iptogeo = 'http://api.map.baidu.com/location/ip?ak=XNOxN1DRZGZFVFkHTEIhxGDt&coor=bd09ll&ip=' + ip
                            ipreturn = json.loads(urllib2.urlopen(iptogeo).read())
                            longitude = ''
                            latitude = ''
                            if ipreturn['status'] == 0:
                                longitude = ipreturn['content']['point']['x']
                                latitude = ipreturn['content']['point']['y']
                                
                                task.longitude = longitude
                                task.latitude = latitude
                        except:
                            pass
                    
                    task.save()
                    
                    return redirect('/tasks/' + id)
                else:
                    content = {
                        'form': form
                    }
                    return render_to_response('tasks/update.html', content, context_instance=RequestContext(request))
            else:
                return redirect('/tasks/' + id)
    else:
        return redirect('/accounts/login/?next=/tasks/update/' + id)

def Cancel(request, id):
    if request.user.is_authenticated():
        try:
            task = Task.objects.get(id=id)
            if task.user.username == request.user.username:
                task.status = 'cancel'
                task.save()
        except Task.DoesNotExist:
            pass
        return redirect('/tasks/' + id)
    else:
        return redirect('/accounts/login/?next=/tasks/update/' + id)