from django.contrib import admin

from .models import CurrentPrice, HistoryLastUpdated, PriceHistory

# Register your models here.
admin.site.register(PriceHistory)
admin.site.register(HistoryLastUpdated)
admin.site.register(CurrentPrice)
