import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.agents.sub_agents import run_agent
from src.core.config_loader import cfg

# ==========================================
# 5. MASTER SYNTHESIZER (Orchestrator)
# ==========================================
ORCHESTRATOR_SYSTEM_PROMPT = (
    cfg.get("orchestrator.system_prompt")
    or cfg.get("prompts.orchestrator")
    or """You are the Chief Academic Editor and Master Synthesizer for an AI Master's degree thesis.

### OBJECTIVE:
Synthesize structured domain reports on "Text-to-Motion and Physics RL" into a comprehensive, publication-ready academic Literature Review Chapter.

### REQUIRED SECTIONS:
1. Executive Summary
2. Analysis of Existing Approaches (Synthesize trends across all specialist sub-agent domains)
3. Consolidated Comparative Table:
   - Preserves columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Method/Architecture | Key Metrics | Limitations |
   - Format "Paper Title & Year" as `[Title (Year)](URL)`
   - Format "Code Repository (GitHub)" strictly as `[owner/repo](https://github.com/owner/repo)` if verified, else `N/A`
4. Research Gap & Motivation (Highlight why combining kinematic sequence generation with RL control in physics simulation resolves current limitations)

### STYLE GUIDELINES:
- Ensure the text is strictly academic, highly rigorous, and cleanly formatted in Markdown.
"""
)

def synthesize_literature_review(
    *args,
    sub_agent_results: dict = None,
    custom_prompt: str = None,
    telemetry = None,
    **kwargs
):
    """Passes all sub-agent outputs dynamically to the Orchestrator for final compilation."""
    results_map = {}
    if sub_agent_results and isinstance(sub_agent_results, dict):
        results_map = sub_agent_results
    elif args:
        legacy_names = [
            "Kinematic Text-to-Motion",
            "Physics-Guided Diffusion",
            "Reinforcement Learning Control",
            "Pose Estimation & Vision"
        ]
        for idx, arg_val in enumerate(args):
            title = legacy_names[idx] if idx < len(legacy_names) else f"Domain {idx + 1}"
            results_map[title] = str(arg_val)

    sections = []
    for idx, (domain_title, res_text) in enumerate(results_map.items(), start=1):
        sections.append(f"---\n{idx}. {domain_title.upper()}:\n{res_text}")

    sub_reports_text = "\n\n".join(sections)
    prompt = f"""Here are the analysis results from the {len(results_map)} domain experts. Please synthesize them into the final Literature Review.

{sub_reports_text}
---
"""
    system_prompt = custom_prompt or ORCHESTRATOR_SYSTEM_PROMPT
    from agent_config import ORCHESTRATOR_MAX_TOKENS, ORCHESTRATOR_TEMPERATURE
    return run_agent(
        system_prompt,
        prompt,
        agent_name="orchestrator",
        temperature=ORCHESTRATOR_TEMPERATURE,
        max_tokens=ORCHESTRATOR_MAX_TOKENS,
        telemetry=telemetry
    )


if __name__ == "__main__":
    print("==================================================")
    print("🎼 Orchestrator Standalone Health Check")
    print("==================================================")
    print("Prompt Preview:")
    print(ORCHESTRATOR_SYSTEM_PROMPT[:200] + "...")
    print("==================================================")


