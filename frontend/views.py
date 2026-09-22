import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import DashboardService

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Renders the SENTRA Security & Intelligence Dashboard.
    Provides initial baseline context from DashboardService for fast first paint,
    while dashboard.js enhances live state and interaction.
    """
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')

    service = DashboardService()
    dashboard_data = service.get_overview(request.user)

    return render(request, 'dashboard/index.html', {
        'dashboard': dashboard_data,
        'summary': dashboard_data['summary'],
        'vulnerabilities': dashboard_data['vulnerabilities'],
        'project_health': dashboard_data['project_health'],
        'attention_required': dashboard_data['attention_required'],
        'recent_scans': dashboard_data['recent_scans'],
        'github': dashboard_data['github'],
        'repository_health': dashboard_data['repository_health'],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_overview(request):
    """
    GET /api/dashboard/overview/
    Returns aggregated security, compliance, vulnerability, and repository health metrics
    strictly filtered for the authenticated user.
    """
    try:
        service = DashboardService()
        data = service.get_overview(request.user)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error generating dashboard overview for user %s: %s", request.user.username, str(e), exc_info=True)
        return Response(
            {'error': 'Unable to load dashboard overview. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
