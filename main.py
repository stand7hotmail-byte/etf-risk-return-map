import time
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from scipy.optimize import minimize
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CustomPortfolioRequest,
    TargetOptimizationRequest,
    HistoricalPerformanceRequest,
    MonteCarloSimulationRequest,
    CSVAnalysisRequest,
    DcaSimulationRequest,
    FutureDcaSimulationRequest,
)


app = FastAPI()

origins = [
    "https://etf-risk-return-map-project.an.r.appspot.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import csv # Add this import

# In-memory cache for ETF details
etf_details_cache = {}
CACHE_TTL = timedelta(hours=1)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from fastapi.responses import HTMLResponse
from fastapi.requests import Request

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# --- Load ETF Definitions from CSV ---
ETF_DEFINITIONS = {}
try:
    with open('etf_list.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['ticker']
            ETF_DEFINITIONS[ticker] = {
                'asset_class': row['asset_class'],
                'region': row['region'],
                'name': row['name'],
                'style': row['style'],
                'size': row['size'],
                'sector': row['sector'],
                'theme': row['theme'],
            }
except FileNotFoundError:
    print("etf_list.csv not found. ETF definitions will be empty.")
except Exception as e:
    print(f"Error loading etf_list.csv: {e}")

ALL_ETF_TICKERS = list(ETF_DEFINITIONS.keys()) # Update this to use keys from ETF_DEFINITIONS

@app.get("/etf_list")
async def get_etf_list():
    return ETF_DEFINITIONS # Return the dictionary

@app.get("/risk_free_rate")
async def get_risk_free_rate():
    return {"risk_free_rate": RISK_FREE_RATE}

# ... (existing code) ...

def _calculate_portfolio_metrics(
    data: pd.DataFrame, final_tickers: list[str]
) -> tuple[pd.Series, pd.DataFrame]:
    """Calculates annual returns and covariance matrix for a given DataFrame of stock prices.

    Args:
        data: A pandas DataFrame containing historical close prices.
        final_tickers: A list of tickers present in the data.

    Returns:
        A tuple containing:
            - avg_returns: Annualized average returns for each ticker.
            - cov_matrix: Annualized covariance matrix of returns.

    """
    returns = data.pct_change().dropna()
    returns = returns[final_tickers]  # Ensure consistent ordering
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    return avg_returns, cov_matrix


def _filter_efficient_frontier(
    efficient_frontier_points: list[dict[str, float]]
) -> list[dict[str, float]]:
    """Filters the efficient frontier points to create a smooth, non-decreasing curve.

    Args:
        efficient_frontier_points: A list of dictionaries, each representing a point on the efficient frontier.

    Returns:
        A filtered list of efficient frontier points.

    """
    if not efficient_frontier_points:
        return []

    efficient_frontier_points.sort(key=lambda x: x["Risk"])

    filtered_frontier = []
    if efficient_frontier_points:
        filtered_frontier.append(efficient_frontier_points[0])
        for i in range(1, len(efficient_frontier_points)):
            if (
                efficient_frontier_points[i]["Risk"] > filtered_frontier[-1]["Risk"]
                and efficient_frontier_points[i]["Return"]
                >= filtered_frontier[-1]["Return"]
            ):
                filtered_frontier.append(efficient_frontier_points[i])
            elif (
                efficient_frontier_points[i]["Risk"] == filtered_frontier[-1]["Risk"]
                and efficient_frontier_points[i]["Return"]
                > filtered_frontier[-1]["Return"]
            ):
                filtered_frontier[-1] = efficient_frontier_points[i]
    return filtered_frontier


RISK_FREE_RATE = 0.02

def _fetch_and_prepare_data(tickers: list[str], period: str, db: Session) -> pd.DataFrame:
    """
    Fetches historical stock data using yfinance.
    (Database caching logic can be added here later)
    """
    data = yf.download(tickers, period=period, group_by="ticker")
    if data.empty:
        raise HTTPException(status_code=404, detail="Could not download data for the given tickers.")
    
    # Handle single vs multi-ticker download
    if len(tickers) > 1:
        # For multi-ticker, data has multi-level columns, e.g., ('VTI', 'Close')
        data = data.xs("Close", level="Price", axis=1)
    else:
        # For single-ticker, columns are flat, e.g., 'Close'
        data = data[["Close"]]
        data.columns = tickers # Rename 'Close' to the ticker name

    # Drop tickers with all NaN values (e.g., for a ticker that doesn't exist)
    data = data.dropna(axis=1, how='all')
    
    # Forward-fill and back-fill any remaining NaNs
    data = data.ffill().bfill()

    if data.empty:
        raise HTTPException(status_code=404, detail="No valid data remaining after cleaning.")

    return data

@app.get("/efficient_frontier")
async def get_efficient_frontier(
    tickers: list[str] = Query(ALL_ETF_TICKERS),
    period: str = Query("5y"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Calculates the efficient frontier and tangency portfolio for a given set of ETFs.

    Args:
        tickers: A list of ETF tickers to include in the analysis.
        period: The historical period for data (e.g., "5y").
        db: The SQLAlchemy session for database access.

    Returns:
        A dictionary containing the efficient frontier points, tangency portfolio,
        and its weights.

    """
    start_time = time.time()

    if not tickers:
        return {
            "frontier_points": [],
            "tangency_portfolio": None,
            "tangency_portfolio_weights": {},
        }

    data = _fetch_and_prepare_data(tickers, period, db)
    final_tickers = data.columns.tolist()

    avg_returns, cov_matrix = _calculate_portfolio_metrics(data, final_tickers)

    num_assets = len(final_tickers)

    efficient_frontier_points, tangency_portfolio, tangency_portfolio_weights = \
        _run_optimization_loop(num_assets, avg_returns, cov_matrix, final_tickers, RISK_FREE_RATE)

    if not efficient_frontier_points:
        return {"error": "No efficient frontier points could be generated."}

    filtered_frontier = _filter_efficient_frontier(efficient_frontier_points)

    # Calculate individual ETF risk and return
    etf_data = []
    for ticker in final_tickers:
        # Calculate individual ETF's annual return and volatility
        etf_returns = data[ticker].pct_change().dropna()
        etf_annual_return = etf_returns.mean() * 252
        etf_annual_volatility = etf_returns.std() * np.sqrt(252)
        etf_data.append({"Ticker": ticker, "Risk": etf_annual_volatility, "Return": etf_annual_return})

    print(
        f"--- /efficient_frontier endpoint took "\
        f"{(time.time() - start_time) * 1000:.2f} ms ---"
    )
    return {
        "etf_data": etf_data,
        "frontier_points": filtered_frontier,
        "tangency_portfolio": tangency_portfolio,
        "tangency_portfolio_weights": tangency_portfolio_weights,
    }
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ポートフォリオのリスクを計算する関数
def portfolio_volatility(weights: np.ndarray, cov_matrix: pd.DataFrame) -> float:
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


# ポートフォリオのリターンを計算する関数
def portfolio_return(weights: np.ndarray, avg_returns: pd.Series) -> float:
    return np.sum(avg_returns * weights)


# シャープ・レシオを計算する関数
def portfolio_sharpe_ratio(
    weights: np.ndarray, avg_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float
) -> float:
    p_return = portfolio_return(weights, avg_returns)
    p_volatility = portfolio_volatility(weights, cov_matrix)
    if p_volatility == 0:  # リスクが0の場合は無限大を返す（または非常に大きな値）
        return -np.inf
    return (p_return - risk_free_rate) / p_volatility


def portfolio_downside_deviation(
    weights: np.ndarray, returns: pd.DataFrame, risk_free_rate: float
) -> float:
    portfolio_returns = np.dot(returns, weights)
    downside_returns = portfolio_returns[portfolio_returns < risk_free_rate]
    if len(downside_returns) == 0:  # No downside returns, so downside deviation is 0
        return 0.0
    return np.sqrt(np.mean((downside_returns - risk_free_rate) ** 2)) * (
        252**0.5
    )  # Annualized


def portfolio_sortino_ratio(
    weights: np.ndarray,
    avg_returns: pd.Series,
    returns: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
) -> float:
    p_return = portfolio_return(weights, avg_returns)
    downside_dev = portfolio_downside_deviation(weights, returns, risk_free_rate)
    if downside_dev == 0:
        return np.inf  # No downside risk, so Sortino is infinite
    return (p_return - risk_free_rate) / downside_dev


def _run_optimization_loop(
    num_assets: int,
    avg_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    final_tickers: list[str],
    risk_free_rate: float,
) -> tuple[list[dict[str, float]], dict[str, Any] | None, dict[str, float]]:
    """Runs the optimization loop to calculate efficient frontier points and the tangency portfolio.

    Args:
        num_assets: The number of assets in the portfolio.
        avg_returns: Annualized average returns for each ticker.
        cov_matrix: Annualized covariance matrix of returns.
        final_tickers: A list of tickers present in the data.
        risk_free_rate: The risk-free rate.

    Returns:
        A tuple containing:
            - efficient_frontier_points: A list of dictionaries, each representing a point on the efficient frontier.
            - tangency_portfolio: A dictionary representing the tangency portfolio (or None if not found).
            - tangency_portfolio_weights: A dictionary of weights for the tangency portfolio.

    """
    constraints_list = ({"type": "eq", "fun": lambda x: np.sum(x) - 1},)
    bounds = tuple([(0.0, 1.0)] * num_assets)

    efficient_frontier_points = []
    target_returns = np.linspace(avg_returns.min() * 0.8, avg_returns.max() * 1.2, 20)
    max_sharpe_ratio = -np.inf
    tangency_portfolio = None
    tangency_portfolio_weights = {}

    for target_return in target_returns:

        def minimize_volatility(weights):
            return portfolio_volatility(weights, cov_matrix)

        constraints_with_target = constraints_list + (
            {
                "type": "eq",
                "fun": lambda x, tr=target_return: (
                    portfolio_return(x, avg_returns) - tr
                ),
            },
        )
        initial_weights = num_assets * [
            1.0 / num_assets,
        ]
        result = minimize(
            minimize_volatility,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_with_target,
        )

        if result.success:
            risk = portfolio_volatility(result.x, cov_matrix)
            ret = portfolio_return(result.x, avg_returns)
            efficient_frontier_points.append({"Risk": risk, "Return": ret})

            sharpe = portfolio_sharpe_ratio(
                result.x, avg_returns, cov_matrix, risk_free_rate
            )
            if sharpe > max_sharpe_ratio:
                max_sharpe_ratio = sharpe
                tangency_portfolio = {
                    "Risk": risk,
                    "Return": ret,
                    "SharpeRatio": sharpe,
                }
                tangency_portfolio_weights = dict(
                    zip(
                        final_tickers,
                        result.x,
                        strict=True
                    )
                )
    return efficient_frontier_points, tangency_portfolio, tangency_portfolio_weights





@app.post("/custom_portfolio_data")
async def calculate_custom_portfolio(request: CustomPortfolioRequest):
    tickers = request.tickers
    weights_dict = request.weights
    period = request.period

    if not tickers:
        return {"error": "No tickers provided."}

    # --- 1. 株価データを取得 ---
    data = yf.download(tickers, period=period, group_by="ticker")
    data = data.xs("Close", level="Price", axis=1)

    # --- 2. 日次リターンと共分散行列を計算 ---
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # 重み辞書をNumPy配列に変換し、ティッカーの順序に合わせる
    # 欠損値があるティッカーは除外する
    available_tickers = [
        t for t in tickers if t in avg_returns.index and t in cov_matrix.columns
    ]
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
        p_volatility = portfolio_volatility(
            weights, cov_matrix.loc[available_tickers, available_tickers]
        )
    except Exception as e:
        return {"error": f"Error calculating portfolio: {str(e)}"}

    return {"Risk": p_volatility, "Return": p_return}


@app.post("/optimize_by_return")
async def optimize_by_return(request: TargetOptimizationRequest):
    tickers = request.tickers
    target_return = request.target_value  # 小数として受け取る
    period = request.period  # <--- Get period from request

    if not tickers:
        return {"error": "No tickers provided."}

    data = yf.download(tickers, period=period, group_by="ticker")
    data = data.xs("Close", level="Price", axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints_list = (
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},  # 重みの合計は1
        {
            "type": "eq",
            "fun": lambda x: portfolio_return(x, avg_returns) - target_return,
        },  # 目標リターンを達成
    )

    # 各資産の重み制約を動的に構築
    bounds = tuple([(0.0, 1.0)] * num_assets)

    initial_weights = num_assets * [
        1.0 / num_assets,
    ]

    # 目的関数: リスクを最小化
    def minimize_volatility(weights):
        return portfolio_volatility(weights, cov_matrix)

    result = minimize(
        minimize_volatility,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_list,
    )

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_sortino = portfolio_sortino_ratio(
            result.x, avg_returns, returns, cov_matrix, RISK_FREE_RATE
        )
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
            "SortinoRatio": optimized_sortino,
            "weights": optimized_weights,
        }
    else:
        return {
            "error": (
                "Could not find an optimal portfolio for the given target return. "
                "Try a different value or fewer ETFs."
            ),
            "details": result.message,
        }


@app.post("/optimize_by_risk")
async def optimize_by_risk(request: TargetOptimizationRequest):
    tickers = request.tickers
    target_risk = request.target_value  # 小数として受け取る
    period = request.period  # <--- Get period from request

    if not tickers:
        return {"error": "No tickers provided."}

    data = yf.download(tickers, period=period, group_by="ticker")
    data = data.xs("Close", level="Price", axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints_list = (
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},  # 重みの合計は1
        {
            "type": "eq",
            "fun": lambda x: portfolio_volatility(x, cov_matrix) - target_risk,
        },  # 目標リスクを達成
    )

    # 各資産の重み制約を動的に構築
    bounds = tuple([(0.0, 1.0)] * num_assets)

    initial_weights = num_assets * [
        1.0 / num_assets,
    ]

    # 目的関数: リターンを最大化 (minimizeなので負のリターンを最小化)
    def maximize_return(weights):
        return -portfolio_return(weights, avg_returns)

    result = minimize(
        maximize_return,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_list,
    )

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_sortino = portfolio_sortino_ratio(
            result.x, avg_returns, returns, cov_matrix, RISK_FREE_RATE
        )
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
            "SortinoRatio": optimized_sortino,
            "weights": optimized_weights,
        }
    else:
        return {
            "error": (
                "Could not find an optimal portfolio for the given target risk. "
                "Try a different value or fewer ETFs."
            ),
            "details": result.message,
        }


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
        data = data.xs("Close", level="Price", axis=1)

        # 日次リターンを計算
        returns = data.pct_change().dropna()

        # 累積リターンを計算 (初期値を1として、(1+r1)(1+r2)... - 1)
        cumulative_returns = (1 + returns).cumprod() - 1

        # 日付を文字列形式に変換
        dates = cumulative_returns.index.strftime("%Y-%m-%d").tolist()

        # 各ティッカーの累積リターンをリストに変換
        cumulative_returns_dict = {}
        for col in cumulative_returns.columns:
            cumulative_returns_dict[col] = cumulative_returns[col].tolist()

        return {"dates": dates, "cumulative_returns": cumulative_returns_dict}

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
        data = data.xs("Close", level="Price", axis=1)

        # 2. 日次リターンと共分散行列を計算
        returns = data.pct_change().dropna()

        # 3. ポートフォリオの重み（均等配分）
        # 将来的にはカスタムポートフォリオの重みも受け取れるように拡張可能
        num_assets = len(tickers)
        weights = np.array([1.0 / num_assets] * num_assets)

        # 4. モンテカルロシミュレーション
        portfolio_returns = np.dot(returns, weights)
        mean_portfolio_return = portfolio_returns.mean()
        std_portfolio_return = portfolio_returns.std()

        # シミュレーション結果を格納するリスト
        final_returns = []

        for _ in range(num_simulations):
            daily_returns = np.random.normal(
                mean_portfolio_return, std_portfolio_return, simulation_days
            )
            cumulative_return = np.prod(1 + daily_returns) - 1
            final_returns.append(cumulative_return)

        # VaR (Value at Risk) と CVaR (Conditional Value at Risk) を計算
        # 例: 95%信頼水準 (つまり、下位5%のリターン)
        final_returns_np = np.array(final_returns)
        var_95 = np.percentile(final_returns_np, 5)  # 5パーセンタイル
        cvar_95 = final_returns_np[
            final_returns_np <= var_95
        ].mean()  # VaRを下回るリターンの平均

        return {"final_returns": final_returns, "var_95": var_95, "cvar_95": cvar_95}

    except Exception as e:
        return {"error": f"Error running Monte Carlo simulation: {str(e)}"}


@app.post("/analyze_csv_data")
async def analyze_csv_data(request: CSVAnalysisRequest):
    import io

    try:
        # CSVデータをDataFrameに読み込む
        data = pd.read_csv(io.StringIO(request.csv_data))

        # 'Date'列をインデックスに設定し、日付形式に変換
        if "Date" not in data.columns:
            raise ValueError("CSV must contain a 'Date' column.")
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.set_index("Date")

        # 数値列のみを選択（ティッカー列）
        numeric_cols = data.select_dtypes(include=np.number).columns
        if numeric_cols.empty:
            raise ValueError("No numeric (ticker) columns found in CSV.")
        data = data[numeric_cols]

        # 日次リターンの計算
        returns = data.pct_change().dropna()

        # 年率リスク・リターンの計算 (252営業日として計算)
        annual_returns = returns.mean() * 252
        annual_volatility = returns.std() * (252**0.5)

        # 結果をまとめる
        result_df = pd.DataFrame(
            {
                "Return": annual_returns,
                "Risk": annual_volatility,
                "Ticker": annual_returns.index,
            }
        )

        # 結果をJSON形式で返す
        return result_df.to_dict(orient="records")

    except Exception as e:
        return {"error": f"Error analyzing CSV data: {str(e)}"}


@app.post("/dca_simulation")
async def run_dca_simulation(request: DcaSimulationRequest):
    try:
        # 1. Get historical data
        data = yf.download(
            request.tickers, period=request.period, interval="1d", group_by="ticker"
        )["Close"]
        data.dropna(inplace=True)

        # Ensure weights match the order of columns in the data
        weights = np.array(
            [request.weights.get(ticker, 0.0) for ticker in data.columns]
        )
        if np.sum(weights) == 0:
            return {"error": "Sum of weights is zero."}
        weights = weights / np.sum(weights)  # Normalize

        # 2. Determine investment dates
        if request.frequency == "monthly":
            # Resample to get the first business day of each month
            investment_dates = data.resample("MS").first().index
        elif request.frequency == "quarterly":
            # Resample to get the first business day of each quarter
            investment_dates = data.resample("QS-JAN").first().index
        else:
            raise ValueError("Invalid frequency")

        # 3. Run the simulation
        total_shares = np.zeros(len(data.columns))
        total_invested = 0.0

        # Create a Series to store portfolio value for each day
        daily_portfolio_value = pd.Series(index=data.index, dtype=float)

        current_investment_date_idx = 0

        for date in data.index:
            # Check if today is an investment day
            if (
                current_investment_date_idx < len(investment_dates)
                and date >= investment_dates[current_investment_date_idx]
            ):
                total_invested += request.investment_amount
                # Get prices on the investment day
                current_prices = data.loc[date].values
                # Calculate new shares to buy, avoiding division by zero
                additional_shares = (request.investment_amount * weights) / np.where(
                    current_prices > 0, current_prices, np.inf
                )
                total_shares += additional_shares
                current_investment_date_idx += 1

            # Calculate portfolio value for the current day
            daily_portfolio_value[date] = np.dot(total_shares, data.loc[date].values)

        # 4. Prepare results
        final_value = daily_portfolio_value.iloc[-1]

        return {
            "dates": daily_portfolio_value.index.strftime("%Y-%m-%d").tolist(),
            "portfolio_values": daily_portfolio_value.tolist(),
            "total_invested": total_invested,
            "final_value": final_value,
            "profit_loss": final_value - total_invested,
        }

    except Exception as e:
        return {"error": f"Error running DCA simulation: {str(e)}"}


@app.post("/future_dca_simulation")
async def run_future_dca_simulation(request: FutureDcaSimulationRequest):
    try:
        # Simulation parameters
        num_simulations = 500  # Number of Monte Carlo simulations
        num_years = request.years
        investment_amount = request.investment_amount
        frequency = 12 if request.frequency == "monthly" else 4
        num_steps = num_years * frequency

        # Convert annual portfolio stats to periodic stats
        periodic_return = (1 + request.portfolio_return) ** (1 / frequency) - 1
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
                portfolio_value *= 1 + market_return

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
        data = data.xs("Close", level="Price", axis=1)

        # Calculate daily returns
        returns = data.pct_change().dropna()

        # Calculate correlation matrix
        correlation_matrix = returns.corr()

        # Format for Plotly heatmap
        return {
            "x": correlation_matrix.columns.tolist(),
            "y": correlation_matrix.index.tolist(),
            "z": correlation_matrix.values.tolist(),
        }

    except Exception as e:
        return {"error": f"Error calculating correlation matrix: {str(e)}"}


def format_market_cap(cap):
    if cap is None or not isinstance(cap, (int, float)):
        return "N/A"
    if cap >= 1_000_000_000_000:
        return f"{cap / 1_000_000_000_000:.2f}T"
    if cap >= 1_000_000_000:
        return f"{cap / 1_000_000_000:.2f}B"
    if cap >= 1_000_000:
        return f"{cap / 1_000_000:.2f}M"
    if cap >= 1_000:
        return f"{cap / 1_000:.2f}K"
    return str(cap)


@app.get("/etf_details/{ticker}")
async def get_etf_details(ticker: str):
    # Check cache first
    if ticker in etf_details_cache:
        cached_entry = etf_details_cache[ticker]
        if datetime.now() - cached_entry["timestamp"] < CACHE_TTL:
            return cached_entry["data"]

    # If not in cache or expired, fetch data
    try:
        etf = yf.Ticker(ticker)
        info = etf.info

        etf_static_data = ETF_DEFINITIONS.get(ticker, {})

        basic_info = {
            "longName": info.get("longName", "N/A"),
            "fundFamily": info.get("fundFamily", "N/A"),
        }

        key_metrics = {
            "AUM": format_market_cap(info.get("totalAssets")),
            "Yield": (
                f'{info.get("trailingAnnualDividendYield", 0) * 100:.2f}%'
                if info.get("trailingAnnualDividendYield")
                else "N/A"
            ),
            "Expense Ratio": (
                f'{info.get("annualReportExpenseRatio", 0) * 100:.2f}%'
                if info.get("annualReportExpenseRatio")
                else "N/A"
            ),
            "YTD Return": (
                f'{info.get("ytdReturn", 0) * 100:.2f}%'
                if info.get("ytdReturn")
                else "N/A"
            ),
            "Beta": f'{info.get("beta", "N/A")}',
            "52wk High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52wk Low": info.get("fiftyTwoWeekLow", "N/A"),
        }

        summary_parts = []
        fund_family = basic_info.get("fundFamily")
        if fund_family and fund_family != "N/A":
            summary_parts.append(f"「{fund_family}」が提供する")

        category = info.get("category")
        asset_class = etf_static_data.get("asset_class")
        region = etf_static_data.get("region")

        description_parts = []
        if region and region.strip():
            description_parts.append(f"【{region.strip()}】")
        if asset_class and asset_class.strip():
            description_parts.append(f"の【{asset_class.strip()}】")

        if description_parts:
            summary_parts.append("".join(description_parts) + "に投資するETFです。")

        if category and category != "N/A":
            summary_parts.append(f"カテゴリは「{category}」に分類されます。")

        style = etf_static_data.get("style")
        if style and style.strip():
            summary_parts.append(f"投資スタイルは「{style.strip()}」です。")

        theme = etf_static_data.get("theme")
        if theme and theme.strip():
            summary_parts.append(
                f"「{theme.strip()}」というテーマに焦点を当てています。"
            )

        basic_info["generatedSummary"] = (
            " ".join(summary_parts) if summary_parts else "詳細なサマリーはありません。"
        )

        result = {
            "basicInfo": basic_info,
            "keyMetrics": key_metrics,
        }

        # Store result in cache
        etf_details_cache[ticker] = {"data": result, "timestamp": datetime.now()}

        return result

    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Could not fetch details for {ticker}: {str(e)}"
        ) from e
