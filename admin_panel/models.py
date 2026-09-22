from django.db import models
from django.conf import settings


class AdminAuditLog(models.Model):
    """
    Tracks administrative actions performed within the SENTRA Admin Console.
    Never stores credentials, tokens, or sensitive user secrets.
    """
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_actions"
    )
    action = models.CharField(max_length=100, db_index=True)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_audit_events"
    )
    target_object_type = models.CharField(max_length=100, blank=True)
    target_object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'

    def __str__(self):
        actor = self.admin_user.username if self.admin_user else "System"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {actor} -> {self.action}"


class UserAccountStatus(models.Model):
    """
    Extends user status with controlled states (ACTIVE, INACTIVE, SUSPENDED).
    Synchronized with Django's built-in is_active field to prevent conflicting sources of truth.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_status'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        verbose_name = 'User Account Status'
        verbose_name_plural = 'User Account Statuses'

    def __str__(self):
        return f"{self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        # Keep Django User.is_active synchronized
        if self.status == 'ACTIVE':
            if not self.user.is_active:
                self.user.is_active = True
                self.user.save(update_fields=['is_active'])
        else:
            if self.user.is_active:
                self.user.is_active = False
                self.user.save(update_fields=['is_active'])
        super().save(*args, **kwargs)


class PlatformSetting(models.Model):
    """
    Safe runtime platform settings manageable by authorized administrators.
    Never exposes or stores environment secrets or API credentials.
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        verbose_name = 'Platform Setting'
        verbose_name_plural = 'Platform Settings'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key: str, default: str = '') -> str:
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key: str, value: str, updated_by=None, description: str = ''):
        obj, _ = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'updated_by': updated_by,
            }
        )
        return obj
