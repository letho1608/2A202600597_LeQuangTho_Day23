"""Routing functions for conditional edges.

Each function takes AgentState and returns a string — the name of the next node.
These strings MUST match node names registered in graph.py.
"""

from __future__ import annotations

from .state import AgentState


def route_after_classify(state: AgentState) -> str:
    route = state.get("route", "simple")
    mapping = {
        "simple": "answer",
        "tool": "tool",
        "missing_info": "clarify",
        "risky": "risky_action",
        "error": "retry"
    }
    return mapping.get(route, "answer")

def route_after_evaluate(state: AgentState) -> str:
    return "retry" if state.get("evaluation_result") == "needs_retry" else "answer"

def route_after_retry(state: AgentState) -> str:
    attempt = state.get("attempt", 0)
    max_attempts = state.get("max_attempts", 3)
    return "tool" if attempt < max_attempts else "dead_letter"

def route_after_approval(state: AgentState) -> str:
    appr = state.get("approval", False)
    if isinstance(appr, dict):
        appr = appr.get("approved", False)
    return "tool" if appr else "clarify"
