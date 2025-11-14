from django.views.generic import ListView, View, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, FloatField
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from inventory.models import Sale, StockItem,SaleItem
from organizations.models import Restaurant
from payments.models import Expenditure
from reports.models import Feedback
from django.db.models import Q
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

        # Get restaurants visible to this user
        if user.user_type == "OWNER":
            restaurants = Restaurant.objects.filter(Q(owner=user) | Q(users=user)).distinct()
        elif user.user_type == "MANAGER" and hasattr(user, "restaurant") and user.restaurant:
            restaurants = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            return []

        filter_type = self.request.GET.get('filter', 'all')
        restaurant_id = self.request.GET.get('restaurant')
        today = timezone.now().date()

        if filter_type == 'daily':
            start_date = today
        elif filter_type == 'weekly':
            start_date = today - timedelta(days=7)
        elif filter_type == 'monthly':
            start_date = today - timedelta(days=30)
        else:
            start_date = None  # all time

        # Filter selected restaurant
        if restaurant_id:
            restaurants = restaurants.filter(id=restaurant_id)

        report_list = []

        for restaurant in restaurants.distinct():
            # Revenue
            sales = Sale.objects.filter(restaurant=restaurant)
            if start_date:
                sales = sales.filter(created_at__date__gte=start_date)
            revenue = sales.aggregate(total_revenue=Sum('total_amount', output_field=FloatField()))['total_revenue'] or 0

            # Revenue per product
            sale_items = SaleItem.objects.filter(sale__in=sales)
            revenue_per_product = sale_items.values('item__name').annotate(
                total=Sum('line_total', output_field=FloatField())
            ).order_by('-total')

            # Expenditure
            expenditures = Expenditure.objects.filter(restaurant=restaurant)
            if start_date:
                expenditures = expenditures.filter(date__gte=start_date)
            total_expenditure = expenditures.aggregate(total=Sum('amount', output_field=FloatField()))['total'] or 0

            # Profit
            profit = revenue - total_expenditure

            # Inventory
            inventory_items = StockItem.objects.filter(restaurant=restaurant)
            low_stock_items = inventory_items.filter(quantity__lte=5)
            in_stock_items = inventory_items.filter(quantity__gt=5)

            # Append report
            report_list.append({
                "restaurant": restaurant.name,
                "title": f"Financial Report - {restaurant.name}",
                "content": [
                    {"title": "Revenue", "value": f"TZS{revenue:.2f}"},
                    {"title": "Expenditure", "value": f"TZS{total_expenditure:.2f}"},
                    {"title": "Profit", "value": f"TZS{profit:.2f}"},
                    {"title": "Revenue Per Product", "value": list(revenue_per_product)},
                    {"title": "Low Stock Items", "value": list(low_stock_items.values('name','quantity'))},
                    {"title": "In Stock Items", "value": list(in_stock_items.values('name','quantity'))},
                ]
            })

        return report_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Restaurants for dropdown
        if user.user_type == "OWNER":
            context['restaurants'] = Restaurant.objects.filter(Q(owner=user) | Q(users=user)).distinct()
        elif user.user_type == "MANAGER" and hasattr(user, "restaurant") and user.restaurant:
            context['restaurants'] = Restaurant.objects.filter(id=user.restaurant.id)
        else:
            context['restaurants'] = Restaurant.objects.none()

        context['filter'] = self.request.GET.get('filter', 'all')
        context['selected_restaurant'] = self.request.GET.get('restaurant', None)
        context['date_filters'] = [
            ('all','All Time'),
            ('daily','Today'),
            ('weekly','Last 7 Days'),
            ('monthly','Last 30 Days')
        ]
        return context

class ReportDownloadPDF(View):
    def get(self, request, *args, **kwargs):
        # Reuse the ReportListView logic
        report_view = ReportListView()
        report_view.request = request
        reports = report_view.get_queryset()

        template_path = 'reports/report_pdf.html'
        context = {
            'reports': reports,
            'filter': request.GET.get('filter', 'all')
        }

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

