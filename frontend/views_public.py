"""
SENTRA — Public Pre-Authentication Views
Handles public pages accessible prior to user authentication:
Home, Features, How It Works, About Us, Documentation, and Contact.
"""
from django.shortcuts import render, redirect


def home_view(request):
    """
    Renders the SENTRA public home page.
    """
    return render(request, 'public/home.html', {
        'active_page': 'home',
    })


def features_view(request):
    """
    Renders the SENTRA capabilities & features page.
    """
    return render(request, 'public/features.html', {
        'active_page': 'features',
    })


def how_it_works_view(request):
    """
    Renders the automatic GitHub repository analysis workflow page.
    """
    return render(request, 'public/how_it_works.html', {
        'active_page': 'how_it_works',
    })


def about_view(request):
    """
    Renders the About Us, mission, and architecture values page.
    """
    return render(request, 'public/about.html', {
        'active_page': 'about',
    })


def docs_view(request):
    """
    Renders the lightweight user guide and reference documentation page.
    """
    return render(request, 'public/documentation.html', {
        'active_page': 'docs',
    })


def contact_view(request):
    """
    Renders the project contact and inquiry page.
    """
    return render(request, 'public/contact.html', {
        'active_page': 'contact',
    })
