from django.urls import path
from . import views

# Frontend template URL patterns
urlpatterns = [
    path('project/<int:project_pk>/upload/', views.scan_upload_view, name='scan_upload'),
    path('<int:pk>/', views.scan_detail_view, name='scan_detail'),
    path('project/<int:project_pk>/history/', views.scan_history_view, name='scan_history'),
]
