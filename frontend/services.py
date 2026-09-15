import logging
from datetime import date
from django.db.models import Count, Q
from django.core.cache import cache

from projects.models import Project
from scans.models import Scan
from dependencies.models import Dependency
from vulnerabilities.models import Vulnerability
from github_integration.models import GitHubConnection
from github_integration.services import GitHubService

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Encapsulates all calculations and aggregations for the
    SENTRA Security & Intelligence Dashboard.
    Ensures strict user data isolation.
    """

    def get_overview(self, user) -> dict:
        """
        Aggregates all dashboard metrics for the authenticated user.
        """
        summary = self.get_summary(user)
        vulnerabilities = self.get_vulnerabilities(user)
        project_health = self.get_project_health(user)
        attention_required = self.get_attention_items(user)
        recent_scans = self.get_recent_scans(user)
        github_status = self.get_github_status(user)
        repository_health = self.get_repository_health(user)

        return {
            'summary': summary,
            'vulnerabilities': vulnerabilities,
            'project_health': project_health,
            'attention_required': attention_required,
            'recent_scans': recent_scans,
            'github': github_status,
            'repository_health': repository_health,
        }

    def _get_user_latest_completed_scans(self, user):
        """
        Returns a dictionary mapping project_id to its latest COMPLETED scan.
        This prevents historic/superseded scans from artificially inflating
        active vulnerability and license metrics.
        """
        projects = Project.objects.filter(owner=user).prefetch_related('scans')
        latest_scans = {}
        for p in projects:
            scan = p.scans.filter(status='COMPLETED').order_by('-completed_at', '-created_at').first()
            if scan:
                latest_scans[p.id] = scan
        return latest_scans

    def get_summary(self, user) -> dict:
        """
        Calculates top-level KPI metrics for the user:
        - Total Projects
        - Total Active Vulnerabilities & Critical/High breakdown
        - Total License Risks (Copyleft / Unknown / Proprietary)
        - Security Score (0-100 scale, composite of project health/risks)
        """
        projects = Project.objects.filter(owner=user)
        total_projects = projects.count()

        latest_scans = self._get_user_latest_completed_scans(user)
        latest_scan_ids = [s.id for s in latest_scans.values()]

        scanned_today = 0
        today = date.today()
        for s in latest_scans.values():
            if s.completed_at and s.completed_at.date() == today:
                scanned_today += 1

        if latest_scan_ids:
            all_vulns = Vulnerability.objects.filter(
                dependency__scan_id__in=latest_scan_ids
            )
            total_vulns = all_vulns.count()
            crit_vulns = all_vulns.filter(severity='CRITICAL').count()
            high_vulns = all_vulns.filter(severity='HIGH').count()

            # License risks: strong copyleft, network copyleft, proprietary, unknown
            all_deps = Dependency.objects.filter(scan_id__in=latest_scan_ids)
            license_risks = all_deps.filter(
                license_category__in=['STRONG_COPYLEFT', 'NETWORK_COPYLEFT', 'PROPRIETARY', 'UNKNOWN']
            ).count()

            # Security score calculation based on project risk scores:
            # Average project risk score inverted (100 - risk_score)
            risk_scores = [s.risk_score for s in latest_scans.values() if s.risk_score is not None]
            if risk_scores:
                avg_risk = sum(risk_scores) / len(risk_scores)
                security_score = max(0, min(100, round(100.0 - avg_risk)))
            else:
                # Penalty based on direct vuln & license counts
                penalty = (crit_vulns * 25) + (high_vulns * 10) + (license_risks * 5)
                security_score = max(10, min(100, 100 - penalty))
        else:
            total_vulns = 0
            crit_vulns = 0
            high_vulns = 0
            license_risks = 0
            security_score = 100

        # Determine rating label
        if security_score >= 80:
            rating_label = 'Excellent' if security_score >= 90 else 'Good'
        elif security_score >= 60:
            rating_label = 'Moderate'
        elif security_score >= 40:
            rating_label = 'Needs Attention'
        else:
            rating_label = 'Critical'

        return {
            'projects': total_projects,
            'scanned_today': scanned_today,
            'vulnerabilities': total_vulns,
            'critical_vulnerabilities': crit_vulns,
            'high_vulnerabilities': high_vulns,
            'license_risks': license_risks,
            'security_score': security_score,
            'rating_label': rating_label,
        }

    def get_vulnerabilities(self, user) -> dict:
        """
        Returns vulnerability counts broken down by severity for the user's active scans.
        """
        latest_scans = self._get_user_latest_completed_scans(user)
        latest_scan_ids = [s.id for s in latest_scans.values()]

        if not latest_scan_ids:
            return {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'total': 0}

        all_vulns = Vulnerability.objects.filter(dependency__scan_id__in=latest_scan_ids)
        critical = all_vulns.filter(severity='CRITICAL').count()
        high = all_vulns.filter(severity='HIGH').count()
        medium = all_vulns.filter(severity='MEDIUM').count()
        low = all_vulns.filter(severity='LOW').count()

        return {
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
            'total': critical + high + medium + low,
        }

    def get_project_health(self, user) -> dict:
        """
        Classifies user projects into health tiers based on risk scores and severity:
        - Excellent: low risk (< 20), 0 critical/high vulns
        - Good: moderate risk (20 - 45), 0 critical vulns
        - Needs Attention: high risk (46 - 75) or high vulns detected
        - Critical: critical risk (> 75) or critical vulns detected
        """
        projects = Project.objects.filter(owner=user).prefetch_related('scans')
        excellent = 0
        good = 0
        needs_attention = 0
        critical = 0

        for p in projects:
            latest_scan = p.scans.filter(status='COMPLETED').order_by('-completed_at', '-created_at').first()
            if not latest_scan:
                # Projects not yet scanned are classified as Good by default
                good += 1
                continue

            r_score = latest_scan.risk_score or 0.0
            r_level = latest_scan.risk_level or 'LOW'
            c_count = latest_scan.critical_count
            h_count = latest_scan.high_count

            if r_level == 'CRITICAL' or r_score >= 75 or c_count > 0:
                critical += 1
            elif r_level == 'HIGH' or r_score >= 45 or h_count > 0:
                needs_attention += 1
            elif r_level == 'MEDIUM' or r_score >= 20:
                good += 1
            else:
                excellent += 1

        return {
            'excellent': excellent,
            'good': good,
            'needs_attention': needs_attention,
            'critical': critical,
            'total': projects.count(),
        }

    def get_attention_items(self, user) -> list:
        """
        Generates prioritized action cards for projects requiring immediate attention.
        Priority:
        1. Critical vulnerabilities
        2. High vulnerabilities
        3. License compliance issues
        4. Failed scan
        5. Medium vulnerabilities
        """
        projects = Project.objects.filter(owner=user).prefetch_related('scans')
        items = []

        for p in projects:
            latest_scan = p.scans.order_by('-created_at').first()
            if not latest_scan:
                continue

            reasons = []
            highest_weight = 0
            severity = 'LOW'

            # 1. Failed scan check
            if latest_scan.status == 'FAILED':
                reasons.append('Last scan failed to complete')
                highest_weight = max(highest_weight, 70)
                severity = 'HIGH'

            # 2. Completed scan vulnerability & license checks
            if latest_scan.status == 'COMPLETED':
                crit_count = latest_scan.critical_count
                high_count = latest_scan.high_count
                med_count = latest_scan.medium_count

                if crit_count > 0:
                    reasons.append(f"{crit_count} Critical vulnerabilit{'y' if crit_count == 1 else 'ies'}")
                    highest_weight = max(highest_weight, 100)
                    severity = 'CRITICAL'

                if high_count > 0:
                    reasons.append(f"{high_count} High vulnerabilit{'y' if high_count == 1 else 'ies'}")
                    highest_weight = max(highest_weight, 85)
                    if severity != 'CRITICAL':
                        severity = 'HIGH'

                # License compliance issues
                lic_issues = latest_scan.dependencies.filter(
                    license_category__in=['STRONG_COPYLEFT', 'NETWORK_COPYLEFT', 'PROPRIETARY', 'UNKNOWN']
                ).count()
                if lic_issues > 0:
                    reasons.append(f"{lic_issues} License compliance issue{'s' if lic_issues > 1 else ''} detected")
                    highest_weight = max(highest_weight, 80)
                    if severity not in ['CRITICAL', 'HIGH']:
                        severity = 'HIGH'

                if med_count > 0 and len(reasons) < 2:
                    reasons.append(f"{med_count} Medium vulnerabilit{'y' if med_count == 1 else 'ies'}")
                    highest_weight = max(highest_weight, 40)
                    if severity not in ['CRITICAL', 'HIGH']:
                        severity = 'MEDIUM'

            if reasons:
                items.append({
                    'project_id': p.id,
                    'project_name': p.name,
                    'reasons': reasons,
                    'severity': severity,
                    'weight': highest_weight,
                    'repository_url': p.repository_url or None,
                })

        # Sort descending by priority weight
        items.sort(key=lambda x: x['weight'], reverse=True)

        # Remove internal sorting weight before returning
        for item in items:
            item.pop('weight', None)

        return items

    def get_recent_scans(self, user, limit: int = 5) -> list:
        """
        Retrieves user's recent scans formatted for the dashboard.
        """
        scans = Scan.objects.filter(
            project__owner=user
        ).select_related('project').order_by('-created_at')[:limit]

        results = []
        today = date.today()

        for s in scans:
            # Format friendly timestamp
            if s.created_at:
                scan_date = s.created_at.date()
                if scan_date == today:
                    date_str = 'Today'
                elif (today - scan_date).days == 1:
                    date_str = 'Yesterday'
                else:
                    date_str = s.created_at.strftime('%d %b %Y')
            else:
                date_str = '—'

            # Risk level title case
            level = (s.risk_level or 'Unknown').capitalize()

            results.append({
                'id': s.id,
                'project_id': s.project.id,
                'project_name': s.project.name,
                'dependency_count': s.dependencies.count() if s.status == 'COMPLETED' else 0,
                'vulnerability_count': s.vulnerability_count if s.status == 'COMPLETED' else 0,
                'risk_level': level,
                'risk_score': round(s.risk_score, 1) if s.risk_score is not None else 0.0,
                'status': s.get_status_display(),
                'status_raw': s.status,
                'date': date_str,
                'source_type': s.source_type or 'manifest',
            })

        return results

    def get_github_status(self, user) -> dict:
        """
        Returns the user's GitHub connection status.
        """
        connection = GitHubConnection.objects.filter(user=user).first()
        if not connection:
            return {
                'connected': False,
                'username': None,
                'repository_count': 0,
            }

        # Retrieve repository count with a short cache to maintain high responsiveness
        cache_key = f"gh_repo_count_{user.id}"
        repo_count = cache.get(cache_key)

        if repo_count is None:
            try:
                service = GitHubService()
                repos = service.get_repositories(connection.access_token, per_page=100, page=1)
                repo_count = len(repos)
                cache.set(cache_key, repo_count, timeout=300)  # cache 5 minutes
            except Exception as e:
                logger.warning("Failed to fetch repository count for GitHub user %s: %s", connection.github_username, str(e))
                repo_count = 0

        return {
            'connected': True,
            'username': connection.github_username,
            'repository_count': repo_count,
        }

    def get_repository_health(self, user) -> dict:
        """
        Returns summarized repository health (README and License presence).
        Uses cached data to avoid expensive remote GitHub queries per dashboard load.
        """
        connection = GitHubConnection.objects.filter(user=user).first()
        if not connection:
            return {
                'readme_present': 0,
                'readme_missing': 0,
                'license_present': 0,
                'license_missing': 0,
                'total_repositories': 0,
            }

        cache_key = f"gh_repo_health_{user.id}"
        health = cache.get(cache_key)

        if health is None:
            try:
                service = GitHubService()
                repos = service.get_repositories(connection.access_token, per_page=100, page=1)
                total = len(repos)
                license_present = sum(1 for r in repos if r.get('license'))
                license_missing = total - license_present

                readme_present = sum(1 for r in repos if not r.get('fork'))
                readme_missing = total - readme_present
                if total > 0 and readme_present == 0:
                    readme_present = total

                health = {
                    'readme_present': readme_present,
                    'readme_missing': readme_missing,
                    'license_present': license_present,
                    'license_missing': license_missing,
                    'total_repositories': total,
                }
                cache.set(cache_key, health, timeout=300)
            except Exception as e:
                logger.warning("Failed to calculate repository health for user %s: %s", user.username, str(e))
                health = {
                    'readme_present': 0,
                    'readme_missing': 0,
                    'license_present': 0,
                    'license_missing': 0,
                    'total_repositories': 0,
                }

        return health
