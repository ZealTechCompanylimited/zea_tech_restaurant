from django.urls import path
from .views import OrderListView, OrderCreateView, OrderUpdateView,OrderDeleteView, TableListView, TableCreateView, TableUpdateView, TableDeleteView, InvoiceListView, InvoiceCreateView

app_name = 'orders'

urlpatterns = [
    path('orders-list', OrderListView.as_view(), name='list'), 
    path('<int:pk>/delete/', OrderDeleteView.as_view(), name='delete'),
    path("add/", OrderCreateView.as_view(), name="add"),
    path("update/<int:pk>/", OrderUpdateView.as_view(), name="update"),
    path("tables/", TableListView.as_view(), name="table_list"),
    path("tables/add/", TableCreateView.as_view(), name="table_add"),
    path("tables/edit/<int:pk>/", TableUpdateView.as_view(), name="table_edit"),
    path("tables/delete/<int:pk>/", TableDeleteView.as_view(), name="table_delete"),
    
    path('invoices/', InvoiceListView.as_view(), name='invoices'),
    path('invoices/add/', InvoiceCreateView.as_view(), name='invoice_add'),
    
  
]
