from django.views.generic import ListView, View, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F, FloatField
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from orders.models import OrderItem
from inventory.models import PurchaseItem, StockItem
from organizations.models import Restaurant
from reports.models import Feedback
from subscriptions.mixins import PlanRequiredMixin
# from subscriptions.decorators import plan_required_for_app
# from django.utils.decorators import method_decorator
  # au view nyingine ya CBV
# @method_decorator(plan_required_for_app("reports"), name='dispatch')
class ReportListView(PlanRequiredMixin, ListView):
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    app_name = "reports"

    def get_queryset(self):
        user = self.request.user
        restaurant = getattr(user, 'restaurant', None)
        if not restaurant:
            return []

        filter_type = self.request.GET.get('filter', 'all')
        today = timezone.now().date()

        if filter_type == 'daily':
            start_date = today
        elif filter_type == 'weekly':
            start_date = today - timedelta(days=7)
        elif filter_type == 'monthly':
            start_date = today - timedelta(days=30)
        else:
            start_date = None

        # Orders & Revenue
        order_items = OrderItem.objects.filter(order__restaurant=restaurant)
        if start_date:
            order_items = order_items.filter(order__created_at__date__gte=start_date)

        revenue = order_items.aggregate(
            total_revenue=Sum(F('unit_price') * F('quantity'), output_field=FloatField())
        )['total_revenue'] or 0

        # Revenue per product
        revenue_per_product = order_items.values('item__name').annotate(
            total=Sum(F('unit_price') * F('quantity'), output_field=FloatField())
        ).order_by('-total')

        # Revenue per category
        revenue_per_category = order_items.values('item__category__name').annotate(
            total=Sum(F('unit_price') * F('quantity'), output_field=FloatField())
        ).order_by('-total')

        # Cost / Expenses
        purchase_items = PurchaseItem.objects.filter(purchase__restaurant=restaurant)
        if start_date:
            purchase_items = purchase_items.filter(purchase__created_at__date__gte=start_date)

        total_cost = purchase_items.aggregate(
            total_cost=Sum(F('line_total'), output_field=FloatField())
        )['total_cost'] or 0

        # Profit
        profit = revenue - total_cost

        # Top Selling Items
        top_selling = order_items.values('item__name').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')[:5]

        # Inventory Status
        inventory_items = StockItem.objects.filter(restaurant=restaurant)
        low_stock_items = inventory_items.filter(quantity__lte=5)
        in_stock_items = inventory_items.filter(quantity__gt=5)

        # Build report list
        report_list = [
            {"title": "Revenue", "content": f"${revenue:.2f}"},
            {"title": "Cost", "content": f"${total_cost:.2f}"},
            {"title": "Profit", "content": f"${profit:.2f}"},
            {"title": "Revenue Per Product", "content": list(revenue_per_product)},
            {"title": "Revenue Per Category", "content": list(revenue_per_category)},
            {"title": "Top Selling Items", "content": list(top_selling)},
            {"title": "Low Stock Items", "content": list(low_stock_items.values('name','quantity'))},
            {"title": "In Stock Items", "content": list(in_stock_items.values('name','quantity'))},
        ]

        return report_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', 'all')
        return context


class ReportDownloadPDF(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        restaurant = getattr(user, 'restaurant', None)
        if not restaurant:
            return HttpResponse("No restaurant assigned.", status=400)

        # Reuse ReportListView logic
        report_view = ReportListView()
        report_view.request = request
        reports = report_view.get_queryset()

        template_path = 'reports/report_pdf.html'
        context = {'reports': reports, 'filter': request.GET.get('filter', 'all')}

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reports.pdf"'

        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response




class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    template_name = 'reports/feedback_form.html'
    fields = ['category', 'message', 'customer_name', 'email', 'restaurant']
    success_url = reverse_lazy('reports:feedback_thanks')

    def form_valid(self, form):
        # Usibadilishe restaurant, iache ichaguliwe na user kupitia form
        form.instance.submitted_by = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Onyesha restaurants zote
        form.fields['restaurant'].queryset = Restaurant.objects.all()
        return form




class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'reports/feedback_list.html'
    context_object_name = 'feedbacks'

    def get_queryset(self):
        user = self.request.user

        if user.user_type == "CUSTOMER":
            # Customer sees only feedbacks they submitted
            return Feedback.objects.filter(submitted_by=user).order_by('-created_at')

        elif user.user_type == "OWNER":
            # Owner sees all feedbacks
            return Feedback.objects.all().order_by('-created_at')

        else:
            # Staff (MANAGER, CHEF, CASHIER, WAITER) see feedback only for their assigned restaurants
            assigned_restaurants = getattr(user, 'restaurants', None)
            if assigned_restaurants:
                return Feedback.objects.filter(restaurant__in=user.restaurants.all()).order_by('-created_at')
            return Feedback.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass a flag so template can show/hide "Create Feedback" button
        context['show_create_button'] = self.request.user.user_type == "CUSTOMER"
        return context

