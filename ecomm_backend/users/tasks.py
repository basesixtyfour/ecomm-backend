from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_welcome_email(user_id, email, username):
    """Send a welcome email to the user after successful registration."""
    subject = "Welcome to Our Store!"
    message = f"""Hello {username},

Thank you for registering with us! We're excited to have you on board.

Get started by exploring our products and enjoy a seamless shopping experience.

Happy shopping!
The Team
"""
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(
        settings, "EMAIL_HOST_USER", "noreply@example.com"
    )
    print(from_email)
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[email],
        fail_silently=True,
    )
