
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
from .jwt_api import CRMTokenRefreshView
from .auth_api import LoginView, LogoutView, MeView
from .registration_api import (
    AcceptInvitationView,
    EmployeeCreateView,
)


urlpatterns = [
    # ==========================================
    # JWT AUTHENTICATION
    # ==========================================

    path(
        "auth/login/",
        LoginView.as_view(),
        name="crm-auth-login",
    ),

    path(
        "auth/me/",
        MeView.as_view(),
        name="crm-auth-me",
    ),

    path(
        "auth/refresh/",
        TokenRefreshView.as_view(),
        name="crm-auth-refresh",
    ),

    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="crm-auth-logout",
    ),

    # ==========================================
    # EMPLOYEE MANAGEMENT
    # ==========================================

    path(
        "users/",
        EmployeeCreateView.as_view(),
        name="crm-user-create",
    ),

    # ==========================================
    # EMPLOYEE INVITATIONS
    # ==========================================

    path(
        "auth/invite/accept/",
        AcceptInvitationView.as_view(),
        name="crm-invite-accept",
    ),
    path(
    "auth/refresh/",
    CRMTokenRefreshView.as_view(),
    name="crm-auth-refresh",
    ),
]

