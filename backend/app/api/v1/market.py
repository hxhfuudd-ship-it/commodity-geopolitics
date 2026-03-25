from datetime import date
from typing import Optional
import asyncio
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.market import CommodityOut, PriceDailyOut, MarketOverviewItem
from app.services import market_service
from app.core.cache import cache_get

router = APIRouter(prefix="/market", tags=["行情"])


@router.get("/overview", response_model=list[MarketOverviewItem])
async def overview(db: AsyncSession = Depends(get_db)) -> list[MarketOverviewItem]:
    # Try realtime cache first
    cached = await cache_get("market:overview:realtime")
    if cached:
        return [MarketOverviewItem(**item) for item in cached]
    return await market_service.get_overview(db)


@router.get("/overview/stream")
async def overview_stream():
    """SSE endpoint: push realtime prices every 3 seconds"""
    async def event_generator():
        try:
            while True:
                try:
                    data = await cache_get("market:overview:realtime")
                    if data:
                        yield f"data: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"
                    else:
                        # Heartbeat to keep connection alive
                        yield ": heartbeat\n\n"
                except Exception:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/commodities/compare")
async def compare(
    symbols: str = Query(..., description="逗号分隔的品种代码"),
    normalize: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols 参数不能为空")
    return await market_service.get_compare_data(db, symbol_list, normalize)


@router.get("/commodities", response_model=list[CommodityOut])
async def list_commodities(
    category: Optional[str] = Query(None, description="metal 或 energy"),
    db: AsyncSession = Depends(get_db),
) -> list[CommodityOut]:
    return await market_service.get_commodities(db, category)


@router.get("/commodities/{symbol}/price")
async def get_price(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    data = await market_service.get_commodity_price(db, symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"品种 {symbol} 不存在")
    return data


@router.get("/commodities/{symbol}/kline", response_model=list[PriceDailyOut])
async def get_kline(
    symbol: str,
    period: str = Query("day"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[PriceDailyOut]:
    return await market_service.get_kline(db, symbol, period, start_date, end_date)


@router.get("/cftc/{symbol}")
async def get_cftc(symbol: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await market_service.get_cftc(db, symbol)
