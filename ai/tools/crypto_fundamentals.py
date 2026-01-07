"""
Cryptocurrency fundamental analysis tool for trading intelligence.

This tool provides comprehensive fundamental analysis of cryptocurrencies using
CoinGecko data including supply metrics, development activity, community engagement,
market trends, and technical indicators like VWAP analysis.

Essential for understanding the underlying health and momentum of crypto assets
beyond just price action.
"""

import logging
from typing import Any
import numpy as np
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool

from ..utils.crypto_data import (
    get_coin_id,
    get_supply_data,
    get_development_data,
    get_community_data,
    get_vwap_analysis,
    check_trending_status,
    get_coin_categories,
)


class CryptoAnalysisInput(BaseModel):
    symbol: str = Field(
        ...,
        description="Cryptocurrency symbol (e.g., BTC, ETH, SOL). Do not use for currencies such as USD or EUR.",
        min_length=1,
        max_length=10,
    )
    analysis_days: int = Field(
        default=7, description="Days for VWAP and trend analysis (1-30)", ge=1, le=30
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
        if isinstance(value, (np.integer, np.floating)):
            value = int(value)
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


@tool(args_schema=CryptoAnalysisInput)
def analyze_crypto_fundamentals(symbol: str, analysis_days: int = 7) -> str:
    """
    Analyze cryptocurrency fundamentals including supply, development,
    community, and market metrics.

    Provides comprehensive fundamental analysis covering:
    - Supply economics and market valuation
    - Development activity and ecosystem health
    - Community engagement and social metrics
    - VWAP analysis and recent trends
    - Market positioning and trending status

    Essential for evaluating crypto assets beyond technical analysis.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, SOL, etc.)
        analysis_days: Days for trend analysis (1-30)

    Returns:
        Formatted fundamental analysis report
    """
    try:
        coin_id = get_coin_id(symbol.upper())

        if not coin_id:
            return (
                f"Error: Could not find data for symbol '{symbol}'. "
                f"Please check the symbol and try again."
            )

        supply_metrics = get_supply_data(coin_id)
        dev_metrics = get_development_data(coin_id)
        community_metrics = get_community_data(coin_id)
        vwap_analysis = get_vwap_analysis(coin_id, analysis_days)

        is_trending = check_trending_status(coin_id)
        categories = get_coin_categories(coin_id)

        result = f"""
            **CRYPTO FUNDAMENTAL ANALYSIS: {symbol.upper()}**

            🏦 **SUPPLY & VALUATION**
            • Market Cap: {format_number(supply_metrics.get('market_cap_usd'))}
            • Circulating Supply: {format_number(supply_metrics.get('circulating_supply', 0), ' tokens')}
            • Total Supply: {format_number(supply_metrics.get('total_supply', 0), ' tokens')}
            • Max Supply: {format_number(supply_metrics.get('max_supply', 0), ' tokens')}
            • 24h Volume: {format_number(supply_metrics.get('volume_24h_usd'))}
            • FDV: {format_number(supply_metrics.get('fully_diluted_valuation'))}
            • Liquidity Score: {supply_metrics.get('liquidity_score', 'N/A')}/10
            
            💻 **DEVELOPMENT ACTIVITY** 
            • GitHub Stars: {format_int(dev_metrics.get('stars', 'N/A'))}
            • Forks: {format_int(dev_metrics.get('forks', 'N/A'))}
            • Contributors: {format_int(dev_metrics.get('subscribers', 'N/A'))}
            • Commits (4 weeks): {format_int(dev_metrics.get('commit_count_4_weeks', 'N/A'))}
            • Issues Closed: {format_int(dev_metrics.get('closed_issues', 'N/A'))}
            
            👥 **COMMUNITY ENGAGEMENT**
            • Twitter Followers: {format_int(community_metrics.get('twitter_followers', 'N/A'))}
            • Reddit Subscribers: {format_int(community_metrics.get('reddit_subscribers', 'N/A'))}
            • Telegram Users: {format_int(community_metrics.get('telegram_channel_user_count', 'N/A'))}
            • Facebook Likes: {format_int(community_metrics.get('facebook_likes', 'N/A'))}

            📊 **VWAP & TREND ANALYSIS ({analysis_days} days)**
            • Current Price: {format_number(vwap_analysis.get('current_price', 0))}
            • VWAP: {format_number(vwap_analysis.get('current_vwap', 0))}
            • Price vs VWAP: {format_percentage(vwap_analysis.get('vwap_premium_pct', 0))} {'📈' if vwap_analysis.get('vwap_premium_pct', 0) > 0 else '📉'}
            • VWAP Trend (3d): {format_percentage(vwap_analysis.get('vwap_trend_3d_pct', 0))} {'🔥' if vwap_analysis.get('vwap_trend_3d_pct', 0) > 0.05 else '❄️' if vwap_analysis.get('vwap_trend_3d_pct', 0) < -0.05 else '➡️'}
            • Volume Trend: {format_percentage(vwap_analysis.get('volume_trend_pct', 0))} {'⬆️' if vwap_analysis.get('volume_trend_pct', 0) > 0.1 else '⬇️' if vwap_analysis.get('volume_trend_pct', 0) < -0.1 else '➡️'}

            🎯 **MARKET CONTEXT**
            • Trending Status: {'🔥 Currently Trending' if is_trending else '⚪ Not Trending'}
            • Categories: {', '.join(categories[:3]) if categories else 'N/A'}
            • Data Quality: {vwap_analysis.get('data_points', 0)} daily samples

            💡 **KEY INSIGHTS**
            • **Valuation**: {'Premium' if vwap_analysis.get('vwap_premium_pct', 0) > 0.05 else 'Discount' if vwap_analysis.get('vwap_premium_pct', 0) < -0.05 else 'Fair'} to VWAP
            • **Momentum**: {'Strong positive' if vwap_analysis.get('vwap_trend_3d_pct', 0) > 0.05 else 'Strong negative' if vwap_analysis.get('vwap_trend_3d_pct', 0) < -0.05 else 'Neutral'} trend
            • **Activity**: {'High' if vwap_analysis.get('volume_trend_pct', 0) > 0.1 else 'Low' if vwap_analysis.get('volume_trend_pct', 0) < -0.1 else 'Normal'} volume activity
            • **Development**: {'Active' if dev_metrics.get('commit_count_4_weeks', 0) > 10 else 'Limited'} recent development

            *Analysis powered by CoinGecko API*
        """.strip()

        logging.info(result[:100])
        return result

    except Exception as e:
        logging.error(f"Error analyzing crypto fundamentals for {symbol}: {e}")
        return f"Error analyzing crypto fundamentals for {symbol}: {str(e)}"
