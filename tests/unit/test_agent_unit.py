import importlib
import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))


def _agent_module():
    return importlib.import_module("agent")


def test_validate_inputs_normalizes_values() -> None:
    tier, total = _agent_module()._validate_inputs("  Gold  ", 250)
    assert tier == "Gold"
    assert total == pytest.approx(250.0)


@pytest.mark.parametrize("bad_tier", ["", "   ", None])  # type: ignore[list-item]
def test_validate_inputs_rejects_empty_tier(bad_tier: object) -> None:
    with pytest.raises(_agent_module().AgentInputError):
        _agent_module()._validate_inputs(bad_tier, 100)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_total", ["abc", None, math.inf, math.nan, -1])  # type: ignore[list-item]
def test_validate_inputs_rejects_invalid_totals(bad_total: object) -> None:
    with pytest.raises(_agent_module().AgentInputError):
        _agent_module()._validate_inputs("VIP", bad_total)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("tier", "order_total", "expected"),
    [
        ("Standard", 500, 0),
        ("Gold", 100, 0),
        ("Gold", 250, 25),
        ("VIP", 400, 80),
        ("VIP", 999999, 500),
    ],
)
def test_deterministic_discount_rules(tier: str, order_total: float, expected: float) -> None:
    assert _agent_module()._deterministic_discount(tier, order_total) == expected


def test_build_prompt_contains_spec_and_required_schema() -> None:
    prompt = _agent_module()._build_prompt("SPEC BODY", "VIP", 3000)
    assert "SPEC BODY" in prompt
    assert '"discount": number' in prompt
    assert "Tier: VIP" in prompt


def test_run_pricing_agent_uses_fallback_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    agent_module = _agent_module()

    def _raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("llm error")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "false")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "true")
    monkeypatch.setattr(agent_module, "load_spec", lambda: "spec")
    monkeypatch.setattr(agent_module, "_run_llm_discount", _raise_runtime_error)

    result = agent_module.run_pricing_agent("Gold", 250)
    assert result["discount"] == 25


def test_run_pricing_agent_raises_when_fallback_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    agent_module = _agent_module()

    def _raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("llm error")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "false")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "false")
    monkeypatch.setattr(agent_module, "load_spec", lambda: "spec")
    monkeypatch.setattr(agent_module, "_run_llm_discount", _raise_runtime_error)

    with pytest.raises(RuntimeError, match="llm error"):
        agent_module.run_pricing_agent("Gold", 250)


def test_run_pricing_agent_skips_llm_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "false")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "true")
    result = _agent_module().run_pricing_agent("VIP", 1000)
    assert result["discount"] == 200


def test_run_pricing_agent_disable_paid_llm_forces_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "would-be-paid-if-called")
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "true")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "true")
    result = _agent_module().run_pricing_agent("Gold", 250)
    assert result["discount"] == 25


def test_run_pricing_agent_requires_llm_or_fallback_when_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENT_DISABLE_PAID_LLM", "false")
    monkeypatch.setenv("PRICING_AGENT_FALLBACK", "false")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY|LLM is disabled"):
        _agent_module().run_pricing_agent("Gold", 250)
