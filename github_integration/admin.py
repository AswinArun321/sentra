from django.contrib import admin
from .models import GitHubConnection


@admin.register(GitHubConnection)
class GitHubConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "github_username",
        "github_user_id",
        "connected_at",
        "updated_at",
    )
    search_fields = (
        "user__email",
        "user__username",
        "github_username",
    )
    readonly_fields = ("connected_at", "updated_at", "masked_token")
    fields = (
        "user",
        "github_user_id",
        "github_username",
        "masked_token",
        "connected_at",
        "updated_at",
    )

    def masked_token(self, obj):
        if obj.access_token:
            return f"gho_***...{obj.access_token[-4:]}" if len(obj.access_token) > 4 else "***"
        return "None"

    masked_token.short_description = "Access Token (Masked)"
