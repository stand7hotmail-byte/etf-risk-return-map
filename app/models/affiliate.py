# -*- coding: utf-8 -*-
"""
SQLAlchemy models for the affiliate functionality.
"""
from datetime import datetime
from typing import List

from app.db.database import Base
from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class AffiliateBroker(Base):
    """
    Represents an affiliate brokerage firm.

    This model stores all information related to a single broker,
    including their affiliate links, commission details, and descriptive
    metadata for display on the front end.
    """
    __tablename__ = "affiliate_brokers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    broker_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(10), index=True)
    affiliate_url: Mapped[str] = mapped_column(Text)
    commission_rate: Mapped[float] = mapped_column(Float)
    commission_type: Mapped[str] = mapped_column(String(20))
    logo_url: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    pros: Mapped[str] = mapped_column(Text)  # Stored as a JSON string
    best_for: Mapped[str] = mapped_column(String(255))
    rating: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to clicks
    clicks: Mapped[List["AffiliateClick"]] = relationship(
        "AffiliateClick", back_populates="broker"
    )

    def __repr__(self) -> str:
        return f"<AffiliateBroker(id={self.id}, name='{self.display_name}')>"


class AffiliateClick(Base):
    """

    Represents a single click event on an affiliate link.

    This model is used for tracking and analytics, recording details
    about the user, session, and context of each click to measure
    the effectiveness of affiliate placements.
    """
    __tablename__ = "affiliate_clicks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    broker_id: Mapped[int] = mapped_column(
        ForeignKey("affiliate_brokers.id"), index=True
    )
    user_id: Mapped[str | None] = mapped_column(String(100), index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)
    referrer: Mapped[str | None] = mapped_column(Text)
    placement: Mapped[str] = mapped_column(String(100), index=True)
    portfolio_data: Mapped[str | None] = mapped_column(Text)  # Stored as a JSON string
    converted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationship to broker
    broker: Mapped["AffiliateBroker"] = relationship(
        "AffiliateBroker", back_populates="clicks"
    )

    def __repr__(self) -> str:
        return f"<AffiliateClick(id={self.id}, broker_id={self.broker_id})>"
