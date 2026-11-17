"""Churn propensity model: evaluation, drivers and a downloadable at-risk list."""

import plotly.express as px
import streamlit as st

from app.common import get_filtered_data, get_model, page_header, require_rows
from churn_dashboard import charts
from churn_dashboard.model import evaluate, feature_importance, score_customers

page_header(
    "Churn Prediction",
    "Logistic-regression churn model (class-balanced, 80/20 stratified split). "
    "Use it to rank current customers by risk before they leave.",
)

model, X_test, y_test = get_model()

threshold = st.slider(
    "Decision threshold", 0.05, 0.95, 0.50, 0.05,
    help="Customers with a predicted probability above this are flagged as at risk. "
         "Lower it to catch more churners at the cost of more false alarms.",
)
report = evaluate(model, X_test, y_test, threshold)

cols = st.columns(5, border=True)
for col, (label, value, helptext) in zip(cols, [
    ("ROC AUC", report.roc_auc, "Ranking quality, threshold-independent"),
    ("PR AUC", report.pr_auc, "Average precision; baseline equals the churn rate (~0.27)"),
    ("Precision", report.precision, "Share of flagged customers who actually churned"),
    ("Recall", report.recall, "Share of churners the model catches"),
    ("F1", report.f1, "Harmonic mean of precision and recall"),
], strict=True):
    col.metric(label, f"{value:.2f}", help=helptext)
st.caption(f"Evaluated on {report.n_test:,} held-out customers the model never saw.")

left, right = st.columns(2)
with left:
    tn, fp, fn, tp = report.confusion.ravel()
    cm = px.imshow(
        report.confusion, text_auto=",", color_continuous_scale=["#cde2fb", "#184f95"],
        x=["Predicted stay", "Predicted churn"], y=["Actually stayed", "Actually churned"],
    )
    cm.update_coloraxes(showscale=False)
    st.plotly_chart(charts._style(cm, title="Confusion matrix (test set)"),
                    width="stretch", config={"displayModeBar": False})
with right:
    imp = feature_importance(model, top_n=12)
    imp["direction"] = imp["coefficient"].gt(0).map({True: "Raises churn", False: "Lowers churn"})
    fig = px.bar(
        imp, x="coefficient", y="feature", orientation="h", color="direction",
        color_discrete_map={"Raises churn": charts.CHURNED, "Lowers churn": charts.RETAINED},
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_traces(marker_cornerradius=4)
    st.plotly_chart(charts._style(fig, title="Top model drivers (coefficients)", height=420),
                    width="stretch", config={"displayModeBar": False})

st.subheader("Current customers most at risk")
current = get_filtered_data(ignore_churn=True)
current = current[~current["Churned"]]
require_rows(current)
scored = current.assign(churn_probability=score_customers(model, current))
at_risk = scored[scored["churn_probability"] >= threshold].sort_values(
    "churn_probability", ascending=False
)
st.write(
    f"**{len(at_risk):,}** of {len(current):,} active customers are above the threshold, "
    f"representing **${at_risk['MonthlyCharges'].sum():,.0f}/month** in revenue."
)
show_cols = ["customerID", "churn_probability", "Contract", "tenure", "InternetService",
             "PaymentMethod", "MonthlyCharges", "numTechTickets"]
st.dataframe(
    at_risk[show_cols].head(500),
    hide_index=True, width="stretch",
    column_config={
        "churn_probability": st.column_config.ProgressColumn(
            "Churn probability", format="percent", min_value=0.0, max_value=1.0
        ),
        "MonthlyCharges": st.column_config.NumberColumn("Monthly charges", format="dollar"),
    },
)
st.download_button(
    "Download at-risk list (CSV)", at_risk[show_cols].to_csv(index=False).encode(),
    file_name="at_risk_customers.csv", mime="text/csv", icon=":material/download:",
)
st.caption(
    "Note: the model is scored on the same customers whose history it learned from, so "
    "probabilities for active customers are best used for ranking, not as exact odds."
)
