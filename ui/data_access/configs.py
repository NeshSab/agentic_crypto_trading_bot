"""
Data access layer for configuration management.
Provides methods to retrieve and update user and symbol configurations
from the SQLite database.
"""

import sqlite3 as sql
import logging
from common_utils.utils import current_date_utc


class ConfigDataAccess:
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

    def get_current_configs(self):
        query = """
        SELECT * FROM user_config WHERE usage = 1
        ORDER BY added_at DESC LIMIT 1
        """
        result = self.execute_query(query)
        return result[0] if result else None

    def update_discontinued_config_by_id(self, config_id: int, params: dict):
        usage = 0
        discontinued_date = params.get("discontinued_date")
        if discontinued_date is None:
            discontinued_date = current_date_utc()
        query = "UPDATE user_config SET usage = ?, discontinued_at = ? WHERE id = ?"
        self.execute_query(query, (usage, discontinued_date, config_id))

    def set_new_config_as_current(self, params: dict):
        usage = 1
        ai_persona = params.get("ai_persona")
        fast_window = params.get("fast_window")
        slow_window = params.get("slow_window")
        confirmation_indicator_window = params.get("confirmation_indicator_window")
        atr_window = params.get("atr_window")
        atr_multiplier = params.get("atr_multiplier")
        date_added = params.get("date_added")
        if date_added is None:
            date_added = current_date_utc()
        query = """
        INSERT INTO user_config (ai_persona, fast_window, slow_window,
        confirmation_indicator_window, atr_window, atr_multiplier,
        usage, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            ai_persona,
            fast_window,
            slow_window,
            confirmation_indicator_window,
            atr_window,
            atr_multiplier,
            usage,
            date_added,
        )
        self.execute_query(query, params)

    def get_current_active_symbol_configs(self):
        query = """SELECT * FROM symbol_config WHERE usage = 1"""
        result = self.execute_query(query)
        return result if result else []

    def update_discontinued_symbol_config_by_id(self, symbol_id: int, params: dict):
        usage = 0
        discontinued_date = params.get("discontinued_date")
        if discontinued_date is None:
            discontinued_date = current_date_utc()
        query = "UPDATE symbol_config SET usage = ?, discontinued_at = ? WHERE id = ?"
        self.execute_query(query, (usage, discontinued_date, symbol_id))

    def set_new_symbol_config_as_current(self, params: dict):
        usage = 1
        symbol_pair = params.get("symbol_pair")
        max_allocation = params.get("max_allocation")
        date_added = params.get("date_added")
        if date_added is None:
            date_added = current_date_utc()
        query = """
        INSERT INTO symbol_config (symbol_pair, max_allocation,
        usage, added_at)
        VALUES (?, ?, ?, ?)
        """
        params = (
            symbol_pair,
            max_allocation,
            usage,
            date_added,
        )
        self.execute_query(query, params)
