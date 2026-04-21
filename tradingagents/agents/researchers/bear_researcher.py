from tradingagents.agents.utils.state_report_bundle import extended_reports_block, news_with_web
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = news_with_web(state)
        fundamentals_report = state["fundamentals_report"]
        valuation_report = state.get("valuation_report") or ""
        accounting_quality_report = state.get("accounting_quality_report") or ""
        sector_report = state.get("sector_report") or ""
        catalyst_report = state.get("catalyst_report") or ""

        curr_situation = (
            f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n"
            f"{valuation_report}\n\n{accounting_quality_report}\n\n{sector_report}\n\n{catalyst_report}"
        )
        extra = extended_reports_block(state)
        if extra:
            curr_situation = curr_situation + "\n\n" + extra
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        tmpl = resolve_prompt(
            prompt_keys.BEAR_RESEARCHER,
            DEFAULT_PROMPTS[prompt_keys.BEAR_RESEARCHER],
        )
        prompt = tmpl.format(
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            valuation_report=valuation_report,
            accounting_quality_report=accounting_quality_report,
            sector_report=sector_report,
            catalyst_report=catalyst_report,
            history=history,
            current_response=current_response,
            past_memory_str=past_memory_str,
        )

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
