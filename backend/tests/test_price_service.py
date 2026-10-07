import pytest
from datetime import datetime, timezone, timedelta, date
from app.services.price_service import PriceService
from app.models import GoldPrice, PriceCache
from tests.mocks import MockGoldProvider

def test_price_service_fetches_and_caches(test_db):
    mock_provider = MockGoldProvider(base_price=7400.0)
    service = PriceService(db=test_db, provider=mock_provider)

    # Initial fetch
    resp = service.get_latest_price()
    assert resp.price_24k_inr > 0
    assert resp.price_24k_10g_inr == round(resp.price_24k_inr * 10, 2)
    assert resp.is_stale is False

    # Check database cache record
    cache = test_db.query(PriceCache).filter(PriceCache.cache_key == "latest").first()
    assert cache is not None
    assert cache.price_24k_inr == resp.price_24k_inr

    # Subsequent fetch should be served from cache without calling provider again
    mock_provider.should_fail = True  # If it called provider, it would fail
    cached_resp = service.get_latest_price()
    assert cached_resp.price_24k_inr == resp.price_24k_inr
    assert cached_resp.is_stale is False

def test_price_service_stale_fallback_on_error(test_db):
    # Populate cache first
    now_utc = datetime.now(timezone.utc) - timedelta(minutes=45)  # Expired cache (TTL=30)
    cache = PriceCache(
        cache_key="latest",
        price_24k_inr=7350.0,
        price_22k_inr=6737.5,
        source="Previous Source",
        source_timestamp="2026-10-06 18:00:00 IST",
        is_converted=False,
        fetched_at=now_utc,
        benchmark_status="Preliminary (latest available price)"
    )
    test_db.add(cache)
    test_db.commit()

    # Now make provider fail
    failing_provider = MockGoldProvider(should_fail=True, failure_msg="Upstream timeout")
    service = PriceService(db=test_db, provider=failing_provider)

    # Should gracefully return stale cached data with is_stale=True and warning notes
    resp = service.get_latest_price(force_refresh=True)
    assert resp.is_stale is True
    assert resp.price_24k_inr == 7350.0
    assert "Stale data" in resp.notes

def test_price_service_raises_when_no_cache_and_provider_fails(test_db):
    failing_provider = MockGoldProvider(should_fail=True, failure_msg="API Network Error")
    service = PriceService(db=test_db, provider=failing_provider)

    with pytest.raises(RuntimeError, match="Could not fetch latest gold price"):
        service.get_latest_price()

def test_price_service_sync_history(test_db):
    mock_provider = MockGoldProvider(days=40)
    service = PriceService(db=test_db, provider=mock_provider)

    inserted = service.sync_history(days=30)
    assert inserted == 30

    count = test_db.query(GoldPrice).count()
    assert count == 30

    # Sync again - should not duplicate records
    inserted_again = service.sync_history(days=30)
    assert inserted_again == 0
    assert test_db.query(GoldPrice).count() == 30
