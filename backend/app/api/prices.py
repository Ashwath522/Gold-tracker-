from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..providers.factory import get_gold_provider
from ..services.price_service import PriceService
from ..schemas import LatestPriceResponse, GoldPriceItem

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.get("/latest", response_model=LatestPriceResponse)
def get_latest_price(
    force_refresh: bool = Query(False, description="Bypass cache and force call to provider API"),
    db: Session = Depends(get_db)
):
    try:
        provider = get_gold_provider()
        service = PriceService(db=db, provider=provider)
        return service.get_latest_price(force_refresh=force_refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_price_history(
    days: int = Query(90, ge=7, le=1825, description="Number of historical days to fetch"),
    db: Session = Depends(get_db)
):
    try:
        provider = get_gold_provider()
        service = PriceService(db=db, provider=provider)
        records = service.get_history_from_db(days=days)
        return [r.to_dict() for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
def sync_price_history(
    days: int = Query(365, ge=30, le=1825),
    db: Session = Depends(get_db)
):
    try:
        provider = get_gold_provider()
        service = PriceService(db=db, provider=provider)
        inserted = service.sync_history(days=days)
        return {"status": "success", "new_records_inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
