from sqlalchemy import Column, Integer, String, Text, SmallInteger, Numeric, Date, ForeignKey
from app.database import Base


class GeopoliticalEvent(Base):
    __tablename__ = "geopolitical_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))
    region = Column(String(100))
    country_codes = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    severity = Column(SmallInteger)
    latitude = Column(Numeric(10, 6))
    longitude = Column(Numeric(10, 6))


class EventImpact(Base):
    __tablename__ = "event_impact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("geopolitical_events.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    price_before = Column(Numeric(16, 4))
    price_after_1d = Column(Numeric(16, 4))
    price_after_7d = Column(Numeric(16, 4))
    price_after_30d = Column(Numeric(16, 4))
    change_pct_1d = Column(Numeric(8, 4))
    change_pct_7d = Column(Numeric(8, 4))
    change_pct_30d = Column(Numeric(8, 4))
    ai_analysis = Column(Text, nullable=True)
