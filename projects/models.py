from django.db import models
from django.conf import settings


class Project(models.Model):
    """A software project to be analyzed for dependency risks."""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    repository_url = models.URLField(blank=True)
    SOURCE_CHOICES = [
        ('manual', 'Manual Upload'),
        ('github', 'GitHub Repository'),
    ]

    ANALYSIS_STATUS_CHOICES = [
        ('NONE', 'None'),
        ('IMPORTING', 'Importing'),
        ('ANALYZING', 'Analyzing'),
        ('COMPLETED', 'Completed'),
        ('NO_MANIFEST', 'No Manifest'),
        ('PARTIAL', 'Partial Analysis'),
        ('FAILED', 'Failed'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    github_repo_id = models.BigIntegerField(null=True, blank=True)
    github_owner = models.CharField(max_length=150, blank=True)
    github_repo_name = models.CharField(max_length=150, blank=True)
    github_default_branch = models.CharField(max_length=100, blank=True, default='main')
    github_commit_sha = models.CharField(max_length=40, blank=True)

    analysis_status = models.CharField(max_length=30, choices=ANALYSIS_STATUS_CHOICES, default='NONE')
    analysis_stage = models.CharField(max_length=80, blank=True)
    analysis_progress = models.IntegerField(default=0)
    analysis_error = models.TextField(blank=True)
    detected_manifests = models.JSONField(default=list, blank=True)
    detected_files = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return f"{self.owner.username}/{self.name}"

    @property
    def latest_scan(self):
        return self.scans.filter(status='COMPLETED').first()

    @property
    def risk_score(self):
        scan = self.latest_scan
        return scan.risk_score if scan else None

    @property
    def risk_level(self):
        scan = self.latest_scan
        return scan.risk_level if scan else 'UNKNOWN'

    @property
    def dependency_count(self):
        scan = self.latest_scan
        if scan:
            return scan.dependencies.count()
        return 0
