from django.db import models
from core.models import BaseModel
from django.conf import settings

# -------------------
# Organization
# -------------------
class Organization(BaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="organizations_created"
    )
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="organizations_managed",
        blank=True
    )
    def __str__(self):
        return self.name


# -------------------
# Restaurant
# -------------------
class Restaurant(models.Model):
    name = models.CharField(max_length=150)
    code = models.SlugField(unique=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=64, default="Africa/Dar_es_Salaam")
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restaurants",
        null=True, blank=True
    )
    
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="restaurants",
        null=True, blank=True
    )
    image = models.ImageField(upload_to='restaurant_images/', blank=True, null=True)

    def __str__(self):
        return self.name


# -------------------
# Branch
# -------------------
class Branch(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="branches",
        null=True, blank=True
    )
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_branches"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branches_created"
    )

    def __str__(self):
        if self.restaurant:
            return f"{self.name} - {self.restaurant.name}"
        return self.name
