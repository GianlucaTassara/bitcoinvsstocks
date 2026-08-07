from django.db import models
from django.db.models import UniqueConstraint


class PriceHistory(models.Model):
    """Represents the price for a particular date"""

    ticker = models.CharField(max_length=12)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    date = models.DateField()

    class Meta:
        constraints = [UniqueConstraint(fields=["ticker", "date"], name="unique_ticker_date")]

    def __str__(self):
        return f"{self.ticker} @ {self.date}: {self.price} {self.currency}"


class HistoryLastUpdated(models.Model):
    """Specifies the last time price history was updated"""

    ticker = models.CharField(primary_key=True, max_length=12)
    last_updated = models.DateField(auto_now=True)
    update_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.ticker} history last updated {self.last_updated}"


class CurrentPrice(models.Model):
    """Specifies the current price for bitcoin or a particular stock"""

    ticker = models.CharField(max_length=12)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    update_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.ticker}: {self.price}"
