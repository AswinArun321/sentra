from django.db import models
from scans.models import Scan


class Dependency(models.Model):
    """A single dependency found in a scan."""

    ECOSYSTEM_CHOICES = [
        ('npm', 'npm (Node.js)'),
        ('PyPI', 'PyPI (Python)'),
        ('Maven', 'Maven (Java)'),
        ('unknown', 'Unknown'),
    ]

    DEP_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('dev', 'Development'),
        ('transitive', 'Transitive'),
        ('unknown', 'Unknown'),
    ]

    MAINTENANCE_CHOICES = [
        ('ACTIVE', 'Active'),
        ('LOW_ACTIVITY', 'Low Activity'),
        ('STALE', 'Stale'),
        ('ABANDONED', 'Abandoned'),
        ('UNKNOWN', 'Unknown'),
    ]

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='dependencies')
    name = models.CharField(max_length=300)
    version = models.CharField(max_length=100, blank=True)
    version_spec = models.CharField(max_length=100, blank=True)  # original spec e.g. "^4.18.2"
    ecosystem = models.CharField(max_length=20, choices=ECOSYSTEM_CHOICES, default='unknown')
    is_direct = models.BooleanField(default=True)
    dependency_type = models.CharField(max_length=20, choices=DEP_TYPE_CHOICES, default='direct')

    # License info
    license = models.CharField(max_length=200, blank=True, default='Unknown')
    license_category = models.CharField(max_length=50, blank=True, default='UNKNOWN')
    license_source = models.CharField(max_length=50, blank=True)

    # Maintenance info
    maintenance_status = models.CharField(max_length=20, choices=MAINTENANCE_CHOICES, default='UNKNOWN')
    last_release_date = models.DateField(null=True, blank=True)
    release_count = models.IntegerField(default=0)

    # Risk
    risk_score = models.FloatField(default=0.0)

    # Metadata
    homepage = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score', 'name']
        verbose_name = 'Dependency'
        verbose_name_plural = 'Dependencies'
        unique_together = ('scan', 'name', 'version')

    def __str__(self):
        return f"{self.name}=={self.version} ({self.ecosystem})"

    @property
    def vulnerability_count(self):
        return self.vulnerabilities.count()


class DependencyRelationship(models.Model):
    """Tracks parent→child dependency relationships."""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='relationships')
    parent = models.ForeignKey(Dependency, on_delete=models.CASCADE, related_name='children')
    child = models.ForeignKey(Dependency, on_delete=models.CASCADE, related_name='parents')
    depth = models.IntegerField(default=1)

    class Meta:
        unique_together = ('parent', 'child')
        verbose_name = 'Dependency Relationship'

    def __str__(self):
        return f"{self.parent.name} → {self.child.name} (depth {self.depth})"
