# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Driver, Client, DemoRequest
from django.conf import settings
from django.core.mail import send_mail

# Existing signal for DemoRequest
@receiver(post_save, sender=DemoRequest)
def send_demo_request_email(sender, instance, created, **kwargs):
    if not created:
        return
    subject = "📞 New Demo Request Received"
    message = (
        f"Name:    {instance.full_name}\n"
        f"Email:   {instance.email}\n"
        f"Company: {instance.company or '—'}\n"
        f"Phone:   {instance.phone or '—'}\n\n"
        f"Date/Time: {instance.datetime or '—'}\n\n"
        f"Message:\n{instance.message or '—'}\n\n"
        f"Requested at: {instance.created_at:%Y-%m-%d %H:%M}"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        ["marvinavi24@gmail.com"],
        fail_silently=False,
    )

# New signal for CustomUser
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == 'driver':
        driver_data = getattr(instance, '_driver_data', {})
        Driver.objects.create(
            user=instance,
            license_number=driver_data.get('license_number'),
            frequent_location=driver_data.get('frequent_location'),
            personalID=driver_data.get('personalID')
        )
    elif instance.role == 'client':
        Client.objects.create(user=instance)