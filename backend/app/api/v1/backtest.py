from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import backtest_service

router = APIRouter(prefix="/backtest", tags=["回测"])


@router.get("/events")
async def backtest_events(db: AsyncSession = Depends(get_db)) -> list:
    return await backtest_service.get_backtest_events(db)


@router.post("/run")
async def run_backtest(
    event_id: int,
    commodities: str = Query(..., description="逗号分隔的品种代码"),
    before_days: int = Query(30, ge=1, le=365),
    after_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol_list = [s.strip() for s in commodities.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="commodities 参数不能为空")
    return await backtest_service.run_backtest(db, event_id, symbol_list, before_days, after_days)


@router.get("/compare")
async def compare_events(
    event_ids: str = Query(..., description="逗号分隔的事件ID"),
    commodity: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        ids = [int(i.strip()) for i in event_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="event_ids 必须为逗号分隔的整数")
    if not ids:
        raise HTTPException(status_code=400, detail="event_ids 参数不能为空")
    return await backtest_service.compare_events(db, ids, commodity)
