import json
import re

from pydantic import ValidationError

from app.agent.prompts import build_planner_prompt
from app.rag.llm import get_llm_provider
from app.schemas.agent import Plan


class PlannerError(Exception):
    """Raised when the LLM's plan can't be parsed/validated after retries."""


def _extract_json(raw: str) -> str:
    """
    LLMs occasionally wrap JSON in markdown fences despite instructions not
    to. Strip those defensively rather than trusting the prompt alone.
    """
    stripped = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    return stripped


def create_plan(objective: str, max_retries: int = 1) -> Plan:
    """
    Calls the LLM to produce a structured plan, validates it against the
    Plan schema. Retries once on a parse/validation failure by re-prompting
    with the error appended (cheap insurance)
    """
    prompt = build_planner_prompt(objective)
    llm = get_llm_provider()

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = llm.generate(prompt)
        try:
            data = json.loads(_extract_json(raw))
            return Plan.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            prompt = (
                build_planner_prompt(objective)
                + f"\n\nYour previous response was invalid ({e}). "
                  f"Respond again with ONLY valid JSON matching the required shape."
            )

    raise PlannerError(f"Failed to produce a valid plan after {max_retries + 1} attempts: {last_error}")