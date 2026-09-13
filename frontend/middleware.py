from django.utils.cache import add_never_cache_headers


class DisableClientCacheMiddleware:
    """
    Middleware that prevents browsers from caching authenticated/dynamic pages.
    This ensures that when a user logs out and clicks the browser 'Back' button,
    the browser is forced to query the server and gets redirected to login,
    rather than showing stale cached protected pages from bfcache/disk.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply strict no-cache headers to all HTML responses and protected routes
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type or request.path.startswith(('/dashboard', '/projects', '/scans', '/auth', '/reports')):
            add_never_cache_headers(response)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
