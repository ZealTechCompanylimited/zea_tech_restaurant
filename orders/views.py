from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.views.generic import DeleteView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Order, OrderItem, Table, Invoice
from menu.models import Item
from organizations.models import Restaurant
from django.db.models import Sum, F, FloatField,Q
# from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib.auth.decorators import login_required
User = settings.AUTH_USER_MODEL  # use custom user model




# --- ORDER LIST ---

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        user = self.request.user

        # Base queryset according to user type
        if user.user_type in ["OWNER" ]:
            queryset = Order.objects.all()
        elif user.user_type in ["CHEF", "WAITER","MANAGER","CASHIER"]:
            queryset = Order.objects.filter(restaurant=user.restaurant)
        elif user.user_type == "CUSTOMER":
            queryset = Order.objects.filter(created_by=user)
        else:
            return Order.objects.none()

        # Search filter: customer name
        search_name = self.request.GET.get("search_name")
        if search_name:
            queryset = queryset.filter(
                Q(guest_name__icontains=search_name) |
                Q(created_by__username__icontains=search_name)
            )

        # Date filter
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
        else:
            # Optional: default show today's orders
            pass  # don't filter by default if you want all orders

        return queryset.order_by("-created_at")


# --- ORDER CREATE ---

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = "orders/order_form.html"
    fields = ["restaurant", "order_type", "table", "notes", "guest_name", "guest_phone"]
    success_url = reverse_lazy("orders:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.filter(is_active=True)
        context['items'] = Item.objects.filter(restaurant__in=context['restaurants'])
        context['tables'] = Table.objects.filter(is_active=True)
        context['current_user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        restaurant_id = request.POST.get("restaurant")
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        order_type = request.POST.get("order_type")
        table_id = request.POST.get("table")
        table = Table.objects.filter(id=table_id).first() if table_id else None
        notes = request.POST.get("notes", "")
        guest_name = request.POST.get("guest_name", "")
        guest_phone = request.POST.get("guest_phone", "")

        # Assign logged-in user as created_by (even for customer)
        created_by = request.user

        order = Order.objects.create(
            restaurant=restaurant,
            created_by=created_by,
            order_type=order_type,
            table=table,
            notes=notes,
            guest_name=guest_name if order_type in ["DELIVERY","TAKEAWAY"] else "",
            guest_phone=guest_phone if order_type in ["DELIVERY","TAKEAWAY"] else "",
        )

        # Add order items
        item_ids = request.POST.getlist("item")
        quantities = request.POST.getlist("quantity")
        for i, item_id in enumerate(item_ids):
            if not item_id:
                continue
            item = get_object_or_404(Item, id=item_id)
            qty = int(quantities[i])
            line_total = (item.price + item.tax_rate) * qty
            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=qty,
                unit_price=item.price,
                tax_rate=item.tax_rate,
                line_total=line_total
            )

        # Calculate totals
        totals = order.items.aggregate(
            subtotal=Sum(F('unit_price') * F('quantity'), output_field=FloatField()),
            tax_total=Sum(F('tax_rate') * F('quantity'), output_field=FloatField())
        )
        order.subtotal = totals["subtotal"] or 0
        order.tax_total = totals["tax_total"] or 0
        order.grand_total = order.subtotal + order.tax_total
        order.save()



        return redirect("orders:list")





class OrderUpdateView(LoginRequiredMixin, View):
    template_name = "orders/order_update.html"

    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        tables = Table.objects.all()  # Retrieve all tables
        return render(request, self.template_name, {
            "object": order,
            "tables": tables,
            "order_types": Order.ORDER_TYPES,
            "statuses": Order.STATUS,
        })

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk)

        order.order_type = request.POST.get("order_type")
        order.status = request.POST.get("status")
        order.notes = request.POST.get("notes")

        table_id = request.POST.get("table")
        order.table = Table.objects.filter(id=table_id).first() if table_id else None

        order.save()
        return redirect("orders:list")



class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = "orders/order_confirm_delete.html"
    success_url = reverse_lazy("orders:list")

  
  
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != "OWNER":
            raise PermissionDenied("you are not allowed to delete orders")
        
        return super().dispatch(request, *args, **kwargs)





class TableListView(LoginRequiredMixin, ListView):
    model = Table
    template_name = "orders/table_list.html"
    context_object_name = "tables"

    def get_queryset(self):
        user = self.request.user

        # If user is owner, return all tables
        if user.user_type == "OWNER":
            return Table.objects.all()

        # If user is manager, chef, or waiter, filter accordingly
        elif user.user_type in ["MANAGER", "CHEF", "WAITER"]:
            # Example: filter by restaurant they belong to
            return Table.objects.filter(restaurant=user.restaurant)

        # Default: return empty queryset
        return Table.objects.none()






# Create Table
class TableCreateView(LoginRequiredMixin, CreateView):
    model = Table
    fields = ["name", "seats", "is_active"]
    template_name = "orders/table_form.html"
    success_url = reverse_lazy("orders:table_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["restaurants"] = Restaurant.objects.all().order_by("name")
        return context

    def form_valid(self, form):
        restaurant_id = self.request.POST.get("restaurant")
        if not restaurant_id:
            form.add_error("restaurant", "Please select a restaurant.")
            return self.form_invalid(form)

        form.instance.restaurant = Restaurant.objects.get(id=restaurant_id)
        response = super().form_valid(form)
        messages.success(self.request, f"Table '{form.instance.name}' created successfully!")
        return response


# Update Table
class TableUpdateView(LoginRequiredMixin, UpdateView):
    model = Table
    fields = ["name", "seats", "is_active"]
    template_name = "orders/table_form.html"
    success_url = reverse_lazy("orders:table_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["restaurants"] = Restaurant.objects.all().order_by("name")
        return context

    def form_valid(self, form):
        restaurant_id = self.request.POST.get("restaurant")
        if restaurant_id:
            form.instance.restaurant = Restaurant.objects.get(id=restaurant_id)
        response = super().form_valid(form)
        messages.success(self.request, f"Table '{form.instance.name}' updated successfully!")
        return response


# Delete Table
class TableDeleteView(LoginRequiredMixin, DeleteView):
    model = Table
    template_name = "orders/table_confirm_delete.html"
    success_url = reverse_lazy("orders:table_list")

    def delete(self, request, *args, **kwargs):
        table = self.get_object()
        messages.success(request, f"Table '{table.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)





class InvoiceListView(ListView):
    model = Invoice
    template_name = 'orders/invoice_list.html'
    context_object_name = 'invoices'

class InvoiceCreateView(CreateView):
    model = Invoice
    fields = ['order', 'paid']
    template_name = 'orders/invoice_form.html'
    success_url = reverse_lazy('orders:invoices')





