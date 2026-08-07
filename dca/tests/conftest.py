from datetime import date, timedelta
from unittest import mock

import pandas as pd
import pytest

from dca.models import CurrentPrice, HistoryLastUpdated, PriceHistory


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail loudly if any test reaches for Yahoo Finance."""
    monkeypatch.setattr(
        "dca.utils.yf.Ticker",
        mock.Mock(side_effect=AssertionError("Test attempted network access via yfinance")),
    )


@pytest.fixture
def fake_yahoo(monkeypatch):
    """Replace yfinance's Ticker with a stub returning canned data.

    Overrides the autouse no_network guard for tests that exercise
    the fetch path itself.
    """

    def _install(info=None, close_prices=None, history_raises=False):
        stub = mock.Mock()
        stub.info = info if info is not None else {}
        if history_raises:
            stub.history.side_effect = RuntimeError("yahoo is down")
        else:
            prices = close_prices if close_prices is not None else []
            index = pd.date_range(end=pd.Timestamp("2026-01-30"), periods=len(prices), freq="D")
            stub.history.return_value = pd.DataFrame({"Close": prices}, index=index)
        monkeypatch.setattr("dca.utils.yf.Ticker", lambda ticker: stub)
        return stub

    return _install


@pytest.fixture
def seed_prices(db):
    """Seed fresh cache rows for a ticker so no fetch is triggered."""

    def _seed(ticker, days=1500, price=100.0, current=200.0):
        today = date.today()
        PriceHistory.objects.bulk_create(
            PriceHistory(ticker=ticker, price=price, currency="USD", date=today - timedelta(days=i))
            for i in range(days)
        )
        CurrentPrice.objects.create(ticker=ticker, price=current, update_count=1)
        HistoryLastUpdated.objects.create(ticker=ticker, update_count=1)

    return _seed
