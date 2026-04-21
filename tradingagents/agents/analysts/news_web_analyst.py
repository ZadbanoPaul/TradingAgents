from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.news_web_tools import search_web_ticker_news
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_news_web_analyst(llm):
    def news_web_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [search_web_ticker_news]

        system_message = (
            resolve_prompt(
                prompt_keys.NEWS_WEB_ANALYST_SYSTEM,
                DEFAULT_PROMPTS[prompt_keys.NEWS_WEB_ANALYST_SYSTEM],
            )
            + get_language_instruction()
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
        prompt = prompt.partial(instrument_context=instrument_context)

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
