from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import get_user_model

from admin_panel.models import AdminAuditLog, UserAccountStatus
from projects.models import Project
from scans.models import Scan
from vulnerabilities.models import Vulnerability
from dependencies.models import Dependency

User = get_user_model()


def paginate_queryset(request, queryset, page_size=25):
    """
    Standard pagination helper for template views.
    """
    paginator = Paginator(queryset, page_size)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj


def filter_users(request, queryset=None):
    """
    Applies search & status filters to User queryset.
    """
    if queryset is None:
        queryset = User.objects.all().select_related('admin_status', 'github_connection').order_by('-date_joined')

    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(github_connection__github_username__icontains=search)
        ).distinct()

    status = request.GET.get('status', '').strip().upper()
    if status == 'ACTIVE':
        # active and not suspended
        queryset = queryset.filter(is_active=True).exclude(admin_status__status='SUSPENDED')
    elif status == 'INACTIVE':
        queryset = queryset.filter(is_active=False).exclude(admin_status__status='SUSPENDED')
    elif status == 'SUSPENDED':
        queryset = queryset.filter(admin_status__status='SUSPENDED')

    role = request.GET.get('role', '').strip().upper()
    if role == 'STAFF' or role == 'ADMIN':
        queryset = queryset.filter(Q(is_staff=True) | Q(is_superuser=True))
    elif role == 'USER':
        queryset = queryset.filter(is_staff=False, is_superuser=False)

    github = request.GET.get('github', '').strip().lower()
    if github == 'connected':
        queryset = queryset.filter(github_connection__isnull=False)
    elif github == 'disconnected':
        queryset = queryset.filter(github_connection__isnull=True)

    return queryset


def filter_projects(request, queryset=None):
    if queryset is None:
        queryset = Project.objects.all().select_related('owner').order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(repository_url__icontains=search) |
            Q(owner__username__icontains=search) |
            Q(owner__email__icontains=search)
        )

    source = request.GET.get('source', '').strip().lower()
    if source in ['github', 'manual']:
        queryset = queryset.filter(source=source)

    analysis_status = request.GET.get('status', '').strip().upper()
    if analysis_status:
        queryset = queryset.filter(analysis_status=analysis_status)

    return queryset


def filter_scans(request, queryset=None):
    if queryset is None:
        queryset = Scan.objects.all().select_related('project', 'project__owner').order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(project__name__icontains=search) |
            Q(project__owner__username__icontains=search) |
            Q(project__owner__email__icontains=search)
        )

    status = request.GET.get('status', '').strip().upper()
    if status in ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED']:
        queryset = queryset.filter(status=status)

    risk_level = request.GET.get('risk_level', '').strip().upper()
    if risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN']:
        queryset = queryset.filter(risk_level=risk_level)

    return queryset


def filter_vulnerabilities(request, queryset=None):
    if queryset is None:
        queryset = Vulnerability.objects.all().select_related(
            'dependency', 'dependency__scan', 'dependency__scan__project', 'dependency__scan__project__owner'
        ).order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(identifier__icontains=search) |
            Q(dependency__name__icontains=search) |
            Q(summary__icontains=search)
        )

    severity = request.GET.get('severity', '').strip().upper()
    if severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
        queryset = queryset.filter(severity=severity)

    ecosystem = request.GET.get('ecosystem', '').strip()
    if ecosystem:
        queryset = queryset.filter(dependency__ecosystem__iexact=ecosystem)

    return queryset


def filter_audit_logs(request, queryset=None):
    if queryset is None:
        queryset = AdminAuditLog.objects.all().select_related('admin_user', 'target_user').order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(action__icontains=search) |
            Q(description__icontains=search) |
            Q(admin_user__username__icontains=search) |
            Q(target_user__username__icontains=search) |
            Q(ip_address__icontains=search)
        )

    action = request.GET.get('action', '').strip().upper()
    if action:
        queryset = queryset.filter(action=action)

    return queryset
