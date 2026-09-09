"""
src.core package initialization.
Provides lazy access to configuration and pipeline runner to prevent circular import warnings.
"""

from typing import Any

__all__ = [
    "PipelineConfig",
    "cfg",
    "execute_t2m_research",
]

def __getattr__(name: str) -> Any:
    if name in ("PipelineConfig", "cfg"):
        from src.core.config_loader import PipelineConfig, cfg
        return PipelineConfig if name == "PipelineConfig" else cfg
    if name == "execute_t2m_research":
        from src.core.pipeline_runner import execute_t2m_research
        return execute_t2m_research
    raise AttributeError(f"module 'src.core' has no attribute '{name}'")
