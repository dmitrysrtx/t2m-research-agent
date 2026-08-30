"""
title: T2M Academic Research Pipeline (IEEE Strictly)
author: Dmitry Strizhak
version: 1.2.0
license: MIT
description: Multi-agent academic research pipeline strictly searching IEEE Xplore (EZproxy) with LLM Sub-Agents.
"""

import os
import sys
from typing import List, Union, Generator, Iterator

# Ensure project root is in python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.fetchers.ieee_fetcher import fetch_ieee_papers
from src.utils.pdf_downloader import download_pdfs
from src.agents.sub_agents import (
    analyze_kinematic, 
    analyze_physics_diffusion, 
    analyze_rl_control, 
    analyze_pose_vision
)
from src.agents.orchestrator import synthesize_literature_review

class Pipeline:
    def __init__(self):
        self.name = "T2M Research Agent (IEEE Strictly + EZproxy)"

    async def on_startup(self):
        print(f"[*] T2M Research Pipeline initialized. Root: {PROJECT_ROOT}")

    async def on_shutdown(self):
        print("[*] T2M Research Pipeline shut down.")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main execution flow triggered when chatting with the T2M Research Agent model in Open WebUI.
        """
        query = user_message.strip() if user_message else "text-to-motion human motion"
        
        # 1. FETCH IEEE PAPERS PER SUB-AGENT DOMAIN
        kinematic_papers = fetch_ieee_papers(query=f"{query} kinematics body model", max_results=5)
        physics_papers = fetch_ieee_papers(query=f"{query} physics diffusion contact", max_results=5)
        rl_papers = fetch_ieee_papers(query=f"{query} reinforcement learning character control", max_results=5)
        pose_papers = fetch_ieee_papers(query=f"{query} 3d pose estimation smpl", max_results=5)
        
        all_papers = kinematic_papers + physics_papers + rl_papers + pose_papers
        
        # Deduplicate
        seen = set()
        unique_papers = []
        for p in all_papers:
            key = p.get('url') or p.get('title')
            if key not in seen:
                seen.add(key)
                unique_papers.append(p)

        # 2. DOWNLOAD PDFs (IEEE ONLY, EZproxy enabled)
        download_count = download_pdfs(unique_papers, output_dir="articles")
        
        # 3. SUB-AGENT ANALYSIS
        kinematic_res = analyze_kinematic(kinematic_papers)
        physics_res = analyze_physics_diffusion(physics_papers)
        rl_res = analyze_rl_control(rl_papers)
        pose_res = analyze_pose_vision(pose_papers)
        
        # 4. ORCHESTRATOR SYNTHESIS
        review = synthesize_literature_review(
            kinematic_res,
            physics_res,
            rl_res,
            pose_res
        )
        
        output = f"# 🎓 T2M IEEE Academic Research Report\n\n"
        output += f"**Query:** `{query}` | **IEEE Unique Papers Processed:** {len(unique_papers)}\n"
        output += f"**IEEE PDFs Secured:** {download_count} stored in `articles/`\n\n"
        output += f"---\n\n"
        output += f"## 🔍 Intermediate Sub-Agent Findings (IEEE Sources & Tables)\n\n"
        output += f"### 1. Kinematic Models Sub-Agent\n{kinematic_res}\n\n"
        output += f"### 2. Physics & Diffusion Sub-Agent\n{physics_res}\n\n"
        output += f"### 3. RL Control Sub-Agent\n{rl_res}\n\n"
        output += f"### 4. Pose & Vision Sub-Agent\n{pose_res}\n\n"
        output += f"---\n\n"
        output += f"# 🏛️ Master Literature Synthesis (Orchestrator)\n\n"
        output += review
        
        return output
