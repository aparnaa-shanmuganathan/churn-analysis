import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from churn_dashboard.data import load_data  # noqa: E402


@pytest.fixture(scope="session")
def df():
    return load_data()
