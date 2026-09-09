import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.agents.sub_agents import run_agent
from src.core.config_loader import cfg

# ==========================================
# 5. MASTER SYNTHESIZER (Orchestrator)
# ==========================================
ORCHESTRATOR_SYSTEM_PROMPT = cfg.get("prompts.orchestrator") or """You are the Chief Academic Editor and Master Synthesizer for an AI Master's degree thesis.

### OBJECTIVE:
Synthesize 4 structured domain reports on "Text-to-Motion and Physics RL" into a comprehensive, publication-ready academic Literature Review Chapter.

### REQUIRED SECTIONS:
1. Executive Summary
2. Analysis of Existing Approaches (Synthesize trends across the 4 sub-agent domains)
3. Consolidated Comparative Table:
   - Preserves columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Method/Architecture | Key Metrics | Limitations |
   - Format "Paper Title & Year" as `[Title (Year)](URL)`
   - Format "Code Repository (GitHub)" strictly as `[owner/repo](https://github.com/owner/repo)` if verified, else `N/A`
4. Research Gap & Motivation (Highlight why combining kinematic sequence generation with RL control in physics simulation resolves current limitations)

### STYLE GUIDELINES:
- Ensure the text is strictly academic, highly rigorous, and cleanly formatted in Markdown.
"""

def synthesize_literature_review(kinematic_res, physics_diff_res, rl_res, pose_res, custom_prompt=None, telemetry=None):
    """Passes all sub-agent outputs to the Orchestrator for final compilation."""
    
    prompt = f"""
Here are the analysis results from the 4 domain experts. Please synthesize them into the final Literature Review.

---
1. KINEMATIC TEXT-TO-MOTION:
{kinematic_res}

---
2. PHYSICS-GUIDED DIFFUSION:
{physics_diff_res}

---
3. REINFORCEMENT LEARNING CONTROL:
{rl_res}

---
4. POSE ESTIMATION & MEDIAPIPE:
{pose_res}
---
"""
    system_prompt = custom_prompt or ORCHESTRATOR_SYSTEM_PROMPT
    return run_agent(system_prompt, prompt, agent_name="orchestrator", telemetry=telemetry)


if __name__ == "__main__":
    print("==================================================")
    print("🎼 Orchestrator Standalone Health Check")
    print("==================================================")
    print("Prompt Preview:")
    print(ORCHESTRATOR_SYSTEM_PROMPT[:200] + "...")
    print("==================================================")


