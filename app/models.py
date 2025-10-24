from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

# Temporary Base definition. This will be replaced by an import from .database later.
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True)  # User ID
    name = Column(String, index=True)
    data = Column(Text)  # JSON string of portfolio data
    created_at = Column(DateTime, default=datetime.now)


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, index=True)
    close_price = Column(Float)

    __table_args__ = (UniqueConstraint("ticker", "date", name="_ticker_date_uc"),)
