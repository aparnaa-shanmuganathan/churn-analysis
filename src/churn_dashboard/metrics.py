"""Pure KPI and aggregation functions (the DAX measures of the Power BI report)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class KPIs:
    total_customers: int
    churned_customers: int
    churn_rate: float
    total_charges: float
    monthly_charges: float
    avg_monthly_charges: float
    avg_total_charges: float
    admin_tickets: int
    tech_tickets: int


def compute_kpis(df: pd.DataFrame) -> KPIs:
    n = len(df)
    churned = int(df["Churned"].sum())
    return KPIs(
        total_customers=n,
        churned_customers=churned,
        churn_rate=churned / n if n else 0.0,
        total_charges=float(df["TotalCharges"].sum()),
        monthly_charges=float(df["MonthlyCharges"].sum()),
        avg_monthly_charges=float(df["MonthlyCharges"].mean()) if n else 0.0,
        avg_total_charges=float(df["TotalCharges"].mean()) if n else 0.0,
        admin_tickets=int(df["numAdminTickets"].sum()),
        tech_tickets=int(df["numTechTickets"].sum()),
    )


def churn_by(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Customers, churned customers, churn rate and monthly revenue per category."""
    grouped = df.groupby(column, observed=True).agg(
        customers=("customerID", "size"),
        churned=("Churned", "sum"),
        monthly_charges=("MonthlyCharges", "sum"),
    )
    grouped["churn_rate"] = grouped["churned"] / grouped["customers"]
    return grouped.reset_index()


def share(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Share of rows in each category of ``column`` (sorted descending)."""
    counts = df[column].value_counts()
    out = (counts / counts.sum()).rename("share").reset_index()
    out.columns = [column, "share"]
    return out


def yes_rate(df: pd.DataFrame, column: str) -> float:
    """Fraction of customers with value 'Yes' in a Yes/No column."""
    return float(df[column].eq("Yes").mean()) if len(df) else 0.0


def format_currency(value: float) -> str:
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= threshold:
            return f"${value / threshold:,.2f}{suffix}"
    return f"${value:,.2f}"


def format_number(value: float) -> str:
    for threshold, suffix in ((1e6, "M"), (1e3, "K")):
        if abs(value) >= threshold:
            return f"{value / threshold:,.2f}{suffix}"
    return f"{value:,.0f}"
