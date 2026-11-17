"""Power BI page 1 - 'Customer Churn Dashboard': profile of churned customers."""

import streamlit as st

from app.common import get_filtered_data, kpi_row, page_header, require_rows
from churn_dashboard import charts
from churn_dashboard.data import SERVICE_LABELS
from churn_dashboard.metrics import compute_kpis, format_currency, share, yes_rate

page_header(
    "Churned Customer Profile",
    "Who left: demographics, subscribed services and account details of churned customers. "
    "(This page always shows churned customers; the Churn filter does not apply.)",
)

base = get_filtered_data(ignore_churn=True)
df = base[base["Churned"]]
require_rows(df)
kpis = compute_kpis(df)
kpi_row(kpis, focus="churned")
CFG = {"displayModeBar": False}

st.subheader("Demographics")
c1, c2, c3 = st.columns([1, 1, 1.4])
with c1:
    st.plotly_chart(charts.share_bar(share(df, "gender"), "gender", title="Gender", height=200),
                    width="stretch", config=CFG)
with c2:
    st.metric("Senior citizens", f"{yes_rate(df, 'SeniorCitizen'):.0%}")
    st.metric("With partner", f"{yes_rate(df, 'Partner'):.0%}")
    st.metric("With dependents", f"{yes_rate(df, 'Dependents'):.0%}")
with c3:
    st.plotly_chart(
        charts.share_bar(share(df, "TenureGroup"), "TenureGroup", title="Tenure when they left"),
        width="stretch", config=CFG,
    )

st.subheader("Subscribed services")
service_cols = st.columns(4, border=True)
for i, (col, label) in enumerate(SERVICE_LABELS.items()):
    service_cols[i % 4].metric(label, f"{yes_rate(df, col):.0%}")
st.plotly_chart(
    charts.share_bar(share(df, "InternetService"), "InternetService", title="Internet service"),
    width="stretch", config=CFG,
)

st.subheader("Account information")
a1, a2, a3 = st.columns(3)
with a1:
    st.plotly_chart(charts.share_bar(share(df, "PaymentMethod"), "PaymentMethod",
                                     title="Payment method"), width="stretch", config=CFG)
with a2:
    st.plotly_chart(charts.share_bar(share(df, "Contract"), "Contract", title="Contract type"),
                    width="stretch", config=CFG)
with a3:
    st.metric("Paperless billing", f"{yes_rate(df, 'PaperlessBilling'):.0%}")
    st.metric("Avg monthly charges", format_currency(kpis.avg_monthly_charges))
    st.metric("Avg total charges", format_currency(kpis.avg_total_charges))
