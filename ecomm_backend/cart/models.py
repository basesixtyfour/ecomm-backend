from django.db import models
from uuid6 import uuid7
from django.conf import settings
from products.models import Product
from decimal import Decimal

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum(
            (item.quantity * item.product.price for item in self.items.all()),
            Decimal('0.00')
        )
    
    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    @property
    def subtotal(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"