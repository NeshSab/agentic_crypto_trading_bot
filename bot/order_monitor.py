"""
Order monitoring module for handling buy, take profit, and stop loss orders.

This module defines the OrderMonitor class, which interacts with a broker's API
to monitor the status of buy orders and take profit/stop loss orders. It includes
methods for monitoring buy orders, take profit/stop loss orders, and updating
the database accordingly.
"""

import logging
import time
from okx_broker import OkxBroker


class OrderMonitor:
    def __init__(self, broker, db_manager, config):
        self.tradeAPI = broker.tradeAPI
        self.accountAPI = broker.accountAPI
        self.broker = broker
        self.db_manager = db_manager
        self.symbols = config.symbols
        self.config = config
        logging.info("OrderMonitor initialized.")

    def monitor_buy_orders(self):
        """
        Monitor buy orders and handle filled and canceled orders.

        Once a buy order is filled, update the trade in the database
        with the entry fill details and place a stop-loss order.
        If a buy order is canceled, update the trade status accordingly.
        """
        try:
            self.db_manager.connect()
            active_orders = self.db_manager.get_entry_orders_ids_by_status(
                order_status="submitted_buy"
            )
            self.db_manager.close()
            if active_orders:
                logging.info(f"Open order ids: {active_orders}")
            filled_orders, other_orders, canceled_orders = (
                self.broker.get_filled_orders(
                    active_orders=active_orders,
                )
            )
            if filled_orders:
                logging.info(f"Filled buy orders: {filled_orders}")
            if canceled_orders:
                logging.info(f"Canceled buy orders: {canceled_orders}")
            if other_orders:
                logging.warning(
                    f"Other buy orders (NEEDS INVESTIGATION): {other_orders}"
                )
            for filled_order_id, result in filled_orders:
                logging.info("checking affective algo ids in order to place tp/sl")
                symbol = result["data"][0]["instId"]
                entry_size = float(result["data"][0]["accFillSz"])
                base_entry_price = float(result["data"][0]["avgPx"])
                try:
                    self.db_manager.connect()
                    self.db_manager.update_trade_with_entry_fill(
                        filled_order_id, "filled_buy", base_entry_price, entry_size
                    )
                    self.db_manager.close()
                except Exception as e:
                    logging.exception(
                        f"Failed to update trade for {filled_order_id}: {e}"
                    )
                    continue

                try:
                    balance = float(self.broker.get_balance(symbol, "base"))
                    entry_size = balance
                except Exception as e:
                    logging.exception(
                        f"Failed to fetch {symbol} balance in monitor_buy_orders: {e} "
                        f" Using entry size from filled order: {entry_size}"
                    )

                try:
                    logging.info(
                        f"Placing stop loss order... with {base_entry_price} "
                        f"and {self.config.buy_stop_loss_pct_multiplier}"
                    )
                    initial_stop_loss_price = (
                        base_entry_price * self.config.buy_stop_loss_pct_multiplier
                    )
                    logging.info("all good")
                    exit_algo_order_id = self.broker.place_stop_loss_sell_order(
                        symbol,
                        entry_size,
                        initial_stop_loss_price,
                    )
                    if exit_algo_order_id is not None:
                        self.db_manager.connect()
                        self.db_manager.update_trade_status_with_exit_algo_order(
                            filled_order_id,
                            "placed_stop_loss",
                            exit_algo_order_id,
                            initial_stop_loss_price,
                        )
                        self.db_manager.close()
                    else:
                        logging.warning(
                            f"Stop loss order placement failed for {filled_order_id}"
                        )
                except Exception as e:
                    logging.warning(f"Buy order {filled_order_id} failed: {e}")

            for canceled_order_id in canceled_orders:
                try:
                    self.db_manager.connect()
                    self.db_manager.update_trade_with_entry_fill(
                        "-1", "canceled_buy", 0.0, 0.0
                    )
                    self.db_manager.close()
                except Exception as e:
                    logging.exception(
                        f"Failed to update canceled trade for {canceled_order_id}: {e}"
                    )
                    continue
        except Exception as e:
            self.db_manager.close()
            logging.exception(f"Error monitoring BUY orders: {e}")

    def monitor_tp_sl_orders(self, data_fetcher):
        """
        Monitor take profit and stop loss orders.
        Effective orders are logged.
        Live orders are checked for stop loss adjustments.

        Parameters
        ----------
        data_fetcher : DataFetcher
            Instance of DataFetcher to retrieve market data.
        """
        try:
            self.db_manager.connect()
            active_algo_ids = self.db_manager.get_exit_algo_ids_by_status(
                order_status="placed_stop_loss"
            )
            self.db_manager.close()
            if active_algo_ids:
                logging.info(f"Active TP/SL algo ids: {active_algo_ids}")
            (
                live_tp_algos,
                effective_tp_algos,
                other_tp_algos,
                effective_failed_tp_algos,
            ) = self.broker.get_successful_algo_orders(
                algo_ids=active_algo_ids,
            )
            for live_algo_id, symbol in live_tp_algos:
                new_stop_loss = self.broker.process_sl_order(
                    data_fetcher,
                    live_algo_id,
                    symbol,
                )
                if new_stop_loss is not None:
                    try:
                        self.db_manager.connect()
                        self.db_manager.update_stop_loss(live_algo_id, new_stop_loss)
                        self.db_manager.close()
                    except Exception as e:
                        logging.exception(
                            f"Failed to update stop loss price in DB for "
                            f"{live_algo_id}: {e}"
                        )

            for effective_algo_id, symbol in effective_tp_algos:
                order_id, exit_fill_size, exit_fill_price = (
                    self.broker.get_algo_order_execution_details(
                        effective_algo_id, symbol
                    )
                )
                self.db_manager.connect()
                self.db_manager.update_trade_status_position_closed(
                    effective_algo_id,
                    "closed",
                    exit_fill_price,
                    exit_fill_size,
                    order_id,
                )
                self.db_manager.close()

            for algo_id, symbol in other_tp_algos + effective_failed_tp_algos:
                logging.warning(
                    f"TP/SL algo {algo_id} for {symbol} requires manual investigation."
                )
                base_balance = (
                    self.broker.get_balance(symbol, "base")
                    if self.broker is not None
                    else 0
                )
                min_order = OkxBroker.get_min_trade_size(symbol)
                if base_balance > min_order:
                    logging.info(
                        f"New stop loss order for {algo_id} on {symbol} "
                        f"with base size {base_balance} should be placed. "
                        f"Add it as new row in the trades table."
                    )
        except Exception as e:
            self.db_manager.close()
            logging.exception(f"Error monitoring TAKE PROFIT AND STOP LOSS orders: {e}")

    def monitor(self, data_fetcher):
        logging.info("Monitoring orders...")
        try:
            logging.info("Monitor buy orders...")
            self.monitor_buy_orders()
            time.sleep(5)
            logging.info("Monitor tp sl orders...")
            self.monitor_tp_sl_orders(data_fetcher)
            time.sleep(5)

            logging.info("Order monitoring complete.\n")
        except Exception as e:
            logging.error(f"Order monitoring failed: {e}")
