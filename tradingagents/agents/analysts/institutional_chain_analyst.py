"""Analitycy z narzędziami w łańcuchu instytucjonalnym (wspólny prefiks + pole raportu)."""

from __future__ import annotations

from typing import Callable

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import get_language_instruction
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS
from tradingagents.prompts.institutional_compose import institutional_system_prefix


def build_tool_system_message(body_key: str, state: dict, tools: list) -> str:
    """Prefiks instytucjonalny + treść roli analityka (bez szablonu collaborator)."""
    tool_names = ", ".join(t.name for t in tools)
    ext = build_extended_instrument_block(state, tool_names=tool_names)
    prefix = institutional_system_prefix(
        current_date=state["trade_date"],
        instrument_extended=ext,
    )
    role = resolve_prompt(body_key, DEFAULT_PROMPTS[body_key])
    return prefix + role + get_language_instruction()


def create_institutional_tool_analyst(
    llm,
    *,
    body_key: str,
    output_state_field: str,
    tools: list,
) -> Callable:
    """Wzorzec jak fundamentals/market — prefiks instytucjonalny + treść roli."""

    def analyst_node(state):
        current_date = state["trade_date"]
        tool_names = ", ".join(t.name for t in tools)
        ext = build_extended_instrument_block(state, tool_names=tool_names)
        prefix = institutional_system_prefix(
            current_date=current_date,
            instrument_extended=ext,
        )
        role_body = resolve_prompt(
            body_key,
            DEFAULT_PROMPTS[body_key],
        )
        system_message = prefix + role_body + get_language_instruction()

        collab = resolve_prompt(
            prompt_keys.TOOL_COLLABORATOR_SYSTEM,
            DEFAULT_PROMPTS[prompt_keys.TOOL_COLLABORATOR_SYSTEM],
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", collab),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=tool_names)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=ext)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = ""
        if not getattr(result, "tool_calls", None):
            report = result.content or ""
        return {
            "messages": [result],
            output_state_field: report,
        }

    return analyst_node
