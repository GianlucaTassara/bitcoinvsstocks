# Bitcoin vs Stocks API

[![CI](https://github.com/GianlucaTassara/bitcoinvsstocks/actions/workflows/ci.yml/badge.svg)](https://github.com/GianlucaTassara/bitcoinvsstocks/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![Django 5.2](https://img.shields.io/badge/django-5.2-092e20)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small REST API that answers one question: **if you had dollar-cost-averaged into
Bitcoin instead of a stock (or index), how would your savings compare?**

Give it an amount, a frequency, a number of years, and a ticker. It fetches price
history from Yahoo Finance (cached locally in SQLite) and returns what your
investment would be worth today in Bitcoin vs the chosen asset.

This is the backend that powers [bitcoinvsstocks.com](https://bitcoinvsstocks.com).
Interactive API docs are served at [`/docs/`](https://bitcoinvsstocks.com/docs/).

## API

One endpoint:

```
GET /?mode=<mode>&amount=<amount>&frequency=<frequency>&years=<years>&ticker=<ticker>
```

| Parameter   | Type   | Values                                              | Description                                  |
| ----------- | ------ | --------------------------------------------------- | -------------------------------------------- |
| `mode`      | string | `simple`, `table`                                   | One result, or one result per year (1..N)    |
| `amount`    | int    | ≥ 1                                                 | Amount invested per period (USD)             |
| `frequency` | string | `d` (daily), `w` (weekly), `b` (biweekly), `m` (monthly) | How often you invest                    |
| `years`     | int    | 1–10                                                | How many years back the DCA runs             |
| `ticker`    | string | any Yahoo Finance ticker, e.g. `AAPL`, `^GSPC`, `GC=F` | The asset to compare Bitcoin against     |

### Example: simple mode

```bash
curl 'https://api.example.com/?mode=simple&amount=100&frequency=w&years=2&ticker=AAPL'
```

```json
{
  "Bitcoin": {
    "ticker": "BTC-USD",
    "invested": 10400,
    "savings": 18342,
    "profit": "76.37",
    "btc_amount": "0.19",
    "past_years": 2
  },
  "Stocks": {
    "ticker": "AAPL",
    "invested": 10400,
    "savings": 12800,
    "profit": "23.08",
    "past_years": 2
  }
}
```

### Example: table mode

`mode=table` returns the same objects as arrays, one entry per year from 1 to `years` —
useful for charting how the comparison evolves over time.

```bash
curl 'https://api.example.com/?mode=table&amount=100&frequency=m&years=5&ticker=^GSPC'
```

### Errors

| Status | Meaning                                                            |
| ------ | ------------------------------------------------------------------ |
| 400    | Invalid parameters, or not enough price history for the requested years |
| 502    | Yahoo Finance is unavailable or the ticker is unknown              |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (it installs the right Python for you).

```bash
git clone https://github.com/GianlucaTassara/bitcoinvsstocks.git
cd bitcoinvsstocks
uv sync
cp .env.example .env   # fill in SECRET_KEY (any random string works for dev)
uv run python manage.py migrate
uv run python manage.py runserver
```

Then try:

```bash
curl 'http://localhost:8000/?mode=simple&amount=100&frequency=w&years=2&ticker=AAPL'
```

The first request for a ticker fetches all available history from Yahoo Finance and
caches it in SQLite; subsequent requests are fast. Spot prices are cached for
15 minutes, history is refreshed daily.

The daily refresh rewrites the ticker's entire cached series, not just new dates.
This matters because Yahoo serves back-adjusted prices: a stock split or dividend
retroactively changes every historical price, so cached rows must be updated to
stay on the same adjustment basis as recent data. Prices are dividend-adjusted
(total return), which keeps the comparison with Bitcoin fair.

## Running tests

```bash
uv run pytest
uv run ruff check .
```

Tests never hit the network — Yahoo Finance is mocked.

## Deployment

The project deploys on [Railway](https://railway.com) using the Railpack builder —
see [railway.json](railway.json). Any platform that can run
`gunicorn bitcoinvsstocks.wsgi:application` works.

Required environment variables (see [.env.example](.env.example)):

| Variable               | Example                                     |
| ---------------------- | ------------------------------------------- |
| `SECRET_KEY`           | a long random string (required)             |
| `DEBUG`                | `False` (default)                           |
| `ALLOWED_HOSTS`        | `api.bitcoinvsstocks.com,myapp.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | `https://bitcoinvsstocks.com`               |
| `DATABASE_URL`         | optional; defaults to local SQLite          |

Note: on Railway, SQLite lives on an ephemeral filesystem unless you mount a
volume — without one, the price cache resets on each deploy (harmless, just a
cold cache on the first request).

## Notes

- Price data comes from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance),
  which is unofficial and occasionally breaks when Yahoo changes things. The fetch
  code has fallback paths for this — tread carefully when refactoring it.
- The frontend (including its ticker lists) lives in a separate repository.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
