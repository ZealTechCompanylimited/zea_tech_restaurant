from django.urls import path
from .views import (
    ReservationListView,
    ReservationCreateView,
    ReservationUpdateView,
    ReservationDeleteView,
)

app_name = "reservations"

urlpatterns = [
    path('reservation_list', ReservationListView.as_view(), name='list'),
    path('add/', ReservationCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', ReservationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ReservationDeleteView.as_view(), name='delete'),
]
