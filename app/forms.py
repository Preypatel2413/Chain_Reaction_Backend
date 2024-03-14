from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2', 'email')  

    def save(self, commit=True):
        user = super().save(commit=False)
        user.games_played = 0
        user.games_won = 0
        if commit:
            user.save()
        return user
