from django.db import models,transaction

from organizations.models import Restaurant


class StockItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    unit = models.CharField(max_length=20, default="pcs") # kg, l, pcs
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"



class StockMovement(models.Model):
    IN = "IN"; OUT = "OUT"
    TYPES = [(IN, "In"), (OUT, "Out")]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,null=True,blank=True)
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=3, choices=TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        # First save (new movement only)
        if not self.pk:
            if self.movement_type == self.IN:
                self.item.quantity += self.quantity
            else:
                if self.item.quantity < self.quantity:
                    raise ValueError("Not enough stock")
                self.item.quantity -= self.quantity
            self.item.save()
        super().save(*args, **kwargs)
        

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.movement_type == self.IN:
            self.item.quantity -= self.quantity
        else:
            self.item.quantity += self.quantity
        self.item.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.item.unit} - {self.item.name}"


# inventory/models.py
class Supplier(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
    
class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Purchase #{self.id} - {self.supplier.name if self.supplier else 'N/A'}"
    
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
        # Update Stock
        self.item.quantity += self.quantity
        self.item.save()
        
        
    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.item.quantity -= self.quantity
        self.item.save()
        super().delete(*args, **kwargs)


class Sale(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def update_total(self):
        self.total_amount = sum(item.line_total for item in self.items.all())
        self.save(update_fields=["total_amount"])

    def __str__(self):
        return f"Sale #{self.id} - {self.customer_name if self.customer_name else 'N/A'}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def clean(self):
        if self.unit_price <= 0:
            raise ValueError("Unit price must be greater than zero")
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero")



    @transaction.atomic
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        if self.item.quantity < self.quantity:
            raise ValueError(f"Not enough stock for {self.item.name}")
        super().save(*args, **kwargs)
        self.item.quantity -= self.quantity
        self.item.save()
        self.sale.update_total()


    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.item.quantity += self.quantity
        self.item.save()
        super().delete(*args, **kwargs)
        self.sale.update_total()