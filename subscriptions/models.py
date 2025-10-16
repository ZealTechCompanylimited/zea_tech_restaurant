from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class SubscriptionPlan(models.Model):
    KEY_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', '1 Year'),
        ('three_years', '3 Years'),
    ]
    key = models.CharField(max_length=32, choices=KEY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()  # 30, 365, 365*3 ...
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.display_name} ({self.price})"


class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usersubscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Automatic start and end dates
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    
    active = models.BooleanField(default=False)
    auto_renew = models.BooleanField(default=False)  # future recurring billing

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # If start_date is not provided, set it automatically
        if self.active and not self.start_date:
            self.start_date = timezone.now()
        # If plan is assigned and end_date is not provided, calculate automatically
        if self.plan and self.start_date and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def activate(self, plan=None, start_when=None):
        if plan:
            self.plan = plan
        self.start_date = start_when or timezone.now()
        if self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        self.active = True
        self.save()

    def deactivate(self):
        self.active = False
        self.save()

    def is_valid(self):
        if not self.active or not self.end_date:
            return False
        return timezone.now() <= self.end_date

    def days_left(self):
        if not self.end_date:
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)

    def __str__(self):
        return f"{self.user} - {self.plan} ({'Active' if self.active else 'Inactive'})"
