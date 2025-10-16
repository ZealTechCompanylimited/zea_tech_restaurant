from django.views.generic import TemplateView, View
from django.shortcuts import render, get_object_or_404, redirect
# from django.http import JsonResponse
# from django.contrib import messages
from .models import SubscriptionPlan
from payments.models import Payment
from payments.services import AzamPayService

from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required







class ChoosePlanView(TemplateView):
    template_name = "subscriptions/choose_plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.all()
        return context


@method_decorator(login_required, name="dispatch")
class InitiateSubscriptionPaymentView(View):
    def post(self, request, plan_key):
        plan = get_object_or_404(SubscriptionPlan, key__iexact=plan_key)
        phone = request.POST.get("phone_number", "255620280809")

        service = AzamPayService()
        response = service.initiate_payment(order=None, amount=plan.price, phone_number=phone)

        if "error" in response:
            # Payment failed
            return render(request, "subscriptions/payment_failed.html")

        # Payment pending, save record
        Payment.objects.create(
            order=None,
            customer=request.user,
            amount=plan.price,
            status="PENDING",
            transaction_id=response.get("transactionId"),
            reference=response.get("reference"),
            plan_key=plan.key
        )

        # Payment initiated successfully
        return render(request, "subscriptions/payment_success.html")


class PaymentSuccessView(View):
    def get(self, request):
        return render(request, "subscriptions/payment_success.html")


class PaymentFailedView(View):
    def get(self, request):
        return render(request, "subscriptions/payment_failed.html")
