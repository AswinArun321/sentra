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
