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

        # Owner sees all reservations
        if user.user_type == "OWNER":
            queryset = Reservation.objects.all()

        # Managers, chefs, waiters, cashiers see reservations for their restaurant
        elif user.user_type in ["MANAGER", "WAITER", "CHEF", "CASHIER"]:
            # Assuming user has `restaurant` field
            queryset = Reservation.objects.filter(restaurant=user.restaurant)

        # Customers see only their own reservations
        elif user.user_type == "CUSTOMER":
            queryset = Reservation.objects.filter(customer=user)

        else:
            return Reservation.objects.none()

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
        context['restaurants'] = Restaurant.objects.filter(is_active=True)
        context['branches'] = Branch.objects.all()
        return context

    def form_valid(self, form):
        form.instance.customer = self.request.user
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all()
        context['restaurants'] = Restaurant.objects.all()
        context['statuses'] = Reservation.STATUS_CHOICES
        context['customers'] = User.objects.filter(user_type='CUSTOMER')
        return context

    def form_valid(self, form):
        if self.request.user.user_type in ['OWNER', 'MANAGER']:
            customer_id = self.request.POST.get('customer')
            if customer_id:
                form.instance.customer_id = customer_id
        else:
            form.instance.customer = self.request.user
        return super().form_valid(form)

# ----------------- DELETE -----------------
class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'reservations/reservation_confirm_delete.html'
    success_url = reverse_lazy('reservations:list')
