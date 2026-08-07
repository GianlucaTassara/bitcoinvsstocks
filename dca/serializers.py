from rest_framework import serializers


class CaseInsensitiveChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        return super().to_internal_value(str(data).lower())


class SavingsSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=12)
    invested = serializers.IntegerField()
    savings = serializers.IntegerField()
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    btc_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    past_years = serializers.IntegerField(min_value=1, max_value=10)


class DcaResponseSerializer(serializers.Serializer):
    """Response shape for mode=simple; mode=table returns a list of the same
    objects per asset, one entry per year."""

    Bitcoin = SavingsSerializer()
    Stocks = SavingsSerializer()


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class DcaRequestSerializer(serializers.Serializer):
    MODE_CHOICES = ["simple", "table"]
    FREQUENCY_CHOICES = ["d", "w", "b", "m"]

    mode = CaseInsensitiveChoiceField(choices=MODE_CHOICES)
    amount = serializers.IntegerField(min_value=1)
    frequency = serializers.ChoiceField(choices=FREQUENCY_CHOICES)
    years = serializers.IntegerField(min_value=1, max_value=10)
    ticker = serializers.CharField(max_length=8)
