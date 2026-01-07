"""
Crypto market regime analysis tool for trading intelligence.

This tool analyzes the current cryptocurrency market regime by examining
multiple factors including price action, market structure, and macro indicators.
It provides a comprehensive assessment of whether the market is in Risk-On,
Risk-Off, or Transitional state.

The regime is determined by scoring 6 key factors:
- BTC price momentum
- ETH/BTC performance
- BTC dominance trends
- Altcoin market cap performance
- Risk appetite (QQQ vs SPY)
- Dollar strength (DXY)

Scoring: +1 for bullish factors, -1 for bearish factors
Regime classification: 4-6 = Risk-On, 2-3 = Transitional, ≤1 = Risk-Off
"""

import logging
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool


from ..utils.regime_analysis import (
    compute_regime_features,
    score_crypto_regime,
    classify_regime,
)


class CryptoRegimeInput(BaseModel):
    lookback_days: int = Field(
        default=5,
        description="Number of days to look back for momentum calculations from one to seven days tops",
        ge=1,
        le=7,
    )

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


@tool(args_schema=CryptoRegimeInput)
def analyze_crypto_regime(lookback_days: int = 5) -> str:
    """
    Analyze current cryptocurrency market regime as Risk-On,
    Risk-Off, or Transitional state. Essential for understanding current
    market dynamics and positioning.

    Args:
        lookback_days: Days to look back for momentum calculations (1-30)

    Returns:
        Formatted regime analysis with current state, trend, and key factors
    """
    try:
        try:
            df = compute_regime_features(lookback_days)
        except Exception as e:
            logging.error(f"Compute regime error: {e}")
            return "Data is not available. Move on."

        df["crypto_score"] = df.apply(score_crypto_regime, axis=1)
        df["crypto_regime"] = df["crypto_score"].apply(classify_regime)

        latest = df.iloc[-1]

        recent_regimes = df["crypto_regime"].tail(5).tolist()
        recent_scores = df["crypto_score"].tail(5).astype(int).tolist()

        result = f"""
            **CRYPTO MARKET REGIME ANALYSIS**

            🎯 **Current Regime**: {latest["crypto_regime"]} (Score: {int(latest["crypto_score"])}/6)

            📊 **Factor Breakdown**:
            • BTC Price ({lookback_days}d): {latest["btc_delta"]:.1%} ({'✅' if latest["btc_delta"] > 0 else '❌'})
            • ETH/BTC Ratio: {latest["eth_btc_delta"]:.1%} ({'✅' if latest["eth_btc_delta"] > 0 else '❌'})  
            • BTC Dominance: {latest["btc_dom_delta"]:.1%} ({'✅' if latest["btc_dom_delta"] < 0 else '❌'})
            • Alt Performance: {latest["alt_rel"]:.1%} ({'✅' if latest["alt_rel"] > 0 else '❌'})
            • QQQ vs SPY: {latest["qqq_rel"]:.1%} ({'✅' if latest["qqq_rel"] > 0 else '❌'})
            • DXY Strength: {latest["dxy_delta"]:.1%} ({'✅' if latest["dxy_delta"] < 0 else '❌'})

            📈 **Recent Trend**: {' → '.join(recent_regimes[-3:])}
            📈 **Score History**: {recent_scores}

            💡 **Market Interpretation**:
            • **Risk-On** (4-6): Strong crypto momentum, favorable for aggressive positioning
            • **Risk-Off** (≤1): Defensive conditions, risk management critical
            • **Transitional** (2-3): Mixed signals, selective positioning recommended

            *Analysis as of: {df.index[-1].date()}*
            *Data sources: Binance, CoinGecko, Yahoo Finance*
        """.strip()

        logging.info(result[:100])
        return result

    except Exception as e:
        error_msg = f"Error analyzing crypto regime: {str(e)}"
        logging.error(error_msg)
        return error_msg
