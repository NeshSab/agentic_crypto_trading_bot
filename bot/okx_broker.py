"""
OKX Broker module for interacting with OKX exchange API.

This module defines the OkxBroker class, which encapsulates methods for
fetching market data, account balances, placing orders, and managing
stop-loss and take-profit orders using the OKX API.
"""

import okx.MarketData as MarketData
import okx.Trade as Trade
import okx.Account as Account
import logging
import requests


class OkxBroker:
    def __init__(self, config, db_manager_obj):
        self.marketAPI = MarketData.MarketAPI(flag=config.flag)
        self.accountAPI = Account.AccountAPI(
            api_key=config.api_key,
            api_secret_key=config.secret_key,
            passphrase=config.passphrase,
            use_server_time=False,
            flag=config.flag,
            domain="https://my.okx.com/",
        )
        self.tradeAPI = Trade.TradeAPI(
            api_key=config.api_key,
            api_secret_key=config.secret_key,
            passphrase=config.passphrase,
            use_server_time=False,
            flag=config.flag,
            domain="https://my.okx.com/",
        )
        self.db_manager = db_manager_obj
        logging.info("OkxBroker initialized.")

    def get_current_price(self, symbol):
        try:
            ticker = self.marketAPI.get_ticker(instId=symbol)
            current_price = float(ticker["data"][0]["last"])
            return current_price
        except Exception as e:
            logging.exception(f"Failed to fetch current price for {symbol}: {e}")
            return None

    def get_balance(self, symbol, currency_type):
        try:
            if currency_type == "base":
                fetch_balance_currency = symbol.split("-")[0]
            else:
                fetch_balance_currency = symbol.split("-")[1]

            balances = self.accountAPI.get_account_balance()
            for asset in balances["data"][0]["details"]:
                total = float(asset["availBal"])
                if asset["ccy"] == fetch_balance_currency:
                    if total > 0:
                        return total
                    else:
                        return 0
        except Exception as e:
            logging.exception(f"Failed to fetch balance: {e}")
            return None

    def get_total_capital_usd(self):
        """
        Fetches and returns the total account balance in USD.
        Each asset is has only equivalent in USD, but not in EUR.
        """
        try:
            balances = self.accountAPI.get_account_balance()
            total_assets_usd = 0
            for asset in balances["data"][0]["details"]:
                asset_usd = float(asset["eqUsd"])
                if asset_usd > 0:
                    total_assets_usd += asset_usd
            return total_assets_usd
        except Exception as e:
            logging.exception(f"Failed to fetch balance in USD: {e}")

    def get_available_euro_balance(self):
        try:
            balances = self.accountAPI.get_account_balance()
            equity_eur = 0
            for asset in balances["data"][0]["details"]:
                ccy = asset["ccy"]
                equity_eur += float(asset["eq"])
                if ccy == "EUR":
                    cash_balance_eur = float(asset["cashBal"])
            return {
                "equity_eur": equity_eur,
                "cash_balance_eur": cash_balance_eur,
            }
        except Exception as e:
            print(f"Failed to fetch EUR equity details: {e}")
            return {"equity_eur": 0, "cash_balance_eur": 0}

    def place_buy_market_order(self, symbol, size):
        try:
            logging.info(f"Placing market buy order for {symbol} of size {size}")
            order = self.tradeAPI.place_order(
                instId=symbol,
                tdMode="cash",
                side="buy",
                ordType="market",
                sz=size,
            )
            return order

        except Exception as e:
            logging.exception(f"Market order error: {e}")

    def get_order_details(self, order_id, symbol):
        try:
            order = self.tradeAPI.get_order(instId=symbol, ordId=order_id)
            return order
        except Exception as e:
            print(f"Failed to fetch order details: {e}")
            return None

    def get_filled_orders(self, active_orders):
        filled_orders = []
        other_orders = []
        canceled_orders = []
        try:
            for order_id, symbol_pair in active_orders:
                result = self.tradeAPI.get_order(instId=symbol_pair, ordId=order_id)
                if result["code"] == "0":
                    status = result["data"][0].get("state")
                    fail_code = result["data"][0].get("failCode")
                    if status == "filled" and fail_code is None:
                        filled_orders.append((order_id, result))
                    elif status == "canceled" or status == "mmp_canceled":
                        canceled_orders.append(order_id)
                    else:
                        other_orders.append(order_id)
                else:
                    logging.warning(
                        f"Failed to get info on successful order: {order_id}"
                    )
            return filled_orders, other_orders, canceled_orders
        except Exception as e:
            logging.exception(f"Order status retrieving error: {e}")
            return None, None, None

    def place_stop_loss_sell_order(self, symbol, entry_size, initial_stop_loss_price):
        try:
            algo_id = self.place_conditional_sl_market_order(
                symbol=symbol,
                size=entry_size,
                trigger_price=initial_stop_loss_price,
                side="sell",
            )
            return algo_id
        except Exception as e:
            logging.exception(f"Failed to place stop loss for {symbol}: {e}")
            return None

    def place_conditional_sl_market_order(self, symbol, size, trigger_price, side):
        order_type = "conditional"
        min_order = self.get_min_trade_size(symbol)
        while size >= min_order:
            try:
                order = self.tradeAPI.place_algo_order(
                    instId=symbol,
                    tdMode="cash",
                    side=side,
                    ordType=order_type,
                    sz=str(size),
                    slTriggerPx=str(trigger_price),
                    slOrdPx="-1",
                    slTriggerPxType="last",
                )
                if order["code"] == "0":
                    algo_id = order["data"][0]["algoId"]
                    logging.info(f"✅ Algo order placed: {order}")
                    return algo_id
                elif order["code"] == "1":
                    logging.warning(
                        f"Not enough funds. Reducing size and retrying. "
                        f"Current size: {size}"
                    )
                    size *= 0.995
                    continue
                else:
                    logging.error(f"Algo order for {symbol} failed: {order}")
                    return None
            except Exception as e:
                logging.exception(f"Algo order error: {e}")
                return None

    def get_successful_algo_orders(self, algo_ids):
        effective_algos = []
        live_algos = []
        other_algos = []
        effective_failed_tp_algos = []
        try:
            for algo_id, symbol_pair in algo_ids:
                result = self.tradeAPI.get_algo_order_details(algoId=algo_id)
                if result["code"] == "0":
                    status = result["data"][0].get("state")
                    fail_code = result["data"][0].get("failCode")
                    if status == "live":
                        live_algos.append((algo_id, symbol_pair))
                    elif status == "effective":
                        if fail_code != "0":
                            effective_failed_tp_algos.append((algo_id, symbol_pair))
                            if fail_code != "51008":
                                logging.warning(
                                    f"Fail code of effective order {fail_code} {algo_id}"
                                )
                        else:
                            effective_algos.append((algo_id, symbol_pair))
                    else:
                        other_algos.append((algo_id, symbol_pair))
                else:
                    logging.warning(
                        f"Failed to get info on successful order: {algo_id}"
                    )
            return live_algos, effective_algos, other_algos, effective_failed_tp_algos
        except Exception as e:
            logging.exception(f"Order status retrieving error: {e}")
            return None, None, None

    def process_sl_order(self, data_fetcher, sl_algo_id, symbol):
        try:
            result = self.tradeAPI.get_algo_order_details(algoId=sl_algo_id)
            if result["code"] != "0":
                logging.warning(
                    f"Getting algo order details failed for algoId: {sl_algo_id}"
                )
                return None
            else:
                data = result.get("data", [])
                sl_trigger_price = float(data[0].get("slTriggerPx"))
                current_price = self.get_current_price(symbol)

                if current_price is None or sl_trigger_price is None:
                    logging.warning(
                        f"Missing 'last' or 'slTriggerPx' in response: {data[0]}"
                    )
                    return None
                else:
                    try:
                        df = data_fetcher.fetch_candles(
                            symbol=symbol, bar="1m", limit=5
                        )
                        last_price = float(df["high"].max())
                    except Exception as e:
                        logging.exception(
                            f"Failed to fetch candles for {symbol} in process_sl_order: "
                            f"{e}"
                        )
                        last_price = float(current_price)

                    self.db_manager.connect()
                    buy_order_fill_price = self.db_manager.get_entry_price_by_algo_id(
                        sl_algo_id
                    )
                    self.db_manager.close()
                    new_trigger_price = self.custom_stop_loss_logic(
                        last_price, buy_order_fill_price
                    )

                    if new_trigger_price > sl_trigger_price:
                        success = self.amend_conditional_order(
                            symbol,
                            sl_algo_id,
                            new_trigger_price,
                        )
                        if success:
                            return new_trigger_price
        except Exception as e:
            logging.exception(
                f"Error occurred while checking sl trigger price for {sl_algo_id}, {e}"
            )

    def amend_conditional_order(
        self,
        symbol,
        algo_id,
        new_trigger_price,
    ):
        try:
            amend_result = self.tradeAPI.amend_algo_order(
                instId=symbol,
                algoId=algo_id,
                newSlTriggerPx=str(new_trigger_price),
            )
            if amend_result["code"] == "0":
                status = "amended"
                logging.info(
                    f"✅ SL order amended: {algo_id} with price {new_trigger_price:.1f}"
                )
                return True
            else:
                status = amend_result["msg"]
                logging.warning(
                    f"Amend order failed: {status}. Response: {amend_result}"
                )
                return False
        except Exception as e:
            logging.exception(f"Amend order error: {e}")
            return False

    def get_algo_order_execution_details(self, algo_id, symbol):
        try:
            result_algo = self.tradeAPI.get_algo_order_details(algoId=algo_id)
            if result_algo["code"] == "0":
                algo_details = result_algo["data"][0]
                symbol = algo_details["instId"]
                order_type = algo_details["ordType"]
                if order_type == "move_order_stop":
                    result_algos_hist = self.tradeAPI.order_algos_history(
                        algoId=algo_id, ordType=order_type
                    )
                    order_id = result_algos_hist["data"][0]["ordId"]
                else:
                    order_id = algo_details["ordId"]
                result = self.tradeAPI.get_order(instId=symbol, ordId=order_id)
                size = None
                price = None
                if result["code"] == "0":
                    order_details = result["data"][0]
                    size = float(order_details["accFillSz"])
                    price = float(order_details["avgPx"])
                else:
                    logging.warning(
                        f"Effective algo {algo_id} did not get size and price. "
                        f"Failure code: {result['code']}"
                    )
                    size = None
                    price = None

                return order_id, size, price
            else:
                logging.warning(
                    f"Get execution details code not 0. Might be time out issue. "
                    f"{algo_id}."
                )
        except Exception as e:
            logging.exception(f"Retrieving execution details error: {e}")
            return None, None, None, None

    def cancel_algo_order(self, algo_id, symbol, msg=""):
        try:
            algo_orders = [
                {"instId": symbol, "algoId": algo_id},
            ]
            order = self.tradeAPI.cancel_algo_order(algo_orders)
            if order["code"] == "0":
                logging.info(f"✅ Algo order cancelled: {order}")
                return True
            else:
                logging.warning(
                    f"Failed to cancel algo order: {order} | {msg} "
                    f"Consider checking if new stop loss needed."
                )
                return False
        except Exception as e:
            logging.exception(f"Algo order cancellation error: {e}")
            return False

    @staticmethod
    def custom_stop_loss_logic(last_price, buy_order_fill_price):
        if last_price >= buy_order_fill_price * 1.05:
            new_trigger_price = last_price * 0.999
        elif last_price >= buy_order_fill_price * 1.04:
            new_trigger_price = last_price * 0.994
        elif last_price >= buy_order_fill_price * 1.03:
            new_trigger_price = last_price * 0.992
        elif last_price >= buy_order_fill_price * 1.02:
            new_trigger_price = last_price * 0.99
        elif last_price >= buy_order_fill_price * 1.015:
            new_trigger_price = last_price * 0.98
        elif last_price >= buy_order_fill_price * 1.01:
            new_trigger_price = last_price * 0.97
        elif last_price >= buy_order_fill_price * 1.005:
            new_trigger_price = last_price * 0.96
        else:
            new_trigger_price = last_price * 0.95

        return new_trigger_price

    @staticmethod
    def get_min_trade_size(symbol):
        url = (
            f"https://www.okx.com/api/v5/public/instruments?"
            f"instType=SPOT&instId={symbol}"
        )
        try:
            response = requests.get(url)
            data = response.json()
            if data["code"] == "0" and data["data"]:
                instrument = data["data"][0]
                return float(instrument["minSz"])
            else:
                logging.warning(f"Failed to fetch instrument details for {symbol}")
        except Exception as e:
            logging.exception(
                f"Error fetching minimum required trade size with request: {e}"
            )
