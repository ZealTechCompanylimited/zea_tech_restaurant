from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import User
from .models import Reservation,Branch, Restaurant
from django.urls import reverse
from django.db.models import Q



# ----------------- LIST -----------------


class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'reservations/reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        user = self.request.user

        # 👇 Restrict reservations based on assigned restaurant
        if hasattr(user, 'restaurant') and user.restaurant and user.user_type in ["OWNER", "MANAGER", "CHEF", "WAITER", "CASHIER"]:
            queryset = Reservation.objects.filter(restaurant=user.restaurant)

        # Customers → reservations zao pekee
        elif user.user_type == "CUSTOMER":
            queryset = Reservation.objects.filter(customer=user)

        else:
            queryset = Reservation.objects.none()

        # Search by guest name or customer username
        search_name = self.request.GET.get("search_name")
        if search_name:
            queryset = queryset.filter(
                Q(guest_name__icontains=search_name) |
                Q(customer__username__icontains=search_name)
            )

        # Filter by date range
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        if start_date and end_date:
            queryset = queryset.filter(date__gte=start_date, date__lte=end_date)

        return queryset.order_by('-date', '-time')

# ----------------- CREATE -----------------
class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    template_name = "reservations/reservation_form.html"
    fields = ["restaurant", "branch", "date", "time", "party_size", "notes"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ✅ Restrict restaurants and branches to user's assigned restaurant
        if hasattr(user, 'restaurant') and user.restaurant:
            context['restaurants'] = Restaurant.objects.filter(id=user.restaurant.id, is_active=True)
            context['branches'] = Branch.objects.filter(restaurant=user.restaurant)
        else:
            context['restaurants'] = Restaurant.objects.none()
            context['branches'] = Branch.objects.none()

        return context

    def form_valid(self, form):
        user = self.request.user

        # Assign current user as customer
        form.instance.customer = user

        # Ensure reservation is for user's assigned restaurant
        if hasattr(user, 'restaurant') and user.restaurant:
            form.instance.restaurant = user.restaurant
        else:
            form.add_error('restaurant', "You do not have an assigned restaurant.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("reservations:list")


# ----------------- UPDATE -----------------
class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    fields = [
        'restaurant', 'branch', 'date', 'time', 'party_size',
        'notes', 'status', 'guest_name', 'guest_phone',
    ]
    template_name = 'reservations/reservation_update.html'
    success_url = reverse_lazy('reservations:list')

    def get_queryset(self):
        user = self.request.user

        if user.user_type == "OWNER":
            # Owner → reservations of branches/restaurants they own
            return Reservation.objects.filter(restaurant__owner=user)
        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"]:
            # Staff → reservations of their assigned restaurant
            return Reservation.objects.filter(restaurant=user.restaurant)
        elif user.user_type == "CUSTOMER":
            # Customer → own reservations only
            return Reservation.objects.filter(customer=user)
        return Reservation.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Restaurants dropdown
        if user.user_type == "OWNER":
            context['restaurants'] = Restaurant.objects.filter(owner=user)
        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"]:
            context['restaurants'] = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            context['restaurants'] = Restaurant.objects.none()

        # Branches dropdown filtered by restaurants user can access
        context['branches'] = Branch.objects.filter(restaurant__in=context['restaurants'])

        # Statuses & customers
        context['statuses'] = Reservation.STATUS_CHOICES
        context['customers'] = User.objects.filter(user_type='CUSTOMER') if user.user_type in ['OWNER','MANAGER'] else None

        return context

    def form_valid(self, form):
        user = self.request.user
        if user.user_type in ['OWNER', 'MANAGER']:
            customer_id = self.request.POST.get('customer')
            if customer_id:
                form.instance.customer_id = customer_id
        else:
            # Ensure customer cannot edit others
            form.instance.customer = user
        return super().form_valid(form)


# ----------------- DELETE -----------------
class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'reservations/reservation_confirm_delete.html'
    success_url = reverse_lazy('reservations:list')
