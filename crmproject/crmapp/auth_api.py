
from uuid import uuid4

from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .mixins import StandardResponseMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Membership


# ==========================================================
# EMPLOYEE PROFILE
# ==========================================================

def employee_profile(user):
    roles = list(
        user.crm_role_grants.filter(
            revoked_at__isnull=True
        )
        .order_by("role__code")
        .values_list("role__code", flat=True)
    )

    team_id = (
        Membership.objects.filter(
            user=user,
            team__is_active=True
        )
        .values_list("team_id", flat=True)
        .first()
    )

    return {
        "id": str(user.pk),
        "name": user.name,
        "email": user.email,
        "personal_mobile": user.personal_mobile,
        "company_mobile": user.company_mobile,
        "address": user.address,
        "roles": roles,
        "team_id": str(team_id) if team_id else None,
        "permissions": sorted(user.get_all_permissions()),
    }


# ==========================================================
# SERIALIZERS
# ==========================================================

class LoginInput(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class LogoutInput(serializers.Serializer):
    refresh = serializers.CharField()


# ==========================================================
# BASE AUTH VIEW
# ==========================================================

class AuthView(StandardResponseMixin, APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request, response, *args, **kwargs
        )
        response["Cache-Control"] = "no-store"
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )
        response["Cache-Control"] = "no-store"
        return response


# ==========================================================
# LOGIN - GENERATE JWT TOKENS
# ==========================================================

class LoginView(AuthView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        form = LoginInput(data=request.data)

        if not form.is_valid():
            return self.error(
                "validation_error",
                "Invalid login data.",
                400,
                form.errors,
            )

        user = authenticate(
            request._request,
            email=form.validated_data["email"].strip().lower(),
            password=form.validated_data["password"],
        )

        if user is None or not user.is_active:
            return self.error(
                "invalid_credentials",
                "Invalid email or password.",
                401,
            )

        refresh = RefreshToken.for_user(user)

        return self.success_response(
             data={
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "token_type": "Bearer",
            "user": employee_profile(user),
        },
        message="Login successful.",
        status_code=200,
)


# ==========================================================
# AUTH ME - CURRENT USER
# ==========================================================

class MeView(AuthView):

    def get(self, request):
        return self.success_response(
            data=employee_profile(request.user),
            message="Employee profile fetched successfully.",
        )

# ==========================================================
# LOGOUT - BLACKLIST REFRESH TOKEN
# ==========================================================


# ==========================================================
# LOGOUT - JWT REFRESH TOKEN BLACKLIST
# ==========================================================


# ==========================================================
# LOGOUT - JWT REFRESH TOKEN BLACKLIST
# ==========================================================

class LogoutView(AuthView):
    """
    POST /api/v1/auth/logout/

    Authentication:
        Authorization: Bearer <access_token>

    Body:
        {
            "refresh": "<refresh_token>"
        }
    """

    def post(self, request):
        # Validate request body.
        form = LogoutInput(data=request.data)

        if not form.is_valid():
            return self.error_response(
                code="validation_error",
                message="A valid refresh token is required.",
                status_code=400,
                fields=form.errors,
            )

        try:
            refresh = RefreshToken(
                form.validated_data["refresh"]
            )

            # Ensure refresh token belongs to
            # the authenticated employee.
            token_user_id = str(
                refresh.payload.get("user_id", "")
            )

            if token_user_id != str(request.user.pk):
                return self.error_response(
                    code="invalid_token",
                    message=(
                        "Refresh token does not belong "
                        "to the authenticated user."
                    ),
                    status_code=403,
                )

            # Revoke the refresh token.
            refresh.blacklist()

        except TokenError:
            return self.error_response(
                code="invalid_token",
                message="Refresh token is invalid, expired, or revoked.",
                status_code=401,
            )

        # Consistent JSON response.
        return self.success_response(
            data=None,
            message="Logged out successfully.",
            status_code=200,
        )

