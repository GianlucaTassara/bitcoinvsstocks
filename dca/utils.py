import yfinance as yf
from datetime import timedelta
from .models import CurrentPrice, PriceHistory, HistoryLastUpdated
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone
from .constants import BTC_TICKER



class Savings():
    """
    Represents the results of a particular DCA strategy.
    """

    def __init__(self, ticker, invested, past_years, savings, profit, btc_amount=None):
        self.ticker = ticker
        self.invested = invested
        self.savings = savings
        self.past_years = past_years
        self.profit = profit
        self.btc_amount = btc_amount

    def __str__(self):
        return f"Ticker: {self.ticker} Invested: {self.invested} Savings: {self.savings} Profit: {self.profit} Btc: {self.btc_amount}"


def update_current_price(ticker):
    """
    Updates current price on database.

    If price doesn't exist or was last updated more than 15 minutes ago,
    then get price from Yahoo and update database.

    :param ticker: Ticker representing bitcoin or a specific stock
    :returns: Current price, extracted from database.
    """

    try:
        db_price = CurrentPrice.objects.get(ticker=ticker)
        fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
        if db_price.last_updated < fifteen_minutes_ago:
            db_price.price = get_price_from_yahoo(ticker)
            db_price.update_count += 1
            db_price.save()
    except ObjectDoesNotExist:
        db_price = CurrentPrice(ticker=ticker, price=get_price_from_yahoo(ticker), update_count=1)
        db_price.save()
    return float(db_price.price)


def get_price_from_yahoo(ticker):
    """
    Retrieves price of bitcoin or stock from Yahoo's API.

    :param ticker: Ticker representing bitcoin or a specific stock.
    :returns: Current price.
    """
    fdata = yf.Ticker(ticker)
    today = fdata.history(period='1d', interval='1m', raise_errors=True)
    if (today.empty):
        raise Exception(f"Unable to extract price for {ticker} ticker")
    return float(today['Close'][-1])


def update_price_history(ticker):
    """
    Updates price history on database.

    If it doesn't exist or hasn't been updated today, 
    then get price history from Yahoo and update database.

    :param ticker: Ticker representing bitcoin or a specific stock.
    :returns: Price history, extracted from database.
    """

    update, *_ = HistoryLastUpdated.objects.get_or_create(ticker=ticker,defaults={"update_count" : 0})
    if update.last_updated != timezone.now().date():
        history = get_history_from_yahoo(ticker, None, update.last_updated, timezone.now().date())
        update_history_db(ticker, history)
    elif update.update_count == 0:
        history = get_history_from_yahoo(ticker, "10y")
        update_history_db(ticker, history)
    update.update_count += 1
    update.save()
    return get_history_from_db(ticker)


def update_history_db(ticker, history):
    """
    Updates price history on database.

    :param ticker: Ticker representing bitcoin or a specific stock.
    :param history: A list of prices already ordered by date.
    """
    prices = [PriceHistory(ticker=ticker, price=price, currency='USD', date=date) for date, price in history.items()]
    PriceHistory.objects.bulk_create(prices, ignore_conflicts=True)


def get_history_from_db(ticker):
    """
    Gets price history from database.

    :param ticker: Ticker representing bitcoin or a specific stock.
    :returns: A list of all daily close prices ordered by date.
    """
    prices_queryset = PriceHistory.objects.filter(ticker=ticker).order_by('date').values_list('price', flat=True)
    return [float(price) for price in prices_queryset]


def get_history_from_yahoo(ticker, period, start=None, end=None):
    """
    Gets price history from Yahoo's API.

    :param ticker: Ticker representing bitcoin or a specific stock.
    :param period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    :param start: If period is None, specify start date
    :param end: If period is None, specifiy end date
    :returns: Dict with dates and price for those dates
    """
    fdata = yf.Ticker(ticker)
    history = fdata.history(period)
    results = {key.date(): value for key, value in history['Close'].to_dict().items()}
    return results
    

def calculate_savings(frequency, amount, years, history, current_price, ticker):
    """
    Calculates the results of a dollar cost average (DCA) strategy.

    Stocks don't have daily close prices for weekends so calculating
    results is done differently than Bitcoin.

    :param frequency: How often: (w)eekly, (b)iweekly, (m)onthly.
    :param amount: How much.
    :param years: Starting how far back in years.
    :param history: List of prices ordered from oldest to recent.
    :param current_price: Current price.
    :param ticker: Ticker representing bitcoin or a specific stock.
    :returns: A Savings object with results.

    """

    if ticker.casefold() == BTC_TICKER.casefold():
        match frequency:
            case "d": days = 1
            case "w": days = 7
            case "b": days = 14
            case "m": days = 30
        timespan = 364 * years
    else:        
        match frequency:
            case "d": days = 1
            case "w": days = 5
            case "b": days = 10
            case "m": days = 21
        timespan = 260 * years
    savings = 0
    counter = 0
    timespan -= days
    while timespan > 0:
        savings += (amount / history[-timespan])
        timespan -= days
        counter += 1
    result = savings * current_price
    profit = (result / (amount * counter) - 1) * 100
    btc_amount = savings if ticker.casefold() == BTC_TICKER.casefold() else None
    return Savings(ticker, amount * counter, years, int(result), profit, btc_amount)


