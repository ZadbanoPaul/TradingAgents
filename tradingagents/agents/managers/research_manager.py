from tradingagents.agents.utils.institutional_context import build_extended_instrument_block
from tradingagents.agents.utils.state_report_bundle import news_with_web
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_extended_instrument_block(
            state, tool_names="(research manager — synteza)"
        )
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = news_with_web(state)
        fundamentals_report = state["fundamentals_report"]
        valuation_report = state.get("valuation_report") or ""
        accounting_quality_report = state.get("accounting_quality_report") or ""
        sector_report = state.get("sector_report") or ""
        catalyst_report = state.get("catalyst_report") or ""
        orchestrator_report = state.get("orchestrator_report") or ""
        data_quality_report = state.get("data_quality_report") or ""
        scoring_report = state.get("scoring_report") or ""

        investment_debate_state = state["investment_debate_state"]
        bull_argument = investment_debate_state.get("bull_history", "")
        bear_argument = investment_debate_state.get("bear_history", "")

        curr_situation = (
            f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n"
            f"{valuation_report}\n\n{accounting_quality_report}\n\n{sector_report}\n\n{catalyst_report}\n\n"
            f"{orchestrator_report}\n\n{data_quality_report}\n\n{scoring_report}"
        )
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        tmpl = resolve_prompt(
            prompt_keys.RESEARCH_MANAGER,
            DEFAULT_PROMPTS[prompt_keys.RESEARCH_MANAGER],
        )
        prompt = tmpl.format(
            past_memory_str=past_memory_str,
            instrument_context=instrument_context,
            history=history,
            orchestrator_report=orchestrator_report,
            data_quality_report=data_quality_report,
            scoring_report=scoring_report,
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            valuation_report=valuation_report,
            accounting_quality_report=accounting_quality_report,
            sector_report=sector_report,
            catalyst_report=catalyst_report,
            bull_argument=bull_argument,
            bear_argument=bear_argument,
        )
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
