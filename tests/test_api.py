
from unittest import mock

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# Mock google.cloud.secretmanager before app is imported
with mock.patch(
    "google.cloud.secretmanager.SecretManagerServiceClient"
) as MockSecretManagerServiceClient:
    (
        MockSecretManagerServiceClient.return_value.access_secret_version.return_value.payload.data.decode.return_value
    ) = "dummy_secret_key"
    from main import app

client = TestClient(app)

@mock.patch("yfinance.download")
def test_get_efficient_frontier(mock_yf_download):
    """Tests the /efficient_frontier endpoint."""
    # 1. Create mock data that yfinance.download would return
    mock_data = {
        ("VTI", "Close"): [150.0, 151.0, 150.5],
        ("AGG", "Close"): [110.0, 110.2, 110.1]
    }
    mock_df = pd.DataFrame(mock_data)
    mock_df.index = pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"])
    mock_df.columns.names = ["Ticker", "Price"] # Name the levels
    mock_yf_download.return_value = mock_df
    # 2. Call the API endpoint
    response = client.get("/efficient_frontier?tickers=VTI&tickers=AGG&period=1y")

    # 3. Assert the response
    assert response.status_code == 200
    data = response.json()

    assert "frontier_points" in data
    assert "tangency_portfolio" in data
    assert "tangency_portfolio_weights" in data

    assert isinstance(data["frontier_points"], list)
    # With only 3 data points, optimization might fail, but the structure
    # should be correct
    # If it succeeds, the list won't be empty.
    if data["frontier_points"]:
        assert "Risk" in data["frontier_points"][0]
        assert "Return" in data["frontier_points"][0]

    # Check tangency portfolio structure if it exists
    if data["tangency_portfolio"]:
        assert "Risk" in data["tangency_portfolio"]
        assert "Return" in data["tangency_portfolio"]
        assert "SharpeRatio" in data["tangency_portfolio"]

    # Check weights structure
    assert isinstance(data["tangency_portfolio_weights"], dict)

def test_get_efficient_frontier_default_tickers():
    """Tests the /efficient_frontier endpoint when it uses the default tickers."""
    # This test is slow because it calculates the full frontier
    response = client.get("/efficient_frontier")
    assert response.status_code == 200
    data = response.json()
    assert data["frontier_points"]  # Check that the list is not empty
    assert data["tangency_portfolio"] is not None
    assert data["tangency_portfolio_weights"]


@mock.patch("yfinance.download")
def test_calculate_custom_portfolio(mock_yf_download):
    """Tests the /custom_portfolio_data endpoint."""
    # 1. Mock yfinance
    mock_data = {
        ("VTI", "Close"): [150.0, 151.0, 150.5, 152.0],
        ("AGG", "Close"): [110.0, 110.2, 110.1, 110.5]
    }
    mock_df = pd.DataFrame(mock_data)
    mock_df.index = pd.to_datetime([
        "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"
    ])
    mock_df.columns.names = ["Ticker", "Price"]
    mock_yf_download.return_value = mock_df

    # 2. Define request body
    request_data = {
        "tickers": ["VTI", "AGG"],
        "weights": {"VTI": 0.6, "AGG": 0.4},
        "period": "1y"
    }

    # 3. Call API
    response = client.post("/custom_portfolio_data", json=request_data)

    # 4. Assert response
    assert response.status_code == 200
    data = response.json()
    assert "Risk" in data
    assert "Return" in data
    assert isinstance(data["Risk"], float)
    assert isinstance(data["Return"], float)


@mock.patch("yfinance.download")
def test_optimize_by_return(mock_yf_download):
    """Tests the /optimize_by_return endpoint."""
    # 1. Mock yfinance
    mock_data = {
        ("VTI", "Close"): [150.0, 151.0, 150.5, 152.0, 153.0],
        ("BND", "Close"): [110.0, 110.2, 110.1, 110.5, 110.3]
    }
    mock_df = pd.DataFrame(mock_data)
    mock_df.index = pd.to_datetime([
        "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"
    ])
    mock_df.columns.names = ["Ticker", "Price"]
    mock_yf_download.return_value = mock_df

    # 2. Define request body
    request_data = {
        "tickers": ["VTI", "BND"],
        "target_value": 0.50, # Target 50% return
        "period": "1y"
    }

    # 3. Call API
    response = client.post("/optimize_by_return", json=request_data)

    # 4. Assert response
    assert response.status_code == 200
    data = response.json()
    assert "Risk" in data
    assert "Return" in data
    assert "weights" in data
    assert "VTI" in data["weights"]
    assert "BND" in data["weights"]
    assert np.isclose(sum(data["weights"].values()), 1.0)


@mock.patch("yfinance.download")
def test_get_historical_performance(mock_yf_download):
    """Tests the /historical_performance endpoint."""
    # 1. Mock yfinance
    mock_data = {
        ("VTI", "Close"): [150.0, 151.0, 150.5, 152.0],
    }
    mock_df = pd.DataFrame(mock_data)
    mock_df.index = pd.to_datetime([
        "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"
    ])
    mock_df.columns.names = ["Ticker", "Price"]
    mock_yf_download.return_value = mock_df

    # 2. Define request body
    request_data = {
        "tickers": ["VTI"],
        "period": "1mo"
    }

    # 3. Call API
    response = client.post("/historical_performance", json=request_data)

    # 4. Assert response
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert "cumulative_returns" in data
    assert "VTI" in data["cumulative_returns"]
    assert len(data["dates"]) == len(data["cumulative_returns"]["VTI"])



