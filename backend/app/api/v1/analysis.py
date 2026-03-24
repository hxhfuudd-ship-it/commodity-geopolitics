from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analysis import CorrelationMatrixOut, EventImpactOut, MacroComparisonOut, RatioItem
from app.services import analysis_service

router = APIRouter(prefix="/analysis", tags=["分析"])


@router.get("/correlation", response_model=CorrelationMatrixOut)
async def correlation(
    symbols: str = Query(..., description="逗号分隔的品种代码"),
    period: str = Query("90d"),
    db: AsyncSession = Depends(get_db),
) -> CorrelationMatrixOut:
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个品种进行相关性分析")
    return await analysis_service.get_correlation(db, symbol_list, period)


@router.get("/event-impact/{event_id}", response_model=list[EventImpactOut])
async def event_impact(event_id: int, db: AsyncSession = Depends(get_db)) -> list[EventImpactOut]:
    return await analysis_service.get_event_impact(db, event_id)


@router.get("/macro/comparison", response_model=MacroComparisonOut)
async def macro_comparison(
    indicator_code: str = Query(...),
    commodity_symbol: str = Query(...),
    period: str = Query("180d"),
    db: AsyncSession = Depends(get_db),
) -> MacroComparisonOut:
    return await analysis_service.get_macro_comparison(db, indicator_code, commodity_symbol, period)


@router.get("/ratios", response_model=list[RatioItem])
async def ratios(period: str = Query("1y"), db: AsyncSession = Depends(get_db)) -> list[RatioItem]:
    return await analysis_service.get_ratios(db, period)


@router.get("/report/daily")
async def daily_report(db: AsyncSession = Depends(get_db)) -> dict:
    report = await analysis_service.get_daily_report(db)
    return {"report": report}
