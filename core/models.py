from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator

class Produce(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(
        max_length=20,
        choices=[
            ('beans', 'Beans'),
            ('maize', 'Grain Maize'),
            ('cowpeas', 'Cowpeas'),
            ('gnuts', 'Groundnuts (G-nuts)'),
            ('rice', 'Rice'),
            ('soybeans', 'Soybeans')
        ]
    )
    branch = models.CharField(
        max_length=20,
        choices=[
            ('maganjo', 'Maganjo'),
            ('matugga', 'Matugga')
        ]
    )

    def __str__(self):
        return f"{self.name} ({self.type}) - {self.branch}"

class Procurement(models.Model):
    produce = models.ForeignKey(Produce, on_delete=models.CASCADE)
    tonnage = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    dealer_name = models.CharField(max_length=100)
    dealer_contact = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter valid phone')])
    branch = models.CharField(
        max_length=20,
        choices=[
            ('maganjo', 'Maganjo'),
            ('matugga', 'Matugga')
        ]
    )
    date_time = models.DateTimeField(auto_now_add=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.dealer_name} - {self.tonnage}t {self.produce.type}"

class Sale(models.Model):
    produce = models.ForeignKey(Produce, on_delete=models.CASCADE)
    tonnage = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    buyer_name = models.CharField(max_length=100)
    buyer_contact = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter valid phone')])
    agent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Agent'})
    date_time = models.DateTimeField(auto_now_add=True)
    is_credit = models.BooleanField(default=False)
    receipt_id = models.CharField(max_length=50, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.receipt_id:
            import uuid
            self.receipt_id = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.buyer_name} - {self.tonnage}t {self.produce.type} (Receipt: {self.receipt_id})"

class CreditSale(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE)
    national_id = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"Credit for {self.sale.buyer_name} - Due: {self.due_date}"

class Stock(models.Model):
    produce = models.OneToOneField(Produce, on_delete=models.CASCADE)
    current_tonnage = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.produce} - {self.current_tonnage}t"