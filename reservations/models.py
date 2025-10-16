from django.db import models
from organizations.models import Branch, Restaurant
from django.conf import settings


class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return self.name


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("BOOKED", "Booked"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed"),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customerr = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    party_size = models.PositiveIntegerField(default=2)
    notes = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default="BOOKED")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    def __str__(self):
        return f"{self.customer.username} - {self.restaurant.name} ({self.date} {self.time})"
