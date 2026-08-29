from typing import TypedDict, Literal

from app.schemas.agent import Plan


class ToolResult(TypedDict):
    step: int
    tool: str
    query: str
    output: list[dict] | dict
    error: str | None


class AgentState(TypedDict):
    objective: str
    plan: Plan | None
    current_step_index: int
    tool_results: list[ToolResult]
    final_answer: str | None
    citations: list[dict]
    status: Literal["planning", "executing", "synthesizing", "done", "failed"]