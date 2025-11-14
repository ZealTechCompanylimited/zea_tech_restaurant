from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib import messages
from .models import User
from django.utils import timezone
from django.db.models import Sum
from orders.models import Order
from organizations.models import Restaurant
from inventory.models import Sale
from orders.models import Table
from menu.models import Item

class RegisterView(View):
    def get(self, request):
        return render(request, "accounts/register.html")

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        phone = request.POST.get("phone")
        image = request.FILES.get("image")

        # Password check
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Unique email check
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("register")

        # Assign user_type dynamically (you can improve this logic later)
        if email.endswith("@company.com"):
            user_type = "MANAGER"
        elif email.endswith("@admin.com"):
            user_type = "OWNER"
        elif email.endswith("@cashier.com"):
            user_type = "CASHIER"
        elif email.endswith("@chef.com"):
            user_type = "CHEF"
        elif email.endswith("@waiter.com"):
            user_type = "WAITER"
        else:
            user_type = "CUSTOMER"

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type,
            phone=phone,
            image=image,
        )
        user.save()
        messages.success(request, f"Account created as {user_type} successfully!")
        return redirect("login")


class LoginView(View):
    def get(self, request):
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on user_type
            redirect_map = {
                "OWNER": "owner-dashboard",
                "MANAGER": "manager-dashboard",
                "CASHIER": "cashier-dashboard",
                "CHEF": "chef-dashboard",
                "WAITER": "waiter-dashboard",
                "CUSTOMER": "customer-dashboard",
            }
            return redirect(redirect_map.get(user.user_type, "index"))
        else:
            messages.error(request, "Invalid email or password")
            return redirect("login")


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("index")




class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/owner_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # OWNER should see only their restaurants
        owner_restaurants = Restaurant.objects.filter(owner=user)

        context["total_restaurants"] = owner_restaurants.count()

        # Monthly revenue for restaurants owned by this owner
        now = timezone.now()
        monthly_revenue = (
            Sale.objects.filter(
                restaurant__owner=user,
                created_at__year=now.year,
                created_at__month=now.month,
            )
            .aggregate(total=Sum("total_amount"))["total"] or 0
        )
        context["monthly_revenue"] = monthly_revenue

        # All-time revenue for all owned restaurants
        all_time_revenue = (
            Sale.objects.filter(restaurant__owner=user)
            .aggregate(total=Sum("total_amount"))["total"] or 0
        )
        context["all_time_revenue"] = all_time_revenue

        # Revenue per owned restaurant (top 5)
        revenue_per_restaurant = (
            Sale.objects.filter(restaurant__owner=user)
            .values("restaurant__name")
            .annotate(total=Sum("total_amount"))
            .order_by("-total")[:5]
        )
        context["revenue_per_restaurant"] = revenue_per_restaurant

        return context
class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/manager_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Ensure manager belongs to a restaurant
        if not hasattr(user, "restaurant") or user.restaurant is None:
            context["open_orders_count"] = 0
            context["open_orders"] = Order.objects.none()
            return context

        # Show only orders for this manager's restaurant
        open_orders = Order.objects.filter(
            restaurant=user.restaurant,
            status="OPEN"
        )

        context["open_orders_count"] = open_orders.count()
        context["open_orders"] = open_orders

        return context


class CashierDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/cashier_dashboard.html"
    


 # adjust import



class ChefDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/chef_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the restaurant for this chef
        restaurant = getattr(self.request.user, "restaurant", None)
        
        if restaurant:
            # Fetch all open orders for this restaurant
            context['pending_orders'] = Order.objects.filter(
                restaurant=restaurant,
                status="OPEN"
            ).prefetch_related("items__item")  # fetch related items for efficiency
        else:
            context['pending_orders'] = []
        
        return context


class WaiterDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/waiter_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Assuming your User model has a 'restaurant' relation
        # If not, you may need to get restaurant via some other relation
        user_restaurant = getattr(self.request.user, "restaurant", None)

        if user_restaurant:
            # Get all tables for this restaurant
            context['assigned_tables'] = Table.objects.filter(restaurant=user_restaurant)
        else:
            context['assigned_tables'] = []

        return context

    




class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/customer_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get 6 available menu items
        menus = Item.objects.filter(is_available=True)[:9]

        context["menus"] = menus
        return context
