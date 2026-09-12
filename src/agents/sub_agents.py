from openai import OpenAI
import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agent_config import API_KEY, BASE_URL, MODEL_NAME
from src.core.config_loader import cfg

import time
from src.telemetry import get_telemetry

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

def run_agent(system_prompt, user_prompt, agent_name="sub_agent", telemetry=None):
    tm = telemetry or get_telemetry()
    if not API_KEY or API_KEY == "your_api_key_here":
        err = "API Key is missing. Please configure the .env file."
        tm.error(err, source=agent_name)
        return f"[!] {err}"
        
    start_t = time.time()
    tm.thinking(f"Analyzing prompt with {MODEL_NAME}...", source=agent_name)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        raw_content = response.choices[0].message.content
        content = raw_content if raw_content is not None else ""
        duration = time.time() - start_t
        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", None) if usage else None
        tm.response(
            content=f"Generated {len(content)} chars in {duration:.2f}s",
            tokens=total_tokens,
            source=agent_name
        )
        return content
    except Exception as e:
        duration = time.time() - start_t
        tm.error(f"Execution error: {str(e)}", source=agent_name, duration=duration)
        return f"[!] Agent Error: {str(e)}"

import re

def format_papers_for_prompt(papers_data):
    prompt = f"Analyze the following {len(papers_data)} papers:\n\n"
    for i, p in enumerate(papers_data):
        citations = p.get('citations', 'N/A')
        impact_factor = p.get('impact_factor', 'N/A')
        github_url = p.get('github_url', 'N/A')
        abstract_text = p.get('abstract', 'N/A')
        if not github_url or github_url == 'N/A':
            # Strip dead or unverified repository URLs from abstract to prevent LLM hallucination
            abstract_text = re.sub(r'https?://(?:www\.)?github\.com/[^\s\)\],;]+', '', abstract_text)
            abstract_text = re.sub(r'https?://[a-zA-Z0-9_\-\.]+\.github\.io/[^\s\)\],;]+', '', abstract_text)
        prompt += (
            f"--- Paper {i+1} ---\n"
            f"Title: {p.get('title', 'N/A')} ({p.get('year', 'N/A')})\n"
            f"Citations: {citations}\n"
            f"Impact Factor / Rank: {impact_factor}\n"
            f"GitHub Code Repo: {github_url}\n"
            f"URL: {p.get('url', 'N/A')}\n"
            f"Abstract: {abstract_text}\n\n"
        )
    return prompt

# Default System Prompts (YAML Configuration Manifest with Inlined Fallbacks)
KINEMATIC_SYSTEM_PROMPT = cfg.get("prompts.kinematic") or """You are a specialized AI Research Agent analyzing Kinematic Text-to-Motion architectures.

### OBJECTIVE:
Extract core technical information from the provided paper abstracts and output a strictly structured Markdown table.

### FORMATTING RULES:
1. Paper Title & Year: Must be a Markdown link: `[Title (Year)](URL)`
2. GitHub Code Repo: Strictly `[owner/repo](https://github.com/owner/repo)` if verified in input, else `N/A`. Never output raw unformatted URLs.
3. Do not omit or summarize papers. Every paper in the prompt must be represented as a row in the table.

### TABLE COLUMNS:
| Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Architecture (Diffusion/GPT) | Pose Skeleton Used | Key Metrics (FID, etc.) | Limitations |
"""

PHYSICS_DIFFUSION_SYSTEM_PROMPT = cfg.get("prompts.physics") or """You are an expert in Physics-Guided Generative Human Motion Models.

### OBJECTIVE:
Extract dynamic and physical constraints from the provided paper abstracts and output a structured Markdown table.

### FORMATTING RULES:
1. Paper Title & Year: Must be a Markdown link: `[Title (Year)](URL)`
2. GitHub Code Repo: Strictly `[owner/repo](https://github.com/owner/repo)` if verified in input, else `N/A`. Never output raw unformatted URLs.
3. Highlight explicit physical equations, friction cones, and ground contact solvers.
4. Do not omit or summarize papers. Every paper in the prompt must be represented as a row in the table.

### TABLE COLUMNS:
| Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Physics Integration Method | Physics Engine (MuJoCo/Isaac) | Physical Metrics | Limitations |
"""

RL_CONTROL_SYSTEM_PROMPT = cfg.get("prompts.rl") or """You are an expert specializing in Reinforcement Learning for physics-based character control.

### OBJECTIVE:
Analyze torque-driven policies, reward functions, and simulation setups, outputting a structured Markdown table.

### FORMATTING RULES:
1. Paper Title & Year: Must be a Markdown link: `[Title (Year)](URL)`
2. GitHub Code Repo: Strictly `[owner/repo](https://github.com/owner/repo)` if verified in input, else `N/A`. Never output raw unformatted URLs.
3. Do not omit or summarize papers. Every paper in the prompt must be represented as a row in the table.

### TABLE COLUMNS:
| Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | RL Algorithm (PPO, etc.) | Reward Function Components | Simulation Environment | Limitations |
"""

MEDIAPIPE_POSE_SYSTEM_PROMPT = cfg.get("prompts.pose") or """You are an expert in Computer Vision, 3D Pose Estimation, and Vision-to-Pose Bridging.

### OBJECTIVE:
Extract vision pipeline specifications, sensor configurations, and keypoint tracking methods into a structured Markdown table.

### FORMATTING RULES:
1. Paper Title & Year: Must be a Markdown link: `[Title (Year)](URL)`
2. GitHub Code Repo: Strictly `[owner/repo](https://github.com/owner/repo)` if verified in input, else `N/A`. Never output raw unformatted URLs.
3. Do not omit or summarize papers. Every paper in the prompt must be represented as a row in the table.

### TABLE COLUMNS:
| Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Pose Representation (MediaPipe/SMPL) | Translation Mechanism | Robustness to Noise | Limitations |
"""



def analyze_domain(papers_data, prompt, domain_name="domain", telemetry=None):
    """Generic analyzer for any dynamically configured domain sub-agent."""
    if not papers_data:
        return f"No {domain_name} papers found."
    agent_tag = f"sub_agent:{domain_name}" if not domain_name.startswith("sub_agent:") else domain_name
    return run_agent(prompt, format_papers_for_prompt(papers_data), agent_name=agent_tag, telemetry=telemetry)

def analyze_kinematic(papers_data, custom_prompt=None, telemetry=None):
    return analyze_domain(papers_data, custom_prompt or KINEMATIC_SYSTEM_PROMPT, domain_name="kinematic", telemetry=telemetry)

def analyze_physics_diffusion(papers_data, custom_prompt=None, telemetry=None):
    return analyze_domain(papers_data, custom_prompt or PHYSICS_DIFFUSION_SYSTEM_PROMPT, domain_name="physics", telemetry=telemetry)

def analyze_rl_control(papers_data, custom_prompt=None, telemetry=None):
    return analyze_domain(papers_data, custom_prompt or RL_CONTROL_SYSTEM_PROMPT, domain_name="rl", telemetry=telemetry)

def analyze_pose_vision(papers_data, custom_prompt=None, telemetry=None):
    return analyze_domain(papers_data, custom_prompt or MEDIAPIPE_POSE_SYSTEM_PROMPT, domain_name="pose", telemetry=telemetry)



if __name__ == "__main__":
    print("==================================================")
    print("🤖 Sub-Agents Standalone Health Check")
    print("==================================================")
    print(f"[*] Configured LLM Model: {MODEL_NAME}")
    print(f"[*] Base URL: {BASE_URL}")
    print(f"[*] API Key set: {'Yes' if API_KEY else 'No'}")
    print("==================================================")
