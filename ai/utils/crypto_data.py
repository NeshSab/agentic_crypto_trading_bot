"""
CoinGecko API data fetching utilities for cryptocurrency fundamentals.

This module defines the CoinGeckoDataFetcher class, which provides methods to
fetch various fundamental data about cryptocurrencies from the CoinGecko API.
It includes functions to resolve coin IDs, retrieve supply metrics, development
and community data, check trending status, get coin categories, and calculate
VWAP trends.
"""

import pandas as pd
from typing import Any, Optional
from pycoingecko import CoinGeckoAPI


class CoinGeckoDataFetcher:
    """Utility class for fetching cryptocurrency data from CoinGecko API."""

    def __init__(self):
        self.cg = CoinGeckoAPI()
        self._coin_list_cache = None
        self._coin_df_cache = None

    def _get_coin_list(self) -> pd.DataFrame:
        """Get cached coin list to avoid repeated API calls."""
        if self._coin_df_cache is None:
            coin_list = self.cg.get_coins_list()
            self._coin_df_cache = pd.DataFrame(coin_list)
            self._coin_df_cache["symbol"] = self._coin_df_cache["symbol"].str.upper()
        return self._coin_df_cache

    def get_best_coin_id(self, symbol: str) -> Optional[str]:
        """
        Resolve trading symbol to best CoinGecko coin ID.

        Args:
            symbol: Trading symbol like 'BTC', 'ETH', 'SOL'

        Returns:
            Best matching CoinGecko coin ID or None if not found
        """
        symbol = symbol.upper()
        coin_df = self._get_coin_list()
        matches = coin_df[coin_df["symbol"] == symbol]

        if matches.empty:
            return None

        preferred_names = {
            "ETH": "ethereum",
            "BTC": "bitcoin",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "MATIC": "polygon",
            "DOT": "polkadot",
            "AVAX": "avalanche",
            "LINK": "chainlink",
            "UNI": "uniswap",
        }

        if symbol in preferred_names:
            target_name = preferred_names[symbol].lower()
            exact_match = matches[matches["name"].str.lower() == target_name]
            if not exact_match.empty:
                return exact_match.iloc[0]["id"]

        matches_sorted = matches.sort_values(by="id", key=lambda x: x.str.len())
        return matches_sorted.iloc[0]["id"]

    def fetch_supply_metrics(self, coin_id: str) -> dict[str, Any]:
        """Fetch supply and market cap metrics for a coin."""
        coin_data = self.cg.get_coin_by_id(id=coin_id, localization=False)
        market_data = coin_data.get("market_data", {})

        return {
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "max_supply": market_data.get("max_supply"),
            "market_cap_usd": market_data.get("market_cap", {}).get("usd"),
            "volume_24h_usd": market_data.get("total_volume", {}).get("usd"),
            "fully_diluted_valuation": market_data.get(
                "fully_diluted_valuation", {}
            ).get("usd"),
            "liquidity_score": coin_data.get("liquidity_score"),
        }

    def fetch_development_metrics(self, coin_id: str) -> dict[str, Any]:
        """Fetch developer activity metrics for a coin."""
        coin_data = self.cg.get_coin_by_id(id=coin_id, localization=False)
        return coin_data.get("developer_data", {})

    def fetch_community_metrics(self, coin_id: str) -> dict[str, Any]:
        """Fetch community engagement metrics for a coin."""
        coin_data = self.cg.get_coin_by_id(id=coin_id, localization=False)
        return coin_data.get("community_data", {})

    def check_trending_status(self, coin_id: str) -> bool:
        """Check if a coin is currently trending on CoinGecko."""
        trending = self.cg.get_search_trending()
        trending_coins = [item["item"]["id"] for item in trending["coins"]]
        return coin_id in trending_coins

    def get_coin_categories(self, coin_id: str) -> list[str]:
        """Get categories/sectors for a specific coin."""
        coin_data = self.cg.get_coin_by_id(id=coin_id, localization=False)
        return coin_data.get("categories", [])

    def calculate_vwap_trends(self, coin_id: str, days: int = 7) -> dict[str, float]:
        """
        Calculate VWAP and trend metrics over specified period.
        VWAP stands for Volume Weighted Average Price.
        If VWAP is higher than current price, it indicates selling pressure.
        Conversely, if VWAP is lower than current price, it indicates buying pressure.

        Args:
            coin_id: CoinGecko coin ID
            days: Number of days to analyze (max 90 for hourly data)

        Returns:
            Dict with VWAP metrics and trend analysis
        """
        data = self.cg.get_coin_market_chart_by_id(
            id=coin_id,
            vs_currency="usd",
            days=min(days, 30),
        )

        prices_df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        volumes_df = pd.DataFrame(
            data["total_volumes"], columns=["timestamp", "volume"]
        )

        df = prices_df.copy()
        df["volume"] = volumes_df["volume"]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["date"] = df["timestamp"].dt.date

        df["price_volume"] = df["price"] * df["volume"]
        daily_vwap = df.groupby("date").agg(
            {
                "price_volume": "sum",
                "volume": "sum",
                "price": "last",
            }
        )
        daily_vwap["vwap"] = daily_vwap["price_volume"] / daily_vwap["volume"]

        latest_vwap = daily_vwap["vwap"].iloc[-1]
        latest_price = daily_vwap["price"].iloc[-1]
        vwap_premium = (latest_price / latest_vwap - 1) if latest_vwap > 0 else 0
        if len(daily_vwap) >= 3:
            recent_vwap = daily_vwap["vwap"].tail(3)
            vwap_trend_3d = recent_vwap.iloc[-1] / recent_vwap.iloc[0] - 1
        else:
            vwap_trend_3d = 0

        avg_volume_7d = daily_vwap["volume"].mean()
        recent_volume_3d = daily_vwap["volume"].tail(3).mean()
        volume_trend = (
            (recent_volume_3d / avg_volume_7d - 1) if avg_volume_7d > 0 else 0
        )

        return {
            "current_price": latest_price,
            "current_vwap": latest_vwap,
            "vwap_premium_pct": vwap_premium,
            "vwap_trend_3d_pct": vwap_trend_3d,
            "volume_trend_pct": volume_trend,
            "avg_daily_volume": avg_volume_7d,
            "data_points": len(daily_vwap),
        }


_fetcher = CoinGeckoDataFetcher()


def get_coin_id(symbol: str) -> Optional[str]:
    """Get CoinGecko coin ID from trading symbol."""
    return _fetcher.get_best_coin_id(symbol)


def get_supply_data(coin_id: str) -> dict[str, Any]:
    """Get supply and market metrics."""
    return _fetcher.fetch_supply_metrics(coin_id)


def get_development_data(coin_id: str) -> dict[str, Any]:
    """Get development activity metrics."""
    return _fetcher.fetch_development_metrics(coin_id)


def get_community_data(coin_id: str) -> dict[str, Any]:
    """Get community metrics."""
    return _fetcher.fetch_community_metrics(coin_id)


def get_vwap_analysis(coin_id: str, days: int = 7) -> dict[str, float]:
    """Get VWAP and trend analysis."""
    return _fetcher.calculate_vwap_trends(coin_id, days)


def check_trending_status(coin_id: str) -> bool:
    """Check if coin is currently trending."""
    return _fetcher.check_trending_status(coin_id)


def get_coin_categories(coin_id: str) -> list[str]:
    """Get coin categories."""
    return _fetcher.get_coin_categories(coin_id)
