
import re

from django.conf import settings
from django.contrib.auth import (
    get_user_model,
    password_validation,
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db import IntegrityError, transaction

from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .auth_api import AuthView, employee_profile
from .models import Role, RoleGrant


User = get_user_model()


# ==========================================================
# INVITATION TOKEN
# ==========================================================

class InvitationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "crmapp.employee_invitation"


invitation_tokens = InvitationTokenGenerator()


# ==========================================================
# MOBILE VALIDATION
# ==========================================================

def validate_mobile_number(value):
    value = value.strip()

    if not re.fullmatch(r"\+?[1-9]\d{7,14}", value):
        raise serializers.ValidationError(
            "Enter a valid mobile number with "
            "8 to 15 digits and an optional '+'."
        )

    return value


# ==========================================================
# EMPLOYEE REGISTRATION SERIALIZER
# ==========================================================

class EmployeeInput(serializers.Serializer):

    name = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
    )

    email = serializers.EmailField(
        max_length=254,
    )

    # Required
    personal_mobile = serializers.CharField(
        max_length=16,
    )

    # Optional
    company_mobile = serializers.CharField(
        max_length=16,
        required=False,
        allow_blank=True,
        default="",
    )

    # Optional employee address
    address = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    # Required CRM role
    role = serializers.CharField(
        max_length=2,
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_personal_mobile(self, value):
        return validate_mobile_number(value)

    def validate_company_mobile(self, value):
        if not value:
            return ""
        return validate_mobile_number(value)

    def validate_role(self, value):
        role_code = value.strip().upper()

        if not Role.objects.filter(
            code=role_code
        ).exists():
            raise serializers.ValidationError(
                "Invalid CRM role code."
            )

        return role_code


# ==========================================================
# ACCEPT INVITATION SERIALIZER
# ==========================================================

class AcceptInvitationInput(serializers.Serializer):

    user_id = serializers.UUIDField()

    token = serializers.CharField(
        max_length=200,
    )

    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=4096,
    )


# ==========================================================
# EMPLOYEE REGISTRATION API
# ==========================================================

class EmployeeCreateView(AuthView):

    def post(self, request):

        actor = request.user

        # JWT authentication is enforced by AuthView.
        # Check the actor's current CRM roles.
        actor_roles = set(
            actor.crm_role_grants.filter(
                revoked_at__isnull=True
            ).values_list(
                "role__code",
                flat=True,
            )
        )

        # Local bootstrap only.
        local_bootstrap = (
            settings.DEBUG
            and getattr(
                settings,
                "CRM_ALLOW_SUPERUSER_BOOTSTRAP",
                False,
            )
            and actor.is_superuser
        )

        if not (
            actor_roles.intersection({"SA", "AD"})
            or local_bootstrap
        ):
            return self.error(
                "permission_denied",
                "Only CRM administrators can register employees.",
                403,
            )

        form = EmployeeInput(data=request.data)

        if not form.is_valid():
            return self.error(
                "validation_error",
                "Invalid employee registration data.",
                400,
                form.errors,
            )

        data = form.validated_data

        # Only SA can assign administrative roles.
        if data["role"] in {"SA", "AD"}:
            if "SA" not in actor_roles and not local_bootstrap:
                return self.error(
                    "permission_denied",
                    "Only a Super Admin can assign "
                    "administrative roles.",
                    403,
                )

        # Create employee and role grant atomically.
        try:
            with transaction.atomic():

                role = Role.objects.get(
                    code=data["role"]
                )

                employee = User.objects.create_user(
                    email=data["email"],
                    name=data["name"],
                    password=None,
                    personal_mobile=data["personal_mobile"],
                    company_mobile=data.get(
                        "company_mobile",
                        "",
                    ),
                    address=data.get(
                        "address",
                        "",
                    ),
                )

                RoleGrant.objects.create(
                    user=employee,
                    role=role,
                    granted_by=actor,
                    reason="Assigned during employee registration",
                )

        except Role.DoesNotExist:
            return self.error(
                "validation_error",
                "Selected CRM role no longer exists.",
                400,
            )

        except IntegrityError:
            if User.objects.filter(
                email__iexact=data["email"]
            ).exists():
                return self.error(
                    "email_exists",
                    "An employee with this email already exists.",
                    409,
                )
            raise

        # Return employee details including address.
        profile = employee_profile(employee)

        profile.update({
            "personal_mobile": employee.personal_mobile,
            "company_mobile": employee.company_mobile,
            "address": employee.address,
        })

        return Response(
            profile,
            status=201,
        )


# ==========================================================
# ACCEPT EMPLOYEE INVITATION
# ==========================================================

class AcceptInvitationView(AuthView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        form = AcceptInvitationInput(
            data=request.data
        )

        if not form.is_valid():
            return self.error(
                "validation_error",
                "Invalid invitation input.",
                400,
                form.errors,
            )

        data = form.validated_data

        employee = User.objects.filter(
            pk=data["user_id"],
            is_active=True,
        ).first()

        if (
            employee is None
            or employee.has_usable_password()
            or not invitation_tokens.check_token(
                employee,
                data["token"],
            )
        ):
            return self.error(
                "invalid_invitation",
                "This invitation is invalid, "
                "expired, or already used.",
                400,
            )

        try:
            password_validation.validate_password(
                data["new_password"],
                user=employee,
            )

        except DjangoValidationError as exc:
            return self.error(
                "validation_error",
                "Please choose a different password.",
                400,
                {
                    "new_password": list(exc.messages)
                },
            )

        # Single-use invitation protection.
        previous_password = employee.password

        employee.set_password(
            data["new_password"]
        )

        updated = User.objects.filter(
            pk=employee.pk,
            is_active=True,
            password=previous_password,
        ).update(
            password=employee.password
        )

        if not updated:
            return self.error(
                "invalid_invitation",
                "Invitation already used.",
                400,
            )

        return Response(status=204)
