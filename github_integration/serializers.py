from rest_framework import serializers


class GitHubConnectionStatusSerializer(serializers.Serializer):
    connected = serializers.BooleanField()
    github_username = serializers.CharField(required=False, allow_null=True)
    github_user_id = serializers.IntegerField(required=False, allow_null=True)
    connected_at = serializers.DateTimeField(required=False, allow_null=True)


class GitHubRepositoryOwnerSerializer(serializers.Serializer):
    login = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)


class GitHubRepositorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, default='')
    private = serializers.BooleanField()
    html_url = serializers.URLField()
    default_branch = serializers.CharField(default='main')
    language = serializers.CharField(allow_blank=True, default='Unknown')
    updated_at = serializers.CharField(allow_blank=True, default='')
    stargazers_count = serializers.IntegerField(default=0)
    forks_count = serializers.IntegerField(default=0)
    owner = GitHubRepositoryOwnerSerializer(required=False)


class GitHubImportSerializer(serializers.Serializer):
    repository_id = serializers.IntegerField(required=True)


class GitHubReadmeCommitSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, allow_blank=False)
    commit_message = serializers.CharField(required=False, default="Add README.md", allow_blank=False)
    overwrite = serializers.BooleanField(required=False, default=False)

