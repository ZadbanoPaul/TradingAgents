# TradingAgents/graph/setup.py

from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.analysts.institutional_chain_analyst import (
    create_institutional_tool_analyst,
)
from tradingagents.agents.analysts.orchestrator_analyst import create_orchestrator_analyst
from tradingagents.agents.analysts.pipeline_llm_analysts import (
    create_data_quality_analyst,
    create_scoring_analyst,
)
from tradingagents.agents.utils.agent_utils import (
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_global_news,
    get_income_statement,
    get_news,
    get_stock_data,
)
from tradingagents.agents.utils.news_web_tools import search_web_ticker_news
from tradingagents.agents.utils.technical_indicators_tools import get_indicators
from tradingagents.prompts import keys as prompt_keys

from tradingagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


def _title_case_id(analyst_type: str) -> str:
    return " ".join(part.capitalize() for part in analyst_type.split("_"))


_NO_TOOL = frozenset({"orchestrator", "data_quality", "scoring"})


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        portfolio_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.portfolio_manager_memory = portfolio_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(self, selected_analysts: List[str] | None = None):
        if not selected_analysts:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        analyst_nodes: dict[str, Any] = {}
        delete_nodes: dict[str, Any] = {}
        local_tool_nodes: dict[str, ToolNode] = {}

        for analyst_type in selected_analysts:
            label = _title_case_id(analyst_type)

            if analyst_type == "orchestrator":
                analyst_nodes["orchestrator"] = create_orchestrator_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["orchestrator"] = create_msg_delete()
                continue

            if analyst_type == "data_quality":
                analyst_nodes["data_quality"] = create_data_quality_analyst(
                    self.deep_thinking_llm, prompt_keys.DATA_QUALITY_SYSTEM
                )
                delete_nodes["data_quality"] = create_msg_delete()
                continue

            if analyst_type == "scoring":
                analyst_nodes["scoring"] = create_scoring_analyst(
                    self.deep_thinking_llm, prompt_keys.SCORING_SYSTEM
                )
                delete_nodes["scoring"] = create_msg_delete()
                continue

            if analyst_type == "market":
                analyst_nodes["market"] = create_market_analyst(self.quick_thinking_llm)
                delete_nodes["market"] = create_msg_delete()
                local_tool_nodes["market"] = self.tool_nodes["market"]
            elif analyst_type == "social":
                analyst_nodes["social"] = create_social_media_analyst(self.quick_thinking_llm)
                delete_nodes["social"] = create_msg_delete()
                local_tool_nodes["social"] = self.tool_nodes["social"]
            elif analyst_type == "news":
                analyst_nodes["news"] = create_news_analyst(self.quick_thinking_llm)
                delete_nodes["news"] = create_msg_delete()
                local_tool_nodes["news"] = self.tool_nodes["news"]
            elif analyst_type == "fundamentals":
                analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["fundamentals"] = create_msg_delete()
                local_tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]
            elif analyst_type == "news_web":
                analyst_nodes["news_web"] = create_news_web_analyst(self.quick_thinking_llm)
                delete_nodes["news_web"] = create_msg_delete()
                local_tool_nodes["news_web"] = self.tool_nodes["news_web"]
            elif analyst_type == "accounting_quality":
                analyst_nodes["accounting_quality"] = create_institutional_tool_analyst(
                    self.quick_thinking_llm,
                    body_key=prompt_keys.ACCOUNTING_QUALITY_SYSTEM,
                    output_state_field="accounting_quality_report",
                    tools=[
                        get_fundamentals,
                        get_balance_sheet,
                        get_cashflow,
                        get_income_statement,
                    ],
                )
                delete_nodes["accounting_quality"] = create_msg_delete()
                local_tool_nodes["accounting_quality"] = self.tool_nodes["fundamentals"]
            elif analyst_type == "valuation":
                analyst_nodes["valuation"] = create_institutional_tool_analyst(
                    self.quick_thinking_llm,
                    body_key=prompt_keys.VALUATION_SYSTEM,
                    output_state_field="valuation_report",
                    tools=[
                        get_fundamentals,
                        get_balance_sheet,
                        get_cashflow,
                        get_income_statement,
                        get_stock_data,
                    ],
                )
                delete_nodes["valuation"] = create_msg_delete()
                local_tool_nodes["valuation"] = self.tool_nodes["valuation"]
            elif analyst_type == "sector":
                analyst_nodes["sector"] = create_institutional_tool_analyst(
                    self.quick_thinking_llm,
                    body_key=prompt_keys.SECTOR_SYSTEM,
                    output_state_field="sector_report",
                    tools=[get_fundamentals, get_news, get_global_news],
                )
                delete_nodes["sector"] = create_msg_delete()
                local_tool_nodes["sector"] = self.tool_nodes["sector"]
            elif analyst_type == "catalyst":
                analyst_nodes["catalyst"] = create_institutional_tool_analyst(
                    self.quick_thinking_llm,
                    body_key=prompt_keys.CATALYST_SYSTEM,
                    output_state_field="catalyst_report",
                    tools=[get_news, get_global_news],
                )
                delete_nodes["catalyst"] = create_msg_delete()
                local_tool_nodes["catalyst"] = self.tool_nodes["catalyst"]
            else:
                raise ValueError(f"Unknown analyst type in graph: {analyst_type}")

        bull_researcher_node = create_bull_researcher(self.quick_thinking_llm, self.bull_memory)
        bear_researcher_node = create_bear_researcher(self.quick_thinking_llm, self.bear_memory)
        research_manager_node = create_research_manager(self.deep_thinking_llm, self.invest_judge_memory)
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(self.deep_thinking_llm, self.portfolio_manager_memory)

        workflow = StateGraph(AgentState)

        for analyst_type, node in analyst_nodes.items():
            label = _title_case_id(analyst_type)
            workflow.add_node(f"{label} Analyst", node)
            workflow.add_node(f"Msg Clear {label}", delete_nodes[analyst_type])
            if analyst_type not in _NO_TOOL:
                workflow.add_node(f"tools_{analyst_type}", local_tool_nodes[analyst_type])

        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        first = selected_analysts[0]
        workflow.add_edge(START, f"{_title_case_id(first)} Analyst")

        for i, analyst_type in enumerate(selected_analysts):
            label = _title_case_id(analyst_type)
            current_analyst = f"{label} Analyst"
            current_clear = f"Msg Clear {label}"

            if analyst_type in _NO_TOOL:
                workflow.add_edge(current_analyst, current_clear)
            else:
                current_tools = f"tools_{analyst_type}"
                workflow.add_conditional_edges(
                    current_analyst,
                    getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                    [current_tools, current_clear],
                )
                workflow.add_edge(current_tools, current_analyst)

            if i < len(selected_analysts) - 1:
                next_label = _title_case_id(selected_analysts[i + 1])
                workflow.add_edge(current_clear, f"{next_label} Analyst")
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_edge("Portfolio Manager", END)

        return workflow.compile()
