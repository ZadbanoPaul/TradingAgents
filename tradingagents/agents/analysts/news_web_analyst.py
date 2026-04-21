from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.analysts.institutional_chain_analyst import build_tool_system_message
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block
from tradingagents.agents.utils.news_web_tools import search_web_ticker_news
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_news_web_analyst(llm):
    def news_web_analyst_node(state):
        current_date = state["trade_date"]
        tools = [search_web_ticker_news]
        system_message = build_tool_system_message(
            prompt_keys.NEWS_WEB_ANALYST_SYSTEM, state, tools
        )

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
            "news_web_report": report,
        }

    return news_web_analyst_node
