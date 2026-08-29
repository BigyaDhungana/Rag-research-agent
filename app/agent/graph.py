from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.agent.nodes.planner_node import planner_node
from app.agent.nodes.tool_router import make_tool_router
from app.agent.nodes.synthesizer import synthesizer_node


def _has_more_steps(state: AgentState) -> str:
    if state["status"] == "failed":
        return "end"
    plan = state["plan"]
    if plan is None or state["current_step_index"] >= len(plan.steps):
        return "synthesize"
    return "continue"


def build_agent_graph(db: Session):
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("tool_router", make_tool_router(db))
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        lambda state: "end" if state["status"] == "failed" else "continue",
        {"continue": "tool_router", "end": END},
    )

    graph.add_conditional_edges(
        "tool_router",
        _has_more_steps,
        {"continue": "tool_router", "synthesize": "synthesizer", "end": END},
    )

    graph.add_edge("synthesizer", END)

    return graph.compile()