from openai import OpenAI
import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agent_config import API_KEY, BASE_URL, MODEL_NAME

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
        content = response.choices[0].message.content
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

ANTI_LAZY_RULE = (
    "\nCRITICAL INSTRUCTION: You MUST include EVERY single paper provided in the input text in your table. Do not skip, summarize, or omit ANY paper. If there are 15 papers in the prompt, there must be 15 rows in your table!\n"
    "CRITICAL GITHUB RULE: For the 'Code Repository (GitHub)' column, you MUST strictly use the exact repository from 'GitHub Code Repo:' formatted as [owner/repo](https://github.com/owner/repo) (e.g. [GuyTevet/motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model)). If 'GitHub Code Repo:' is 'N/A', you MUST write 'N/A'. Never output raw unformatted URLs, and do NOT extract unverified repositories from abstract text!"
)

# Default System Prompts
KINEMATIC_SYSTEM_PROMPT = """
You are a highly specialized AI research agent analyzing kinematic Text-to-Motion models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column strictly as [owner/repo](https://github.com/owner/repo) if a verified URL is provided in "GitHub Code Repo:", or "N/A" if it says "N/A". Never output raw unformatted URLs.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Architecture (Diffusion/GPT) | Pose Skeleton Used | Key Metrics (FID, etc.) | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

PHYSICS_DIFFUSION_SYSTEM_PROMPT = """
You are an expert in Physics-Guided Generative Motion Models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column strictly as [owner/repo](https://github.com/owner/repo) if a verified URL is provided in "GitHub Code Repo:", or "N/A" if it says "N/A". Never output raw unformatted URLs.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Physics Integration Method | Physics Engine (MuJoCo/Isaac) | Physical Metrics | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

RL_CONTROL_SYSTEM_PROMPT = """
You are an expert specializing in Reinforcement Learning for physics-based character control.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column strictly as [owner/repo](https://github.com/owner/repo) if a verified URL is provided in "GitHub Code Repo:", or "N/A" if it says "N/A". Never output raw unformatted URLs.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | RL Algorithm (PPO, etc.) | Reward Function Components | Simulation Environment | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

MEDIAPIPE_POSE_SYSTEM_PROMPT = """
You are an expert in computer vision, 3D pose estimation, and vision-to-pose bridging.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column strictly as [owner/repo](https://github.com/owner/repo) if a verified URL is provided in "GitHub Code Repo:", or "N/A" if it says "N/A". Never output raw unformatted URLs.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Pose Representation (MediaPipe/SMPL) | Translation Mechanism | Robustness to Noise | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE


def analyze_kinematic(papers_data, custom_prompt=None, telemetry=None):
    if not papers_data: return "No kinematic papers found."
    prompt = custom_prompt or KINEMATIC_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data), agent_name="sub_agent:kinematic", telemetry=telemetry)

def analyze_physics_diffusion(papers_data, custom_prompt=None, telemetry=None):
    if not papers_data: return "No physics/diffusion papers found."
    prompt = custom_prompt or PHYSICS_DIFFUSION_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data), agent_name="sub_agent:physics", telemetry=telemetry)

def analyze_rl_control(papers_data, custom_prompt=None, telemetry=None):
    if not papers_data: return "No RL papers found."
    prompt = custom_prompt or RL_CONTROL_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data), agent_name="sub_agent:rl", telemetry=telemetry)

def analyze_pose_vision(papers_data, custom_prompt=None, telemetry=None):
    if not papers_data: return "No Pose/Vision papers found."
    prompt = custom_prompt or MEDIAPIPE_POSE_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data), agent_name="sub_agent:pose", telemetry=telemetry)



if __name__ == "__main__":
    print("==================================================")
    print("🤖 Sub-Agents Standalone Health Check")
    print("==================================================")
    print(f"[*] Configured LLM Model: {MODEL_NAME}")
    print(f"[*] Base URL: {BASE_URL}")
    print(f"[*] API Key set: {'Yes' if API_KEY else 'No'}")
    print("==================================================")
