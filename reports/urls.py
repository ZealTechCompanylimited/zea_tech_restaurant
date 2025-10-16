from django.urls import path
from .views import ReportListView,ReportDownloadPDF,FeedbackCreateView, FeedbackListView
from django.views.generic import TemplateView

app_name = 'reports'

urlpatterns = [
    path('reports-list/', ReportListView.as_view(), name='list'),
    path('reports-download/', ReportDownloadPDF.as_view(), name='download'),
    
    path('feedback/submit/', FeedbackCreateView.as_view(), name='feedback_submit'),
    path('feedback/list/', FeedbackListView.as_view(), name='feedback_list'),
    path('feedback/thanks/', TemplateView.as_view(template_name='reports/feedback_thanks.html'), name='feedback_thanks')


]
