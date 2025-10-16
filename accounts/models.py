from django.contrib.auth.models import AbstractUser
from django.db import models

USER_TYPES = [
        ("OWNER", "Owner"),
        ("MANAGER", "Manager"),
        ("CASHIER", "Cashier"),
        ("CHEF", "Chef"),
        ("WAITER", "Waiter"),
        ("CUSTOMER", "Customer"),
        ]

class User(AbstractUser):
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default="CUSTOMER")
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to="users/", blank=True, null=True)
    restaurant = models.ForeignKey(
        'organizations.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )


    USERNAME_FIELD = "email"   # ✅ ensures login uses email
    REQUIRED_FIELDS = ["username"]


    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
