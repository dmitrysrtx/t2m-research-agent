"""
title: T2M Academic Research Pipeline (Configurable Valves)
author: Dmitry Strizhak
version: 2.0.0
license: MIT
description: Multi-agent academic research pipeline with configurable sub-agent prompts and search engine toggles.
"""

import os
import sys
from typing import List, Union, Generator, Iterator, Optional
from pydantic import BaseModel, Field

# Ensure agent project directory is in python path
AGENT_PATHS = [
    "/app/t2m-agent",
    "/home/user/projects/RL/Maya_Project/t2m-research-agent",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
]
for p in AGENT_PATHS:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from src.core.pipeline_runner import execute_t2m_research
from src.agents.sub_agents import (
    KINEMATIC_SYSTEM_PROMPT,
    PHYSICS_DIFFUSION_SYSTEM_PROMPT,
    RL_CONTROL_SYSTEM_PROMPT,
    MEDIAPIPE_POSE_SYSTEM_PROMPT
)
from src.agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

class Pipeline:
    class Valves(BaseModel):
        ENABLE_IEEE: Optional[bool] = Field(
            default=True,
            description="Enable paper searching via IEEE Xplore (EZproxy authentication required)"
        )
        ENABLE_SCHOLAR: Optional[bool] = Field(
            default=False,
            description="Enable academic paper searching via Google Scholar Index"
        )
        ENABLE_ARXIV: Optional[bool] = Field(
            default=False,
            description="Enable open preprint searching via ArXiv API"
        )
        ENABLE_SEMANTIC_SCHOLAR: Optional[bool] = Field(
            default=False,
            description="Enable academic paper searching via Semantic Scholar API"
        )
        MAX_RESULTS_PER_DOMAIN: Optional[int] = Field(
            default=5,
            description="Maximum paper results to retrieve per sub-agent domain"
        )
        EZPROXY_COOKIE: Optional[str] = Field(
            default="",
            description="Raw Cookie header string for EZproxy authentication (e.g., ezproxy=...; JSESSIONID=...)"
        )
        EZPROXY_DOMAIN: Optional[str] = Field(
            default="ezproxy.afeka.ac.il",
            description="Institutional EZproxy domain name"
        )
        KINEMATIC_PROMPT: Optional[str] = Field(
            default=KINEMATIC_SYSTEM_PROMPT,
            description="System Prompt for Kinematic Motion Sub-Agent (Markdown supported)"
        )
        PHYSICS_PROMPT: Optional[str] = Field(
            default=PHYSICS_DIFFUSION_SYSTEM_PROMPT,
            description="System Prompt for Physics & Diffusion Sub-Agent (Markdown supported)"
        )
        RL_PROMPT: Optional[str] = Field(
            default=RL_CONTROL_SYSTEM_PROMPT,
            description="System Prompt for Reinforcement Learning Control Sub-Agent (Markdown supported)"
        )
        POSE_PROMPT: Optional[str] = Field(
            default=MEDIAPIPE_POSE_SYSTEM_PROMPT,
            description="System Prompt for 3D Pose & Vision Sub-Agent (Markdown supported)"
        )
        ORCHESTRATOR_PROMPT: Optional[str] = Field(
            default=ORCHESTRATOR_SYSTEM_PROMPT,
            description="System Prompt for Master Orchestrator Synthesizer (Markdown supported)"
        )

    def __init__(self):
        self.name = "T2M Multi-Agent Academic Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[*] T2M Research Pipeline v2.0 initialized successfully.")

    async def on_shutdown(self):
        print("[*] T2M Research Pipeline shut down.")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # 🔄 Dynamic module reload on each execution (Hot-Reloading without Docker restart)
        try:
            import importlib
            import src.core.pipeline_runner
            import src.agents.sub_agents
            import src.agents.orchestrator

            importlib.reload(src.agents.sub_agents)
            importlib.reload(src.agents.orchestrator)
            importlib.reload(src.core.pipeline_runner)
        except Exception as e:
            print(f"[!] Hot reload warning: {e}")

        query = user_message.strip() if user_message else "text-to-motion human motion"

        enable_ieee = True if self.valves.ENABLE_IEEE is None else self.valves.ENABLE_IEEE
        enable_scholar = False if self.valves.ENABLE_SCHOLAR is None else self.valves.ENABLE_SCHOLAR
        enable_arxiv = False if self.valves.ENABLE_ARXIV is None else self.valves.ENABLE_ARXIV
        enable_semantic_scholar = False if self.valves.ENABLE_SEMANTIC_SCHOLAR is None else self.valves.ENABLE_SEMANTIC_SCHOLAR
        max_results = 5 if not self.valves.MAX_RESULTS_PER_DOMAIN else self.valves.MAX_RESULTS_PER_DOMAIN
        ezproxy_cookie = "" if not self.valves.EZPROXY_COOKIE else self.valves.EZPROXY_COOKIE
        ezproxy_domain = "ezproxy.afeka.ac.il" if not self.valves.EZPROXY_DOMAIN else self.valves.EZPROXY_DOMAIN

        return execute_t2m_research(
            query=query,
            enable_ieee=enable_ieee,
            enable_scholar=enable_scholar,
            enable_arxiv=enable_arxiv,
            enable_semantic_scholar=enable_semantic_scholar,
            max_results_per_domain=max_results,
            ezproxy_cookie=ezproxy_cookie,
            ezproxy_domain=ezproxy_domain,
            kinematic_prompt=self.valves.KINEMATIC_PROMPT or KINEMATIC_SYSTEM_PROMPT,
            physics_prompt=self.valves.PHYSICS_PROMPT or PHYSICS_DIFFUSION_SYSTEM_PROMPT,
            rl_prompt=self.valves.RL_PROMPT or RL_CONTROL_SYSTEM_PROMPT,
            pose_prompt=self.valves.POSE_PROMPT or MEDIAPIPE_POSE_SYSTEM_PROMPT,
            orchestrator_prompt=self.valves.ORCHESTRATOR_PROMPT or ORCHESTRATOR_SYSTEM_PROMPT,
            save_output_file=True
        )
