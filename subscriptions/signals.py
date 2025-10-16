from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.utils import timezone
from payments.models import Payment
from .models import UserSubscription, SubscriptionPlan

# Activate subscription after successful payment
@receiver(post_save, sender=Payment)
def activate_subscription_on_payment(sender, instance, created, **kwargs):
    if instance.status == "SUCCESS":
        user = instance.customer
        plan_key = getattr(instance, "plan_key", None)
        try:
            plan = SubscriptionPlan.objects.get(key=plan_key)
        except SubscriptionPlan.DoesNotExist:
            return
        sub, _ = UserSubscription.objects.get_or_create(user=user)
        sub.activate(plan, start_when=timezone.now())

# Create default plans after migrations
@receiver(post_migrate)
def create_default_plans(sender, **kwargs):
    from django.db.utils import OperationalError, ProgrammingError
    try:
        if not SubscriptionPlan.objects.exists():
            SubscriptionPlan.objects.get_or_create(key='monthly', defaults={
                'display_name': 'Monthly',
                'price': 10000.00,
                'duration_days': 30,
            })
            SubscriptionPlan.objects.get_or_create(key='yearly', defaults={
                'display_name': 'Yearly',
                'price': 100000.00,
                'duration_days': 365,
            })
            SubscriptionPlan.objects.get_or_create(key='three_years', defaults={
                'display_name': '3 Years',
                'price': 250000.00,
                'duration_days': 365*3,
            })
    except (OperationalError, ProgrammingError):
        pass
