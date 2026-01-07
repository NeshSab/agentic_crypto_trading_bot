"""
Trading bot main execution script.

Initializes and runs the trading bot with all necessary components, including
configuration management, database handling, data fetching, signal generation,
trade execution, and order monitoring.
"""

import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_ENV = os.getenv("OPENAI_API_KEY", "")
USER_AGENT_ENV = os.getenv("USER_AGENT", "")
os.environ["USER_AGENT"] = USER_AGENT_ENV
os.environ["OPENAI_API_KEY"] = OPENAI_ENV

from config_manager import ConfigManager
from database_manager import DatabaseManager
from logger_manager import LoggerManager
from signal_generator import SignalGenerator
from data_fetcher import DataFetcher
from okx_broker import OkxBroker
from bot_engine import BotEngine
from bot.trade_executor import TradeExecutor
from bot.order_monitor import OrderMonitor


def main():
    print("Starting trading bot...")
    db_path = "../storage/trading.db"
    log_path = "../storage/logs/bot.log"

    logger = LoggerManager(log_path)
    db_manager = DatabaseManager(db_path)
    config = ConfigManager(db_manager)

    broker = OkxBroker(config, db_manager)
    data_fetcher = DataFetcher(broker)
    signal_generator = SignalGenerator(config)

    trade_executor = TradeExecutor(broker, db_manager, config)
    order_monitor = OrderMonitor(broker, db_manager, config)

    bot = BotEngine(
        config,
        logger,
        db_manager,
        data_fetcher,
        signal_generator,
        trade_executor,
        order_monitor,
        broker,
    )
    bot.run()


if __name__ == "__main__":
    main()
