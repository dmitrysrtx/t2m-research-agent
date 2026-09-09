import os
import re
import copy
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "pipeline_config.yaml")

# Preload .env into environment
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _expand_env_vars(data: Any) -> Any:
    """Recursively expands ${VAR_NAME} and ${VAR_NAME:-default} in configuration strings."""
    if isinstance(data, str):
        def _replace_match(m: re.Match) -> str:
            expr = m.group(1).strip()
            if ":-" in expr:
                var_name, default_val = expr.split(":-", 1)
                val = os.getenv(var_name.strip())
                return val if val is not None and val != "" else default_val
            return os.getenv(expr, "")
        return re.sub(r'\$\{([^}]+)\}', _replace_match, data)
    elif isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    return data


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges overrides onto base dictionary, supporting dot-notation keys."""
    result = copy.deepcopy(base)
    for key, val in overrides.items():
        if "." in key:
            parts = key.split(".")
            target = result
            for part in parts[:-1]:
                if part not in target or not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = val
        elif isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


class PipelineConfig:
    """
    Singleton Configuration Provider for T2M Research Agent.
    Manages pipeline_config.yaml, profile overrides, and env variable interpolation.
    """
    _instance: Optional["PipelineConfig"] = None
    _raw_data: Dict[str, Any] = {}
    _data: Dict[str, Any] = {}
    _active_profile: str = "default"

    def __new__(cls) -> "PipelineConfig":
        if cls._instance is None:
            cls._instance = super(PipelineConfig, cls).__new__(cls)
            cls._instance.reload()
        return cls._instance

    def reload(self) -> None:
        """Reloads YAML manifest from disk, interpolates environment, and applies active profile."""
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._raw_data = _expand_env_vars(raw)
        else:
            self._raw_data = {}

        self._active_profile = self._raw_data.get("active_profile", "default")
        self._apply_profile(self._active_profile)

    def _apply_profile(self, profile_name: str) -> None:
        """Applies configuration overrides from selected profile."""
        base = copy.deepcopy(self._raw_data)
        profiles = base.get("profiles", {})
        if profile_name and profile_name != "default" and profile_name in profiles:
            overrides = profiles[profile_name]
            clean_overrides = {k: v for k, v in overrides.items() if k != "description"}
            self._data = _deep_merge(base, clean_overrides)
            self._active_profile = profile_name
        else:
            self._data = base
            self._active_profile = profile_name or "default"
        self._data["active_profile"] = self._active_profile

    def set_profile(self, profile_name: str) -> bool:
        """Switches active profile and re-evaluates configuration overrides."""
        profiles = self._raw_data.get("profiles", {})
        if profile_name != "default" and profile_name not in profiles:
            return False
        self._apply_profile(profile_name)
        return True

    def get_profile(self) -> str:
        """Returns the currently active profile name."""
        return self._active_profile

    def list_profiles(self) -> List[str]:
        """Returns list of available profile names."""
        return list(self._raw_data.get("profiles", {}).keys())

    def get(self, path: str, default: Any = None) -> Any:
        """Accesses nested configuration parameter using dot-notation (e.g. 'llm.model_name')."""
        keys = path.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def to_dict(self) -> Dict[str, Any]:
        """Returns deep copy of current active configuration state."""
        return copy.deepcopy(self._data)


# Global singleton instance
cfg = PipelineConfig()
cfg.reload()


if __name__ == "__main__":
    print("==================================================")
    print("🧭 PipelineConfig Standalone Health Check")
    print("==================================================")
    print(f"[*] Config file: {CONFIG_PATH}")
    print(f"[*] Active profile: {cfg.get_profile()}")
    print(f"[*] Available profiles: {cfg.list_profiles()}")
    print(f"[*] LLM Model: {cfg.get('llm.model_name')}")
    print(f"[*] SOTA Bucket Ratio: {cfg.get('scoring_ranking.frontier_bucket_ratio')}")
    print(f"[*] Min Citations: {cfg.get('search_discovery.min_citations')}")
    print(f"[*] Verified Code Boost: {cfg.get('scoring_ranking.verified_code_boost')}")
    print(f"[*] API Key Present: {'Yes' if cfg.get('llm.api_key') else 'No'}")
    print("==================================================")
