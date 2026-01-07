"""
Data fetching utilities for crypto regime analysis.

This module provides functions to fetch historical price data from Binance,
market capitalization data from CoinGecko, and macroeconomic data from Yahoo
Finance. The data is processed into pandas DataFrames for further analysis.
"""

import requests
import pandas as pd
import yfinance as yf
import time

BINANCE_SYMBOLS = {
    "btc": "BTCUSDT",
    "eth": "ETHUSDT",
}

YAHOO_TICKERS = {
    "sp500": "^GSPC",
    "qqq": "QQQ",
    "dxy": "DX-Y.NYB",
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def fetch_binance_klines(symbol: str, days: int) -> pd.Series:
    """Fetch daily price data from Binance API."""
    limit = days + 5
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1d",
        "limit": limit,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(
        data,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "num_trades",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )
    df["close"] = df["close"].astype(float)
    df["date"] = pd.to_datetime(df["close_time"], unit="ms")
    return df.set_index("date")["close"]


def fetch_coingecko_market_cap_series(coin_id: str, days: int) -> pd.Series:
    """Fetch market cap time series from CoinGecko API."""
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "market_caps" not in data:
        raise RuntimeError(f"CoinGecko error for {coin_id}: {data}")

    df = pd.DataFrame(data["market_caps"], columns=["ts", "mcap"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    return df.set_index("date")["mcap"]


def fetch_total_and_alt_mcap(days: int = 7) -> pd.DataFrame:
    """Calculate total crypto market cap and altcoin market cap."""
    btc_mcap = fetch_coingecko_market_cap_series("bitcoin", days)
    time.sleep(0.5)

    global_url = f"{COINGECKO_BASE}/global"
    response = requests.get(global_url, timeout=10)
    response.raise_for_status()
    global_data = response.json()["data"]

    btc_share = global_data["market_cap_percentage"]["btc"] / 100
    total_mcap = btc_mcap / btc_share

    df = pd.DataFrame(
        {
            "btc_mcap": btc_mcap,
            "total": total_mcap,
        }
    )

    df["alt"] = df["total"] - df["btc_mcap"]
    return df


def fetch_yahoo_data(tickers: dict[str, str], period: str = "1mo") -> pd.DataFrame:
    """Fetch macro market data from Yahoo Finance."""
    df = yf.download(
        list(tickers.values()),
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )["Close"]

    return df.rename(columns={v: k for k, v in tickers.items()}).ffill()
