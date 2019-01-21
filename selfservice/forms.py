from django import forms
from django.contrib.auth.forms import UserCreationForm
from members.models import User
from django.forms import ModelForm

class UserForm(ModelForm):
    class Meta:
       model = User
       fields = [ 'first_name', 'last_name', 'email', 'phone_number', 'image' ]
       help_texts = {
            'email': "When you change this field; you will get a verification email to your new address. And your old address and the trustee's are sent a notice of this change."
       }

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    phone_number = forms.CharField(max_length=40, required=False, help_text="Optional; only visible to the trustees and board delegated administrators")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', )

