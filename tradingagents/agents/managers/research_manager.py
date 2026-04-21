from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        if state.get("news_web_report"):
            news_report = f"{news_report}\n\n--- News Web (RSS) ---\n{state['news_web_report']}"
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
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
