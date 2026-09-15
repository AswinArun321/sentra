from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model for SENTRA."""
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def project_count(self):
        return self.projects.count()

    @property
    def scan_count(self):
        from scans.models import Scan
        return Scan.objects.filter(project__owner=self).count()
