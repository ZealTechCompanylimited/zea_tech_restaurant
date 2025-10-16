
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    
    path('organizations/', include('organizations.urls')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),
    path('inventory/', include('inventory.urls')),
    path('reservations/', include('reservations.urls')),
    path('reports/', include('reports.urls')),
    path("payment/", include("payments.urls")),
    path("subscriptions/", include("subscriptions.urls")),

]
