"""Filtered raw data with download and data dictionary."""

import streamlit as st

from app.common import get_filtered_data, page_header

page_header(
    "Data Explorer",
    "The cleaned dataset behind every chart, with the sidebar filters applied.",
)

df = get_filtered_data()
st.write(f"{len(df):,} customers")
st.dataframe(df.drop(columns=["Churned"]), hide_index=True, width="stretch", height=480)
st.download_button(
    "Download filtered data (CSV)", df.to_csv(index=False).encode(),
    file_name="churn_filtered.csv", mime="text/csv", icon=":material/download:",
)

with st.expander("Data dictionary"):
    st.markdown(
        """
| Column | Description |
|---|---|
| customerID | Unique customer identifier |
| gender, SeniorCitizen, Partner, Dependents | Demographics |
| tenure | Months the customer has been with the company |
| PhoneService ... StreamingMovies | Subscribed services (Yes / No / No service) |
| Contract | Month-to-month, One year, Two year |
| PaperlessBilling, PaymentMethod | Billing setup |
| MonthlyCharges | Current monthly bill ($) |
| TotalCharges | Lifetime charges ($). Blank for 11 brand-new (tenure 0) customers, filled with 0 |
| numAdminTickets, numTechTickets | Support tickets raised |
| Churn | Whether the customer left (Yes / No) |
| TenureGroup *(derived)* | Tenure bucket in years |
| TotalTickets *(derived)* | Admin + tech tickets |
"""
    )
