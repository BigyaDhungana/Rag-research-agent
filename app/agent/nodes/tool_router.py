from sqlalchemy.orm import Session

from app.agent.tools import TOOL_REGISTRY
from app.agent.state import AgentState


def make_tool_router(db: Session):
    """
    Factory so the node closes over a db Session without AgentState itself
    needing to carry one (TypedDict + SQLAlchemy Session don't mix well as
    graph state — state should stay serializable).
    """

    def tool_router(state: AgentState) -> AgentState:
        plan = state["plan"]
        idx = state["current_step_index"]
        step = plan.steps[idx]

        if step.tool not in TOOL_REGISTRY:
            # Should be unreachable given the Literal-typed schema
            # but the registry check is what actually enforces the
            # "restricted to registered tools" requirement
            result = {
                "step": step.step,
                "tool": step.tool,
                "query": step.query,
                "output": [],
                "error": f"Tool '{step.tool}' is not registered.",
            }
        else:
            tool_fn = TOOL_REGISTRY[step.tool]
            try:
                if step.tool == "search_documents":
                    output = tool_fn(db, step.query)
                else:
                    output = tool_fn(step.query)
                result = {
                    "step": step.step,
                    "tool": step.tool,
                    "query": step.query,
                    "output": output,
                    "error": None,
                }
            except Exception as e:
                result = {
                    "step": step.step,
                    "tool": step.tool,
                    "query": step.query,
                    "output": [],
                    "error": str(e),
                }

        return {
            **state,
            "tool_results": state["tool_results"] + [result],
            "current_step_index": idx + 1,
        }

    return tool_router
