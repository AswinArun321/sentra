# Risk Calculation Engine for dependencies and scans

SEVERITY_WEIGHTS = {'CRITICAL': 100, 'HIGH': 80, 'MEDIUM': 50, 'LOW': 20, 'UNKNOWN': 30}
LICENSE_WEIGHTS = {'PERMISSIVE': 0, 'WEAK_COPYLEFT': 40, 'STRONG_COPYLEFT': 75, 'PROPRIETARY': 80, 'UNKNOWN': 60}
MAINTENANCE_WEIGHTS = {'ACTIVE': 0, 'LOW_ACTIVITY': 30, 'STALE': 65, 'ABANDONED': 90, 'UNKNOWN': 40}

def score_to_level(score: float) -> str:
    if score >= 80: return 'CRITICAL'
    if score >= 60: return 'HIGH'
    if score >= 30: return 'MEDIUM'
    return 'LOW'

def calculate_dependency_risk(dep_data: dict, vulns: list) -> float:
    """Calculates weighted risk score (0-100) for a single package."""
    sec_score = 0.0
    if vulns:
        worst = max(SEVERITY_WEIGHTS.get(v.get('severity', 'UNKNOWN'), 30) for v in vulns)
        sec_score = min(worst * min(1.0 + (len(vulns) - 1) * 0.05, 1.3), 100)

    lic_score = LICENSE_WEIGHTS.get(dep_data.get('license_category', 'UNKNOWN'), 60)
    maint_score = MAINTENANCE_WEIGHTS.get(dep_data.get('maintenance_status', 'UNKNOWN'), 40)
    dep_score = 20 if not dep_data.get('is_direct', True) else 0

    # 50% security, 25% license, 15% maintenance, 10% dependency type
    total = (sec_score * 0.50) + (lic_score * 0.25) + (maint_score * 0.15) + (dep_score * 0.10)
    return round(min(max(total, 0.0), 100.0), 1)

def calculate_scan_risk(deps_with_vulns: list) -> dict:
    """Calculates composite risk metrics across all scanned packages."""
    if not deps_with_vulns:
        return {'risk_score': 0.0, 'risk_level': 'LOW', 'security_score': 0.0, 'license_score': 0.0, 'maintenance_score': 0.0}

    sec_list, lic_list, maint_list = [], [], []
    for dep_data, vulns in deps_with_vulns:
        sec_list.append(max((SEVERITY_WEIGHTS.get(v.get('severity', 'UNKNOWN'), 30) for v in vulns), default=0))
        lic_list.append(LICENSE_WEIGHTS.get(dep_data.get('license_category', 'UNKNOWN'), 60))
        maint_list.append(MAINTENANCE_WEIGHTS.get(dep_data.get('maintenance_status', 'UNKNOWN'), 40))

    def top_avg(lst):
        if not lst: return 0.0
        s = sorted(lst, reverse=True)
        top_k = max(1, int(len(s) * 0.1))
        return sum(s[:top_k]) / top_k

    sec_avg, lic_avg, maint_avg = top_avg(sec_list), top_avg(lic_list), top_avg(maint_list)
    dep_weight = min(len(deps_with_vulns) * 0.5, 30)
    overall = round(min((sec_avg * 0.5) + (lic_avg * 0.25) + (maint_avg * 0.15) + (dep_weight * 0.1), 100.0), 1)

    return {
        'risk_score': overall,
        'risk_level': score_to_level(overall),
        'security_score': round(sec_avg, 1),
        'license_score': round(lic_avg, 1),
        'maintenance_score': round(maint_avg, 1)
    }

def generate_risk_findings(dep_data: dict, vulns: list) -> list:
    """Generates human-readable security and compliance findings."""
    findings = []
    crits = [v for v in vulns if v.get('severity') == 'CRITICAL']
    highs = [v for v in vulns if v.get('severity') == 'HIGH']

    if crits:
        findings.append({
            'category': 'SECURITY', 'severity': 'CRITICAL',
            'title': f"{len(crits)} critical vulnerabilities detected",
            'description': f"Identifiers: {', '.join(v['identifier'] for v in crits[:3])}",
            'recommendation': 'Upgrade package to the latest patched release immediately.'
        })
    elif highs:
        findings.append({
            'category': 'SECURITY', 'severity': 'HIGH',
            'title': f"{len(highs)} high severity vulnerabilities",
            'description': f"Identifiers: {', '.join(v['identifier'] for v in highs[:3])}",
            'recommendation': 'Upgrade to patched version as soon as possible.'
        })

    lic = dep_data.get('license_category', 'UNKNOWN')
    if lic == 'STRONG_COPYLEFT':
        findings.append({
            'category': 'LICENSE', 'severity': 'HIGH',
            'title': 'Strong copyleft license detected',
            'description': f"Package uses viral copyleft license ({dep_data.get('license')}).",
            'recommendation': 'Ensure open source compliance or replace with permissive alternative.'
        })

    maint = dep_data.get('maintenance_status', 'UNKNOWN')
    if maint in ('ABANDONED', 'STALE'):
        findings.append({
            'category': 'MAINTENANCE', 'severity': 'MEDIUM',
            'title': f'Package is {maint.lower()}',
            'description': 'No releases published recently on package registry.',
            'recommendation': 'Monitor package or evaluate active replacements.'
        })

    return findings
