
from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 
ALL_ETF_TICKERS = ['SPY', 'VOO', 'QQQ', 'VTI', 'VXUS', 'BND', 'AGG', 'GLD', 'TLT', 'XLK', 'XLF', 'XLV', 'VNQ', 'IEMG', 'EFA']

#  (
RISK_FREE_RATE = 0.02 # 

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
async def get_etf_data(tickers: list[str] = Query(ALL_ETF_TICKERS)): # 
    if not tickers:
        return [] # 

    # --- 2. yfinance
    # 5
    data = yf.download(tickers, period="5y")
    # MultiIndex'Close'(
    data = data.xs('Close', level='Price', axis=1)

    # --- 3. 
    returns = data.pct_change().dropna()

    # --- 4. 
    # (252)
    annual_returns = returns.mean() * 252
    annual_volatility = returns.std() * (252 ** 0.5)

    # 
    result_df = pd.DataFrame({
        'Return': annual_returns,
        'Risk': annual_volatility,
        'Ticker': annual_returns.index
    })

    # --- 5. JSON
    return result_df.to_dict(orient='records')

# 
def portfolio_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

# 
def portfolio_return(weights, avg_returns):
    return np.sum(avg_returns * weights)

@app.get("/efficient_frontier")
async def get_efficient_frontier(tickers: list[str] = Query(ALL_ETF_TICKERS)):
    if not tickers:
        return []

    # --- 1. 
    data = yf.download(tickers, period="5y")
    data = data.xs('Close', level='Price', axis=1)

    # --- 2. 
    returns = data.pct_change().dropna()
    avg_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    num_assets = len(tickers)

    # 
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},) # 1
    bounds = tuple((0, 1) for asset in range(num_assets)) # 01

    efficient_frontier_points = []

    # 
    min_return = avg_returns.min()
    max_return = avg_returns.max()
    target_returns = np.linspace(min_return * 0.8, max_return * 1.2, 50) # 

    for target_return in target_returns:
        # 
        def minimize_volatility(weights):
            return portfolio_volatility(weights, cov_matrix)

        # :
        constraints_with_target = constraints + \
                                  ({'type': 'eq', 'fun': lambda x: portfolio_return(x, avg_returns) - target_return},)

        # 
        initial_weights = num_assets * [1. / num_assets,]

        # 
        result = minimize(minimize_volatility, initial_weights, method='SLSQP',
                          bounds=bounds, constraints=constraints_with_target)

        if result.success:
            efficient_frontier_points.append({
                'Risk': portfolio_volatility(result.x, cov_matrix),
                'Return': portfolio_return(result.x, avg_returns)
            })

    # 
    efficient_frontier_points.sort(key=lambda x: x['Risk'])

    # 
    filtered_frontier = []
    if efficient_frontier_points:
        filtered_frontier.append(efficient_frontier_points[0])
        for i in range(1, len(efficient_frontier_points)):
            # 
            if efficient_frontier_points[i]['Risk'] > filtered_frontier[-1]['Risk'] and \
               efficient_frontier_points[i]['Return'] >= filtered_frontier[-1]['Return']:
                filtered_frontier.append(efficient_frontier_points[i])
            # 
            elif efficient_frontier_points[i]['Risk'] == filtered_frontier[-1]['Risk'] and \
                 efficient_frontier_points[i]['Return'] > filtered_frontier[-1]['Return']:
                filtered_frontier[-1] = efficient_frontier_points[i] # 

    return filtered_frontier
