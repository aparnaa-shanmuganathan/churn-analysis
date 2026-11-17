import pandas as pd
import pytest

from churn_dashboard.data import (
    REQUIRED_COLUMNS,
    TENURE_LABELS,
    DataValidationError,
    apply_filters,
    clean,
    load_raw,
)


def test_schema_and_shape(df):
    assert len(df) == 7043
    assert REQUIRED_COLUMNS <= set(df.columns)
    assert df["customerID"].is_unique


def test_total_charges_blanks_filled_only_for_new_customers():
    raw = load_raw()
    blank = pd.to_numeric(raw["TotalCharges"], errors="coerce").isna()
    assert blank.sum() == 11
    assert (raw.loc[blank, "tenure"] == 0).all()
    cleaned = clean(raw)
    assert cleaned["TotalCharges"].notna().all()


def test_tenure_groups_cover_every_customer(df):
    assert df["TenureGroup"].notna().all()
    assert list(df["TenureGroup"].cat.categories) == TENURE_LABELS


def test_missing_column_raises(df):
    with pytest.raises(DataValidationError, match="missing columns"):
        clean(df.drop(columns=["Churn"]))


def test_duplicate_ids_raise(df):
    with pytest.raises(DataValidationError, match="unique"):
        clean(pd.concat([df.head(2), df.head(1)]))


def test_filters(df):
    out = apply_filters(df, churn="Yes", contract=["Two year"], tenure_range=(60, 72))
    assert out["Churned"].all()
    assert set(out["Contract"]) == {"Two year"}
    assert out["tenure"].between(60, 72).all()
    assert len(apply_filters(df)) == len(df)
