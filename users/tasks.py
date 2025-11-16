from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, otp):
    subject = "Verify Your Torgovo Account"
    message = f"Your verification code is: {otp}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

@shared_task
def send_alert_email(user_email, subject, message):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])