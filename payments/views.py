from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, HttpResponse
# from django.contrib.auth import get_user_model
from orders.models import Order
from .models import Payment,Expenditure
from .services import AzamPayService
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
from django.views.generic import DetailView
from .forms import PaymentForm
from django.conf import settings
from django.urls import reverse
import logging
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from datetime import date
from django.db.models import Sum



# User = get_user_model()
User = settings.AUTH_USER_MODEL 
logger = logging.getLogger(__name__)


class InitiatePaymentView(View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        phone_number = request.POST.get("phone_number") or getattr(order, "guest_phone", None) or "255620280809"

        user = getattr(order, "customer", None) or getattr(order, "created_by", None)
        if not user:
            user, _ = User.objects.get_or_create(
                username="guest_user",
                defaults={"email": "guest@example.com", "password": User.objects.make_random_password()}
            )

        service = AzamPayService()
        response = service.initiate_payment(order=order, amount=order.grand_total, phone_number=phone_number)

        if "error" in response:
            logger.error(f"Payment initiation failed: {response['error']}")
            return JsonResponse({"message": "Payment initiation failed", "error": response["error"]}, status=400)

        Payment.objects.create(
            order=order,
            customer=user,
            amount=order.grand_total,
            status="PENDING",
            transaction_id=response.get("transactionId"),
            reference=response.get("reference"),
        )

        return JsonResponse({"message": "Payment initiated", "data": response})


@method_decorator(csrf_exempt, name="dispatch")
class PaymentCallbackView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            order_id = data.get("externalId") or data.get("orderReference")
            status = data.get("status")
            transaction_id = data.get("transactionId")

            if not order_id:
                return HttpResponse("Missing orderReference", status=400)

            order = get_object_or_404(Order, pk=order_id)
            payment = Payment.objects.filter(order=order).order_by('-id').first()

            if not payment:
                return HttpResponse("No payment found", status=404)

            if status and status.upper() == "SUCCESS":
                payment.status = "SUCCESS"
                order.status = "PAID"
            else:
                payment.status = "FAILED"
                order.status = "FAILED"

            payment.transaction_id = transaction_id
            payment.save()
            order.save()
            return HttpResponse("OK")
        except Exception as e:
            logger.error(f"Callback error: {e}")
            return HttpResponse("Callback error", status=400)
        
        
        



class PaymentFormView(DetailView):
    model = Order
    template_name = "payments/payment_form.html"
    context_object_name = "order"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PaymentForm(request.POST)

        if form.is_valid():
            phone_number = form.cleaned_data["phone_number"]
            amount = form.cleaned_data["amount"]

            service = AzamPayService()
            resp = service.initiate_payment(self.object, amount, phone_number, provider="Airtel")

            # Log response for debugging
            logger.info(f"AzamPay response: {resp}")

            # Extract transactionId and reference safely
            transaction_id = None
            reference = None

            if "data" in resp:
                transaction_id = resp["data"].get("transactionId")
                reference = resp["data"].get("messageCode")
            else:
                # fallback if no 'data' key (sandbox/live may vary)
                transaction_id = resp.get("transactionId")
                reference = resp.get("messageCode")

            if "error" in resp or not transaction_id:
                # Payment initiation failed
                error_message = resp.get("error") or resp.get("message") or "Payment initiation failed"
                return render(request, "payments/payment_failed.html", {"error": error_message})

            # Save payment
            Payment.objects.create(
                order=self.object,
                customer=getattr(self.object, "customer", None),
                amount=amount,
                status="PENDING",
                transaction_id=transaction_id,
                reference=reference,
            )

            return redirect(reverse("payments:payment_success"))

        # Form invalid
        return render(request, self.template_name, {"order": self.object, "form": form})



class PaymentSuccessView(View):
    def get(self, request):
        return render(request, "payments/payment_success.html")

class PaymentFailedView(View):
    def get(self, request):
        return render(request, "payments/payment_failed.html")






class ExpenditureListView(LoginRequiredMixin, ListView):
    template_name = "payments/expenditure_list.html"
    context_object_name = "expenditures"

    def get_queryset(self):
        qs = Expenditure.objects.filter(restaurant=self.request.user.restaurant).order_by('-date')

        filter_type = self.request.GET.get('filter_type', 'today')
        if filter_type == 'today':
            qs = qs.filter(date=date.today())
        elif filter_type == 'month':
            month = self.request.GET.get('month')
            if month:
                qs = qs.filter(date__month=int(month))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Total expenditure for current filter
        context["total_amount"] = sum(e.amount for e in context["expenditures"])

        # Months for dropdown
        context["months"] = [
            (1, "January"), (2, "February"), (3, "March"), (4, "April"),
            (5, "May"), (6, "June"), (7, "July"), (8, "August"),
            (9, "September"), (10, "October"), (11, "November"), (12, "December")
        ]
        return context



class ExpenditureCreateView(LoginRequiredMixin, CreateView):
    model = Expenditure
    fields = ["title", "amount"]
    template_name = "payments/expenditure_form.html"
    success_url = reverse_lazy("payments:explist")

    def form_valid(self, form):
        form.instance.restaurant = self.request.user.restaurant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

