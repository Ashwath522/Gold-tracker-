from .base import GoldPriceProvider
from .goldapi import GoldAPIProvider
from .yahoo import YahooGoldProvider
from .adjusted import IndiaAdjustedProvider
from ..config import settings

def get_gold_provider() -> GoldPriceProvider:
    """
    Factory function returning the configured GoldPriceProvider instance.
    Swappable via GOLD_PRICE_PROVIDER in .env.
    """
    provider_name = settings.GOLD_PRICE_PROVIDER.lower().strip()
    if provider_name == "goldapi":
        provider: GoldPriceProvider = GoldAPIProvider(api_key=settings.GOLDAPI_KEY)
    elif provider_name == "yahoo":
        provider = YahooGoldProvider()
    else:
        raise ValueError(
            f"Unsupported GOLD_PRICE_PROVIDER: '{provider_name}'. Supported options are 'goldapi' or 'yahoo'."
        )

    if abs(settings.price_multiplier - 1.0) > 1e-9:
        return IndiaAdjustedProvider(provider, settings.price_multiplier)
    return provider
