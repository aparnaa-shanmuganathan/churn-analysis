"""Streamlit entry point: navigation, shared sidebar filters, logging.

Run locally with ``streamlit run streamlit_app.py``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in (ROOT / "src", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from app.common import render_sidebar_filters  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

st.set_page_config(
    page_title="Customer Churn Analytics",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("app/views/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page(
        "app/views/churn_dashboard.py",
        title="Churned Customer Profile",
        icon=":material/person_off:",
    ),
    st.Page("app/views/risk_analysis.py", title="Risk Analysis", icon=":material/warning:"),
    st.Page("app/views/prediction.py", title="Churn Prediction", icon=":material/model_training:"),
    st.Page("app/views/data_explorer.py", title="Data Explorer", icon=":material/table:"),
]

navigation = st.navigation(pages)
render_sidebar_filters()
navigation.run()
