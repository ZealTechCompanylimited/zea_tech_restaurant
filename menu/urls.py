from django.urls import path
from .views import (
    MenuListView,
    ItemDetailView,
    ItemCreateView,
    ItemUpdateView,
    ItemDeleteView,
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    CustomerRestaurantListView,
    MenuItemsByRestaurantView
)

app_name = 'menu'

urlpatterns = [
    # --- Menu Items ---
    path('menu-list/', MenuListView.as_view(), name='menu_list'),
    path('menu/add/', ItemCreateView.as_view(), name='item_add'),
    path('menu/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),
    path('menu/<int:pk>/edit/', ItemUpdateView.as_view(), name='item_edit'),
    path('menu/<int:pk>/delete/', ItemDeleteView.as_view(), name='item_delete'),
    path('customer_restaurants/', CustomerRestaurantListView.as_view(), name='customer_restaurants'),
    path('restaurants/<int:restaurant_id>/menu/', MenuItemsByRestaurantView.as_view(), name='menu_by_restaurant'),


    # --- Categories ---
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/add/', CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]
