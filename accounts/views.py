import logging
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


# ─── REST API Views ────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Register a new user."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info(f"New user registered: {user.email}")
        return Response({
            'message': 'Registration successful.',
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Login and return JWT tokens."""
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, username=email, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        logger.info(f"User logged in: {user.email}")
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        })
    return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Blacklist refresh token (logout)."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'message': 'Logged out.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """Get current user profile."""
    return Response(UserProfileSerializer(request.user).data)


# ─── Template (Frontend) Views ─────────────────────────────────

def login_view(request):
    """Django session login page."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next')
            if user.is_staff or user.is_superuser:
                if next_url and not next_url.startswith('/dashboard'):
                    return redirect(next_url)
                return redirect('admin_dashboard')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        messages.error(request, 'Invalid email or password.')
    return render(request, 'auth/login.html')


def register_view(request):
    """Django session register page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        serializer = RegisterSerializer(data={
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'password2': request.POST.get('password2'),
        })
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, f'Welcome to SENTRA, {user.username}!')
            return redirect('dashboard')
        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    return render(request, 'auth/register.html')


def logout_view(request):
    """Logout and redirect."""
    logout(request)
    request.session.flush()
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def profile_view(request):
    """User profile page."""
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'auth/profile.html', {'user': request.user})
