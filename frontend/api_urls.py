from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.api_dashboard_overview, name='api_dashboard_overview'),
]
