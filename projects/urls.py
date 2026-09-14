from django.urls import path
from . import views

# REST API
urlpatterns = [
    path('', views.project_list_create, name='api_project_list'),
    path('<int:pk>/', views.project_detail, name='api_project_detail'),
    path('<int:pk>/analysis-status/', views.api_project_analysis_status, name='api_project_analysis_status'),
    path('<int:pk>/refresh-analysis/', views.api_project_refresh_analysis, name='api_project_refresh_analysis'),
]
