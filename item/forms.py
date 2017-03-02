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
                if str(file.content_type.split('/')[0]) == 'image':
                    return file
                else:
                    return None
        else:
            #raise ValidationError("Couldn't read uploaded image.")
            return None

class LinkForm(forms.ModelForm):
    url = forms.CharField(required=True)
    logo = forms.CharField(required=False)
    title = forms.CharField(required=True)
    description = forms.CharField(required=False)

    class Meta:
        model = Link
        fields = ('url', 'logo', 'title', 'description',)
