"""Node functions for the LangGraph workflow.

Each function receives AgentState and returns a partial state update dict.
Do NOT mutate input state — return new values only.

LLM REQUIREMENT:
- classify_node MUST use a real LLM call (structured output for intent classification)
- answer_node MUST use a real LLM call (grounded response generation)
- evaluate_node SHOULD use LLM-as-judge (bonus points; heuristic acceptable for base score)
"""

from __future__ import annotations

import os
from .state import AgentState, make_event
from .llm import get_llm

def intake_node(state: AgentState) -> dict:
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }
from pydantic import BaseModel, Field

class Classification(BaseModel):
    route: str = Field(description="One of: simple, tool, missing_info, risky, error")
    risk_level: str = Field(description="high if route is risky, else low")

def classify_node(state: AgentState) -> dict:
    llm = get_llm().with_structured_output(Classification)
    query = state.get("query", "")
    prompt = f"Classify the following query: {query}"
    res = llm.invoke(prompt)
    if isinstance(res, dict):
        route = res.get("route", "simple")
        risk_level = res.get("risk_level", "low")
    elif getattr(res, "route", None) is not None:
        route = getattr(res, "route")
        risk_level = getattr(res, "risk_level")
    else:
        route = "simple"
        risk_level = "low"
    return {
        "route": route,
        "risk_level": risk_level,
        "events": [make_event("classify", "completed", f"classified as {route}")]
    }

def tool_node(state: AgentState) -> dict:
    attempt = state.get("attempt", 0)
    route = state.get("route", "")
    if route == "error" and attempt < 2:
        res = "ERROR: Simulated transient failure"
    else:
        res = "SUCCESS: Mock tool completed"
    return {
        "tool_results": [res],
        "events": [make_event("tool", "completed", f"tool result: {res}")]
    }

def evaluate_node(state: AgentState) -> dict:
    last_res = state.get("tool_results", [])[-1] if state.get("tool_results") else ""
    res = "needs_retry" if "ERROR" in last_res else "success"
    return {
        "evaluation_result": res,
        "events": [make_event("evaluate", "completed", f"evaluated as {res}")]
    }

def answer_node(state: AgentState) -> dict:
    llm = get_llm()
    query = state.get("query", "")
    prompt = f"Answer the query: {query}. Context: {state.get('tool_results', [])}, Approval: {state.get('approval', False)}"
    res = llm.invoke(prompt).content
    return {
        "final_answer": str(res),
        "events": [make_event("answer", "completed", "answer generated")]
    }

def ask_clarification_node(state: AgentState) -> dict:
    q = "Could you please provide more details?"
    return {
        "pending_question": q,
        "final_answer": q,
        "events": [make_event("ask_clarification", "completed", "asked clarification")]
    }

def risky_action_node(state: AgentState) -> dict:
    query = state.get("query", "")
    action = f"Proposed risky action for {query}"
    return {
        "proposed_action": action,
        "events": [make_event("risky_action", "completed", "prepared action")]
    }

def approval_node(state: AgentState) -> dict:
    interrupt = os.getenv("LANGGRAPH_INTERRUPT", "false").lower() == "true"
    if interrupt:
        from langgraph.types import interrupt as lg_interrupt
        res = lg_interrupt({"proposed_action": state.get("proposed_action", "")})
        appr = res.get("approved", False)
    else:
        appr = True
    return {
        "approval": appr,
        "events": [make_event("approval", "completed", f"approval: {appr}")]
    }

def retry_or_fallback_node(state: AgentState) -> dict:
    attempt = state.get("attempt", 0) + 1
    return {
        "attempt": attempt,
        "errors": ["transient failure recorded"],
        "events": [make_event("retry_or_fallback", "completed", f"attempt {attempt}")]
    }

def dead_letter_node(state: AgentState) -> dict:
    ans = "Request failed after maximum retries."
    return {
        "final_answer": ans,
        "events": [make_event("dead_letter", "completed", "dead letter")]
    }

def finalize_node(state: AgentState) -> dict:
    return {
        "events": [make_event("finalize", "completed", "workflow finished")]
    }
