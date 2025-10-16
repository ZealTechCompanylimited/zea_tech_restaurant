from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Restaurant
from menu.models import Item
from django.conf import settings



class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=20) # e.g., T1, T2
    seats = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)


    class Meta:
        unique_together = ("restaurant", "name")


    def __str__(self):
        return f"{self.restaurant}:{self.name}"


class Order(models.Model):
    ORDER_TYPES = [("DINE_IN","Dine-In"),("TAKEAWAY","Take Away"),("DELIVERY","Delivery")]
    STATUS = [("OPEN","Open"),("PAID","Paid"),("CANCELLED","Cancelled")]


    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
  

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders_created")

    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, default="DINE_IN")
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(max_length=10, choices=STATUS, default="OPEN")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders_as_customer")
    guest_name = models.CharField(max_length=150, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    
    @property
    def table_number(self):
        return self.table.name if self.table else "-"
    
    @property
    def customer_name(self):
        """Return the full name of the customer or guest"""
        if self.customer:
            # Use first_name + last_name, fallback to username
            full_name = f"{self.customer.first_name} {self.customer.last_name}".strip()
            return full_name if full_name else self.customer.username
        elif self.guest_name:
            return self.guest_name
        else:
            return "Guest"
    
    # is_deleted = models.BooleanField(default=False)

    # def delete(self, *args, **kwargs):
    #     # Override delete method to perform soft delete
    #     self.is_deleted = True
    #     self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.SET_NULL, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Invoice(models.Model):
    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("MOBILE", "Mobile Money"),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cashier_invoices')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default="CASH")

    def __str__(self):
        return f"Invoice #{self.invoice_number} for Order #{self.order.id}"



# class Notification(models.Model):
#     recipient = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='notifications'
#     )
#     order = models.ForeignKey('Order', on_delete=models.CASCADE)
#     message = models.CharField(max_length=255)
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Notification for {self.recipient} - Order #{self.order.id}"
