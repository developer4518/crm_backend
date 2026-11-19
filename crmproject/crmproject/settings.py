
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


# ==========================================================
# BASE CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in (
        "true", "1", "yes", "on"
    )


def env_list(name, default=""):
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY environment variable is required."
    )


ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,192.168.1.14" if DEBUG else "",
)

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be configured in production."
    )


# ==========================================================
# INSTALLED APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Django REST Framework
    "rest_framework",

    # CORS
    "corsheaders",

    # JWT token blacklisting
    "rest_framework_simplejwt.token_blacklist",

    # FlyingLyte CRM
    "crmapp.apps.CrmappConfig",
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# URL CONFIGURATION
# ==========================================================

ROOT_URLCONF = "crmproject.urls"


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "crmproject.wsgi.application"

ASGI_APPLICATION = "crmproject.asgi.application"


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

# SQLite for local development.
# Use a production-grade database such as PostgreSQL
# before deploying a multi-user CRM.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "crm_dev.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}


# ==========================================================
# CUSTOM USER MODEL
# ==========================================================

AUTH_USER_MODEL = "crmapp.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==========================================================
# DJANGO REST FRAMEWORK - JWT AUTHENTICATION
# ==========================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        (
            "rest_framework_simplejwt.authentication."
            "JWTAuthentication"
        ),
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],

    # Standardize DRF / JWT validation and authentication errors.
    "EXCEPTION_HANDLER": "crmapp.exceptions.crm_exception_handler",

    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],

    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}


# ==========================================================
# JWT TOKEN CONFIGURATION
# ==========================================================

SIMPLE_JWT = {
    # Access token expires after 15 minutes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),

    # Refresh token expires after 7 days.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),

    # Issue a new refresh token during refresh.
    "ROTATE_REFRESH_TOKENS": True,

    # Blacklist the old refresh token after rotation.
    "BLACKLIST_AFTER_ROTATION": True,

    # Avoid unnecessary last-login database writes.
    "UPDATE_LAST_LOGIN": False,

    # JWT signature algorithm.
    "ALGORITHM": "HS256",

    # Separate signing key can be supplied in production.
    # Keep this secret stable to preserve token validity.
    "SIGNING_KEY": os.getenv(
        "DJANGO_JWT_SIGNING_KEY",
        SECRET_KEY,
    ),

    "VERIFYING_KEY": "",

    "AUDIENCE": None,

    "ISSUER": "flyinglyte-crm",

    # Authorization: Bearer <access_token>
    "AUTH_HEADER_TYPES": ("Bearer",),

    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",

    # UUID-based employee identification.
    "USER_ID_FIELD": "id",

    "USER_ID_CLAIM": "user_id",

    "TOKEN_TYPE_CLAIM": "token_type",

    "JTI_CLAIM": "jti",

    "AUTH_TOKEN_CLASSES": (
        "rest_framework_simplejwt.tokens.AccessToken",
    ),

    # Check the user's active status during authentication.
    "CHECK_USER_IS_ACTIVE": True,
}


# ==========================================================
# DJANGO ADMIN SESSION CONFIGURATION
# ==========================================================

# Django Admin continues using Django sessions.
# CRM REST APIs use JWT only.

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_NAME = "sessionid"

SESSION_COOKIE_AGE = 60 * 60 * 8

SESSION_SAVE_EVERY_REQUEST = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_PATH = "/"

SESSION_COOKIE_DOMAIN = (
    os.getenv("DJANGO_SESSION_COOKIE_DOMAIN") or None
)


# ==========================================================
# CSRF SECURITY - DJANGO ADMIN
# ==========================================================

# JWT Bearer APIs do not require CSRF protection
# when authenticating exclusively through headers.
# Django Admin still uses standard CSRF protection.

CSRF_COOKIE_NAME = "csrftoken"

CSRF_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_PATH = "/"

CSRF_COOKIE_DOMAIN = (
    os.getenv("DJANGO_CSRF_COOKIE_DOMAIN") or None
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://192.168.1.14:3000"
        if DEBUG else ""
    ),
)

CSRF_USE_SESSIONS = False


# ==========================================================
# NEXT.JS FRONTEND - CORS CONFIGURATION
# ==========================================================

CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://192.168.1.14:3000"
        if DEBUG else ""
    ),
)

# JWT credentials are sent through the Authorization header.
# No cross-origin cookies are required for this API design.
CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_ALL_ORIGINS = False


# ==========================================================
# SECURITY SETTINGS
# ==========================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = (
    "strict-origin-when-cross-origin"
)

X_FRAME_OPTIONS = "DENY"

# Enable once HTTPS deployment is configured correctly.
SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    False,
)

# Enable only behind a trusted reverse proxy that
# sanitizes incoming forwarded protocol headers.
if env_bool("DJANGO_TRUST_PROXY_SSL_HEADER", False):
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

SECURE_HSTS_SECONDS = int(
    os.getenv("DJANGO_HSTS_SECONDS", "0")
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
    False,
)

SECURE_HSTS_PRELOAD = env_bool(
    "DJANGO_HSTS_PRELOAD",
    False,
)


# ==========================================================
# LANGUAGE AND TIMEZONE
# ==========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC FILE CONFIGURATION
# ==========================================================

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


# ==========================================================
# MEDIA FILE CONFIGURATION
# ==========================================================

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DJANGO_DEFAULT_FROM_EMAIL",
    "no-reply@localhost",
)

EMAIL_HOST = os.getenv(
    "DJANGO_EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.getenv("DJANGO_EMAIL_PORT", "587")
)

EMAIL_USE_TLS = env_bool(
    "DJANGO_EMAIL_USE_TLS",
    True,
)

EMAIL_USE_SSL = env_bool(
    "DJANGO_EMAIL_USE_SSL",
    False,
)

EMAIL_HOST_USER = os.getenv(
    "DJANGO_EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.getenv(
    "DJANGO_EMAIL_HOST_PASSWORD",
    "",
)

EMAIL_TIMEOUT = 15

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured(
        "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True."
    )


# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================

LOGGING = {
    "version": 1,

    "disable_existing_loggers": False,

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },

    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# ==========================================================
# CRM CUSTOM CONFIGURATION
# ==========================================================

CRM_ALLOW_SUPERUSER_BOOTSTRAP = env_bool(
    "CRM_ALLOW_SUPERUSER_BOOTSTRAP",
    False,
)


# Employee invitation configuration
CRM_FRONTEND_URL = os.getenv(
    "CRM_FRONTEND_URL",
    "http://127.0.0.1:3000" if DEBUG else "",
).rstrip("/")

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # 24 hours