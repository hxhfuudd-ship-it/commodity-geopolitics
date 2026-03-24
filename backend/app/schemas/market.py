from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class CommodityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name_cn: str
    category: str
    exchange: Optional[str] = None
    unit: Optional[str] = None


class PriceDailyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    change_pct: Optional[float] = None


class KlineQuery(BaseModel):
    period: str = "day"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CompareQuery(BaseModel):
    symbols: list[str]
    normalize: bool = True


class MarketOverviewItem(BaseModel):
    symbol: str
    name_cn: str
    category: str
    latest_price: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    settle: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    updated_at: Optional[datetime] = None
