from tradingagents.agents.utils.agent_utils import get_language_instruction
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block
from tradingagents.agents.utils.state_report_bundle import news_with_web
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_portfolio_manager(llm, memory):
    def portfolio_manager_node(state) -> dict:

        instrument_context = build_extended_instrument_block(
            state, tool_names="(portfolio manager — decyzja końcowa)"
        )

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = news_with_web(state)
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        valuation_report = state.get("valuation_report") or ""
        accounting_quality_report = state.get("accounting_quality_report") or ""
        sector_report = state.get("sector_report") or ""
        catalyst_report = state.get("catalyst_report") or ""
        data_quality_report = state.get("data_quality_report") or ""
        scoring_report = state.get("scoring_report") or ""
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        curr_situation = (
            f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n"
            f"{valuation_report}\n\n{data_quality_report}"
        )
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        tmpl = resolve_prompt(
            prompt_keys.PORTFOLIO_MANAGER,
            DEFAULT_PROMPTS[prompt_keys.PORTFOLIO_MANAGER],
        )
        prompt = tmpl.format(
            instrument_context=instrument_context,
            research_plan=research_plan,
            trader_plan=trader_plan,
            past_memory_str=past_memory_str,
            history=history,
            language_suffix=get_language_instruction(),
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
        )

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return portfolio_manager_node
