from django.contrib import admin
from .models import PriceHistory, HistoryLastUpdated, CurrentPrice

# Register your models here.
admin.site.register(PriceHistory)
admin.site.register(HistoryLastUpdated)
admin.site.register(CurrentPrice)