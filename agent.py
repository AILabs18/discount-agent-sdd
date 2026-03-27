from __future__ import annotations

from pathlib import Path

SPEC_PATH = Path("specs/discount_logic.md")


def load_spec(path: Path = SPEC_PATH) -> str:
    """Load the markdown specification used as the source of truth."""
    return path.read_text(encoding="utf-8")


def run_pricing_agent(customer_tier: str, order_total: float) -> dict[str, float]:
    """
    Spec-driven pricing agent.

    In a full LLM workflow, you would pass `spec` + task data to a model and
    parse JSON output. For this starter project, we keep execution deterministic
    so you can run and verify behavior locally.
    """
    spec = load_spec()
    _ = spec  # Kept intentionally to show the SDD input contract.

    tier = customer_tier.strip().lower()
    discount = 0.0

    if tier == "vip":
        discount = order_total * 0.20
    elif tier == "gold" and order_total > 100:
        discount = order_total * 0.10
    else:
        discount = 0.0

    # Safety cap from the spec.
    discount = min(discount, 500.0)

    return {"discount": round(discount, 2)}
