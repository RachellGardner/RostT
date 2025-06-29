from django import forms
from django.contrib.auth.forms import UserCreationForm
from bio_core_website.models import CustomUser  # Импорт твоей кастомной модели

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'gender', 'weight', 'height', 'age', 'password1', 'password2')
