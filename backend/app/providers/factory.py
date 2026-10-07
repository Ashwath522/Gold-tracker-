from .base import GoldPriceProvider
from .goldapi import GoldAPIProvider
from .yahoo import YahooGoldProvider
from ..config import settings

def get_gold_provider() -> GoldPriceProvider:
    """
    Factory function returning the configured GoldPriceProvider instance.
    Swappable via GOLD_PRICE_PROVIDER in .env.
    """
    provider_name = settings.GOLD_PRICE_PROVIDER.lower().strip()
    if provider_name == "goldapi":
        return GoldAPIProvider(api_key=settings.GOLDAPI_KEY)
    elif provider_name == "yahoo":
        return YahooGoldProvider()
    else:
        raise ValueError(
            f"Unsupported GOLD_PRICE_PROVIDER: '{provider_name}'. Supported options are 'goldapi' or 'yahoo'."
        )
