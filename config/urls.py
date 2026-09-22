"""
SENTRA — Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from scans.views import api_start_scan, api_project_scans
from frontend import views_public

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
    path('api/admin/', include('admin_panel.api_urls')),

    # SENTRA Admin Console
    path('admin-console/', include('admin_panel.urls')),

    # Public Pages (accessible prior to authentication)
    path('', views_public.home_view, name='home'),
    path('features/', views_public.features_view, name='features'),
    path('how-it-works/', views_public.how_it_works_view, name='how_it_works'),
    path('about/', views_public.about_view, name='about'),
    path('docs/', views_public.docs_view, name='documentation'),
    path('contact/', views_public.contact_view, name='contact'),

    # Frontend (template views)
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
