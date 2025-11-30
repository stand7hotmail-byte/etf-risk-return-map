from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# The database file will be created in the `data` directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/affiliate.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args is needed only for SQLite.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


def get_db() -> Generator:
    """
    FastAPI dependency to get a database session.

    Yields:
        Generator: A database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all database tables defined by models inheriting from Base.
    """
    # Create the data directory if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
