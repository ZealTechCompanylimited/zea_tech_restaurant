from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
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
        # Show all restaurants in the dropdown
        form.fields["restaurant"].queryset = Restaurant.objects.all()
        return form

    def form_valid(self, form):
        # Automatically assign logged-in user as created_by
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "menu/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        user = self.request.user

        # If user is owner, return all tables
        if user.user_type == "OWNER":
            return Category.objects.all()

        # If user is manager, chef, or waiter, filter accordingly
        elif user.user_type in ["MANAGER", "CHEF", "WAITER"]:
            # Example: filter by restaurant they belong to
            return Category.objects.filter(restaurant=user.restaurant)

        # Default: return empty queryset
        return Category.objects.none()


    
class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'is_active', 'restaurant']
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # Return all restaurants in system
        if user.user_type == "OWNER":
            # Owner → anaona zote aliomiliki
            form.fields["restaurant"].queryset = Restaurant.objects.all()  # all restaurants
        elif hasattr(user, "restaurant") and user.restaurant:
            # Staff → one restaurant assigned
            form.fields["restaurant"].queryset = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            form.fields["restaurant"].queryset = Restaurant.objects.none()
        return form

    def form_valid(self, form):
        # Ensure created_by stays intact for update
        if not form.instance.created_by:
            form.instance.created_by = self.request.user
        return super().form_valid(form)

    
    
# Delete
# -----------------------------
class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "menu/category_confirm_delete.html"
    success_url = reverse_lazy("menu:category_list")



# class MenuListView(LoginRequiredMixin, ListView):
#     model = Item
#     template_name = "menu/menu_list.html"
#     context_object_name = "menu_items"

#     def get_queryset(self):
#         user = self.request.user

#         if user.user_type == "OWNER":
#             # Owner → menu zake na zile za restaurant zake
#             return Item.objects.filter(
#                 Q(created_by=user) | Q(restaurant__owner=user)
#             ).order_by('restaurant__name', 'category__name', 'name')

#         elif user.user_type == "MANAGER":
#             # Manager → menus za restaurants aliye assigniwa
#             return Item.objects.filter(
#                 restaurant__in=user.restaurants.all()
#             ).order_by('restaurant__name', 'category__name', 'name')

#         elif user.user_type in ["CHEF", "CASHIER", "WAITER"]:
#             return Item.objects.filter(
#                 restaurant__in=user.restaurants.all()
#             ).order_by('restaurant__name', 'category__name', 'name')

#         elif user.user_type == "CUSTOMER":
#             return Item.objects.filter(
#                 restaurant__is_active=True
#             ).order_by('restaurant__name', 'category__name', 'name')

#         return Item.objects.none()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user

#         if user.user_type == "OWNER":
#             context['restaurants'] = user.restaurants.all()
#         elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
#             context['restaurants'] = user.restaurants.all()
#         else:
#             context['restaurants'] = []

#         return context


















class MenuListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = "menu/menu_list.html"
    context_object_name = "menu_items"
    
    
    
    def get_queryset(self):
        user = self.request.user

        # If user is owner, return all tables
        if user.user_type == "OWNER":
            return Item.objects.all()

        # If user is manager, chef, or waiter, filter accordingly
        elif user.user_type in ["MANAGER", "CHEF", "WAITER","CASHIER"]:
            # Example: filter by restaurant they belong to
            return Item.objects.filter(restaurant=user.restaurant)

        # Default: return empty queryset
        return Item.objects.none()

    # def get_queryset(self):
    #     user = self.request.user

    #     if user.user_type == "OWNER":
    #         # Owner sees all menu items
    #         queryset = Item.objects.all().order_by('restaurant__name', 'category__name', 'name')

    #     elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
    #         # Staff sees menu items for their assigned restaurants
    #         queryset = Item.objects.filter(restaurant__in=user.restaurants.all())\
    #                                .order_by('restaurant__name', 'category__name', 'name')

    #     elif user.user_type == "CUSTOMER":
    #         # Customers see items only from active restaurants
    #         queryset = Item.objects.filter(restaurant__is_active=True)\
    #                                .order_by('restaurant__name', 'category__name', 'name')

    #     else:
    #         queryset = Item.objects.none()

    #     return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user

    #     if user.user_type == "OWNER":
    #         context['restaurants'] = Restaurant.objects.all()
    #     elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
    #         context['restaurants'] = user.restaurants.all()
    #     else:
    #         context['restaurants'] = []

    #     return context



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
    template_name = "menu/item_form.html"  # use same template as create
    success_url = reverse_lazy("menu:menu_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filter categories based on user's restaurant if exists
        if user.user_type == "OWNER":
            context['categories'] = Category.objects.all()

        elif hasattr(user, "restaurant") and user.restaurant:
            context['categories'] = Category.objects.filter(restaurant=user.restaurant)
        else:
            context['categories'] = Category.objects.all()

        # Restaurants for display (optional)
        context['restaurants'] = Restaurant.objects.all()

        # Pass current user for "Created By" readonly input
        context['current_user'] = user

        return context

    def form_valid(self, form):
        # Update the created_by to current user
        form.instance.created_by = self.request.user
        return super().form_valid(form)



class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = "menu/item_confirm_delete.html"
    success_url = reverse_lazy("menu:menu_list")
