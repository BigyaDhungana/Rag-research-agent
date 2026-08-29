from fastapi import APIRouter, HTTPException

from app.agent.planner import create_plan, PlannerError
from app.schemas.agent import Plan

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/plan", response_model=Plan)
def plan(objective: str):
    try:
        return create_plan(objective)
    except PlannerError as e:
        raise HTTPException(status_code=502, detail=str(e))