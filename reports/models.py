from django.db import models
from scans.models import Scan


class Report(models.Model):
    """A generated report for a scan."""

    REPORT_TYPE_CHOICES = [
        ('JSON', 'JSON Summary'),
        ('PDF', 'PDF Report'),
        ('SBOM_CYCLONEDX', 'CycloneDX SBOM (JSON)'),
        ('SBOM_SPDX', 'SPDX SBOM (JSON)'),
    ]

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    content = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f"{self.report_type} report for Scan #{self.scan.pk}"
