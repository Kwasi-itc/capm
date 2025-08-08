"""
Pytest plug-in for the *tests.tools* suite.

It prints a timestamped banner when each test starts and its final
outcome (PASSED/FAILED/SKIPPED) when it finishes.  Run the tests with
``pytest -s`` (or ``pytest -q -s``) to see the messages.
"""
from datetime import datetime
import pytest


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def pytest_runtest_logstart(nodeid, location):  # noqa: D401
    """Called just before a test starts running."""
    print(f"\n[{_ts()}] START  {nodeid}")


def pytest_runtest_logreport(report: pytest.TestReport):  # noqa: D401
    """Called after each test phase; we care about the main *call* phase."""
    if report.when != "call":
        return
    print(f"[{_ts()}] RESULT {report.nodeid} … {report.outcome.upper()}")
