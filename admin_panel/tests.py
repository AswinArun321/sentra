from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from admin_panel.models import AdminAuditLog, UserAccountStatus, PlatformSetting
from admin_panel.services import AdminAuditService, AdminUserService, AdminSystemHealthService
from projects.models import Project
from scans.models import Scan
from github_integration.models import GitHubConnection

User = get_user_model()


class AdminAccessAndPermissionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()

        # Regular user
        self.regular_user = User.objects.create_user(
            username='developer',
            email='dev@example.com',
            password='Password123!'
        )

        # Staff admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!',
            is_staff=True
        )

        # Superuser
        self.super_user = User.objects.create_superuser(
            username='superadmin',
            email='super@example.com',
            password='SuperPassword123!'
        )

    def test_anonymous_user_redirected(self):
        """Anonymous users must be redirected to login with next parameter."""
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)

    def test_normal_user_denied_access(self):
        """Authenticated non-staff users must receive 403 Forbidden."""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'admin_panel/403.html')

    def test_staff_user_granted_access(self):
        """Authenticated staff users must be able to view the admin console."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/dashboard.html')

    def test_superuser_granted_access(self):
        """Authenticated superusers must be able to view the admin console."""
        self.client.force_login(self.super_user)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_api_admin_requires_staff(self):
        """Admin REST APIs must return 403 to non-staff users and 200 to staff."""
        # Anonymous must return 401 Unauthorized
        res = self.api_client.get(reverse('api_admin_dashboard'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated non-staff user must return 403 Forbidden
        self.api_client.force_authenticate(user=self.regular_user)
        res = self.api_client.get(reverse('api_admin_dashboard'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user
        self.api_client.force_authenticate(user=self.admin_user)
        res = self.api_client.get(reverse('api_admin_dashboard'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', res.data)


class UserManagementAndStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()

        self.admin = User.objects.create_user(
            username='platform_admin',
            email='admin@sentra.local',
            password='AdminPass123!',
            is_staff=True
        )
        self.target_user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='UserPass123!'
        )

    def test_suspend_user_via_service(self):
        """Suspending a user must set is_active=False and record an audit log."""
        status_obj = AdminUserService.set_status(
            admin_user=self.admin,
            target_user=self.target_user,
            new_status='SUSPENDED',
            reason='Suspicious access pattern'
        )
        self.target_user.refresh_from_db()
        self.assertEqual(status_obj.status, 'SUSPENDED')
        self.assertFalse(self.target_user.is_active)

        # Verify audit log
        log = AdminAuditLog.objects.filter(target_user=self.target_user, action='USER_SUSPENDED').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.admin_user, self.admin)
        self.assertIn('Suspicious access pattern', log.description)

    def test_reactivate_suspended_user(self):
        """Reactivating a suspended user must restore is_active=True."""
        AdminUserService.set_status(self.admin, self.target_user, 'SUSPENDED')
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

        AdminUserService.set_status(self.admin, self.target_user, 'ACTIVE')
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)

        log = AdminAuditLog.objects.filter(target_user=self.target_user, action='USER_REACTIVATED').first()
        self.assertIsNotNone(log)

    def test_api_user_suspend_and_activate(self):
        """Admin API allows suspending and activating users with proper authorization."""
        self.api_client.force_authenticate(user=self.admin)
        url = reverse('api_admin_user_action', kwargs={'user_id': self.target_user.id, 'action': 'suspend'})
        res = self.api_client.post(url, {'reason': 'Policy audit'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

        # Activate
        url_act = reverse('api_admin_user_action', kwargs={'user_id': self.target_user.id, 'action': 'activate'})
        res_act = self.api_client.post(url_act, {}, format='json')
        self.assertEqual(res_act.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)

    def test_prevent_self_demotion_for_admin(self):
        """Admin cannot revoke their own staff privileges."""
        with self.assertRaises(PermissionError):
            AdminUserService.toggle_staff(self.admin, self.admin, False)


class TokenProtectionAndSafeSerializationTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.admin = User.objects.create_user(
            username='admin_auditor',
            email='auditor@sentra.local',
            password='AdminPass123!',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='oauth_dev',
            email='oauth@example.com',
            password='SecretPassword123!'
        )
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_user_id=9876543,
            github_username='github_developer',
            access_token='gho_SECRET_SENSITIVE_OAUTH_TOKEN_DO_NOT_EXPOSE'
        )

    def test_user_list_api_never_exposes_password(self):
        """User list API must never contain password hashes or raw passwords."""
        self.api_client.force_authenticate(user=self.admin)
        res = self.api_client.get(reverse('api_admin_users'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data_str = str(res.data)
        self.assertNotIn('password', data_str)
        self.assertNotIn('SecretPassword123!', data_str)

    def test_github_api_never_exposes_access_token(self):
        """GitHub connection monitoring API must never return access_token."""
        self.api_client.force_authenticate(user=self.admin)
        res = self.api_client.get(reverse('api_admin_github'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data_str = str(res.data)
        self.assertNotIn('access_token', data_str)
        self.assertNotIn('gho_SECRET_SENSITIVE_OAUTH_TOKEN_DO_NOT_EXPOSE', data_str)
        self.assertIn('github_developer', data_str)


class AdminAuditLogAndSettingsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.admin = User.objects.create_user(
            username='settings_admin',
            email='settings@sentra.local',
            password='SettingsPass123!',
            is_staff=True
        )

    def test_platform_settings_management(self):
        """Admins can view and safely update platform settings."""
        self.api_client.force_authenticate(user=self.admin)

        # Set value via API
        res = self.api_client.post(
            reverse('api_admin_settings'),
            {'key': 'maintenance_mode', 'value': 'True', 'description': 'Maintenance banner'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(PlatformSetting.get_value('maintenance_mode'), 'True')

        # Check audit log created
        log = AdminAuditLog.objects.filter(action='SETTING_CHANGED').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.admin_user, self.admin)

    def test_system_health_check_safe(self):
        """System health service returns diagnostic components without leaking credentials."""
        health = AdminSystemHealthService.check_health()
        self.assertIn('status', health)
        self.assertIn('database', health['components'])
        self.assertEqual(health['components']['database']['status'], 'HEALTHY')
        self.assertIn('database_metrics', health)

        # Must not contain secret key or credentials
        health_str = str(health)
        self.assertNotIn('SECRET_KEY', health_str)
        self.assertNotIn('django-insecure', health_str)
