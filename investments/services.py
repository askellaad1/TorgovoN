"""
Quantum AI Investment Distribution Service
Handles pooling, distribution calculations, and scheduled payouts for Quantum AI investments
As specified in planning.md
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import QuantumInvestment, QuantumPool, QuantumTradeResult
from users.models import User

logger = logging.getLogger('TorgovoN.QuantumServices')


class QuantumDistributionService:
    """Service for managing Quantum AI investment pools and distributions"""

    def __init__(self):
        # Configurable percentage of actual P&L shown to users (default 20%)
        self.shown_profit_percentage = Decimal(str(getattr(settings, 'QUANTUM_SHOWN_PROFIT_PERCENTAGE', '0.20')))
        # Distribution frequency in days (default fortnightly)
        self.distribution_frequency_days = getattr(settings, 'QUANTUM_DISTRIBUTION_FREQUENCY_DAYS', 14)

    def calculate_pool_total(self, investment_date=None):
        """
        Calculate total pool amount for a specific date period
        Returns total pool of approved investments up to the specified date
        """
        try:
            queryset = QuantumInvestment.objects.filter(status='approved')

            if investment_date:
                queryset = queryset.filter(approved_at__lte=investment_date)
            else:
                queryset = queryset.filter(approved_at__lte=timezone.now())

            total = queryset.aggregate(
                total_amount=models.Sum('amount')
            )['total_amount'] or Decimal('0.00')

            logger.info(f"Calculated pool total: ${total}")
            return total

        except Exception as e:
            logger.error(f"Error calculating pool total: {e}")
            return Decimal('0.00')

    def get_approved_investments(self, pool_date=None):
        """
        Get all approved investments for the specified pool date
        """
        try:
            queryset = QuantumInvestment.objects.filter(status='approved')

            if pool_date:
                queryset = queryset.filter(approved_at__lte=pool_date)
            else:
                queryset = queryset.filter(approved_at__lte=timezone.now())

            return queryset.select_related('user').order_by('approved_at')

        except Exception as e:
            logger.error(f"Error getting approved investments: {e}")
            return QuantumInvestment.objects.none()

    def calculate_user_shares(self, total_pool, approved_investments):
        """
        Calculate proportional shares for each investor
        Returns dictionary mapping user_id to share amount
        Formula: (user_investment / total_pool) * shown_adjustment
        """
        shares = {}

        try:
            if total_pool <= 0:
                logger.warning("Total pool is zero, no shares to calculate")
                return shares

            for investment in approved_investments:
                user_share_percentage = Decimal(str(investment.amount)) / total_pool
                shares[investment.user.id] = user_share_percentage

            logger.info(f"Calculated shares for {len(shares)} investors")
            return shares

        except Exception as e:
            logger.error(f"Error calculating user shares: {e}")
            return {}

    def process_admin_trade_result(self, actual_pl, trade_description=""):
        """
        Process admin-executed trade results and create distribution records
        """
        try:
            with transaction.atomic():
                # Calculate shown adjustment (configurable percentage of actual P&L)
                shown_adjustment = actual_pl * self.shown_profit_percentage

                # Get total pool for this trade
                total_pool = self.calculate_pool_total()

                # Create quantum trade result record
                trade_result = QuantumTradeResult.objects.create(
                    actual_profit_loss=actual_pl,
                    shown_profit_loss=shown_adjustment,
                    profit_percentage=self.shown_profit_percentage,
                    trade_date=timezone.now(),
                    description=trade_description,
                    total_pool=total_pool,
                    total_investors=QuantumInvestment.objects.filter(status='approved').count(),
                    applied=False,  # Mark as ready for distribution
                )

                logger.info(f"Created trade result: PL=${actual_pl}, Shown={shown_adjustment}")
                return trade_result

        except Exception as e:
            logger.error(f"Error processing admin trade result: {e}")
            return None

    def calculate_distribution_amounts(self, trade_result):
        """
        Calculate individual distribution amounts based on trade result and user shares
        Formula: (user_investment / total_pool) * shown_adjustment
        """
        distributions = {}

        try:
            total_pool = trade_result['total_pool']
            shown_pl = trade_result['shown_profit_loss']

            # Get approved investments at the time of trade
            approved_investments = self.get_approved_investments(trade_result['trade_date'])
            user_shares = self.calculate_user_shares(total_pool, approved_investments)

            for user_id, share_percentage in user_shares.items():
                distribution_amount = shown_pl * share_percentage
                distributions[user_id] = distribution_amount

            logger.info(f"Calculated {len(distributions)} distribution amounts")
            return distributions

        except Exception as e:
            logger.error(f"Error calculating distribution amounts: {e}")
            return {}

    def execute_distribution(self, distributions, trade_result):
        """
        Execute distribution by updating user quantum balances
        """
        executed_distributions = []

        try:
            with transaction.atomic():
                for user_id, amount in distributions.items():
                    user = User.objects.get(id=user_id)

                    # Update user quantum balance
                    old_balance = user.quantum_balance
                    user.quantum_balance += amount
                    user.save()

                    # Create distribution record for audit trail
                    distribution_data = {
                        'user': user,
                        'amount': amount,
                        'old_balance': old_balance,
                        'new_balance': user.quantum_balance,
                        'trade_result': trade_result,
                        'distributed_at': timezone.now(),
                    }

                    executed_distributions.append(distribution_data)
                    logger.info(f"Distributed ${amount} to user {user_id} (old: ${old_balance}, new: ${user.quantum_balance})")

            return executed_distributions

        except Exception as e:
            logger.error(f"Error executing distribution: {e}")
            return []

    def get_next_distribution_date(self):
        """
        Calculate next distribution date based on frequency
        """
        try:
            last_distribution = QuantumTradeResult.objects.order_by('-trade_date').first()

            if not last_distribution:
                # If no previous distribution, start from today + frequency
                next_date = timezone.now() + timedelta(days=self.distribution_frequency_days)
            else:
                # Add frequency days to last distribution date
                next_date = last_distribution.trade_date + timedelta(days=self.distribution_frequency_days)

            return next_date.date()

        except Exception as e:
            logger.error(f"Error calculating next distribution date: {e}")
            return (timezone.now() + timedelta(days=self.distribution_frequency_days)).date()

    def get_distribution_summary(self):
        """
        Get comprehensive summary of distribution statistics
        """
        try:
            cache_key = 'quantum_distribution_summary'
            cached_summary = cache.get(cache_key)

            if cached_summary:
                return cached_summary

            total_pool = self.calculate_pool_total()
            approved_investments = self.get_approved_investments()
            total_investors = approved_investments.count()

            # Calculate statistics
            latest_trade = QuantumTradeResult.objects.order_by('-trade_date').first()
            next_distribution = self.get_next_distribution_date()

            summary = {
                'total_pool': float(total_pool),
                'total_investors': total_investors,
                'average_investment': float(total_pool / total_investors) if total_investors > 0 else 0,
                'latest_trade_date': latest_trade.trade_date.isoformat() if latest_trade else None,
                'latest_pl': float(latest_trade.shown_profit_loss) if latest_trade else 0,
                'next_distribution_date': next_distribution.isoformat(),
                'distribution_frequency_days': self.distribution_frequency_days,
                'shown_profit_percentage': float(self.shown_profit_percentage),
                'status': 'active' if total_investors > 0 else 'inactive',
            }

            # Cache for 5 minutes
            cache.set(cache_key, summary, 300)
            return summary

        except Exception as e:
            logger.error(f"Error getting distribution summary: {e}")
            return {}

    def process_manual_withdrawal(self, user, amount, withdrawal_method='manual'):
        """
        Process manual withdrawal request from user's quantum balance
        """
        try:
            with transaction.atomic():
                # Check user balance
                if user.quantum_balance < amount:
                    raise ValueError("Insufficient quantum balance")

                # Update user balance
                old_balance = user.quantum_balance
                user.quantum_balance -= amount
                user.save()

                # Create withdrawal record for audit trail
                withdrawal_data = {
                    'user': user,
                    'amount': amount,
                    'old_balance': old_balance,
                    'new_balance': user.quantum_balance,
                    'method': withdrawal_method,
                    'status': 'pending',
                    'requested_at': timezone.now(),
                }

                logger.info(f"Processed withdrawal request: ${amount} for user {user.id}")
                return withdrawal_data

        except ValueError as e:
            logger.warning(f"Withdrawal validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}")
            raise

    def validate_investment_amount(self, amount):
        """
        Validate investment amount meets minimum requirements
        """
        min_investment = Decimal(str(getattr(settings, 'QUANTUM_MIN_INVESTMENT', '100.00')))
        max_investment = Decimal(str(getattr(settings, 'QUANTUM_MAX_INVESTMENT', '100000.00')))

        if amount < min_investment:
            raise ValueError(f"Minimum investment is ${min_investment}")

        if amount > max_investment:
            raise ValueError(f"Maximum investment is ${max_investment}")

        return True

    def get_user_investment_history(self, user):
        """
        Get detailed investment history for a specific user
        """
        try:
            investments = QuantumInvestment.objects.filter(
                user=user
            ).select_related().order_by('-created_at')

            history = []
            for investment in investments:
                investment_data = {
                    'id': str(investment.id),
                    'amount': float(investment.amount),
                    'blockchain': investment.blockchain,
                    'wallet_address': investment.wallet_address,
                    'status': investment.status,
                    'created_at': investment.created_at.isoformat(),
                    'approved_at': investment.approved_at.isoformat() if investment.approved_at else None,
                    'current_balance': float(investment.current_balance) if investment.current_balance else 0,
                }

                history.append(investment_data)

            return history

        except Exception as e:
            logger.error(f"Error getting investment history: {e}")
            return []

    def recalculate_balances(self, from_date=None):
        """
        Force recalculation of all user quantum balances from scratch
        Used for corrections or data migration
        """
        try:
            logger.info("Starting quantum balance recalculation")

            # Get all trade results in chronological order
            from .models import QuantumTradeResult  # Import to avoid circular dependency
            trade_results = QuantumTradeResult.objects.filter(applied=True).order_by('trade_date')

            if from_date:
                trade_results = trade_results.filter(trade_date__gte=from_date)

            # Reset all quantum balances to 0
            User.objects.all().update(quantum_balance=0)

            # Recalculate from first trade result
            for trade_result in trade_results:
                distributions = self.calculate_distribution_amounts(trade_result)
                self.execute_distribution(distributions, trade_result)

            logger.info("Quantum balance recalculation completed")
            return True

        except Exception as e:
            logger.error(f"Error during balance recalculation: {e}")
            return False


# Singleton instance for easy access
quantum_service = QuantumDistributionService()


# Celery task for scheduled distributions
def execute_fortnightly_distribution():
    """
    Celery task to execute fortnightly quantum AI distributions
    """
    try:
        logger.info("Starting fortnightly quantum distribution")

        # Check if distribution is due
        next_distribution_date = quantum_service.get_next_distribution_date()
        today = timezone.now().date()

        if today < next_distribution_date:
            logger.info(f"Next distribution scheduled for {next_distribution_date}")
            return "No distribution due"

        # Get latest pending trade result
        from .models import QuantumTradeResult
        latest_trade = QuantumTradeResult.objects.filter(
            applied=True,
            distributed=False
        ).order_by('-trade_date').first()

        if not latest_trade:
            logger.info("No pending trade results to distribute")
            return "No pending trade results"

        # Execute distribution
        distributions = quantum_service.calculate_distribution_amounts(latest_trade)
        executed_distributions = quantum_service.execute_distribution(distributions, latest_trade)

        # Mark trade as distributed
        latest_trade.distributed = True
        latest_trade.distributed_at = timezone.now()
        latest_trade.save()

        result = f"Executed distribution for {len(executed_distributions)} users"
        logger.info(f"Fortnightly distribution completed: {result}")

        return result

    except Exception as e:
        error_msg = f"Fortnightly distribution failed: {e}"
        logger.error(error_msg)
        return error_msg


# Utility functions for admin dashboard
def get_quantum_pool_status():
    """Get current pool status for admin dashboard"""
    return quantum_service.get_distribution_summary()


def process_admin_trade(actual_pl, description=""):
    """Process admin-executed trade and prepare for distribution"""
    trade_result = quantum_service.process_admin_trade_result(actual_pl, description)

    if trade_result:
        # Prepare for next automatic distribution
        next_distribution = quantum_service.get_next_distribution_date()
        distributions = quantum_service.calculate_distribution_amounts(trade_result)

        return {
            'success': True,
            'trade_result': trade_result,
            'distributions_count': len(distributions),
            'next_distribution_date': next_distribution,
            'total_distributed': float(sum(distributions.values())),
        }

    return {'success': False, 'error': 'Failed to process trade'}


def get_user_quantum_report(user):
    """Generate comprehensive quantum investment report for user"""
    return {
        'current_balance': float(user.quantum_balance),
        'investment_history': quantum_service.get_user_investment_history(user),
        'distribution_summary': quantum_service.get_distribution_summary(),
    }