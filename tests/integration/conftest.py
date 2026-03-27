from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _integration_uses_deterministic_pricing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Match CI: no paid LLM, deterministic rules only (no OPENAI_API_KEY required)."""
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "true")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "true")
