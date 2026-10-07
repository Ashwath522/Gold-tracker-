from datetime import date
from app.models import GoldPrice, Investment

def test_gold_price_model(test_db):
    gp = GoldPrice(
        date=date(2026, 10, 7),
        price_24k_inr=7550.25,
        price_22k_inr=6921.06,
        source="GoldAPI.io",
        source_timestamp="2026-10-07 11:30:00 IST",
        is_converted=False,
        notes="Official rate"
    )
    test_db.add(gp)
    test_db.commit()

    saved = test_db.query(GoldPrice).filter(GoldPrice.date == date(2026, 10, 7)).first()
    assert saved is not None
    assert saved.price_24k_inr == 7550.25
    d = saved.to_dict()
    assert d["date"] == "2026-10-07"
    assert d["price_24k_inr"] == 7550.25

def test_investment_model_and_avg_price(test_db):
    # Investment with PhonePe actuals: 100 invested, 0.0125 grams received
    inv = Investment(
        date=date(2026, 10, 7),
        time_ist="14:30:00",
        market_price=7500.0,
        model_score=72.0,
        model_rec_fixed=35.0,
        model_rec_extra=40.0,
        model_rec_total=75.0,
        actual_amount=100.0,
        gst_paid=2.91,
        actual_grams=0.0125,
        is_estimated_grams=False,
        avg_purchase_price=100.0 / 0.0125,  # 8000.0
        notes="PhonePe purchase"
    )
    test_db.add(inv)
    test_db.commit()

    saved = test_db.query(Investment).first()
    assert saved.avg_purchase_price == 8000.0
    assert saved.actual_grams == 0.0125
    assert saved.to_dict()["avg_purchase_price"] == 8000.0
