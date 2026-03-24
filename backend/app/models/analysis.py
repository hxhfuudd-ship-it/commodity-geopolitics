from sqlalchemy import Column, Integer, String, Numeric, Date, BigInteger, ForeignKey, UniqueConstraint
from app.database import Base


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_code = Column(String(50), nullable=False)
    indicator_name = Column(String(100))
    value = Column(Numeric(16, 4))
    report_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("indicator_code", "report_date", name="uq_macro_code_date"),
    )


class CftcPosition(Base):
    __tablename__ = "cftc_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    report_date = Column(Date, nullable=False)
    long_positions = Column(BigInteger)
    short_positions = Column(BigInteger)
    net_positions = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint("commodity_id", "report_date", name="uq_cftc_commodity_date"),
    )
