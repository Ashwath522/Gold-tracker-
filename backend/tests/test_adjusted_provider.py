import pytest
from app.providers.adjusted import IndiaAdjustedProvider
from tests.mocks import MockGoldProvider


@pytest.mark.asyncio
async def test_adjusted_provider_scales_latest_and_history():
    inner = MockGoldProvider(base_price=10000.0, days=40)
    adj = IndiaAdjustedProvider(inner, 1.2)

    raw = await inner.get_latest()
    out = await adj.get_latest()
    assert out.price_24k_inr == pytest.approx(raw.price_24k_inr * 1.2, abs=0.01)
    assert out.price_22k_inr == pytest.approx(raw.price_22k_inr * 1.2, abs=0.01)

    raw_h = await inner.get_history(10)
    out_h = await adj.get_history(10)
    assert len(out_h) == 10
    assert [p.date for p in out_h] == [p.date for p in raw_h]
    assert out_h[0].price_24k_inr == pytest.approx(raw_h[0].price_24k_inr * 1.2, abs=0.01)
