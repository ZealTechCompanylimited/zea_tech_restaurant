
from django.urls import path
from .views import (
    InitiatePaymentView,
    PaymentCallbackView,
    PaymentSuccessView,
    PaymentFailedView,
    PaymentFormView,
    ExpenditureListView,
    ExpenditureCreateView,
)
app_name = "payments"

urlpatterns = [
    path("pay/<int:pk>/", PaymentFormView.as_view(), name="payment_form"),
    path("initiate/<int:order_id>/", InitiatePaymentView.as_view(), name="initiate_payment"),
    path("callback/", PaymentCallbackView.as_view(), name="payment_callback"),
    path("success/", PaymentSuccessView.as_view(), name="payment_success"),
    path("failed/", PaymentFailedView.as_view(), name="payment_failed"),
    path("explist", ExpenditureListView.as_view(), name="explist"),
    path("expcreate/", ExpenditureCreateView.as_view(), name="expcreate"),
]
