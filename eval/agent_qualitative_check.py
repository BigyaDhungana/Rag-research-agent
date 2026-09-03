QUALITATIVE_OBJECTIVES = [
    "According to the Nepal Road Safety Notes on bridges, what alignment lengths are required for approaches, and what are the current global standards for transition zones?",
    "Can I download Spotify directly on my Versa 4 to play offline music without a phone?",
    "What are best practices for fault-tolerant software design, according to my documents and current industry sources?",
]


def run_qualitative_check(db, objectives: list[str] = None) -> list[dict]:
    """
    Checks simple structural signals per objective: did the plan include
    BOTH tool types when the objective called for
    both, did tool execution succeed, did the final answer actually cite
    both web and document sources when both were used.
    """
    from app.agent.graph import build_agent_graph
    from app.agent.state import AgentState
    from app.agent.planner import PlannerError

    objectives = objectives or QUALITATIVE_OBJECTIVES
    graph = build_agent_graph(db)
    results = []

    for objective in objectives:
        try:
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

            tools_used = {r["tool"] for r in final_state["tool_results"]}
            citation_sources = {c.get("tool") for c in final_state["citations"]}

            results.append(
                {
                    "objective": objective,
                    "status": final_state["status"],
                    "tools_planned": tools_used,
                    "citation_tools_used": citation_sources,
                    "used_both_tool_types": len({"search_web"} & tools_used) > 0
                    and len({"search_documents"} & tools_used) > 0,
                    "answer_preview": (final_state["final_answer"] or "")[:200],
                }
            )
        except PlannerError as e:
            results.append(
                {
                    "objective": objective,
                    "status": "failed",
                    "tools_planned": set(),
                    "citation_tools_used": set(),
                    "used_both_tool_types": False,
                    "answer_preview": f"Planning failed: {e}",
                }
            )
    return results
