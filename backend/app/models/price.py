from sqlalchemy import Column, Integer, BigInteger, Date, Numeric, ForeignKey, UniqueConstraint, Index
from app.database import Base


class PriceDaily(Base):
    __tablename__ = "price_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(Numeric(16, 4))
    high = Column(Numeric(16, 4))
    low = Column(Numeric(16, 4))
    close = Column(Numeric(16, 4))
    volume = Column(BigInteger)
    open_interest = Column(BigInteger, nullable=True)
    change_pct = Column(Numeric(8, 4))

    __table_args__ = (
        UniqueConstraint("commodity_id", "trade_date", name="uq_price_commodity_date"),
        Index("ix_price_trade_date", "trade_date"),
    )
