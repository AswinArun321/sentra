from django.contrib import admin
from admin_panel.models import AdminAuditLog, UserAccountStatus, PlatformSetting


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'admin_user', 'action', 'target_user', 'target_object_type', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('admin_user__username', 'target_user__username', 'description', 'action', 'ip_address')
    readonly_fields = ('created_at', 'admin_user', 'action', 'target_user', 'target_object_type', 'target_object_id', 'description', 'ip_address', 'user_agent')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserAccountStatus)
class UserAccountStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'updated_at', 'updated_by')
    list_filter = ('status', 'updated_at')
    search_fields = ('user__username', 'user__email', 'reason')


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at', 'updated_by')
    search_fields = ('key', 'value', 'description')
