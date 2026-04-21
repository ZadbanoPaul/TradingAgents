# TradingAgents/graph/signal_processing.py

from typing import Any

from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: Any):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Extracted rating (BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, or SELL)
        """
        sys = resolve_prompt(
            prompt_keys.SIGNAL_EXTRACTOR_SYSTEM,
            DEFAULT_PROMPTS[prompt_keys.SIGNAL_EXTRACTOR_SYSTEM],
        )
        messages = [
            ("system", sys),
            ("human", full_signal),
        ]

        return self.quick_thinking_llm.invoke(messages).content
