from app.agent.planner import create_plan, PlannerError
from app.agent.state import AgentState


def planner_node(state: AgentState) -> AgentState:
    try:
        plan = create_plan(state["objective"])
        return {**state, "plan": plan, "status": "executing"}
    except PlannerError as e:
        return {
            **state,
            "plan": None,
            "status": "failed",
            "final_answer": f"Could not create a research plan: {e}",
        }
