import pytest
from app.providers.goldapi import GoldAPIProvider
from app.providers.yahoo import YahooGoldProvider, TROY_OZ_TO_GRAM
from tests.mocks import MockGoldProvider

@pytest.mark.asyncio
async def test_goldapi_missing_key_raises_value_error():
    provider = GoldAPIProvider(api_key="")
    with pytest.raises(ValueError, match="GOLDAPI_KEY in your .env"):
        await provider.get_latest()

    with pytest.raises(ValueError, match="GOLDAPI_KEY in your .env"):
        await provider.get_history(days=10)

def test_troy_ounce_to_gram_constant():
    # 1 troy ounce = 31.1034768 grams
    assert round(TROY_OZ_TO_GRAM, 4) == 31.1035

@pytest.mark.asyncio
async def test_mock_provider_deterministic_contract():
    provider = MockGoldProvider(base_price=7500.0, days=45)
    latest = await provider.get_latest()
    assert latest.price_24k_inr > 7000.0
    assert latest.price_22k_inr is not None
    assert latest.is_converted is False
    assert "Mock Provider" in latest.source

    history = await provider.get_history(days=30)
    assert len(history) == 30
    # Chronological order ascending
    for i in range(len(history) - 1):
        assert history[i].date < history[i + 1].date
