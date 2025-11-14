from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Organization, Restaurant, Branch
from django.conf import settings
from django.db.models import Q
User = settings.AUTH_USER_MODEL 

# -------------------
# RESTAURANT VIEWS
# -------------------
class RestaurantListView(LoginRequiredMixin, ListView):
    model = Restaurant
    template_name = 'organizations/restaurant_list.html'
    context_object_name = 'restaurants'

    def get_queryset(self):
        user = self.request.user

        # OWNER → aone restaurants zote alizomiliki
        if user.user_type == "OWNER":
            return Restaurant.objects.filter(owner=user).order_by('name')

        # MANAGER → aone restaurant yake tu
        elif user.user_type == "MANAGER" and hasattr(user, 'restaurant'):
            return Restaurant.objects.filter(id=user.restaurant.id)

        # STAFF (CHEF, WAITER, CASHIER) → aone restaurant yake tu
        elif user.user_type in ["CHEF", "WAITER", "CASHIER"] and hasattr(user, 'restaurant'):
            return Restaurant.objects.filter(id=user.restaurant.id)

        # CUSTOMER → optional: aone active restaurants tu
        elif user.user_type == "CUSTOMER":
            return Restaurant.objects.filter(is_active=True).order_by('name')

        # Default: hakuna
        return Restaurant.objects.none()


class RestaurantCreateView(LoginRequiredMixin, CreateView):
    model = Restaurant
    fields = ['name', 'code', 'address', 'phone', 'timezone', 'is_active']
    template_name = 'organizations/restaurant_form.html'
    success_url = reverse_lazy('organizations:restaurant_list')

    def dispatch(self, request, *args, **kwargs):
        # Only OWNER can create restaurants
        if request.user.user_type != "OWNER":
            messages.error(request, "Only owners can create restaurants.")
            return redirect('organizations:restaurant_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Assign logged-in user as owner
        form.instance.owner = self.request.user
        messages.success(self.request, f"Restaurant '{form.instance.name}' created successfully!")
        return super().form_valid(form)



class RestaurantUpdateView(LoginRequiredMixin, UpdateView):
    model = Restaurant
    fields = ['name', 'code', 'address', 'phone', 'timezone', 'is_active']
    template_name = 'organizations/restaurant_form.html'
    success_url = reverse_lazy('organizations:restaurant_list')

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'OWNER':
            # Owner → restaurants alizomiliki
            return Restaurant.objects.filter(owner=user)

        elif user.user_type in ['MANAGER', 'CHEF', 'CASHIER', 'WAITER']:
            # Staff → restaurants walizo-assigniwa
            return Restaurant.objects.filter(users=user)

        # Default → no access
        return Restaurant.objects.none()

    
    



class RestaurantDeleteView(LoginRequiredMixin, DeleteView):
    model = Restaurant
    template_name = 'organizations/restaurant_confirm_delete.html'
    success_url = reverse_lazy('organizations:restaurant_list')
    # def get_queryset(self):
    #     user = self.request.user
    #     # Owner/Manager delete restaurants zao tu
    #     if user.user_type == 'OWNER':
    #         return Restaurant.objects.filter(owner=user)
    #     elif user.user_type == 'MANAGER':
    #         return Restaurant.objects.filter(users=user)
        # return Restaurant.objects.none()
# -------------------
# ORGANIZATION VIEWS
# -------------------



class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = "organizations/organization_list.html"
    context_object_name = "organizations"

    def get_queryset(self):
        user = self.request.user

        # Owner → organizations alizozitengeneza
        if user.user_type == "OWNER":
            return Organization.objects.filter(created_by=user)

        # Manager → organizations alizoassigniwa
        elif user.user_type == "MANAGER":
            return Organization.objects.filter(managers=user)

        # Customer → hana organization
        elif user.user_type == "CUSTOMER":
            return Organization.objects.none()

        # Staff wengine → unaweza kurestrict
        return Organization.objects.none()





class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    fields = ['name', 'address', 'email', 'phone']
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('organizations:list')

    def form_valid(self, form):
        # Hapa automatically set created_by
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    fields = ['name', 'address', 'email', 'phone']
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('organizations:list')

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'OWNER':
            # Owner → update organizations system-wide or those he owns
            return Organization.objects.all()  # or filter(owner=user) if Organization has owner field

        elif user.user_type in ['MANAGER', 'CHEF', 'CASHIER', 'WAITER']:
            # Staff → organizations aliye-assigniwa
            # Assuming Organization has a relation to staff via users or managers
            return Organization.objects.filter(users=user)

        # Default → no access
        return Organization.objects.none()



class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')

# -------------------
# BRANCH VIEWS
# -------------------

class BranchListView(LoginRequiredMixin, ListView):
    model = Branch
    template_name = "organizations/branch_list.html"
    context_object_name = "branches"

    def get_queryset(self):
        user = self.request.user

        # 👇 OWNER anaona branches za restaurant aliyepo assigned tu
        if hasattr(user, 'restaurant') and user.restaurant and user.user_type == "OWNER":
            return Branch.objects.filter(restaurant=user.restaurant).order_by('name')

        # Staff (MANAGER, CHEF, CASHIER, WAITER) → branches zao pekee
        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            if hasattr(user, 'restaurant') and user.restaurant:
                return Branch.objects.filter(restaurant=user.restaurant).order_by('name')
            return Branch.objects.none()

        # CUSTOMER → branches active tu
        elif user.user_type == "CUSTOMER":
            return Branch.objects.filter(restaurant__is_active=True).order_by('restaurant__name', 'name')

        return Branch.objects.none()



class BranchCreateView(LoginRequiredMixin, CreateView):
    model = Branch
    fields = ['restaurant', 'name', 'location', 'phone']
    template_name = "organizations/branch_form.html"
    success_url = reverse_lazy('organizations:branch_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in ['OWNER', 'MANAGER']:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ✅ Restrict restaurants to user's assigned one
        if hasattr(user, 'restaurant') and user.restaurant:
            context['restaurants'] = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            context['restaurants'] = Restaurant.objects.none()

        context['manager_label'] = 'Owner' if user.user_type == 'OWNER' else 'Manager'
        context['manager_value'] = user.username
        return context

    def form_valid(self, form):
        user = self.request.user

        # Assign manager (creator) and ensure branch is for assigned restaurant
        if hasattr(user, 'restaurant') and user.restaurant:
            form.instance.restaurant = user.restaurant
            form.instance.manager = user
        else:
            form.add_error('restaurant', 'You do not have an assigned restaurant.')
            return self.form_invalid(form)

        return super().form_valid(form)


class BranchUpdateView(LoginRequiredMixin, UpdateView):
    model = Branch
    fields = ['restaurant', 'name', 'location', 'phone']
    template_name = "organizations/branch_form.html"
    success_url = reverse_lazy('organizations:branch_list')

    def get_queryset(self):
        user = self.request.user

        if user.user_type == "OWNER":
            # Owner → branches of restaurants they own
            return Branch.objects.filter(restaurant__owner=user)

        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            # Staff → branches of their assigned restaurant
            return Branch.objects.filter(restaurant=user.restaurant)

        return Branch.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Show restaurants the user can actually select
        if user.user_type == "OWNER":
            context['restaurants'] = Restaurant.objects.filter(owner=user)
        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            context['restaurants'] = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            context['restaurants'] = Restaurant.objects.none()

        return context


class BranchDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Branch
    template_name = "organizations/branch_confirm_delete.html"
    success_url = reverse_lazy('organizations:branch_list')

    # Hakikisha tu owner au manager anaweza delete
    def test_func(self):
        user = self.request.user
        branch = self.get_object()
        return user.user_type in ['OWNER', 'MANAGER'] and (
            branch.manager == user or user.user_type == 'OWNER'
        )

# -------------------
# ASSIGN USERS TO RESTAURANT
# -------------------



# class AssignUsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
#     template_name = "organizations/assign_users.html"

#     def test_func(self):
#         restaurant_id = self.kwargs.get('pk')
#         restaurant = Restaurant.objects.get(id=restaurant_id)
#         return self.request.user == restaurant.owner

#     def handle_no_permission(self):
#         raise PermissionDenied("You cannot assign users to this restaurant.")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         restaurant_id = self.kwargs.get('pk')
#         restaurant = Restaurant.objects.get(id=restaurant_id)
#         context['restaurant'] = restaurant
#         context['users'] = User.objects.filter(
#             user_type__in=['MANAGER', 'CHEF', 'CASHIER', 'WAITER']
#         ).exclude(restaurant__isnull=False)  # users already assigned are excluded
#         return context

#     def post(self, request, *args, **kwargs):
#         restaurant_id = self.kwargs.get('pk')
#         restaurant = Restaurant.objects.get(id=restaurant_id)

#         user_ids = request.POST.getlist('users')  # from <select multiple>
#         # Remove old users from this restaurant
#         User.objects.filter(restaurant=restaurant).update(restaurant=None)
#         # Assign selected users to this restaurant
#         User.objects.filter(id__in=user_ids).update(restaurant=restaurant)

#         return redirect('organizations:restaurant_list')

