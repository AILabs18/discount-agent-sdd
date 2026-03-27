from __future__ import annotations

from typing import TypedDict


class _TestResult(TypedDict):
    suite: str
    test: str
    status: str


_RESULTS: list[_TestResult] = []


def _suite_from_nodeid(nodeid: str) -> str:
    if nodeid.startswith("tests/unit/"):
        return "unit"
    if nodeid.startswith("tests/integration/"):
        return "integration"
    return "other"


def pytest_runtest_makereport(item, call):  # type: ignore[no-untyped-def]
    if call.when != "call":
        return

    outcome = "passed"
    if call.excinfo is not None:
        outcome = "failed"

    _RESULTS.append(
        {
            "suite": _suite_from_nodeid(item.nodeid),
            "test": item.name,
            "status": outcome.upper(),
        }
    )


def pytest_terminal_summary(terminalreporter, exitstatus, config):  # type: ignore[no-untyped-def]
    if not _RESULTS:
        return

    terminalreporter.write_sep("-", "Test Status Summary")
    headers = ["Suite", "Test Case", "Status"]

    rows = [[result["suite"], result["test"], result["status"]] for result in _RESULTS]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    terminalreporter.write_line(fmt(headers))
    terminalreporter.write_line(separator)
    for row in rows:
        terminalreporter.write_line(fmt(row))
