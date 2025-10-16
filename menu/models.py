from django.db import models
from organizations.models import Restaurant
from inventory.models import StockItem
from django.conf import settings

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True,                  # allow null
    blank=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_created'
    )
    class Meta:
        unique_together = ("restaurant", "name")


    def __str__(self):
        return f"{self.restaurant} - {self.name}"


class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0) # %
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to="menu/", blank=True, null=True)
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="menu_items"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_items'
    )


    class Meta:
        unique_together = ("restaurant", "name")


    def __str__(self):
        return self.name
