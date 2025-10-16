from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
        # Return all restaurants in the system
        return Restaurant.objects.all().order_by('name')

class RestaurantCreateView(LoginRequiredMixin, CreateView):
    model = Restaurant
    fields = ['name', 'code', 'address', 'phone', 'timezone', 'is_active']
    template_name = 'organizations/restaurant_form.html'
    success_url = reverse_lazy('organizations:restaurant_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class RestaurantUpdateView(LoginRequiredMixin, UpdateView):
    model = Restaurant
    fields = ['name', 'code', 'address', 'phone', 'timezone', 'is_active']
    template_name = 'organizations/restaurant_form.html'
    success_url = reverse_lazy('organizations:restaurant_list')

    def get_queryset(self):
        user = self.request.user
        # Owner/Manager update restaurants zao tu
        if user.user_type == 'OWNER':
            return Restaurant.objects.filter(owner=user)
        elif user.user_type == 'MANAGER':
            return Restaurant.objects.filter(users=user)
        return Restaurant.objects.none()
    
    


class RestaurantUpdateView(LoginRequiredMixin, UpdateView):
    model = Restaurant
    fields = ['name', 'code', 'address', 'phone', 'organization', 'is_active']
    template_name = 'organizations/restaurant_form.html'
    success_url = reverse_lazy('organizations:restaurant_list')

    def form_valid(self, form):
        # Automatically set the owner if not set
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Optional: Limit organizations if needed
        form.fields['organization'].queryset = Organization.objects.all()
        return form


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





# class OrganizationListView(LoginRequiredMixin, ListView):
#     model = Organization
#     template_name = "organizations/organization_list.html"
#     context_object_name = "organizations"

#     def get_queryset(self):
#         user = self.request.user
#         # Return organizations where user is Owner OR Manager
#         return Organization.objects.filter(
#             Q(created_by=user) | Q(managers=user)
#         ).distinct()



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

        if user.user_type == "OWNER":
            # Owner → aone branches zote za restaurants zake pamoja na branches zote system-wide
            return Branch.objects.all().order_by('restaurant__name', 'name')

        elif user.user_type in ["MANAGER", "CHEF", "CASHIER", "WAITER"]:
            # Staff → aone branches walizo assigniwa
            return Branch.objects.filter(manager=user).order_by('restaurant__name', 'name')

        elif user.user_type == "CUSTOMER":
            # Customers → optional: active branches tu
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

    def form_valid(self, form):
        form.instance.manager = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.all()  # all restaurants
        context['manager_label'] = 'Owner' if self.request.user.user_type == 'OWNER' else 'Manager'
        context['manager_value'] = self.request.user.username
        return context

class BranchUpdateView(LoginRequiredMixin, UpdateView):
    model = Branch
    fields = ['restaurant', 'name', 'location', 'phone']
    template_name = "organizations/branch_form.html"
    success_url = reverse_lazy('organizations:branch_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Rudisha restaurants zote kwenye system
        context['restaurants'] = Restaurant.objects.all()
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

