from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.main import app
from app.models.affiliate import AffiliateBroker, AffiliateClick


@pytest.fixture(name="session")
def session_fixture():
    with patch("app.db.database.SessionLocal", new_callable=MagicMock) as mock_session_local:
        session = mock_session_local.return_value
        app.dependency_overrides[get_db] = lambda: session
        yield session
        app.dependency_overrides.clear()

client = TestClient(app)

def create_test_broker(id, name, region, rating, is_active=True, best_for=""):
    """Creates an AffiliateBroker instance for testing."""
    now = datetime.now(timezone.utc)
    return AffiliateBroker(
        id=id, broker_name=name, display_name=name, region=region,
        is_active=is_active, affiliate_url=f"http://{name.lower().replace(' ', '')}.com",
        logo_url=f"http://{name.lower().replace(' ', '')}.com/logo.png",
        rating=rating, best_for=best_for, pros='[]', commission_rate=0.0,
        commission_type="percent", description="A test broker.",
        created_at=now, updated_at=now,
    )

def test_get_brokers(session: MagicMock):
    """Test the GET /api/brokers endpoint with corrected mocking."""
    broker1 = create_test_broker(1, "Broker 1", "US", 4.5, True)
    broker2 = create_test_broker(2, "Broker 2", "JP", 4.0, True)
    broker3 = create_test_broker(3, "Broker 3", "US", 3.0, False)

    # Test case: default (active_only=true)
    session.reset_mock()
    query_chain = session.query.return_value.filter.return_value
    query_chain.all.return_value = [broker1, broker2]
    response = client.get("/api/brokers")
    assert response.status_code == 200
    assert len(response.json()) == 2
    query_chain.all.assert_called_once()
    session.query.return_value.filter.assert_called_once()

    # Test case: active_only=false
    session.reset_mock()
    query_chain = session.query.return_value
    query_chain.all.return_value = [broker1, broker2, broker3]
    response = client.get("/api/brokers?active_only=false")
    assert response.status_code == 200
    assert len(response.json()) == 3
    query_chain.all.assert_called_once()
    session.query.return_value.filter.assert_not_called()

def test_get_broker_recommendations(session: MagicMock):
    """Test the GET /api/brokers/recommend endpoint with corrected mocking."""
    broker1 = create_test_broker(1, "Broker 1", "US", 5.0, True, "Beginners")
    broker2 = create_test_broker(2, "Broker 2", "US", 4.0, True, "Experienced")

    # Test case 1: Specific recommendation found
    session.reset_mock()
    (session.query.return_value.filter.return_value.filter.return_value
     .order_by.return_value.limit.return_value.all.return_value) = [broker1]
    response = client.get("/api/brokers/recommend?region=US&user_level=Beginners")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Test case 2: Fallback to general recommendation
    session.reset_mock()
    all_mock = MagicMock(side_effect=[
        [],
        [broker1, broker2]
    ])
    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all = all_mock
    session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all = all_mock
    
    response = client.get("/api/brokers/recommend?region=US&user_level=Advanced")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1

    # Test case 3: No brokers found at all
    session.reset_mock()
    all_mock_empty = MagicMock(side_effect=[[], []])
    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all = all_mock_empty
    session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all = all_mock_empty
    response = client.get("/api/brokers/recommend?region=CA")
    assert response.status_code == 404

@patch("app.api.affiliate.datetime", MagicMock(now=MagicMock(return_value=datetime(2023, 1, 1, tzinfo=timezone.utc))))
def test_track_affiliate_click(session: MagicMock):
    """Test the POST /api/brokers/track-click endpoint with corrected mocking."""
    broker = create_test_broker(1, "Test Broker", "US", 5.0)
    session.query.return_value.filter.return_value.first.return_value = broker
    
    with patch("app.api.affiliate.AffiliateClick") as MockClick:
        mock_instance = MagicMock()
        mock_instance.id = 123
        MockClick.return_value = mock_instance

        request_body = {"broker_id": 1, "placement": "test_page"}
        response = client.post("/api/brokers/track-click", json=request_body)
        assert response.status_code == 200
        MockClick.assert_called_once_with(
            broker_id=1, user_id=None, session_id=ANY, clicked_at=ANY,
            ip_address=ANY, user_agent=ANY, referrer=ANY,
            placement="test_page", portfolio_data=None, converted=False
        )
        session.add.assert_called_once_with(mock_instance)
        session.commit.assert_called_once()

    session.reset_mock()
    session.query.return_value.filter.return_value.first.return_value = None
    request_body = {"broker_id": 999, "placement": "not_found_test"}
    response = client.post("/api/brokers/track-click", json=request_body)
    assert response.status_code == 404
