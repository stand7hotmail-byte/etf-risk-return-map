

from fastapi import FastAPI, Request, Query, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import json
from jose import jwt, JWTError
import firebase_admin
from firebase_admin import credentials, auth
import time
import os

# Firebase Admin SDKの初期化
cred = credentials.Certificate("etf-webapp-firebase-adminsdk-fbsvc-96649b4b25.json")
firebase_admin.initialize_app(cred)


app = FastAPI()

# データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# データベースモデル
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True) # User ID
    name = Column(String, index=True)
    data = Column(Text) # JSON string of portfolio data
    created_at = Column(DateTime, default=datetime.now)

class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, index=True)
    close_price = Column(Float)

    __table_args__ = (UniqueConstraint('ticker', 'date', name='_ticker_date_uc'),)

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

# データベースセッションの依存性注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Stock Price Data Functions ---
def get_prices_from_db(db: Session, tickers: list[str], start_date: datetime, end_date: datetime):
    prices = db.query(StockPrice).filter(
        StockPrice.ticker.in_(tickers),
        StockPrice.date >= start_date,
        StockPrice.date <= end_date
    ).all()
    
    if not prices:
        return pd.DataFrame()
    
    df = pd.DataFrame([(p.date, p.ticker, p.close_price) for p in prices], columns=['date', 'ticker', 'close_price'])
    price_df = df.pivot(index='date', columns='ticker', values='close_price')
    price_df.sort_index(inplace=True)
    return price_df

def save_prices_to_db(db: Session, df: pd.DataFrame):
    df_long = df.reset_index().melt(id_vars=['Date'], var_name='ticker', value_name='close_price')
    df_long.rename(columns={'Date': 'date'}, inplace=True)
    df_long.dropna(subset=['close_price'], inplace=True)
    
    # This is a simplified upsert for SQLite
    for record in df_long.to_dict(orient="records"):
        db.merge(StockPrice(**record))
    db.commit()
# --- End of Stock Price Data Functions ---


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# JWT認証設定
SECRET_KEY = os.environ.get("SECRET_KEY", "a-fallback-secret-key-for-local-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Pydanticモデル (認証用)
class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=128)

class UserInDB(BaseModel):
    username: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class GoogleToken(BaseModel):
    token: str

# ユーザー登録エンドポイント
@app.post("/register", response_model=UserInDB)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

# ログインエンドポイント
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Googleログイン用エンドポイント
@app.post("/token/google", response_model=Token)
async def login_google(google_token: GoogleToken, db: Session = Depends(get_db)):
    try:
        # Firebase IDトークンを検証
        decoded_token = auth.verify_id_token(google_token.token)
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token.",
            )

    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}",
        )

    # データベースでユーザーを検索または作成
    user = db.query(User).filter(User.username == email).first()
    if not user:
        # ユーザーが存在しない場合は、新しいユーザーを作成
        # Googleログインユーザーはパスワードを持たないため、hashed_passwordは空にする
        new_user = User(username=email, hashed_password="")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    # 既存のシステムと同じように、内部用のJWTトークンを生成して返す
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ポートフォリオ保存エンドポイント
@app.post("/save_portfolio")
async def save_user_portfolio(portfolio_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio_name = portfolio_data.get("name", "Untitled Portfolio")
    portfolio_content = json.dumps(portfolio_data.get("content", {}))

    db_portfolio = Portfolio(
        owner_id=current_user.id,
        name=portfolio_name,
        data=portfolio_content
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return {"message": "Portfolio saved successfully!", "portfolio_id": db_portfolio.id}

# ポートフォリオ一覧取得エンドポイント
@app.get("/list_portfolios")
async def list_user_portfolios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolios = db.query(Portfolio).filter(Portfolio.owner_id == current_user.id).all()
    return [{
        "id": p.id,
        "name": p.name,
        "created_at": p.created_at.isoformat()
    } for p in portfolios]

# ポートフォリオ読み込みエンドポイント
@app.get("/load_portfolio/{portfolio_id}")
async def load_user_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return json.loads(portfolio.data)

# ポートフォリオ削除エンドポイント
@app.delete("/delete_portfolio/{portfolio_id}")
async def delete_user_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    return {"message": "Portfolio deleted successfully!"}

# Load ETF definitions from CSV
def load_etf_definitions():
    try:
        df = pd.read_csv("etf_list.csv")
        # Convert to the nested dictionary format, using ticker as the key
        return df.set_index('ticker').to_dict(orient='index')
    except FileNotFoundError:
        # Fallback or error handling if the CSV is not found
        return {}

ETF_DEFINITIONS = load_etf_definitions()
ALL_ETF_TICKERS = list(ETF_DEFINITIONS.keys())

# リスクフリーレート (年率)
RISK_FREE_RATE = 0.02 # 例: 2%

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/etf_list")
async def get_etf_list():
    return ETF_DEFINITIONS

@app.get("/risk_free_rate")
async def get_risk_free_rate():
    return {"risk_free_rate": RISK_FREE_RATE}

@app.get("/data")
async def get_etf_data(tickers: list[str] = Query(ALL_ETF_TICKERS), period: str = Query("5y"), db: Session = Depends(get_db)):
    start_time = time.time()
    if not tickers:
        return []

    end_date = datetime.now()
    if period.endswith('y'):
        years = int(period[:-1])
        start_date = end_date - timedelta(days=years * 365)
    else:
        start_date = end_date - timedelta(days=365)

    db_price_df = get_prices_from_db(db, tickers, start_date, end_date)
    missing_tickers = [t for t in tickers if t not in db_price_df.columns]

    if missing_tickers:
        yf_data = yf.download(missing_tickers, start=start_date, end=end_date, group_by='ticker')
        if not yf_data.empty:
            yf_price_df = yf_data.xs('Close', level=1, axis=1).copy()
            yf_price_df.index = pd.to_datetime(yf_price_df.index)
            save_prices_to_db(db, yf_price_df)
            data = pd.concat([db_price_df, yf_price_df], axis=1)
        else:
            data = db_price_df
    else:
        data = db_price_df

    data.sort_index(inplace=True)
    
    returns = data.pct_change().dropna()
    annual_returns = returns.mean() * 252
    annual_volatility = returns.std() * (252 ** 0.5)

    result_df = pd.DataFrame({
        'Return': annual_returns,
        'Risk': annual_volatility,
        'Ticker': annual_returns.index
    })

    print(f"--- /data endpoint took {(time.time() - start_time) * 1000:.2f} ms ---")
    return result_df.to_dict(orient='records')

# ポートフォリオのリスクを計算する関数
def portfolio_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

# ポートフォリオのリターンを計算する関数
def portfolio_return(weights, avg_returns):
    return np.sum(avg_returns * weights)

# シャープ・レシオを計算する関数
def portfolio_sharpe_ratio(weights, avg_returns, cov_matrix, risk_free_rate):
    p_return = portfolio_return(weights, avg_returns)
    p_volatility = portfolio_volatility(weights, cov_matrix)
    if p_volatility == 0: # リスクが0の場合は無限大を返す（または非常に大きな値）
        return -np.inf
    return (p_return - risk_free_rate) / p_volatility

def portfolio_downside_deviation(weights, returns, risk_free_rate):
    portfolio_returns = np.dot(returns, weights)
    downside_returns = portfolio_returns[portfolio_returns < risk_free_rate]
    if len(downside_returns) == 0: # No downside returns, so downside deviation is 0
        return 0.0 
    return np.sqrt(np.mean((downside_returns - risk_free_rate)**2)) * (252**0.5) # Annualized

def portfolio_sortino_ratio(weights, avg_returns, returns, cov_matrix, risk_free_rate):
    p_return = portfolio_return(weights, avg_returns)
    downside_dev = portfolio_downside_deviation(weights, returns, risk_free_rate)
    if downside_dev == 0:
        return np.inf # No downside risk, so Sortino is infinite
    return (p_return - risk_free_rate) / downside_dev

@app.get("/efficient_frontier")
async def get_efficient_frontier(tickers: list[str] = Query(ALL_ETF_TICKERS), period: str = Query("5y"), db: Session = Depends(get_db)):
    start_time = time.time()
    import json
    if not tickers:
        return {"frontier_points": [], "tangency_portfolio": None, "tangency_portfolio_weights": {}}

    end_date = datetime.now()
    if period.endswith('y'):
        years = int(period[:-1])
        start_date = end_date - timedelta(days=years * 365)
    else:
        start_date = end_date - timedelta(days=365)

    db_price_df = get_prices_from_db(db, tickers, start_date, end_date)
    missing_tickers = [t for t in tickers if t not in db_price_df.columns]

    if missing_tickers:
        yf_data = yf.download(missing_tickers, start=start_date, end=end_date, group_by='ticker')
        if not yf_data.empty:
            yf_price_df = yf_data.xs('Close', level=1, axis=1).copy()
            yf_price_df.index = pd.to_datetime(yf_price_df.index)
            save_prices_to_db(db, yf_price_df)
            data = pd.concat([db_price_df, yf_price_df], axis=1)
        else:
            data = db_price_df
    else:
        data = db_price_df
    
    # --- Start of Major Change: Ensure consistent ordering ---
    # 1. Get the final list of tickers that have data
    final_tickers = data.columns.tolist()
    data = data[final_tickers] # Re-order data columns alphabetically
    data.sort_index(inplace=True)

    # 2. Calculate returns and re-order again to be safe
    returns = data.pct_change().dropna()
    returns = returns[final_tickers]

    # 3. Create avg_returns and cov_matrix from the consistently ordered returns
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    # --- End of Major Change ---

    num_assets = len(final_tickers) # Use final_tickers
    constraints_list = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},)
    bounds = tuple([(0.0, 1.0)] * num_assets)

    efficient_frontier_points = []
    target_returns = np.linspace(avg_returns.min() * 0.8, avg_returns.max() * 1.2, 20)
    max_sharpe_ratio = -np.inf
    tangency_portfolio = None
    tangency_portfolio_weights = {}

    for target_return in target_returns:
        def minimize_volatility(weights):
            return portfolio_volatility(weights, cov_matrix)

        constraints_with_target = constraints_list + ({'type': 'eq', 'fun': lambda x: portfolio_return(x, avg_returns) - target_return},)
        initial_weights = num_assets * [1. / num_assets,]
        result = minimize(minimize_volatility, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_with_target)

        if result.success:
            risk = portfolio_volatility(result.x, cov_matrix)
            ret = portfolio_return(result.x, avg_returns)
            efficient_frontier_points.append({'Risk': risk, 'Return': ret})

            sharpe = portfolio_sharpe_ratio(result.x, avg_returns, cov_matrix, RISK_FREE_RATE)
            if sharpe > max_sharpe_ratio:
                max_sharpe_ratio = sharpe
                tangency_portfolio = {'Risk': risk, 'Return': ret, 'SharpeRatio': sharpe}
                tangency_portfolio_weights = {ticker: weight for ticker, weight in zip(final_tickers, result.x)}

    if not efficient_frontier_points:
        return {"error": "No efficient frontier points could be generated."}

    efficient_frontier_points.sort(key=lambda x: x['Risk'])

    # This filtering step is crucial for a smooth curve
    filtered_frontier = []
    if efficient_frontier_points:
        filtered_frontier.append(efficient_frontier_points[0])
        for i in range(1, len(efficient_frontier_points)):
            if efficient_frontier_points[i]['Risk'] > filtered_frontier[-1]['Risk'] and efficient_frontier_points[i]['Return'] >= filtered_frontier[-1]['Return']:
                filtered_frontier.append(efficient_frontier_points[i])
            elif efficient_frontier_points[i]['Risk'] == filtered_frontier[-1]['Risk'] and efficient_frontier_points[i]['Return'] > filtered_frontier[-1]['Return']:
                filtered_frontier[-1] = efficient_frontier_points[i]

    print(f"--- /efficient_frontier endpoint took {(time.time() - start_time) * 1000:.2f} ms ---")
    return {"frontier_points": filtered_frontier, "tangency_portfolio": tangency_portfolio, "tangency_portfolio_weights": tangency_portfolio_weights}

class CustomPortfolioRequest(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"

class TargetOptimizationRequest(BaseModel):
    tickers: list[str]
    target_value: float
    period: str = "5y"

class HistoricalPerformanceRequest(BaseModel):
    tickers: list[str]
    period: str = "5y"

class MonteCarloSimulationRequest(BaseModel):
    tickers: list[str]
    period: str = "5y"
    num_simulations: int
    simulation_days: int

class CSVAnalysisRequest(BaseModel):
    csv_data: str

class DcaSimulationRequest(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"
    investment_amount: float
    frequency: str # 'monthly' or 'quarterly'

class FutureDcaSimulationRequest(BaseModel):
    portfolio_return: float
    portfolio_risk: float
    investment_amount: float
    frequency: str
    years: int

@app.post("/custom_portfolio_data")
async def calculate_custom_portfolio(request: CustomPortfolioRequest):
    tickers = request.tickers
    weights_dict = request.weights
    period = request.period

    if not tickers:
        return {"error": "No tickers provided."}

    # --- 1. 株価データを取得 ---
    data = yf.download(tickers, period=period, group_by='ticker')
    data = data.xs('Close', level='Price', axis=1)

    # --- 2. 日次リターンと共分散行列を計算 ---
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # 重み辞書をNumPy配列に変換し、ティッカーの順序に合わせる
    # 欠損値があるティッカーは除外する
    available_tickers = [t for t in tickers if t in avg_returns.index and t in cov_matrix.columns]
    if not available_tickers:
        return {"error": "No valid tickers with data found."}

    # 辞書からNumPy配列に変換する際に、avg_returns.indexの順序に合わせる
    weights = np.array([weights_dict.get(ticker, 0.0) for ticker in available_tickers])

    # 重みを正規化（フロントエンドで正規化されているはずだが、念のため）
    if np.sum(weights) == 0:
        return {"error": "Sum of weights is zero."}
    weights = weights / np.sum(weights)

    # ポートフォリオのリスクとリターンを計算
    try:
        p_return = portfolio_return(weights, avg_returns[available_tickers])
        p_volatility = portfolio_volatility(weights, cov_matrix.loc[available_tickers, available_tickers])
    except Exception as e:
        return {"error": f"Error calculating portfolio: {str(e)}"}

    return {
        "Risk": p_volatility,
        "Return": p_return
    }

@app.post("/optimize_by_return")
async def optimize_by_return(request: TargetOptimizationRequest):
    tickers = request.tickers
    target_return = request.target_value # 小数として受け取る
    period = request.period # <--- Get period from request

    if not tickers:
        return {"error": "No tickers provided."}

    data = yf.download(tickers, period=period, group_by='ticker')
    data = data.xs('Close', level='Price', axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints_list = (
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # 重みの合計は1
        {'type': 'eq', 'fun': lambda x: portfolio_return(x, avg_returns) - target_return} # 目標リターンを達成
    )

    # 各資産の重み制約を動的に構築
    bounds = tuple([(0.0, 1.0)] * num_assets)

    initial_weights = num_assets * [1. / num_assets,]

    # 目的関数: リスクを最小化
    def minimize_volatility(weights):
        return portfolio_volatility(weights, cov_matrix)

    result = minimize(minimize_volatility, initial_weights, method='SLSQP',
                      bounds=bounds, constraints=constraints_list)

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_sortino = portfolio_sortino_ratio(result.x, avg_returns, returns, cov_matrix, RISK_FREE_RATE)
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
            "SortinoRatio": optimized_sortino,
            "weights": optimized_weights
        }
    else:
        return {"error": "Could not find an optimal portfolio for the given target return. Try a different value or fewer ETFs.", "details": result.message}

@app.post("/optimize_by_risk")
async def optimize_by_risk(request: TargetOptimizationRequest):
    tickers = request.tickers
    target_risk = request.target_value # 小数として受け取る
    period = request.period # <--- Get period from request

    if not tickers:
        return {"error": "No tickers provided."}

    data = yf.download(tickers, period=period, group_by='ticker')
    data = data.xs('Close', level='Price', axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints_list = (
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # 重みの合計は1
        {'type': 'eq', 'fun': lambda x: portfolio_volatility(x, cov_matrix) - target_risk} # 目標リスクを達成
    )

    # 各資産の重み制約を動的に構築
    bounds = tuple([(0.0, 1.0)] * num_assets)

    initial_weights = num_assets * [1. / num_assets,]

    # 目的関数: リターンを最大化 (minimizeなので負のリターンを最小化)
    def maximize_return(weights):
        return -portfolio_return(weights, avg_returns)

    result = minimize(maximize_return, initial_weights, method='SLSQP',
                      bounds=bounds, constraints=constraints_list)

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_sortino = portfolio_sortino_ratio(result.x, avg_returns, returns, cov_matrix, RISK_FREE_RATE)
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
            "SortinoRatio": optimized_sortino,
            "weights": optimized_weights
        }
    else:
        return {"error": "Could not find an optimal portfolio for the given target risk. Try a different value or fewer ETFs.", "details": result.message}

@app.post("/historical_performance")
async def get_historical_performance(request: HistoricalPerformanceRequest):
    tickers = request.tickers
    period = request.period

    if not tickers:
        return {"error": "No tickers provided."}

    try:
        # 日次データを取得
        data = yf.download(tickers, period=period, interval="1d")
        # 'Close'列のみを抽出
        data = data.xs('Close', level='Price', axis=1)

        # 日次リターンを計算
        returns = data.pct_change().dropna()

        # 累積リターンを計算 (初期値を1として、(1+r1)(1+r2)... - 1)
        cumulative_returns = (1 + returns).cumprod() - 1

        # 日付を文字列形式に変換
        dates = cumulative_returns.index.strftime('%Y-%m-%d').tolist()

        # 各ティッカーの累積リターンをリストに変換
        cumulative_returns_dict = {}
        for col in cumulative_returns.columns:
            cumulative_returns_dict[col] = cumulative_returns[col].tolist()

        return {
            "dates": dates,
            "cumulative_returns": cumulative_returns_dict
        }

    except Exception as e:
        return {"error": f"Error fetching historical data: {str(e)}"}

@app.post("/monte_carlo_simulation")
async def run_monte_carlo_simulation(request: MonteCarloSimulationRequest):
    tickers = request.tickers
    period = request.period
    num_simulations = request.num_simulations
    simulation_days = request.simulation_days

    if not tickers:
        return {"error": "No tickers provided."}

    try:
        # 1. 過去の日次データを取得
        data = yf.download(tickers, period=period, interval="1d")
        data = data.xs('Close', level='Price', axis=1)

        # 2. 日次リターンと共分散行列を計算
        returns = data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # 3. ポートフォリオの重み（均等配分）
        # 将来的にはカスタムポートフォリオの重みも受け取れるように拡張可能
        num_assets = len(tickers)
        weights = np.array([1. / num_assets] * num_assets)

        # 4. モンテカルロシミュレーション
        portfolio_returns = np.dot(returns, weights)
        mean_portfolio_return = portfolio_returns.mean()
        std_portfolio_return = portfolio_returns.std()

        # シミュレーション結果を格納するリスト
        final_returns = []

        for _ in range(num_simulations):
            daily_returns = np.random.normal(mean_portfolio_return, std_portfolio_return, simulation_days)
            cumulative_return = np.prod(1 + daily_returns) - 1
            final_returns.append(cumulative_return)

        # VaR (Value at Risk) と CVaR (Conditional Value at Risk) を計算
        # 例: 95%信頼水準 (つまり、下位5%のリターン)
        final_returns_np = np.array(final_returns)
        var_95 = np.percentile(final_returns_np, 5) # 5パーセンタイル
        cvar_95 = final_returns_np[final_returns_np <= var_95].mean() # VaRを下回るリターンの平均

        return {
            "final_returns": final_returns,
            "var_95": var_95,
            "cvar_95": cvar_95
        }

    except Exception as e:
        return {"error": f"Error running Monte Carlo simulation: {str(e)}"}

@app.post("/analyze_csv_data")
async def analyze_csv_data(request: CSVAnalysisRequest):
    import io

    try:
        # CSVデータをDataFrameに読み込む
        data = pd.read_csv(io.StringIO(request.csv_data))

        # 'Date'列をインデックスに設定し、日付形式に変換
        if 'Date' not in data.columns:
            raise ValueError("CSV must contain a 'Date' column.")
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.set_index('Date')

        # 数値列のみを選択（ティッカー列）
        numeric_cols = data.select_dtypes(include=np.number).columns
        if numeric_cols.empty:
            raise ValueError("No numeric (ticker) columns found in CSV.")
        data = data[numeric_cols]

        # 日次リターンの計算
        returns = data.pct_change().dropna()

        # 年率リスク・リターンの計算 (252営業日として計算)
        annual_returns = returns.mean() * 252
        annual_volatility = returns.std() * (252 ** 0.5)

        # 結果をまとめる
        result_df = pd.DataFrame({
            'Return': annual_returns,
            'Risk': annual_volatility,
            'Ticker': annual_returns.index
        })

        # 結果をJSON形式で返す
        return result_df.to_dict(orient='records')

    except Exception as e:
        return {"error": f"Error analyzing CSV data: {str(e)}"}


@app.post("/dca_simulation")
async def run_dca_simulation(request: DcaSimulationRequest):
    try:
        # 1. Get historical data
        data = yf.download(request.tickers, period=request.period, interval="1d", group_by='ticker')['Close']
        data.dropna(inplace=True)

        # Ensure weights match the order of columns in the data
        weights = np.array([request.weights.get(ticker, 0.0) for ticker in data.columns])
        if np.sum(weights) == 0: return {"error": "Sum of weights is zero."}
        weights = weights / np.sum(weights) # Normalize

        # 2. Determine investment dates
        if request.frequency == 'monthly':
            # Resample to get the first business day of each month
            investment_dates = data.resample('MS').first().index
        elif request.frequency == 'quarterly':
            # Resample to get the first business day of each quarter
            investment_dates = data.resample('QS-JAN').first().index
        else:
            raise ValueError("Invalid frequency")

        # 3. Run the simulation
        total_shares = np.zeros(len(data.columns))
        portfolio_values = []
        total_invested = 0.0

        # Create a Series to store portfolio value for each day
        daily_portfolio_value = pd.Series(index=data.index, dtype=float)

        current_investment_date_idx = 0

        for date in data.index:
            # Check if today is an investment day
            if current_investment_date_idx < len(investment_dates) and date >= investment_dates[current_investment_date_idx]:
                total_invested += request.investment_amount
                # Get prices on the investment day
                current_prices = data.loc[date].values
                # Calculate new shares to buy, avoiding division by zero
                additional_shares = (request.investment_amount * weights) / np.where(current_prices > 0, current_prices, np.inf)
                total_shares += additional_shares
                current_investment_date_idx += 1

            # Calculate portfolio value for the current day
            daily_portfolio_value[date] = np.dot(total_shares, data.loc[date].values)

        # 4. Prepare results
        final_value = daily_portfolio_value.iloc[-1]

        return {
            "dates": daily_portfolio_value.index.strftime('%Y-%m-%d').tolist(),
            "portfolio_values": daily_portfolio_value.tolist(),
            "total_invested": total_invested,
            "final_value": final_value,
            "profit_loss": final_value - total_invested
        }

    except Exception as e:
        return {"error": f"Error running DCA simulation: {str(e)}"}


@app.post("/future_dca_simulation")
async def run_future_dca_simulation(request: FutureDcaSimulationRequest):
    try:
        # Simulation parameters
        num_simulations = 500 # Number of Monte Carlo simulations
        num_years = request.years
        investment_amount = request.investment_amount
        frequency = 12 if request.frequency == 'monthly' else 4
        num_steps = num_years * frequency

        # Convert annual portfolio stats to periodic stats
        periodic_return = (1 + request.portfolio_return)**(1/frequency) - 1
        periodic_risk = request.portfolio_risk / np.sqrt(frequency)

        # Store final values for all simulations
        all_scenarios = np.zeros((num_simulations, num_steps + 1))
        total_invested_steps = np.zeros(num_steps + 1)

        for i in range(num_simulations):
            portfolio_value = 0
            total_invested = 0
            all_scenarios[i, 0] = 0
            total_invested_steps[0] = 0

            for t in range(1, num_steps + 1):
                # Add new investment
                portfolio_value += investment_amount
                total_invested += investment_amount

                # Simulate market return for the period
                market_return = np.random.normal(periodic_return, periodic_risk)
                portfolio_value *= (1 + market_return)

                all_scenarios[i, t] = portfolio_value
                total_invested_steps[t] = total_invested

        # Calculate mean, upper (95th percentile), and lower (5th percentile) outcomes
        mean_scenario = np.mean(all_scenarios, axis=0)
        upper_scenario = np.percentile(all_scenarios, 95, axis=0)
        lower_scenario = np.percentile(all_scenarios, 5, axis=0)

        # Generate time labels (e.g., Year 1, Year 2...)
        time_labels = [f"Year {t/frequency:.2f}" for t in range(num_steps + 1)]

        return {
            "time_labels": time_labels,
            "mean_scenario": mean_scenario.tolist(),
            "upper_scenario": upper_scenario.tolist(),
            "lower_scenario": lower_scenario.tolist(),
            "total_invested": total_invested_steps.tolist(),
            "final_mean_value": mean_scenario[-1],
        }

    except Exception as e:
        return {"error": f"Error running future DCA simulation: {str(e)}"}

@app.post("/correlation_matrix")
async def get_correlation_matrix(request: HistoricalPerformanceRequest):
    tickers = request.tickers
    period = request.period

    if not tickers:
        return {"error": "No tickers provided."}

    try:
        # Fetch historical data
        data = yf.download(tickers, period=period, interval="1d")
        data = data.xs('Close', level='Price', axis=1)
        
        # Calculate daily returns
        returns = data.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr()
        
        # Format for Plotly heatmap
        return {
            "x": correlation_matrix.columns.tolist(),
            "y": correlation_matrix.index.tolist(),
            "z": correlation_matrix.values.tolist()
        }

    except Exception as e:
        return {"error": f"Error calculating correlation matrix: {str(e)}"}
