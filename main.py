# import yfinance as yf
import pytz
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup


def get_sp500_tickers():
    from io import StringIO

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(
        res.content,
        "html.parser",
    )
    table = soup.find_all("table")[0]
    df = pd.read_html(StringIO(str(table)))
    tickers = list(df[0].Symbol)
    return tickers


def get_history(ticker, period_start, period_end, granularity="1d"):
    import yfinance

    df = (
        yfinance.Ticker(ticker)
        .history(
            start=period_start, end=period_end, interval=granularity, auto_adjust=True
        )
        .reset_index()
    )
    df = df.rename(
        columns={
            "Date": "datetime",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    if df.empty:
        return pd.DataFrame()

    df["datetime"] = df["datetime"].dt.tz_convert(pytz.utc)
    df = df.drop(columns=["Dividends", "Stock Splits"])
    df = df.set_index("datetime", drop=True)
    return df


import threading


def get_histories(tickers, period_start, period_end, granularity="1d"):
    dfs = [None] * len(tickers)

    def _helper(i):
        print(tickers[i])
        try:
            df = get_history(
                tickers[i], period_start, period_end, granularity=granularity
            )
            if df is not None and not df.empty:
                dfs[i] = df
        except Exception:
            pass

    threads = [threading.Thread(target=_helper, args=(i,)) for i in range(len(tickers))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    tickers = [tickers[i] for i in range(len(tickers)) if dfs[i] is not None]
    dfs = [df for df in dfs if df is not None]

    return tickers, dfs


def get_ticker_dfs(start, end):
    tickers = get_sp500_tickers()
    starts = [start] * len(tickers)
    ends = [end] * len(tickers)
    tickers, dfs = get_histories(tickers[:30], starts, ends, granularity="1d")
    return tickers, {ticker: df for ticker, df in zip(tickers, dfs)}


period_start = datetime(2015, 1, 1, tzinfo=pytz.utc)
period_end = datetime(2026, 1, 1, tzinfo=pytz.utc)
tickers, tickers_dfs = get_ticker_dfs(start=period_start, end=period_end)
print(tickers_dfs)
