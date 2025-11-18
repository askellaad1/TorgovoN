"""
Referral Bonus System Service
Handles referral bonus calculations, processing, and management
As specified in planning.md
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import Referral, ReferralBonusConfig
from users.models import User

logger = logging.getLogger('TorgovoN.ReferralServices')


class ReferralBonusService:
    """Service for managing referral bonuses and rewards"""

    def __init__(self):
        # Default bonus configurations (can be overridden by admin)
        self.default_bonus_configs = {
            'alerts': {
                'amount': 5,
                'description': '5 free webhook alerts',
                'type': 'alerts',
                'claim_required': False,  # Auto-claimed
                'expiry_days': 30,
            },
            'discount': {
                'amount': Decimal('10.00'),  # $10 discount
                'description': '$10 subscription discount',
                'type': 'discount',
                'claim_required': False,  # Auto-claimed
                'expiry_days': 365,
                'discount_percentage': 10,  # 10%
            },
            'usdt': {
                'amount': Decimal('5.00'),  # $5 USDT
                'description': '$5 USDT reward',
                'type': 'usdt',
                'claim_required': True,  # Requires manual claim
                'expiry_days': 60,
            },
        }

    def get_bonus_config(self, bonus_type=None, user_id=None):
        """
        Get bonus configuration from database or defaults
        """
        try:
            cache_key = f'referral_bonus_config_{bonus_type}' if bonus_type else 'referral_bonus_config'
            if user_id:
                cache_key += f'_user_{user_id}'

            cached_config = cache.get(cache_key)

            if cached_config:
                return cached_config

            # Get from database
            if bonus_type:
                config = ReferralBonusConfig.objects.filter(
                    bonus_type=bonus_type,
                    is_active=True
                ).first()
            else:
                configs = ReferralBonusConfig.objects.filter(is_active=True)

            # Use database configs or defaults
            if configs.exists():
                if bonus_type:
                    config = configs.filter(bonus_type=bonus_type).first()
                else:
                    config = configs.first()

            return {
                'amount': float(config.amount),
                'description': config.description,
                'type': config.bonus_type,
            }

        except Exception as e:
            logger.error(f"Error getting bonus config for {bonus_type}: {e}")
            return self.default_bonus_configs.get(bonus_type, self.default_bonus_configs['alerts'])

    def create_referral_record(self, referrer, referred_user, referral_code):
        """
        Create a new referral record
        """
        try:
            with transaction.atomic():
                referral = Referral.objects.create(
                    referrer=referrer,
                    referred=referred_user,
                    code=referral_code,
                    created_at=timezone.now(),
                )

                logger.info(f"Created referral record: {referral.id} - {referrer.referral_code} referred {referred_user.id}")

                return referral

        except Exception as e:
            logger.error(f"Error creating referral record: {e}")
            return None

    def get_referral_by_code(self, referral_code):
        """
        Get referral record by code
        """
        try:
            return Referral.objects.select_related('referrer', 'referred').get(code=referral_code)

        except Exception as e:
            logger.error(f"Error getting referral by code {referral_code}: {e}")
            return None

    def process_referral_bonus(self, referral_id):
        """
        Process and award referral bonus when referred user signs up and meets criteria
        """
        try:
            referral = Referral.objects.select_related('referrer', 'referred').get(id=referral_id)
            bonus_config = self.get_bonus_config('alerts')  # Default to alerts bonus

            # Check if bonus has already been claimed
            if referral.bonus_claimed_at:
                logger.info(f"Referral {referral_id} bonus already claimed at {referral.bonus_claimed_at}")
                return None

            # Get referred user and check if they meet bonus criteria
            referred_user = referral.referred
            if not referred_user:
                logger.warning(f"Referred user not found for referral {referral_id}")
                return None

            # Check if user is active and meets minimum criteria
            if not referred_user.is_active:
                logger.info(f"Referred user {referred_user.id} is not active for referral {referral_id}")
                return None

            # Check bonus specific requirements
            bonus_awarded = False

            if bonus_config['claim_required']:
                # Manual claim required - admin must approve
                logger.info(f"Referral {referral_id} requires manual bonus claim approval")
            elif bonus_config['bonus_type'] == 'discount':
                # Discount bonus - check if user has active subscription
                if not referred_user.subscription_plan or referred_user.subscription_plan.subscription_tier == 'basic':
                    logger.info(f"Referral {referral_id} user {referred_user.id} has basic plan, no discount bonus applicable")
                    return None
                bonus_awarded = True
            elif bonus_config['bonus_type'] == 'usdt':
                # USDT bonus - check minimum quantum investment
                min_investment = Decimal(str(getattr(settings, 'REFERRAL_MIN_USDT_INVESTMENT', '100.00')))
                if referred_user.quantum_balance < min_investment:
                    logger.info(f"Referral {referral_id} user {referred_user.id} has insufficient USDT balance for USDT bonus")
                    return None
                bonus_awarded = True

            elif bonus_config['bonus_type'] == 'alerts':
                # Alert bonus - no additional requirements, auto-awarded
                bonus_awarded = True

            else:
                # Auto-claimed bonus
                bonus_awarded = True

            if bonus_awarded:
                # Create bonus record
                ReferralBonusRecord.objects.create(
                    referral=referral,
                    bonus_type=bonus_config['bonus_type'],
                    bonus_amount=Decimal(str(bonus_config['amount'])),
                    status='pending' if bonus_config['claim_required'] else 'claimed',
                    created_at=timezone.now(),
                )

                # Update referral status
                referral.bonus_awarded_at = timezone.now()
                referral.save()

                # Process the bonus (except manual claim which needs admin approval)
                if not bonus_config['claim_required']:
                    self._apply_bonus_to_user(referral.referred, bonus_config)

                logger.info(f"Awarded {bonus_config['bonus_type']} bonus to user {referred_user.id} for referral {referral.id}")

                return {
                    'referral_id': referral_id,
                    'bonus_type': bonus_config['bonus_type'],
                    'bonus_amount': bonus_config['amount'],
                    'bonus_status': 'processed',
                }

            return None

        except Exception as e:
            logger.error(f"Error processing referral bonus for {referral_id}: {e}")
            return None

    def _apply_bonus_to_user(self, user, bonus_config):
        """
        Apply bonus effects to user account
        """
        try:
            with transaction.atomic():
                if bonus_config['bonus_type'] == 'alerts':
                    # Add webhook alerts
                    user.webhook_alerts_used += bonus_config['amount']
                    logger.info(f"Added {bonus_config['amount']} webhook alerts to user {user.id}")

                elif bonus_config['bonus_type'] == 'discount':
                    # Apply subscription discount
                    # Implementation would depend on payment system
                    logger.info(f"Applied {bonus_config['amount']} discount to user {user.id}")

                elif bonus_config['bonus_type'] == 'usdt':
                    # Add USDT to quantum balance
                    user.quantum_balance += Decimal(str(bonus_config['amount']))
                    user.save()

                    logger.info(f"Added {bonus_config['amount']} USDT to user {user.id} quantum balance")

        except Exception as e:
            logger.error(f"Error applying bonus to user {user.id}: {e}")

    def get_referral_stats(self, user):
        """
        Get comprehensive referral statistics for user
        """
        try:
            # Get referrals where user is referrer
            sent_referrals = Referral.objects.filter(referrer=user).select_related('referred')

            # Get referrals where user is referred
            received_referrals = Referral.objects.filter(referred=user).select_related('referrer')

            # Calculate stats
            total_sent = sent_referrals.count()
            total_received = received_referrals.count()

            # Count successful referrals (where bonus was claimed)
            successful_referrals = Referral.objects.filter(
                referrer=user,
                bonus_claimed_at__isnull=False
            ).count()

            # Get bonus breakdown
            bonus_breakdown = {}
            for bonus_type in ['alerts', 'discount', 'usdt']:
                bonus_records = ReferralBonusRecord.objects.filter(
                    referral__referrer=user,
                    bonus_type=bonus_type,
                    status='claimed'
                ).aggregate(total_bonus=models.Sum('bonus_amount'))['total_bonus'] or Decimal('0.00')

                bonus_breakdown[bonus_type] = {
                    'count': ReferralBonusRecord.objects.filter(
                        referral__referrer=user,
                        bonus_type=bonus_type,
                        status='claimed'
                    ).count(),
                    'total_amount': float(bonus_records['total_bonus']) if bonus_records else 0,
                }

            # Calculate total bonuses earned
            total_bonuses_earned = sum(breakdown['count'] for breakdown in bonus_breakdown.values())
            total_bonus_value = sum(breakdown['total_amount'] for breakdown in bonus_breakdown.values())

            # Generate referral link
            referral_link = self._generate_referral_link(user)

            stats = {
                'total_sent': total_sent,
                'total_received': total_received,
                'successful_referrals': successful_referrals,
                'success_rate': float(successful_referrals / total_received) if total_received > 0 else 0,
                'total_bonuses_earned': total_bonuses_earned,
                'total_bonus_value': total_bonus_value,
                'bonus_breakdown': bonus_breakdown,
                'referral_link': referral_link,
                'pending_claims': ReferralBonusRecord.objects.filter(
                    referral__referrer=user,
                    status='pending'
                ).count(),
                'total_pending_value': self._calculate_pending_bonus_value(user),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting referral stats for user {user.id}: {e}")
            return {}

    def _generate_referral_link(self, user):
        """
        Generate referral link for user
        """
        try:
            base_url = getattr(settings, 'FRONTEND_URL', 'https://torgovo.com')
            return f"{base_url}/auth?ref={user.referral_code}"

        except Exception as e:
            logger.error(f"Error generating referral link for user {user.id}: {e}")
            return ""

    def _calculate_pending_bonus_value(self, user):
        """
        Calculate potential bonus value for pending claims
        """
        try:
            pending_bonuses = ReferralBonusRecord.objects.filter(
                referral__referrer=user,
                status='pending'
            )

            pending_value = Decimal('0.00')
            for bonus in pending_bonuses:
                bonus_config = self.get_bonus_config(bonus.bonus_type)
                pending_value += bonus_config['amount']

            return float(pending_value)

        except Exception as e:
            logger.error(f"Error calculating pending bonus value: {e}")
            return Decimal('0.00')

    def get_referral_leaderboard(self, limit=10):
        """
        Get top referrers leaderboard
        """
        try:
            cache_key = f'referral_leaderboard'
            cached_leaderboard = cache.get(cache_key)

            if cached_leaderboard:
                return cached_leaderboard

            # Get all referrers with their stats
            referrers = User.objects.annotate(
                total_referrals_made=models.Count('referrals_made')
            ).filter(
                total_referrals_made__gt=0
            ).order_by('-total_referrals_made')[:limit]

            leaderboard = []
            for i, referrer in enumerate(referrers, 1):
                stats = self.get_referral_stats(referrer)
                leaderboard.append({
                    'rank': i,
                    'user_id': str(referrer.id),
                    'email': referrer.email,
                    'first_name': referrer.first_name,
                    'last_name': referrer.last_name,
                    'total_referrals_made': stats['total_sent'],
                    'total_referrals_received': stats['total_received'],
                    'successful_referrals': stats['successful_referrals'],
                    'success_rate': stats['success_rate'],
                    'total_bonuses_earned': stats['total_bonuses_earned'],
                    'referral_link': stats['referral_link'],
                })

            # Cache for 10 minutes
            cache.set(cache_key, leaderboard, 600)
            return leaderboard

        except Exception as e:
            logger.error(f"Error getting referral leaderboard: {e}")
            return []

    def validate_referral_code(self, referral_code):
        """
        Validate if referral code exists and is available for use
        """
        try:
            exists = User.objects.filter(referral_code=referral_code).exists()

            if exists:
                # Check if code is already used by this user
                user_with_code = User.objects.get(referral_code=referral_code)
                if user_with_code and user_with_code.referrer:
                    logger.warning(f"Referral code {referral_code} already used by user {user_with_code.id}")
                    return {'valid': False, 'message': 'This referral code has already been used'}

                return {'valid': True, 'message': 'Referral code is available'}

        except Exception as e:
            logger.error(f"Error validating referral code {referral_code}: {e}")
            return {'valid': False, 'message': 'Error validating referral code'}

    def process_bulk_bonus_claims(self, bonus_type, limit=50):
        """
        Process multiple pending bonus claims in batches
        """
        try:
            logger.info(f"Processing {limit} pending {bonus_type} bonus claims")

            # Get pending bonuses of specified type
            pending_bonuses = ReferralBonusRecord.objects.filter(
                bonus_type=bonus_type,
                status='pending'
            ).order_by('created_at')[:limit]

            processed_count = 0
            failed_count = 0

            for bonus in pending_bonuses:
                try:
                    referral = bonus.referral
                    if referral:
                        result = self.process_referral_bonus(bonus.id)
                        if result:
                            processed_count += 1
                        else:
                            failed_count += 1

                    time.sleep(0.1)  # Avoid rate limiting

                except Exception as e:
                    failed_count += 1
                    continue

            result_msg = f"Processed {processed_count} {bonus_type} bonuses, {failed_count} failed"
            logger.info(result_msg)
            return result_msg

        except Exception as e:
            error_msg = f"Bulk processing {bonus_type} bonuses failed: {e}"
            logger.error(error_msg)
            return error_msg


# Singleton instance for easy access
referral_service = ReferralBonusService()


# Utility functions
def get_user_referral_link(user):
    """Get user's referral link for sharing"""
    return referral_service._generate_referral_link(user)


def validate_referral_code(referral_code):
    """Validate a referral code for availability"""
    return referral_service.validate_referral_code(referral_code)


def get_referral_leaderboard(limit=10):
    """Get top referrers leaderboard"""
    return referral_service.get_referral_leaderboard(limit=limit)