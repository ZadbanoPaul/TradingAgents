import functools

from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        if state.get("news_web_report"):
            news_report = f"{news_report}\n\n--- News Web (RSS) ---\n{state['news_web_report']}"
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. {instrument_context} This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        tmpl = resolve_prompt(
            prompt_keys.TRADER_SYSTEM,
            DEFAULT_PROMPTS[prompt_keys.TRADER_SYSTEM],
        )
        messages = [
            {
                "role": "system",
                "content": tmpl.format(past_memory_str=past_memory_str),
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
