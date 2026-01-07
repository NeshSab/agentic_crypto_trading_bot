"""
Configuration manager module for handling bot settings and parameters.

This module defines the ConfigManager class, which loads configuration
parameters from environment variables and a database. It sets up trading
symbols, strategy parameters, and risk management settings.
"""

import os
from dotenv import load_dotenv


class ConfigManager:
    def __init__(self, db_manager_obj):
        load_dotenv()

        self.api_key = os.getenv("OKX_API_KEY")
        self.secret_key = os.getenv("OKX_SECRET_KEY")
        self.passphrase = os.getenv("OKX_PASSPHRASE")
        self.flag = "0"

        self.pause_threshold_seconds = 90
        self.min_to_check_log_portfolio = [59, 14, 29, 44]

        self.fast_bar = "1H"
        self.confirm_bar = "4H"
        self.ema_signal_check_frequency = 240

        db_manager_obj.connect()

        db_config = db_manager_obj.get_current_active_user_config()
        if db_config:
            (
                _id,
                ai_persona,
                fast_window,
                slow_window,
                confirmation_indicator_window,
                atr_window,
                atr_multiplier,
                _usage,
                _added_at,
                _discontinued_at,
            ) = db_config
        else:
            ai_persona = "Sherlock Holmes"
            fast_window = 9
            slow_window = 21
            confirmation_indicator_window = 9
            atr_window = 7
            atr_multiplier = 3.0

        self.strategy_params = {
            "fast_window": fast_window,
            "slow_window": slow_window,
            "confirmation_indicator_window": confirmation_indicator_window,
            "atr_window": atr_window,
            "atr_multiplier": atr_multiplier,
        }
        self.ai_persona = ai_persona

        bars_needed = (
            max(fast_window, slow_window)
            + max(confirmation_indicator_window, atr_window)
            + 5
        )
        self.ema_limit = bars_needed if bars_needed > 100 else 100

        symbol_configs_table = db_manager_obj.get_current_active_symbol_configs()
        if symbol_configs_table:
            symbol_configs = {}
            for symbol_config in symbol_configs_table:
                (
                    _id,
                    symbol_pair,
                    max_allocation,
                    _usage,
                    _added_at,
                    _discontinued_at,
                ) = symbol_config
                symbol_configs[symbol_pair] = max_allocation
        else:
            symbol_configs = {"BTC-EUR": 50, "ETH-EUR": 50}

        self.symbols = list(symbol_configs.keys())
        self.max_allocation = symbol_configs

        self.buy_stop_loss_pct_multiplier = 0.95
        self.sell_stop_loss_pct_multiplier = 1.05
        self.okx_fee_rate = 0.0035
