from datetime import date, timedelta

import pytest
from django.utils import timezone

from dca.constants import BTC_TICKER
from dca.models import CurrentPrice, PriceHistory
from dca.utils import (
    InsufficientHistoryError,
    UpstreamDataError,
    calculate_savings,
    get_price_from_yahoo,
    update_current_price,
    update_price_history,
)


class TestCalculateSavings:
    def test_stock_weekly_constant_price(self):
        # Constant $100 history, $200 current price: every $100 buys one
        # "unit", so profit is exactly 100% regardless of frequency.
        history = [100.0] * 800
        result = calculate_savings("w", 100, 1, history, 200.0, "AAPL")
        assert result.invested == 5200  # 52 weekly buys
        assert result.savings == 10400
        assert result.profit == pytest.approx(100.0)
        assert result.btc_amount is None
        assert result.past_years == 1

    def test_btc_weekly_uses_seven_day_stride(self):
        # 52 iterations * 7-day stride needs 364 entries; 363 is one short.
        result = calculate_savings("w", 100, 1, [100.0] * 364, 200.0, BTC_TICKER)
        assert result.invested == 5200
        assert result.btc_amount == pytest.approx(52.0)
        with pytest.raises(InsufficientHistoryError):
            calculate_savings("w", 100, 1, [100.0] * 363, 200.0, BTC_TICKER)

    @pytest.mark.parametrize(
        "frequency,buys_per_year,stock_stride",
        [("d", 364, 1), ("w", 52, 5), ("b", 26, 10), ("m", 12, 21)],
    )
    def test_stock_frequencies(self, frequency, buys_per_year, stock_stride):
        history = [100.0] * (buys_per_year * stock_stride)
        result = calculate_savings(frequency, 10, 1, history, 100.0, "AAPL")
        assert result.invested == 10 * buys_per_year
        assert result.profit == pytest.approx(0.0)

    def test_history_too_short_raises(self):
        with pytest.raises(InsufficientHistoryError):
            calculate_savings("m", 100, 10, [100.0] * 100, 200.0, "AAPL")


class TestCurrentPriceCache:
    def test_fresh_price_served_from_db(self, db):
        # The autouse no_network guard proves no fetch happens here.
        CurrentPrice.objects.create(ticker="AAPL", price=150.5, update_count=1)
        assert update_current_price("AAPL") == 150.5

    def test_stale_price_refetched(self, db, monkeypatch):
        CurrentPrice.objects.create(ticker="AAPL", price=150.5, update_count=1)
        CurrentPrice.objects.update(last_updated=timezone.now() - timedelta(minutes=16))
        monkeypatch.setattr("dca.utils.get_price_from_yahoo", lambda ticker: 123.0)
        assert update_current_price("AAPL") == 123.0
        assert CurrentPrice.objects.get(ticker="AAPL").update_count == 2

    def test_unknown_ticker_fetched_and_stored(self, db, monkeypatch):
        monkeypatch.setattr("dca.utils.get_price_from_yahoo", lambda ticker: 42.0)
        assert update_current_price("MSFT") == 42.0
        assert CurrentPrice.objects.get(ticker="MSFT").update_count == 1


class TestGetPriceFromYahoo:
    def test_uses_info_current_price(self, fake_yahoo):
        fake_yahoo(info={"currentPrice": 42.5})
        assert get_price_from_yahoo("AAPL") == 42.5

    def test_falls_back_to_last_close(self, fake_yahoo):
        # Missing currentPrice triggers the history fallback; regression
        # test for positional indexing that pandas 3 no longer allows.
        fake_yahoo(info={}, close_prices=[10.0, 20.0, 30.0])
        assert get_price_from_yahoo("AAPL") == 30.0

    def test_upstream_failure_raises(self, fake_yahoo):
        fake_yahoo(info={}, history_raises=True)
        with pytest.raises(UpstreamDataError):
            get_price_from_yahoo("NOPE")

    def test_empty_history_raises(self, fake_yahoo):
        fake_yahoo(info={}, close_prices=[])
        with pytest.raises(UpstreamDataError):
            get_price_from_yahoo("NOPE")


class TestPriceHistoryCache:
    def test_new_ticker_fetches_and_stores(self, db, fake_yahoo):
        fake_yahoo(close_prices=[10.0, 11.0, 12.0])
        history = update_price_history("AAPL")
        assert history == [10.0, 11.0, 12.0]
        assert PriceHistory.objects.filter(ticker="AAPL").count() == 3

    def test_fresh_history_served_from_db(self, seed_prices):
        # seed_prices creates a fresh HistoryLastUpdated row with
        # update_count=1, so no fetch happens (no_network would fail it).
        seed_prices("AAPL", days=5)
        assert update_price_history("AAPL") == [100.0] * 5

    def test_refresh_overwrites_cached_rows(self, db, fake_yahoo):
        # Yahoo back-adjusts history after splits/dividends, so a refresh
        # must rewrite existing rows, not just insert new dates. Seed rows
        # on a pre-split basis (10x) for the same dates the fetch returns.
        for offset, stale_price in enumerate([100.0, 110.0, 120.0]):
            PriceHistory.objects.create(
                ticker="AAPL",
                price=stale_price,
                currency="USD",
                date=date(2026, 1, 28) + timedelta(days=offset),
            )
        fake_yahoo(close_prices=[10.0, 11.0, 12.0])
        assert update_price_history("AAPL") == [10.0, 11.0, 12.0]
        assert PriceHistory.objects.filter(ticker="AAPL").count() == 3
