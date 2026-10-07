from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional, List

@dataclass
class ProviderPrice:
    date: date
    price_24k_inr: float
    price_22k_inr: Optional[float]
    source: str
    source_timestamp: str
    is_converted: bool
    notes: Optional[str] = None

class GoldPriceProvider(ABC):
    """
    Abstract interface for all gold price data providers.
    All prices must be returned in INR per gram.
    """

    @abstractmethod
    async def get_latest(self) -> ProviderPrice:
        """
        Fetch current/latest available gold price in INR per gram.
        Returns 24k and 22k (if available) with provider's original timestamp.
        """
        pass

    @abstractmethod
    async def get_history(self, days: int) -> List[ProviderPrice]:
        """
        Fetch historical daily gold prices in INR per gram for the specified number of days.
        Must return list sorted chronologically ascending.
        Never interpolate or fabricate missing days.
        """
        pass
