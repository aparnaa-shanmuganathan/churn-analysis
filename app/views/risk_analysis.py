"""Power BI page 2 - 'Customer Risk Analysis': churn rate drivers across all customers."""

import streamlit as st

from app.common import get_filtered_data, kpi_row, page_header, require_rows
from churn_dashboard import charts
from churn_dashboard.metrics import churn_by, compute_kpis

page_header(
    "Customer Risk Analysis",
    "Where churn concentrates. Each driver shows churn rate next to the volume at stake.",
)

df = get_filtered_data()
require_rows(df)
kpi_row(compute_kpis(df))
CFG = {"displayModeBar": False}

DRIVERS = [
    ("InternetService", "internet service", "customers", "Customers", False),
    ("Contract", "contract type", "customers", "Customers", False),
    ("TenureGroup", "tenure", "monthly_charges", "Monthly charges", True),
    ("PaymentMethod", "payment method", "monthly_charges", "Monthly charges", True),
]

for column, label, value, value_label, money in DRIVERS:
    agg = churn_by(df, column)
    st.subheader(f"By {label}")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.churn_rate_bar(agg, column, title="Churn rate"),
                        width="stretch", config=CFG)
    with right:
        st.plotly_chart(charts.volume_bar(agg, column, value, title=value_label, money=money),
                        width="stretch", config=CFG)

st.subheader("Churned vs retained mix")
m1, m2 = st.columns(2)
with m1:
    st.plotly_chart(charts.histogram_by_churn(df, "tenure", title="Tenure (months)"),
                    width="stretch", config=CFG)
with m2:
    st.plotly_chart(charts.histogram_by_churn(df, "MonthlyCharges", title="Monthly charges ($)"),
                    width="stretch", config=CFG)
