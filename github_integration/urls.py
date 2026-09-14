from django.urls import path
from . import views

urlpatterns = [
    path('connect/', views.github_connect_view, name='github_connect'),
    path('callback/', views.github_callback_view, name='github_callback'),
    path('repositories/', views.github_repositories_view, name='github_repositories'),
    path('repositories/<int:repo_id>/documentation/', views.github_documentation_view, name='github_documentation'),
    path('disconnect/', views.github_disconnect_view, name='github_disconnect'),
]
