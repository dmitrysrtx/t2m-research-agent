from openai import OpenAI
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY,
)

def run_agent(system_prompt, user_prompt):
    if not config.API_KEY or config.API_KEY == "your_api_key_here":
        return "[!] API Key is missing. Please configure the .env file."
        
    try:
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
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
        prompt += f"--- Paper {i+1} ---\nTitle: {p['title']} ({p['year']})\nURL: {p['url']}\nAbstract: {p['abstract']}\n\n"
    return prompt

# ==========================================
# COMMON ANTI-LAZINESS RULE
# ==========================================
ANTI_LAZY_RULE = "\nCRITICAL INSTRUCTION: You MUST include EVERY single paper provided in the input text in your table. Do not skip, summarize, or omit ANY paper. If there are 15 papers in the prompt, there must be 15 rows in your table!"

# ==========================================
# 1. KINEMATIC EXPERT
# ==========================================
KINEMATIC_SYSTEM_PROMPT = """
You are a highly specialized AI research agent analyzing kinematic Text-to-Motion models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Columns: | Paper Title & Year | Architecture (Diffusion/GPT) | Pose Skeleton Used | Key Metrics (FID, etc.) | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

def analyze_kinematic(papers_data):
    if not papers_data: return "No kinematic papers found."
    return run_agent(KINEMATIC_SYSTEM_PROMPT, format_papers_for_prompt(papers_data))

# ==========================================
# 2. PHYSICS & DIFFUSION EXPERT
# ==========================================
PHYSICS_DIFFUSION_SYSTEM_PROMPT = """
You are an expert in Physics-Guided Generative Motion Models.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Columns: | Paper Title & Year | Physics Integration Method | Physics Engine (MuJoCo/Isaac) | Physical Metrics | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

def analyze_physics_diffusion(papers_data):
    if not papers_data: return "No physics/diffusion papers found."
    return run_agent(PHYSICS_DIFFUSION_SYSTEM_PROMPT, format_papers_for_prompt(papers_data))

# ==========================================
# 3. RL & CHARACTER CONTROL EXPERT
# ==========================================
RL_CONTROL_SYSTEM_PROMPT = """
You are an expert specializing in Reinforcement Learning for physics-based character control.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Columns: | Paper Title & Year | RL Algorithm (PPO, etc.) | Reward Function Components | Simulation Environment | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

def analyze_rl_control(papers_data):
    if not papers_data: return "No RL papers found."
    return run_agent(RL_CONTROL_SYSTEM_PROMPT, format_papers_for_prompt(papers_data))

# ==========================================
# 4. MEDIAPIPE & POSE EXPERT
# ==========================================
MEDIAPIPE_POSE_SYSTEM_PROMPT = """
You are an expert in computer vision, 3D pose estimation, and vision-to-pose bridging.
Extract core information from the provided abstracts and return a structured Markdown table.
Format the "Paper Title & Year" column as a Markdown hyperlink: [Title (Year)](URL).
Columns: | Paper Title & Year | Pose Representation (MediaPipe/SMPL) | Translation Mechanism | Robustness to Noise | Limitations |
Limit response to ONLY the table.""" + ANTI_LAZY_RULE

def analyze_pose_vision(papers_data):
    if not papers_data: return "No Pose/Vision papers found."
    return run_agent(MEDIAPIPE_POSE_SYSTEM_PROMPT, format_papers_for_prompt(papers_data))
