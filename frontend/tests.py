from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from projects.models import Project
from scans.models import Scan
from dependencies.models import Dependency
from vulnerabilities.models import Vulnerability
from github_integration.models import GitHubConnection
from frontend.services import DashboardService

User = get_user_model()


class DashboardAPITestCase(TestCase):
    """
    Tests for the Dashboard REST API and DashboardService.
    Ensures authentication, user data isolation, and accurate calculations.
    """

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='user_a', email='a@example.com', password='password123')
        self.user_b = User.objects.create_user(username='user_b', email='b@example.com', password='password123')

        # Project for User A
        self.proj_a = Project.objects.create(
            owner=self.user_a,
            name='AlphaProject',
            description='Test project A'
        )

        # Scan for User A
        self.scan_a = Scan.objects.create(
            project=self.proj_a,
            status='COMPLETED',
            source_type='requirements.txt',
            risk_score=65.0,
            risk_level='HIGH'
        )

        # Dependencies for User A
        self.dep_a1 = Dependency.objects.create(
            scan=self.scan_a,
            name='requests',
            version='2.25.0',
            ecosystem='PyPI',
            license='GPL-3.0',
            license_category='STRONG_COPYLEFT'
        )
        self.dep_a2 = Dependency.objects.create(
            scan=self.scan_a,
            name='flask',
            version='1.1.2',
            ecosystem='PyPI',
            license='MIT',
            license_category='PERMISSIVE'
        )

        # Vulnerabilities for User A
        self.vuln_a1 = Vulnerability.objects.create(
            dependency=self.dep_a1,
            identifier='CVE-2023-1111',
            severity='CRITICAL',
            cvss_score=9.8
        )
        self.vuln_a2 = Vulnerability.objects.create(
            dependency=self.dep_a2,
            identifier='CVE-2023-2222',
            severity='HIGH',
            cvss_score=7.5
        )

        # Project & Scan for User B
        self.proj_b = Project.objects.create(
            owner=self.user_b,
            name='BetaProject',
            description='Test project B'
        )
        self.scan_b = Scan.objects.create(
            project=self.proj_b,
            status='COMPLETED',
            risk_score=10.0,
            risk_level='LOW'
        )
        self.dep_b1 = Dependency.objects.create(
            scan=self.scan_b,
            name='express',
            version='4.17.1',
            ecosystem='npm',
            license='MIT',
            license_category='PERMISSIVE'
        )

    def test_unauthenticated_dashboard_api(self):
        """Unauthenticated requests to /api/dashboard/overview/ must be denied."""
        response = self.client.get(reverse('api_dashboard_overview'))
        self.assertIn(response.status_code, [401, 403])

    def test_authenticated_dashboard_api(self):
        """Authenticated requests return HTTP 200 with required dashboard sections."""
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('api_dashboard_overview'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('summary', data)
        self.assertIn('vulnerabilities', data)
        self.assertIn('project_health', data)
        self.assertIn('attention_required', data)
        self.assertIn('recent_scans', data)
        self.assertIn('github', data)
        self.assertIn('repository_health', data)

    def test_user_data_isolation(self):
        """User A must not see User B's metrics, and User B must not see User A's."""
        # User A metrics
        self.client.force_login(self.user_a)
        resp_a = self.client.get(reverse('api_dashboard_overview'))
        data_a = resp_a.json()

        self.assertEqual(data_a['summary']['projects'], 1)
        self.assertEqual(data_a['summary']['vulnerabilities'], 2)
        self.assertEqual(data_a['summary']['critical_vulnerabilities'], 1)
        self.assertEqual(data_a['summary']['high_vulnerabilities'], 1)
        self.assertEqual(data_a['summary']['license_risks'], 1)

        # User B metrics
        self.client.force_login(self.user_b)
        resp_b = self.client.get(reverse('api_dashboard_overview'))
        data_b = resp_b.json()

        self.assertEqual(data_b['summary']['projects'], 1)
        self.assertEqual(data_b['summary']['vulnerabilities'], 0)
        self.assertEqual(data_b['summary']['critical_vulnerabilities'], 0)
        self.assertEqual(data_b['summary']['high_vulnerabilities'], 0)
        self.assertEqual(data_b['summary']['license_risks'], 0)
        self.assertEqual(data_b['summary']['security_score'], 90)

    def test_attention_items_prioritization(self):
        """Attention items are generated and prioritized by severity."""
        service = DashboardService()
        items = service.get_attention_items(self.user_a)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['project_name'], 'AlphaProject')
        self.assertEqual(items[0]['severity'], 'CRITICAL')
        self.assertTrue(any('Critical' in r for r in items[0]['reasons']))
        self.assertTrue(any('License' in r for r in items[0]['reasons']))

        # User B has a clean low-risk project, attention list should be empty
        items_b = service.get_attention_items(self.user_b)
        self.assertEqual(len(items_b), 0)

    def test_project_health_classification(self):
        """Projects are classified into excellent, good, needs_attention, and critical."""
        service = DashboardService()
        health_a = service.get_project_health(self.user_a)
        self.assertEqual(health_a['critical'], 1)  # Due to critical vulnerability & risk score 65
        self.assertEqual(health_a['excellent'], 0)

        health_b = service.get_project_health(self.user_b)
        self.assertEqual(health_b['excellent'], 1)
        self.assertEqual(health_b['critical'], 0)

    def test_github_status_disconnected_and_connected(self):
        """GitHub status reflects disconnected and connected states accurately."""
        service = DashboardService()
        status_disconnected = service.get_github_status(self.user_a)
        self.assertFalse(status_disconnected['connected'])
        self.assertIsNone(status_disconnected['username'])

        # Connect user A
        GitHubConnection.objects.create(
            user=self.user_a,
            github_user_id=123456,
            github_username='octodev',
            access_token='gho_fake_token_123'
        )

        with patch('github_integration.services.GitHubService.get_repositories', return_value=[{'id': 1, 'name': 'repo1', 'license': {'key': 'mit'}}]):
            status_connected = service.get_github_status(self.user_a)
            self.assertTrue(status_connected['connected'])
            self.assertEqual(status_connected['username'], 'octodev')
            self.assertEqual(status_connected['repository_count'], 1)

    def test_dashboard_template_view(self):
        """Main dashboard view renders cleanly with status 200."""
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertContains(response, 'Security & Compliance Overview')
        self.assertContains(response, 'AlphaProject')
