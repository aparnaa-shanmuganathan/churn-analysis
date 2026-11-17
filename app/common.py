"""Shared Streamlit helpers: cached data/model, sidebar slicers, KPI cards."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from churn_dashboard import data as data_mod
from churn_dashboard import model as model_mod
from churn_dashboard.charts import CATEGORY_ORDERS
from churn_dashboard.metrics import KPIs, format_currency, format_number

FILTER_KEY = "filters"


@st.cache_data(show_spinner="Loading customer data...")
def get_data() -> pd.DataFrame:
    return data_mod.load_data()


@st.cache_resource(show_spinner="Training churn model...")
def get_model():
    """Train once per server process; shared across sessions."""
    df = get_data()
    return model_mod.train(df)


def render_sidebar_filters() -> None:
    """Global slicers (same as the Power BI report) - persist across pages."""
    try:
        df = get_data()
    except (FileNotFoundError, data_mod.DataValidationError) as exc:
        st.error(f"Could not load the dataset: {exc}")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        churn = st.segmented_control(
            "Churn", ["All", "Yes", "No"], default="All", key="f_churn"
        ) or "All"
        internet = st.multiselect(
            "Internet service", CATEGORY_ORDERS["InternetService"], key="f_internet",
            placeholder="All",
        )
        contract = st.multiselect(
            "Contract", CATEGORY_ORDERS["Contract"], key="f_contract", placeholder="All"
        )
        lo, hi = int(df["tenure"].min()), int(df["tenure"].max())
        tenure = st.slider("Tenure (months)", lo, hi, (lo, hi), key="f_tenure")
        st.caption("Filters apply to every dashboard page.")

    st.session_state[FILTER_KEY] = dict(
        churn=churn, internet_service=internet, contract=contract, tenure_range=tenure
    )


def get_filtered_data(*, ignore_churn: bool = False) -> pd.DataFrame:
    filters = dict(st.session_state.get(FILTER_KEY, {}))
    if ignore_churn:
        filters["churn"] = "All"
    return data_mod.apply_filters(get_data(), **filters)


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def require_rows(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No customers match the current filters. Widen the filters in the sidebar.")
        st.stop()


def kpi_row(kpis: KPIs, *, focus: str = "all") -> None:
    """Top-of-page KPI cards. ``focus='churned'`` mirrors the churn dashboard header."""
    cols = st.columns(5, border=True)
    if focus == "churned":
        items = [
            ("Churned customers", f"{kpis.churned_customers:,}"),
            ("Tech tickets", f"{kpis.tech_tickets:,}"),
            ("Admin tickets", f"{kpis.admin_tickets:,}"),
            ("Total charges", format_currency(kpis.total_charges)),
            ("Monthly charges", format_currency(kpis.monthly_charges)),
        ]
    else:
        items = [
            ("Total customers", f"{kpis.total_customers:,}"),
            ("Churn rate", f"{kpis.churn_rate:.2%}"),
            ("Total charges", format_currency(kpis.total_charges)),
            ("Admin tickets", format_number(kpis.admin_tickets)),
            ("Tech tickets", format_number(kpis.tech_tickets)),
        ]
    for col, (label, value) in zip(cols, items, strict=True):
        col.metric(label, value)
