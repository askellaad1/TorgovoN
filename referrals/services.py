from django.db import transaction
from .models import Referral, ReferralBonusConfig
from users.models import User


class ReferralService:
    @staticmethod
    @transaction.atomic
    def process_referral(new_user: User, referral_code: str):
        """Process referral when new user signs up"""
        try:
            referrer = User.objects.get(referral_code=referral_code)
            if referrer.id == new_user.id:
                return  # Prevent self-referral

            bonus_config = ReferralBonusConfig.objects.filter(is_active=True).first()
            if not bonus_config:
                return

            # Create referral record
            referral = Referral.objects.create(
                referrer=referrer,
                referred=new_user,
                code_used=referral_code,
                bonus_amount=bonus_config.value
            )

            # Apply bonus based on type
            if bonus_config.bonus_type == 'alerts':
                referrer.webhook_alerts_used = max(0, referrer.webhook_alerts_used - int(bonus_config.value))
                referrer.save()
            elif bonus_config.bonus_type == 'discount':
                # Apply discount to next subscription
                pass
            elif bonus_config.bonus_type == 'usdt':
                # Credit USDT equivalent (requires wallet model)
                pass

        except User.DoesNotExist:
            pass

    @staticmethod
    def get_referral_earnings(user: User):
        """Calculate total earnings from referrals"""
        referrals = Referral.objects.filter(referrer=user)
        return sum(ref.bonus_amount for ref in referrals)

    @staticmethod
    def get_referrals_made(user: User):
        """Get list of successful referrals"""
        return Referral.objects.filter(referrer=user).select_related('referred')