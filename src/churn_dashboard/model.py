"""Churn propensity model: scikit-learn pipeline + evaluation helpers.

A logistic regression is used deliberately: it is fast enough to train on page
load, well calibrated, and its coefficients are explainable to business users.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges", "numAdminTickets", "numTechTickets"]
CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
RANDOM_STATE = 42


@dataclass(frozen=True)
class ModelReport:
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    f1: float
    threshold: float
    confusion: np.ndarray
    n_test: int


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), CATEGORICAL_FEATURES),
        ]
    )
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)
    return Pipeline([("pre", pre), ("clf", clf)])


def train(df: pd.DataFrame, test_size: float = 0.2) -> tuple[Pipeline, pd.DataFrame, pd.Series]:
    """Fit on a stratified split; return the model plus the held-out test set."""
    X, y = df[FEATURES], df["Churned"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )
    model = build_pipeline().fit(X_train, y_train)
    logger.info("Trained churn model on %d rows", len(X_train))
    return model, X_test, y_test


def evaluate(model: Pipeline, X: pd.DataFrame, y: pd.Series, threshold: float = 0.5) -> ModelReport:
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= threshold).astype(int)
    return ModelReport(
        roc_auc=roc_auc_score(y, proba),
        pr_auc=average_precision_score(y, proba),
        precision=precision_score(y, pred, zero_division=0),
        recall=recall_score(y, pred, zero_division=0),
        f1=f1_score(y, pred, zero_division=0),
        threshold=threshold,
        confusion=confusion_matrix(y, pred),
        n_test=len(y),
    )


def feature_importance(model: Pipeline, top_n: int = 15) -> pd.DataFrame:
    """Signed logistic-regression coefficients (on standardised / one-hot features)."""
    names = model.named_steps["pre"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    out = pd.DataFrame({"feature": names, "coefficient": coefs})
    out["feature"] = out["feature"].str.replace(r"^(num|cat)__", "", regex=True)
    out["abs"] = out["coefficient"].abs()
    return out.nlargest(top_n, "abs").drop(columns="abs").reset_index(drop=True)


def score_customers(model: Pipeline, df: pd.DataFrame) -> pd.Series:
    """Churn probability for every row in ``df``."""
    proba = model.predict_proba(df[FEATURES])[:, 1]
    return pd.Series(proba, index=df.index, name="churn_probability")
