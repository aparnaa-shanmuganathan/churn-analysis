"""Plotly figure builders with one consistent visual system.

Design rules (vs. the original Power BI report):
* no pie/donut charts - horizontal bars compare shares more accurately;
* no dual-axis combo charts - churn rate and volume are shown as two charts;
* churned vs. retained always use the same two colours on every page;
* categorical colours are assigned in a fixed order, never by rank.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Validated categorical palette (light mode), fixed order.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
PRIMARY = SERIES[0]
CHURNED = "#eb6834"
RETAINED = "#2a78d6"
CHURN_COLORS = {"Yes": CHURNED, "No": RETAINED}
TEXT = "#52514e"
GRID = "#e6e5e0"

# Stable category orders so colours/positions never shift when filters change.
CATEGORY_ORDERS: dict[str, list[str]] = {
    "Contract": ["Month-to-month", "One year", "Two year"],
    "InternetService": ["Fiber optic", "DSL", "No"],
    "PaymentMethod": [
        "Electronic check", "Mailed check",
        "Bank transfer (automatic)", "Credit card (automatic)",
    ],
    "TenureGroup": ["0-1 yr", "1-2 yrs", "2-3 yrs", "3-4 yrs", "4-5 yrs", "5+ yrs"],
    "Churn": ["No", "Yes"],
    "gender": ["Female", "Male"],
}


def _style(fig: go.Figure, *, height: int = 320, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#0b0b0b"), x=0, xanchor="left")
        if title else None,
        height=height,
        margin=dict(l=8, r=16, t=48 if title else 16, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=TEXT),
        bargap=0.35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, title=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=None)
    return fig


def _order(df: pd.DataFrame, column: str) -> list[str]:
    known = CATEGORY_ORDERS.get(column)
    present = [str(v) for v in df[column].unique()]
    return [c for c in known if c in present] if known else present


def churn_rate_bar(
    data: pd.DataFrame, column: str, *, title: str, label: str | None = None, horizontal=False
) -> go.Figure:
    """Single-series bar of churn rate per category (output of metrics.churn_by)."""
    order = _order(data, column)
    data = data.assign(**{column: data[column].astype(str)})
    kwargs = dict(
        x="churn_rate" if horizontal else column,
        y=column if horizontal else "churn_rate",
        orientation="h" if horizontal else "v",
        text=data["churn_rate"].map("{:.1%}".format),
        custom_data=["customers", "churned"],
        category_orders={column: order},
    )
    fig = px.bar(data, **kwargs)
    fig.update_traces(
        marker_color=PRIMARY,
        marker_cornerradius=4,
        textposition="outside",
        cliponaxis=False,
        hovertemplate=f"<b>%{{{'y' if horizontal else 'x'}}}</b><br>"
        "Churn rate: %{text}<br>Customers: %{customdata[0]:,}<br>"
        "Churned: %{customdata[1]:,}<extra></extra>",
    )
    axis = fig.update_xaxes if horizontal else fig.update_yaxes
    axis(tickformat=".0%", range=[0, data["churn_rate"].max() * 1.18])
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    if label:
        (fig.update_yaxes if horizontal else fig.update_xaxes)(title=label)
    return _style(fig, title=title)


def volume_bar(
    data: pd.DataFrame, column: str, value: str, *, title: str, money: bool = False
) -> go.Figure:
    """Single-series bar of an absolute measure (customers or charges) per category."""
    order = _order(data, column)
    data = data.assign(**{column: data[column].astype(str)})
    fmt = "$,.3s" if money else ",.0f"
    fig = px.bar(data, x=column, y=value, category_orders={column: order}, text_auto=fmt)
    fig.update_traces(
        marker_color=PRIMARY, marker_cornerradius=4, textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>%{y:" + fmt + "}<extra></extra>",
    )
    fig.update_yaxes(tickformat=fmt, range=[0, data[value].max() * 1.18])
    return _style(fig, title=title)


def share_bar(data: pd.DataFrame, column: str, *, title: str, height: int = 260) -> go.Figure:
    """Horizontal bar of category shares (replaces Power BI pies/donuts)."""
    order = _order(data, column)
    data = data.assign(**{column: data[column].astype(str)})
    fig = px.bar(
        data, x="share", y=column, orientation="h",
        category_orders={column: order}, text=data["share"].map("{:.1%}".format),
    )
    fig.update_traces(
        marker_color=PRIMARY, marker_cornerradius=4, textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{text} of customers<extra></extra>",
    )
    # Headroom so outside labels are never clipped.
    fig.update_xaxes(tickformat=".0%", range=[0, data["share"].max() * 1.22], showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return _style(fig, title=title, height=height)


def stacked_churn_share(df: pd.DataFrame, column: str, *, title: str) -> go.Figure:
    """100% stacked bar: share of churned vs retained customers within each category."""
    order = _order(df, column)
    counts = (
        df.assign(**{column: df[column].astype(str)})
        .groupby([column, "Churn"], observed=True).size().rename("n").reset_index()
    )
    counts["pct"] = counts["n"] / counts.groupby(column)["n"].transform("sum")
    fig = px.bar(
        counts, x="pct", y=column, color="Churn", orientation="h",
        color_discrete_map=CHURN_COLORS,
        category_orders={column: order, "Churn": CATEGORY_ORDERS["Churn"]},
        custom_data=["n"],
        labels={"Churn": "Churned"},
    )
    fig.update_traces(
        marker_line_color="white", marker_line_width=2,
        hovertemplate="%{y}<br>%{fullData.name}: %{x:.1%} (%{customdata[0]:,})<extra></extra>",
    )
    for trace in fig.data:
        trace.name = "Churned" if trace.name == "Yes" else "Retained"
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    fig.update_yaxes(autorange="reversed")
    return _style(fig, title=title, height=60 + 48 * len(order))


def histogram_by_churn(df: pd.DataFrame, column: str, *, title: str, nbins: int = 36) -> go.Figure:
    fig = px.histogram(
        df, x=column, color="Churn", nbins=nbins, barmode="overlay", opacity=0.75,
        color_discrete_map=CHURN_COLORS, category_orders={"Churn": CATEGORY_ORDERS["Churn"]},
    )
    for trace in fig.data:
        trace.name = "Churned" if trace.name == "Yes" else "Retained"
    fig.update_yaxes(title="Customers")
    return _style(fig, title=title)
