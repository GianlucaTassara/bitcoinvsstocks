from urllib.parse import urlencode

import pytest
from rest_framework.test import APIClient

from dca.constants import BTC_TICKER
from dca.utils import UpstreamDataError

VALID = {"mode": "simple", "amount": "100", "frequency": "w", "years": "2", "ticker": "AAPL"}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def seeded(seed_prices):
    seed_prices(BTC_TICKER)
    seed_prices("AAPL")


def test_simple_mode_shape(client, seeded):
    response = client.get("/", VALID)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"Bitcoin", "Stocks"}
    assert data["Bitcoin"]["ticker"] == BTC_TICKER
    assert data["Stocks"]["ticker"] == "AAPL"
    assert data["Bitcoin"]["btc_amount"] is not None
    assert data["Bitcoin"]["past_years"] == 2


def test_table_mode_returns_one_row_per_year(client, seeded):
    response = client.get("/", {**VALID, "mode": "table", "years": "3"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["Bitcoin"]) == 3
    assert len(data["Stocks"]) == 3
    assert [row["past_years"] for row in data["Bitcoin"]] == [1, 2, 3]


def test_mode_is_case_insensitive(client, seeded):
    response = client.get("/", {**VALID, "mode": "Simple"})
    assert response.status_code == 200


def test_missing_params_rejected(client, db):
    response = client.get("/", {"mode": "simple"})
    assert response.status_code == 400
    errors = response.json()
    assert {"amount", "frequency", "years", "ticker"} <= set(errors)


def test_invalid_mode_rejected(client, db):
    response = client.get("/", {**VALID, "mode": "chart"})
    assert response.status_code == 400


def test_upstream_failure_returns_502(client, db, monkeypatch):
    def boom(ticker):
        raise UpstreamDataError(f"Unable to extract price for {ticker} ticker")

    monkeypatch.setattr("dca.views.update_current_price", boom)
    response = client.get("/", VALID)
    assert response.status_code == 502
    # The raw upstream error is logged, not leaked to the client.
    assert response.json() == {"error": "Unknown ticker or price data temporarily unavailable"}


def test_insufficient_history_returns_400(client, seed_prices):
    seed_prices(BTC_TICKER, days=30)
    seed_prices("AAPL", days=30)
    response = client.get("/", VALID)
    assert response.status_code == 400
    assert "error" in response.json()


def test_post_with_query_params_still_works(client, seeded):
    response = client.post(f"/?{urlencode(VALID)}")
    assert response.status_code == 200
    assert set(response.json()) == {"Bitcoin", "Stocks"}
