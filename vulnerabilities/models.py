from django.db import models
from dependencies.models import Dependency


class Vulnerability(models.Model):
    """A known security vulnerability affecting a dependency."""

    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
        ('UNKNOWN', 'Unknown'),
    ]

    SOURCE_CHOICES = [
        ('OSV', 'OSV (Open Source Vulnerabilities)'),
        ('NVD', 'NVD (National Vulnerability Database)'),
        ('GITHUB', 'GitHub Security Advisory'),
        ('MANUAL', 'Manual'),
    ]

    dependency = models.ForeignKey(Dependency, on_delete=models.CASCADE, related_name='vulnerabilities')
    identifier = models.CharField(max_length=100)   # e.g. CVE-2023-1234 or GHSA-xxxx
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='OSV')
    summary = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='UNKNOWN')
    cvss_score = models.FloatField(null=True, blank=True)
    affected_versions = models.TextField(blank=True)
    fixed_version = models.CharField(max_length=100, blank=True)
    references = models.JSONField(default=list, blank=True)
    published_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cvss_score', 'severity']
        verbose_name = 'Vulnerability'
        verbose_name_plural = 'Vulnerabilities'
        unique_together = ('dependency', 'identifier')

    def __str__(self):
        return f"{self.identifier} [{self.severity}] → {self.dependency.name}"


class RiskFinding(models.Model):
    """A specific risk finding with explanation and recommendation."""

    CATEGORY_CHOICES = [
        ('SECURITY', 'Security'),
        ('LICENSE', 'License'),
        ('MAINTENANCE', 'Maintenance'),
        ('DEPENDENCY', 'Dependency'),
    ]

    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
        ('INFO', 'Informational'),
    ]

    dependency = models.ForeignKey(Dependency, on_delete=models.CASCADE, related_name='risk_findings')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=300)
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'severity']
        verbose_name = 'Risk Finding'

    def __str__(self):
        return f"[{self.category}] {self.title}"
