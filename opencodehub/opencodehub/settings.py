"""
Django settings for opencodehub project.
"""

import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env in local dev only (not on Render)
if os.environ.get("RENDER", "") != "true":
    load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-2r+hp@h)(uy0(9bz$w#59*)qn5)%-31#zh!b(w#^7jpr$++_ww")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

# Allowed Hosts Configuration
if DEBUG:
    # Development: Allow local development
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.localhost', '0.0.0.0', 'testserver']
else:
    # Production: Use environment variable
    ALLOWED_HOSTS = [
        h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") 
        if h.strip()
    ]

# CSRF Configuration - Cross-Site Request Forgery Protection
# This ensures secure form submissions and prevents CSRF attacks
CSRF_COOKIE_SECURE = not DEBUG  # Only require HTTPS cookies in production
CSRF_COOKIE_SAMESITE = 'Lax'    # Allow cross-site requests with referrer
CSRF_USE_SESSIONS = False        # Use cookies instead of sessions for CSRF tokens
CSRF_COOKIE_HTTPONLY = False     # Allow JavaScript access to CSRF token

# CSRF Trusted Origins - Domains allowed to make POST requests
if DEBUG:
    # Development: Allow local development and IDE browser previews
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:8000",   # Direct Django server
        "http://localhost:8000",    # Localhost alias
        "https://127.0.0.1:8000",  # HTTPS variant
        "https://localhost:8000",   # HTTPS localhost
    ]
    # Add common development server ports (React, Vue, etc.)
    for port in [3000, 3001, 8080, 8081, 9000, 9001]:
        CSRF_TRUSTED_ORIGINS.extend([
            f"http://127.0.0.1:{port}",
            f"http://localhost:{port}",
        ])
    # Add IDE browser preview proxy ports (VS Code, WebStorm, etc.)
    # Add common proxy port ranges
    proxy_ports = list(range(49000, 50000, 100)) + list(range(60000, 65000, 100))
    for port in proxy_ports:
        CSRF_TRUSTED_ORIGINS.append(f"http://127.0.0.1:{port}")
    
    # Add specific browser preview ports if detected
    CSRF_TRUSTED_ORIGINS.append("http://127.0.0.1:61958")
    CSRF_TRUSTED_ORIGINS.append("http://127.0.0.1:65509")
    CSRF_TRUSTED_ORIGINS.append("http://127.0.0.1:61016")
else:
    # Production: Use environment variable for security
    CSRF_TRUSTED_ORIGINS = [
        o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") 
        if o.strip()
    ]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise here
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'opencodehub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'opencodehub.wsgi.application'

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Use PostgreSQL with SSL
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Use SQLite for local development (no SSL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Media files configuration for file uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # UTC+8 (Philippines/Hong Kong/Singapore)
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: serve compressed static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration (for password reset)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'OpenCodeHub <noreply@opencodehub.com>'

# Login/Logout redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'landing'

# File Upload Settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Blocked file extensions for security
BLOCKED_FILE_EXTENSIONS = [
    '.exe', '.bat', '.sh', '.cmd', '.com', '.app', '.dmg', '.deb',
    '.rpm', '.msi', '.scr', '.vbs', '.js.exe',
]

# Maximum storage per user
MAX_USER_STORAGE = 1 * 1024 * 1024 * 1024  # 1GB per user

# Django's built-in file upload size limit
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB 
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# Security settings for production
if os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True