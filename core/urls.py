from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import * 
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', HomeCreateView.as_view(), name='index'),
    
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    
    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



