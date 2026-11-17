"""KPIs must reproduce the numbers shown in the original Power BI dashboards."""

import pytest

from churn_dashboard.metrics import (
    churn_by,
    compute_kpis,
    format_currency,
    format_number,
    share,
    yes_rate,
)


def test_risk_dashboard_kpis(df):
    k = compute_kpis(df)
    assert k.total_customers == 7043
    assert round(k.churn_rate * 100, 2) == 26.54
    assert format_currency(k.total_charges) == "$16.06M"
    assert k.admin_tickets == 3632
    assert k.tech_tickets == 2955


def test_churn_dashboard_kpis(df):
    k = compute_kpis(df[df["Churned"]])
    assert k.churned_customers == 1869
    assert k.tech_tickets == 2173
    assert k.admin_tickets == 885
    assert format_currency(k.total_charges) == "$2.86M"
    assert format_number(k.monthly_charges) == "139.13K"
    assert k.avg_monthly_charges == pytest.approx(74.44, abs=0.01)


def test_churn_rate_by_contract(df):
    rates = churn_by(df, "Contract").set_index("Contract")["churn_rate"].round(4)
    assert rates.to_dict() == {"Month-to-month": 0.4271, "One year": 0.1127, "Two year": 0.0283}


def test_churn_rate_by_internet(df):
    rates = churn_by(df, "InternetService").set_index("InternetService")["churn_rate"].round(4)
    assert rates["Fiber optic"] == 0.4189
    assert rates["DSL"] == 0.1896


def test_churned_tenure_share(df):
    s = share(df[df["Churned"]], "TenureGroup").set_index("TenureGroup")["share"]
    assert round(s["0-1 yr"] * 100, 2) == 55.48


def test_yes_rate(df):
    churned = df[df["Churned"]]
    assert round(yes_rate(churned, "Partner"), 2) == 0.36
    assert round(yes_rate(churned, "PhoneService"), 2) == 0.91


def test_empty_frame_is_safe(df):
    k = compute_kpis(df.head(0))
    assert k.churn_rate == 0.0 and k.total_customers == 0
