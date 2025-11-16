from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_payment_confirmation(user_email, payment_id):
    send_mail(
        "Payment Received",
        f"Your payment {payment_id} has been received and is pending approval.",
        settings.DEFAULT_FROM_EMAIL,
        [user_email]
    )