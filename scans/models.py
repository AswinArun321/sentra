from django.db import models
from projects.models import Project


class Scan(models.Model):
    """A single dependency scan run for a project."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    SOURCE_CHOICES = [
        ('package.json', 'package.json (npm)'),
        ('requirements.txt', 'requirements.txt (PyPI)'),
        ('pom.xml', 'pom.xml (Maven)'),
        ('github', 'GitHub Repository'),
    ]

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
        ('UNKNOWN', 'Unknown'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scans')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    source_type = models.CharField(max_length=30, choices=SOURCE_CHOICES, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_file = models.FileField(upload_to='scans/', blank=True, null=True)

    # Risk results
    risk_score = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='UNKNOWN')

    # Scan metadata
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scan'
        verbose_name_plural = 'Scans'

    def __str__(self):
        return f"Scan #{self.pk} — {self.project.name} ({self.status})"

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def vulnerability_count(self):
        from vulnerabilities.models import Vulnerability
        return Vulnerability.objects.filter(dependency__scan=self).count()

    @property
    def critical_count(self):
        from vulnerabilities.models import Vulnerability
        return Vulnerability.objects.filter(dependency__scan=self, severity='CRITICAL').count()

    @property
    def high_count(self):
        from vulnerabilities.models import Vulnerability
        return Vulnerability.objects.filter(dependency__scan=self, severity='HIGH').count()

    @property
    def medium_count(self):
        from vulnerabilities.models import Vulnerability
        return Vulnerability.objects.filter(dependency__scan=self, severity='MEDIUM').count()

    @property
    def low_count(self):
        from vulnerabilities.models import Vulnerability
        return Vulnerability.objects.filter(dependency__scan=self, severity='LOW').count()
