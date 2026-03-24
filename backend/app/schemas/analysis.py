from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from app.schemas.news import EventOut
from app.schemas.market import CommodityOut


class CorrelationQuery(BaseModel):
    symbols: list[str]
    period: str = "90d"


class CorrelationMatrixOut(BaseModel):
    symbols: list[str]
    matrix: list[list[float]]


class EventImpactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: EventOut
    commodity: CommodityOut
    price_before: Optional[float] = None
    price_after_1d: Optional[float] = None
    price_after_7d: Optional[float] = None
    price_after_30d: Optional[float] = None
    change_pct_1d: Optional[float] = None
    change_pct_7d: Optional[float] = None
    change_pct_30d: Optional[float] = None
    ai_analysis: Optional[str] = None


class MacroComparisonQuery(BaseModel):
    indicator_code: str
    commodity_symbol: str
    period: str = "180d"


class MacroComparisonOut(BaseModel):
    indicator_code: str
    indicator_name: str
    commodity_symbol: str
    dates: list[date]
    indicator_values: list[Optional[float]]
    commodity_prices: list[Optional[float]]


class RatioItem(BaseModel):
    date: date
    ratio_name: str
    value: float
