
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class InvitationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "crmapp.employee_invitation"


invitation_tokens = InvitationTokenGenerator()


def send_employee_invitation(employee):
    """
    Generate and email a secure employee invitation.

    The token expires according to PASSWORD_RESET_TIMEOUT.
    A successful send_mail return means the email backend
    accepted the message, not necessarily inbox delivery.
    """

    token = invitation_tokens.make_token(employee)

    query = urlencode({
        "user_id": str(employee.pk),
        "token": token,
    })

    frontend_url = settings.CRM_FRONTEND_URL

    if not frontend_url:
        raise ValueError(
            "CRM_FRONTEND_URL must be configured."
        )

    invitation_url = (
        f"{frontend_url}/accept-invitation?{query}"
    )

    subject = "You're invited to FlyingLyte CRM"

    message = (
        f"Hello {employee.name},\n\n"
        "You have been invited to join FlyingLyte CRM.\n\n"
        "Please click the link below to set your password:\n\n"
        f"{invitation_url}\n\n"
        "This link is valid for 24 hours.\n"
        "It can only be used once.\n\n"
        "If you weren't expecting this invitation, "
        "please ignore this email.\n\n"
        "Regards,\n"
        "FlyingLyte CRM Team"
    )

    result = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[employee.email],
        fail_silently=False,
    )

    return result == 1
