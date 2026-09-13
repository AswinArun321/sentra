from rest_framework import serializers
from .models import Dependency


class DependencySerializer(serializers.ModelSerializer):
    vulnerability_count = serializers.IntegerField(read_only=True)
    compliance_status = serializers.SerializerMethodField()

    class Meta:
        model = Dependency
        fields = (
            'id', 'name', 'version', 'version_spec', 'ecosystem',
            'is_direct', 'dependency_type', 'license', 'license_category',
            'license_source', 'maintenance_status', 'last_release_date',
            'release_count', 'risk_score', 'homepage', 'description',
            'vulnerability_count', 'compliance_status',
        )

    def get_compliance_status(self, obj):
        from scanner.license_analyzer import get_compliance_status
        return get_compliance_status(obj.license_category)
