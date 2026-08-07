# Contributing

Thanks for your interest in improving Bitcoin vs Stocks!

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
cp .env.example .env   # set SECRET_KEY to any random string
uv run python manage.py migrate
uv run python manage.py runserver
```

## Before opening a PR

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

All three must pass — CI runs the same checks.

## Guidelines

- Keep changes small and focused; one topic per PR.
- Add or update tests for behavior changes. Tests must not hit the network
  (Yahoo Finance is mocked — see `dca/tests/conftest.py`).
- The yfinance fetch code in `dca/utils.py` contains deliberate fallback paths
  because Yahoo's API is unofficial and flaky — don't simplify them away.
- For larger changes, open an issue first to discuss the approach.
