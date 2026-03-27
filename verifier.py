from __future__ import annotations

from time import perf_counter

from agent import run_pricing_agent


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


def run_verification_report() -> bool:
    print("Running SDD verification...\n")

    started_at = perf_counter()
    passed = 0
    failed = 0

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

        print(
            f"[{status}] #{index} {scenario['name']} | "
            f"Tier={scenario['tier']}, Total=${scenario['order_total']} | "
            f"Expected={expected}, Actual={actual}"
        )

    total = len(SCENARIOS)
    elapsed_ms = (perf_counter() - started_at) * 1000
    pass_rate = (passed / total) * 100 if total else 0

    print("\n--- Verification Metrics ---")
    print(f"Total scenarios run : {total}")
    print(f"Passed              : {passed}")
    print(f"Failed              : {failed}")
    print(f"Pass rate           : {pass_rate:.1f}%")
    print(f"Execution time      : {elapsed_ms:.2f} ms")

    if failed == 0:
        print("\nAll scenarios passed. Ready for deployment.")
        return True

    print("\nVerification failed. Please review failed scenarios.")
    return False


if __name__ == "__main__":
    success = run_verification_report()
    if not success:
        raise SystemExit(1)
