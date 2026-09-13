from django.urls import path
from . import views

# REST API URLs
urlpatterns = [
    path('<int:pk>/', views.api_scan_detail, name='api_scan_detail'),
    path('<int:pk>/dependencies/', views.api_scan_dependencies, name='api_scan_dependencies'),
    path('<int:pk>/vulnerabilities/', views.api_scan_vulnerabilities, name='api_scan_vulnerabilities'),
    path('<int:pk>/licenses/', views.api_scan_licenses, name='api_scan_licenses'),
    path('<int:pk>/report/', views.api_scan_report, name='api_scan_report'),
    # Scan start is under /api/projects/{id}/scan/
]
