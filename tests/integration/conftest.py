"""Match CI: no paid LLM calls during integration tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_paid_llm_in_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "true")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
