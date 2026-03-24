from sqlalchemy import Column, Integer, String
from app.database import Base


class Commodity(Base):
    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name_cn = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)
    exchange = Column(String(30))
    unit = Column(String(20))
    akshare_symbol = Column(String(50))
