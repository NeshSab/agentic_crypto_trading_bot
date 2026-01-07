"""
Charts module for trades analysis visualization.

This module provides chart functions specifically for trading performance analysis
using Plotly with consistent styling and professional visualization.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


PASTEL_COLORS_RGB = {
    "coral_orange": "rgb(248, 156, 116)",
    "aqua_blue": "rgb(102, 197, 204)",
    "leafy_green": "rgb(135, 197, 95)",
    "neutral_grey": "rgb(179, 179, 179)",
}

pastel_colors = list(PASTEL_COLORS_RGB.values())
pio.templates["plotly_dark"].layout.colorway = pastel_colors
pio.templates.default = "plotly_dark"


def _apply_standard_layout(
    fig: go.Figure,
    title: str,
    subtitle: str = "",
    show_legend: bool = True,
) -> None:
    """
    Apply consistent styling to all charts.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure to style
    title : str
        Chart title
    subtitle : str
        Chart subtitle
    show_legend : bool
        Whether to show legend
    """
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:14px;'>{subtitle}</span>",
            x=0.5,
            font=dict(size=18),
        ),
        showlegend=show_legend,
        margin=dict(l=60, r=60, t=100, b=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(
            gridcolor="rgba(128, 128, 128, 0.2)",
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(128, 128, 128, 0.2)",
            showgrid=True,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.5)",
        ),
    )


def create_trades_bar_chart(
    df: pd.DataFrame, metric: str, title: str, subtitle: str
) -> go.Figure:
    """
    Create a customized bar chart for trading metrics using professional styling.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'symbol_pair' and the selected metric column
    metric : str
        The column name for the metric to display on y-axis
    title : str
        Chart title
    subtitle : str
        Chart subtitle

    Returns
    -------
    go.Figure
        Styled Plotly figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No trading data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        _apply_standard_layout(fig, title, subtitle, show_legend=False)
        return fig

    df_sorted = df.sort_values(metric, ascending=False)

    if any(keyword in metric.lower() for keyword in ["pnl", "return", "win_rate"]):
        colors = [
            (
                PASTEL_COLORS_RGB["leafy_green"]
                if val >= 0
                else PASTEL_COLORS_RGB["coral_orange"]
            )
            for val in df_sorted[metric]
        ]
    else:
        colors = [PASTEL_COLORS_RGB["aqua_blue"]] * len(df_sorted)

    fig = go.Figure()

    if "pnl" in metric.lower():
        text_values = [f"${val:,.0f}" for val in df_sorted[metric]]
        hover_format = "$%{y:,.0f}"
    elif "pct" in metric or "rate" in metric:
        text_values = [f"{val:.1f}%" for val in df_sorted[metric]]
        hover_format = "%{y:.1f}%"
    elif "score" in metric:
        text_values = [f"{val:.2f}" for val in df_sorted[metric]]
        hover_format = "%{y:.2f}"
    elif "hours" in metric:
        text_values = [f"{val:.1f}h" for val in df_sorted[metric]]
        hover_format = "%{y:.1f}h"
    else:
        text_values = [f"{val:.0f}" for val in df_sorted[metric]]
        hover_format = "%{y:.0f}"

    fig.add_trace(
        go.Bar(
            x=df_sorted["symbol_pair"],
            y=df_sorted[metric],
            marker=dict(color=colors),
            text=text_values,
            textposition="outside",
            hovertemplate=f"%{{x}}<br>{metric}: {hover_format}<extra></extra>",
        )
    )

    _apply_standard_layout(fig, title, subtitle, show_legend=False)
    fig.update_xaxes(title_text="Symbol Pair", tickangle=45)

    y_max = df_sorted[metric].max()
    y_min = df_sorted[metric].min()
    y_range = y_max - y_min

    padding_top = y_range * 0.2 if y_range > 0 else abs(y_max) * 0.2
    padding_bottom = y_range * 0.2 if y_range > 0 else abs(y_min) * 0.2

    y_axis_min = y_min - padding_bottom
    y_axis_max = y_max + padding_top

    y_titles = {
        "total_pnl": "Total PnL ($)",
        "avg_return_pct": "Average Return (%)",
        "win_rate_pct": "Win Rate (%)",
        "total_trades": "Number of Trades",
        "avg_position_size": "Average Position Size ($)",
        "avg_duration_hours": "Average Trade Duration (Hours)",
        "total_signals": "Number of Signals",
        "signal_conversion_rate": "Signal Conversion Rate (%)",
        "avg_confidence_score": "Average Confidence Score",
        "avg_risk_score": "Average Risk Score",
        "closed_trades": "Closed Trades Count",
    }

    y_title = y_titles.get(metric, metric.replace("_", " ").title())
    fig.update_yaxes(title_text=y_title, range=[y_axis_min, y_axis_max])

    return fig
