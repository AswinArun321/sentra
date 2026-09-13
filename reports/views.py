import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from scans.models import Scan
from .generators import generate_json_report, generate_cyclonedx_sbom


@login_required
def download_report(request, scan_pk):
    """Download JSON report for a scan."""
    scan = get_object_or_404(Scan, pk=scan_pk, project__owner=request.user)
    report_data = generate_json_report(scan)
    response = HttpResponse(
        json.dumps(report_data, indent=2, default=str),
        content_type='application/json',
    )
    response['Content-Disposition'] = f'attachment; filename="licenselens-report-scan-{scan.pk}.json"'
    return response


@login_required
def download_sbom(request, scan_pk):
    """Download CycloneDX SBOM for a scan."""
    scan = get_object_or_404(Scan, pk=scan_pk, project__owner=request.user)
    sbom_data = generate_cyclonedx_sbom(scan)
    response = HttpResponse(
        json.dumps(sbom_data, indent=2, default=str),
        content_type='application/json',
    )
    response['Content-Disposition'] = f'attachment; filename="sbom-{scan.project.name}-scan-{scan.pk}.cdx.json"'
    return response
