"""
Crypto regime analysis utilities and calculations.

This module provides functions to compute features necessary for crypto regime
analysis, score the regime based on these features, and classify the regime
into categories such as "Risk-On", "Risk-Off", or "Transitional".
"""

import pandas as pd
from typing import Literal

from .data_fetchers import (
    fetch_binance_klines,
    fetch_total_and_alt_mcap,
    fetch_yahoo_data,
    YAHOO_TICKERS,
)


def compute_regime_features(lookback_days: int = 5) -> pd.DataFrame:
    """Compute all features needed for crypto regime analysis."""
    btc = fetch_binance_klines("BTCUSDT", lookback_days)
    btc.index = btc.index.normalize()

    eth = fetch_binance_klines("ETHUSDT", lookback_days)
    eth.index = eth.index.normalize()

    prices = pd.concat([btc, eth], axis=1)
    prices.columns = ["btc", "eth"]

    mcap = fetch_total_and_alt_mcap(days=7)
    mcap = mcap.resample("1D").ffill()

    macro = fetch_yahoo_data(YAHOO_TICKERS)

    df = prices.join(mcap, how="left")
    df = df.join(macro, how="left")
    df[["sp500", "qqq", "dxy"]] = df[["sp500", "qqq", "dxy"]].ffill()

    df["eth_btc"] = df["eth"] / df["btc"]
    df["btc_dom"] = 1 - df["alt"] / df["total"]

    PCT_COLS = ["btc", "eth_btc", "dxy", "btc_dom"]

    for col in PCT_COLS:
        df[f"{col}_delta"] = (df[col] / df[col].shift(lookback_days)) - 1

    df["alt_rel"] = (df["alt"] / df["alt"].shift(lookback_days)) - (
        df["total"] / df["total"].shift(lookback_days)
    )
    df["qqq_rel"] = (df["qqq"] / df["qqq"].shift(lookback_days)) - (
        df["sp500"] / df["sp500"].shift(lookback_days)
    )

    return df.dropna(
        subset=[
            "btc_delta",
            "eth_btc_delta",
            "btc_dom_delta",
            "alt_rel",
            "qqq_rel",
            "dxy_delta",
        ]
    )


def score_crypto_regime(row: pd.Series) -> int:
    """
    Score a single row for crypto regime analysis.
    Explanation of scoring:
    - BTC Price up = +1, down = -1
    - ETH/BTC up = +1, down = -1
    - BTC Dominance down = +1, up = -1
    - Alt Performance up = +1, down = -1
    - QQQ vs SPY up = +1, down = -1
    - DXY down = +1, up = -1
    Total score ranges from -6 (very bearish) to +6 (very bullish).

    """
    score = 0
    score += 1 if row["btc_delta"] > 0 else -1
    score += 1 if row["eth_btc_delta"] > 0 else -1
    score += 1 if row["btc_dom_delta"] < 0 else -1
    score += 1 if row["alt_rel"] > 0 else -1
    score += 1 if row["qqq_rel"] > 0 else -1
    score += 1 if row["dxy_delta"] < 0 else -1
    return score


def classify_regime(score: int) -> Literal["Risk-On", "Risk-Off", "Transitional"]:
    """Classify regime based on composite score."""
    if score >= 4:
        return "Risk-On"
    if score <= 1:
        return "Risk-Off"
    return "Transitional"
