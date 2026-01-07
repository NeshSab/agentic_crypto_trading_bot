"""
Data fetching module for retrieving market data and calculating technical indicators.

This module defines the DataFetcher class, which interacts with a broker's API
to fetch candlestick data and market tickers. It also includes methods to
process the data into pandas DataFrames and compute various technical indicators
using the 'ta' library.
"""

import logging
import pandas as pd
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator


class DataFetcher:
    def __init__(self, broker):
        self.marketAPI = broker.marketAPI
        logging.info("DataFetcher initialized with OKX MarketAPI.")

    def fetch_candles(self, symbol, bar, limit):
        try:
            candles = self.marketAPI.get_candlesticks(
                instId=symbol, bar=bar, limit=limit
            )
            df = pd.DataFrame(
                candles["data"],
                columns=[
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "volCcy",
                    "volCcyQuote",
                    "confirm",
                ],
            )
            df = DataFetcher.convert_to_float(df)
            df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="ms")
            df = df.sort_values("ts")
            logging.info(f"Fetched {len(df)} candles for {symbol}")
            return df
        except Exception as e:
            logging.error(f"Failed to fetch candles for {symbol}: {e}")
            return None

    def fetch_candles_with_indicators(self, symbol, bar, limit, params):
        try:
            candles = self.marketAPI.get_candlesticks(
                instId=symbol, bar=bar, limit=limit
            )
            df = pd.DataFrame(
                candles["data"],
                columns=[
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "volCcy",
                    "volCcyQuote",
                    "confirm",
                ],
            )
            df = DataFetcher.convert_to_float(df)
            df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="ms")
            df = df.sort_values("ts")
            df = self.add_indicator_columns(df, params)
            logging.info(f"Fetched {len(df)} candles for {symbol}")
            return df
        except Exception as e:
            logging.error(f"Failed to fetch candles for {symbol}: {e}")
            return None

    @staticmethod
    def convert_to_float(df, skip_cols=["ts", "timestamp"]):
        try:
            numeric_cols = [col for col in df.columns if col not in skip_cols]
            df[numeric_cols] = df[numeric_cols].astype(float)
        except Exception as e:
            logging.exception(f"Error converting to floats: {e}")
        return df

    def get_ticker(self, symbol):
        try:
            ticker = self.marketAPI.get_ticker(instId=symbol)
            logging.info(f"Ticker fetched for {symbol}")
            return ticker
        except Exception as e:
            logging.error(f"Failed to fetch ticker for {symbol}: {e}")
            return None

    @staticmethod
    def add_indicator_columns(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        df = df.sort_index()

        df["ema_fast"] = EMAIndicator(
            df["close"], window=params["fast_window"]
        ).ema_indicator()
        df["ema_slow"] = EMAIndicator(
            df["close"], window=params["slow_window"]
        ).ema_indicator()
        df["rsi"] = RSIIndicator(
            df["close"], window=params["confirmation_indicator_window"]
        ).rsi()
        adx = ADXIndicator(
            df["high"],
            df["low"],
            df["close"],
            window=params["confirmation_indicator_window"],
        )
        df["adx"] = adx.adx()
        df["adx_pos"] = adx.adx_pos()
        df["adx_neg"] = adx.adx_neg()

        df["atr"] = AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=params["atr_window"],
        ).average_true_range()

        return df
