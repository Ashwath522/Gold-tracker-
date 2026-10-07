from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..services.portfolio_service import PortfolioService
from ..services.price_service import PriceService
from ..providers.factory import get_gold_provider
from ..schemas import InvestmentCreate, InvestmentUpdate, InvestmentOut, PortfolioSummary

router = APIRouter(prefix="/investments", tags=["Investments"])

@router.get("", response_model=List[InvestmentOut])
def list_investments(db: Session = Depends(get_db)):
    service = PortfolioService(db)
    items = service.list_investments()
    return [
        InvestmentOut(
            id=i.id,
            date=i.date,
            time_ist=i.time_ist,
            market_price=i.market_price,
            model_score=i.model_score,
            model_rec_fixed=i.model_rec_fixed,
            model_rec_extra=i.model_rec_extra,
            model_rec_total=i.model_rec_total,
            actual_amount=i.actual_amount,
            gst_paid=i.gst_paid,
            actual_grams=i.actual_grams,
            is_estimated_grams=i.is_estimated_grams,
            avg_purchase_price=i.avg_purchase_price,
            notes=i.notes
        )
        for i in items
    ]

@router.post("", response_model=InvestmentOut)
def create_investment(payload: InvestmentCreate, db: Session = Depends(get_db)):
    try:
        service = PortfolioService(db)
        inv = service.add_investment(payload)
        return InvestmentOut(
            id=inv.id,
            date=inv.date,
            time_ist=inv.time_ist,
            market_price=inv.market_price,
            model_score=inv.model_score,
            model_rec_fixed=inv.model_rec_fixed,
            model_rec_extra=inv.model_rec_extra,
            model_rec_total=inv.model_rec_total,
            actual_amount=inv.actual_amount,
            gst_paid=inv.gst_paid,
            actual_grams=inv.actual_grams,
            is_estimated_grams=inv.is_estimated_grams,
            avg_purchase_price=inv.avg_purchase_price,
            notes=inv.notes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{inv_id}", response_model=InvestmentOut)
def update_investment(inv_id: int, payload: InvestmentUpdate, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    updated = service.update_investment(inv_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Investment entry not found")
    return InvestmentOut(
        id=updated.id,
        date=updated.date,
        time_ist=updated.time_ist,
        market_price=updated.market_price,
        model_score=updated.model_score,
        model_rec_fixed=updated.model_rec_fixed,
        model_rec_extra=updated.model_rec_extra,
        model_rec_total=updated.model_rec_total,
        actual_amount=updated.actual_amount,
        gst_paid=updated.gst_paid,
        actual_grams=updated.actual_grams,
        is_estimated_grams=updated.is_estimated_grams,
        avg_purchase_price=updated.avg_purchase_price,
        notes=updated.notes
    )

@router.delete("/{inv_id}")
def delete_investment(inv_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    success = service.delete_investment(inv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Investment entry not found")
    return {"status": "success", "deleted_id": inv_id}

@router.get("/portfolio", response_model=PortfolioSummary)
def get_portfolio_summary(db: Session = Depends(get_db)):
    try:
        provider = get_gold_provider()
        price_svc = PriceService(db=db, provider=provider)
        latest = price_svc.get_latest_price()
        current_market_price = latest.price_24k_inr
    except Exception:
        current_market_price = 0.0

    port_svc = PortfolioService(db)
    return port_svc.get_portfolio_summary(current_market_price=current_market_price)

@router.get("/export-csv")
def export_investments_csv(db: Session = Depends(get_db)):
    service = PortfolioService(db)
    csv_str = service.export_csv()
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gold_investments.csv"}
    )

@router.post("/import-csv")
async def import_investments_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        csv_text = contents.decode("utf-8")
        service = PortfolioService(db)
        count = service.import_csv(csv_text)
        return {"status": "success", "imported_count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import CSV: {e}")
