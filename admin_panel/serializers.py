from rest_framework import serializers
from django.contrib.auth import get_user_model
from admin_panel.models import AdminAuditLog, PlatformSetting, UserAccountStatus
from projects.models import Project
from scans.models import Scan
from dependencies.models import Dependency
from vulnerabilities.models import Vulnerability
from reports.models import Report
from github_integration.models import GitHubConnection

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    account_status = serializers.SerializerMethodField()
    status_reason = serializers.SerializerMethodField()
    project_count = serializers.IntegerField(read_only=True)
    scan_count = serializers.IntegerField(read_only=True)
    github_connected = serializers.SerializerMethodField()
    github_username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'account_status',
            'status_reason',
            'project_count',
            'scan_count',
            'github_connected',
            'github_username',
        ]
        read_only_fields = fields

    def get_account_status(self, obj):
        if hasattr(obj, 'admin_status'):
            return obj.admin_status.status
        return 'ACTIVE' if obj.is_active else 'INACTIVE'

    def get_status_reason(self, obj):
        if hasattr(obj, 'admin_status'):
            return obj.admin_status.reason
        return ''

    def get_github_connected(self, obj):
        return hasattr(obj, 'github_connection') and obj.github_connection is not None

    def get_github_username(self, obj):
        if hasattr(obj, 'github_connection') and obj.github_connection:
            return obj.github_connection.github_username
        return None


class AdminProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    risk_score = serializers.FloatField(read_only=True)
    risk_level = serializers.CharField(read_only=True)
    dependency_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'owner',
            'owner_username',
            'owner_email',
            'repository_url',
            'source',
            'github_repo_name',
            'analysis_status',
            'risk_score',
            'risk_level',
            'dependency_count',
            'created_at',
            'updated_at',
        ]


class AdminScanSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    owner_username = serializers.CharField(source='project.owner.username', read_only=True)
    owner_email = serializers.CharField(source='project.owner.email', read_only=True)
    vulnerability_count = serializers.IntegerField(read_only=True)
    critical_count = serializers.IntegerField(read_only=True)
    high_count = serializers.IntegerField(read_only=True)
    medium_count = serializers.IntegerField(read_only=True)
    low_count = serializers.IntegerField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = Scan
        fields = [
            'id',
            'project',
            'project_name',
            'owner_username',
            'owner_email',
            'status',
            'source_type',
            'risk_score',
            'risk_level',
            'error_message',
            'duration_seconds',
            'vulnerability_count',
            'critical_count',
            'high_count',
            'medium_count',
            'low_count',
            'started_at',
            'completed_at',
            'created_at',
        ]


class AdminVulnerabilitySerializer(serializers.ModelSerializer):
    dependency_name = serializers.CharField(source='dependency.name', read_only=True)
    dependency_version = serializers.CharField(source='dependency.version', read_only=True)
    ecosystem = serializers.CharField(source='dependency.ecosystem', read_only=True)
    project_id = serializers.IntegerField(source='dependency.scan.project.id', read_only=True)
    project_name = serializers.CharField(source='dependency.scan.project.name', read_only=True)
    owner_username = serializers.CharField(source='dependency.scan.project.owner.username', read_only=True)

    class Meta:
        model = Vulnerability
        fields = [
            'id',
            'identifier',
            'severity',
            'cvss_score',
            'source',
            'summary',
            'affected_versions',
            'fixed_version',
            'references',
            'published_date',
            'dependency_name',
            'dependency_version',
            'ecosystem',
            'project_id',
            'project_name',
            'owner_username',
            'created_at',
        ]


class AdminDependencySerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='scan.project.id', read_only=True)
    project_name = serializers.CharField(source='scan.project.name', read_only=True)
    owner_username = serializers.CharField(source='scan.project.owner.username', read_only=True)
    vulnerability_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dependency
        fields = [
            'id',
            'name',
            'version',
            'ecosystem',
            'is_direct',
            'dependency_type',
            'license',
            'license_category',
            'maintenance_status',
            'risk_score',
            'vulnerability_count',
            'project_id',
            'project_name',
            'owner_username',
            'created_at',
        ]


class AdminReportSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='scan.project.id', read_only=True)
    project_name = serializers.CharField(source='scan.project.name', read_only=True)
    owner_username = serializers.CharField(source='scan.project.owner.username', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'scan',
            'project_id',
            'project_name',
            'owner_username',
            'report_type',
            'file_path',
            'created_at',
        ]


class AdminGitHubConnectionSafeSerializer(serializers.ModelSerializer):
    """
    NEVER exposes access_token, refresh_token, or OAuth secrets.
    Only safe metadata for monitoring.
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = GitHubConnection
        fields = [
            'id',
            'user_id',
            'username',
            'user_email',
            'github_user_id',
            'github_username',
            'connected_at',
            'updated_at',
        ]


class AdminAuditLogSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin_user.username', default='System', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', default=None, read_only=True)
    target_user_email = serializers.CharField(source='target_user.email', default=None, read_only=True)

    class Meta:
        model = AdminAuditLog
        fields = [
            'id',
            'admin_user',
            'admin_username',
            'action',
            'target_user',
            'target_user_username',
            'target_user_email',
            'target_object_type',
            'target_object_id',
            'description',
            'ip_address',
            'user_agent',
            'created_at',
        ]


class PlatformSettingSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', default=None, read_only=True)

    class Meta:
        model = PlatformSetting
        fields = [
            'id',
            'key',
            'value',
            'description',
            'updated_at',
            'updated_by_username',
        ]
