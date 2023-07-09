from rest_framework import serializers

class SavingsSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=12)
    invested = serializers.IntegerField(min_value=1)
    savings = serializers.IntegerField(min_value=1)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    btc_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    past_years = serializers.IntegerField(min_value=1, max_value=7)

    

class DcaSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=12)
    bitcoin_savings = SavingsSerializer
    trad_savings = SavingsSerializer


class DcaRequestSerializer(serializers.Serializer):
    #mode, amount, frequency, years, ticker
    mode = serializers.CharField(max_length=12)
    amount = serializers.IntegerField(min_value=1)
    frequency = serializers.CharField(max_length=1)
    years = serializers.IntegerField(min_value=1, max_value=7)
    ticker = serializers.CharField(max_length=5)

    #def validate(self, attrs):
    #    frequency = attrs.get['frequency']
    #    if frequency.casefold() not in ['d','w','b','m']:
    #        raise serializers.ValidationError('Frequency must be d, w, b or m')
    #    return attrs
