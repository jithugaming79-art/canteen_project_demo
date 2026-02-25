"""Django settings for canteen project."""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required by allauth
    
    # Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',  # For Instagram login
    
    # Our apps
    'accounts',
    'menu',
    'orders.apps.OrdersConfig',
    'payments',
    'chatbot',
    'axes',
]

# Add daphne/channels only for local development (not supported on Render free tier)
if DEBUG:
    INSTALLED_APPS.insert(1, 'daphne')
    INSTALLED_APPS.insert(2, 'channels')

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'canteen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'canteen.wsgi.application'

# ASGI/Channels only for local development
if DEBUG:
    ASGI_APPLICATION = 'canteen.asgi.application'
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }

# For production, switch to Redis (pip install channels-redis):
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {"hosts": [config('REDIS_URL', default='redis://127.0.0.1:6379/0')]},
#     }
# }

# Database Configuration
# Use DATABASE_URL (PostgreSQL on Render) if available, otherwise fall back to MySQL for local dev
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='canteen_db'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            }
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: serve static files directly from STATICFILES_DIRS as fallback
WHITENOISE_USE_FINDERS = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'axes': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'orders': {'level': 'INFO'},
        'menu': {'level': 'INFO'},
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth settings
LOGIN_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Axes (login rate-limiting) settings
AXES_FAILURE_LIMIT = 5          # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1           # Lock for 1 hour
AXES_RESET_ON_SUCCESS = True    # Reset counter on successful login
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']  # Lock by combo
AXES_ENABLED = True             # Enable axes
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'  # Explicit DB handler for production

# Allauth settings
ACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = 'home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'login'
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disabled as per user request
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SILENCED_SYSTEM_CHECKS = ['allauth.W001', 'allauth.W002', 'allauth.E001', 'allauth.E002']
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

# Password Reset Settings
ACCOUNT_PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  # Auto-login after verifying email
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # Verification link valid for 3 days


# Email Configuration
try:
    _email_host = config('EMAIL_HOST', default='')
    if _email_host:
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_HOST = _email_host
        EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
        EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
        EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
        EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
        DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
except Exception:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Firebase API Config (for email verification via Pyrebase)
FIREBASE_CONFIG = {
  "apiKey": config('FIREBASE_API_KEY', default=''),
  "authDomain": config('FIREBASE_AUTH_DOMAIN', default=''),
  "projectId": config('FIREBASE_PROJECT_ID', default=''),
  "storageBucket": config('FIREBASE_STORAGE_BUCKET', default=''),
  "messagingSenderId": config('FIREBASE_MESSAGING_SENDER_ID', default=''),
  "appId": config('FIREBASE_APP_ID', default=''),
  "databaseURL": ""  # Only needed if using RTDB
}
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# Stripe Payment Gateway
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'picture',
        ],
        'VERSION': 'v13.0',
    }
}


# Jazzmin Admin Settings
JAZZMIN_SETTINGS = {
    "site_title": "CampusBites Admin",
    "site_header": "CampusBites",
    "site_brand": "CampusBites",
    "welcome_sign": "Welcome to CampusBites Admin",
    "copyright": "CampusBites Ltd",
    "search_model": ["auth.User", "orders.Order"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["orders", "menu", "accounts", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "orders.Order": "fas fa-shopping-cart",
        "menu.MenuItem": "fas fa-hamburger",
        "menu.Category": "fas fa-list-alt",
        "accounts.ValidStudent": "fas fa-id-card",
        "payments.Payment": "fas fa-credit-card",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# --- SECURITY & SESSION HARDENING ---
# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on activity (like Swiggy)

# CSRF security
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://canteen-project-demo.onrender.com',
]

# Production settings (applied if DEBUG=False)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Render handles SSL at the proxy level, so disable Django's redirect
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
