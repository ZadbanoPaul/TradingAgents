from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.analysts.institutional_chain_analyst import build_tool_system_message
from tradingagents.agents.utils.agent_utils import (
    get_indicators,
    get_stock_data,
)
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block
from tradingagents.dataflows.config import get_config
from tradingagents.indicators_catalog import format_indicator_policy_for_market_prompt
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        tools = [
            get_stock_data,
            get_indicators,
        ]
        instrument_context = build_tool_system_message(
            prompt_keys.MARKET_ANALYST_SYSTEM, state, tools
        )
        system_message = (
            instrument_context
            + "\n\n"
            + format_indicator_policy_for_market_prompt(get_config())
        )

        collab = resolve_prompt(
            prompt_keys.TOOL_COLLABORATOR_SYSTEM,
            DEFAULT_PROMPTS[prompt_keys.TOOL_COLLABORATOR_SYSTEM],
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    collab,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(
            instrument_context=build_extended_instrument_block(
                state, tool_names=", ".join(t.name for t in tools)
            )
        )

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
