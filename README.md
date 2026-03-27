# Discount Agent SDD Demo

This project demonstrates **Spec-Driven Development (SDD)** using a simple
Discount Approval Agent in Python.

The goal is to show how an agent can stay aligned with business rules by
treating a written spec as the source of truth, then verifying behavior with
tests.

## What This Project Does

- Defines discount rules in a markdown spec.
- Implements an agent function that calculates discounts from those rules.
- Verifies acceptance criteria with a lightweight test script.

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
  Runs the acceptance checks from the spec:
  - VIP `$3000` -> `$500` (cap applied)
  - Gold `$50` -> `$0` (threshold not met)
- `tests/test_discount_agent.py`  
  Pytest-based checks for acceptance criteria and edge cases.

## Run Locally

From the project root:

```bash
python verifier.py
```

Expected output:

```text
Running SDD verification...
All spec criteria passed. Ready for deployment.
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
