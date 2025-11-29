from django.contrib import admin
from .models import Produce, Procurement, Sale,Stock,CreditSale
# Register your models here.
admin.site.register([Produce, Procurement, Sale, Stock, CreditSale])