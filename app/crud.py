import os
import re
from datetime import datetime, timedelta

import pandas as pd
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from google.cloud import secretmanager
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Portfolio, StockPrice, User
from app.schemas import TokenData


# Function to access Secret Manager
def access_secret_version(
    project_id: str, secret_id: str, version_id: str = "latest"
) -> str:
    """Access a secret version from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


# Determine project ID dynamically for App Engine or use environment variable
PROJECT_ID = (
    os.environ.get("GOOGLE_CLOUD_PROJECT") or "your-gcp-project-id"
)  # Replace with your actual project ID if not on App Engine

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT認証設定
# SECRET_KEYはFastAPIのlifespanイベントで設定される
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_prices_from_db(
    db: Session, tickers: list[str], start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """Retrieve stock prices from the database for given tickers and date range."""
    prices = (
        db.query(StockPrice)
        .filter(
            StockPrice.ticker.in_(tickers),
            StockPrice.date >= start_date,
            StockPrice.date <= end_date,
        )
        .all()
    )

    if not prices:
        return pd.DataFrame()

    df = pd.DataFrame([p.__dict__ for p in prices])
    df["date"] = pd.to_datetime(df["date"])
    df = df.pivot_table(index="date", columns="ticker", values="close").sort_index()
    return df


def save_prices_to_db(db: Session, price_df: pd.DataFrame) -> None:
    """Save stock prices from a DataFrame to the database."""
    for ticker in price_df.columns:
        for date, close_price in price_df[ticker].items():
            # Check if the price already exists for the given ticker and date
            existing_price = (
                db.query(StockPrice)
                .filter_by(ticker=ticker, date=date.date())
                .first()
            )
            if existing_price:
                # Update existing price
                existing_price.close = close_price
            else:
                # Add new price
                db_price = StockPrice(
                    ticker=ticker, date=date.date(), close=close_price
                )
                db.add(db_price)
    db.commit()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    request: Request = Depends(),
) -> str:
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    secret_key = request.app.state.secret_key
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = Depends(),
) -> User:
    """Retrieve the current authenticated user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        secret_key = request.app.state.secret_key
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception from e
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


def create_user_token(username: str) -> dict:
    """Create a user token with a given username."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def get_user_portfolio_by_id(db: Session, user_id: int, portfolio_id: int) -> Portfolio:
    """Retrieve a user's portfolio by its ID."""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.owner_id == user_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )
    return portfolio


def is_password_strong_enough(password: str) -> bool:
    """Check if a password meets the strength requirements."""
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True
