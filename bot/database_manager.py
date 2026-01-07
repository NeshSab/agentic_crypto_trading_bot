"""
Database manager module for handling database operations.

This module defines the DatabaseManager class, which provides methods to
connect to a SQLite database, execute queries, and manage trading signals
and trades.
"""

import logging
import sqlite3 as sql

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common_utils.utils import current_date_utc


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        try:
            self.connection = sql.connect(self.db_path)
        except sql.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: tuple = ()):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.fetchall()
        except sql.Error as e:
            logging.error(f"Error executing query: {e}")
            raise

    def log_signal(self, signal_data: dict):
        query = """
        INSERT INTO signals (symbol_pair, signal_type, price, ema_metrices,
        confirmation_metrices, strategy, detected_at, processed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        detected_at = current_date_utc()
        params = (
            signal_data.get("symbol_pair"),
            signal_data.get("signal_type"),
            signal_data.get("price"),
            signal_data.get("ema_metrices"),
            signal_data.get("confirmation_metrices"),
            signal_data.get("strategy"),
            detected_at,
            signal_data.get("processed"),
        )
        self.execute_query(query, params)

    def update_signal_processed_status_by_id(self, signal_id: int):
        query = "UPDATE signals SET processed = 1 WHERE id = ?"
        self.execute_query(query, (signal_id,))

    def get_unprocessed_signals(self):
        query = "SELECT * FROM signals WHERE processed = 0"
        return self.execute_query(query)

    def get_signal_params_by_id(self, signal_id: int):
        query = "SELECT * FROM signals WHERE id = ?"
        result = self.execute_query(query, (signal_id,))
        return result[0] if result else None

    def log_trade(self, trade_data: dict):
        query = """
        INSERT INTO trades (entry_order_id, signal_id, ai_decision_id, user_config_id,
        symbol_pair, side, quantity, entry_price, initial_stop_loss, order_status,
        opened_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        opened_at = current_date_utc()
        params = (
            trade_data.get("entry_order_id"),
            trade_data.get("signal_id"),
            trade_data.get("ai_decision_id"),
            trade_data.get("user_config_id"),
            trade_data.get("symbol_pair"),
            trade_data.get("side"),
            trade_data.get("quantity"),
            trade_data.get("entry_price"),
            trade_data.get("initial_stop_loss"),
            trade_data.get("order_status"),
            opened_at,
        )
        self.execute_query(query, params)

    def update_trade_with_entry_fill(
        self,
        trade_id: int,
        order_status: str,
        entry_fill_price: float,
        entry_fill_quantity: float,
    ):
        query = """
        UPDATE trades
        SET order_status = ?, entry_fill_price = ?, entry_fill_quantity = ?
        WHERE entry_order_id = ?
        """
        params = (order_status, entry_fill_price, entry_fill_quantity, trade_id)
        self.execute_query(query, params)

    def update_trade_status_with_exit_algo_order(
        self,
        trade_id: int,
        order_status: str,
        exit_algo_id: str = None,
        stop_loss: float = None,
    ):
        query = """
        UPDATE trades
        SET order_status = ?, exit_algo_id = ?, amended_stop_loss = ?
        WHERE entry_order_id = ?
        """
        params = (order_status, exit_algo_id, stop_loss, trade_id)
        self.execute_query(query, params)

    def update_trade_status_position_closed(
        self,
        trade_id: int,
        order_status: str,
        exit_fill_price: float,
        exit_fill_quantity: float,
        exit_order_id: str = None,
    ):
        query = """
        UPDATE trades
        SET order_status = ?, exit_fill_price = ?, exit_fill_quantity = ?,
        exit_order_id = ?, closed_at = ?
        WHERE exit_algo_id = ?
        """
        closed_at = current_date_utc()
        params = (
            order_status,
            exit_fill_price,
            exit_fill_quantity,
            exit_order_id,
            closed_at,
            trade_id,
        )
        self.execute_query(query, params)

    def update_stop_loss(self, trade_id: int, new_stop_loss: float):
        query = """
        UPDATE trades
        SET amended_stop_loss = ?
        WHERE exit_algo_id = ?
        """
        params = (new_stop_loss, trade_id)
        self.execute_query(query, params)

    def get_trade_params_by_id(self, trade_id: int):
        query = "SELECT * FROM trades WHERE entry_order_id = ?"
        result = self.execute_query(query, (trade_id,))
        return result[0] if result else None

    def get_user_config_by_id(self, config_id: int):
        query = "SELECT * FROM user_config WHERE id = ?"
        result = self.execute_query(query, (config_id,))
        return result[0] if result else None

    def get_current_active_user_config(self):
        query = """
        SELECT * FROM user_config WHERE usage = 1
        ORDER BY added_at DESC LIMIT 1
        """
        result = self.execute_query(query)
        return result[0] if result else None

    def get_symbol_config_by_symbol(self, symbol_pair: str):
        query = "SELECT * FROM symbol_config WHERE symbol_pair = ?"
        result = self.execute_query(query, (symbol_pair,))
        return result[0] if result else None

    def get_current_active_symbol_configs(self):
        query = """SELECT * FROM symbol_config WHERE usage = 1"""
        result = self.execute_query(query)
        return result if result else []

    def get_current_active_user_configs_id(self):
        query = """
        SELECT id FROM user_config WHERE usage = 1
        ORDER BY added_at DESC LIMIT 1
        """
        result = self.execute_query(query)
        return result[0][0] if result else None

    def get_latest_signal_id_for_symbol(self, symbol_pair: str):
        query = """
        SELECT id FROM signals
        WHERE symbol_pair = ?
        ORDER BY detected_at DESC
        LIMIT 1
        """
        result = self.execute_query(query, (symbol_pair,))
        return result[0][0] if result else None

    def get_latest_ai_decision_id_for_symbol(self, symbol_pair: str):
        query = """
        SELECT id FROM ai_decisions
        WHERE symbol_pair = ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = self.execute_query(query, (symbol_pair,))
        return result[0][0] if result else None

    def get_entry_orders_ids_by_status(self, order_status: str):
        query = """
        SELECT entry_order_id, symbol_pair FROM trades
        WHERE order_status = ?
        """
        result = self.execute_query(query, (order_status,))
        return [(row[0], row[1]) for row in result] if result else []

    def get_exit_algo_ids_by_status(self, order_status: str):
        query = """
        SELECT exit_algo_id, symbol_pair FROM trades
        WHERE order_status = ?
        """
        result = self.execute_query(query, (order_status,))
        return [(row[0], row[1]) for row in result] if result else []

    def get_entry_price_by_algo_id(self, algo_id: str):
        query = """
        SELECT entry_fill_price FROM trades
        WHERE exit_algo_id = ?
        """
        result = self.execute_query(query, (algo_id,))
        return float(result[0][0]) if result else None
