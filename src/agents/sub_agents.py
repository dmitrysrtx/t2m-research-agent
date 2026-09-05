from openai import OpenAI
import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agent_config import API_KEY, BASE_URL, MODEL_NAME

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

def run_agent(system_prompt, user_prompt):
    if not API_KEY or API_KEY == "your_api_key_here":
        return "[!] API Key is missing. Please configure the .env file."
        
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[!] Agent Error: {str(e)}"

def format_papers_for_prompt(papers_data):
    prompt = f"Analyze the following {len(papers_data)} papers:\n\n"
    for i, p in enumerate(papers_data):
        citations = p.get('citations', 'N/A')
        impact_factor = p.get('impact_factor', 'N/A')
        github_url = p.get('github_url', 'N/A')
        prompt += (
            f"--- Paper {i+1} ---\n"
            f"Title: {p.get('title', 'N/A')} ({p.get('year', 'N/A')})\n"
            f"Citations: {citations}\n"
            f"Impact Factor / Rank: {impact_factor}\n"
            f"GitHub Code Repo: {github_url}\n"
            f"URL: {p.get('url', 'N/A')}\n"
            f"Abstract: {p.get('abstract', 'N/A')}\n\n"
        )
    return prompt

ANTI_LAZY_RULE = "\nCRITICAL INSTRUCTION: You MUST include EVERY single paper provided in the input text in your table. Do not skip, summarize, or omit ANY paper. If there are 15 papers in the prompt, there must be 15 rows in your table!"

# Default System Prompts
KINEMATIC_SYSTEM_PROMPT = """
You are a highly specialized AI research agent analyzing kinematic Text-to-Motion models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column as a Markdown hyperlink if a valid URL is provided, or "N/A" if unavailable.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Architecture (Diffusion/GPT) | Pose Skeleton Used | Key Metrics (FID, etc.) | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

PHYSICS_DIFFUSION_SYSTEM_PROMPT = """
You are an expert in Physics-Guided Generative Motion Models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column as a Markdown hyperlink if a valid URL is provided, or "N/A" if unavailable.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Physics Integration Method | Physics Engine (MuJoCo/Isaac) | Physical Metrics | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

RL_CONTROL_SYSTEM_PROMPT = """
You are an expert specializing in Reinforcement Learning for physics-based character control.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column as a Markdown hyperlink if a valid URL is provided, or "N/A" if unavailable.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | RL Algorithm (PPO, etc.) | Reward Function Components | Simulation Environment | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

MEDIAPIPE_POSE_SYSTEM_PROMPT = """
You are an expert in computer vision, 3D pose estimation, and vision-to-pose bridging.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Format the "Code Repository (GitHub)" column as a Markdown hyperlink if a valid URL is provided, or "N/A" if unavailable.
Columns: | Paper Title & Year | Citations | Impact Factor | Code Repository (GitHub) | Pose Representation (MediaPipe/SMPL) | Translation Mechanism | Robustness to Noise | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE


def analyze_kinematic(papers_data, custom_prompt=None):
    if not papers_data: return "No kinematic papers found."
    prompt = custom_prompt or KINEMATIC_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data))

def analyze_physics_diffusion(papers_data, custom_prompt=None):
    if not papers_data: return "No physics/diffusion papers found."
    prompt = custom_prompt or PHYSICS_DIFFUSION_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data))

def analyze_rl_control(papers_data, custom_prompt=None):
    if not papers_data: return "No RL papers found."
    prompt = custom_prompt or RL_CONTROL_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data))

def analyze_pose_vision(papers_data, custom_prompt=None):
    if not papers_data: return "No Pose/Vision papers found."
    prompt = custom_prompt or MEDIAPIPE_POSE_SYSTEM_PROMPT
    return run_agent(prompt, format_papers_for_prompt(papers_data))


if __name__ == "__main__":
    print("==================================================")
    print("🤖 Sub-Agents Standalone Health Check")
    print("==================================================")
    print(f"[*] Configured LLM Model: {MODEL_NAME}")
    print(f"[*] Base URL: {BASE_URL}")
    print(f"[*] API Key set: {'Yes' if API_KEY else 'No'}")
    print("==================================================")
