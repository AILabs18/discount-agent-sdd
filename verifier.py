from __future__ import annotations

"""
Business-friendly verification runner.

This module executes predefined discount scenarios, prints a readable table for
non-technical stakeholders, and emits structured logs for monitoring systems.
"""

import os
from time import perf_counter

# Keep verifier console output business-friendly by default.
# Logs are still written to file sink unless disabled.
os.environ.setdefault("LOG_CONSOLE_ENABLED", "false")

from agent import run_pricing_agent
from logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("verifier")

ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"


SCENARIOS = [
    {
        "name": "VIP safety cap",
        "tier": "VIP",
        "order_total": 3000,
        "expected_discount": 500,
    },
    {
        "name": "Gold threshold not met",
        "tier": "Gold",
        "order_total": 50,
        "expected_discount": 0,
    },
    {
        "name": "Standard customer no discount",
        "tier": "Standard",
        "order_total": 1000,
        "expected_discount": 0,
    },
    {
        "name": "Gold customer gets 10 percent",
        "tier": "Gold",
        "order_total": 250,
        "expected_discount": 25,
    },
    {
        "name": "VIP regular percentage",
        "tier": "VIP",
        "order_total": 400,
        "expected_discount": 80,
    },
    {
        "name": "Unknown tier defaults to zero",
        "tier": "Platinum",
        "order_total": 250,
        "expected_discount": 0,
    },
]

def _print_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render and print a clean ASCII table; returns the separator line."""
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _fmt_row(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[i]) for i, value in enumerate(values))

    separator = "-+-".join("-" * width for width in widths)
    print(_fmt_row(headers))
    print(separator)
    for row in rows:
        print(_fmt_row(row))
    return separator


def _use_color_output() -> bool:
    """
    Control ANSI color output for report readability.

    Disabled when `NO_COLOR` is set or `REPORT_USE_COLOR=false`.
    """
    no_color = os.getenv("NO_COLOR") is not None
    use_color = os.getenv("REPORT_USE_COLOR", "true").lower() == "true"
    return use_color and not no_color


def _colorize(value: str, status: str) -> str:
    if not _use_color_output():
        return value
    if status == "PASS":
        return f"{ANSI_GREEN}{value}{ANSI_RESET}"
    if status == "FAIL":
        return f"{ANSI_RED}{value}{ANSI_RESET}"
    return value


def run_verification_report() -> bool:
    """
    Execute all scenarios and print a business-readable verification report.

    Returns `True` when all scenarios pass, otherwise `False`.
    """
    print("Discount Approval Verification Report")
    print("=" * 90)
    logger.info("verification_started", scenario_count=len(SCENARIOS))

    started_at = perf_counter()
    passed = 0
    failed = 0
    rows: list[list[str]] = []

    for index, scenario in enumerate(SCENARIOS, start=1):
        result = run_pricing_agent(scenario["tier"], scenario["order_total"])
        actual = result["discount"]
        expected = scenario["expected_discount"]
        is_pass = actual == expected

        if is_pass:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        rows.append(
            [
                str(index),
                _colorize(scenario["name"], status),
                scenario["tier"],
                f"{scenario['order_total']:.2f}",
                f"{expected:.2f}",
                f"{actual:.2f}",
                _colorize(status, status),
            ]
        )

        logger.info(
            "scenario_evaluated",
            scenario_index=index,
            scenario_name=scenario["name"],
            tier=scenario["tier"],
            order_total=scenario["order_total"],
            expected_discount=expected,
            actual_discount=actual,
            status=status,
        )

    headers = ["#", "Scenario", "Tier", "Order Total", "Expected", "Actual", "Status"]
    separator = _print_table(headers, rows)

    total = len(SCENARIOS)
    elapsed_ms = (perf_counter() - started_at) * 1000
    pass_rate = (passed / total) * 100 if total else 0
    print(separator)
    print(
        f"Total: {total}  Passed: {passed}  Failed: {failed}  "
        f"Pass Rate: {pass_rate:.1f}%  Time: {elapsed_ms:.2f} ms"
    )

    logger.info(
        "verification_metrics",
        total_scenarios=total,
        passed=passed,
        failed=failed,
        pass_rate=round(pass_rate, 1),
        execution_time_ms=round(elapsed_ms, 2),
    )

    if failed == 0:
        print("Result: SUCCESS")
        logger.info("verification_completed", status="SUCCESS")
        return True

    print("Result: FAILED")
    logger.error("verification_completed", status="FAILED")
    return False


if __name__ == "__main__":
    success = run_verification_report()
    if not success:
        raise SystemExit(1)
