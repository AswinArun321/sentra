from django.urls import path
from admin_panel import views

urlpatterns = [
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', views.admin_users_view, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('projects/', views.admin_projects_view, name='admin_projects'),
    path('scans/', views.admin_scans_view, name='admin_scans'),
    path('vulnerabilities/', views.admin_vulnerabilities_view, name='admin_vulnerabilities'),
    path('dependencies/', views.admin_dependencies_view, name='admin_dependencies'),
    path('licenses/', views.admin_licenses_view, name='admin_licenses'),
    path('reports/', views.admin_reports_view, name='admin_reports'),
    path('reports/<int:scan_id>/download/', views.admin_download_report_view, {'report_format': 'json'}, name='admin_download_report'),
    path('reports/<int:scan_id>/download-sbom/', views.admin_download_report_view, {'report_format': 'sbom'}, name='admin_download_sbom'),
    path('github/', views.admin_github_view, name='admin_github'),
    path('audit-logs/', views.admin_audit_logs_view, name='admin_audit_logs'),
    path('system/', views.admin_system_health_view, name='admin_system_health'),
    path('settings/', views.admin_settings_view, name='admin_settings'),
]
