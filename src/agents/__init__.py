"""
Agents layer package exports with lazy loading to prevent circular imports.
"""

__all__ = [
    "run_agent",
    "format_papers_for_prompt",
    "analyze_domain",
    "analyze_kinematic",
    "analyze_physics_diffusion",
    "analyze_rl_control",
    "analyze_pose_vision",
    "chunk_papers",
    "merge_markdown_tables",
    "execute_subagent_mapreduce",
    "synthesize_literature_review",
]


def __getattr__(name: str):
    if name in (
        "run_agent",
        "format_papers_for_prompt",
        "analyze_domain",
        "analyze_kinematic",
        "analyze_physics_diffusion",
        "analyze_rl_control",
        "analyze_pose_vision",
    ):
        import src.agents.sub_agents as sa
        return getattr(sa, name)

    if name in (
        "chunk_papers",
        "merge_markdown_tables",
        "execute_subagent_mapreduce",
    ):
        import src.agents.map_reduce as mr
        return getattr(mr, name)

    if name == "synthesize_literature_review":
        import src.agents.orchestrator as orch
        return getattr(orch, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
