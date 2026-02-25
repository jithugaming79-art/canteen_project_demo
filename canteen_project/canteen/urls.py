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

def debug_order(request):
    """Debug endpoint to test place_order components."""
    results = {}
    
    # Step 1: Test SystemSettings
    try:
        from accounts.models import SystemSettings
        ss = SystemSettings.get_settings()
        results['1_system_settings'] = f'OK - maintenance={ss.maintenance_mode}, delivery_fee={ss.delivery_fee}'
    except Exception as e:
        results['1_system_settings'] = f'FAIL: {e}'
    
    # Step 2: Test Order model import and migration status
    try:
        from orders.models import Order, OrderItem
        results['2_order_import'] = f'OK - choices={Order.PAYMENT_CHOICES}'
    except Exception as e:
        results['2_order_import'] = f'FAIL: {e}'
    
    # Step 3: Test DB connection with Order query
    try:
        count = Order.objects.count()
        results['3_order_query'] = f'OK - {count} orders exist'
    except Exception as e:
        results['3_order_query'] = f'FAIL: {e}'
    
    # Step 4: Test MenuItem query
    try:
        from menu.models import MenuItem
        count = MenuItem.objects.count()
        results['4_menuitem_query'] = f'OK - {count} items exist'
    except Exception as e:
        results['4_menuitem_query'] = f'FAIL: {e}'
    
    # Step 5: Test transaction.atomic
    try:
        from django.db import transaction
        with transaction.atomic():
            pass
        results['5_transaction_atomic'] = 'OK'
    except Exception as e:
        results['5_transaction_atomic'] = f'FAIL: {e}'
    
    # Step 6: Test generate_token
    try:
        from orders.models import generate_token
        token = generate_token()
        results['6_generate_token'] = f'OK - {token}'
    except Exception as e:
        results['6_generate_token'] = f'FAIL: {e}'
    
    # Step 7: Test email backend
    try:
        from django.core.mail import get_connection
        conn = get_connection()
        results['7_email_backend'] = f'OK - backend={conn.__class__.__name__}'
    except Exception as e:
        results['7_email_backend'] = f'FAIL: {e}'
    
    # Step 8: Test URL reverse
    try:
        from django.urls import reverse
        results['8_url_payment_page'] = f'OK - {reverse("payment_page", args=[1])}'
        results['8_url_process_online'] = f'OK - {reverse("process_online_payment", args=[1])}'
    except Exception as e:
        results['8_url_reverse'] = f'FAIL: {e}'
    
    # Step 9: Check installed apps
    results['9_installed_apps'] = list(settings.INSTALLED_APPS)
    
    # Step 10: Check middleware
    results['10_middleware'] = list(settings.MIDDLEWARE)
    
    return JsonResponse(results, json_dumps_params={'indent': 2})

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
    path('debug-order/', debug_order, name='debug_order'),
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

