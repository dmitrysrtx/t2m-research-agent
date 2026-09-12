import os
import sys
from typing import Any, Dict, List, Tuple

class ConfigValidationError(ValueError):
    """Raised when pipeline_config.yaml is missing required fields or has invalid values."""
    pass


def validate_pipeline_config(cfg_data: Dict[str, Any]) -> List[str]:
    """
    Strictly validates configuration data from pipeline_config.yaml.
    Returns a list of human-readable error descriptions. Empty list means valid.
    """
    errors: List[str] = []

    if not isinstance(cfg_data, dict):
        return ["Configuration root must be a valid dictionary/mapping."]

    # 1. Validate Sub-Agents Specification
    sub_agents = cfg_data.get("sub_agents")
    if sub_agents is None:
        errors.append("Missing required layer 'sub_agents'. At least one domain sub-agent must be defined.")
    elif not isinstance(sub_agents, list) or len(sub_agents) == 0:
        errors.append("'sub_agents' must be a non-empty list of sub-agent definitions.")
    else:
        seen_ids = set()
        for idx, agent in enumerate(sub_agents):
            if not isinstance(agent, dict):
                errors.append(f"sub_agents[{idx}] must be a dictionary.")
                continue

            aid = str(agent.get("id", "")).strip()
            name = str(agent.get("name", "")).strip()
            queries = agent.get("search_queries")
            prompt = str(agent.get("system_prompt", "")).strip()

            if not aid:
                errors.append(f"sub_agents[{idx}] is missing required parameter 'id' (unique string identifier).")
            elif aid in seen_ids:
                errors.append(f"sub_agents[{idx}] has duplicate identifier 'id: {aid}'. IDs must be strictly unique.")
            else:
                seen_ids.add(aid)

            prefix = f"sub_agents[{aid or idx}]"

            if not name:
                errors.append(f"{prefix} is missing required parameter 'name' (human-readable title).")

            if queries is None:
                errors.append(f"{prefix} is missing required parameter 'search_queries' (list of search queries).")
            elif not isinstance(queries, list) or len(queries) == 0:
                errors.append(f"{prefix}.search_queries must be a non-empty list of academic query strings.")
            else:
                for q_idx, q in enumerate(queries):
                    if not isinstance(q, str) or not q.strip():
                        errors.append(f"{prefix}.search_queries[{q_idx}] cannot be empty.")

            if not prompt:
                errors.append(f"{prefix} is missing required parameter 'system_prompt' (multi-line Markdown prompt).")

    # 2. Validate Master Orchestrator
    orchestrator = cfg_data.get("orchestrator") or {}
    orch_prompt = orchestrator.get("system_prompt") if isinstance(orchestrator, dict) else None
    if not orch_prompt:
        # Fallback check under legacy prompts.orchestrator
        orch_prompt = (cfg_data.get("prompts") or {}).get("orchestrator")

    if not orch_prompt or not str(orch_prompt).strip():
        errors.append("Missing required parameter 'orchestrator.system_prompt' (Master literature review synthesizer prompt).")

    # 3. Validate LLM Layer
    llm = cfg_data.get("llm") or {}
    if not isinstance(llm, dict):
        errors.append("Missing or invalid 'llm' configuration layer.")
    else:
        if not str(llm.get("model_name", "")).strip():
            errors.append("Missing required parameter 'llm.model_name'.")
        if not str(llm.get("base_url", "")).strip():
            errors.append("Missing required parameter 'llm.base_url'.")

    # 4. Validate Search & Discovery Layer
    search = cfg_data.get("search_discovery") or {}
    if isinstance(search, dict):
        max_res = search.get("max_results_per_domain")
        try:
            if max_res is None or int(max_res) < 1:
                errors.append("search_discovery.max_results_per_domain must be an integer >= 1.")
        except (ValueError, TypeError):
            errors.append(f"search_discovery.max_results_per_domain must be a valid integer, got: {max_res}")

    # 5. Validate Scoring & Ranking Formulas
    scoring = cfg_data.get("scoring_ranking") or {}
    if isinstance(scoring, dict):
        fb = scoring.get("frontier_bucket_ratio")
        fo = scoring.get("foundational_bucket_ratio")
        if fb is not None and fo is not None:
            try:
                total_ratio = float(fb) + float(fo)
                if not (0.95 <= total_ratio <= 1.05):
                    errors.append(
                        f"scoring_ranking bucket ratios must sum to 1.0 (frontier: {fb} + foundational: {fo} = {total_ratio:.2f})."
                    )
            except (ValueError, TypeError):
                errors.append("scoring_ranking ratios must be valid numeric values.")

    # 6. Validate PDF Ingestion
    pdf = cfg_data.get("pdf_ingestion") or {}
    if isinstance(pdf, dict):
        if not str(pdf.get("output_dir", "")).strip():
            errors.append("Missing required parameter 'pdf_ingestion.output_dir'.")
        multiplier = pdf.get("candidate_pool_multiplier")
        if multiplier is not None:
            try:
                if float(multiplier) < 1.0:
                    errors.append("pdf_ingestion.candidate_pool_multiplier must be >= 1.0.")
            except (ValueError, TypeError):
                errors.append(f"pdf_ingestion.candidate_pool_multiplier must be numeric, got: {multiplier}")

    return errors


def enforce_valid_config(cfg_data: Dict[str, Any]) -> None:
    """Validates configuration and raises ConfigValidationError if any issues exist."""
    errors = validate_pipeline_config(cfg_data)
    if errors:
        msg = (
            "❌ Configuration Validation Failed (pipeline_config.yaml):\n"
            + "\n".join(f"  • {e}" for e in errors)
            + "\n\nPlease rectify the missing or invalid parameters before running the research agent."
        )
        raise ConfigValidationError(msg)


if __name__ == "__main__":
    print("==================================================")
    print("🔍 Configuration Validator Standalone Health Check")
    print("==================================================")

    # Test 1: Empty config
    errs_empty = validate_pipeline_config({})
    print(f"[*] Empty config errors detected: {len(errs_empty)}")
    assert len(errs_empty) >= 3, "Should detect multiple errors on empty config"

    # Test 2: Missing prompt in sub-agent
    sample_bad_agent = {
        "llm": {"model_name": "test", "base_url": "http://test"},
        "sub_agents": [
            {
                "id": "test_agent",
                "name": "Test Agent",
                "search_queries": ["query 1"],
                "system_prompt": ""  # Missing!
            }
        ],
        "orchestrator": {"system_prompt": "Orchestrator prompt"},
        "pdf_ingestion": {"output_dir": "articles", "candidate_pool_multiplier": 1.5}
    }
    errs_bad_prompt = validate_pipeline_config(sample_bad_agent)
    print(f"[*] Missing prompt test detected error: {errs_bad_prompt[0] if errs_bad_prompt else 'None'}")
    assert any("system_prompt" in e for e in errs_bad_prompt), "Should detect missing system_prompt"

    print("✅ All Validator Health Checks Passed Successfully!")
    print("==================================================")
