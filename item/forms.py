from django import forms

from item.models import *

import datetime
from django.utils.timezone import utc

class ItemContentForm(forms.ModelForm):
    content = forms.CharField(required=False, widget=forms.Textarea)
    
    class Meta:
        model = ItemContent
        fields = ('content',)

class ContentAttachmentForm(forms.ModelForm):
    file = forms.FileField()
    
    class Meta:
        model = ContentAttachment
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
