from django.shortcuts import render, redirect
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from organizations.models import Restaurant
from django.utils import timezone
from orders.models import Order
from reservations.models import Reservation
from django.db.models import Sum, Max
from django.views.generic import TemplateView



class HomeCreateView(TemplateView):
    
    template_name='cores/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all restaurants, you can order as needed
        context['restaurants'] = Restaurant.objects.all()[:12]  # load first 12, carousel will show 3 at a time
        return context




# class DashboardView(LoginRequiredMixin, TemplateView):

#     def get_template_names(self):
#         user_type = self.request.user.user_type
#         template_map = {
#             "OWNER": "dashboards/owner_dashboard.html",
#             "MANAGER": "dashboards/manager_dashboard.html",
#             "CASHIER": "dashboards/cashier_dashboard.html",
#             "CHEF": "dashboards/chef_dashboard.html",
#             "WAITER": "dashboards/waiter_dashboard.html",
#             "CUSTOMER": "dashboards/customer_dashboard.html",
#         }
#         return [template_map.get(user_type, "dashboards/customer_dashboard.html")]

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         # Restaurants user can access
#         if user.user_type == "OWNER":
#             restaurants = Restaurant.objects.filter(owner=user)
#         else:
#             restaurants = Restaurant.objects.filter(users=user)

#         context['total_restaurants'] = restaurants.count()
#         context['total_orders'] = Order.objects.filter(restaurant__in=restaurants).count()
#         context['total_reservations'] = Reservation.objects.filter(restaurant__in=restaurants).count()

#         now = timezone.now()
#         revenue = Order.objects.filter(
#             restaurant__in=restaurants,
#             created_at__year=now.year,
#             created_at__month=now.month
#         ).aggregate(total=Sum('total_amount'))['total'] or 0
#         context['revenue_this_month'] = revenue

#         context['total_customers'] = restaurants.values('users').distinct().count()
#         context['top_restaurant_rating'] = restaurants.aggregate(max_rating=Max('rating'))['max_rating'] or 0
#         context['year'] = now.year

#         return context




