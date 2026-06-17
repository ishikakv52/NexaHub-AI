from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'age', 'gender', 'height_cm', 'weight_kg',
            'target_weight_kg', 'activity_level', 'goal', 'food_preference', 'food_style',
            'profile_photo',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age in years', 'min': 10, 'max': 100}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm', 'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current weight in kg', 'step': '0.1'}),
            'target_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Target weight in kg', 'step': '0.1'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'goal': forms.Select(attrs={'class': 'form-select'}),
            'food_preference': forms.Select(attrs={'class': 'form-select'}),
            'food_style': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.FileInput(attrs={'class': 'profile-photo-input', 'style': 'display: none;'}),
        }

class WeightUpdateForm(forms.Form):
    weight_kg = forms.FloatField(
        min_value=30, max_value=300,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter weight in kg', 'step': '0.1'})
    )
