from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("choose/", views.ChoosePlanView.as_view(), name="choose_plan"),
    path("initiate/<str:plan_key>/", views.InitiateSubscriptionPaymentView.as_view(), name="initiate_subscription_payment"),
    path("success/", views.PaymentSuccessView.as_view(), name="payment_success"),
    path("failed/", views.PaymentFailedView.as_view(), name="payment_failed"),

]
