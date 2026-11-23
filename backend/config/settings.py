import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import dotenv_values, load_dotenv
from corsheaders.defaults import default_headers

try:
    import dj_database_url
except ImportError:  # Local environments may not have reinstalled requirements.txt yet.
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_ENV = dotenv_values(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

DEBUG_DEFAULT = "False" if os.getenv("RENDER") else "True"
DEBUG = os.getenv("DJANGO_DEBUG", DEBUG_DEFAULT).lower() in {"1", "true", "yes"}


def mail_environment_value(name, default=""):
    local_value = (LOCAL_ENV.get(name) or "").strip()
    if DEBUG and local_value:
        return local_value
    return (os.getenv(name) or default).strip()


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured when debug is disabled.")
    SECRET_KEY = "local-development-key-do-not-use-in-production"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
    if host.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "accounts.apps.AccountsConfig",
    "products.apps.ProductsConfig",
    "cart.apps.CartConfig",
    "wishlist.apps.WishlistConfig",
    "coupons.apps.CouponsConfig",
    "orders.apps.OrdersConfig",
    "payments.apps.PaymentsConfig",
    "reviews.apps.ReviewsConfig",
    "communications.apps.CommunicationsConfig",
    "dashboard.apps.DashboardConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

try:
    import whitenoise  # noqa: F401
except ImportError:  # WhiteNoise is installed from requirements.txt in production.
    pass
else:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if os.getenv("RENDER") and not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL must be configured for the Render deployment.")
if DATABASE_URL:
    if dj_database_url is None:
        raise ImproperlyConfigured(
            "Install dj-database-url from requirements.txt to use DATABASE_URL."
        )
    try:
        DATABASES = {
            "default": dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                ssl_require=not DEBUG,
            )
        }
    except ValueError as error:
        raise ImproperlyConfigured("DATABASE_URL is not a valid database URL.") from error
elif DB_ENGINE == "mysql":
    DB_NAME = os.getenv("DB_NAME", "").strip()
    DB_USER = os.getenv("DB_USER", "").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    if not DB_NAME or not DB_USER or not DB_PASSWORD:
        raise ImproperlyConfigured(
            "DB_NAME, DB_USER, and DB_PASSWORD must be configured when DB_ENGINE is 'mysql'."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE must be either 'sqlite' or 'mysql'.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    if not any("whitenoise.middleware.WhiteNoiseMiddleware" == item for item in MIDDLEWARE):
        raise ImproperlyConfigured("Install whitenoise from requirements.txt for production static files.")
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

# Render terminates HTTPS at its proxy and forwards the original scheme here.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_RATES": {
        "contact-submission": "5/hour",
        "newsletter-subscription": "5/hour",
        "faq-answer": "10/hour",
        "auth-register": "5/hour",
        "auth-login": "10/hour",
        "email-verify": "10/hour",
        "email-resend": "5/hour",
        "email-change": "3/hour",
        "password-reset": "5/hour",
        "password-reset-confirm": "20/hour",
        "password-change": "5/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
if FRONTEND_BASE_URL.startswith(("http://", "https://")) and FRONTEND_BASE_URL not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_BASE_URL)
CORS_ALLOW_HEADERS = (*default_headers, "x-cart-token", "idempotency-key")
def decimal_setting(name, default):
    try:
        value = Decimal(os.getenv(name, default))
    except InvalidOperation as error:
        raise ImproperlyConfigured(f"{name} must be a non-negative decimal number.") from error
    if not value.is_finite() or value < 0:
        raise ImproperlyConfigured(f"{name} must be a non-negative decimal number.")
    return value


ORDER_SHIPPING_FEE = decimal_setting("ORDER_SHIPPING_FEE", "0.00")
ORDER_TAX_RATE_PERCENT = decimal_setting("ORDER_TAX_RATE_PERCENT", "0")
if ORDER_TAX_RATE_PERCENT > 100:
    raise ImproperlyConfigured("ORDER_TAX_RATE_PERCENT cannot exceed 100.")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
if FRONTEND_BASE_URL.startswith(("http://", "https://")) and FRONTEND_BASE_URL not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_BASE_URL)
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = mail_environment_value("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(mail_environment_value("EMAIL_PORT", "587"))
EMAIL_USE_TLS = mail_environment_value("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes"}
EMAIL_USE_SSL = mail_environment_value("EMAIL_USE_SSL", "False").lower() in {"1", "true", "yes"}
EMAIL_HOST_USER = mail_environment_value("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = mail_environment_value("EMAIL_HOST_PASSWORD")
if EMAIL_HOST.lower() == "smtp.gmail.com":
    # Google displays app passwords in groups; SMTP expects the same value without spaces.
    EMAIL_HOST_PASSWORD = "".join(EMAIL_HOST_PASSWORD.split())
EMAIL_TIMEOUT = int(mail_environment_value("EMAIL_TIMEOUT", "20"))
# Send from the same mailbox that authenticates with Gmail SMTP.
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SUPPORT_EMAIL = mail_environment_value("SUPPORT_EMAIL") or DEFAULT_FROM_EMAIL
PASSWORD_RESET_TIMEOUT = 60 * 60
