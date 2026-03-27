# Discount Agent SDD Demo

This project demonstrates **Spec-Driven Development (SDD)** using a simple
Discount Approval Agent in Python.

The goal is to show how an agent can stay aligned with business rules by
treating a written spec as the source of truth, then verifying behavior with
tests.

## What This Project Does

- Defines discount rules in a markdown spec.
- Implements an agent function that calculates discounts from those rules.
- Runs scenario-based verification with pass/fail reporting and summary metrics.

## Project Structure

- `specs/discount_logic.md`  
  Business rules and acceptance criteria.
- `agent.py`  
  `run_pricing_agent(customer_tier, order_total)` applies:
  - Standard: `0%`
  - Gold: `10%` when order total is over `$100`
  - VIP: `20%` on all orders
  - Safety cap: discount never exceeds `$500`
- `verifier.py`  
  Runs multiple scenarios and prints:
  - per-scenario status (`PASS` / `FAIL`)
  - expected vs actual discount
  - metrics summary (total run, passed, failed, pass rate, execution time)
- `tests/test_discount_agent.py`  
  Pytest-based checks for acceptance criteria and edge cases.

## Run Locally

From the project root:

```bash
python verifier.py
```

Expected output (example):

```text
Running SDD verification...

[PASS] #1 VIP safety cap | Tier=VIP, Total=$3000 | Expected=500, Actual=500.0
[PASS] #2 Gold threshold not met | Tier=Gold, Total=$50 | Expected=0, Actual=0.0
...

--- Verification Metrics ---
Total scenarios run : 6
Passed              : 6
Failed              : 0
Pass rate           : 100.0%
Execution time      : 2.70 ms

All scenarios passed. Ready for deployment.
```

Example failing output:

```text
Running SDD verification...

[PASS] #1 VIP safety cap | Tier=VIP, Total=$3000 | Expected=500, Actual=500.0
[FAIL] #2 Gold threshold not met | Tier=Gold, Total=$50 | Expected=0, Actual=5.0
...

--- Verification Metrics ---
Total scenarios run : 6
Passed              : 5
Failed              : 1
Pass rate           : 83.3%
Execution time      : 2.61 ms

Verification failed. Please review failed scenarios.
```

## Run Tests (Pytest)

Install once:

```bash
python -m pip install pytest
```

Then run:

```bash
python -m pytest -q
```

## Why This Matters

Without a spec, AI-generated logic can drift or hallucinate.  
With SDD, the workflow becomes:

1. Write the rules in a spec.
2. Implement agent behavior against the spec.
3. Continuously verify outputs against acceptance criteria.

## Next Steps

1. **Connect a real LLM call**
   - Replace deterministic logic in `agent.py` with an LLM client call.
   - Keep loading `specs/discount_logic.md` and pass it in every prompt.
   - Parse and validate JSON response shape: `{"discount": number}`.

2. **Expand `pytest` coverage further**
   - Add malformed input cases (`None`, negative totals, extra spaces, mixed case).
   - Validate response schema consistency for all paths.

3. **Add CI guardrail**
   - Run tests automatically on each push/PR (for example, GitHub Actions).
   - Fail CI if behavior drifts from the spec.
   - Optional: include a spec checksum check to detect unreviewed spec changes.
