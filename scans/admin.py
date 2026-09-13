from django.contrib import admin
from .models import Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'source_type', 'status', 'risk_score', 'risk_level', 'created_at')
    list_filter = ('status', 'risk_level', 'source_type')
    search_fields = ('project__name',)
    readonly_fields = ('created_at', 'started_at', 'completed_at')
