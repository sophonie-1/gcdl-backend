from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=[('Agent', 'Sales Agent'), ('Manager', 'Branch Manager'), ('CEO', 'CEO')])

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user