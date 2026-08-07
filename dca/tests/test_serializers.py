import pytest

from dca.serializers import DcaRequestSerializer

VALID = {"mode": "simple", "amount": 100, "frequency": "w", "years": 2, "ticker": "AAPL"}


def make(**overrides):
    return DcaRequestSerializer(data={**VALID, **overrides})


def test_valid_request():
    serializer = make()
    assert serializer.is_valid()
    assert serializer.validated_data["mode"] == "simple"


@pytest.mark.parametrize("mode", ["Simple", "TABLE", "table"])
def test_mode_is_case_insensitive(mode):
    serializer = make(mode=mode)
    assert serializer.is_valid()
    assert serializer.validated_data["mode"] == mode.lower()


def test_unknown_mode_rejected():
    serializer = make(mode="chart")
    assert not serializer.is_valid()
    assert "mode" in serializer.errors


@pytest.mark.parametrize("frequency", ["d", "w", "b", "m"])
def test_valid_frequencies(frequency):
    assert make(frequency=frequency).is_valid()


def test_unknown_frequency_rejected():
    assert not make(frequency="y").is_valid()


@pytest.mark.parametrize("years,ok", [(0, False), (1, True), (10, True), (11, False)])
def test_years_bounds(years, ok):
    assert make(years=years).is_valid() is ok


@pytest.mark.parametrize("amount,ok", [(0, False), (1, True), (-5, False)])
def test_amount_bounds(amount, ok):
    assert make(amount=amount).is_valid() is ok


def test_missing_field_rejected():
    data = dict(VALID)
    del data["ticker"]
    serializer = DcaRequestSerializer(data=data)
    assert not serializer.is_valid()
    assert "ticker" in serializer.errors
