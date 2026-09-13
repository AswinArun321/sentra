from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# REST API URLs
urlpatterns = [
    path('register/', views.api_register, name='api_register'),
    path('login/', views.api_login, name='api_login'),
    path('logout/', views.api_logout, name='api_logout'),
    path('profile/', views.api_profile, name='api_profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
