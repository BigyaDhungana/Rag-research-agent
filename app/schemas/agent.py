from typing import Literal

from pydantic import BaseModel


class PlanStep(BaseModel):
    step: int
    tool: Literal["search_web", "search_documents", "fetch_page"]
    query: str
    reason: str


class Plan(BaseModel):
    objective: str
    steps: list[PlanStep]
