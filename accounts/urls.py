from django.urls import path
from .views import *

urlpatterns = [
    path('accounts-login/', LoginView.as_view(), name='login'),
    path('accounts-register/', RegisterView.as_view(), name='register'),
    path("dashboard/owner/", OwnerDashboardView.as_view(), name="owner-dashboard"),
    path("dashboard/manager/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    path("dashboard/cashier/", CashierDashboardView.as_view(), name="cashier-dashboard"),
    path("dashboard/chef/", ChefDashboardView.as_view(), name="chef-dashboard"),
    path("dashboard/waiter/", WaiterDashboardView.as_view(), name="waiter-dashboard"),
    path("dashboard/customer/", CustomerDashboardView.as_view(), name="customer-dashboard"),
    path('logout/', LogoutView.as_view(), name='logout'),
]



