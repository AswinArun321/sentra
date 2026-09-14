from django.db import models
from django.conf import settings


class GitHubConnection(models.Model):
    """
    Stores GitHub OAuth connection information per LicenseLens user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="github_connection"
    )
    github_user_id = models.BigIntegerField(unique=True)
    github_username = models.CharField(max_length=150)
    access_token = models.TextField()
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "GitHub Connection"
        verbose_name_plural = "GitHub Connections"
        ordering = ['-connected_at']

    def __str__(self):
        return f"{self.user.username} (@{self.github_username})"
