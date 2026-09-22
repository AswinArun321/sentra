from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from admin_panel.permissions import IsSENTRAAdminUser
from admin_panel.models import AdminAuditLog, PlatformSetting, UserAccountStatus
from admin_panel.services import (
    AdminAuditService,
    AdminUserService,
    AdminDashboardService,
    AdminSystemHealthService,
)
from admin_panel.serializers import (
    AdminUserSerializer,
    AdminProjectSerializer,
    AdminScanSerializer,
    AdminVulnerabilitySerializer,
    AdminDependencySerializer,
    AdminReportSerializer,
    AdminGitHubConnectionSafeSerializer,
    AdminAuditLogSerializer,
    PlatformSettingSerializer,
)
from admin_panel.filters import (
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
from github_integration.models import GitHubConnection

User = get_user_model()


class AdminDashboardApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        metrics = AdminDashboardService.get_overview_metrics()
        charts = AdminDashboardService.get_chart_series()
        return Response({
            'metrics': metrics,
            'charts': charts,
        })


class AdminUserListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        users_qs = filter_users(request)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = users_qs.count()
        serializer = AdminUserSerializer(users_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminUserDetailApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User.objects.select_related('github_connection', 'admin_status'), pk=user_id)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)


class AdminUserActionApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def post(self, request, user_id, action):
        user = get_object_or_404(User, pk=user_id)
        action = action.lower()

        if action == 'activate':
            AdminUserService.set_status(request.user, user, 'ACTIVE', request=request)
            return Response({'status': 'ACTIVE', 'message': f'User {user.username} activated.'})

        elif action == 'deactivate':
            AdminUserService.set_status(request.user, user, 'INACTIVE', request=request)
            return Response({'status': 'INACTIVE', 'message': f'User {user.username} deactivated.'})

        elif action == 'suspend':
            reason = request.data.get('reason', '').strip()
            AdminUserService.set_status(request.user, user, 'SUSPENDED', reason=reason, request=request)
            return Response({'status': 'SUSPENDED', 'message': f'User {user.username} suspended.'})

        elif action == 'reactivate':
            AdminUserService.set_status(request.user, user, 'ACTIVE', request=request)
            return Response({'status': 'ACTIVE', 'message': f'User {user.username} reactivated.'})

        elif action == 'toggle-staff':
            make_staff = bool(request.data.get('is_staff', False))
            try:
                result = AdminUserService.toggle_staff(request.user, user, make_staff, request=request)
                return Response({'is_staff': result, 'message': f"Updated staff privilege for {user.username}."})
            except PermissionError as pe:
                return Response({'error': str(pe)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': f'Unsupported action: {action}'}, status=status.HTTP_400_BAD_REQUEST)


class AdminProjectListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        projects_qs = filter_projects(request)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = projects_qs.count()
        serializer = AdminProjectSerializer(projects_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminScanListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        scans_qs = filter_scans(request)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = scans_qs.count()
        serializer = AdminScanSerializer(scans_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminVulnerabilityListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        vulns_qs = filter_vulnerabilities(request)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        start = (page - 1) * page_size
        end = start + page_size

        total = vulns_qs.count()
        serializer = AdminVulnerabilitySerializer(vulns_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminDependencyListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        search = request.GET.get('q', '').strip()
        ecosystem = request.GET.get('ecosystem', '').strip()

        deps_qs = Dependency.objects.all().select_related('scan__project__owner').order_by('-risk_score', 'name')
        if search:
            deps_qs = deps_qs.filter(name__icontains=search)
        if ecosystem:
            deps_qs = deps_qs.filter(ecosystem__iexact=ecosystem)

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        start = (page - 1) * page_size
        end = start + page_size

        total = deps_qs.count()
        serializer = AdminDependencySerializer(deps_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminLicenseListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        licenses_qs = Dependency.objects.exclude(license__in=['', 'Unknown', 'UNKNOWN'])\
            .values('license', 'license_category')\
            .annotate(package_count=Count('id'))\
            .order_by('-package_count')

        unknown_count = Dependency.objects.filter(Q(license='') | Q(license__iexact='unknown')).count()
        total_packages = Dependency.objects.count()

        return Response({
            'total_packages': total_packages,
            'unknown_license_packages': unknown_count,
            'licenses': list(licenses_qs[:50]),
        })


class AdminReportListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        reports_qs = Report.objects.all().select_related('scan__project__owner').order_by('-created_at')
        search = request.GET.get('q', '').strip()
        if search:
            reports_qs = reports_qs.filter(
                Q(scan__project__name__icontains=search) |
                Q(scan__project__owner__username__icontains=search)
            )

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        start = (page - 1) * page_size
        end = start + page_size

        total = reports_qs.count()
        serializer = AdminReportSerializer(reports_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminGitHubConnectionApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        connections_qs = GitHubConnection.objects.all().select_related('user').order_by('-connected_at')
        search = request.GET.get('q', '').strip()
        if search:
            connections_qs = connections_qs.filter(
                Q(user__username__icontains=search) |
                Q(github_username__icontains=search)
            )

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = connections_qs.count()
        serializer = AdminGitHubConnectionSafeSerializer(connections_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })

    def delete(self, request, connection_id=None):
        """Admin disconnects a user's GitHub integration."""
        conn = get_object_or_404(GitHubConnection, pk=connection_id)
        target_user = conn.user
        gh_user = conn.github_username
        conn.delete()

        AdminAuditService.log_action(
            admin_user=request.user,
            action='GITHUB_DISCONNECTED',
            target_user=target_user,
            target_object_type='GitHubConnection',
            target_object_id=str(connection_id),
            description=f"Admin disconnected GitHub account @{gh_user} for user {target_user.username}.",
            request=request
        )
        return Response({'message': f"Disconnected GitHub account @{gh_user} for user {target_user.username}."})


class AdminAuditLogListApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        logs_qs = filter_audit_logs(request)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 30))
        start = (page - 1) * page_size
        end = start + page_size

        total = logs_qs.count()
        serializer = AdminAuditLogSerializer(logs_qs[start:end], many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class AdminSystemHealthApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        health = AdminSystemHealthService.check_health()
        return Response(health)


class AdminSettingsApiView(APIView):
    permission_classes = [IsSENTRAAdminUser]

    def get(self, request):
        settings_qs = PlatformSetting.objects.all()
        serializer = PlatformSettingSerializer(settings_qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        key = request.data.get('key', '').strip()
        value = request.data.get('value', '').strip()
        desc = request.data.get('description', '').strip()

        if not key:
            return Response({'error': 'Key is required.'}, status=status.HTTP_400_BAD_REQUEST)

        obj = PlatformSetting.set_value(key, value, updated_by=request.user, description=desc)

        AdminAuditService.log_action(
            admin_user=request.user,
            action='SETTING_CHANGED',
            target_object_type='PlatformSetting',
            target_object_id=str(obj.id),
            description=f"Admin updated setting '{key}'.",
            request=request
        )

        serializer = PlatformSettingSerializer(obj)
        return Response(serializer.data)
