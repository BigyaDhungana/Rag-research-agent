import json
import re

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agent.document_signal import get_document_signal
from app.agent.prompts import build_planner_prompt
from app.rag.llm import get_llm_provider, LLMProviderError
from app.schemas.agent import Plan

from langfuse import observe


class PlannerError(Exception):
    """Raised when the LLM's plan can't be parsed/validated after retries."""


def _extract_json(raw: str) -> str:
    stripped = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    return stripped


@observe(name="create_plan")
def create_plan(db: Session, objective: str, max_retries: int = 1) -> Plan:
    """
    Calls the LLM to produce a structured plan, validates it against the
    """
    document_signal = get_document_signal(db, objective)
    prompt = build_planner_prompt(objective, document_signal)
    llm = get_llm_provider()

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = llm.generate(prompt)
        except LLMProviderError as e:
            last_error = e
            if attempt == max_retries:
                raise PlannerError(f"LLM unavailable while planning: {e}") from e
            continue  # try again

        try:
            data = json.loads(_extract_json(raw))
            return Plan.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            prompt = (
                build_planner_prompt(objective, document_signal)
                + f"\n\nYour previous response was invalid ({e}). "
                f"Respond again with ONLY valid JSON matching the required shape."
            )

    raise PlannerError(
        f"Failed to produce a valid plan after {max_retries + 1} attempts: {last_error}"
    )
