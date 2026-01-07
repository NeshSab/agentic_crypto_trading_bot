"""
Bot engine module for managing the trading bot's main loop.

This module defines the BotEngine class, which orchestrates the main
trading loop, including data fetching, signal generation, trade execution,
and order monitoring.
"""

import logging
import time
from datetime import datetime, timezone

from ai.ai_agent import evaluate_trade


class BotEngine:
    def __init__(
        self,
        config,
        logger,
        db_manager,
        data_fetcher,
        signal_generator,
        trade_executor,
        order_monitor,
        broker,
    ):
        self.config = config
        self.logger = logger
        self.db_manager_obj = db_manager
        self.data_fetcher = data_fetcher
        self.signal_generator = signal_generator
        self.trade_executor = trade_executor
        self.order_monitor = order_monitor
        self.broker = broker

    def run(self):
        last = datetime.now(timezone.utc)
        logging.info(f"OOP Trading Bot Started at {last.isoformat()}")
        while True:
            now = datetime.now(timezone.utc)
            minute = now.minute
            hour = now.hour
            final_signal = "hold"
            strategy_name = ""

            if (
                hour % (self.config.ema_signal_check_frequency / 60) == 0
                and minute == 1
            ):
                for symbol in self.config.symbols:
                    try:
                        fast_df = self.data_fetcher.fetch_candles_with_indicators(
                            symbol=symbol,
                            bar=self.config.fast_bar,
                            limit=self.config.ema_limit,
                            params=self.config.strategy_params,
                        )
                        last_candle = fast_df["ts"].iloc[-1]
                        last_candle_hour = last_candle.hour
                        if last_candle_hour == hour:
                            fast_df = fast_df[:-1]

                        confirm_df = self.data_fetcher.fetch_candles_with_indicators(
                            symbol=symbol,
                            bar=self.config.confirm_bar,
                            limit=self.config.ema_limit,
                            params=self.config.strategy_params,
                        )
                        last_confirm_candle = confirm_df["ts"].iloc[-1]
                        last_confirm_candle_hour = last_confirm_candle.hour
                        if last_confirm_candle_hour == hour:
                            confirm_df = confirm_df[:-1]

                        if (
                            fast_df is None
                            or fast_df.empty
                            or confirm_df is None
                            or confirm_df.empty
                        ):
                            logging.warning(f"No candle data for {symbol}, skipping.")
                            continue

                        signal_metrics = (
                            self.signal_generator.evaluate_ema_crossover_with_metrics(
                                fast_df, confirm_df
                            )
                        )

                        logging.info(f"Signal metrics for {symbol}: {signal_metrics}")
                        if signal_metrics is None:
                            logging.info(f"No signal generated for {symbol}, skipping.")
                            continue
                        else:
                            signal_direction = signal_metrics["signal"]

                        if signal_direction == "bullish":
                            final_signal = "buy"
                        elif signal_direction == "bearish":
                            final_signal = "sell"
                        else:
                            logging.info(f"No valid signal for {symbol}, skipping.")
                            continue

                        strategy_name = "EMA_Strategy"
                        logging.info(
                            f"Final signal for {symbol}: {final_signal}, "
                            f"strategy: {strategy_name}"
                        )

                        confirmation_indicators = (
                            self.signal_generator.check_confirmations(
                                confirm_df,
                                signal_direction,
                            )
                        )

                        current_price = self.broker.get_current_price(symbol)

                        params = {
                            "symbol_pair": symbol,
                            "signal_type": final_signal,
                            "price": current_price,
                            "ema_metrices": str(signal_metrics["ema_metrics"]),
                            "confirmation_metrices": str(confirmation_indicators),
                            "strategy": strategy_name,
                            "processed": 0,
                        }
                        self.db_manager_obj.connect()
                        self.db_manager_obj.log_signal(params)
                        signal_id = self.db_manager_obj.get_latest_signal_id_for_symbol(
                            symbol_pair=symbol,
                        )
                        self.db_manager_obj.close()

                        signal_context = {
                            "symbol_pair": symbol,
                            "signal_type": final_signal,
                            "price": current_price,
                            "strategy": strategy_name,
                            "detected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        signal_context.update(self.config.strategy_params)
                        signal_context.update(signal_metrics["ema_metrics"])
                        signal_context.update(confirmation_indicators)

                        try:
                            logging.info(
                                f"Evaluating trade for {symbol} with AI agent."
                            )
                            trade_evaluation = evaluate_trade(signal_context, signal_id)
                            ai_approval, ai_suggested_allocation = trade_evaluation
                        except Exception as e:
                            logging.error(
                                f"Error processing AI evaluation for {symbol}: {e}"
                            )
                            continue

                        logging.info(f"AI decision for {symbol}: {ai_approval}")

                        if ai_approval not in ["BUY", "SELL"]:
                            logging.info(
                                f"Trade for {symbol} was not confirmed "
                                f"by AI risk manager."
                            )
                            continue
                        else:
                            final_signal = ai_approval.lower()

                        logging.info(
                            f"Attempting to execute {final_signal} for {symbol}"
                        )

                        if final_signal == "buy":
                            order_id, quantity = self.trade_executor.execute(
                                symbol=symbol,
                                signal=final_signal,
                                current_price=current_price,
                                ai_position_sizing=ai_suggested_allocation,
                            )
                            if order_id is None:
                                logging.info(f"Buy order for {symbol} was not placed.")
                                continue

                            self.db_manager_obj.connect()

                            ai_decision_id = self.db_manager_obj.get_latest_ai_decision_id_for_symbol(
                                symbol_pair=symbol
                            )

                            usef_config_id = (
                                self.db_manager_obj.get_current_active_user_configs_id()
                            )

                            trade_params = {
                                "entry_order_id": order_id,
                                "signal_id": signal_id,
                                "ai_decision_id": ai_decision_id,
                                "user_config_id": usef_config_id,
                                "symbol_pair": symbol,
                                "side": final_signal,
                                "quantity": quantity,
                                "entry_price": current_price,
                                "initial_stop_loss": (
                                    current_price
                                    * self.config.buy_stop_loss_pct_multiplier
                                ),
                                "order_status": "submitted_buy",
                            }
                            self.db_manager_obj.log_trade(trade_params)
                            self.db_manager_obj.close()

                    except Exception as e:
                        logging.exception(f"Error processing {symbol}: {e}")

            self.order_monitor.monitor(self.data_fetcher)

            now_check = datetime.now(timezone.utc)
            seconds_to_next_minute = (
                60 - now_check.second - now_check.microsecond / 1000000
            )
            time.sleep(seconds_to_next_minute)

            delta = (now_check - last).total_seconds()
            if delta > self.config.pause_threshold_seconds:
                logging.warning(
                    f"Sleep or pause detected! Gap of {delta:.1f} "
                    f"seconds at {now_check.isoformat()}"
                )
            last = now_check
