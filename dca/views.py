from django.shortcuts import render
from django.http import JsonResponse
from .models import CurrentPrice, HistoryLastUpdated, PriceHistory
from .serializers import SavingsSerializer, DcaSerializer, DcaRequestSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import update_current_price, update_price_history, calculate_savings
from .constants import BTC_TICKER
import datetime



@api_view(['GET', 'POST'])
def get_DCA_data(request):

    DcaRequest = DcaRequestSerializer(data=request.query_params)
    
    if not DcaRequest.is_valid():
        return Response(DcaRequest.errors, status.HTTP_400_BAD_REQUEST)

    try:

        bitcoin_price = update_current_price(BTC_TICKER)
        stock_price = update_current_price(DcaRequest.data['ticker'])
        bitcoin_history = update_price_history(BTC_TICKER)
        stock_history = update_price_history(DcaRequest.data['ticker'])

        if DcaRequest.data['mode'].casefold() == 'simple':            
            bitcoin_savings = SavingsSerializer(calculate_savings(DcaRequest.data['frequency'], DcaRequest.data['amount'], DcaRequest.data['years'], bitcoin_history, bitcoin_price, BTC_TICKER))
            stock_savings = SavingsSerializer(calculate_savings(DcaRequest.data['frequency'], DcaRequest.data['amount'], DcaRequest.data['years'], stock_history, stock_price, DcaRequest.data['ticker']))

        elif DcaRequest.data['mode'].casefold() == 'table':
            bitcoin_savings = []
            stock_savings = []
            for n in range(1,DcaRequest.data['years']+1):
                bitcoin_savings.append(calculate_savings(DcaRequest.data['frequency'], DcaRequest.data['amount'], n, bitcoin_history, bitcoin_price, BTC_TICKER))
                stock_savings.append(calculate_savings(DcaRequest.data['frequency'], DcaRequest.data['amount'], n, stock_history, stock_price, DcaRequest.data['ticker']))
            bitcoin_savings = SavingsSerializer(bitcoin_savings, many=True)
            stock_savings = SavingsSerializer(stock_savings, many=True)
            
    except Exception as e:
        return Response({'error': str(e)}, status.HTTP_501_NOT_IMPLEMENTED)

    return JsonResponse({"Bitcoin": bitcoin_savings.data, "Stocks": stock_savings.data})
    
    
