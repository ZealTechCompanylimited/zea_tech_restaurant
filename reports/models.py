from django.db import models
from core.models import BaseModel
from django.conf import settings
from organizations.models import Restaurant

class Report(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    FEEDBACK_CATEGORIES = [
        ('service', 'Service'),
        ('food', 'Food'),
        ('app', 'App Experience'),
        ('other', 'Other'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=120, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=FEEDBACK_CATEGORIES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.customer_name or 'Anonymous'} - {self.category}"