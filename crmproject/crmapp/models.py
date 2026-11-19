
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


# ==========================================================
# MOBILE NUMBER VALIDATOR
# ==========================================================

mobile_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message=(
        "Enter a valid mobile number with 8 to 15 digits, "
        "optionally starting with '+'."
    ),
)


# ==========================================================
# CUSTOM USER MANAGER
# ==========================================================

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email or not email.strip():
            raise ValueError("An email address is required.")

        email = self.normalize_email(email.strip()).lower()

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields["is_staff"] is not True:
            raise ValueError(
                "A superuser must have is_staff=True."
            )

        if extra_fields["is_superuser"] is not True:
            raise ValueError(
                "A superuser must have is_superuser=True."
            )

        if not password:
            raise ValueError(
                "A superuser password is required."
            )

        return self.create_user(
            email,
            password,
            **extra_fields,
        )


# ==========================================================
# CUSTOM USER MODEL
# ==========================================================


class User(AbstractUser):

    # ==================================================
    # USER IDENTIFICATION
    # ==================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    username = None

    email = models.EmailField(
        unique=True,
        max_length=254,
    )

    name = models.CharField(
        max_length=150,
    )

    # ==================================================
    # EMPLOYEE CONTACT DETAILS
    # ==================================================

    # Required for new employee registration.
    # blank=True allows existing users without a mobile
    # number to remain valid during migration.
    # EmployeeInput serializer enforces this requirement.

    personal_mobile = models.CharField(
        max_length=16,
        validators=[mobile_validator],
        blank=True,
        default="",
    )

    # Optional company-issued mobile number.

    company_mobile = models.CharField(
        max_length=16,
        validators=[mobile_validator],
        blank=True,
        default="",
    )

    # ==================================================
    # EMPLOYEE ADDRESS
    # ==================================================

    # Optional employee address.
    # Can store street, city, state, PIN and country.

    address = models.TextField(
        max_length=500,
        blank=True,
        default="",
    )

    # ==================================================
    # AUTHENTICATION CONFIGURATION
    # ==================================================

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "name",
        "personal_mobile",
    ]

    objects = UserManager()

    # ==================================================
    # MODEL CONFIGURATION
    # ==================================================

    class Meta:
        ordering = ["name", "email"]

    def __str__(self):
        return self.email



# ==========================================================
# TEAM MODEL
# ==========================================================

class Team(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=120,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ==========================================================
# ROLE MODEL
# ==========================================================

class Role(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    code = models.CharField(
        max_length=2,
        unique=True,
    )

    name = models.CharField(
        max_length=80,
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ==========================================================
# TEAM MEMBERSHIP MODEL
# ==========================================================

class Membership(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        "crmapp.User",
        on_delete=models.PROTECT,
        related_name="crm_membership",
    )

    team = models.ForeignKey(
        "crmapp.Team",
        on_delete=models.PROTECT,
        related_name="memberships",
    )

    def __str__(self):
        return f"{self.user.email} - {self.team.name}"


# ==========================================================
# ROLE GRANT MODEL
# ==========================================================

class RoleGrant(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        "crmapp.User",
        on_delete=models.PROTECT,
        related_name="crm_role_grants",
    )

    role = models.ForeignKey(
        "crmapp.Role",
        on_delete=models.PROTECT,
        related_name="grants",
    )

    granted_by = models.ForeignKey(
        "crmapp.User",
        on_delete=models.PROTECT,
        related_name="issued_crm_role_grants",
    )

    reason = models.CharField(
        max_length=255,
    )

    granted_at = models.DateTimeField(
        auto_now_add=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(
                    revoked_at__isnull=True
                ),
                name="unique_active_crm_role_grant",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.role.code}"
        )
