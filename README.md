# ETF Portfolio Analysis API

A comprehensive FastAPI-based web application for ETF portfolio analysis, optimization, and simulation with interactive visualization.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Web Interface](#-web-interface)
- [Configuration](#-configuration)
- [Authentication](#-authentication)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Analysis
- **Efficient Frontier**: Calculate optimal risk-return trade-offs.
- **Monte Carlo Simulation**: Project portfolio returns with VaR/CVaR.
- **Custom Portfolio Analysis**: Analyze portfolios with custom weights.
- **Target Optimization**: Optimize for specific return or risk levels.
- **Historical Performance**: Track cumulative returns over time.
- **Correlation Matrix**: Visualize asset correlations.
- **DCA Simulation**: Backtest and forecast Dollar-Cost Averaging strategies.
- **CSV Analysis**: Analyze custom ETF data from CSV files.

### Web Interface & UX
- **Interactive Dashboard**: Modern, responsive UI built with Bootstrap 5.
- **Real-time Visualization**: Interactive Plotly.js charts.
- **Advanced Filtering**: Filter ETFs by asset class, region, style, and more.
- **Dark/Light Mode**: User-selectable theme support.

### User & Portfolio Management
- **User Authentication**: Secure user registration and login with JWT.
- **Google OAuth**: Seamless sign-in with Google accounts.
- **Portfolio Persistence**: Save, load, and manage portfolio configurations (functionality under review).

### Affiliate & Admin
- **Broker Recommendations**: Suggests suitable brokers based on user's portfolio.
- **Affiliate Link Tracking**: Tracks clicks on affiliate links for analytics.
- **Admin Dashboard**: A secure area for administrators to view performance statistics.

### Data & Information
- **Comprehensive ETF Database**: 80+ ETFs with detailed metadata from a local CSV.
- **Live Data Integration**: Real-time market data from Yahoo Finance.
- **Configurable Risk-Free Rate**: Adjustable rate for financial calculations.

---

## 🛠 Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **Python 3.9+**: Core programming language
- **Pydantic**: Data validation and settings management
- **uvicorn**: ASGI server for production

### Financial Analysis
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation and analysis
- **SciPy**: Scientific computing and optimization
- **yfinance**: Yahoo Finance data retrieval

### Frontend
- **Bootstrap 5.3**: Responsive UI framework
- **Plotly.js 2.32**: Interactive data visualization
- **Vanilla JavaScript (ES6 modules)**: Modular client-side logic

### Database & Security
- **SQLAlchemy 2.0**: ORM for database interaction
- **Firebase Admin SDK**: Backend authentication for Google OAuth
- **JWT (python-jose)**: Secure API authentication tokens
- **bcrypt**: Password hashing

### Infrastructure & Others
- **Google Cloud Platform**: Recommended for deployment
- **slowapi**: Rate limiting for API endpoints
- **python-dotenv**: Environment configuration management

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/etf-portfolio-api.git
   cd etf-portfolio-api
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   1. `.env.example` をコピーして `.env` を作成:
      ```bash
      cp .env.example .env
      ```

   2. `.env` ファイルを編集して実際の値を設定:
      ```bash
      nano .env
      ```

   3. **重要**: `.env` ファイルは絶対にGitにコミットしないでください。

   #### 必須の環境変数

   - `SECRET_KEY`: JWT署名用のシークレットキー（最低32文字のランダムな文字列）
     ```bash
     # 生成方法
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```

   - `DATABASE_URL`: データベース接続URL
     - 開発環境: `sqlite:///./data/affiliate.db`
     - 本番環境: PostgreSQL等の接続文字列


5. **Run the application**
   ```bash
   # Recommended method (includes web UI)
   python main.py

   # Alternative method (API only)
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the application**
   - **Web Interface**: http://localhost:8000
   - **Interactive API Docs**: http://localhost:8000/docs
   - **Alternative API Docs**: http://localhost:8000/redoc

---

## 📁 Project Structure

```
etf-portfolio-api/
├── app/
│   ├── api/                    # API endpoint routers
│   │   ├── admin.py           # Admin dashboard endpoints
│   │   ├── affiliate.py       # Affiliate broker and tracking endpoints
│   │   ├── analysis.py        # Financial analysis endpoints
│   │   ├── auth.py            # User authentication endpoints
│   │   ├── etf.py             # ETF information endpoints
│   │   ├── portfolio.py       # Portfolio optimization endpoints
│   │   └── simulation.py      # Financial simulation endpoints
│   ├── db/
│   │   └── database.py        # SQLAlchemy database setup
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py            # User model
│   │   └── affiliate.py       # AffiliateBroker and AffiliateClick models
│   ├── services/               # Service layer (business logic)
│   │   ├── auth_service.py    # Handles user creation and authentication
│   │   ├── data_service.py    # Data fetching (yfinance) and caching
│   │   ├── etf_service.py     # ETF information management
│   │   ├── optimization_service.py  # Portfolio optimization logic
│   │   └── simulation_service.py    # Simulation logic
│   ├── utils/                  # Utility functions
│   │   ├── cache.py           # Thread-safe caching
│   │   ├── calculations.py    # Mathematical utilities
│   │   └── formatters.py      # Data formatting helpers
│   ├── config.py              # Application configuration (Pydantic)
│   ├── constants.py           # Global constants
│   ├── dependencies.py        # FastAPI dependency injection setup
│   ├── schemas.py             # Pydantic data validation models
│   └── main.py                # FastAPI app object and core middleware
├── static/                     # Frontend static files
│   ├── js/                    # (Recommended structure)
│   │   ├── admin-dashboard.js # Admin dashboard logic
│   │   ├── api.js             # API communication layer
│   │   ├── auth.js            # Authentication and Firebase logic
│   │   ├── brokers.js         # Broker comparison page logic
│   │   ├── main.js            # Main application logic
│   │   ├── theme.js           # Dark/light theme switching
│   │   └── ui.js              # DOM manipulation and UI updates
│   └── ...
├── templates/                  # Jinja2 HTML templates
│   ├── admin/
│   │   └── affiliate_dashboard.html
│   ├── blog/
│   │   └── ...
│   ├── brokers.html           # Broker comparison page
│   └── index.html             # Main web interface
├── content/
│   └── blog/                  # Markdown files for the blog
├── scripts/
│   ├── build_blog.py          # Script to generate static blog pages
│   └── seed_brokers.py        # Script to seed initial broker data
├── main.py                    # Application entry point (runs uvicorn)
├── etf_list.csv               # ETF definitions database
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 📡 API Endpoints

All endpoints are prefixed with `/api`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user. |
| POST | `/token` | Authenticate with username/password to get a JWT token. |
| POST | `/token/google` | Authenticate with a Google ID token to get a JWT token. |

### Portfolio Optimization

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/portfolio/efficient_frontier` | Calculate efficient frontier for a set of tickers. |
| POST | `/portfolio/custom_metrics` | Analyze a portfolio with custom weights. |
| POST | `/portfolio/optimize_by_return` | Optimize a portfolio for a target return. |
| POST | `/portfolio/optimize_by_risk` | Optimize a portfolio for a target risk. |

### Simulations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulation/monte_carlo` | Run a Monte Carlo simulation on a portfolio. |
| POST | `/simulation/historical_dca` | Backtest a historical Dollar-Cost Averaging strategy. |
| POST | `/simulation/future_dca` | Project future DCA results with probabilistic scenarios. |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analysis/historical_performance` | Get cumulative historical returns for selected tickers. |
| POST | `/analysis/correlation_matrix` | Calculate the correlation matrix for selected tickers. |
| POST | `/analysis/csv` | Analyze historical data from an uploaded CSV file. |

### ETF Information

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/etfs/list` | Get all available ETF definitions. |
| GET | `/etfs/details/{ticker}` | Get detailed information for a specific ETF. |
| GET | `/etfs/risk_free_rate` | Get the configured risk-free rate. |

### Affiliate

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/brokers` | Get a list of affiliate brokers, filterable by region. |
| GET | `/brokers/recommend` | Get broker recommendations based on region and ETFs. |
| POST | `/brokers/track-click` | Track a click on an affiliate link. |

### Admin (Requires Admin Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/affiliate/stats` | Get overall affiliate performance statistics. |
| GET | `/admin/affiliate/top-performing` | Get top-performing brokers by a specific metric. |
| POST | `/admin/affiliate/conversions` | Manually record an affiliate conversion. |

---

## 🌐 Web Interface

### Main Features

The web interface (`/`) provides a comprehensive dashboard with:

1. **ETF Selection Panel** (Left Sidebar)
   - Search functionality
   - Multiple filter options (asset class, region, style, size, sector, theme)
   - Select/deselect all buttons
   - Hover tooltips with detailed ETF information

2. **User Authentication & Portfolio Management**
   - Username/password registration and login
   - Google OAuth integration
   - Save/load/delete portfolio configurations
   - JWT-based secure session management

3. **Analysis Tabs**
   - **Risk-Return Map**: Interactive efficient frontier visualization
   - **Custom Portfolio**: Create portfolios with custom weights using sliders
   - **Advanced Tools**: Access to optimization, simulations, and analysis features

4. **Advanced Tools (Accordion)**
   - Target Optimization (by return or risk)
   - Correlation Matrix heatmap
   - Historical Performance charts
   - Monte Carlo Simulation
   - Dollar-Cost Averaging (DCA) Simulation
   - CSV File Analysis

5. **Theme Support**
   - Dark/light mode toggle
   - Persistent theme selection
   - Plotly charts automatically adapt to theme

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root by copying `.env.example`. This file is used to store sensitive keys and application-specific settings.

```env
# Database
DATABASE_URL=sqlite:///./data/affiliate.db

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
RISK_FREE_RATE=0.02
CACHE_TTL_SECONDS=3600

# CORS Settings (comma-separated for multiple origins)
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Google Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Affiliate URLs (replace with actual URLs once approved)
AFFILIATE_IBKR_URL=https://ibkr.com/referral/placeholder
# ... and other broker URLs
```

### ETF Database

The `etf_list.csv` file contains ETF metadata. To add new ETFs, simply append rows to this file with the required columns (`ticker`, `name`, `asset_class`, `region`, etc.).

---

## 💻 Development

### Setting Up Development Environment

1. **Install all dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run in development mode with auto-reload**
   ```bash
   python main.py
   # or
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Code formatting** (recommended)
   ```bash
   black app/ --line-length 100
   ruff check app/
   ```

### Architecture Overview

The application follows a **layered architecture**:

```
Web UI (HTML/JS/Bootstrap)
         ↓
API Layer (FastAPI routes)
         ↓
Service Layer (Business logic)
         ↓
Model Layer (Calculations)
         ↓
Data Layer (yfinance, cache, database)
```

**Key Design Principles:**
- **Dependency Injection**: Services injected via FastAPI's `Depends()`
- **Single Responsibility**: Each layer has a clear purpose
- **Type Safety**: Pydantic models throughout
- **Caching**: Automatic caching of expensive operations
- **Thread Safety**: Thread-safe cache implementation
- **Modular Frontend**: ES6 modules for clean separation of concerns

### Adding New Features

**Backend (New API Endpoint):**
```python
# In app/api/your_module.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/your-endpoint")
async def your_function(data: YourSchema):
    # Your logic here
    return {"result": "data"}
```

**Frontend (New UI Feature):**
```javascript
// In static/main.js or appropriate module
document.getElementById('your-button').addEventListener('click', async () => {
    const result = await api.yourApiFunction(params);
    ui.displayYourResult(result);
});
```

---

## 🧪 Testing

### Manual Testing

Use the **interactive web interface** for comprehensive testing:

1. Open http://localhost:8000
2. Select multiple ETFs
3. Generate Risk-Return Map
4. Test Custom Portfolio creation
5. Explore Advanced Tools (correlation, Monte Carlo, DCA)
6. Test authentication (register, login, save portfolio)

### API Testing

Use the built-in FastAPI documentation:

```bash
# Access interactive API docs
open http://localhost:8000/docs
```

Test endpoints directly in the Swagger UI or use curl/Postman.

### Integration Testing

```bash
# Run integration tests (if test suite exists)
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_portfolio.py -v
```

---

## 🚢 Deployment

### Google Cloud Platform (App Engine)

1. **Create `app.yaml`**
   ```yaml
   runtime: python39
   entrypoint: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

   env_variables:
     RISK_FREE_RATE: "0.02"
     CACHE_TTL_SECONDS: "3600"

   handlers:
   - url: /static
     static_dir: static
   - url: /.*
     script: auto
   ```

2. **Install gunicorn**
   ```bash
   pip install gunicorn
   pip freeze > requirements.txt
   ```

3. **Deploy**
   ```bash
   gcloud app deploy
   ```

### Google Cloud Run (Alternative)

1. **Create Dockerfile** (you'll need to create this)
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 8080

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Build and deploy**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/etf-api
   gcloud run deploy etf-api --image gcr.io/PROJECT_ID/etf-api --platform managed
   ```

### Environment-Specific Configuration

- **Development**: Use `.env` file
- **Production**: Use Google Cloud Secret Manager or environment variables
- **Firebase**: Update Firebase configuration in `static/auth.js` with production values

### Production Checklist

- [ ] Set `reload=False` in uvicorn
- [ ] Use production database
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up monitoring and logging
- [ ] Enable rate limiting
- [ ] Secure Firebase API keys
- [ ] Use Secret Manager for sensitive data
- [ ] Set up automated backups
- [ ] Configure proper error handling

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Coding Standards

- Follow PEP 8 style guidelines (backend)
- Use ESLint rules for JavaScript (frontend)
- Add type hints to all Python functions
- Write docstrings in Google format
- Ensure all tests pass
- Update documentation as needed

---

## ⚠️ Disclaimer / 免責事項

### English

**IMPORTANT: This application is provided for educational and informational purposes only.**

- **Not Financial Advice**: The information, analysis, and tools provided by this application do NOT constitute financial, investment, trading, or any other type of professional advice.
- **No Investment Recommendations**: This application does not provide personalized investment recommendations. Any portfolio suggestions or optimizations are based solely on historical data and mathematical models.
- **Past Performance**: Historical performance data and simulations do not guarantee future results. Investment returns can be volatile and unpredictable.
- **Use at Your Own Risk**: You acknowledge that any investment decisions made based on information from this application are made at your sole discretion and risk.
- **No Liability**: The developers, contributors, and operators of this application shall not be liable for any direct, indirect, incidental, special, consequential, or exemplary damages, including but not limited to:
  - Loss of profits
  - Loss of capital
  - Trading losses
  - Opportunity costs
  - Data inaccuracies
  - System errors or downtime
- **Data Accuracy**: While we strive to provide accurate data through Yahoo Finance integration, we cannot guarantee the accuracy, completeness, or timeliness of any information.
- **Consult Professionals**: Before making any investment decisions, you should consult with qualified financial advisors, tax professionals, and legal counsel.
- **Regulatory Compliance**: Users are responsible for ensuring their use of this application complies with all applicable laws and regulations in their jurisdiction.

**BY USING THIS APPLICATION, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE TO THIS DISCLAIMER.**

---

### 日本語

**重要: このアプリケーションは教育および情報提供のみを目的として提供されています。**

- **金融アドバイスではありません**: 本アプリケーションが提供する情報、分析、ツールは、金融、投資、取引、その他いかなる種類の専門的アドバイスも構成するものではありません。
- **投資推奨ではありません**: 本アプリケーションは個別の投資推奨を提供するものではありません。ポートフォリオの提案や最適化は、過去のデータと数学的モデルのみに基づいています。
- **過去の実績**: 過去のパフォーマンスデータやシミュレーションは、将来の結果を保証するものではありません。投資リターンは変動性が高く、予測不可能です。
- **自己責任での使用**: 本アプリケーションからの情報に基づいて行われる投資判断は、すべてあなた自身の裁量とリスクで行われることを承認します。
- **免責事項**: 本アプリケーションの開発者、貢献者、運営者は、以下を含むがこれに限定されない、直接的、間接的、偶発的、特別、結果的、または懲罰的損害について一切の責任を負いません:
  - 利益の損失
  - 資本の損失
  - 取引損失
  - 機会損失
  - データの不正確性
  - システムエラーまたはダウンタイム
- **データの正確性**: Yahoo Financeとの連携により正確なデータを提供するよう努めていますが、情報の正確性、完全性、適時性を保証することはできません。
- **専門家への相談**: 投資判断を行う前に、資格を持つファイナンシャルアドバイザー、税理士、法律顧問に相談してください。
- **規制遵守**: ユーザーは、本アプリケーションの使用が自身の管轄区域におけるすべての適用法令に準拠していることを確認する責任を負います。

**本アプリケーションを使用することにより、あなたはこの免責事項を読み、理解し、同意したことを認めます。**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note**: The MIT License applies to the software code itself. The disclaimer above applies to the use of the application and any financial analysis or recommendations it may provide.

---

## 🙏 Acknowledgments

- **Yahoo Finance** for providing financial data via yfinance
- **FastAPI** for the excellent web framework
- **Bootstrap** for the responsive UI framework
- **Plotly** for interactive visualizations
- **Firebase** for authentication services
- **Modern Portfolio Theory** for the mathematical foundation

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the integration test plan

Project Link: [https://github.com/yourusername/etf-portfolio-api](https://github.com/yourusername/etf-portfolio-api)

---

## 📈 Performance

- **Cache Hit Rate**: ~90% for repeated queries
- **Response Time**: 
  - Cached data: <100ms
  - First request: 2-7 seconds (data fetching from Yahoo Finance)
  - Efficient Frontier calculation: 1-3 seconds
- **Concurrent Users**: Supports multiple simultaneous users
- **Rate Limiting**: 60 requests/minute per IP (configurable)
- **Database**: Peewee ORM with SQLite (development) or PostgreSQL (production)

---

## 🔒 Security

- **Authentication**: JWT-based with bcrypt password hashing
- **Rate Limiting**: Implemented via slowapi
- **Input Validation**: Pydantic models throughout
- **CORS Configuration**: Configurable allowed origins
- **Secret Management**: Google Cloud Secret Manager (production)
- **SQL Injection Protection**: Peewee ORM with parameterized queries
- **XSS Protection**: Content Security Policy headers

---

## 🗺️ Roadmap

Future enhancements:

- [ ] Docker support with multi-stage builds
- [ ] Automated testing suite (unit + integration)
- [ ] WebSocket support for real-time updates
- [ ] Additional optimization algorithms (Black-Litterman, Risk Parity)
- [ ] Machine learning predictions
- [ ] Enhanced backtesting features
- [ ] Multi-currency support
- [ ] Email notifications for portfolio alerts
- [ ] Export reports to PDF
- [ ] Mobile app (React Native)

---

**Built with ❤️ using FastAPI, Bootstrap, and Modern Portfolio Theory**