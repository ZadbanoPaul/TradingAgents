import functools

from tradingagents.agents.utils.state_report_bundle import extended_reports_block, news_with_web
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = news_with_web(state)
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        annex = extended_reports_block(state)
        context = {
            "role": "user",
            "content": (
                f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. "
                f"This plan incorporates insights from technical, sentiment, macro/news, fundamentals, valuation, accounting, sector, catalyst, data quality, and scoring layers.\n\n"
                f"Proposed Investment Plan:\n{investment_plan}\n\n"
                f"Market report:\n{market_research_report}\n\n"
                f"Sentiment report:\n{sentiment_report}\n\n"
                f"News / macro report:\n{news_report}\n\n"
                f"Fundamentals report:\n{fundamentals_report}\n\n"
                + (f"Annex:\n{annex}\n\n" if annex else "")
                + "Use this package to produce the mandated transaction proposal format."
            ),
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
