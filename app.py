
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    # --- 1. ETFティッカーリストの定義 ---
    tickers = ['SPY', 'QQQ', 'GLD', 'VTI', 'AGG'] # サンプルETF

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

    # --- 5. Plotlyで散布図を作成 ---
    fig = px.scatter(
        result_df,
        x='Risk',
        y='Return',
        text='Ticker', # 点の近くにティッカー名を表示
        title='ETF Risk-Return Map (Annualized)'
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        xaxis_title="Risk (Annualized Volatility)",
        yaxis_title="Expected Return (Annualized)",
    )

    # --- 6. グラフをHTML形式に変換 ---
    graph_html = pio.to_html(fig, full_html=False)

    # --- 7. HTMLテンプレートにグラフを埋め込んで返す ---
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "graph_html": graph_html}
    )
