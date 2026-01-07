"""
Signal generation module for trading strategies.

This module defines the SignalGenerator class, which evaluates EMA crossovers,
long-term trends, and confirmation indicators to generate trading signals.
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress
from typing import Literal
import logging


class SignalGenerator:
    """
    Generates trading signals and confirms them using technical indicators.

    Methods
    -------
    evaluate_ema_crossover(fast_df, confirm_df, fast, slow)
        Checks for bullish or bearish EMA crossover signals,
        confirmed on a higher timeframe.

    evaluate_long_term_trend(df_1h, df_4h)
        Evaluates long-term trend direction based on EMA 50/200 crossovers
        on 1h and 4h charts.

    check_confirmations(df, trend_bias, trade_signal)
        Validates a trade signal using multiple momentum and volume indicators.

    calculate_slope(series, window, normalize)
        Computes a normalized slope for a time series using linear regression over
        a lookback window.
    """

    def __init__(self, config):
        """
        Initialize SignalGenerator with customizable indicator toggles.

        Parameters
        ----------
        indicators : dict, optional
            Dictionary specifying which indicators to include in confirmation, e.g.,
            {'rsi': True, 'stoch': True, 'adx': True, 'di': True,
            'volume': True, 'bias': True}
        """
        self.confirmation_indicator_window = config.strategy_params[
            "confirmation_indicator_window"
        ]
        self.atr_multiplier = config.strategy_params["atr_multiplier"]
        self.atr_window = config.strategy_params["atr_window"]

    def evaluate_ema_crossover_with_metrics(
        self,
        fast_df: pd.DataFrame,
        confirm_df: pd.DataFrame,
        lookback_bars: int = 3,
        persistence_bars: int = 0,
        eps: float = 0.0,
        min_delta_k_atr: float = 0.0,
        slope_window_fast: int = 3,
        slope_threshold: float = 0.0,
        confirm_slope_window: int = 2,
        confirm_slope_threshold: float = 0.0005,
    ) -> dict:

        last_row_atr = fast_df.iloc[-1]["atr"]
        eps = 0.01 * last_row_atr if last_row_atr > 0 else 0.0

        fe = fast_df["ema_fast"]
        se = fast_df["ema_slow"]

        bullish_mask = (fe.shift(1) <= se.shift(1) + eps) & (fe > se - eps)
        bearish_mask = (fe.shift(1) >= se.shift(1) - eps) & (fe < se + eps)

        recent_bullish = bullish_mask.tail(lookback_bars)
        recent_bearish = bearish_mask.tail(lookback_bars)

        signal_type = None
        cross_idx = None
        if recent_bullish.any():
            signal_type = "bullish"
            cross_idx = recent_bullish[recent_bullish].index[-1]
        elif recent_bearish.any():
            signal_type = "bearish"
            cross_idx = recent_bearish[recent_bearish].index[-1]
        else:
            return None

        if persistence_bars > 0:
            post = fast_df.loc[cross_idx:].head(persistence_bars + 1)
            if len(post) >= persistence_bars + 1:
                if signal_type == "bullish":
                    if not (post["ema_fast"] > post["ema_slow"]).all():
                        return None
                elif signal_type == "bearish":
                    if not (post["ema_fast"] < post["ema_slow"]).all():
                        return None

        if min_delta_k_atr > 0 and "atr" in fast_df.columns:
            last_row = fast_df.iloc[-1]
            delta = abs(last_row["ema_fast"] - last_row["ema_slow"])
            if last_row["atr"] > 0 and delta < min_delta_k_atr * last_row["atr"]:
                return None

        s_fast = self.calculate_slope(fe, slope_window_fast)
        if signal_type == "bullish" and s_fast <= slope_threshold:
            return None
        if signal_type == "bearish" and s_fast >= -slope_threshold:
            return None

        ce = confirm_df["ema_fast"].dropna()
        if len(ce) >= confirm_slope_window:
            conf_s = self.calculate_slope(
                ce,
                confirm_slope_window,
            )
            if signal_type == "bullish" and conf_s <= confirm_slope_threshold:
                return None
            if signal_type == "bearish" and conf_s >= -confirm_slope_threshold:
                return None

        metrics = {
            "ema_fast_slope": round(
                float(self.calculate_slope(fe, slope_window_fast)), 6
            ),
            "ema_slow_slope": round(
                float(self.calculate_slope(se, slope_window_fast)), 6
            ),
            "ema_confirm_slope": (
                round(float(self.calculate_slope(ce, confirm_slope_window)), 6)
                if len(ce) >= confirm_slope_window
                else None
            ),
            "close_slope": round(
                float(self.calculate_slope(fast_df["close"], slope_window_fast)), 6
            ),
            "ema_separation_pct": round(
                float(((fe.iloc[-1] - se.iloc[-1]) / se.iloc[-1]) * 100), 6
            ),
            "ema_fast_acceleration": round(float(self.calculate_slope(fe, 2)), 6),
        }
        return {
            "signal": signal_type,
            "ema_metrics": metrics,
        }

    def check_confirmations(
        self, df: pd.DataFrame, trade_signal: str, confirmation_slope_window: int = 5
    ) -> dict:
        """
        Collect confirmation indicators.

        Parameters
        ----------
        df : pd.DataFrame
            Data used to compute confirmation indicators.
        trade_signal : str or None
            Short/medium-term trade signal to confirm.
        now : datetime.datetime


        Returns
        -------
        dict
            Dictionary with 'valid': bool and 'direction': str.
        """
        indicator_dictionary = {}

        adx_value = df["adx"].iloc[-1]
        adx_slope = self.calculate_slope(df["adx"], window=confirmation_slope_window)
        indicator_dictionary["adx_slope"] = adx_slope
        indicator_dictionary["adx"] = round(adx_value, 1)

        di_plus = df["adx_pos"].iloc[-1]
        di_minus = df["adx_neg"].iloc[-1]
        di_plus_slope = self.calculate_slope(
            df["adx_pos"], window=confirmation_slope_window
        )
        di_minus_slope = self.calculate_slope(
            df["adx_neg"], window=confirmation_slope_window
        )
        indicator_dictionary["di_plus"] = round(di_plus, 1)
        indicator_dictionary["di_minus"] = round(di_minus, 1)
        indicator_dictionary["di_difference"] = round(di_plus - di_minus, 2)
        indicator_dictionary["di_plus_slope"] = round(di_plus_slope, 3)
        indicator_dictionary["di_minus_slope"] = round(di_minus_slope, 3)

        volume = df["volume"].iloc[-1]
        avg_volume = (
            df["volume"]
            .rolling(window=self.confirmation_indicator_window)
            .mean()
            .iloc[-1]
        )
        volume_slope = self.calculate_slope(
            df["volume"], window=self.confirmation_indicator_window
        )

        indicator_dictionary["volume"] = round(volume)
        indicator_dictionary["avg_volume"] = round(avg_volume)
        indicator_dictionary["volume_trend_slope"] = round(volume_slope, 4)

        rsi_series = df["rsi"]
        rsi = rsi_series.iloc[-1]
        rsi_last = rsi_series.iloc[-confirmation_slope_window:]
        rsi_last_mean = rsi_last.mean()
        rsi_ratio = rsi / rsi_last_mean
        indicator_dictionary["rsi"] = round(rsi, 1)
        indicator_dictionary["rsi_ratio_to_avg"] = round(rsi_ratio, 4)

        price = df["close"].iloc[-1]
        atr = df["atr"].iloc[-1]
        atr_avg = df["atr"].rolling(window=self.atr_window).mean().iloc[-1]
        atr_slope = self.calculate_slope(df["atr"], window=self.atr_window)
        stop_loss_price = (
            (price - self.atr_multiplier * atr)
            if trade_signal == "bullish"
            else (price + self.atr_multiplier * atr)
        )
        stop_loss_to_price_ratio = abs(((stop_loss_price / price) - 1) * 100)
        indicator_dictionary["atr_avg"] = round(atr_avg, 4)
        indicator_dictionary["atr"] = round(atr, 4)
        indicator_dictionary["atr_slope"] = round(atr_slope, 4)
        indicator_dictionary["stop_loss_to_price_pct"] = round(
            stop_loss_to_price_ratio, 3
        )

        return indicator_dictionary

    @staticmethod
    def calculate_slope(
        series: pd.Series,
        window: int = 3,
        normalize: Literal["first", "mean", "last", None] = "mean",
    ) -> float:
        """
        Calculate the normalized slope of a pandas Series over a specified window.

        Parameters
        ----------
        series : pd.Series
            Time series data such as RSI, EMA, or price.
        window : int, optional
            Number of most recent points to include in slope calculation. Default is 5.
        normalize : {'first', 'mean', None}, optional
            Method used to normalize the slope value:
            - 'first': Normalize by the first value in the window.
            - 'mean': Normalize by the mean value in the window.
            - None: Return the raw slope value.
            Default is 'first'.

        Returns
        -------
        float
            The normalized slope of the series. Returns np.nan if insufficient data.

        """
        if len(series) < window:
            logging.error("\n\nInsufficient data for slope calculation.\n\n")
            return np.nan

        y = series.iloc[-window:].values
        x = np.arange(window)

        slope, _, _, _, _ = linregress(x, y)

        if normalize == "first":
            return slope / y[0]
        elif normalize == "last":
            return slope / y[-1]
        elif normalize == "mean":
            return slope / np.mean(y)
        else:
            return slope
