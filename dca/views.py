import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .constants import BTC_TICKER
from .serializers import DcaRequestSerializer, SavingsSerializer
from .utils import (
    InsufficientHistoryError,
    UpstreamDataError,
    calculate_savings,
    update_current_price,
    update_price_history,
)

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
def get_DCA_data(request):
    serializer = DcaRequestSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    params = serializer.validated_data

    try:
        results = {}
        for label, ticker in (("Bitcoin", BTC_TICKER), ("Stocks", params["ticker"])):
            price = update_current_price(ticker)
            history = update_price_history(ticker)
            if params["mode"] == "simple":
                savings = calculate_savings(
                    params["frequency"], params["amount"], params["years"], history, price, ticker
                )
                results[label] = SavingsSerializer(savings).data
            else:  # table: one row per year from 1 to `years`
                rows = [
                    calculate_savings(
                        params["frequency"], params["amount"], n, history, price, ticker
                    )
                    for n in range(1, params["years"] + 1)
                ]
                results[label] = SavingsSerializer(rows, many=True).data
    except InsufficientHistoryError as e:
        return Response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
    except UpstreamDataError:
        logger.exception("Upstream price data fetch failed for ticker %s", params["ticker"])
        return Response(
            {"error": "Unknown ticker or price data temporarily unavailable"},
            status.HTTP_502_BAD_GATEWAY,
        )

    return Response(results)
