import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from projects.models import Project
from .models import Scan
from .serializers import ScanSerializer, ScanDetailSerializer
from scanner.orchestrator import run_scan

logger = logging.getLogger(__name__)

ALLOWED_FILES = {'package.json', 'requirements.txt', 'pom.xml'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# ─── REST API Views ────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_start_scan(request, project_pk):
    """Upload a dependency file and start a scan."""
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    file_name = uploaded_file.name
    if file_name not in ALLOWED_FILES:
        return Response({'error': f'Unsupported file: {file_name}. Allowed: {", ".join(ALLOWED_FILES)}'}, status=400)

    if uploaded_file.size > MAX_FILE_SIZE:
        return Response({'error': 'File too large. Maximum 5 MB.'}, status=400)

    scan = Scan.objects.create(
        project=project,
        source_type=file_name,
        file_name=file_name,
        uploaded_file=uploaded_file,
    )

    # Run scan synchronously (MVP)
    success = run_scan(scan)
    scan.refresh_from_db()

    return Response(ScanDetailSerializer(scan).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_project_scans(request, project_pk):
    """List all scans for a project."""
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    scans = project.scans.all()
    return Response(ScanSerializer(scans, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scan_detail(request, pk):
    """Get full scan detail."""
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    return Response(ScanDetailSerializer(scan).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scan_dependencies(request, pk):
    """List dependencies for a scan."""
    from dependencies.serializers import DependencySerializer
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    deps = scan.dependencies.all()
    return Response(DependencySerializer(deps, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scan_vulnerabilities(request, pk):
    """List vulnerabilities for a scan."""
    from vulnerabilities.serializers import VulnerabilitySerializer
    from vulnerabilities.models import Vulnerability
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    vulns = Vulnerability.objects.filter(dependency__scan=scan)
    return Response(VulnerabilitySerializer(vulns, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scan_licenses(request, pk):
    """License summary for a scan."""
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    deps = scan.dependencies.values('license', 'license_category').order_by('license')
    from collections import Counter
    counts = Counter(d['license'] for d in deps)
    return Response([{'license': k, 'count': v} for k, v in counts.most_common()])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scan_report(request, pk):
    """Generate JSON report for a scan."""
    from reports.generators import generate_json_report
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    report_data = generate_json_report(scan)
    return Response(report_data)


# ─── Template (Frontend) Views ─────────────────────────────────

@login_required
def scan_upload_view(request, project_pk):
    """Upload a file and trigger a scan from the frontend."""
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('project_detail', pk=project_pk)

        file_name = uploaded_file.name
        if file_name not in ALLOWED_FILES:
            messages.error(request, f'Unsupported file type: {file_name}. Upload package.json or requirements.txt.')
            return redirect('project_detail', pk=project_pk)

        if uploaded_file.size > MAX_FILE_SIZE:
            messages.error(request, 'File is too large. Maximum file size is 5 MB.')
            return redirect('project_detail', pk=project_pk)

        scan = Scan.objects.create(
            project=project,
            source_type=file_name,
            file_name=file_name,
            uploaded_file=uploaded_file,
        )

        logger.info(f"User {request.user.email} started scan #{scan.pk} on project {project.name}")
        messages.info(request, f'Scan started for {file_name}. Analyzing dependencies...')

        success = run_scan(scan)
        scan.refresh_from_db()

        if success:
            messages.success(request, f'Scan completed! Found {scan.dependencies.count()} dependencies. Risk: {scan.risk_level} ({scan.risk_score})')
        else:
            messages.error(request, f'Scan failed: {scan.error_message}')

        return redirect('scan_detail', pk=scan.pk)

    return redirect('project_detail', pk=project_pk)


@login_required
def scan_detail_view(request, pk):
    """Full scan detail page with tabs."""
    scan = get_object_or_404(Scan, pk=pk, project__owner=request.user)
    from vulnerabilities.models import Vulnerability
    vulns = Vulnerability.objects.filter(dependency__scan=scan).select_related('dependency')
    deps = scan.dependencies.prefetch_related('vulnerabilities', 'risk_findings').all()

    # Stats
    stats = {
        'critical': vulns.filter(severity='CRITICAL').count(),
        'high': vulns.filter(severity='HIGH').count(),
        'medium': vulns.filter(severity='MEDIUM').count(),
        'low': vulns.filter(severity='LOW').count(),
        'total_vulns': vulns.count(),
        'total_deps': deps.count(),
        'direct_deps': deps.filter(is_direct=True).count(),
        'stale_deps': deps.filter(maintenance_status__in=['STALE', 'ABANDONED']).count(),
        'license_issues': deps.filter(license_category__in=['STRONG_COPYLEFT', 'UNKNOWN']).count(),
    }

    # License distribution
    from collections import Counter
    license_counts = Counter(d.license for d in deps)

    # Maintenance distribution
    maint_counts = Counter(d.maintenance_status for d in deps)

    return render(request, 'scans/detail.html', {
        'scan': scan,
        'project': scan.project,
        'deps': deps,
        'vulns': vulns,
        'stats': stats,
        'license_counts': dict(license_counts.most_common(10)),
        'maint_counts': dict(maint_counts),
    })


@login_required
def scan_history_view(request, project_pk):
    """Show scan history for a project."""
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    scans = project.scans.all()
    return render(request, 'scans/history.html', {
        'project': project,
        'scans': scans,
    })
