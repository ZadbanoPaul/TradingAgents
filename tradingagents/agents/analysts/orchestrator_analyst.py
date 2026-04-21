"""Orchestrator — jedna odpowiedź LLM bez narzędzi."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS
from tradingagents.prompts.institutional_compose import institutional_system_prefix
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block


def create_orchestrator_analyst(llm):
    def orchestrator_node(state):
        trade_date = state["trade_date"]
        ext = build_extended_instrument_block(
            state, tool_names="(kolejne węzły — market, social, news, …)"
        )
        prefix = institutional_system_prefix(
            current_date=trade_date,
            instrument_extended=ext,
        )
        body = resolve_prompt(
            prompt_keys.ORCHESTRATOR_SYSTEM,
            DEFAULT_PROMPTS[prompt_keys.ORCHESTRATOR_SYSTEM],
        )
        sys = prefix + body
        msgs = [
            SystemMessage(content=sys),
            HumanMessage(
                content=(
                    f"Uruchom orchestrację dla tickera `{state['company_of_interest']}` "
                    f"na datę {trade_date}. Zwróć wymagane sekcje wyjścia."
                )
            ),
        ]
        r = llm.invoke(msgs)
        return {
            "orchestrator_report": r.content or "",
            "messages": [r],
        }

    return orchestrator_node
