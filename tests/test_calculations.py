
# Mock google.cloud.secretmanager before app is imported
from unittest import mock

import numpy as np
import pandas as pd
import pytest

with mock.patch("google.cloud.secretmanager.SecretManagerServiceClient"):
    from main import (
        RISK_FREE_RATE,
        portfolio_return,
        portfolio_sharpe_ratio,
        portfolio_volatility,
    )

@pytest.fixture
def mock_data():
    """Provides mock data for testing calculation functions."""
    # Using a small, predictable dataset
    avg_returns = pd.Series([0.1, 0.2, 0.15], index=["ETF1", "ETF2", "ETF3"])

    # Simple covariance matrix
    cov_matrix = pd.DataFrame([
        [0.10, 0.02, 0.01],
        [0.02, 0.15, 0.03],
        [0.01, 0.03, 0.12]
    ], index=["ETF1", "ETF2", "ETF3"], columns=["ETF1", "ETF2", "ETF3"])

    # Equal weights
    weights = np.array([1/3, 1/3, 1/3])

    return {
        "avg_returns": avg_returns,
        "cov_matrix": cov_matrix,
        "weights": weights
    }

def test_portfolio_return(mock_data):
    """Tests the portfolio_return function."""
    p_return = portfolio_return(mock_data["weights"], mock_data["avg_returns"])

    # Expected: (0.1 + 0.2 + 0.15) / 3 = 0.45 / 3 = 0.15
    assert np.isclose(p_return, 0.15)

def test_portfolio_volatility(mock_data):
    """Tests the portfolio_volatility function."""
    p_volatility = portfolio_volatility(mock_data["weights"], mock_data["cov_matrix"])

    # Expected calculation:
    # w.T * C * w =
    # [1/3, 1/3, 1/3] * [[0.10, 0.02, 0.01], [0.02, 0.15, 0.03],
    #                    [0.01, 0.03, 0.12]] * [1/3, 1/3, 1/3]^T
    # = [1/3, 1/3, 1/3] * [0.13/3, 0.20/3, 0.16/3]^T
    # = (0.13 + 0.20 + 0.16) / 9 = 0.49 / 9 = 0.05444...
    # sqrt(0.05444...) = 0.2333...
    expected_volatility = np.sqrt(0.05444444444)
    assert np.isclose(p_volatility, expected_volatility)

def test_portfolio_sharpe_ratio(mock_data):
    """Tests the portfolio_sharpe_ratio function."""
    p_return = portfolio_return(mock_data["weights"], mock_data["avg_returns"])
    p_volatility = portfolio_volatility(mock_data["weights"], mock_data["cov_matrix"])

    sharpe_ratio = portfolio_sharpe_ratio(
        mock_data["weights"], mock_data["avg_returns"],
        mock_data["cov_matrix"], RISK_FREE_RATE
    )

    expected_sharpe = (p_return - RISK_FREE_RATE) / p_volatility

    assert np.isclose(sharpe_ratio, expected_sharpe)

def test_portfolio_sharpe_ratio_zero_volatility(mock_data):
    """Tests that sharpe ratio handles zero volatility."""
    zero_cov_matrix = pd.DataFrame(np.zeros((3,3)), columns=["ETF1", "ETF2", "ETF3"])
    sharpe_ratio = portfolio_sharpe_ratio(
        mock_data["weights"], mock_data["avg_returns"],
        zero_cov_matrix, RISK_FREE_RATE
    )

    # Should return -inf as per the function's logic to avoid division by zero
    assert sharpe_ratio == -np.inf
