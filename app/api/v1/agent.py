from fastapi import APIRouter, HTTPException, Depends

from app.agent.planner import create_plan, PlannerError
from app.schemas.agent import Plan
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.agent.graph import build_agent_graph
from app.agent.state import AgentState

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/plan", response_model=Plan)
def plan(objective: str, db: Session = Depends(get_db)):
    try:
        return create_plan(db, objective)
    except PlannerError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/research")
def research(objective: str, db: Session = Depends(get_db)):
    graph = build_agent_graph(db)
    initial_state: AgentState = {
        "objective": objective,
        "plan": None,
        "current_step_index": 0,
        "tool_results": [],
        "final_answer": None,
        "citations": [],
        "status": "planning",
    }
    final_state = graph.invoke(initial_state)
    return {
        "objective": objective,
        "plan": final_state["plan"].model_dump() if final_state["plan"] else None,
        "tool_results": final_state["tool_results"],
        "answer": final_state["final_answer"],
        "citations": final_state["citations"],
        "status": final_state["status"],
    }
