import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from projects.models import Project
from .models import GitHubConnection
from .services import (
    GitHubService,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
)
from .serializers import (
    GitHubConnectionStatusSerializer,
    GitHubRepositorySerializer,
    GitHubImportSerializer,
    GitHubReadmeCommitSerializer,
)
from .documentation import DocumentationAnalyzer
from .readme_generator import ReadmeGenerator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Template Views
# ---------------------------------------------------------

@login_required
def github_connect_view(request):
    """
    Start GitHub OAuth authorization flow.
    Generates CSRF state token, stores it in session, and redirects to GitHub.
    """
    service = GitHubService()
    if not service.client_id or not service.client_secret:
        messages.error(
            request,
            "GitHub OAuth credentials are not configured yet. "
            "Please add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to your .env file."
        )
        return redirect('github_repositories')

    try:
        auth_url, state = service.get_authorization_url()
        request.session['github_oauth_state'] = state
        return redirect(auth_url)
    except Exception as e:
        logger.error("Failed to generate GitHub authorization URL: %s", str(e))
        messages.error(request, "GitHub integration is not properly configured. Please check your settings.")
        return redirect('profile')


@login_required
def github_callback_view(request):
    """
    Handle GitHub OAuth callback.
    Validates CSRF state, exchanges authorization code for access token,
    retrieves GitHub user details, and creates/updates GitHubConnection.
    """
    expected_state = request.session.pop('github_oauth_state', None)
    received_state = request.GET.get('state')

    # 1. State Validation
    if not expected_state or not received_state or expected_state != received_state:
        logger.warning("GitHub OAuth state mismatch or missing for user %s", request.user.username)
        messages.error(request, "GitHub authentication could not be verified. Please try connecting again.")
        return redirect('profile')

    # 2. Check for user cancellation or errors
    if 'error' in request.GET:
        error_msg = request.GET.get('error_description', request.GET.get('error'))
        logger.info("GitHub authorization denied/cancelled: %s", error_msg)
        messages.warning(request, "GitHub authorization was cancelled.")
        return redirect('profile')

    code = request.GET.get('code')
    if not code:
        messages.error(request, "Authorization code was not provided by GitHub.")
        return redirect('profile')

    service = GitHubService()

    # 3. Exchange code for access token
    try:
        access_token = service.exchange_code_for_token(code)
    except GitHubAuthError as e:
        logger.error("OAuth token exchange error: %s", str(e))
        messages.error(request, f"Failed to authenticate with GitHub: {str(e)}")
        return redirect('profile')
    except Exception as e:
        logger.error("Unexpected error in token exchange: %s", str(e))
        messages.error(request, "Unable to complete GitHub authorization. Please try again.")
        return redirect('profile')

    # 4. Fetch GitHub user profile
    try:
        gh_user = service.get_user(access_token)
    except GitHubAPIError as e:
        logger.error("Failed to fetch GitHub user details: %s", str(e))
        messages.error(request, f"Unable to retrieve GitHub profile: {str(e)}")
        return redirect('profile')

    # 5. Prevent account collision: Check if another LicenseLens user already connected this GitHub account
    existing_connection = GitHubConnection.objects.filter(
        github_user_id=gh_user['id']
    ).exclude(user=request.user).first()

    if existing_connection:
        logger.warning(
            "GitHub account @%s (ID %s) is already connected to user %s",
            gh_user['login'], gh_user['id'], existing_connection.user.username
        )
        messages.error(request, "This GitHub account is already connected to another LicenseLens account.")
        return redirect('profile')

    # 6. Create or update GitHubConnection record for current user
    connection, created = GitHubConnection.objects.update_or_create(
        user=request.user,
        defaults={
            'github_user_id': gh_user['id'],
            'github_username': gh_user['login'],
            'access_token': access_token,
        }
    )

    logger.info("GitHub account @%s connected for LicenseLens user %s", gh_user['login'], request.user.username)
    messages.success(request, f"Connected to GitHub as @{gh_user['login']}!")
    return redirect('github_repositories')


@login_required
def github_repositories_view(request):
    """
    Render GitHub Repositories browser page.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    service = GitHubService()
    has_credentials = bool(service.client_id and service.client_secret)
    return render(request, 'github/repositories.html', {
        'connection': connection,
        'is_connected': connection is not None,
        'has_credentials': has_credentials,
    })


@login_required
def github_documentation_view(request, repo_id):
    """
    Render repository README Documentation Analyzer & Recommendation page.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        messages.warning(request, "Please connect your GitHub account to analyze repository documentation.")
        return redirect('github_repositories')

    service = GitHubService()
    try:
        repo = service.get_repository(connection.access_token, repo_id)
    except GitHubAuthError as e:
        connection.delete()
        messages.error(request, f"GitHub token error: {str(e)}. Please reconnect.")
        return redirect('github_repositories')
    except Exception as e:
        logger.error("Failed to load repository %s for documentation: %s", repo_id, str(e))
        messages.error(request, "Unable to access repository details from GitHub.")
        return redirect('github_repositories')

    return render(request, 'github/documentation.html', {
        'connection': connection,
        'repository': repo,
        'repo_id': repo_id,
    })


@login_required
def github_disconnect_view(request):
    """
    Template disconnect action (handles POST or GET with confirmation redirect).
    """
    if request.method == 'POST':
        deleted_count, _ = GitHubConnection.objects.filter(user=request.user).delete()
        if deleted_count > 0:
            logger.info("GitHub account disconnected for user %s", request.user.username)
            messages.success(request, "GitHub account disconnected. Existing projects have been retained.")
        else:
            messages.info(request, "No GitHub account was connected.")
        return redirect('profile')
    return redirect('profile')


# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_status(request):
    """
    GET /api/github/status/
    Returns current user's GitHub connection status.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if connection:
        data = {
            'connected': True,
            'github_username': connection.github_username,
            'github_user_id': connection.github_user_id,
            'connected_at': connection.connected_at,
        }
    else:
        data = {
            'connected': False,
            'github_username': None,
            'github_user_id': None,
            'connected_at': None,
        }
    serializer = GitHubConnectionStatusSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_repositories(request):
    """
    GET /api/github/repositories/
    Returns repositories belonging to or accessible to the connected GitHub account.
    Supports query parameters: page, per_page, sort, direction, search.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response(
            {'error': 'GitHub account is not connected.', 'connected': False},
            status=status.HTTP_400_BAD_REQUEST
        )

    page = request.GET.get('page', 1)
    try:
        page = max(1, int(page))
    except ValueError:
        page = 1

    per_page = request.GET.get('per_page', 30)
    try:
        per_page = max(1, min(100, int(per_page)))
    except ValueError:
        per_page = 30

    sort = request.GET.get('sort', 'updated')
    direction = request.GET.get('direction', 'desc')
    search_query = request.GET.get('search', '').strip().lower()

    service = GitHubService()
    try:
        repos = service.get_repositories(
            access_token=connection.access_token,
            page=page,
            per_page=per_page,
            sort=sort,
            direction=direction,
        )
    except GitHubAuthError as e:
        logger.warning("Token expired or revoked for user %s: %s", request.user.username, str(e))
        # Invalidate local connection if token is rejected by GitHub
        connection.delete()
        return Response(
            {'error': 'GitHub access token has expired or was revoked. Please reconnect your account.', 'connected': False},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except GitHubRateLimitError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    # Optional search filtering
    if search_query:
        repos = [
            r for r in repos
            if search_query in r.get('name', '').lower()
            or search_query in r.get('full_name', '').lower()
            or search_query in (r.get('description') or '').lower()
            or search_query in (r.get('language') or '').lower()
        ]

    # Annotate with whether project is already imported by this user
    existing_urls = set(Project.objects.filter(owner=request.user).values_list('repository_url', flat=True))
    for r in repos:
        r['already_imported'] = r.get('html_url') in existing_urls

    serializer = GitHubRepositorySerializer(repos, many=True)
    return Response({
        'count': len(serializer.data),
        'page': page,
        'per_page': per_page,
        'results': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_repository_detail(request, repo_id):
    """
    GET /api/github/repositories/<repo_id>/
    Returns detailed info for one repository.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response(
            {'error': 'GitHub account is not connected.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = GitHubService()
    try:
        repo = service.get_repository(connection.access_token, repo_id)
    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubNotFoundError:
        return Response({'error': 'Repository not found or no longer accessible.'}, status=status.HTTP_404_NOT_FOUND)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    existing_project = Project.objects.filter(owner=request.user, repository_url=repo['html_url']).first()
    repo['already_imported'] = existing_project is not None
    if existing_project:
        repo['project_id'] = existing_project.id

    serializer = GitHubRepositorySerializer(repo)
    return Response(serializer.data, status=status.HTTP_200_OK)


def _import_repo(request, repo_id):
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response(
            {'error': 'GitHub account is not connected.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = GitHubService()

    # Verify repository access via GitHub API
    try:
        repo = service.get_repository(connection.access_token, repo_id)
    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubNotFoundError:
        return Response({'error': 'Repository could not be found or is no longer accessible.'}, status=status.HTTP_404_NOT_FOUND)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    html_url = repo.get('html_url')
    name = repo.get('name') or f"repo-{repo_id}"
    description = repo.get('description') or ''

    # Check for duplicate project
    existing_project = Project.objects.filter(
        owner=request.user,
        repository_url=html_url
    ).first()

    if existing_project:
        return Response({
            'message': 'Repository already imported.',
            'project_id': existing_project.id,
            'project_name': existing_project.name,
            'project_url': reverse('project_detail', kwargs={'pk': existing_project.pk}),
            'already_exists': True,
            'analysis_status': existing_project.analysis_status,
        }, status=status.HTTP_200_OK)

    # Create new Project reusing existing Project architecture with GitHub metadata
    project = Project.objects.create(
        owner=request.user,
        name=name,
        description=description,
        repository_url=html_url,
        source='github',
        github_repo_id=repo.get('id'),
        github_owner=repo.get('owner', {}).get('login', ''),
        github_repo_name=name,
        github_default_branch=repo.get('default_branch', 'main'),
        analysis_status='ANALYZING',
    )

    logger.info("Imported GitHub repository %s as Project %s for user %s", html_url, project.id, request.user.username)

    # Trigger automatic analysis in background
    try:
        from .analysis_service import trigger_analysis_in_background
        trigger_analysis_in_background(request.user, project)
    except Exception as e:
        logger.warning("Could not launch automatic analysis in background: %s", str(e))

    return Response({
        'message': 'Repository imported successfully.',
        'project_id': project.id,
        'project_name': project.name,
        'project_url': reverse('project_detail', kwargs={'pk': project.pk}),
        'already_exists': False,
        'analysis_status': project.analysis_status,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_github_import(request):
    """
    POST /api/github/import/
    Import a repository as a LicenseLens Project via request body { "repository_id": ... }.
    """
    serializer = GitHubImportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return _import_repo(request, serializer.validated_data['repository_id'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_github_import_by_id(request, repo_id):
    """
    POST /api/github/repositories/<repo_id>/import/
    Import a repository as a LicenseLens Project using repo_id from URL path.
    """
    return _import_repo(request, repo_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_github_disconnect(request):
    """
    POST /api/github/disconnect/
    Deletes the GitHubConnection for the authenticated user.
    Retains all existing projects and scans.
    """
    deleted_count, _ = GitHubConnection.objects.filter(user=request.user).delete()
    logger.info("GitHub account disconnected for user %s via API", request.user.username)
    return Response({
        'message': 'GitHub account disconnected successfully.',
        'disconnected': True,
    }, status=status.HTTP_200_OK)


# ---------------------------------------------------------
# Documentation & README Endpoints
# ---------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_documentation(request, repo_id):
    """
    GET /api/github/repositories/<repo_id>/documentation/
    Analyzes repository root for README, calculates 100-pt score and recommendations.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response({'error': 'GitHub account is not connected.'}, status=status.HTTP_400_BAD_REQUEST)

    analyzer = DocumentationAnalyzer()
    try:
        analysis = analyzer.analyze_repository(connection.access_token, repo_id)
        return Response(analysis, status=status.HTTP_200_OK)
    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_readme(request, repo_id):
    """
    GET /api/github/repositories/<repo_id>/readme/
    Returns decoded content of existing README file if present.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response({'error': 'GitHub account is not connected.'}, status=status.HTTP_400_BAD_REQUEST)

    analyzer = DocumentationAnalyzer()
    try:
        check = analyzer.check_readme(connection.access_token, repo_id)
        if not check['exists']:
            return Response({'error': 'No README found in repository.', 'exists': False}, status=status.HTTP_404_NOT_FOUND)

        content, sha = analyzer.get_readme_content(connection.access_token, repo_id, check['path'])
        return Response({
            'exists': True,
            'filename': check['filename'],
            'path': check['path'],
            'sha': sha,
            'content': content,
        }, status=status.HTTP_200_OK)
    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_github_generate_readme(request, repo_id):
    """
    POST /api/github/repositories/<repo_id>/readme/generate/
    Synthesizes standard tailored README.md based on repository structure & framework detection.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response({'error': 'GitHub account is not connected.'}, status=status.HTTP_400_BAD_REQUEST)

    generator = ReadmeGenerator()
    try:
        generated = generator.generate_readme(connection.access_token, repo_id)
        return Response(generated, status=status.HTTP_200_OK)
    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_github_commit_readme(request, repo_id):
    """
    POST /api/github/repositories/<repo_id>/readme/commit/
    Commits README.md to the repository on GitHub with user confirmation.
    Prevents accidental overwrites of existing READMEs unless overwrite=True.
    """
    connection = GitHubConnection.objects.filter(user=request.user).first()
    if not connection:
        return Response({'error': 'GitHub account is not connected.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = GitHubReadmeCommitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    content = serializer.validated_data['content']
    commit_message = serializer.validated_data.get('commit_message') or 'Add README.md'
    overwrite = serializer.validated_data.get('overwrite', False)

    analyzer = DocumentationAnalyzer()
    service = GitHubService()

    try:
        readme_info = analyzer.check_readme(connection.access_token, repo_id)

        # Protection against accidental overwrite
        if readme_info['exists'] and not overwrite:
            return Response({
                'error': 'A README already exists in this repository. Overwrite must be explicitly confirmed.',
                'already_exists': True,
                'filename': readme_info['filename'],
            }, status=status.HTTP_400_BAD_REQUEST)

        filename = readme_info['filename'] if (readme_info['exists'] and overwrite) else 'README.md'
        sha = readme_info.get('sha') if (readme_info['exists'] and overwrite) else None

        commit_result = service.commit_file(
            access_token=connection.access_token,
            repo_identifier=repo_id,
            path=filename,
            content_str=content,
            commit_message=commit_message,
            sha=sha,
        )

        logger.info("README committed to repository %s by user %s", repo_id, request.user.username)

        content_meta = commit_result.get('content', {})
        return Response({
            'message': f'{filename} added successfully to repository.',
            'committed': True,
            'filename': filename,
            'commit_sha': commit_result.get('commit', {}).get('sha', ''),
            'html_url': content_meta.get('html_url', ''),
        }, status=status.HTTP_200_OK)

    except GitHubAuthError as e:
        connection.delete()
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except GitHubAPIError as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
