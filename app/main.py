from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import analysis, etf, portfolio, simulation
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager to handle startup and shutdown events.
    """
    # Logic on startup (e.g., connecting to DB, loading models)
    print("--- Application starting up ---")
    yield
    # Logic on shutdown
    print("--- Application shutting down ---")


# Initialize FastAPI App
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiter ---
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_per_minute]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Static Files ---
# Note: The root `main.py` will mount this. If running `app.main` directly, adjust paths.
# We will handle this in the new root `main.py`.


# --- API Routers ---
app.include_router(etf.router)
app.include_router(portfolio.router)
app.include_router(simulation.router)
app.include_router(analysis.router)

# The root path can still serve the main page, but this logic belongs in the root main.py
# that serves the entire application, not in the app module itself.
# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the ETF Analysis API"}
