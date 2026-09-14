from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project
from .models import GitHubConnection
from .services import (
    GitHubService,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubAPIError,
)
from .documentation import DocumentationAnalyzer
from .readme_generator import ReadmeGenerator

User = get_user_model()


class GitHubServiceTestCase(TestCase):
    def setUp(self):
        self.service = GitHubService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://127.0.0.1:8000/github/callback/",
            api_url="https://api.github.com"
        )

    def test_get_authorization_url(self):
        url, state = self.service.get_authorization_url()
        self.assertTrue(url.startswith("https://github.com/login/oauth/authorize"))
        self.assertIn("client_id=test_client_id", url)
        self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fgithub%2Fcallback%2F", url)
        self.assertIn(f"state={state}", url)
        self.assertIn("scope=read%3Auser%2Crepo", url)

    @patch("requests.post")
    def test_exchange_code_for_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "gho_testtoken12345",
            "token_type": "bearer",
            "scope": "repo,read:user"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        token = self.service.exchange_code_for_token("test_auth_code")
        self.assertEqual(token, "gho_testtoken12345")

    @patch("requests.post")
    def test_exchange_code_for_token_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "bad_verification_code",
            "error_description": "The code passed is incorrect or expired."
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with self.assertRaises(GitHubAuthError):
            self.service.exchange_code_for_token("invalid_code")

    @patch("requests.get")
    def test_get_user_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "login": "octocat",
            "name": "The Octocat",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "html_url": "https://github.com/octocat",
            "public_repos": 8,
        }
        mock_get.return_value = mock_response

        user_info = self.service.get_user("gho_dummy_token")
        self.assertEqual(user_info["id"], 12345)
        self.assertEqual(user_info["login"], "octocat")
        self.assertEqual(user_info["name"], "The Octocat")

    @patch("requests.get")
    def test_get_repositories_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 999,
                "name": "LicenseLens",
                "full_name": "octocat/LicenseLens",
                "description": "Dependency risk auditor",
                "private": False,
                "html_url": "https://github.com/octocat/LicenseLens",
                "default_branch": "main",
                "language": "Python",
                "updated_at": "2026-09-14T09:00:00Z",
                "stargazers_count": 42,
                "forks_count": 5,
                "owner": {"login": "octocat", "avatar_url": "https://github.com/octocat.png"},
            }
        ]
        mock_get.return_value = mock_response

        repos = self.service.get_repositories("gho_dummy_token")
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "LicenseLens")
        self.assertEqual(repos[0]["language"], "Python")
        self.assertFalse(repos[0]["private"])

    def test_normalize_repository_empty_fields(self):
        raw = {"id": 100}
        normalized = GitHubService.normalize_repository(raw)
        self.assertEqual(normalized["id"], 100)
        self.assertEqual(normalized["name"], "")
        self.assertEqual(normalized["description"], "")
        self.assertEqual(normalized["language"], "Unknown")
        self.assertEqual(normalized["default_branch"], "main")


class GitHubOAuthViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="securePassword123!"
        )

    def test_connect_view_redirects_unauthenticated(self):
        response = self.client.get(reverse("github_connect"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    @patch.object(GitHubService, "__init__", lambda self: setattr(self, "client_id", "") or setattr(self, "client_secret", ""))
    def test_connect_view_missing_credentials_redirects_with_error(self):
        self.client.login(email="testuser@example.com", password="securePassword123!")
        response = self.client.get(reverse("github_connect"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("github_repositories"))

    @override_settings(GITHUB_CLIENT_ID="test_client_id", GITHUB_CLIENT_SECRET="test_secret")
    def test_connect_view_sets_state_and_redirects(self):
        self.client.login(email="testuser@example.com", password="securePassword123!")
        response = self.client.get(reverse("github_connect"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://github.com/login/oauth/authorize", response.url)
        self.assertIn("github_oauth_state", self.client.session)

    def test_callback_view_state_mismatch_rejected(self):
        self.client.login(email="testuser@example.com", password="securePassword123!")
        session = self.client.session
        session["github_oauth_state"] = "valid_state_123"
        session.save()

        response = self.client.get(reverse("github_callback") + "?code=testcode&state=wrong_state")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(GitHubConnection.objects.count(), 0)

    @patch.object(GitHubService, "exchange_code_for_token", return_value="gho_mocked_token")
    @patch.object(GitHubService, "get_user", return_value={"id": 88888, "login": "gitdeveloper", "name": "Dev"})
    def test_callback_view_success(self, mock_user, mock_token):
        self.client.login(email="testuser@example.com", password="securePassword123!")
        session = self.client.session
        session["github_oauth_state"] = "matching_state_xyz"
        session.save()

        response = self.client.get(reverse("github_callback") + "?code=good_code&state=matching_state_xyz")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("github_repositories"))

        conn = GitHubConnection.objects.get(user=self.user)
        self.assertEqual(conn.github_username, "gitdeveloper")
        self.assertEqual(conn.github_user_id, 88888)
        self.assertEqual(conn.access_token, "gho_mocked_token")

    def test_disconnect_view_deletes_connection(self):
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=123,
            github_username="dev",
            access_token="gho_token"
        )
        self.assertEqual(GitHubConnection.objects.filter(user=self.user).count(), 1)

        self.client.login(email="testuser@example.com", password="securePassword123!")
        response = self.client.post(reverse("github_disconnect"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GitHubConnection.objects.filter(user=self.user).count(), 0)


class GitHubAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="api_tester",
            email="api_tester@example.com",
            password="testPassword123!"
        )

    def test_api_status_unauthenticated(self):
        response = self.client.get(reverse("api_github_status"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_status_not_connected(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("api_github_status"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["connected"])

    def test_api_status_connected(self):
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=55555,
            github_username="octoapi",
            access_token="gho_secret"
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("api_github_status"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["connected"])
        self.assertEqual(response.data["github_username"], "octoapi")

    def test_api_repositories_not_connected(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("api_github_repositories"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch.object(GitHubService, "get_repositories")
    def test_api_repositories_connected(self, mock_repos):
        mock_repos.return_value = [
            {
                "id": 101,
                "name": "ProjectA",
                "full_name": "user/ProjectA",
                "description": "Awesome repo",
                "private": False,
                "html_url": "https://github.com/user/ProjectA",
                "default_branch": "main",
                "language": "Python",
                "updated_at": "2026-09-14T00:00:00Z",
                "stargazers_count": 10,
                "forks_count": 2,
                "owner": {"login": "user", "avatar_url": ""},
            }
        ]
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=55555,
            github_username="octoapi",
            access_token="gho_secret"
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("api_github_repositories"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "ProjectA")

    @patch.object(GitHubService, "get_repository")
    def test_api_import_repository_creates_project(self, mock_get_repo):
        mock_get_repo.return_value = {
            "id": 777,
            "name": "BackendService",
            "full_name": "user/BackendService",
            "description": "Core Django backend",
            "html_url": "https://github.com/user/BackendService",
            "private": False,
            "default_branch": "main",
            "language": "Python",
            "updated_at": "2026-09-14T00:00:00Z",
            "stargazers_count": 1,
            "forks_count": 0,
        }
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=55555,
            github_username="octoapi",
            access_token="gho_secret"
        )
        self.client.force_authenticate(user=self.user)

        # 1. Import first time -> 201 Created
        response = self.client.post(
            reverse("api_github_import"),
            {"repository_id": 777},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["already_exists"])
        project_id = response.data["project_id"]

        project = Project.objects.get(id=project_id)
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.name, "BackendService")
        self.assertEqual(project.repository_url, "https://github.com/user/BackendService")

        # 2. Import second time -> 200 OK (Duplicate prevention)
        response_dup = self.client.post(
            reverse("api_github_import"),
            {"repository_id": 777},
            format="json"
        )
        self.assertEqual(response_dup.status_code, status.HTTP_200_OK)
        self.assertTrue(response_dup.data["already_exists"])
        self.assertEqual(response_dup.data["project_id"], project_id)
        self.assertEqual(Project.objects.filter(owner=self.user, repository_url="https://github.com/user/BackendService").count(), 1)

    def test_api_disconnect_retains_projects(self):
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=55555,
            github_username="octoapi",
            access_token="gho_secret"
        )
        project = Project.objects.create(
            owner=self.user,
            name="SampleApp",
            repository_url="https://github.com/octoapi/SampleApp"
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("api_github_disconnect"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["disconnected"])

        # Connection should be deleted
        self.assertFalse(GitHubConnection.objects.filter(user=self.user).exists())
        # Project should still exist!
        self.assertTrue(Project.objects.filter(id=project.id).exists())


class DocumentationAnalyzerTestCase(TestCase):
    def setUp(self):
        self.analyzer = DocumentationAnalyzer()

    def test_check_readme_present(self):
        with patch.object(GitHubService, "get_contents") as mock_contents:
            mock_contents.return_value = [
                {"name": "manage.py", "type": "file"},
                {"name": "README.md", "path": "README.md", "sha": "sha_readme_123", "size": 1024},
            ]
            res = self.analyzer.check_readme("token", 123)
            self.assertTrue(res["exists"])
            self.assertEqual(res["status"], "PRESENT")
            self.assertEqual(res["filename"], "README.md")
            self.assertEqual(res["sha"], "sha_readme_123")

    def test_check_readme_case_insensitive(self):
        with patch.object(GitHubService, "get_contents") as mock_contents:
            mock_contents.return_value = [
                {"name": "readme.txt", "path": "readme.txt", "sha": "sha_txt_456"},
            ]
            res = self.analyzer.check_readme("token", 123)
            self.assertTrue(res["exists"])
            self.assertEqual(res["filename"], "readme.txt")

    def test_check_readme_missing(self):
        with patch.object(GitHubService, "get_contents") as mock_contents:
            mock_contents.return_value = [
                {"name": "src", "type": "dir"},
                {"name": "package.json", "type": "file"},
            ]
            res = self.analyzer.check_readme("token", 123)
            self.assertFalse(res["exists"])
            self.assertEqual(res["status"], "MISSING")
            self.assertIsNone(res["filename"])

    def test_analyze_readme_text_full_score(self):
        full_markdown = """# LicenseLens Security Auditor

## Overview
A comprehensive vulnerability and dependency auditor for modern applications.

## Key Features
- Automated dependency scanning
- License compliance detection
- Risk score calculation

## Requirements
- Python 3.11+
- SQLite / PostgreSQL

## Installation & Setup
Run pip install -r requirements.txt to install dependencies.

## Configuration
Configure environment variables using .env:
SECRET_KEY=dev-secret

## Usage
Run python manage.py runserver to launch application.

## Project Structure
```text
app/
├── accounts/
└── scanner/
```

## Contributing
Submit pull requests to contribute to the repository.

## License
Distributed under the MIT License.
"""
        result = self.analyzer.analyze_readme_text(full_markdown)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["rating"], "Excellent")
        self.assertEqual(len(result["recommendations"]), 0)

    def test_analyze_readme_text_partial_score(self):
        partial_markdown = """# Simple Utility

## Installation
Run pip install mytool
"""
        result = self.analyzer.analyze_readme_text(partial_markdown)
        self.assertGreater(result["score"], 0)
        self.assertLess(result["score"], 100)
        self.assertTrue(result["sections"]["title"])
        self.assertTrue(result["sections"]["installation"])
        self.assertFalse(result["sections"]["license"])
        self.assertIn("Add licensing information stating how this project is licensed.", result["recommendations"])

    def test_analyze_readme_text_empty(self):
        result = self.analyzer.analyze_readme_text("")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["rating"], "Very Poor / Missing")
        self.assertEqual(len(result["recommendations"]), 10)


class ReadmeGeneratorTestCase(TestCase):
    def setUp(self):
        self.generator = ReadmeGenerator()

    @patch.object(GitHubService, "get_repository")
    @patch.object(GitHubService, "get_contents")
    def test_generate_readme_django(self, mock_contents, mock_repo):
        mock_repo.return_value = {
            "name": "EcommerceBackend",
            "full_name": "developer/EcommerceBackend",
            "description": "High performance ecommerce API",
            "language": "Python",
            "html_url": "https://github.com/developer/EcommerceBackend",
            "default_branch": "main",
        }
        mock_contents.return_value = [
            {"name": "manage.py", "type": "file"},
            {"name": "requirements.txt", "type": "file"},
            {"name": "accounts", "type": "dir"},
        ]

        result = self.generator.generate_readme("dummy_token", 987)
        self.assertEqual(result["repository"], "EcommerceBackend")
        self.assertIn("Django", result["frameworks"])
        content = result["content"]
        self.assertIn("# EcommerceBackend", content)
        self.assertIn("manage.py runserver", content)
        self.assertIn("requirements.txt", content)
        self.assertIn("## Installation", content)
        self.assertIn("## License", content)


class DocumentationAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="doc_tester",
            email="doc_tester@example.com",
            password="testPassword123!"
        )
        GitHubConnection.objects.create(
            user=self.user,
            github_user_id=777888,
            github_username="doctestuser",
            access_token="gho_test_token"
        )
        self.client.force_authenticate(user=self.user)

    @patch.object(DocumentationAnalyzer, "analyze_repository")
    def test_api_documentation_success(self, mock_analyze):
        mock_analyze.return_value = {
            "exists": True,
            "filename": "README.md",
            "score": 85,
            "rating": "Good",
            "sections": {"title": True},
            "recommendations": ["Add usage section."],
        }
        response = self.client.get(reverse("api_github_documentation", kwargs={"repo_id": 101}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], 85)
        self.assertEqual(response.data["rating"], "Good")

    @patch.object(DocumentationAnalyzer, "check_readme")
    def test_api_readme_missing_returns_404(self, mock_check):
        mock_check.return_value = {"exists": False}
        response = self.client.get(reverse("api_github_readme", kwargs={"repo_id": 101}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch.object(DocumentationAnalyzer, "check_readme")
    def test_api_commit_readme_prevents_accidental_overwrite(self, mock_check):
        mock_check.return_value = {"exists": True, "filename": "README.md", "sha": "existing_sha"}
        response = self.client.post(
            reverse("api_github_commit_readme", kwargs={"repo_id": 101}),
            {"content": "# New README", "overwrite": False},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data["already_exists"])

    @patch.object(DocumentationAnalyzer, "check_readme")
    @patch.object(GitHubService, "commit_file")
    def test_api_commit_readme_success(self, mock_commit, mock_check):
        mock_check.return_value = {"exists": False}
        mock_commit.return_value = {
            "commit": {"sha": "new_commit_sha_123"},
            "content": {"html_url": "https://github.com/user/repo/blob/main/README.md"},
        }
        response = self.client.post(
            reverse("api_github_commit_readme", kwargs={"repo_id": 101}),
            {"content": "# Fresh README content", "commit_message": "Add README.md"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["committed"])
        self.assertEqual(response.data["commit_sha"], "new_commit_sha_123")


class MultiUserGitHubIsolationTestCase(TestCase):
    """
    Automated test suite verifying multi-user GitHub account isolation as specified in
    Multi_User_GitHub_Account_Isolation.md.
    """

    def setUp(self):
        self.client_a = APIClient()
        self.client_b = APIClient()

        self.user_a = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password123"
        )
        self.user_b = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="password123"
        )

        self.client_a.force_authenticate(user=self.user_a)
        self.client_b.force_authenticate(user=self.user_b)

        # Connection for User A
        self.conn_a = GitHubConnection.objects.create(
            user=self.user_a,
            github_user_id=1001,
            github_username="alice-gh",
            access_token="gho_token_alice"
        )

        # Connection for User B
        self.conn_b = GitHubConnection.objects.create(
            user=self.user_b,
            github_user_id=2002,
            github_username="bob-gh",
            access_token="gho_token_bob"
        )

    def test_user_a_and_user_b_status_isolated(self):
        """User A sees Alice's GitHub username; User B sees Bob's."""
        resp_a = self.client_a.get(reverse("api_github_status"))
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_a.data["connected"])
        self.assertEqual(resp_a.data["github_username"], "alice-gh")

        resp_b = self.client_b.get(reverse("api_github_status"))
        self.assertEqual(resp_b.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_b.data["connected"])
        self.assertEqual(resp_b.data["github_username"], "bob-gh")

    @patch("github_integration.services.GitHubService.get_repositories")
    def test_repository_isolation_between_users(self, mock_get_repos):
        """Repositories returned for User A use Token A; Repositories for User B use Token B."""
        def side_effect(access_token, **kwargs):
            if access_token == "gho_token_alice":
                return [{
                    "id": 11, "name": "alice-repo", "full_name": "alice-gh/alice-repo",
                    "description": "", "private": False, "html_url": "https://github.com/alice-gh/alice-repo",
                    "default_branch": "main", "language": "Python", "updated_at": "",
                    "stargazers_count": 0, "forks_count": 0
                }]
            elif access_token == "gho_token_bob":
                return [{
                    "id": 22, "name": "bob-repo", "full_name": "bob-gh/bob-repo",
                    "description": "", "private": False, "html_url": "https://github.com/bob-gh/bob-repo",
                    "default_branch": "main", "language": "Python", "updated_at": "",
                    "stargazers_count": 0, "forks_count": 0
                }]
            return []

        mock_get_repos.side_effect = side_effect

        resp_a = self.client_a.get(reverse("api_github_repositories"))
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_a.data["count"], 1)
        self.assertEqual(resp_a.data["results"][0]["name"], "alice-repo")

        resp_b = self.client_b.get(reverse("api_github_repositories"))
        self.assertEqual(resp_b.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_b.data["count"], 1)
        self.assertEqual(resp_b.data["results"][0]["name"], "bob-repo")

    @patch("github_integration.services.GitHubService.get_user")
    @patch("github_integration.services.GitHubService.exchange_code_for_token")
    def test_account_conflict_prevention_on_callback(self, mock_token, mock_user):
        """User B cannot connect Alice's GitHub account if Alice already has it connected."""
        c = Client()
        c.force_login(self.user_b)
        session = c.session
        session["github_oauth_state"] = "valid_state_123"
        session.save()

        mock_token.return_value = "gho_new_token"
        mock_user.return_value = {
            "id": 1001,  # Same GitHub ID already linked to Alice!
            "login": "alice-gh",
            "name": "Alice GitHub",
        }

        response = c.get(reverse("github_callback") + "?code=auth_code_xyz&state=valid_state_123")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

        # Confirm Bob's connection was NOT overwritten with Alice's ID
        conn_b_after = GitHubConnection.objects.get(user=self.user_b)
        self.assertEqual(conn_b_after.github_user_id, 2002)
        self.assertEqual(conn_b_after.github_username, "bob-gh")

    @patch("github_integration.services.GitHubService.get_repository")
    def test_import_isolation_between_users(self, mock_get_repo):
        """Projects imported by User A belong only to User A."""
        mock_get_repo.return_value = {
            "id": 500,
            "name": "SuperProject",
            "description": "Awesome repo",
            "html_url": "https://github.com/alice-gh/SuperProject"
        }

        resp = self.client_a.post(
            reverse("api_github_import"),
            {"repository_id": 500},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        project_id = resp.data["project_id"]

        # Verify project is owned by User A
        p = Project.objects.get(id=project_id)
        self.assertEqual(p.owner, self.user_a)

        # User B should NOT see Project A in User B's project list
        self.assertEqual(Project.objects.filter(owner=self.user_b).count(), 0)

    def test_disconnect_isolation(self):
        """Disconnecting User B leaves User A's connection active."""
        resp = self.client_b.post(reverse("api_github_disconnect"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # User B is now disconnected
        self.assertFalse(GitHubConnection.objects.filter(user=self.user_b).exists())

        # User A is still connected
        self.assertTrue(GitHubConnection.objects.filter(user=self.user_a).exists())
        conn_a = GitHubConnection.objects.get(user=self.user_a)
        self.assertEqual(conn_a.github_username, "alice-gh")

    def test_new_user_starts_disconnected(self):
        """A new user has no connection and receives disconnected status."""
        new_user = User.objects.create_user(
            username="charlie",
            email="charlie@example.com",
            password="password123"
        )
        c = APIClient()
        c.force_authenticate(user=new_user)
        resp = c.get(reverse("api_github_status"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["connected"])
        self.assertIsNone(resp.data["github_username"])

    def test_service_user_bound_helpers(self):
        """GitHubService user-bound helper methods function correctly."""
        service = GitHubService()
        conn = service.get_connection_for_user(self.user_a)
        self.assertIsNotNone(conn)
        self.assertEqual(conn.github_username, "alice-gh")

        with patch.object(service, "get_repositories", return_value=[{"name": "test-repo"}]):
            repos = service.get_repositories_for_user(self.user_a)
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0]["name"], "test-repo")

