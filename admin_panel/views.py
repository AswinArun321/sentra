import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q

from admin_panel.permissions import admin_required
from admin_panel.models import AdminAuditLog, PlatformSetting, UserAccountStatus
from admin_panel.services import (
    AdminAuditService,
    AdminUserService,
    AdminDashboardService,
    AdminSystemHealthService,
)
from admin_panel.filters import (
    paginate_queryset,
    filter_users,
    filter_projects,
    filter_scans,
    filter_vulnerabilities,
    filter_audit_logs,
)
from projects.models import Project
from scans.models import Scan
from dependencies.models import Dependency
from vulnerabilities.models import Vulnerability
from reports.models import Report
from reports.generators import generate_json_report, generate_cyclonedx_sbom
from github_integration.models import GitHubConnection

User = get_user_model()


@admin_required
def admin_dashboard_view(request):
    metrics = AdminDashboardService.get_overview_metrics()
    chart_data = AdminDashboardService.get_chart_series()

    recent_users = User.objects.all().select_related('admin_status', 'github_connection').order_by('-date_joined')[:6]
    recent_scans = Scan.objects.all().select_related('project', 'project__owner').order_by('-created_at')[:6]
    recent_audit_logs = AdminAuditLog.objects.all().select_related('admin_user', 'target_user').order_by('-created_at')[:8]

    context = {
        'page_title': 'Platform Overview',
        'metrics': metrics,
        'chart_data_json': json.dumps(chart_data),
        'recent_users': recent_users,
        'recent_scans': recent_scans,
        'recent_audit_logs': recent_audit_logs,
        'active_tab': 'overview',
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_users_view(request):
    users_qs = filter_users(request)
    users_page = paginate_queryset(request, users_qs, page_size=20)

    context = {
        'page_title': 'User Management',
        'users_page': users_page,
        'total_users_count': User.objects.count(),
        'query_params': request.GET.dict(),
        'active_tab': 'users',
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    target_user = get_object_or_404(
        User.objects.select_related('github_connection', 'admin_status'),
        pk=user_id
    )

    user_status = AdminUserService.get_status_info(target_user)
    user_projects = Project.objects.filter(owner=target_user).prefetch_related('scans').order_by('-updated_at')
    user_scans = Scan.objects.filter(project__owner=target_user).select_related('project').order_by('-created_at')[:10]

    # Vulnerability breakdown for user's scans
    vuln_stats = Vulnerability.objects.filter(
        dependency__scan__project__owner=target_user
    ).aggregate(
        total=Count('id'),
        critical=Count('id', filter=Q(severity='CRITICAL')),
        high=Count('id', filter=Q(severity='HIGH')),
        medium=Count('id', filter=Q(severity='MEDIUM')),
        low=Count('id', filter=Q(severity='LOW')),
    )

    user_audit_logs = AdminAuditLog.objects.filter(
        Q(target_user=target_user) | Q(admin_user=target_user)
    ).select_related('admin_user', 'target_user').order_by('-created_at')[:15]

    context = {
        'page_title': f"User: {target_user.username}",
        'target_user': target_user,
        'user_status': user_status,
        'user_projects': user_projects,
        'user_scans': user_scans,
        'vuln_stats': vuln_stats,
        'user_audit_logs': user_audit_logs,
        'active_tab': 'users',
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def admin_projects_view(request):
    projects_qs = filter_projects(request)
    projects_page = paginate_queryset(request, projects_qs, page_size=20)

    context = {
        'page_title': 'Project Repositories',
        'projects_page': projects_page,
        'total_projects_count': Project.objects.count(),
        'query_params': request.GET.dict(),
        'active_tab': 'projects',
    }
    return render(request, 'admin_panel/projects.html', context)


@admin_required
def admin_scans_view(request):
    scans_qs = filter_scans(request)
    scans_page = paginate_queryset(request, scans_qs, page_size=20)

    metrics = Scan.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='COMPLETED')),
        running=Count('id', filter=Q(status='RUNNING')),
        failed=Count('id', filter=Q(status='FAILED')),
        pending=Count('id', filter=Q(status='PENDING')),
    )

    context = {
        'page_title': 'Scan Monitoring',
        'scans_page': scans_page,
        'metrics': metrics,
        'query_params': request.GET.dict(),
        'active_tab': 'scans',
    }
    return render(request, 'admin_panel/scans.html', context)


@admin_required
def admin_vulnerabilities_view(request):
    vulns_qs = filter_vulnerabilities(request)
    vulns_page = paginate_queryset(request, vulns_qs, page_size=25)

    severity_counts = Vulnerability.objects.aggregate(
        total=Count('id'),
        critical=Count('id', filter=Q(severity='CRITICAL')),
        high=Count('id', filter=Q(severity='HIGH')),
        medium=Count('id', filter=Q(severity='MEDIUM')),
        low=Count('id', filter=Q(severity='LOW')),
    )

    context = {
        'page_title': 'Security Vulnerabilities',
        'vulns_page': vulns_page,
        'severity_counts': severity_counts,
        'query_params': request.GET.dict(),
        'active_tab': 'vulnerabilities',
    }
    return render(request, 'admin_panel/vulnerabilities.html', context)


@admin_required
def admin_dependencies_view(request):
    search = request.GET.get('q', '').strip()
    ecosystem = request.GET.get('ecosystem', '').strip()

    deps_qs = Dependency.objects.all().select_related('scan__project__owner').order_by('-risk_score', 'name')
    if search:
        deps_qs = deps_qs.filter(Q(name__icontains=search) | Q(license__icontains=search))
    if ecosystem:
        deps_qs = deps_qs.filter(ecosystem__iexact=ecosystem)

    deps_page = paginate_queryset(request, deps_qs, page_size=25)

    # Top popular packages across all scans
    popular_packages = Dependency.objects.values('name', 'ecosystem')\
        .annotate(occurrences=Count('id'), vuln_count=Count('vulnerabilities'))\
        .order_by('-occurrences')[:10]

    context = {
        'page_title': 'Dependency Intelligence',
        'deps_page': deps_page,
        'popular_packages': popular_packages,
        'total_dependencies_count': Dependency.objects.count(),
        'query_params': request.GET.dict(),
        'active_tab': 'dependencies',
    }
    return render(request, 'admin_panel/dependencies.html', context)


@admin_required
def admin_licenses_view(request):
    licenses_qs = Dependency.objects.exclude(license__in=['', 'Unknown', 'UNKNOWN'])\
        .values('license', 'license_category')\
        .annotate(package_count=Count('id'))\
        .order_by('-package_count')

    unknown_count = Dependency.objects.filter(Q(license='') | Q(license__iexact='unknown')).count()
    total_packages = Dependency.objects.count()

    context = {
        'page_title': 'License Compliance',
        'licenses': licenses_qs[:50],
        'unknown_count': unknown_count,
        'total_packages': total_packages,
        'active_tab': 'licenses',
    }
    return render(request, 'admin_panel/licenses.html', context)


@admin_required
def admin_reports_view(request):
    reports_qs = Report.objects.all().select_related('scan__project__owner').order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        reports_qs = reports_qs.filter(
            Q(scan__project__name__icontains=search) |
            Q(scan__project__owner__username__icontains=search)
        )

    report_type = request.GET.get('type', '').strip()
    if report_type:
        reports_qs = reports_qs.filter(report_type=report_type)

    reports_page = paginate_queryset(request, reports_qs, page_size=25)

    context = {
        'page_title': 'Reports Management',
        'reports_page': reports_page,
        'total_reports_count': Report.objects.count(),
        'query_params': request.GET.dict(),
        'active_tab': 'reports',
    }
    return render(request, 'admin_panel/reports.html', context)


@admin_required
def admin_download_report_view(request, scan_id, report_format='json'):
    scan = get_object_or_404(Scan.objects.select_related('project', 'project__owner'), pk=scan_id)

    # Log report download in audit log
    AdminAuditService.log_action(
        admin_user=request.user,
        action='REPORT_DOWNLOADED',
        target_user=scan.project.owner,
        target_object_type='Scan',
        target_object_id=str(scan.id),
        description=f"Admin downloaded {report_format.upper()} report for Scan #{scan.id} (Project: {scan.project.name}).",
        request=request
    )

    if report_format == 'sbom':
        sbom_data = generate_cyclonedx_sbom(scan)
        response = HttpResponse(json.dumps(sbom_data, indent=2, default=str), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="admin-sbom-{scan.project.name}-scan-{scan.pk}.cdx.json"'
        return response
    else:
        report_data = generate_json_report(scan)
        response = HttpResponse(json.dumps(report_data, indent=2, default=str), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="admin-report-scan-{scan.pk}.json"'
        return response


@admin_required
def admin_github_view(request):
    """
    Shows GitHub connection monitoring. NEVER displays access tokens.
    """
    connections_qs = GitHubConnection.objects.all().select_related('user').order_by('-connected_at')
    search = request.GET.get('q', '').strip()
    if search:
        connections_qs = connections_qs.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(github_username__icontains=search)
        )

    connections_page = paginate_queryset(request, connections_qs, page_size=20)
    total_users_count = User.objects.count()
    connected_users_count = GitHubConnection.objects.count()

    context = {
        'page_title': 'GitHub Connections',
        'connections_page': connections_page,
        'connected_count': connected_users_count,
        'disconnected_count': max(0, total_users_count - connected_users_count),
        'query_params': request.GET.dict(),
        'active_tab': 'github',
    }
    return render(request, 'admin_panel/github.html', context)


@admin_required
def admin_audit_logs_view(request):
    logs_qs = filter_audit_logs(request)
    logs_page = paginate_queryset(request, logs_qs, page_size=30)

    actions = AdminAuditLog.objects.values_list('action', flat=True).distinct().order_by('action')

    context = {
        'page_title': 'Administrative Audit Logs',
        'logs_page': logs_page,
        'actions': actions,
        'query_params': request.GET.dict(),
        'active_tab': 'audit_logs',
    }
    return render(request, 'admin_panel/audit_logs.html', context)


@admin_required
def admin_system_health_view(request):
    health = AdminSystemHealthService.check_health()
    context = {
        'page_title': 'System Health & Telemetry',
        'health': health,
        'active_tab': 'system',
    }
    return render(request, 'admin_panel/system.html', context)


@admin_required
def admin_settings_view(request):
    defaults = {
        'platform_name': 'SENTRA',
        'maintenance_mode': 'False',
        'max_upload_size_mb': '5',
        'scan_timeout_seconds': '300',
        'report_retention_days': '90',
    }

    if request.method == 'POST':
        for key in defaults.keys():
            val = request.POST.get(key, '').strip()
            if val:
                PlatformSetting.set_value(key=key, value=val, updated_by=request.user)

        AdminAuditService.log_action(
            admin_user=request.user,
            action='SETTING_CHANGED',
            target_object_type='PlatformSetting',
            description="Updated platform runtime settings.",
            request=request
        )
        messages.success(request, "Platform settings updated successfully.")
        return redirect('admin_settings')

    current_settings = {}
    for key, default_val in defaults.items():
        current_settings[key] = PlatformSetting.get_value(key, default_val)

    context = {
        'page_title': 'Platform Settings',
        'settings': current_settings,
        'active_tab': 'settings',
    }
    return render(request, 'admin_panel/settings.html', context)
