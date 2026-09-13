from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'risk_level', 'dependency_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
