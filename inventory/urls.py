from django.urls import path
from .views import (
    SaleCreateView, SaleListView, StockItemListView, StockItemCreateView, StockItemUpdateView, StockItemDeleteView,
    StockMovementListView, StockMovementCreateView,SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView,
    PurchaseListView, PurchaseCreateView, SupplierDeleteView, InventoryHistoryView,SaleUpdateView, SaleDeleteView, get_items_by_restaurant
)

app_name = 'inventory'

urlpatterns = [
    path('stock-list', StockItemListView.as_view(), name='list'),
    path('add/', StockItemCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', StockItemUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', StockItemDeleteView.as_view(), name='delete'),
    path('movements/', StockMovementListView.as_view(), name='movements'),
    path('movements/add/', StockMovementCreateView.as_view(), name='movements_add'),
    # urls.py
    path('get_items_by_restaurant/<int:restaurant_id>/', get_items_by_restaurant, name='get_items_by_restaurant'),

    path('suppliers/', SupplierListView.as_view(), name='suppliers'),
    path('suppliers/add/', SupplierCreateView.as_view(), name='supplier_add'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),

    path('purchases/', PurchaseListView.as_view(), name='purchases'),
    path('purchases/add/', PurchaseCreateView.as_view(), name='purchase_add'),
    
      # Sales
    path('sales/', SaleListView.as_view(), name='sales'),
    path('sales/add/', SaleCreateView.as_view(), name='sale_add'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_edit'),
    path('sales/<int:pk>/delete/', SaleDeleteView.as_view(), name='sale_delete'),
    path('history/', InventoryHistoryView.as_view(), name='history'),
    
]
