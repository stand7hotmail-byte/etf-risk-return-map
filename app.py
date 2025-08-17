from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 拡張されたETFティッカーリスト
ALL_ETF_TICKERS = ['SPY', 'VOO', 'QQQ', 'VTI', 'VXUS', 'BND', 'AGG', 'GLD', 'TLT', 'XLK', 'XLF', 'XLV', 'VNQ', 'IEMG', 'EFA']

# リスクフリーレート (年率)
RISK_FREE_RATE = 0.02 # 例: 2%

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/etf_list")
async def get_etf_list():
    return ALL_ETF_TICKERS

@app.get("/risk_free_rate")
async def get_risk_free_rate():
    return {"risk_free_rate": RISK_FREE_RATE}

@app.get("/data")
async def get_etf_data(tickers: list[str] = Query(ALL_ETF_TICKERS), period: str = Query("5y")): # デフォルトで全ティッカーを選択
    if not tickers:
        return [] # ティッカーが選択されていない場合は空のリストを返す

    # --- 2. yfinanceで株価データを取得 ---
    # 過去5年分のデータを取得
    data = yf.download(tickers, period=period)
    # MultiIndexから'Close'のデータのみを抽出（これが実質的な調整済み終値）
    data = data.xs('Close', level='Price', axis=1)

    # --- 3. 日次リターンの計算 ---
    returns = data.pct_change().dropna()

    # --- 4. 年率リスク・リターンの計算 ---
    # (252営業日として計算)
    annual_returns = returns.mean() * 252
    annual_volatility = returns.std() * (252 ** 0.5)

    # 結果をまとめる
    result_df = pd.DataFrame({
        'Return': annual_returns,
        'Risk': annual_volatility,
        'Ticker': annual_returns.index
    })

    # --- 5. 結果をJSON形式で返す ---
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

@app.get("/efficient_frontier")
async def get_efficient_frontier(tickers: list[str] = Query(ALL_ETF_TICKERS), period: str = Query("5y")):
    if not tickers:
        return {"frontier_points": [], "tangency_portfolio": None, "tangency_portfolio_weights": {}}

    # --- 1. 株価データを取得 ---
    data = yf.download(tickers, period=period)
    data = data.xs('Close', level='Price', axis=1)

    # --- 2. 日次リターンと共分散行列を計算 ---
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},) # 重みの合計は1
    bounds = tuple((0, 1) for asset in range(num_assets)) # 各資産の重みは0から1の間

    efficient_frontier_points = []

    # リターン目標の範囲をより適切に設定
    min_return = avg_returns.min()
    max_return = avg_returns.max()
    target_returns = np.linspace(min_return * 0.8, max_return * 1.2, 50) # 範囲を広げる

    max_sharpe_ratio = -np.inf
    tangency_portfolio = None
    tangency_portfolio_weights = {}

    for target_return in target_returns:
        # 目的関数: リスクを最小化
        def minimize_volatility(weights):
            return portfolio_volatility(weights, cov_matrix)

        # 制約: 目標リターンを達成
        constraints_with_target = constraints + \
                                  ({'type': 'eq', 'fun': lambda x: portfolio_return(x, avg_returns) - target_return},)

        # 初期値
        initial_weights = num_assets * [1. / num_assets,]

        # 最適化を実行
        result = minimize(minimize_volatility, initial_weights, method='SLSQP',
                          bounds=bounds, constraints=constraints_with_target)

        if result.success:
            risk = portfolio_volatility(result.x, cov_matrix)
            ret = portfolio_return(result.x, avg_returns)
            efficient_frontier_points.append({
                'Risk': risk,
                'Return': ret
            })

            # シャープ・レシオを計算し、最大シャープ・レシオのポートフォリオを更新
            sharpe = portfolio_sharpe_ratio(result.x, avg_returns, cov_matrix, RISK_FREE_RATE)
            if sharpe > max_sharpe_ratio:
                max_sharpe_ratio = sharpe
                tangency_portfolio = {'Risk': risk, 'Return': ret, 'SharpeRatio': sharpe}
                # 重みを保存
                tangency_portfolio_weights = {tickers[i]: result.x[i] for i in range(num_assets)}

    # リスクでソートし、重複する点や不適切な点を除外して滑らかにする
    efficient_frontier_points.sort(key=lambda x: x['Risk'])

    # 効率的フロンティアの点をフィルタリングして、より滑らかな曲線にする
    filtered_frontier = []
    if efficient_frontier_points:
        filtered_frontier.append(efficient_frontier_points[0])
        for i in range(1, len(efficient_frontier_points)):
            # 前の点よりもリスクが大きく、リターンも大きい（または同等）場合のみ追加
            if efficient_frontier_points[i]['Risk'] > filtered_frontier[-1]['Risk'] and \
               efficient_frontier_points[i]['Return'] >= filtered_frontier[-1]['Return']:
                filtered_frontier.append(efficient_frontier_points[i])
            # または、リスクが同じでリターンが大きい場合
            elif efficient_frontier_points[i]['Risk'] == filtered_frontier[-1]['Risk'] and \
                 efficient_frontier_points[i]['Return'] > filtered_frontier[-1]['Return']:
                filtered_frontier[-1] = efficient_frontier_points[i] # より良い点に置き換え

    return {"frontier_points": filtered_frontier, "tangency_portfolio": tangency_portfolio, "tangency_portfolio_weights": tangency_portfolio_weights}

class CustomPortfolioRequest(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"

class TargetOptimizationRequest(BaseModel):
    tickers: list[str]
    target_value: float
    period: str = "5y"

@app.post("/custom_portfolio_data")
async def calculate_custom_portfolio(request: CustomPortfolioRequest):
    tickers = request.tickers
    weights_dict = request.weights
    period = request.period

    if not tickers:
        return {"error": "No tickers provided."}

    # --- 1. 株価データを取得 ---
    data = yf.download(tickers, period=period)
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

    data = yf.download(tickers, period=period)
    data = data.xs('Close', level='Price', axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints = (
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # 重みの合計は1
        {'type': 'eq', 'fun': lambda x: portfolio_return(x, avg_returns) - target_return} # 目標リターンを達成
    )
    bounds = tuple((0, 1) for asset in range(num_assets)) # 各資産の重みは0から1の間

    initial_weights = num_assets * [1. / num_assets,]

    # 目的関数: リスクを最小化
    def minimize_volatility(weights):
        return portfolio_volatility(weights, cov_matrix)

    result = minimize(minimize_volatility, initial_weights, method='SLSQP',
                      bounds=bounds, constraints=constraints)

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
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

    data = yf.download(tickers, period=period)
    data = data.xs('Close', level='Price', axis=1)
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 最適化の制約条件
    constraints = (
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # 重みの合計は1
        {'type': 'eq', 'fun': lambda x: portfolio_volatility(x, cov_matrix) - target_risk} # 目標リスクを達成
    )
    bounds = tuple((0, 1) for asset in range(num_assets)) # 各資産の重みは0から1の間

    initial_weights = num_assets * [1. / num_assets,]

    # 目的関数: リターンを最大化 (minimizeなので負のリターンを最小化)
    def maximize_return(weights):
        return -portfolio_return(weights, avg_returns)

    result = minimize(maximize_return, initial_weights, method='SLSQP',
                      bounds=bounds, constraints=constraints)

    if result.success:
        optimized_risk = portfolio_volatility(result.x, cov_matrix)
        optimized_return = portfolio_return(result.x, avg_returns)
        optimized_weights = {tickers[i]: result.x[i] for i in range(num_assets)}
        return {
            "Risk": optimized_risk,
            "Return": optimized_return,
            "weights": optimized_weights
        }
    else:
        return {"error": "Could not find an optimal portfolio for the given target risk. Try a different value or fewer ETFs.", "details": result.message}