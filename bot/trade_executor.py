"""
Trade execution module for handling buy and sell orders based on trading signals.

This module defines the TradeExecutor class, which interacts with a broker's API
to place market orders according to received trading signals. It includes methods
for executing trades, handling buy and sell signals, and managing position sizing.
"""

import logging


class TradeExecutor:
    def __init__(self, broker, db_manager, config):
        self.accountAPI = broker.accountAPI
        self.tradeAPI = broker.tradeAPI
        self.config = config
        self.broker = broker
        self.db_manager = db_manager
        logging.info("TradeExecutor initialized.")

    def execute(self, symbol, signal, current_price, ai_position_sizing=None):
        logging.info(f"Executing trade for {symbol}: {signal} at {current_price}")
        try:
            if signal == "buy":
                order_id, quantity = self._buy_signal_order(
                    symbol,
                    current_price,
                    ai_position_sizing,
                )
                return order_id, quantity
            elif signal == "sell":
                order_id, quantity = self._sell_signal_order(
                    symbol,
                    current_price,
                )
                return order_id, quantity
            else:
                logging.info(f"No trade executed for {symbol}: signal is {signal}")
                return None, None
        except Exception as e:
            logging.error(f"Trade execution failed for {symbol}: {e}")
            return None, None

    def _buy_signal_order(
        self,
        symbol: str,
        current_price: float,
        ai_position_sizing: float = None,
    ):
        try:
            base_balance = self.broker.get_balance(symbol, "base")
            base_balance_eur = base_balance * current_price

            euro_value = self.broker.get_available_euro_balance()
            total_capital = euro_value.get("equity_eur", 0)
            available_capital = euro_value.get("cash_balance_eur", 0)
            base_balance_percentage = base_balance_eur / total_capital
            max_allocation_allowed_pct = self.config.max_allocation.get(symbol, 0) / 100

            if base_balance_percentage >= max_allocation_allowed_pct * 0.99:
                logging.info(
                    f"Max allocation reached for {symbol}. No buy order placed."
                )
                return None, None

            max_allocation_pct = max_allocation_allowed_pct - base_balance_percentage

            if ai_position_sizing is not None:
                logging.info(
                    f"Suggested AI position sizing for {symbol}: {ai_position_sizing}, "
                    f" final sizing: {max_allocation_pct} - determined by max allocation."
                )

            allocate_max_current_trade_euro = max_allocation_pct * available_capital

            allocate_current_trade_base = (
                allocate_max_current_trade_euro / current_price
            )

            min_trade_size = self.broker.get_min_trade_size(symbol)

            if allocate_current_trade_base > min_trade_size:
                order = self.broker.place_buy_market_order(
                    symbol=symbol,
                    size=allocate_max_current_trade_euro,
                )
                if order["code"] == "0":
                    logging.info(
                        f"Buy order placed for {symbol}: "
                        f"Size: {allocate_current_trade_base} at trigger price "
                        f"{current_price}"
                    )
                    return order["data"][0]["ordId"], allocate_current_trade_base
                else:
                    logging.error(f"Failed to place buy order for {symbol}.")
                    return None, None
            else:
                logging.info(
                    f"Calculated trade size for {symbol} is below minimum trade size. "
                    f"No buy order placed."
                )
                return None, None

        except Exception as e:
            logging.exception(f"Error reacting to buy signal: {e}")
            return None, None

    def _sell_signal_order(
        self,
        symbol,
        current_price,
    ):
        logging.info(
            f"Placeholder: Placing sell order for {symbol} at price {current_price}"
        )
        return None, None
