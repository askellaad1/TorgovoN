from django.db import transaction
from .models import QuantumInvestment, QuantumPool, QuantumTradeResult, QuantumPool
from users.models import User
from django.conf import settings
import uuid


class QuantumDistributionService:
    @staticmethod
    @transaction.atomic
    def distribute_profit_loss(trade_result: QuantumTradeResult):
        """
        Distribute profit/loss proportionally among all approved investors
        """
        if trade_result.applied:
            return

        # Get admin-configured cap (default 20%)
        distribution_cap = getattr(settings, 'QUANTUM_DISTRIBUTION_CAP', 0.20)

        # Calculate shown adjustment based on cap
        actual_pl = trade_result.actual_profit_loss
        shown_adjustment = actual_pl * distribution_cap

        # Get total pool
        pool = QuantumPool.objects.get(id=1)
        total_invested = pool.total_invested

        if total_invested <= 0:
            return

        # Get all approved investments
        approved_investments = QuantumInvestment.objects.filter(status='approved')

        # Distribute proportionally
        for investment in approved_investments:
            user_share = investment.amount / total_invested
            user_adjustment = user_share * shown_adjustment

            # Update user's quantum balance
            user = investment.user
            user.quantum_balance += user_adjustment
            user.save()

            # Log distribution (optional: create separate model for audit trail)

        # Mark as applied
        trade_result.shown_adjustment = shown_adjustment
        trade_result.applied = True
        trade_result.save()

        # Send notifications for significant changes
        if abs(shown_adjustment) > 100:  # Arbitrary threshold
            from users.tasks import send_alert_email
            for investment in approved_investments:
                if abs(user_share * shown_adjustment) > 10:
                    send_alert_email.delay(
                        investment.user.email,
                        "Quantum AI Balance Update",
                        f"Your balance has been updated by {user_share * shown_adjustment:.2f} USDT"
                    )


    @staticmethod
    def get_user_share(user: User):
        """Calculate user's share in the pool"""
        pool = QuantumPool.objects.get(id=1)
        if pool.total_invested == 0:
            return 0
        return user.quantum_balance / pool.total_invested