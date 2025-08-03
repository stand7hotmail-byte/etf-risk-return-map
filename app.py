
from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import pandas as pd

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 拡張されたETFティッカーリスト
ALL_ETF_TICKERS = ['SPY', 'VOO', 'QQQ', 'VTI', 'VXUS', 'BND', 'AGG', 'GLD', 'TLT', 'XLK', 'XLF', 'XLV', 'VNQ', 'IEMG', 'EFA']

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/etf_list")
async def get_etf_list():
    return ALL_ETF_TICKERS

@app.get("/data")
async def get_etf_data(tickers: list[str] = Query(ALL_ETF_TICKERS)): # デフォルトで全ティッカーを選択
    if not tickers:
        return [] # ティッカーが選択されていない場合は空のリストを返す

    # --- 2. yfinanceで株価データを取得 ---
    # 過去1年分のデータを取得
    data = yf.download(tickers, period="1y")
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
