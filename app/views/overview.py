"""Landing page: headline KPIs and auto-generated key insights."""

import streamlit as st

from app.common import get_filtered_data, kpi_row, page_header, require_rows
from churn_dashboard import charts
from churn_dashboard.metrics import churn_by, compute_kpis

page_header(
    "Customer Churn Analytics",
    "Interactive version of the Power BI churn report for a telecom customer base "
    "(7,043 customers). Use the sidebar to slice every page.",
)

df = get_filtered_data(ignore_churn=True)
require_rows(df)
kpis = compute_kpis(df)
kpi_row(kpis)

st.subheader("Key insights")
contract = churn_by(df, "Contract").set_index("Contract")["churn_rate"]
internet = churn_by(df, "InternetService").set_index("InternetService")["churn_rate"]
tenure = churn_by(df, "TenureGroup").set_index("TenureGroup")["churn_rate"]
payment = churn_by(df, "PaymentMethod").set_index("PaymentMethod")["churn_rate"]

insights = []
if {"Month-to-month", "Two year"} <= set(contract.index):
    insights.append(
        f"**Contract length is the strongest lever.** Month-to-month customers churn at "
        f"{contract['Month-to-month']:.1%}, vs {contract['Two year']:.1%} on two-year contracts."
    )
if len(tenure):
    insights.append(
        f"**The first year is the danger zone.** Churn is highest in the "
        f"{tenure.idxmax()} cohort ({tenure.max():.1%}) and falls with tenure."
    )
if len(internet):
    insights.append(
        f"**{internet.idxmax()} customers churn most** ({internet.max():.1%}), "
        f"despite generating the most monthly revenue."
    )
if len(payment):
    insights.append(
        f"**Payment method matters.** {payment.idxmax()} has the highest churn "
        f"({payment.max():.1%}); automatic payments churn far less."
    )
for line in insights:
    st.markdown(f"- {line}")

left, right = st.columns(2)
with left:
    st.plotly_chart(
        charts.churn_rate_bar(churn_by(df, "Contract"), "Contract", title="Churn rate by contract"),
        width="stretch", config={"displayModeBar": False},
    )
with right:
    st.plotly_chart(
        charts.churn_rate_bar(churn_by(df, "TenureGroup"), "TenureGroup",
                              title="Churn rate by tenure"),
        width="stretch", config={"displayModeBar": False},
    )

with st.expander("About this project"):
    st.markdown(
        "- **v1** - exploratory analysis notebook on the BankChurners dataset "
        "(kept in `archive/v1-bankchurners-eda`).\n"
        "- **v2** - two Power BI dashboards (`powerbi/`).\n"
        "- **v3 (this app)** - the Power BI analytics rebuilt as a deployable Streamlit app, "
        "with cross-page filters, a churn propensity model and downloadable at-risk lists."
    )
