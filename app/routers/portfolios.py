import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import (
    get_current_user,
    get_user_portfolio_by_id,
)  # Assuming get_current_user is in crud.py
from app.database import get_db
from app.models import Portfolio, User

router = APIRouter()


@router.post("/save_portfolio")
async def save_user_portfolio(
    portfolio_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Save a user's portfolio."""
    portfolio_name = portfolio_data.get("name", "Untitled Portfolio")
    portfolio_content = json.dumps(portfolio_data.get("content", {}))

    db_portfolio = Portfolio(
        owner_id=current_user.id, name=portfolio_name, data=portfolio_content
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return {"message": "Portfolio saved successfully!", "portfolio_id": db_portfolio.id}


@router.get("/list_portfolios")
async def list_user_portfolios(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[dict]:
    """List all portfolios for the current user."""
    portfolios = db.query(Portfolio).filter(Portfolio.owner_id == current_user.id).all()
    return [
        {"id": p.id, "name": p.name, "created_at": p.created_at.isoformat()}
        for p in portfolios
    ]


@router.get("/load_portfolio/{portfolio_id}")
async def load_user_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Load a specific portfolio for the current user."""
    portfolio = get_user_portfolio_by_id(db, current_user.id, portfolio_id)
    return json.loads(portfolio.data)


@router.delete("/delete_portfolio/{portfolio_id}")
async def delete_user_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a specific portfolio for the current user."""
    portfolio = get_user_portfolio_by_id(db, current_user.id, portfolio_id)
    db.delete(portfolio)
    db.commit()
    return {"message": "Portfolio deleted successfully!"}
