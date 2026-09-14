# Scan pipeline orchestrator
import logging
from datetime import datetime, timezone
from .parsers import package_json, requirements_txt
from . import vulnerability as vuln_scanner
from . import license_analyzer, maintenance, risk_engine

logger = logging.getLogger(__name__)

def run_scan(scan) -> bool:
    """Coordinates parsing, vulnerability checks, licensing, and risk scoring."""
    from dependencies.models import Dependency
    from vulnerabilities.models import Vulnerability, RiskFinding

    scan.status = 'RUNNING'
    scan.started_at = datetime.now(timezone.utc)
    scan.save(update_fields=['status', 'started_at'])

    try:
        if not scan.uploaded_file:
            raise ValueError("No manifest file uploaded.")

        scan.uploaded_file.open('r')
        content = scan.uploaded_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')
        scan.uploaded_file.close()

        # 1. Parse manifest
        if scan.source_type == 'package.json':
            raw_deps = package_json.parse(content)
        elif scan.source_type == 'requirements.txt':
            raw_deps = requirements_txt.parse(content)
        else:
            raise ValueError(f"Unsupported manifest type: {scan.source_type}")

        if not raw_deps:
            scan.status, scan.risk_score, scan.risk_level = 'COMPLETED', 0.0, 'LOW'
            scan.completed_at = datetime.now(timezone.utc)
            scan.save(update_fields=['status', 'risk_score', 'risk_level', 'completed_at'])
            return True

        # 2. Save dependencies
        dep_objs = []
        for r in raw_deps:
            dep, _ = Dependency.objects.get_or_create(
                scan=scan, name=r['name'], version=r.get('version', ''),
                defaults={
                    'version_spec': r.get('version_spec', ''),
                    'ecosystem': r.get('ecosystem', 'unknown'),
                    'is_direct': r.get('is_direct', True),
                    'dependency_type': r.get('dependency_type', 'direct')
                }
            )
            dep_objs.append(dep)

        # 3. Batch OSV Vulnerability scan
        vuln_map = vuln_scanner.scan_batch([
            {'name': d.name, 'version': d.version, 'ecosystem': d.ecosystem} for d in dep_objs
        ])

        # 4. License, maintenance, and scoring
        risk_inputs = []
        for dep in dep_objs:
            # License
            lic_info = license_analyzer.get_license(dep.name, dep.version, dep.ecosystem)
            dep.license = lic_info['license']
            dep.license_category = lic_info['license_category']
            dep.license_source = lic_info['license_source']

            # Maintenance
            maint_info = maintenance.get_maintenance_status(dep.name, dep.version, dep.ecosystem)
            dep.maintenance_status = maint_info['maintenance_status']
            dep.last_release_date = maint_info['last_release_date']
            dep.release_count = maint_info.get('release_count', 0)

            # Vulnerabilities
            dep_vulns = vuln_map.get(dep.name, [])
            for v in dep_vulns:
                Vulnerability.objects.get_or_create(
                    dependency=dep, identifier=v['identifier'],
                    defaults={
                        'source': 'OSV', 'summary': v.get('summary', ''),
                        'severity': v.get('severity', 'UNKNOWN'),
                        'fixed_version': v.get('fixed_version', ''),
                        'published_date': v.get('published_date')
                    }
                )

            dep_data = {'license_category': dep.license_category, 'maintenance_status': dep.maintenance_status, 'is_direct': dep.is_direct}
            dep.risk_score = risk_engine.calculate_dependency_risk(dep_data, dep_vulns)
            dep.save()

            for f in risk_engine.generate_risk_findings(dep_data, dep_vulns):
                RiskFinding.objects.get_or_create(
                    dependency=dep, category=f['category'], title=f['title'],
                    defaults={'severity': f['severity'], 'description': f['description'], 'recommendation': f.get('recommendation', '')}
                )
            risk_inputs.append((dep_data, dep_vulns))

        # 5. Overall scan risk calculation
        scan_risk = risk_engine.calculate_scan_risk(risk_inputs)
        scan.risk_score = scan_risk['risk_score']
        scan.risk_level = scan_risk['risk_level']
        scan.status = 'COMPLETED'
        scan.completed_at = datetime.now(timezone.utc)
        scan.save(update_fields=['status', 'risk_score', 'risk_level', 'completed_at'])
        return True

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        scan.status = 'FAILED'
        scan.error_message = str(e)[:500]
        scan.completed_at = datetime.now(timezone.utc)
        scan.save(update_fields=['status', 'error_message', 'completed_at'])
        return False
