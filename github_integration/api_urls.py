from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.api_github_status, name='api_github_status'),
    path('repositories/', views.api_github_repositories, name='api_github_repositories'),
    path('repositories/<int:repo_id>/', views.api_github_repository_detail, name='api_github_repository_detail'),
    path('import/', views.api_github_import, name='api_github_import'),
    path('repositories/<int:repo_id>/import/', views.api_github_import_by_id, name='api_github_import_by_id'),
    path('disconnect/', views.api_github_disconnect, name='api_github_disconnect'),
    path('repositories/<int:repo_id>/documentation/', views.api_github_documentation, name='api_github_documentation'),
    path('repositories/<int:repo_id>/readme/', views.api_github_readme, name='api_github_readme'),
    path('repositories/<int:repo_id>/readme/generate/', views.api_github_generate_readme, name='api_github_generate_readme'),
    path('repositories/<int:repo_id>/readme/commit/', views.api_github_commit_readme, name='api_github_commit_readme'),
]
