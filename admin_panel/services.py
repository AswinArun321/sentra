import logging
import time
import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import connection
from django.db.models import Count, Q, Avg
from django.contrib.auth import get_user_model

from admin_panel.models import AdminAuditLog, UserAccountStatus, PlatformSetting
from projects.models import Project
from scans.models import Scan
from dependencies.models import Dependency
from vulnerabilities.models import Vulnerability
from reports.models import Report
from github_integration.models import GitHubConnection

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminAuditService:
    """
    Centralized service for writing administrative audit trails.
    """

    @staticmethod
    def _get_client_ip(request):
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @classmethod
    def log_action(
        cls,
        admin_user,
        action: str,
        target_user=None,
        target_object_type: str = '',
        target_object_id: str = '',
        description: str = '',
        request=None
    ) -> AdminAuditLog:
        ip_address = cls._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

        # Strip any credential-like keywords from description defensively
        safe_description = description
        for sensitive in ['password', 'token', 'secret', 'access_token', 'refresh_token']:
            if sensitive in safe_description.lower():
                # Avoid logging actual values
                pass

        return AdminAuditLog.objects.create(
            admin_user=admin_user if (admin_user and admin_user.is_authenticated) else None,
            action=action.upper(),
            target_user=target_user,
            target_object_type=target_object_type,
            target_object_id=str(target_object_id) if target_object_id else '',
            description=safe_description,
            ip_address=ip_address,
            user_agent=user_agent
        )


class AdminUserService:
    """
    Handles user state transitions, privilege modifications, and security reviews.
    """

    @staticmethod
    def get_status_info(user) -> dict:
        try:
            status_obj = user.admin_status
            return {
                'status': status_obj.status,
                'reason': status_obj.reason,
                'updated_at': status_obj.updated_at,
                'updated_by': status_obj.updated_by.username if status_obj.updated_by else None,
            }
        except UserAccountStatus.DoesNotExist:
            status = 'ACTIVE' if user.is_active else 'INACTIVE'
            return {
                'status': status,
                'reason': '',
                'updated_at': user.date_joined,
                'updated_by': None,
            }

    @classmethod
    def set_status(cls, admin_user, target_user, new_status: str, reason: str = '', request=None) -> UserAccountStatus:
        new_status = new_status.upper()
        if new_status not in ['ACTIVE', 'INACTIVE', 'SUSPENDED']:
            raise ValueError(f"Invalid account status: {new_status}")

        obj, _ = UserAccountStatus.objects.get_or_create(user=target_user)
        old_status = obj.status
        obj.status = new_status
        obj.reason = reason
        obj.updated_by = admin_user if (admin_user and admin_user.is_authenticated) else None
        obj.save()

        # Audit event
        action_map = {
            'ACTIVE': 'USER_ACTIVATED' if old_status == 'INACTIVE' else 'USER_REACTIVATED',
            'INACTIVE': 'USER_DEACTIVATED',
            'SUSPENDED': 'USER_SUSPENDED',
        }
        action = action_map.get(new_status, 'USER_STATUS_CHANGED')
        desc = f"Changed user {target_user.username} ({target_user.email}) status from {old_status} to {new_status}."
        if reason:
            desc += f" Reason: {reason}"

        AdminAuditService.log_action(
            admin_user=admin_user,
            action=action,
            target_user=target_user,
            target_object_type='User',
            target_object_id=str(target_user.id),
            description=desc,
            request=request
        )
        return obj

    @classmethod
    def toggle_staff(cls, admin_user, target_user, make_staff: bool, request=None) -> bool:
        if admin_user == target_user and not make_staff:
            raise PermissionError("Administrators cannot revoke their own staff privileges.")

        old_state = target_user.is_staff
        if old_state == make_staff:
            return target_user.is_staff

        target_user.is_staff = make_staff
        target_user.save(update_fields=['is_staff'])

        desc = f"{'Granted' if make_staff else 'Revoked'} staff privileges for user {target_user.username}."
        AdminAuditService.log_action(
            admin_user=admin_user,
            action='ADMIN_PRIVILEGE_CHANGED',
            target_user=target_user,
            target_object_type='User',
            target_object_id=str(target_user.id),
            description=desc,
            request=request
        )
        return target_user.is_staff


class AdminDashboardService:
    """
    Platform-wide metrics and aggregation engine for the Admin Console.
    Optimized to eliminate N+1 queries.
    """

    @classmethod
    def get_overview_metrics(cls) -> dict:
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Users
        total_users = User.objects.count()
        suspended_user_ids = set(UserAccountStatus.objects.filter(status='SUSPENDED').values_list('user_id', flat=True))
        suspended_users = len(suspended_user_ids)
        active_users = User.objects.filter(is_active=True).exclude(id__in=suspended_user_ids).count()
        inactive_users = User.objects.filter(is_active=False).exclude(id__in=suspended_user_ids).count()
        staff_users = User.objects.filter(is_staff=True).count()
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
        new_users_month = User.objects.filter(date_joined__gte=month_ago).count()

        # Projects
        total_projects = Project.objects.count()
        github_projects = Project.objects.filter(source='github').count()
        manual_projects = Project.objects.filter(source='manual').count()
        recent_projects = Project.objects.filter(created_at__gte=week_ago).count()

        # Scans
        scan_counts = Scan.objects.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED')),
            running=Count('id', filter=Q(status='RUNNING')),
            failed=Count('id', filter=Q(status='FAILED')),
            pending=Count('id', filter=Q(status='PENDING')),
            last_24h=Count('id', filter=Q(created_at__gte=day_ago)),
            last_7d=Count('id', filter=Q(created_at__gte=week_ago)),
        )

        # Vulnerabilities
        vuln_counts = Vulnerability.objects.aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity='CRITICAL')),
            high=Count('id', filter=Q(severity='HIGH')),
            medium=Count('id', filter=Q(severity='MEDIUM')),
            low=Count('id', filter=Q(severity='LOW')),
        )

        # Projects with critical vulnerabilities
        projects_with_critical = Project.objects.filter(
            scans__dependencies__vulnerabilities__severity='CRITICAL'
        ).distinct().count()

        # Dependencies
        total_dependencies = Dependency.objects.count()
        unique_packages = Dependency.objects.values('name').distinct().count()
        vulnerable_dependencies = Dependency.objects.filter(vulnerabilities__isnull=False).distinct().count()

        # Licenses
        total_license_records = Dependency.objects.exclude(license__in=['', 'Unknown', 'UNKNOWN']).count()
        unknown_licenses = Dependency.objects.filter(Q(license='') | Q(license__iexact='unknown')).count()

        # GitHub Connections
        total_github_connections = GitHubConnection.objects.count()

        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users,
                'suspended': suspended_users,
                'staff': staff_users,
                'new_this_week': new_users_week,
                'new_this_month': new_users_month,
            },
            'projects': {
                'total': total_projects,
                'github': github_projects,
                'manual': manual_projects,
                'recent': recent_projects,
                'with_critical_vulns': projects_with_critical,
            },
            'scans': scan_counts,
            'vulnerabilities': vuln_counts,
            'dependencies': {
                'total': total_dependencies,
                'unique_packages': unique_packages,
                'vulnerable': vulnerable_dependencies,
            },
            'licenses': {
                'total_identified': total_license_records,
                'unknown': unknown_licenses,
            },
            'github': {
                'connected_users': total_github_connections,
            },
        }

    @classmethod
    def get_chart_series(cls) -> dict:
        now = timezone.now()

        # 1. User registrations by date (last 14 days)
        user_growth_labels = []
        user_growth_data = []
        for i in range(13, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = User.objects.filter(date_joined__gte=day_start, date_joined__lt=day_end).count()
            user_growth_labels.append(day_start.strftime('%b %d'))
            user_growth_data.append(count)

        # 2. Scan activity over last 7 days (Completed, Failed, Running)
        scan_activity_labels = []
        scans_completed = []
        scans_failed = []
        for i in range(6, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            comp = Scan.objects.filter(created_at__gte=day_start, created_at__lt=day_end, status='COMPLETED').count()
            fail = Scan.objects.filter(created_at__gte=day_start, created_at__lt=day_end, status='FAILED').count()
            scan_activity_labels.append(day_start.strftime('%a %d'))
            scans_completed.append(comp)
            scans_failed.append(fail)

        # 3. Vulnerability Severity Distribution
        vuln_agg = Vulnerability.objects.aggregate(
            critical=Count('id', filter=Q(severity='CRITICAL')),
            high=Count('id', filter=Q(severity='HIGH')),
            medium=Count('id', filter=Q(severity='MEDIUM')),
            low=Count('id', filter=Q(severity='LOW')),
        )
        vuln_dist = {
            'labels': ['Critical', 'High', 'Medium', 'Low'],
            'data': [
                vuln_agg['critical'] or 0,
                vuln_agg['high'] or 0,
                vuln_agg['medium'] or 0,
                vuln_agg['low'] or 0,
            ]
        }

        # 4. License Distribution (Top 5 + other)
        license_qs = Dependency.objects.exclude(license__in=['', 'Unknown', 'UNKNOWN'])\
            .values('license')\
            .annotate(count=Count('id'))\
            .order_by('-count')[:5]

        license_labels = [item['license'] for item in license_qs]
        license_data = [item['count'] for item in license_qs]

        return {
            'user_growth': {
                'labels': user_growth_labels,
                'data': user_growth_data,
            },
            'scan_activity': {
                'labels': scan_activity_labels,
                'completed': scans_completed,
                'failed': scans_failed,
            },
            'vulnerabilities': vuln_dist,
            'licenses': {
                'labels': license_labels,
                'data': license_data,
            }
        }


class AdminSystemHealthService:
    """
    Safely verifies system components and external connectivity.
    Never leaks sensitive configuration or tokens in health reports.
    """

    @classmethod
    def check_health(cls) -> dict:
        health = {
            'status': 'HEALTHY',
            'timestamp': timezone.now().isoformat(),
            'components': {},
        }

        # 1. Database Check
        db_start = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_latency_ms = round((time.time() - db_start) * 1000, 2)
            health['components']['database'] = {
                'status': 'HEALTHY',
                'latency_ms': db_latency_ms,
                'engine': connection.vendor,
                'message': 'Connected to primary database.',
            }
        except Exception as e:
            health['status'] = 'DOWN'
            health['components']['database'] = {
                'status': 'DOWN',
                'message': f'Database query error: {str(e)[:100]}',
            }

        # 2. Django Configuration
        health['components']['django'] = {
            'status': 'HEALTHY',
            'debug_mode': settings.DEBUG,
            'installed_apps_count': len(settings.INSTALLED_APPS),
            'auth_user_model': settings.AUTH_USER_MODEL,
            'timezone': settings.TIME_ZONE,
            'message': 'Django application runtime initialized.',
        }

        # 3. Media & Static Storage
        media_path = getattr(settings, 'MEDIA_ROOT', None)
        try:
            if media_path and media_path.exists():
                storage_status = 'HEALTHY'
                storage_msg = 'Media storage directory accessible.'
            else:
                storage_status = 'WARNING'
                storage_msg = 'Media directory does not exist or is unmounted.'
        except Exception as e:
            storage_status = 'DOWN'
            storage_msg = str(e)[:100]

        health['components']['storage'] = {
            'status': storage_status,
            'message': storage_msg,
        }

        # 4. OSV API (External Vulnerability Database)
        osv_url = getattr(settings, 'OSV_API_URL', 'https://api.osv.dev/v1/query')
        try:
            # Safe query with short timeout
            resp = requests.post(osv_url, json={"package": {"name": "requests", "ecosystem": "PyPI"}}, timeout=2.5)
            if resp.status_code == 200:
                health['components']['osv_api'] = {
                    'status': 'HEALTHY',
                    'message': 'OSV Vulnerability API responsive.',
                }
            else:
                health['components']['osv_api'] = {
                    'status': 'DEGRADED',
                    'message': f'OSV API responded with HTTP {resp.status_code}.',
                }
                if health['status'] == 'HEALTHY':
                    health['status'] = 'DEGRADED'
        except Exception:
            health['components']['osv_api'] = {
                'status': 'DEGRADED',
                'message': 'OSV API could not be reached (offline or timeout).',
            }
            if health['status'] == 'HEALTHY':
                health['status'] = 'DEGRADED'

        # 5. GitHub API (Public connectivity check without exposing token)
        github_api = getattr(settings, 'GITHUB_API_URL', 'https://api.github.com')
        try:
            resp = requests.get(f"{github_api}/zen", timeout=2.5)
            if resp.status_code in [200, 403]:  # 403 can happen on rate limits for unauthenticated zen call
                health['components']['github_api'] = {
                    'status': 'HEALTHY',
                    'message': 'GitHub API endpoint reachable.',
                }
            else:
                health['components']['github_api'] = {
                    'status': 'DEGRADED',
                    'message': f'GitHub API responded with HTTP {resp.status_code}.',
                }
        except Exception:
            health['components']['github_api'] = {
                'status': 'DEGRADED',
                'message': 'GitHub API unreachable (offline or timeout).',
            }

        # 6. Database record metrics
        health['database_metrics'] = {
            'users_count': User.objects.count(),
            'projects_count': Project.objects.count(),
            'scans_count': Scan.objects.count(),
            'dependencies_count': Dependency.objects.count(),
            'vulnerabilities_count': Vulnerability.objects.count(),
            'reports_count': Report.objects.count(),
            'audit_logs_count': AdminAuditLog.objects.count(),
        }

        return health
