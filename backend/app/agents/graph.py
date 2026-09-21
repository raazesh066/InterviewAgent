"""LangGraph graph assembly for the interview multi-agent system.

Two graphs are built:
- question_graph: Orchestrator -> {Technical | Behavioral | SystemDesign | Coding} -> END
- evaluation_graph: Evaluation -> END  (difficulty adjustment happens inside the node)

A third, simple single-node graph is used for the Feedback Agent at interview completion.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.agents.evaluation_agent import evaluation_agent_node
from app.agents.feedback_agent import feedback_agent_node
from app.agents.orchestrator import orchestrator_node, route_after_orchestrator
from app.agents.question_agents import (
    behavioral_agent_node,
    coding_agent_node,
    system_design_agent_node,
    technical_agent_node,
)
from app.agents.state import InterviewGraphState


@lru_cache
def build_question_graph():
    graph = StateGraph(InterviewGraphState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("technical", technical_agent_node)
    graph.add_node("behavioral", behavioral_agent_node)
    graph.add_node("system_design", system_design_agent_node)
    graph.add_node("coding", coding_agent_node)

    graph.set_entry_point("orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "technical": "technical",
            "behavioral": "behavioral",
            "system_design": "system_design",
            "coding": "coding",
        },
    )
    for node in ("technical", "behavioral", "system_design", "coding"):
        graph.add_edge(node, END)

    return graph.compile()


@lru_cache
def build_evaluation_graph():
    graph = StateGraph(InterviewGraphState)
    graph.add_node("evaluation", evaluation_agent_node)
    graph.set_entry_point("evaluation")
    graph.add_edge("evaluation", END)
    return graph.compile()


@lru_cache
def build_feedback_graph():
    graph = StateGraph(InterviewGraphState)
    graph.add_node("feedback", feedback_agent_node)
    graph.set_entry_point("feedback")
    graph.add_edge("feedback", END)
    return graph.compile()
