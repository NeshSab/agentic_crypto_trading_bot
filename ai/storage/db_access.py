"""
Database access layer for AI decision logging and retrieval.

This module provides a DatabaseAccess class to handle connections and
operations on the SQLite database used for logging AI decisions and retrieving
unprocessed signals. It encapsulates methods for connecting to the database,
executing queries, and specific operations related to AI decision data.
"""

import logging
import sqlite3 as sql
from common_utils.utils import current_date_utc


class DatabaseAccess:
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

    def get_unprocessed_signals(self):
        query = "SELECT * FROM signals WHERE processed = 0"
        return self.execute_query(query)

    def log_ai_decision(self, decision_data: dict):
        query = """
        INSERT INTO ai_decisions (signal_id, user_configs_id, symbol_pair,
        fast_timeframe, slow_timeframe, strategy, signal, action,
        confidence, risk_score, position_size_pct, stop_loss_pct, take_profit_pct,
        rationale, key_factors, source, model_name, tools_used, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        created_at = current_date_utc()
        params = (
            decision_data.get("signal_id"),
            decision_data.get("user_configs_id"),
            decision_data.get("symbol_pair"),
            decision_data.get("fast_timeframe"),
            decision_data.get("slow_timeframe"),
            decision_data.get("strategy"),
            decision_data.get("signal"),
            decision_data.get("action"),
            decision_data.get("confidence"),
            decision_data.get("risk_score"),
            decision_data.get("position_size_pct"),
            decision_data.get("stop_loss_pct"),
            decision_data.get("take_profit_pct"),
            decision_data.get("rationale"),
            decision_data.get("key_factors"),
            decision_data.get("source"),
            decision_data.get("model_name"),
            decision_data.get("tools_used"),
            created_at,
        )
        self.execute_query(query, params)

    def get_ai_decision_by__signal_id(self, signal_id: int):
        query = "SELECT * FROM ai_decisions WHERE signal_id = ?"
        return self.execute_query(query, (signal_id,))

    def get_current_ai_persona(self):
        query = """
        SELECT ai_persona FROM user_config WHERE usage = 1
        ORDER BY added_at DESC LIMIT 1
        """
        result = self.execute_query(query)
        return result[0][0] if result else None

    def get_current_user_configs_id(self):
        query = """
        SELECT id FROM user_config WHERE usage = 1
        ORDER BY added_at DESC LIMIT 1
        """
        result = self.execute_query(query)
        return result[0][0] if result else None
