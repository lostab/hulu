from django import forms
from main.models import *

class FileUploadForm(forms.Form):
    file = forms.FileField(required=True)

    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            try:
                if file.content_type.split('/')[0] != 'image':
                    return None
                if file._size > 2 * 1024 * 1024:
                    #raise ValidationError("Image file too large ( > 200KB ).")
                    return None
                else:
                    return file
            except:
                return None
        else:
            #raise ValidationError("Couldn't read uploaded image.")
            return None
