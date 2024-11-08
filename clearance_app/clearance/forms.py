from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import ClearableFileInput
from .models import User, Document, ClearanceSet

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']

class PredictionForm(forms.Form):
    # If you need any fields for the prediction form, add them here
    pass

class FacultySignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_faculty = True
        if commit:
            user.save()
        return user

class AdminSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = True
        if commit:
            user.save()
        return user

class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']

class ClearanceSetForm(forms.ModelForm):
    class Meta:
        model = ClearanceSet
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter clearance set name'
            })
        }
