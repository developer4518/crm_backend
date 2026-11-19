
from django.contrib import admin
from django.urls import include, path

from crmapp.views import health


urlpatterns = [
    # ==========================================
    # DJANGO ADMIN
    # ==========================================

    path(
        "admin/",
        admin.site.urls,
    ),

    # ==========================================
    # HEALTH CHECK
    # ==========================================

    path(
        "api/v1/health/",
        health,
        name="api-health",
    ),

    # ==========================================
    # CRM API VERSION 1
    # ==========================================

    path(
        "api/v1/",
        include("crmapp.api_urls"),
    ),
]
