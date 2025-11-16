from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                "name": "Basic (Free)",
                "plan_type": "basic",
                "price_monthly": 0.00,
                "webhook_limit": 50,
                "allows_custom_bots": False,
                "allows_grid_bots": False,
                "allows_martingale_bots": False,
                "allows_telegram_signals": False,
                "allows_telegram_alerts": False,
                "allows_quantum_ai": False
            },
            {
                "name": "Pro",
                "plan_type": "pro",
                "price_monthly": 29.99,
                "webhook_limit": 500,
                "allows_custom_bots": True,
                "allows_grid_bots": True,
                "allows_martingale_bots": True,
                "allows_telegram_signals": False,
                "allows_telegram_alerts": True,
                "allows_quantum_ai": False
            },
            {
                "name": "Premium",
                "plan_type": "premium",
                "price_monthly": 49.99,
                "webhook_limit": 2000,
                "allows_custom_bots": True,
                "allows_grid_bots": True,
                "allows_martingale_bots": True,
                "allows_telegram_signals": True,
                "allows_telegram_alerts": True,
                "allows_quantum_ai": False
            },
            {
                "name": "Quantum AI Access",
                "plan_type": "quantum",
                "price_monthly": 99.99,
                "webhook_limit": 5000,
                "allows_custom_bots": True,
                "allows_grid_bots": True,
                "allows_martingale_bots": True,
                "allows_telegram_signals": True,
                "allows_telegram_alerts": True,
                "allows_quantum_ai": True
            }
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                plan_type=plan_data["plan_type"],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated plan: {plan.name}"))