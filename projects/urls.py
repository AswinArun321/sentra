from django.urls import path
from . import views

# REST API
urlpatterns = [
    path('', views.project_list_create, name='api_project_list'),
    path('<int:pk>/', views.project_detail, name='api_project_detail'),
]
