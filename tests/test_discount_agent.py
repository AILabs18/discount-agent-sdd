import pytest

from agent import run_pricing_agent


def test_vip_safety_cap_applied() -> None:
    result = run_pricing_agent("VIP", 3000)
    assert result["discount"] == 500


def test_gold_threshold_not_met() -> None:
    result = run_pricing_agent("Gold", 50)
    assert result["discount"] == 0


def test_gold_exact_threshold_no_discount() -> None:
    result = run_pricing_agent("Gold", 100)
    assert result["discount"] == 0


def test_gold_above_threshold_gets_ten_percent() -> None:
    result = run_pricing_agent("Gold", 101)
    assert result["discount"] == pytest.approx(10.1)


def test_unknown_tier_defaults_to_zero() -> None:
    result = run_pricing_agent("Platinum", 999)
    assert result["discount"] == 0


def test_large_vip_order_still_capped() -> None:
    result = run_pricing_agent("VIP", 1_000_000)
    assert result["discount"] == 500
