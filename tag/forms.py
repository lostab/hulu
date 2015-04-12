from django import forms

from tag.models import *

import datetime
from django.utils.timezone import utc

class TaskForm(forms.ModelForm):
    amount = forms.IntegerField(required=False)
    expired = forms.CharField(required=False)
    reword = forms.CharField(required=False, max_length=255)
    content = forms.CharField(required=False, widget=forms.Textarea)
    longitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    latitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    template = forms.CharField(required=False, max_length=30)
    
    class Meta:
        model = Task
        fields = ('title', 'amount', 'expired', 'reword', 'content', 'longitude', 'latitude', 'template')
    
    def clean_expired(self):
        expired = self.cleaned_data['expired']
        if expired:
            return expired.replace('T', ' ')
        else:
            return None

class TaskCommentForm(forms.ModelForm):
    content = forms.CharField(required=False, widget=forms.Textarea)
    longitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    latitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    class Meta:
        model = TaskComment
        fields = ('content', 'longitude', 'latitude')

class TaskAttachmentForm(forms.ModelForm):
    file = forms.FileField()
    
    class Meta:
        model = TaskAttachment
        fields = ('file',)
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            if file._size > 2*1024*1024:
                #raise ValidationError("Image file too large ( > 200KB ).")
                return None
            else:
                return file
        else:
            #raise ValidationError("Couldn't read uploaded image.")
            return None

class TaskCommentAttachmentForm(forms.ModelForm):
    file = forms.FileField()
    
    class Meta:
        model = TaskCommentAttachment
        fields = ('file',)
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            if file._size > 2*1024*1024:
                #raise ValidationError("Image file too large ( > 200KB ).")
                return None
            else:
                return file
        else:
            #raise ValidationError("Couldn't read uploaded image.")
            return None
