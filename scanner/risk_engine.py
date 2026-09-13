"""
Risk Engine — calculates overall project and per-dependency risk scores.

Weighting (from plan.md section 21):
    Security       50%
    License        25%
    Maintenance    15%
    Dependency     10%

Risk Levels (from plan.md section 22):
    0–29      LOW
    30–59     MEDIUM
    60–79     HIGH
    80–100    CRITICAL
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dependencies.models import Dependency
    from vulnerabilities.models import Vulnerability

logger = logging.getLogger(__name__)

# Score weights
SECURITY_WEIGHT = 0.50
LICENSE_WEIGHT = 0.25
MAINTENANCE_WEIGHT = 0.15
DEPENDENCY_WEIGHT = 0.10

# Severity → base score
VULN_SEVERITY_SCORES = {
    'CRITICAL': 100,
    'HIGH': 80,
    'MEDIUM': 50,
    'LOW': 20,
    'UNKNOWN': 30,
}

# License category → risk score
LICENSE_RISK_SCORES = {
    'PERMISSIVE': 0,
    'WEAK_COPYLEFT': 40,
    'STRONG_COPYLEFT': 75,
    'PROPRIETARY': 80,
    'UNKNOWN': 60,
}

# Maintenance → risk score
MAINTENANCE_RISK_SCORES = {
    'ACTIVE': 0,
    'LOW_ACTIVITY': 30,
    'STALE': 65,
    'ABANDONED': 90,
    'UNKNOWN': 40,
}


def calculate_dependency_risk(dep_data: dict, vulns: list) -> float:
    """
    Calculate risk score for a single dependency.

    Args:
        dep_data: dict with 'license_category', 'maintenance_status', 'is_direct'
        vulns: list of vuln dicts with 'severity'

    Returns:
        float: 0.0 – 100.0
    """
    # Security risk: based on worst vulnerability
    security_score = 0.0
    if vulns:
        worst = max(VULN_SEVERITY_SCORES.get(v.get('severity', 'UNKNOWN'), 30) for v in vulns)
        # Multiple vulns add a bit more weight
        multiplier = min(1.0 + (len(vulns) - 1) * 0.05, 1.3)
        security_score = min(worst * multiplier, 100)

    # License risk
    license_cat = dep_data.get('license_category', 'UNKNOWN')
    license_score = LICENSE_RISK_SCORES.get(license_cat, 60)

    # Maintenance risk
    maintenance = dep_data.get('maintenance_status', 'UNKNOWN')
    maintenance_score = MAINTENANCE_RISK_SCORES.get(maintenance, 40)

    # Dependency risk: transitive deps are slightly lower risk than direct
    is_direct = dep_data.get('is_direct', True)
    dependency_score = 20 if not is_direct else 0

    # Weighted composite
    risk = (
        security_score * SECURITY_WEIGHT
        + license_score * LICENSE_WEIGHT
        + maintenance_score * MAINTENANCE_WEIGHT
        + dependency_score * DEPENDENCY_WEIGHT
    )

    return round(min(max(risk, 0.0), 100.0), 1)


def calculate_scan_risk(dependencies_with_vulns: list) -> dict:
    """
    Calculate overall risk score for a scan.

    Args:
        dependencies_with_vulns: list of (dep_data_dict, vulns_list)

    Returns:
        {
            'risk_score': float,
            'risk_level': str,
            'security_score': float,
            'license_score': float,
            'maintenance_score': float,
        }
    """
    if not dependencies_with_vulns:
        return {
            'risk_score': 0.0,
            'risk_level': 'LOW',
            'security_score': 0.0,
            'license_score': 0.0,
            'maintenance_score': 0.0,
        }

    all_security = []
    all_license = []
    all_maintenance = []

    for dep_data, vulns in dependencies_with_vulns:
        # Security: each dep contributes its max severity score
        if vulns:
            worst = max(VULN_SEVERITY_SCORES.get(v.get('severity', 'UNKNOWN'), 30) for v in vulns)
            all_security.append(worst)
        else:
            all_security.append(0)

        license_cat = dep_data.get('license_category', 'UNKNOWN')
        all_license.append(LICENSE_RISK_SCORES.get(license_cat, 60))

        maintenance = dep_data.get('maintenance_status', 'UNKNOWN')
        all_maintenance.append(MAINTENANCE_RISK_SCORES.get(maintenance, 40))

    # Scan-level: use 90th percentile of worst scores (not simple average)
    # This avoids one bad dep dragging everything up while still being sensitive
    def percentile90(lst):
        if not lst:
            return 0.0
        sorted_lst = sorted(lst, reverse=True)
        idx = max(0, int(len(sorted_lst) * 0.1))
        return sum(sorted_lst[:max(1, idx)]) / max(1, idx)

    security_score = percentile90(all_security)
    license_score = percentile90(all_license)
    maintenance_score = percentile90(all_maintenance)
    dependency_score = min(len(dependencies_with_vulns) * 0.5, 30)  # more deps = more risk

    overall = (
        security_score * SECURITY_WEIGHT
        + license_score * LICENSE_WEIGHT
        + maintenance_score * MAINTENANCE_WEIGHT
        + dependency_score * DEPENDENCY_WEIGHT
    )
    overall = round(min(max(overall, 0.0), 100.0), 1)

    return {
        'risk_score': overall,
        'risk_level': score_to_level(overall),
        'security_score': round(security_score, 1),
        'license_score': round(license_score, 1),
        'maintenance_score': round(maintenance_score, 1),
    }


def score_to_level(score: float) -> str:
    """Convert numeric risk score to text level."""
    if score >= 80:
        return 'CRITICAL'
    elif score >= 60:
        return 'HIGH'
    elif score >= 30:
        return 'MEDIUM'
    return 'LOW'


def generate_risk_findings(dep_data: dict, vulns: list) -> list[dict]:
    """
    Generate human-readable risk findings for a dependency.

    Returns list of finding dicts with:
        category, severity, title, description, recommendation
    """
    findings = []

    # Vulnerability findings
    crit_vulns = [v for v in vulns if v.get('severity') == 'CRITICAL']
    high_vulns = [v for v in vulns if v.get('severity') == 'HIGH']

    if crit_vulns:
        findings.append({
            'category': 'SECURITY',
            'severity': 'CRITICAL',
            'title': f"{len(crit_vulns)} critical vulnerability{'s' if len(crit_vulns) > 1 else ''}",
            'description': f"This package has {len(crit_vulns)} critical security vulnerability{'s' if len(crit_vulns) > 1 else ''}: " +
                           ', '.join(v['identifier'] for v in crit_vulns[:3]),
            'recommendation': 'Upgrade to the latest patched version immediately, or replace this dependency.',
        })

    if high_vulns:
        findings.append({
            'category': 'SECURITY',
            'severity': 'HIGH',
            'title': f"{len(high_vulns)} high-severity vulnerability{'s' if len(high_vulns) > 1 else ''}",
            'description': f"This package has {len(high_vulns)} high-severity vulnerability{'s' if len(high_vulns) > 1 else ''}: " +
                           ', '.join(v['identifier'] for v in high_vulns[:3]),
            'recommendation': 'Upgrade to the patched version as soon as possible.',
        })

    other_vulns = [v for v in vulns if v.get('severity') not in ('CRITICAL', 'HIGH')]
    if other_vulns:
        findings.append({
            'category': 'SECURITY',
            'severity': 'MEDIUM',
            'title': f"{len(other_vulns)} medium/low vulnerability{'s' if len(other_vulns) > 1 else ''}",
            'description': f"This package has {len(other_vulns)} lower-severity vulnerability{'s' if len(other_vulns) > 1 else ''}.",
            'recommendation': 'Plan an upgrade in your next maintenance cycle.',
        })

    # License findings
    license_cat = dep_data.get('license_category', 'UNKNOWN')
    license_name = dep_data.get('license', 'Unknown')
    if license_cat == 'STRONG_COPYLEFT':
        findings.append({
            'category': 'LICENSE',
            'severity': 'HIGH',
            'title': f'Strong copyleft license: {license_name}',
            'description': 'This package uses a strong copyleft license (GPL/AGPL). '
                           'Depending on how it is linked and distributed, your application may need to be released under the same license.',
            'recommendation': 'Consult your legal team or organization policy. Consider a permissively-licensed alternative if needed.',
        })
    elif license_cat == 'WEAK_COPYLEFT':
        findings.append({
            'category': 'LICENSE',
            'severity': 'MEDIUM',
            'title': f'Weak copyleft license: {license_name}',
            'description': 'This package uses a weak copyleft license (LGPL/MPL). '
                           'Modifications to this library itself may need to be shared.',
            'recommendation': 'Review how this library is used in your project.',
        })
    elif license_cat == 'UNKNOWN':
        findings.append({
            'category': 'LICENSE',
            'severity': 'MEDIUM',
            'title': 'License unknown',
            'description': 'No license information could be found for this package.',
            'recommendation': 'Check the package source repository for a license file before using in production.',
        })

    # Maintenance findings
    maintenance = dep_data.get('maintenance_status', 'UNKNOWN')
    if maintenance == 'ABANDONED':
        findings.append({
            'category': 'MAINTENANCE',
            'severity': 'HIGH',
            'title': 'Package appears abandoned',
            'description': 'This package has not had a release in over 4 years and may be unmaintained.',
            'recommendation': 'Consider replacing this dependency with an actively maintained alternative.',
        })
    elif maintenance == 'STALE':
        findings.append({
            'category': 'MAINTENANCE',
            'severity': 'MEDIUM',
            'title': 'Package is stale',
            'description': 'This package has not had a release in over 2 years.',
            'recommendation': 'Monitor for updates or plan migration to a maintained alternative.',
        })
    elif maintenance == 'LOW_ACTIVITY':
        findings.append({
            'category': 'MAINTENANCE',
            'severity': 'LOW',
            'title': 'Low maintenance activity',
            'description': 'This package has not had a release in over a year.',
            'recommendation': 'Keep an eye on this package for continued maintenance.',
        })

    return findings
