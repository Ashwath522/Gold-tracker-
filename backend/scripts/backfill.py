#!/usr/bin/env python3
"""
Backfill script to populate historical gold prices into SQLite / PostgreSQL.
Fetches up to 365 days of authentic market closes from the configured provider
and stores them with full integrity checks (no fabricated or interpolated dates).
"""
import sys
import os
import argparse

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base, SessionLocal
from app.models import GoldPrice
from app.providers.factory import get_gold_provider
from app.services.price_service import PriceService
from app.config import settings

def main():
    parser = argparse.ArgumentParser(description="Backfill gold price history")
    parser.add_argument("--days", type=int, default=365, help="Number of historical days to backfill (default: 365)")
    args = parser.parse_args()

    print(f"Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)

    print(f"Initializing provider: {settings.GOLD_PRICE_PROVIDER}...")
    try:
        provider = get_gold_provider()
    except Exception as e:
        print(f"Error initializing provider: {e}")
        sys.exit(1)

    db = SessionLocal()
    try:
        service = PriceService(db=db, provider=provider)
        print(f"Fetching up to {args.days} days of history from {settings.GOLD_PRICE_PROVIDER}...")
        inserted = service.sync_history(days=args.days)
        total_count = db.query(GoldPrice).count()
        print(f"Successfully backfilled {inserted} new records.")
        print(f"Total historical gold price records in database: {total_count}")
    except Exception as e:
        print(f"Backfill failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
