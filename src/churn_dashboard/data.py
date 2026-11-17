"""Data loading, validation and cleaning for the Telco customer churn dataset.

All business logic that the dashboards depend on (tenure buckets, the churn
flag, handling of blank ``TotalCharges``) lives here so that every page and
every test sees exactly the same dataset.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "telco_churn.csv"

REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
        "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
        "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
        "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
        "MonthlyCharges", "TotalCharges", "numAdminTickets", "numTechTickets", "Churn",
    }
)

# Same buckets as the Power BI "Subscription time" / "Years of contract" visuals:
# (0,12] months -> first year, (12,24] -> second year, ...
TENURE_BINS: list[float] = [-1, 12, 24, 36, 48, 60, np.inf]
TENURE_LABELS: list[str] = ["0-1 yr", "1-2 yrs", "2-3 yrs", "3-4 yrs", "4-5 yrs", "5+ yrs"]

SERVICE_LABELS: dict[str, str] = {
    "PhoneService": "Phone service",
    "MultipleLines": "Multiple lines",
    "OnlineSecurity": "Online security",
    "OnlineBackup": "Online backup",
    "DeviceProtection": "Device protection",
    "TechSupport": "Tech support",
    "StreamingTV": "Streaming TV",
    "StreamingMovies": "Streaming movies",
}
SERVICE_COLUMNS: list[str] = list(SERVICE_LABELS)


class DataValidationError(ValueError):
    """Raised when the input data does not match the expected schema."""


def load_raw(path: Path | str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Read the raw CSV export. Raises ``FileNotFoundError`` with a clear message."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Churn dataset not found at {path}")
    logger.info("Loading churn dataset from %s", path)
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and enrich the raw dataframe. Returns a new dataframe."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(f"Dataset is missing columns: {sorted(missing)}")
    if df["customerID"].duplicated().any():
        raise DataValidationError("customerID must be unique")
    if not set(df["Churn"].dropna().unique()) <= {"Yes", "No"}:
        raise DataValidationError("Churn must only contain 'Yes'/'No'")

    out = df.copy()

    # TotalCharges arrives as text with blanks for brand-new customers (tenure 0).
    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce")
    blank = out["TotalCharges"].isna()
    if blank.any():
        logger.info("Filling %d blank TotalCharges (tenure=0 customers) with 0", blank.sum())
        out.loc[blank, "TotalCharges"] = 0.0

    out["Churned"] = out["Churn"].eq("Yes")
    out["SeniorCitizen"] = out["SeniorCitizen"].map({1: "Yes", 0: "No"})
    out["TenureGroup"] = pd.cut(
        out["tenure"], bins=TENURE_BINS, labels=TENURE_LABELS, ordered=True
    )
    out["TotalTickets"] = out["numAdminTickets"] + out["numTechTickets"]
    return out


def load_data(path: Path | str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load, validate and clean the dataset in one call."""
    return clean(load_raw(path))


def apply_filters(
    df: pd.DataFrame,
    *,
    churn: str = "All",
    internet_service: list[str] | None = None,
    contract: list[str] | None = None,
    tenure_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Slicer logic shared by every dashboard page (mirrors the Power BI slicers)."""
    mask = pd.Series(True, index=df.index)
    if churn in {"Yes", "No"}:
        mask &= df["Churn"].eq(churn)
    if internet_service:
        mask &= df["InternetService"].isin(internet_service)
    if contract:
        mask &= df["Contract"].isin(contract)
    if tenure_range is not None:
        lo, hi = tenure_range
        mask &= df["tenure"].between(lo, hi)
    return df.loc[mask]
