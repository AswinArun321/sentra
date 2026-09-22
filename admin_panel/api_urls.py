from django.urls import path
from admin_panel import api_views

urlpatterns = [
    path('dashboard/', api_views.AdminDashboardApiView.as_view(), name='api_admin_dashboard'),
    path('users/', api_views.AdminUserListApiView.as_view(), name='api_admin_users'),
    path('users/<int:user_id>/', api_views.AdminUserDetailApiView.as_view(), name='api_admin_user_detail'),
    path('users/<int:user_id>/<str:action>/', api_views.AdminUserActionApiView.as_view(), name='api_admin_user_action'),
    path('projects/', api_views.AdminProjectListApiView.as_view(), name='api_admin_projects'),
    path('scans/', api_views.AdminScanListApiView.as_view(), name='api_admin_scans'),
    path('vulnerabilities/', api_views.AdminVulnerabilityListApiView.as_view(), name='api_admin_vulnerabilities'),
    path('dependencies/', api_views.AdminDependencyListApiView.as_view(), name='api_admin_dependencies'),
    path('licenses/', api_views.AdminLicenseListApiView.as_view(), name='api_admin_licenses'),
    path('reports/', api_views.AdminReportListApiView.as_view(), name='api_admin_reports'),
    path('github/', api_views.AdminGitHubConnectionApiView.as_view(), name='api_admin_github'),
    path('github/<int:connection_id>/disconnect/', api_views.AdminGitHubConnectionApiView.as_view(), name='api_admin_github_disconnect'),
    path('audit-logs/', api_views.AdminAuditLogListApiView.as_view(), name='api_admin_audit_logs'),
    path('system/', api_views.AdminSystemHealthApiView.as_view(), name='api_admin_system_health'),
    path('settings/', api_views.AdminSettingsApiView.as_view(), name='api_admin_settings'),
]
