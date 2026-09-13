"""
Scan Orchestrator — ties together parsing, vulnerability scanning,
license analysis, maintenance checking, and risk scoring.

This runs synchronously for the MVP. Celery/Redis can be added later.
"""
import logging
from datetime import datetime, timezone

from .parsers import package_json, requirements_txt
from . import vulnerability as vuln_scanner
from . import license_analyzer
from . import maintenance as maint_checker
from . import risk_engine

logger = logging.getLogger(__name__)


def run_scan(scan) -> bool:
    """
    Execute a full dependency scan.

    Args:
        scan: scans.models.Scan instance (already created, file uploaded)

    Returns:
        True if successful, False if failed
    """
    from scans.models import Scan
    from dependencies.models import Dependency
    from vulnerabilities.models import Vulnerability, RiskFinding

    logger.info(f"Starting scan #{scan.pk} for project '{scan.project.name}'")

    # Update scan status
    scan.status = 'RUNNING'
    scan.started_at = datetime.now(timezone.utc)
    scan.save(update_fields=['status', 'started_at'])

    try:
        # ── Step 1: Read and parse the uploaded file ───────────────────
        if not scan.uploaded_file:
            raise ValueError("No file uploaded for this scan.")

        scan.uploaded_file.open('r')
        file_content = scan.uploaded_file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8', errors='replace')
        scan.uploaded_file.close()

        source_type = scan.source_type
        if source_type == 'package.json':
            raw_deps = package_json.parse(file_content)
        elif source_type == 'requirements.txt':
            raw_deps = requirements_txt.parse(file_content)
        else:
            raise ValueError(f"Unsupported file type: {source_type}")

        logger.info(f"Scan #{scan.pk}: parsed {len(raw_deps)} dependencies")

        if not raw_deps:
            logger.warning(f"Scan #{scan.pk}: no dependencies found in file")
            scan.status = 'COMPLETED'
            scan.risk_score = 0.0
            scan.risk_level = 'LOW'
            scan.completed_at = datetime.now(timezone.utc)
            scan.save(update_fields=['status', 'risk_score', 'risk_level', 'completed_at'])
            return True

        # ── Step 2: Create Dependency records ──────────────────────────
        dep_objects = []
        for raw in raw_deps:
            dep, _ = Dependency.objects.get_or_create(
                scan=scan,
                name=raw['name'],
                version=raw.get('version', ''),
                defaults={
                    'version_spec': raw.get('version_spec', ''),
                    'ecosystem': raw.get('ecosystem', 'unknown'),
                    'is_direct': raw.get('is_direct', True),
                    'dependency_type': raw.get('dependency_type', 'direct'),
                }
            )
            dep_objects.append((dep, raw))

        # ── Step 3: Batch vulnerability scan ───────────────────────────
        logger.info(f"Scan #{scan.pk}: querying OSV for {len(dep_objects)} packages...")
        packages_for_osv = [
            {'name': dep.name, 'version': dep.version, 'ecosystem': dep.ecosystem}
            for dep, _ in dep_objects
        ]
        all_vulns = vuln_scanner.scan_batch(packages_for_osv)

        # ── Step 4: License + Maintenance + Risk per dependency ─────────
        risk_inputs = []
        for dep, raw in dep_objects:
            name = dep.name
            version = dep.version
            ecosystem = dep.ecosystem

            # License
            try:
                lic_info = license_analyzer.get_license(name, version, ecosystem)
            except Exception as e:
                logger.warning(f"License fetch failed for {name}: {e}")
                lic_info = {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'error'}

            dep.license = lic_info['license']
            dep.license_category = lic_info['license_category']
            dep.license_source = lic_info['license_source']

            # Maintenance
            try:
                maint_info = maint_checker.get_maintenance_status(name, version, ecosystem)
            except Exception as e:
                logger.warning(f"Maintenance check failed for {name}: {e}")
                maint_info = {'maintenance_status': 'UNKNOWN', 'last_release_date': None, 'release_count': 0}

            dep.maintenance_status = maint_info['maintenance_status']
            dep.last_release_date = maint_info['last_release_date']
            dep.release_count = maint_info.get('release_count', 0)

            # Save vulnerabilities
            dep_vulns_raw = all_vulns.get(name, [])
            vuln_dicts = []
            for v in dep_vulns_raw:
                try:
                    Vulnerability.objects.get_or_create(
                        dependency=dep,
                        identifier=v['identifier'],
                        defaults={
                            'source': v.get('source', 'OSV'),
                            'summary': v.get('summary', ''),
                            'severity': v.get('severity', 'UNKNOWN'),
                            'cvss_score': v.get('cvss_score'),
                            'fixed_version': v.get('fixed_version', ''),
                            'affected_versions': v.get('affected_versions', ''),
                            'references': v.get('references', []),
                            'published_date': v.get('published_date'),
                        }
                    )
                    vuln_dicts.append(v)
                except Exception as e:
                    logger.warning(f"Error saving vulnerability {v.get('identifier')}: {e}")

            # Calculate dependency risk score
            dep_risk_data = {
                'license_category': dep.license_category,
                'maintenance_status': dep.maintenance_status,
                'is_direct': dep.is_direct,
            }
            dep.risk_score = risk_engine.calculate_dependency_risk(dep_risk_data, vuln_dicts)
            dep.save()

            # Generate risk findings
            findings = risk_engine.generate_risk_findings(dep_risk_data, vuln_dicts)
            for f in findings:
                RiskFinding.objects.get_or_create(
                    dependency=dep,
                    category=f['category'],
                    title=f['title'],
                    defaults={
                        'severity': f['severity'],
                        'description': f['description'],
                        'recommendation': f.get('recommendation', ''),
                    }
                )

            risk_inputs.append((dep_risk_data, vuln_dicts))

        # ── Step 5: Calculate overall scan risk ────────────────────────
        scan_risk = risk_engine.calculate_scan_risk(risk_inputs)

        scan.risk_score = scan_risk['risk_score']
        scan.risk_level = scan_risk['risk_level']
        scan.status = 'COMPLETED'
        scan.completed_at = datetime.now(timezone.utc)
        scan.save(update_fields=['status', 'risk_score', 'risk_level', 'completed_at'])

        logger.info(
            f"Scan #{scan.pk} completed: "
            f"score={scan.risk_score}, level={scan.risk_level}, "
            f"deps={len(dep_objects)}"
        )
        return True

    except Exception as e:
        logger.error(f"Scan #{scan.pk} failed: {e}", exc_info=True)
        scan.status = 'FAILED'
        scan.error_message = str(e)[:1000]
        scan.completed_at = datetime.now(timezone.utc)
        scan.save(update_fields=['status', 'error_message', 'completed_at'])
        return False
