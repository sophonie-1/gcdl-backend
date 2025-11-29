from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Procurement, Sale, Stock

@receiver(post_save, sender=Procurement)
def update_stock_on_procurement(sender, instance, created, **kwargs):
    if created:
        stock, _ = Stock.objects.get_or_create(produce=instance.produce)
        stock.current_tonnage += instance.tonnage
        stock.save()

@receiver(post_save, sender=Sale)
def update_stock_on_sale(sender, instance, created, **kwargs):
    if created:
        try:
            stock = Stock.objects.get(produce=instance.produce)
            if stock.current_tonnage < instance.tonnage:
                instance.delete()
                raise ValueError('Insufficient stock')
            stock.current_tonnage -= instance.tonnage
            stock.save()
        except (Stock.DoesNotExist, ValueError):
            pass