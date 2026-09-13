import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer

logger = logging.getLogger(__name__)


# ─── REST API Views ────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_list_create(request):
    """List all projects for user, or create a new one."""
    if request.method == 'GET':
        projects = Project.objects.filter(owner=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        project = serializer.save()
        logger.info(f"Project created: {project.name} by {request.user.email}")
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail(request, pk):
    """Retrieve, update or delete a project."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    if request.method == 'GET':
        return Response(ProjectSerializer(project).data)

    if request.method == 'PUT':
        serializer = ProjectCreateSerializer(project, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(ProjectSerializer(project).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        name = project.name
        project.delete()
        logger.info(f"Project deleted: {name} by {request.user.email}")
        return Response({'message': f'Project "{name}" deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ─── Template (Frontend) Views ─────────────────────────────────

@login_required
def project_list_view(request):
    """Show all projects for logged-in user."""
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'projects/list.html', {'projects': projects})


@login_required
def project_create_view(request):
    """Create a new project."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        repository_url = request.POST.get('repository_url', '').strip()
        if not name:
            messages.error(request, 'Project name is required.')
            return render(request, 'projects/create.html')
        project = Project.objects.create(
            owner=request.user,
            name=name,
            description=description,
            repository_url=repository_url,
        )
        messages.success(request, f'Project "{project.name}" created successfully!')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/create.html')


@login_required
def project_detail_view(request, pk):
    """Show project details, scans, and stats."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    scans = project.scans.all()
    latest_scan = project.latest_scan
    return render(request, 'projects/detail.html', {
        'project': project,
        'scans': scans,
        'latest_scan': latest_scan,
    })


@login_required
def project_delete_view(request, pk):
    """Delete a project."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('project_list')
    return render(request, 'projects/confirm_delete.html', {'project': project})
