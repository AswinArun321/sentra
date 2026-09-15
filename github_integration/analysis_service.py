"""
LicenseLens — Automatic GitHub Repository Analysis Service.
Coordinates repository metadata retrieval, tree fetching, manifest detection,
file retrieval, and execution of the existing scan pipeline.
"""

import os
import logging
import threading
from django.core.files.base import ContentFile
from django.utils import timezone
from scans.models import Scan
from scanner.orchestrator import run_scan
from .models import GitHubConnection
from .services import (
    GitHubService,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
)
from .manifest_detector import ManifestDetector
from .documentation import DocumentationAnalyzer

logger = logging.getLogger(__name__)


MAX_TREE_ENTRIES = 20000
MAX_MANIFEST_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_MANIFESTS = 15


class RepositoryAnalysisService:
    """
    Orchestrates automatic inspection and scanning of imported GitHub repositories.
    """

    def __init__(self, service=None):
        self.service = service or GitHubService()

    def analyze_github_repository(self, user, project):
        """
        Main entry point for repository analysis.
        Uses the authenticated user's GitHub connection.
        Updates project.analysis_status and related metadata fields.
        """
        connection = GitHubConnection.objects.filter(user=user).first()
        if not connection:
            error_msg = "No connected GitHub account found for this user."
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            project.analysis_error = error_msg
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            logger.warning("Automatic analysis aborted for project %s: %s", project.id, error_msg)
            return False

        access_token = connection.access_token

        try:
            # Stage 1: Fetch repository metadata
            project.analysis_status = 'ANALYZING'
            project.analysis_stage = 'fetching_repository'
            project.analysis_progress = 10
            project.analysis_error = ''
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_progress', 'analysis_error'])

            repo_id = project.github_repo_id
            if not repo_id:
                # Try to extract repo name from repository_url
                # e.g. https://github.com/owner/repo
                parts = project.repository_url.strip('/').split('/')
                if len(parts) >= 2:
                    repo_id = f"{parts[-2]}/{parts[-1]}"
                else:
                    raise ValueError(f"Unable to determine GitHub repository identifier from URL: {project.repository_url}")

            repo_meta = self.service.get_repository(access_token, repo_id)
            project.github_repo_id = repo_meta.get('id') or project.github_repo_id
            project.github_owner = repo_meta.get('owner', {}).get('login', '') or project.github_owner
            project.github_repo_name = repo_meta.get('name', '') or project.github_repo_name
            default_branch = repo_meta.get('default_branch') or 'main'
            project.github_default_branch = default_branch

            # Fetch latest commit SHA
            commit_sha = self.service.get_latest_commit_sha(access_token, repo_id, branch=default_branch)
            if commit_sha:
                project.github_commit_sha = commit_sha

            project.save(update_fields=[
                'github_repo_id', 'github_owner', 'github_repo_name',
                'github_default_branch', 'github_commit_sha'
            ])

            # Stage 2: Fetch recursive repository tree
            project.analysis_stage = 'fetching_tree'
            project.analysis_progress = 25
            project.save(update_fields=['analysis_stage', 'analysis_progress'])

            tree_target = commit_sha or default_branch
            tree_data = self.service.get_repository_tree(access_token, repo_id, branch_or_sha=tree_target)
            tree_entries = tree_data.get('tree', [])

            # Large repository protection (Section 46)
            if len(tree_entries) > MAX_TREE_ENTRIES:
                logger.warning("Repository tree size (%s entries) exceeds max limit for project %s", len(tree_entries), project.id)
                project.analysis_status = 'FAILED'
                project.analysis_stage = 'failed'
                project.analysis_error = "Repository is too large for automatic analysis. Please select or upload a supported manifest manually."
                project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
                return False

            # Stage 3: Detect manifests, READMEs, and Licenses
            project.analysis_stage = 'detecting_files'
            project.analysis_progress = 40
            project.save(update_fields=['analysis_stage', 'analysis_progress'])

            detection = ManifestDetector.detect(tree_entries)
            project.detected_manifests = detection['manifests']

            # Inspect README and License
            readme_info = detection.get('readme')
            license_info = detection.get('license')

            # License metadata from GitHub repository object if present
            gh_license = repo_meta.get('license')
            detected_files = {
                'readme': {
                    'present': readme_info is not None,
                    'path': readme_info['path'] if readme_info else None,
                    'filename': readme_info['filename'] if readme_info else None,
                },
                'license': {
                    'present': license_info is not None or bool(gh_license),
                    'path': license_info['path'] if license_info else None,
                    'filename': license_info['filename'] if license_info else None,
                    'spdx_id': gh_license.get('spdx_id') if isinstance(gh_license, dict) else None,
                    'name': gh_license.get('name') if isinstance(gh_license, dict) else None,
                },
                'stats': detection.get('stats', {}),
                'truncated_tree': tree_data.get('truncated', False),
            }
            project.detected_files = detected_files
            project.save(update_fields=['detected_manifests', 'detected_files'])

            # Stage 4: Documentation check (Sections 20, 25)
            project.analysis_stage = 'inspecting_documentation'
            project.analysis_progress = 55
            project.save(update_fields=['analysis_stage', 'analysis_progress'])

            if readme_info and readme_info.get('path'):
                try:
                    readme_content, _ = self.service.get_file_content(
                        access_token,
                        repo_id,
                        readme_info['path'],
                        ref=commit_sha or default_branch
                    )
                    if readme_content:
                        doc_analyzer = DocumentationAnalyzer(self.service)
                        readme_analysis = doc_analyzer.analyze_readme_text(readme_content)
                        detected_files['readme']['score'] = readme_analysis.get('score')
                        detected_files['readme']['rating'] = readme_analysis.get('rating')
                        detected_files['readme']['recommendations'] = readme_analysis.get('recommendations', [])
                        project.detected_files = detected_files
                        project.save(update_fields=['detected_files'])
                except Exception as doc_err:
                    logger.warning("Could not complete README quality analysis for project %s: %s", project.id, str(doc_err))

            # Stage 5: Manifest evaluation
            supported_manifests = detection.get('supported_manifests', [])
            unsupported_manifests = detection.get('unsupported_manifests', [])

            if not supported_manifests:
                # No supported manifest found
                logger.info("No supported manifest found for project %s (%s)", project.id, project.name)
                project.analysis_status = 'NO_MANIFEST'
                project.analysis_stage = 'completed_no_manifest'
                project.analysis_progress = 100
                if unsupported_manifests:
                    names = ', '.join([m['filename'] for m in unsupported_manifests[:3]])
                    project.analysis_error = f"Detected dependency manifest ({names}) is not yet supported by the scan engine."
                else:
                    project.analysis_error = "No supported dependency manifests (package.json, requirements.txt) detected."
                project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_progress', 'analysis_error'])
                return True

            # Limit manifests if excessive (Section 46)
            if len(supported_manifests) > MAX_MANIFESTS:
                supported_manifests = supported_manifests[:MAX_MANIFESTS]

            # Stage 6: Retrieve manifest contents and run scans
            project.analysis_stage = 'retrieving_manifests'
            project.analysis_progress = 70
            project.save(update_fields=['analysis_stage', 'analysis_progress'])

            scans_succeeded = 0
            for manifest in supported_manifests:
                manifest_path = manifest['path']
                try:
                    content, file_sha = self.service.get_file_content(
                        access_token,
                        repo_id,
                        manifest_path,
                        ref=commit_sha or default_branch
                    )
                except Exception as e:
                    logger.error("Failed to retrieve manifest %s from GitHub: %s", manifest_path, str(e))
                    continue

                if len(content.encode('utf-8')) > MAX_MANIFEST_SIZE_BYTES:
                    logger.warning("Manifest %s in project %s exceeds max file size limit (%s bytes)", manifest_path, project.id, len(content))
                    continue

                project.analysis_stage = 'analyzing_dependencies'
                project.analysis_progress = 85
                project.save(update_fields=['analysis_stage', 'analysis_progress'])

                # Create Scan record reusing existing LicenseLens scanning engine
                file_basename = os.path.basename(manifest_path)
                scan = Scan.objects.create(
                    project=project,
                    status='PENDING',
                    source_type=manifest['parser'],
                    file_name=manifest_path,
                )
                # Save file content
                scan.uploaded_file.save(file_basename, ContentFile(content.encode('utf-8')), save=False)
                scan.save()

                scan_success = run_scan(scan)
                if scan_success:
                    scans_succeeded += 1
                else:
                    logger.warning("Scan run returned failure for manifest %s in project %s", manifest_path, project.id)

            # Finalize Status
            if scans_succeeded == 0:
                project.analysis_status = 'FAILED'
                project.analysis_stage = 'failed'
                project.analysis_error = "Dependency scanning failed to process detected manifests."
            elif unsupported_manifests:
                # Some supported files parsed, but other manifests unsupported
                project.analysis_status = 'PARTIAL'
                project.analysis_stage = 'completed_partial'
                project.analysis_error = ''
            else:
                project.analysis_status = 'COMPLETED'
                project.analysis_stage = 'completed'
                project.analysis_error = ''

            project.analysis_progress = 100
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_progress', 'analysis_error'])
            logger.info("Automatic analysis for project %s completed with status %s", project.id, project.analysis_status)
            return True

        except GitHubAuthError as e:
            logger.warning("GitHub authentication error during analysis for project %s: %s", project.id, str(e))
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            project.analysis_error = "GitHub authorization expired. Please reconnect your GitHub account."
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            return False

        except GitHubRateLimitError as e:
            logger.warning("GitHub rate limit reached during analysis for project %s: %s", project.id, str(e))
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            project.analysis_error = "GitHub API rate limit reached. Please try again in a few minutes."
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            return False

        except GitHubNotFoundError:
            logger.warning("Repository not found or inaccessible for project %s", project.id)
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            project.analysis_error = "Repository not found or no longer accessible on GitHub."
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            return False

        except GitHubAPIError as e:
            logger.warning("GitHub API error during analysis for project %s: %s", project.id, str(e))
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            if getattr(e, 'status_code', None) == 403:
                project.analysis_error = "LicenseLens cannot access this repository. Please check GitHub permissions."
            else:
                project.analysis_error = f"GitHub API error: {str(e)[:200]}"
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            return False

        except Exception as e:
            logger.error("Unexpected error analyzing repository for project %s: %s", project.id, str(e), exc_info=True)
            project.analysis_status = 'FAILED'
            project.analysis_stage = 'failed'
            project.analysis_error = f"Analysis error: {str(e)[:200]}"
            project.save(update_fields=['analysis_status', 'analysis_stage', 'analysis_error'])
            return False


def trigger_analysis_in_background(user, project):
    """
    Launch automatic repository analysis in a background daemon thread
    to keep HTTP requests responsive while scans execute.
    In testing runner environments, skips background thread to prevent SQLite connection locks.
    """
    import sys
    if 'test' in sys.argv:
        return None

    service = RepositoryAnalysisService()
    thread = threading.Thread(
        target=service.analyze_github_repository,
        args=(user, project),
        daemon=True,
        name=f"repo-analysis-project-{project.id}"
    )
    thread.start()
    return thread
