
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.http import request
User = get_user_model() 
from orders.models import Order   

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment",null=True, blank=True)  # 👉 add null=True, blank=True
    
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    plan_key = models.CharField(max_length=32, null=True, blank=True)  # add hapa Payment model

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"
