from django.contrib import admin
from .models import StockItem,StockMovement

admin.site.register(StockItem)
admin.site.register(StockMovement)
