"""
LicenseLens — Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from scans.views import api_start_scan, api_project_scans

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # REST API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/projects/<int:project_pk>/scan/', api_start_scan, name='api_start_scan'),
    path('api/projects/<int:project_pk>/scans/', api_project_scans, name='api_project_scans'),
    path('api/scans/', include('scans.urls')),
    path('api/github/', include('github_integration.api_urls')),
    path('api/dashboard/', include('frontend.api_urls')),

    # Frontend (template views)
    path('', lambda request: redirect('dashboard') if request.user.is_authenticated else redirect('login'), name='home'),
    path('auth/', include('accounts.frontend_urls')),
    path('dashboard/', include('frontend.urls')),
    path('projects/', include('projects.frontend_urls')),
    path('github/', include('github_integration.urls')),
    path('scans/', include('scans.frontend_urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
