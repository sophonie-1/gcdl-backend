from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import Procurement, Sale, CreditSale, Produce

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

class ProcurementForm(forms.ModelForm):
    class Meta:
        model = Procurement
        fields = ['produce', 'tonnage', 'cost', 'dealer_name', 'dealer_contact', 'branch', 'selling_price']
        widgets = {
            'produce': forms.Select(),
            'tonnage': forms.NumberInput(attrs={'step': '0.01', 'min': '1'}),
            'cost': forms.NumberInput(attrs={'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01'}),
            'dealer_contact': forms.TextInput(),
            'branch': forms.Select(choices=[('maganjo', 'Maganjo'), ('matugga', 'Matugga')]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produce'].queryset = Produce.objects.all()

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['produce', 'tonnage', 'amount_paid', 'buyer_name', 'buyer_contact', 'is_credit']
        widgets = {
            'produce': forms.Select(),
            'tonnage': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'amount_paid': forms.NumberInput(attrs={'step': '0.01'}),
            'buyer_contact': forms.TextInput(),
            'is_credit': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produce'].queryset = Produce.objects.all()

class CreditSaleForm(forms.ModelForm):
    class Meta:
        model = CreditSale
        fields = ['national_id', 'location', 'amount_due', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }