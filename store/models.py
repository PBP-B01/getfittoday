from django.conf import settings
from django.db import models
from decimal import Decimal
from home.models import FitnessSpot

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    rating = models.CharField(max_length=10, null=True, blank=True)
    units_sold = models.CharField(max_length=50, null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    store = models.ForeignKey(
        FitnessSpot,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name="products"
    )

    def __str__(self):
        return f"{self.name} — Rp{int(self.price):,}"


class Cart(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    session_key = models.CharField(max_length=40, blank=True, help_text='Session key for anonymous carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.owner:
            return f"Cart({self.owner})"
        return f"Cart(session={self.session_key})"

    def total_price(self):
        total = Decimal(0)
        for item in self.items.all():
            total += item.total_price()
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def total_price(self):
        return Decimal(self.product.price) * self.quantity