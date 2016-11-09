from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from user.models import *
from django.utils import timezone

class UserCreationForm(UserCreationForm):
    username = forms.CharField(min_length=3)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'last_login')

class UserProfileForm(forms.ModelForm):
    info = forms.CharField(required=False, max_length=255)
    profile = forms.CharField(required=False, widget=forms.Textarea)
    page = forms.CharField(required=False, widget=forms.Textarea)
    avatar = forms.FileField(required=False)

    class Meta:
        model = UserProfile
        fields = ('info', 'profile', 'page', 'avatar')

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar:
            try:
                if avatar.content_type.split('/')[0] != 'image':
                    return None
                if avatar._size > 2 * 1024 * 1024:
                    #raise ValidationError("Image file too large ( > 200KB ).")
                    return None
                else:
                    return avatar
            except:
                return None
        else:
            #raise ValidationError("Couldn't read uploaded image.")
            return None
