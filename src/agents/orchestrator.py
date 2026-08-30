import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.agents.sub_agents import run_agent

# ==========================================
# 5. MASTER SYNTHESIZER (Orchestrator)
# ==========================================
ORCHESTRATOR_SYSTEM_PROMPT = """
You are the Chief Academic Editor and Master Synthesizer for an AI Master's degree thesis.
You will receive 4 structured reports from your sub-agents regarding "Text-to-Motion and Physics RL".
Your task is to compile a comprehensive, academic Literature Review Chapter.

Include the following sections:
1. Executive Summary
2. Analysis of Existing Approaches (Synthesize the trends from the 4 sub-agent reports)
3. Consolidated Metrics & Evaluation Trends
4. Research Gap & Motivation (Highlight why combining kinematic sequence generation with RL control in physics simulation solves current limitations)

Ensure the text is strictly academic, highly readable, and formatted in Markdown.
"""

def synthesize_literature_review(kinematic_res, physics_diff_res, rl_res, pose_res, custom_prompt=None):
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
    return run_agent(system_prompt, prompt)
