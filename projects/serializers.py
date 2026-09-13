from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    risk_score = serializers.FloatField(read_only=True)
    risk_level = serializers.CharField(read_only=True)
    dependency_count = serializers.IntegerField(read_only=True)
    scan_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'repository_url',
            'owner_username', 'risk_score', 'risk_level',
            'dependency_count', 'scan_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_scan_count(self, obj):
        return obj.scans.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'description', 'repository_url')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
