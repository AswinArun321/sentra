import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from projects.models import Project
from scans.models import Scan
from github_integration.models import GitHubConnection
from github_integration.services import GitHubService, GitHubAuthError, GitHubNotFoundError
from github_integration.manifest_detector import ManifestDetector
from github_integration.analysis_service import RepositoryAnalysisService

User = get_user_model()


class ManifestDetectorTests(TestCase):
    """Test repository file detection logic."""

    def test_detect_root_manifests_and_docs(self):
        tree = [
            {'path': 'README.md', 'type': 'blob'},
            {'path': 'LICENSE', 'type': 'blob'},
            {'path': 'requirements.txt', 'type': 'blob'},
            {'path': 'main.py', 'type': 'blob'},
        ]
        result = ManifestDetector.detect(tree)
        self.assertTrue(result['has_manifests'])
        self.assertTrue(result['has_supported_manifests'])
        self.assertEqual(len(result['supported_manifests']), 1)
        self.assertEqual(result['supported_manifests'][0]['path'], 'requirements.txt')
        self.assertEqual(result['supported_manifests'][0]['ecosystem'], 'pypi')
        self.assertTrue(result['supported_manifests'][0]['supported'])
        self.assertIsNotNone(result['readme'])
        self.assertEqual(result['readme']['filename'], 'README.md')
        self.assertIsNotNone(result['license'])
        self.assertEqual(result['license']['filename'], 'LICENSE')

    def test_detect_nested_and_multiple_manifests(self):
        tree = [
            {'path': 'frontend/package.json', 'type': 'blob'},
            {'path': 'backend/requirements.txt', 'type': 'blob'},
            {'path': 'services/api/go.mod', 'type': 'blob'},
            {'path': 'docs/README.txt', 'type': 'blob'},
        ]
        result = ManifestDetector.detect(tree)
        self.assertEqual(result['stats']['total_manifests'], 3)
        self.assertEqual(result['stats']['supported_count'], 2)
        self.assertEqual(result['stats']['unsupported_count'], 1)
        
        supported_paths = [m['path'] for m in result['supported_manifests']]
        self.assertIn('frontend/package.json', supported_paths)
        self.assertIn('backend/requirements.txt', supported_paths)
        
        unsupported_paths = [m['path'] for m in result['unsupported_manifests']]
        self.assertIn('services/api/go.mod', unsupported_paths)

    def test_ignore_vendor_and_node_modules(self):
        tree = [
            {'path': 'node_modules/express/package.json', 'type': 'blob'},
            {'path': 'venv/lib/requirements.txt', 'type': 'blob'},
            {'path': 'package.json', 'type': 'blob'},
        ]
        result = ManifestDetector.detect(tree)
        self.assertEqual(len(result['manifests']), 1)
        self.assertEqual(result['manifests'][0]['path'], 'package.json')

    def test_no_manifest_detection(self):
        tree = [
            {'path': 'README.md', 'type': 'blob'},
            {'path': 'index.html', 'type': 'blob'},
            {'path': 'style.css', 'type': 'blob'},
        ]
        result = ManifestDetector.detect(tree)
        self.assertFalse(result['has_manifests'])
        self.assertFalse(result['has_supported_manifests'])
        self.assertEqual(result['stats']['supported_count'], 0)
        self.assertTrue(result['stats']['has_readme'])


class RepositoryAnalysisServiceTests(TestCase):
    """Test RepositoryAnalysisService orchestration."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='repo_tester',
            email='tester@sentra.dev',
            password='TestPassword123!'
        )
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_user_id=123456,
            github_username='octotester',
            access_token='gho_validtoken123'
        )
        self.project = Project.objects.create(
            owner=self.user,
            name='TestRepo',
            repository_url='https://github.com/octotester/TestRepo',
            source='github',
            github_repo_id=98765,
            github_owner='octotester',
            github_repo_name='TestRepo',
            github_default_branch='main',
        )

    @patch.object(GitHubService, 'get_latest_commit_sha')
    @patch.object(GitHubService, 'get_repository_tree')
    @patch.object(GitHubService, 'get_file_content')
    @patch.object(GitHubService, 'get_repository')
    def test_successful_analysis_requirements_txt(self, mock_get_repo, mock_get_file, mock_get_tree, mock_get_sha):
        mock_get_repo.return_value = {
            'id': 98765,
            'name': 'TestRepo',
            'full_name': 'octotester/TestRepo',
            'default_branch': 'main',
            'license': {'spdx_id': 'MIT', 'name': 'MIT License'},
            'owner': {'login': 'octotester'},
        }
        mock_get_sha.return_value = 'a1b2c3d4e5f67890'
        mock_get_tree.return_value = {
            'sha': 'tree123',
            'tree': [
                {'path': 'README.md', 'type': 'blob'},
                {'path': 'LICENSE', 'type': 'blob'},
                {'path': 'requirements.txt', 'type': 'blob'},
            ]
        }
        mock_get_file.return_value = ("requests==2.28.1\nurllib3==1.26.9\n", "sha_req")

        service = RepositoryAnalysisService()
        result = service.analyze_github_repository(self.user, self.project)

        self.assertTrue(result)
        self.project.refresh_from_db()
        self.assertEqual(self.project.analysis_status, 'COMPLETED')
        self.assertEqual(self.project.github_commit_sha, 'a1b2c3d4e5f67890')
        self.assertEqual(self.project.scans.count(), 1)
        scan = self.project.scans.first()
        self.assertEqual(scan.status, 'COMPLETED')
        self.assertGreater(scan.dependencies.count(), 0)

    @patch.object(GitHubService, 'get_latest_commit_sha')
    @patch.object(GitHubService, 'get_repository_tree')
    @patch.object(GitHubService, 'get_repository')
    def test_no_manifest_repository(self, mock_get_repo, mock_get_tree, mock_get_sha):
        mock_get_repo.return_value = {
            'id': 98765,
            'name': 'TestRepo',
            'default_branch': 'main',
            'owner': {'login': 'octotester'},
        }
        mock_get_sha.return_value = 'commit_no_manifest'
        mock_get_tree.return_value = {
            'sha': 'tree123',
            'tree': [
                {'path': 'README.md', 'type': 'blob'},
                {'path': 'index.html', 'type': 'blob'},
            ]
        }

        service = RepositoryAnalysisService()
        result = service.analyze_github_repository(self.user, self.project)

        self.assertTrue(result)
        self.project.refresh_from_db()
        self.assertEqual(self.project.analysis_status, 'NO_MANIFEST')
        self.assertEqual(self.project.scans.count(), 0)
        self.assertTrue(self.project.detected_files['readme']['present'])

    @patch.object(GitHubService, 'get_file_content')
    @patch.object(GitHubService, 'get_latest_commit_sha')
    @patch.object(GitHubService, 'get_repository_tree')
    @patch.object(GitHubService, 'get_repository')
    def test_readme_quality_analysis_integration(self, mock_get_repo, mock_get_tree, mock_get_sha, mock_get_file):
        mock_get_repo.return_value = {
            'id': 98765,
            'name': 'TestRepo',
            'default_branch': 'main',
            'owner': {'login': 'octotester'},
        }
        mock_get_sha.return_value = 'commit_readme'
        mock_get_tree.return_value = {
            'sha': 'tree123',
            'tree': [
                {'path': 'README.md', 'type': 'blob'},
                {'path': 'requirements.txt', 'type': 'blob'},
            ]
        }
        readme_sample = "# My Awesome Project\n\n## Overview\nA great tool.\n\n## Installation\npip install mytool\n\n## Usage\npython main.py\n"
        req_sample = "requests==2.28.1\n"
        mock_get_file.side_effect = [
            (readme_sample, 'sha_readme'),
            (req_sample, 'sha_req'),
        ]

        service = RepositoryAnalysisService()
        result = service.analyze_github_repository(self.user, self.project)

        self.assertTrue(result)
        self.project.refresh_from_db()
        readme_info = self.project.detected_files.get('readme', {})
        self.assertTrue(readme_info.get('present'))
        self.assertIsNotNone(readme_info.get('score'))
        self.assertGreater(readme_info.get('score'), 0)
        self.assertIn('rating', readme_info)

    @patch.object(GitHubService, 'get_latest_commit_sha')
    @patch.object(GitHubService, 'get_repository_tree')
    @patch.object(GitHubService, 'get_repository')
    def test_large_repository_tree_protection(self, mock_get_repo, mock_get_tree, mock_get_sha):
        from github_integration.analysis_service import MAX_TREE_ENTRIES
        mock_get_repo.return_value = {
            'id': 98765,
            'name': 'HugeRepo',
            'default_branch': 'main',
            'owner': {'login': 'octotester'},
        }
        mock_get_sha.return_value = 'commit_huge'
        # Create tree exceeding limit
        huge_tree = [{'path': f'file_{i}.txt', 'type': 'blob'} for i in range(MAX_TREE_ENTRIES + 10)]
        mock_get_tree.return_value = {'sha': 'huge_tree', 'tree': huge_tree}

        service = RepositoryAnalysisService()
        result = service.analyze_github_repository(self.user, self.project)

        self.assertFalse(result)
        self.project.refresh_from_db()
        self.assertEqual(self.project.analysis_status, 'FAILED')
        self.assertIn("Repository is too large for automatic analysis", self.project.analysis_error)

    @patch.object(GitHubService, 'get_repository')
    def test_github_403_forbidden_handling(self, mock_get_repo):
        from github_integration.services import GitHubAPIError
        mock_get_repo.side_effect = GitHubAPIError("Forbidden", status_code=403)

        service = RepositoryAnalysisService()
        result = service.analyze_github_repository(self.user, self.project)

        self.assertFalse(result)
        self.project.refresh_from_db()
        self.assertEqual(self.project.analysis_status, 'FAILED')
        self.assertEqual(self.project.analysis_error, "SENTRA cannot access this repository. Please check GitHub permissions.")

    def test_manual_project_remains_unaffected(self):
        manual_proj = Project.objects.create(
            owner=self.user,
            name='ManualProject',
            source='manual'
        )
        self.assertEqual(manual_proj.source, 'manual')
        self.assertEqual(manual_proj.analysis_status, 'NONE')
        self.assertIsNone(manual_proj.latest_scan)


class AutomaticAnalysisAPITests(TestCase):
    """Test API endpoints for analysis status, refresh, and user isolation."""

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username='user_a', email='user_a@test.com', password='Password123!')
        self.user_b = User.objects.create_user(username='user_b', email='user_b@test.com', password='Password123!')

        self.conn_a = GitHubConnection.objects.create(
            user=self.user_a,
            github_user_id=111,
            github_username='octo_a',
            access_token='gho_token_a'
        )

        self.project_a = Project.objects.create(
            owner=self.user_a,
            name='ProjectA',
            repository_url='https://github.com/octo_a/ProjectA',
            source='github',
            github_repo_id=101,
            analysis_status='COMPLETED',
            analysis_stage='completed',
            analysis_progress=100,
            github_commit_sha='fedcba9876543210'
        )

    def test_get_analysis_status(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('api_project_analysis_status', kwargs={'pk': self.project_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertEqual(response.data['commit_sha'], 'fedcba9876543210')
        self.assertEqual(response.data['progress'], 100)

    def test_user_isolation_forbidden_access(self):
        # User B cannot access User A's project analysis status
        self.client.force_authenticate(user=self.user_b)
        url = reverse('api_project_analysis_status', kwargs={'pk': self.project_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # User B cannot refresh User A's project analysis
        refresh_url = reverse('api_project_refresh_analysis', kwargs={'pk': self.project_a.pk})
        response_refresh = self.client.post(refresh_url)
        self.assertEqual(response_refresh.status_code, status.HTTP_404_NOT_FOUND)

    def test_refresh_analysis_initiates(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('api_project_refresh_analysis', kwargs={'pk': self.project_a.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ANALYZING')
        self.project_a.refresh_from_db()
        self.assertEqual(self.project_a.analysis_status, 'ANALYZING')
