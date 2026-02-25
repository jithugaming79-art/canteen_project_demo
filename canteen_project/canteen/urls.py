"""URL Configuration for canteen project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseServerError
import django
import traceback
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """Health check endpoint showing deployment status."""
    return JsonResponse({
        'status': 'ok',
        'django_version': django.get_version(),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
    })

def custom_500(request):
    """Custom 500 handler that logs the full error details."""
    import sys
    exc_info = sys.exc_info()
    if exc_info[1]:
        logger.error("500 Error: %s", exc_info[1], exc_info=exc_info)
    return HttpResponseServerError(
        "<h1>Internal Server Error</h1>"
        "<p>Something went wrong. The error has been logged.</p>"
    )

handler500 = custom_500

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('accounts.urls')),
    path('', include('menu.urls')),
    path('', include('orders.urls')),
    path('', include('payments.urls')),
    path('', include('chatbot.urls')),
    path('offline/', TemplateView.as_view(template_name="offline.html"), name='offline'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

