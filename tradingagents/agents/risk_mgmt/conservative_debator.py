from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        if state.get("news_web_report"):
            news_report = f"{news_report}\n\n--- News Web (RSS) ---\n{state['news_web_report']}"
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        tmpl = resolve_prompt(
            prompt_keys.CONSERVATIVE_DEBATOR,
            DEFAULT_PROMPTS[prompt_keys.CONSERVATIVE_DEBATOR],
        )
        prompt = tmpl.format(
            trader_decision=trader_decision,
            market_research_report=market_research_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            fundamentals_report=fundamentals_report,
            history=history,
            current_aggressive_response=current_aggressive_response,
            current_neutral_response=current_neutral_response,
        )

        response = llm.invoke(prompt)

        argument = f"Conservative Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
