from django.urls import path
from .views import (
    OrganizationListView, OrganizationCreateView, OrganizationUpdateView, OrganizationDeleteView,
    RestaurantListView, RestaurantCreateView, RestaurantUpdateView, RestaurantDeleteView,BranchListView, BranchCreateView, BranchUpdateView, BranchDeleteView
)

app_name = 'organizations'

urlpatterns = [
    # Organization URLs
    path('organization-list', OrganizationListView.as_view(), name='list'),
    path('add/', OrganizationCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', OrganizationUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', OrganizationDeleteView.as_view(), name='delete'),

    # Restaurant URLs
    path('restaurants/', RestaurantListView.as_view(), name='restaurant_list'),
    path('restaurants/add/', RestaurantCreateView.as_view(), name='restaurant_add'),
    path('restaurants/edit/<int:pk>/', RestaurantUpdateView.as_view(), name='restaurant_edit'),
    path('restaurants/delete/<int:pk>/', RestaurantDeleteView.as_view(), name='restaurant_delete'),
    
    path('branches/', BranchListView.as_view(), name='branch_list'),
    path('branches/add/', BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/edit/', BranchUpdateView.as_view(), name='branch_update'),
    path('branches/<int:pk>/delete/', BranchDeleteView.as_view(), name='branch_delete'),
    
    # path(
    #     'restaurants/<int:pk>/assign-users/',
    #     AssignUsersView.as_view(),
    #     name='assign_users'
    # ),
]
