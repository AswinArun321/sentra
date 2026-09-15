"""Report generator — creates JSON and SBOM reports."""
from datetime import datetime, timezone
from vulnerabilities.models import Vulnerability


def generate_json_report(scan) -> dict:
    """Generate a comprehensive JSON report for a completed scan."""
    from collections import Counter

    deps = scan.dependencies.all()
    vulns = Vulnerability.objects.filter(dependency__scan=scan)

    # License distribution
    license_dist = dict(Counter(d.license for d in deps).most_common())
    # Maintenance distribution
    maint_dist = dict(Counter(d.maintenance_status for d in deps).most_common())

    # Top risky dependencies
    top_risky = []
    for dep in deps.order_by('-risk_score')[:10]:
        top_risky.append({
            'name': dep.name,
            'version': dep.version,
            'ecosystem': dep.ecosystem,
            'risk_score': dep.risk_score,
            'license': dep.license,
            'maintenance_status': dep.maintenance_status,
            'vulnerability_count': dep.vulnerabilities.count(),
        })

    # Vulnerability breakdown
    vuln_list = []
    for v in vulns.order_by('severity', '-cvss_score')[:100]:
        vuln_list.append({
            'identifier': v.identifier,
            'package': v.dependency.name,
            'version': v.dependency.version,
            'severity': v.severity,
            'cvss_score': v.cvss_score,
            'summary': v.summary,
            'fixed_version': v.fixed_version,
        })

    return {
        'report_generated_at': datetime.now(timezone.utc).isoformat(),
        'project': scan.project.name,
        'scan_id': scan.pk,
        'scan_date': scan.created_at.isoformat(),
        'source_file': scan.file_name,
        'executive_summary': {
            'risk_score': scan.risk_score,
            'risk_level': scan.risk_level,
            'total_dependencies': deps.count(),
            'total_vulnerabilities': vulns.count(),
            'critical_vulnerabilities': vulns.filter(severity='CRITICAL').count(),
            'high_vulnerabilities': vulns.filter(severity='HIGH').count(),
            'medium_vulnerabilities': vulns.filter(severity='MEDIUM').count(),
            'low_vulnerabilities': vulns.filter(severity='LOW').count(),
            'license_issues': deps.filter(license_category__in=['STRONG_COPYLEFT', 'UNKNOWN']).count(),
            'stale_packages': deps.filter(maintenance_status__in=['STALE', 'ABANDONED']).count(),
        },
        'license_distribution': license_dist,
        'maintenance_distribution': maint_dist,
        'top_risky_dependencies': top_risky,
        'vulnerabilities': vuln_list,
        'disclaimer': (
            'SENTRA provides automated software dependency risk and open-source compliance analysis. '
            'Its findings are informational and should not be treated as legal or security guarantees. '
            'Final compliance decisions should be reviewed by qualified security or legal professionals.'
        ),
    }


def generate_cyclonedx_sbom(scan) -> dict:
    """Generate a CycloneDX 1.4 SBOM JSON for a scan."""
    deps = scan.dependencies.all()
    components = []

    for dep in deps:
        component = {
            'type': 'library',
            'name': dep.name,
            'version': dep.version,
            'purl': _build_purl(dep),
        }
        if dep.license and dep.license != 'Unknown':
            component['licenses'] = [{'license': {'id': dep.license}}]
        if dep.description:
            component['description'] = dep.description[:500]
        components.append(component)

    return {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.4',
        'version': 1,
        'serialNumber': f'urn:uuid:{scan.pk}',
        'metadata': {
            'timestamp': scan.created_at.isoformat(),
            'component': {
                'type': 'application',
                'name': scan.project.name,
            },
            'tools': [{'name': 'SENTRA', 'version': '1.0.0'}],
        },
        'components': components,
    }


def _build_purl(dep) -> str:
    """Build a Package URL (PURL) for a dependency."""
    eco_map = {'npm': 'npm', 'PyPI': 'pypi', 'Maven': 'maven'}
    eco = eco_map.get(dep.ecosystem, dep.ecosystem.lower())
    name = dep.name.lower() if dep.ecosystem == 'PyPI' else dep.name
    version = f'@{dep.version}' if dep.version else ''
    return f'pkg:{eco}/{name}{version}'
