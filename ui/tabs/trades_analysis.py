"""
Trades Analysis Tab - Comprehensive trading performance visualization and analysis.

This module provides detailed analysis of trading performance across
different symbol pairs, including PnL analysis, win rates, signal conversion rates,
and AI decision quality metrics.
"""

import streamlit as st
import pandas as pd
import os
from ui.data_access.trades import TradeDataAccess
from ui.widgets.charts import create_trades_bar_chart


def render():
    """
    Render the trades analysis tab with comprehensive trading performance analysis.

    Displays interactive charts and detailed metrics tables for trading performance
    across different symbol pairs.
    """
    st.title("📈 Trades Analysis")
    st.markdown(
        """
    Analyze your trading performance across different symbol pairs. 
    Review profitability, signal conversion rates, and AI decision quality.
    """
    )

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        # CHANGE TO trading.db FOR PRODUCTION
        db_path = os.path.join(project_root, "storage", "trading_mockup.db")

        trade_data = TradeDataAccess(db_path)
        trade_data.connect()

        trading_data = trade_data.get_combined_trading_overview()

        if not trading_data:
            st.warning("No trading data found. Start trading to see analysis here.")
            trade_data.close()
            return

        _display_summary_metrics(trading_data)

        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col2:
            st.subheader("Chart Settings")

            metric_options = {
                "Total PnL ($)": "total_pnl",
                "Average Return (%)": "avg_return_pct",
                "Win Rate (%)": "win_rate_pct",
                "Number of Trades": "total_trades",
                "Closed Trades": "closed_trades",
                "Average Position Size ($)": "avg_position_size",
                "Average Duration (Hours)": "avg_duration_hours",
                "Total Signals": "total_signals",
                "Signal Conversion Rate (%)": "signal_conversion_rate",
                "Average Confidence Score": "avg_confidence_score",
                "Average Risk Score": "avg_risk_score",
            }

            selected_metric_label = st.radio(
                "Select Metric to Display:", list(metric_options.keys()), index=0
            )

            selected_metric = metric_options[selected_metric_label]

            show_table = st.checkbox("Show Detailed Table", value=True)

        with col1:
            df = pd.DataFrame(trading_data)
            df_filtered = df[df[selected_metric].notna() & (df[selected_metric] != 0)]

            chart_title = f"Trading Performance: {selected_metric_label}"
            chart_subtitle = (
                f"Performance analysis across {len(df_filtered)} symbol pairs"
            )

            fig = create_trades_bar_chart(
                df_filtered, selected_metric, chart_title, chart_subtitle
            )

            st.plotly_chart(fig, width="stretch")

        if show_table:
            st.markdown("---")
            _display_detailed_table(trading_data)

        if len(df) > 0:
            st.markdown("---")
            st.subheader("💡 Performance Insights")

            insights_col1, insights_col2 = st.columns(2)

            with insights_col1:
                st.markdown("**🎯 Best Performing Symbols:**")
                top_performers = df.nlargest(3, "total_pnl")[
                    ["symbol_pair", "total_pnl", "win_rate_pct"]
                ]
                for _, row in top_performers.iterrows():
                    st.write(
                        f"• {row['symbol_pair']}: ${row['total_pnl']:,.0f} "
                        f"PnL ({row['win_rate_pct']:.1f}% win rate)"
                    )

            with insights_col2:
                st.markdown("**⚠️ Areas for Improvement:**")

                poor_performers = df[
                    (df["total_pnl"] < 0) | (df["win_rate_pct"] < 50)
                ].nsmallest(3, "total_pnl")[
                    ["symbol_pair", "total_pnl", "win_rate_pct"]
                ]

                if len(poor_performers) > 0:
                    for _, row in poor_performers.iterrows():
                        st.write(
                            f"• {row['symbol_pair']}: ${row['total_pnl']:,.0f} "
                            f"PnL ({row['win_rate_pct']:.1f}% win rate)"
                        )
                else:
                    st.write("• All symbols showing positive performance! 🎉")

        trade_data.close()

    except Exception as e:
        st.error(f"Error loading trading data: {str(e)}")
        st.info("Make sure the trading database exists and contains data.")


def _display_summary_metrics(data: list):
    """
    Display summary trading metrics in a card layout.

    Parameters
    ----------
    data : list
        List of trading metrics dictionaries
    """
    if not data:
        st.warning("No trading data available for analysis.")
        return

    df = pd.DataFrame(data)

    total_pnl = df["total_pnl"].sum()
    total_trades = df["total_trades"].sum()
    avg_win_rate = (
        df["win_rate_pct"].mean() if not df["win_rate_pct"].isna().all() else 0
    )
    total_signals = df["total_signals"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Portfolio PnL",
            value=f"${total_pnl:,.0f}",
            delta=f"{(total_pnl / 10000 * 100):+.1f}%" if total_pnl != 0 else None,
        )

    with col2:
        st.metric(
            label="Total Trades",
            value=f"{total_trades:,.0f}",
            delta=f"Across {len(df)} symbols",
        )

    with col3:
        st.metric(
            label="Average Win Rate",
            value=f"{avg_win_rate:.1f}%",
            delta="Portfolio average",
        )

    with col4:
        conversion_rate = (
            (total_trades / max(total_signals, 1)) * 100 if total_signals > 0 else 0
        )
        st.metric(
            label="Signal Conversion",
            value=f"{conversion_rate:.1f}%",
            delta=f"{total_signals} signals",
        )


def _display_detailed_table(data: list):
    """
    Display detailed trading metrics in a sortable table.

    Parameters
    ----------
    data : list
        List of trading metrics dictionaries
    """
    if not data:
        return

    df = pd.DataFrame(data)

    display_columns = {
        "symbol_pair": "Symbol",
        "total_pnl": "Total PnL ($)",
        "avg_return_pct": "Avg Return (%)",
        "win_rate_pct": "Win Rate (%)",
        "total_trades": "Trades",
        "closed_trades": "Closed",
        "total_signals": "Signals",
        "signal_conversion_rate": "Conversion (%)",
        "avg_confidence_score": "Confidence",
        "avg_risk_score": "Risk Score",
    }

    available_columns = {k: v for k, v in display_columns.items() if k in df.columns}
    df_display = df[list(available_columns.keys())].copy()
    df_display.columns = list(available_columns.values())
    numeric_formats = {
        "Total PnL ($)": "{:,.0f}",
        "Avg Return (%)": "{:.1f}",
        "Win Rate (%)": "{:.1f}",
        "Conversion (%)": "{:.1f}",
        "Confidence": "{:.2f}",
        "Risk Score": "{:.2f}",
    }

    for col, fmt in numeric_formats.items():
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: fmt.format(x) if pd.notnull(x) else "-"
            )

    st.subheader("📊 Detailed Trading Metrics")
    st.dataframe(df_display, width="stretch", hide_index=True)
