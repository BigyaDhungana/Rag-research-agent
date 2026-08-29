from sqlalchemy.orm import Session

from app.agent.planner import create_plan, PlannerError
from app.agent.state import AgentState


def make_planner_node(db: Session):
    def planner_node(state: AgentState) -> AgentState:
        try:
            plan = create_plan(db, state["objective"])
            return {**state, "plan": plan, "status": "executing"}
        except PlannerError as e:
            return {
                **state,
                "plan": None,
                "status": "failed",
                "final_answer": f"Could not create a research plan: {e}",
            }
    return planner_node