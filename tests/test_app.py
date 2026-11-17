"""Smoke-test every page with Streamlit's AppTest (no browser needed)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "app" / "views").glob("[!_]*.py"))


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exceptions(page):
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=120)
    at.switch_page(page)
    at.run()
    assert not at.exception, at.exception
