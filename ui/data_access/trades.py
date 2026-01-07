"""
Data access layer for trade and signal data.
Provides methods to retrieve trade and signal information
from the SQLite database, along with aggregated metrics.
"""

import sqlite3 as sql
import logging


class TradeDataAccess:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        try:
            self.connection = sql.connect(self.db_path)
            logging.info("Database connection established.")
        except sql.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")

    def execute_query(self, query: str, params: tuple = ()):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            logging.info("Query executed successfully.")
            return cursor.fetchall()
        except sql.Error as e:
            logging.error(f"Error executing query: {e}")
            raise

    def get_all_trades(self):
        query = "SELECT * FROM trades"
        result = self.execute_query(query)
        return result

    def get_trades_by_status(self, status: str):
        query = "SELECT * FROM trades WHERE order_status = ?"
        result = self.execute_query(query, (status,))
        return result

    def get_trades_by_symbol(self, symbol: str):
        query = "SELECT * FROM trades WHERE symbol_pair = ?"
        result = self.execute_query(query, (symbol,))
        return result

    def get_all_signals(self):
        query = "SELECT * FROM signals"
        result = self.execute_query(query)
        return result

    def get_trade_metrics_by_symbol(self):
        """
        Calculate comprehensive trading metrics grouped by symbol pair.

        Returns
        -------
        list
            List of dictionaries with symbol and metric data
        """
        query = """
        SELECT
            symbol_pair,
            COUNT(*) as total_trades,
            SUM(CASE
                WHEN exit_fill_price IS NOT NULL AND exit_fill_quantity IS NOT NULL
                THEN (exit_fill_price - entry_fill_price) * exit_fill_quantity
                ELSE 0
            END) as total_pnl,
            AVG(CASE
                WHEN exit_fill_price IS NOT NULL AND entry_fill_price IS NOT NULL AND entry_fill_price > 0
                THEN ((exit_fill_price - entry_fill_price) / entry_fill_price) * 100
                ELSE NULL
            END) as avg_return_pct,
            SUM(CASE
                WHEN exit_fill_price > entry_fill_price THEN 1
                ELSE 0
            END) * 100.0 / COUNT(*) as win_rate_pct,
            AVG(quantity * entry_fill_price) as avg_position_size,
            COUNT(CASE WHEN exit_fill_price IS NOT NULL THEN 1 END) as closed_trades,
            COUNT(CASE WHEN exit_fill_price IS NULL THEN 1 END) as open_trades,
            AVG(CASE
                WHEN closed_at IS NOT NULL AND opened_at IS NOT NULL
                THEN (julianday(closed_at) - julianday(opened_at)) * 24
                ELSE NULL
            END) as avg_duration_hours
        FROM trades
        WHERE entry_fill_price IS NOT NULL
        GROUP BY symbol_pair
        ORDER BY symbol_pair
        """
        result = self.execute_query(query)

        # Convert to list of dictionaries for easier handling
        columns = [
            "symbol_pair",
            "total_trades",
            "total_pnl",
            "avg_return_pct",
            "win_rate_pct",
            "avg_position_size",
            "closed_trades",
            "open_trades",
            "avg_duration_hours",
        ]

        return [dict(zip(columns, row)) for row in result]

    def get_signal_metrics_by_symbol(self):
        """
        Calculate signal generation metrics grouped by symbol pair.

        Returns
        -------
        list
            List of dictionaries with symbol and signal data
        """
        query = """
        SELECT
            symbol_pair,
            COUNT(*) as total_signals,
            SUM(CASE WHEN signal_type = 'buy' THEN 1 ELSE 0 END) as buy_signals,
            SUM(CASE WHEN signal_type = 'sell' THEN 1 ELSE 0 END) as sell_signals,
            AVG(price) as avg_signal_price,
            COUNT(CASE WHEN processed = 1 THEN 1 END) as processed_signals,
            COUNT(CASE WHEN processed = 0 THEN 1 END) as pending_signals
        FROM signals
        GROUP BY symbol_pair
        ORDER BY symbol_pair
        """
        result = self.execute_query(query)

        columns = [
            "symbol_pair",
            "total_signals",
            "buy_signals",
            "sell_signals",
            "avg_signal_price",
            "processed_signals",
            "pending_signals",
        ]

        return [dict(zip(columns, row)) for row in result]

    def get_ai_decision_metrics_by_symbol(self):
        """
        Calculate AI decision metrics grouped by symbol pair.

        Returns
        -------
        list
            List of dictionaries with symbol and AI decision data
        """
        query = """
        SELECT
            symbol_pair,
            COUNT(*) as total_decisions,
            SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_decisions,
            SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_decisions,
            SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END) as hold_decisions,
            AVG(CASE WHEN confidence = 'high' THEN 3 WHEN confidence = 'medium' THEN 2 WHEN confidence = 'low' THEN 1 END) as avg_confidence_score,
            AVG(risk_score) as avg_risk_score,
            AVG(position_size_pct) as avg_position_size_pct,
            COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_confidence_count,
            COUNT(CASE WHEN confidence = 'medium' THEN 1 END) as medium_confidence_count,
            COUNT(CASE WHEN confidence = 'low' THEN 1 END) as low_confidence_count
        FROM ai_decisions
        GROUP BY symbol_pair
        ORDER BY symbol_pair
        """
        result = self.execute_query(query)

        columns = [
            "symbol_pair",
            "total_decisions",
            "buy_decisions",
            "sell_decisions",
            "hold_decisions",
            "avg_confidence_score",
            "avg_risk_score",
            "avg_position_size_pct",
            "high_confidence_count",
            "medium_confidence_count",
            "low_confidence_count",
        ]

        return [dict(zip(columns, row)) for row in result]

    def get_combined_trading_overview(self):
        """
        Get a comprehensive overview combining trades, signals, and AI decisions.

        Returns
        -------
        list
            List of dictionaries with combined metrics by symbol
        """
        trade_metrics = {
            item["symbol_pair"]: item for item in self.get_trade_metrics_by_symbol()
        }
        signal_metrics = {
            item["symbol_pair"]: item for item in self.get_signal_metrics_by_symbol()
        }
        ai_metrics = {
            item["symbol_pair"]: item
            for item in self.get_ai_decision_metrics_by_symbol()
        }

        all_symbols = (
            set(trade_metrics.keys())
            | set(signal_metrics.keys())
            | set(ai_metrics.keys())
        )

        combined_data = []
        for symbol in all_symbols:
            combined = {
                "symbol_pair": symbol,
                "total_pnl": trade_metrics.get(symbol, {}).get("total_pnl", 0) or 0,
                "avg_return_pct": trade_metrics.get(symbol, {}).get("avg_return_pct", 0)
                or 0,
                "win_rate_pct": trade_metrics.get(symbol, {}).get("win_rate_pct", 0)
                or 0,
                "total_trades": trade_metrics.get(symbol, {}).get("total_trades", 0)
                or 0,
                "avg_position_size": trade_metrics.get(symbol, {}).get(
                    "avg_position_size", 0
                )
                or 0,
                "avg_duration_hours": trade_metrics.get(symbol, {}).get(
                    "avg_duration_hours", 0
                )
                or 0,
                "closed_trades": trade_metrics.get(symbol, {}).get("closed_trades", 0)
                or 0,
                "total_signals": signal_metrics.get(symbol, {}).get("total_signals", 0)
                or 0,
                "signal_conversion_rate": (
                    (trade_metrics.get(symbol, {}).get("total_trades", 0) or 0)
                    * 100.0
                    / max(
                        signal_metrics.get(symbol, {}).get("total_signals", 1) or 1, 1
                    )
                ),
    
                "avg_confidence_score": ai_metrics.get(symbol, {}).get(
                    "avg_confidence_score", 0
                )
                or 0,
                "avg_risk_score": ai_metrics.get(symbol, {}).get("avg_risk_score", 0)
                or 0,
                "total_decisions": ai_metrics.get(symbol, {}).get("total_decisions", 0)
                or 0,
            }
            combined_data.append(combined)

        return combined_data
