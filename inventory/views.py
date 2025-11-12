from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import StockItem, StockMovement, Purchase, PurchaseItem, Supplier, Sale, SaleItem, Restaurant
from django.http import HttpResponseForbidden
from decimal import Decimal, InvalidOperation


from django.http import JsonResponse

from .models import StockMovement, StockItem, Restaurant



# ======================
# STOCK ITEMS
# ======================

class StockItemListView(LoginRequiredMixin, ListView):
    model = StockItem
    template_name = 'inventory/stockitem_list.html'
    context_object_name = 'inventory_items'

    def get_queryset(self):
        user = self.request.user
        queryset = StockItem.objects.all()

        # OWNER sees all
        if user.user_type != "OWNER":
            if hasattr(user, 'restaurant') and user.restaurant:
                queryset = queryset.filter(restaurant=user.restaurant)
            else:
                queryset = StockItem.objects.none()

        # ✅ handle search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context




# class StockItemCreateView(LoginRequiredMixin, CreateView):
#     model = StockItem
#     fields = ['restaurant', 'name', 'unit', 'quantity', 'min_threshold']
#     template_name = 'inventory/stockitem_form.html'
#     success_url = reverse_lazy('inventory:list')

#     def get_form(self, form_class=None):
#         form = super().get_form(form_class)
#         user = self.request.user
#         # Filter restaurants kulingana na user
#         if user.user_type == "OWNER":
#             form.fields['restaurant'].queryset = Restaurant.objects.all()
#         else:
#             form.fields['restaurant'].queryset = Restaurant.objects.filter(users=user)
#         return form

#     def form_valid(self, form):
#         # Assign restaurant automatically kama staff hana kuchagua
#         if not form.instance.restaurant:
#             form.instance.restaurant = self.request.user.restaurant
#         return super().form_valid(form)


class StockItemCreateView(LoginRequiredMixin, CreateView):
    model = StockItem
    fields = [
        'restaurant',
        'name',
        'unit',
        'quantity',
        'min_threshold',
        'buying_price',
        'selling_price'
    ]
    template_name = 'inventory/stockitem_form.html'
    success_url = reverse_lazy('inventory:list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        if user.user_type == "OWNER":
            form.fields['restaurant'].queryset = Restaurant.objects.all()
        else:
            form.fields['restaurant'].queryset = Restaurant.objects.filter(users=user)
        return form

    def form_valid(self, form):
        if not form.instance.restaurant:
            form.instance.restaurant = self.request.user.restaurant
        return super().form_valid(form)



class StockItemUpdateView(LoginRequiredMixin, UpdateView):
    model = StockItem
    fields = ['name', 'unit', 'quantity', 'min_threshold', 'buying_price', 'selling_price']  # added
    template_name = 'inventory/stockitem_form.html'
    success_url = reverse_lazy('inventory:list')

    def get_queryset(self):
        # ensure user can only update items of their restaurant
        user = self.request.user
        if user.user_type == "OWNER":
            return StockItem.objects.all()
        return StockItem.objects.filter(restaurant=user.restaurant)


class StockItemDeleteView(LoginRequiredMixin, DeleteView):
    model = StockItem
    template_name = 'inventory/stockitem_confirm_delete.html'
    success_url = reverse_lazy('inventory:list')

    def get_queryset(self):
        return StockItem.objects.filter(restaurant=self.request.user.restaurant)
    
    


# ======================
# STOCK MOVEMENTS
# ======================

class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/stockmovement_list.html'
    context_object_name = 'movements'

    def get_queryset(self):
        user = self.request.user

        # 👑 OWNER anaona movements zote
        if user.user_type == "OWNER":
            return StockMovement.objects.all().order_by('-created_at')

        # 👨‍🍳 Staff (Manager, Chef, Cashier, Waiter)
        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            # kama ana restaurant moja (ForeignKey)
            if hasattr(user, 'restaurant') and user.restaurant:
                return StockMovement.objects.filter(
                    item__restaurant=user.restaurant
                ).order_by('-created_at')

            # kama ana assigned restaurants nyingi (ManyToMany)
            elif hasattr(user, 'assigned_restaurants'):
                return StockMovement.objects.filter(
                    item__restaurant__in=user.assigned_restaurants.all()
                ).order_by('-created_at')

        # wengine (ambao si owner wala staff waliotajwa)
        return StockMovement.objects.none()






class StockMovementCreateView(LoginRequiredMixin, CreateView):
    model = StockMovement
    fields = ['restaurant', 'item', 'movement_type', 'quantity', 'note']
    template_name = 'inventory/stockmovement_form.html'
    success_url = reverse_lazy('inventory:movements')

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user

        # ===== Determine restaurants based on user type =====
        if hasattr(user, 'user_type') and user.user_type == 'OWNER':
            # Owner sees all restaurants
            form.fields['restaurant'].queryset = Restaurant.objects.all()
        elif hasattr(user, 'restaurant') and user.restaurant:
            # Regular user sees only their restaurant
            form.fields['restaurant'].queryset = Restaurant.objects.filter(id=user.restaurant.id)
            form.initial['restaurant'] = user.restaurant.id
        else:
            form.fields['restaurant'].queryset = Restaurant.objects.none()

        # ===== Filter items based on selected restaurant =====
        if self.request.method == 'POST':
            restaurant_id = self.request.POST.get('restaurant')
        else:
            restaurant_id = form.initial.get('restaurant')

        if restaurant_id:
            form.fields['item'].queryset = StockItem.objects.filter(restaurant_id=restaurant_id)
        else:
            form.fields['item'].queryset = StockItem.objects.none()

        return form


# ===== API endpoint for AJAX dynamic items =====
def get_items_by_restaurant(request, restaurant_id):
    items = StockItem.objects.filter(restaurant_id=restaurant_id)
    data = [
        {"id": item.id, "name": item.name, "quantity": float(item.quantity), "unit": item.unit}
        for item in items
    ]
    return JsonResponse(data, safe=False)


# class StockMovementCreateView(LoginRequiredMixin, CreateView):
#     model = StockMovement
#     fields = ['item', 'movement_type', 'quantity', 'note']
#     template_name = 'inventory/stockmovement_form.html'
#     success_url = reverse_lazy('inventory:movements')

#     def get_form(self, *args, **kwargs):
#         form = super().get_form(*args, **kwargs)
#         if hasattr(self.request.user, "restaurant") and self.request.user.restaurant:
#             form.fields['item'].queryset = StockItem.objects.filter(restaurant=self.request.user.restaurant)
#         return form

# ======================
# SUPPLIERS
# ======================

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'OWNER':
            # Owner → suppliers of restaurants they own
            return Supplier.objects.filter(restaurant__owner=user)
        else:
            # Staff → suppliers of restaurants they are assigned to
            return Supplier.objects.filter(restaurant__users=user)


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    fields = ['name', 'phone', 'email', 'address']  # remove 'restaurant' from form
    template_name = "inventory/supplier_form.html"
    success_url = reverse_lazy('inventory:suppliers')

    def form_valid(self, form):
        user = self.request.user
        if user.user_type == 'OWNER':
            # Auto-assign first restaurant owned by the user
            form.instance.restaurant = Restaurant.objects.filter(owner=user).first()
        else:
            # Auto-assign first restaurant the staff is assigned to
            form.instance.restaurant = Restaurant.objects.filter(users=user).first()
        
        return super().form_valid(form)



class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    fields = ['restaurant', 'name', 'phone', 'email', 'address']
    template_name = "inventory/supplier_form.html"
    success_url = reverse_lazy('inventory:suppliers')

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'OWNER':
            return Supplier.objects.filter(restaurant__owner=user)
        else:
            return Supplier.objects.filter(restaurant__users=user)


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = "inventory/supplier_confirm_delete.html"
    success_url = reverse_lazy('inventory:suppliers')

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'OWNER':
            return Supplier.objects.filter(restaurant__owner=user)
        else:
            return Supplier.objects.filter(restaurant__users=user)



# ======================
# PURCHASES
# ======================



class PurchaseListView(LoginRequiredMixin, ListView):
    model = Purchase
    template_name = 'inventory/purchase_list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        # Pata restaurants user owns
        user_restaurants = Restaurant.objects.filter(owner=self.request.user)
        return Purchase.objects.filter(restaurant__in=user_restaurants)


class PurchaseCreateView(LoginRequiredMixin, View):
    template_name = "inventory/purchase_form.html"

    def get_user_restaurants(self, user):
        """
        Returns all restaurants the user owns
        """
        return Restaurant.objects.filter(owner=user)

    def get(self, request, *args, **kwargs):
        user_restaurants = self.get_user_restaurants(request.user)
        suppliers = Supplier.objects.filter(restaurant__in=user_restaurants)
        stock_items = StockItem.objects.filter(restaurant__in=user_restaurants)
        return render(
            request,
            self.template_name,
            {'suppliers': suppliers, 'stock_items': stock_items, 'restaurants': user_restaurants}
        )

    def post(self, request, *args, **kwargs):
        user_restaurants = self.get_user_restaurants(request.user)

        # Get restaurant from form
        restaurant_id = request.POST.get('restaurant')
        if not restaurant_id or int(restaurant_id) not in [r.id for r in user_restaurants]:
            return HttpResponseForbidden("You cannot create a purchase for this restaurant.")

        restaurant = get_object_or_404(Restaurant, id=restaurant_id)

        supplier_id = request.POST.get('supplier')
        notes = request.POST.get('notes')
        total_cost = request.POST.get('total_cost') or 0

        purchase = Purchase.objects.create(
            supplier_id=supplier_id,
            restaurant=restaurant,
            notes=notes,
            total_cost=total_cost
        )

        items = request.POST.getlist('item[]')
        quantities = request.POST.getlist('quantity[]')
        unit_costs = request.POST.getlist('unit_cost[]')

        for i, item_id in enumerate(items):
            # Validate item belongs to one of user's restaurants
            stock_item = get_object_or_404(StockItem, id=item_id, restaurant__in=user_restaurants)

            qty = float(quantities[i])
            cost = float(unit_costs[i])

            PurchaseItem.objects.create(
                purchase=purchase,
                item=stock_item,
                quantity=qty,
                unit_cost=cost,
                line_total=qty * cost
            )

            # Update stock quantity
            stock_item.quantity += qty
            stock_item.save()

        return redirect('inventory:purchases')





# ===============================
# List Sales
# ===============================




from django.views.generic import ListView
from django.db.models import Q

from django.views.generic import ListView
from django.db.models import Q

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = "inventory/sale_list.html"
    context_object_name = "sales"

    def get_queryset(self):
        user = self.request.user

        # Base queryset depending on user type
        if user.user_type == "OWNER":
            queryset = Sale.objects.all()
        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            if hasattr(user, 'restaurant') and user.restaurant:
                queryset = Sale.objects.filter(restaurant=user.restaurant)
            else:
                queryset = Sale.objects.none()
        else:
            queryset = Sale.objects.none()

        queryset = queryset.order_by('-created_at')

        # ✅ Search filter (now includes notes)
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(items__item__name__icontains=search) |
                Q(notes__icontains=search)                # ✅ Add notes here
            ).distinct()

        # ✅ Attach profit dynamically
        for sale in queryset:
            total_profit = sum(
                (item.unit_price - item.item.buying_price) * item.quantity
                for item in sale.items.all()
            )
            sale.total_profit = total_profit

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get('search', '')
        return context



# class SaleCreateView(LoginRequiredMixin, View):
#     template_name = "inventory/sale_form.html"

#     def get_user_restaurants(self, user):
#         if user.user_type == "OWNER":
#             return Restaurant.objects.all()
#         elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
#             return Restaurant.objects.filter(id=user.restaurant.id) if user.restaurant else Restaurant.objects.none()
#         return Restaurant.objects.none()

#     def get(self, request):
#         restaurants = self.get_user_restaurants(request.user)
#         stock_items = StockItem.objects.filter(restaurant__in=restaurants)
#         return render(request, self.template_name, {"restaurants": restaurants, "stock_items": stock_items})

#     def post(self, request):
#         user_restaurants = self.get_user_restaurants(request.user)

#         # Validate restaurant
#         try:
#             restaurant_id = int(request.POST.get("restaurant"))
#             restaurant = get_object_or_404(user_restaurants, id=restaurant_id)
#         except (ValueError, TypeError):
#             return HttpResponseForbidden("Invalid restaurant selected.")

#         customer_name = request.POST.get("customer_name") or ""
#         notes = request.POST.get("notes") or ""

#         # Convert total_amount safely
#         try:
#             total_amount = Decimal(request.POST.get("total_amount") or "0")
#         except InvalidOperation:
#             total_amount = Decimal("0")

#         sale = Sale.objects.create(
#             restaurant=restaurant,
#             customer_name=customer_name,
#             notes=notes,
#             total_amount=total_amount
#         )

#         items = request.POST.getlist("item[]")
#         quantities = request.POST.getlist("quantity[]")
#         unit_prices = request.POST.getlist("unit_price[]")

#         for i, item_id in enumerate(items):
#             stock_item = get_object_or_404(StockItem, id=item_id, restaurant=restaurant)

#             # Convert quantities and prices safely
#             try:
#                 qty = Decimal(quantities[i])
#                 price = Decimal(unit_prices[i])
#             except (InvalidOperation, IndexError):
#                 continue  # skip invalid entries

#             if stock_item.quantity < qty:
#                 sale.delete()  # rollback sale
#                 return HttpResponseForbidden(f"Not enough stock for {stock_item.name}")

#             # Update stock safely
#             stock_item.quantity -= qty
#             stock_item.save()

#             SaleItem.objects.create(
#                 sale=sale,
#                 item=stock_item,
#                 quantity=qty,
#                 unit_price=price
#             )

#         return redirect("inventory:sales")
    
from decimal import Decimal, InvalidOperation

from django.db import transaction



class SaleCreateView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/sale_form.html"

    def get_user_restaurants(self, user):
        if user.user_type == "OWNER":
            return Restaurant.objects.all()
        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            return Restaurant.objects.filter(id=user.restaurant.id) if user.restaurant else Restaurant.objects.none()
        return Restaurant.objects.none()

    def get(self, request, *args, **kwargs):
        restaurants = self.get_user_restaurants(request.user)
        stock_items = StockItem.objects.filter(restaurant__in=restaurants)
        return render(request, self.template_name, {
            "restaurants": restaurants,
            "stock_items": stock_items
        })

    def post(self, request, *args, **kwargs):
        user_restaurants = self.get_user_restaurants(request.user)

        try:
            restaurant_id = int(request.POST.get("restaurant"))
            restaurant = get_object_or_404(user_restaurants, id=restaurant_id)
        except (ValueError, TypeError):
            return HttpResponseForbidden("Invalid restaurant selected.")

        customer_name = request.POST.get("customer_name") or ""
        notes = request.POST.get("notes") or ""
        total_amount = Decimal(request.POST.get("total_amount") or "0")

        with transaction.atomic():
            sale = Sale.objects.create(
                restaurant=restaurant,
                customer_name=customer_name,
                notes=notes,
                total_amount=total_amount
            )

            items = request.POST.getlist("item[]")
            quantities = request.POST.getlist("quantity[]")
            unit_prices = request.POST.getlist("unit_price[]")

            for i, item_id in enumerate(items):
                stock_item = get_object_or_404(StockItem, id=item_id, restaurant=restaurant)

                try:
                    qty = Decimal(quantities[i])
                    price = Decimal(unit_prices[i])
                except (InvalidOperation, IndexError):
                    continue

                if stock_item.quantity < qty:
                    transaction.set_rollback(True)
                    return HttpResponseForbidden(f"Not enough stock for {stock_item.name}")

                SaleItem.objects.create(
                    sale=sale,
                    item=stock_item,
                    quantity=qty,
                    unit_price=price
                )

        return redirect("inventory:sales")
 

class SaleUpdateView(LoginRequiredMixin, View):
    template_name = "inventory/sale_form.html"

    def get(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        restaurants = Restaurant.objects.all() if request.user.user_type == "OWNER" else Restaurant.objects.filter(id=request.user.restaurant.id)
        stock_items = StockItem.objects.filter(restaurant__in=restaurants)

        return render(request, self.template_name, {
            "sale": sale,
            "restaurants": restaurants,
            "stock_items": stock_items
        })

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)

        try:
            restaurant_id = int(request.POST.get("restaurant"))
            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        except (ValueError, TypeError):
            return HttpResponseForbidden("Invalid restaurant selected.")

        sale.customer_name = request.POST.get("customer_name") or ""
        sale.notes = request.POST.get("notes") or ""

        try:
            sale.total_amount = Decimal(request.POST.get("total_amount") or "0")
        except InvalidOperation:
            sale.total_amount = Decimal("0")

        sale.save()
        # Optionally: handle SaleItem updates if needed
        return redirect("inventory:sales")


# ---- Delete Sale ----
class SaleDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        if request.user.user_type != "OWNER":
            return HttpResponseForbidden("Only OWNER can delete sales.")
        sale.delete()
        return redirect("inventory:sales")
    
    

# ---------------- Inventory History ----------------
class InventoryHistoryView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/inventory_history.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = getattr(self.request.user, "restaurant", None)
        if restaurant:
            movements = StockMovement.objects.filter(item__restaurant=restaurant)
            purchases = Purchase.objects.filter(restaurant=restaurant)
            sales = Sale.objects.filter(restaurant=restaurant)
            history = sorted(
                list(movements) + list(purchases) + list(sales),
                key=lambda x: x.created_at,
                reverse=True
            )
            context['history'] = history
        else:
            context['history'] = []
        return context
