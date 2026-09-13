from rest_framework import serializers
from .models import Scan


class ScanSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    vulnerability_count = serializers.IntegerField(read_only=True)
    dependency_count = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = (
            'id', 'project_name', 'status', 'source_type', 'file_name',
            'risk_score', 'risk_level', 'vulnerability_count', 'dependency_count',
            'started_at', 'completed_at', 'created_at',
        )
        read_only_fields = fields

    def get_dependency_count(self, obj):
        return obj.dependencies.count()


class ScanDetailSerializer(ScanSerializer):
    critical_count = serializers.IntegerField(read_only=True)
    high_count = serializers.IntegerField(read_only=True)
    medium_count = serializers.IntegerField(read_only=True)
    low_count = serializers.IntegerField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    error_message = serializers.CharField(read_only=True)

    class Meta(ScanSerializer.Meta):
        fields = ScanSerializer.Meta.fields + (
            'critical_count', 'high_count', 'medium_count', 'low_count',
            'duration_seconds', 'error_message',
        )
