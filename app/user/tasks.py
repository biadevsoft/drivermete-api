from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_activation_email(email, activation_url):
    message = f"""
    <html>
        <body>
            <p>Please click on the link below to activate your account:</p>
            <p><a href="{activation_url}">{activation_url}</a></p>
        </body>
    </html>
    """
    send_mail(
        'Activate your account',
        message,
        settings.DEFAULT_FROM_EMAIL,  # Replace with a valid sender email address
        [email],  # The recipient's email address
        fail_silently=False,
    )
