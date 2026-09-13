from rest_framework import serializers
from .models import Vulnerability, RiskFinding


class VulnerabilitySerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source='dependency.name', read_only=True)
    package_version = serializers.CharField(source='dependency.version', read_only=True)
    ecosystem = serializers.CharField(source='dependency.ecosystem', read_only=True)

    class Meta:
        model = Vulnerability
        fields = (
            'id', 'package_name', 'package_version', 'ecosystem',
            'identifier', 'source', 'summary', 'severity', 'cvss_score',
            'fixed_version', 'affected_versions', 'references', 'published_date',
        )


class RiskFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskFinding
        fields = ('id', 'category', 'severity', 'title', 'description', 'recommendation')
