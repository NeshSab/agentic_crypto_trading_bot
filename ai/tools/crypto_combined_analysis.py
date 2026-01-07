"""
Combined cryptocurrency analysis tool for trading intelligence.

This tool provides comprehensive analysis by combining market regime assessment
with detailed fundamental analysis of a specific cryptocurrency. It first evaluates
the overall crypto market regime (Risk-On/Risk-Off/Transitional) and then analyzes
the target cryptocurrency's fundamentals.

This combined view helps traders understand both macro market conditions and
micro asset-specific factors for better decision-making.
"""

import logging
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool

from ..utils.regime_analysis import (
    compute_regime_features,
    score_crypto_regime,
    classify_regime,
)
from ..utils.crypto_data import (
    get_coin_id,
    get_supply_data,
    get_development_data,
    get_community_data,
    get_vwap_analysis,
    check_trending_status,
    get_coin_categories,
)


class CryptoCombinedInput(BaseModel):
    symbol: str = Field(
        ...,
        description="Cryptocurrency symbol (e.g., BTC, ETH, SOL). Do not use for currencies such as USD or EUR.",
        min_length=1,
        max_length=10,
    )
    regime_lookback_days: int = Field(
        default=5,
        description="Days to look back for regime momentum calculations (1-7)",
        ge=1,
        le=7,
    )
    fundamentals_days: int = Field(
        default=7,
        description="Days for VWAP and trend analysis (1-30)",
        ge=1,
        le=30,
    )

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


def format_number(value: Any, suffix: str = "") -> str:
    """Format large numbers with appropriate suffixes."""
    if value is None or value == 0:
        return "N/A"

    try:
        if abs(value) >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B{suffix}"
        elif abs(value) >= 1_000_000:
            return f"${value/1_000_000:.2f}M{suffix}"
        elif abs(value) >= 1_000:
            return f"${value/1_000:.2f}K{suffix}"
        else:
            return f"${value:.2f}{suffix}"
    except Exception:
        return str(value)


def format_int(value: Any) -> str:
    """Safely format integers with thousands separator or return N/A."""
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


def format_percentage(value: Any) -> str:
    """Format percentage values."""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value*100:.1f}%"
    return str(value)


@tool(args_schema=CryptoCombinedInput)
def analyze_crypto_combined(
    symbol: str, regime_lookback_days: int = 5, fundamentals_days: int = 7
) -> str:
    """
    Perform comprehensive cryptocurrency analysis combining market regime
    assessment with detailed fundamental analysis.

    First analyzes the overall crypto market regime to understand macro conditions,
    then provides deep fundamental analysis of the specific cryptocurrency including
    supply metrics, development activity, community engagement, and VWAP trends.

    This combined analysis helps traders understand both:
    1. Macro market conditions (Risk-On/Risk-Off/Transitional)
    2. Asset-specific fundamentals and momentum

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, SOL, etc.)
        regime_lookback_days: Days for regime momentum calculations (1-7)
        fundamentals_days: Days for VWAP and trend analysis (1-30)

    Returns:
        Comprehensive analysis report with regime context and fundamentals
    """
    result_parts = []

    try:
        try:
            df = compute_regime_features(regime_lookback_days)

            df["crypto_score"] = df.apply(score_crypto_regime, axis=1)
            df["crypto_regime"] = df["crypto_score"].apply(classify_regime)

            latest = df.iloc[-1]
            recent_regimes = df["crypto_regime"].tail(5).tolist()
            recent_scores = df["crypto_score"].tail(5).astype(int).tolist()

            regime_score = int(latest["crypto_score"])
            regime_section = f"""
                **═══════════════════════════════════════════════════════**
                **CRYPTO MARKET REGIME ANALYSIS**
                **═══════════════════════════════════════════════════════**

                **Current Regime**: {latest["crypto_regime"]} (Score: {regime_score}/6)

                **Factor Breakdown**:
                • BTC Price ({regime_lookback_days}d): {latest["btc_delta"]:.1%}
                • ETH/BTC Ratio: {latest["eth_btc_delta"]:.1%}
                • BTC Dominance: {latest["btc_dom_delta"]:.1%}
                • Alt Performance: {latest["alt_rel"]:.1%}
                • QQQ vs SPY: {latest["qqq_rel"]:.1%}
                • DXY Strength: {latest["dxy_delta"]:.1%}

                **Recent Trend**: {' → '.join(recent_regimes[-3:])}
                **Score History**: {recent_scores}

                **Market Context**:
                • **Risk-On** (4-6): Strong crypto momentum, favorable for aggressive positioning
                • **Risk-Off** (≤1): Defensive conditions, risk management critical
                • **Transitional** (2-3): Mixed signals, selective positioning recommended

                *Analysis as of: {df.index[-1].date()}*
            """.strip()

            result_parts.append(regime_section)

        except Exception as e:
            logging.error(f"Regime analysis error: {e}")
            result_parts.append(
                "**CRYPTO MARKET REGIME ANALYSIS**\n Regime data unavailable - continuing with fundamentals analysis"
            )

    except Exception as e:
        logging.error(f"Error in regime analysis section: {e}")
        result_parts.append(
            "**CRYPTO MARKET REGIME ANALYSIS**\n Error analyzing regime"
        )

    try:
        coin_id = get_coin_id(symbol.upper())

        if not coin_id:
            result_parts.append(
                f"\n\n**FUNDAMENTALS ANALYSIS ERROR**\nCould not find data for symbol "
                f"'{symbol}'. Please check the symbol and try again."
            )
            return "\n".join(result_parts)

        supply_metrics = get_supply_data(coin_id)
        community_metrics = get_community_data(coin_id)
        vwap_analysis = get_vwap_analysis(coin_id, fundamentals_days)
        is_trending = check_trending_status(coin_id)
        valuation = (
            "Premium"
            if vwap_analysis.get("vwap_premium_pct", 0) > 0.05
            else (
                "Discount"
                if vwap_analysis.get("vwap_premium_pct", 0) < -0.05
                else "Fair"
            )
        )
        momentum = (
            "Strong positive"
            if vwap_analysis.get("vwap_trend_3d_pct", 0) > 0.05
            else (
                "Strong negative"
                if vwap_analysis.get("vwap_trend_3d_pct", 0) < -0.05
                else "Neutral"
            )
        )

        activity = (
            "High"
            if vwap_analysis.get("volume_trend_pct", 0) > 0.1
            else "Low" if vwap_analysis.get("volume_trend_pct", 0) < -0.1 else "Normal"
        )
        fundamentals_section = f"""

            **═══════════════════════════════════════════════════════**
            **FUNDAMENTAL ANALYSIS: {symbol.upper()}**
            **═══════════════════════════════════════════════════════**

            **SUPPLY & VALUATION**
            • Market Cap: {format_number(supply_metrics.get('market_cap_usd'))}
            • Circulating Supply: {format_number(supply_metrics.get('circulating_supply', 0), ' tokens')}
            • Total Supply: {format_number(supply_metrics.get('total_supply', 0), ' tokens')}
            • Max Supply: {format_number(supply_metrics.get('max_supply', 0), ' tokens')}
            • 24h Volume: {format_number(supply_metrics.get('volume_24h_usd'))}
            • FDV: {format_number(supply_metrics.get('fully_diluted_valuation'))}
            • Liquidity Score: {supply_metrics.get('liquidity_score', 'N/A')}/10

            **COMMUNITY ENGAGEMENT**
            • Twitter Followers: {format_int(community_metrics.get('twitter_followers', 'N/A'))}
            • Reddit Subscribers: {format_int(community_metrics.get('reddit_subscribers', 'N/A'))}
            • Telegram Users: {format_int(community_metrics.get('telegram_channel_user_count', 'N/A'))}
            • Facebook Likes: {format_int(community_metrics.get('facebook_likes', 'N/A'))}

            **VWAP & TREND ANALYSIS ({fundamentals_days} days)**
            • Current Price: {format_number(vwap_analysis.get('current_price', 0))}
            • VWAP: {format_number(vwap_analysis.get('current_vwap', 0))}
            • Price vs VWAP: {format_percentage(vwap_analysis.get('vwap_premium_pct', 0))}
            • VWAP Trend (3d): {format_percentage(vwap_analysis.get('vwap_trend_3d_pct', 0))}
            • Volume Trend: {format_percentage(vwap_analysis.get('volume_trend_pct', 0))}

            **MARKET POSITIONING**
            • Trending Status: {'Currently Trending' if is_trending else 'Not Trending'}
            • Data Quality: {vwap_analysis.get('data_points', 0)} daily samples

            💡 **KEY INSIGHTS**
            • **Valuation**: {valuation} to VWAP
            • **Momentum**: {momentum} trend
            • **Activity**: {activity} volume activity
        """.strip()
        result_parts.append(fundamentals_section)

    except Exception as e:
        logging.error(f"Error analyzing fundamentals for {symbol}: {e}")
        result_parts.append(f"\n\n**❌ FUNDAMENTALS ANALYSIS ERROR**\n{str(e)}")

    result = "\n".join(result_parts)
    result += "\n\n*Data sources: Binance, CoinGecko, Yahoo Finance*"

    logging.info(f"Combined analysis completed for {symbol}")
    return result
