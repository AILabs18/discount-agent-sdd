from __future__ import annotations

"""
Pricing agent execution pipeline.

This module is intentionally split into small steps so each concern is clear:
configuration, validation, prompting, LLM execution, and deterministic fallback.
"""

import importlib
import json
import math
import os
from pathlib import Path
from typing import Any

from logging_config import configure_logging, get_logger

SPEC_PATH = Path("specs/discount_logic.md")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class AgentInputError(ValueError):
    """Raised when incoming pricing inputs are invalid."""


class AgentResponseError(RuntimeError):
    """Raised when the LLM response is missing or malformed."""


configure_logging()
logger = get_logger("pricing_agent")


# --- Environment and configuration helpers ---
def _load_dotenv_if_available() -> None:
    """Load environment variables from `.env` when python-dotenv exists."""
    try:
        dotenv_module = importlib.import_module("dotenv")
    except ImportError:
        return

    load_dotenv = getattr(dotenv_module, "load_dotenv", None)
    if callable(load_dotenv):
        load_dotenv()


def load_spec(path: Path = SPEC_PATH) -> str:
    """Load the markdown spec that defines pricing behavior."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Specification file not found: {path}") from exc


# --- Input safety and deterministic fallback ---
def _validate_inputs(customer_tier: str, order_total: float) -> tuple[str, float]:
    """Normalize and validate external inputs before running any logic."""
    if not isinstance(customer_tier, str) or not customer_tier.strip():
        raise AgentInputError("customer_tier must be a non-empty string.")

    try:
        numeric_total = float(order_total)
    except (TypeError, ValueError) as exc:
        raise AgentInputError("order_total must be numeric.") from exc

    if not math.isfinite(numeric_total):
        raise AgentInputError("order_total must be a finite number.")
    if numeric_total < 0:
        raise AgentInputError("order_total cannot be negative.")

    return customer_tier.strip(), numeric_total


def _deterministic_discount(customer_tier: str, order_total: float) -> float:
    """Rule-based engine used when LLM path is unavailable."""
    tier = customer_tier.strip().lower()
    discount = 0.0

    if tier == "vip":
        discount = order_total * 0.20
    elif tier == "gold" and order_total > 100:
        discount = order_total * 0.10
    else:
        discount = 0.0

    return min(discount, 500.0)


# --- Prompt and LLM execution ---
def _build_prompt(spec: str, customer_tier: str, order_total: float) -> str:
    """Build a strict prompt that forces JSON-only LLM output."""
    return f"""
You are the Pricing-Specialist-Agent.
Follow the rules in this SPECIFICATION strictly:

{spec}

Task:
- Tier: {customer_tier}
- Order total: {order_total}

Return ONLY valid JSON with this exact schema:
{{"discount": number}}
"""


def _run_llm_discount(spec: str, customer_tier: str, order_total: float) -> float:
    """Call OpenAI and validate returned JSON discount payload."""
    try:
        openai_module = importlib.import_module("openai")
    except ImportError as exc:
        raise RuntimeError("openai package is not installed.") from exc

    if not hasattr(openai_module, "OpenAI"):
        raise RuntimeError("openai package is not installed.")

    client = openai_module.OpenAI()
    logger.debug(
        "llm_request_started",
        tier=customer_tier,
        order_total=order_total,
        model=DEFAULT_MODEL,
    )
    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict pricing agent that returns JSON only.",
                },
                {
                    "role": "user",
                    "content": _build_prompt(spec, customer_tier, order_total),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as exc:
        logger.error("llm_request_failed", tier=customer_tier, order_total=order_total)
        raise RuntimeError("OpenAI request failed.") from exc

    content = completion.choices[0].message.content
    if not content:
        raise AgentResponseError("LLM response content is empty.")

    try:
        payload: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AgentResponseError("LLM did not return valid JSON.") from exc

    if "discount" not in payload:
        raise AgentResponseError("LLM JSON missing required field: discount.")

    try:
        raw_discount = float(payload["discount"])
    except (TypeError, ValueError) as exc:
        raise AgentResponseError("LLM discount value is not numeric.") from exc

    if raw_discount < 0:
        raise AgentResponseError("LLM discount cannot be negative.")

    logger.debug(
        "llm_request_succeeded",
        tier=customer_tier,
        order_total=order_total,
        discount=round(min(raw_discount, 500.0), 2),
    )
    return round(min(raw_discount, 500.0), 2)


# --- Public entry point ---
def run_pricing_agent(customer_tier: str, order_total: float) -> dict[str, float]:
    """
    Execute pricing with an LLM-first strategy.

    Flow: load env -> validate input -> load spec -> run LLM -> fallback if needed.
    """
    _load_dotenv_if_available()
    try:
        normalized_tier, normalized_total = _validate_inputs(customer_tier, order_total)
    except AgentInputError:
        logger.error("input_validation_failed", tier=customer_tier, order_total=order_total)
        raise

    spec = load_spec()
    fallback_enabled = os.getenv("PRICING_AGENT_FALLBACK", "true").lower() == "true"

    try:
        discount = _run_llm_discount(spec, normalized_tier, normalized_total)
        logger.debug(
            "pricing_agent_completed",
            tier=normalized_tier,
            order_total=normalized_total,
            discount=discount,
            source="llm",
        )
        return {"discount": discount}
    except RuntimeError:
        if not fallback_enabled:
            raise
        fallback_discount = round(_deterministic_discount(normalized_tier, normalized_total), 2)
        logger.debug(
            "pricing_agent_fallback_used",
            tier=normalized_tier,
            order_total=normalized_total,
            discount=fallback_discount,
            source="deterministic",
        )
        return {"discount": fallback_discount}
