from django.urls import path
from . import views

urlpatterns = [
    path('scan/<int:scan_pk>/download/', views.download_report, name='download_report'),
    path('scan/<int:scan_pk>/sbom/', views.download_sbom, name='download_sbom'),
]
