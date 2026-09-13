from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from projects.models import Project
from scans.models import Scan
from vulnerabilities.models import Vulnerability
from collections import Counter


@login_required
def dashboard_view(request):
    """Main dashboard — overview of all projects and scans."""
    user = request.user
    projects = Project.objects.filter(owner=user)

    # Recent scans
    recent_scans = Scan.objects.filter(
        project__owner=user,
        status='COMPLETED'
    ).select_related('project')[:10]

    # Aggregate stats
    from dependencies.models import Dependency
    all_deps = Dependency.objects.filter(scan__project__owner=user, scan__status='COMPLETED')
    all_vulns = Vulnerability.objects.filter(dependency__scan__project__owner=user, dependency__scan__status='COMPLETED')

    total_deps = all_deps.count()
    crit_vulns = all_vulns.filter(severity='CRITICAL').count()
    high_vulns = all_vulns.filter(severity='HIGH').count()
    license_issues = all_deps.filter(license_category__in=['STRONG_COPYLEFT', 'UNKNOWN']).count()
    stale_packages = all_deps.filter(maintenance_status__in=['STALE', 'ABANDONED']).count()
    total_vulns = all_vulns.count()

    stats = {
        'total_projects': projects.count(),
        'total_scans': Scan.objects.filter(project__owner=user).count(),
        'total_dependencies': total_deps,
        'total_vulnerabilities': total_vulns,
        'critical_vulns': crit_vulns,
        'high_vulns': high_vulns,
        'license_issues': license_issues,
        'stale_packages': stale_packages,
    }

    # Reference Dashboard metrics
    if total_deps > 0:
        permissive_count = all_deps.filter(license_category='PERMISSIVE').count()
        permissive_pct = round((permissive_count / total_deps) * 100) if total_deps else 100
        vuln_pct = min(100, round((total_vulns / total_deps) * 100))
        copyleft_pct = min(100, round((license_issues / total_deps) * 100))
        penalty = (crit_vulns * 25) + (high_vulns * 12) + (license_issues * 6)
        health_score = max(10, min(100, 100 - penalty))
        safe_packages = max(0, total_deps - total_vulns)
        limit_pct = min(100, round((total_deps / max(1, total_deps + 50)) * 100))
    else:
        permissive_pct = 100
        vuln_pct = 0
        copyleft_pct = 0
        health_score = 100
        safe_packages = 0
        limit_pct = 0

    outcome_stats = {
        'permissive_pct': permissive_pct,
        'vuln_pct': vuln_pct,
        'copyleft_pct': copyleft_pct,
        'health_score': health_score,
        'safe_packages': safe_packages,
        'limit_pct': limit_pct,
    }

    # Vuln breakdown for chart
    vuln_chart = {
        'critical': crit_vulns,
        'high': high_vulns,
        'medium': all_vulns.filter(severity='MEDIUM').count(),
        'low': all_vulns.filter(severity='LOW').count(),
    }

    # License distribution for chart
    license_counts = dict(Counter(d.license for d in all_deps).most_common(8))

    return render(request, 'dashboard/index.html', {
        'projects': projects,
        'recent_scans': recent_scans,
        'stats': stats,
        'outcome_stats': outcome_stats,
        'vuln_chart': vuln_chart,
        'license_counts': license_counts,
    })
