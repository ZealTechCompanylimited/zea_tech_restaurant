from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Item, Category
from organizations.models import Restaurant
from django.db.models import Q

# ======================
# CATEGORY VIEWS
# ======================



class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = ["name", "is_active", "restaurant"]
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # OWNER → restaurants alizomiliki
        if user.user_type == "OWNER":
            form.fields["restaurant"].queryset = Restaurant.objects.filter(owner=user)

        # STAFF (MANAGER, CHEF, WAITER, CASHIER) → restaurant yake tu
        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"] and hasattr(user, "restaurant"):
            form.fields["restaurant"].queryset = Restaurant.objects.filter(id=user.restaurant.id)
            form.initial["restaurant"] = user.restaurant.id

        # CUSTOMER au wengine → hakuna restaurants
        else:
            form.fields["restaurant"].queryset = Restaurant.objects.none()

        return form

    def form_valid(self, form):
        user = self.request.user

        # Assign created_by automatically
        form.instance.created_by = user

        # Validate if user can create for that restaurant
        restaurant = form.cleaned_data.get("restaurant")
        if not restaurant:
            form.add_error("restaurant", "Please select a valid restaurant.")
            return self.form_invalid(form)

        if user.user_type != "OWNER" and getattr(user, "restaurant", None) != restaurant:
            form.add_error("restaurant", "You cannot create a category for another restaurant.")
            return self.form_invalid(form)

        messages.success(self.request, f"Category '{form.instance.name}' created successfully!")
        return super().form_valid(form)
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "menu/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        user = self.request.user

        # OWNER → aone categories za restaurants alizomiliki
        if user.user_type == "OWNER":
            return Category.objects.filter(restaurant__owner=user).order_by("restaurant__name", "name")

        # STAFF (MANAGER, CHEF, WAITER, CASHIER) → restaurant yake tu
        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"] and hasattr(user, "restaurant"):
            return Category.objects.filter(restaurant=user.restaurant).order_by("name")

        # CUSTOMER → hakuna access
        return Category.objects.none()



    
class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'is_active', 'restaurant']
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")

    def get_queryset(self):
        user = self.request.user

        # OWNER: can update only categories of restaurants he owns
        if user.user_type == "OWNER":
            return Category.objects.filter(restaurant__owner=user)

        # MANAGER: only categories of assigned restaurant
        if user.user_type == "MANAGER":
            return Category.objects.filter(restaurant=user.restaurant)

        # others → block
        return Category.objects.none()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # OWNER: show only restaurants he owns
        if user.user_type == "OWNER":
            form.fields["restaurant"].queryset = Restaurant.objects.filter(owner=user)

        # MANAGER: only his assigned restaurant
        elif user.user_type == "MANAGER":
            form.fields["restaurant"].queryset = Restaurant.objects.filter(id=user.restaurant.id)

        else:
            form.fields["restaurant"].queryset = Restaurant.objects.none()

        return form

    def form_valid(self, form):
        # preserve created_by if existing
        if not form.instance.created_by:
            form.instance.created_by = self.request.user
        return super().form_valid(form)

    
    
# Delete
# -----------------------------
class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "menu/category_confirm_delete.html"
    success_url = reverse_lazy("menu:category_list")



class MenuListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = "menu/menu_list.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        user = self.request.user

        # 👇 Hata OWNER anaona menu za restaurant yake tu
        if hasattr(user, 'restaurant') and user.restaurant:
            return Item.objects.filter(restaurant=user.restaurant)
        
        # Default: empty queryset
        return Item.objects.none()





# Step 1: Show all restaurants
class CustomerRestaurantListView(ListView):
    model = Restaurant
    template_name = "menu/customer_restaurant_list.html"
    context_object_name = "restaurants"

    def get_queryset(self):
        return Restaurant.objects.filter(is_active=True)


# Step 2: Show menu items of selected restaurant
class MenuItemsByRestaurantView(ListView):
    model = Item
    template_name = "menu/menu_items_by_restaurant.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        restaurant_id = self.kwargs.get("restaurant_id")
        return Item.objects.filter(restaurant_id=restaurant_id).select_related("category")


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "menu/item_detail.html"
    context_object_name = "item"





class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = ["category", "name", "sku", "price", "tax_rate", "is_available", "image", "restaurant"]
    template_name = "menu/item_form.html"
    success_url = reverse_lazy("menu:menu_list")  # redirect to menu list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filter categories by user's restaurant if exists
        if self.request.user.user_type == "OWNER":
            context['categories'] = Category.objects.all()
        elif hasattr(self.request.user, "restaurant") and self.request.user.restaurant:
            context['categories'] = Category.objects.filter(restaurant=self.request.user.restaurant)
        else:
            context['categories'] = Category.objects.all()
        # All restaurants for dropdown
        context['restaurants'] = Restaurant.objects.all()
        # Pass current user for Created By display
        context['current_user'] = self.request.user
        return context

    def form_valid(self, form):
        # Auto-assign restaurant if user has one
        if hasattr(self.request.user, "restaurant") and self.request.user.restaurant:
            form.instance.restaurant = self.request.user.restaurant
        # Auto-assign created_by
        form.instance.created_by = self.request.user
        return super().form_valid(form)




class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    fields = ["category", "name", "sku", "price", "tax_rate", "is_available", "image"]
    template_name = "menu/item_form.html"
    success_url = reverse_lazy("menu:menu_list")

    # SECURITY: prevent editing items outside user's restaurant
    def get_queryset(self):
        user = self.request.user

        # OWNER → items za restaurant anazomiliki tu
        if user.user_type == "OWNER":
            return Item.objects.filter(category__restaurant__owner=user)

        # MANAGER / STAFF → items za restaurant aliyo-assigniwa
        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"]:
            return Item.objects.filter(category__restaurant=user.restaurant)

        # CUSTOMER → no permission
        return Item.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # CATEGORY FILTERING
        if user.user_type == "OWNER":
            context["categories"] = Category.objects.filter(
                restaurant__owner=user
            )

        elif user.user_type in ["MANAGER", "CHEF", "WAITER", "CASHIER"]:
            context["categories"] = Category.objects.filter(
                restaurant=user.restaurant
            )

        else:
            context["categories"] = Category.objects.none()

        # Optional: restaurants display in template
        if user.user_type == "OWNER":
            context["restaurants"] = Restaurant.objects.filter(owner=user)
        elif hasattr(user, "restaurant") and user.restaurant:
            context["restaurants"] = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            context["restaurants"] = Restaurant.objects.none()

        context["current_user"] = user
        return context

    def form_valid(self, form):
        # preserve original creator; do not overwrite
        if not form.instance.created_by:
            form.instance.created_by = self.request.user
        return super().form_valid(form)




class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = "menu/item_confirm_delete.html"
    success_url = reverse_lazy("menu:menu_list")
