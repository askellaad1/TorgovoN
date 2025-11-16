import uuid
from django.conf import settings

def generate_uuid():
    return uuid.uuid4()

def encrypt_data(data: str) -> str:
    return settings.FERNET.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return settings.FERNET.decrypt(encrypted_data.encode()).decode()

def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"****{key[-4:]}"

def generate_webhook_path(bot_type: str, bot_id: uuid.UUID) -> str:
    return f"/webhooks/{bot_type}_bots/{bot_id}/"

def generate_json_template(bot_id: uuid.UUID, secret_key: str) -> dict:
    return {
        "bot_id": str(bot_id),
        "buy_sell": "buy|sell",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "amount": 0.0,
        "timestamp": "2024-01-01T00:00:00Z",
        "code": "optional_user_code",
        "secret_key": secret_key
    }