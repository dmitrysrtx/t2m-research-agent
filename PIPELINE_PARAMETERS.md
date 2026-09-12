# 🧭 T2M Pipeline Parameter Catalog & Configuration Reference

This document provides a comprehensive inventory of **every configurable parameter** across all layers of the academic literature review and discovery pipeline.

---

## 📑 Summary of Pipeline Layers

1. [LLM Provider & Generation Layer](#1-llm-provider--generation-layer)
2. [Academic Search & Discovery Layer](#2-academic-search--discovery-layer)
3. [Dual-Bucket Ranking & Scoring Formulas](#3-dual-bucket-ranking--scoring-formulas)
4. [Artifact & GitHub Code Verification](#4-artifact--github-code-verification)
5. [PDF Acquisition & Ingestion Cascade](#5-pdf-acquisition--ingestion-cascade)
6. [Sub-Agent & Orchestrator Prompts](#6-sub-agent--orchestrator-prompts)
7. [Telemetry, Storage & Output](#7-telemetry-storage--output)

---

## 1. LLM Provider & Generation Layer

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Model Identifier** | `MODEL_NAME` | `anthropic/claude-3.5-sonnet` | String (e.g. `google/gemini-2.5-pro`) | Main LLM used for extraction, reasoning, and synthesis. |
| **API Base URL** | `API_BASE_URL` | `https://openrouter.ai/api/v1` | String (URL) | OpenAI-compatible endpoint (OpenRouter, LiteLLM, vLLM, Ollama). |
| **API Key** | `OPENROUTER_API_KEY` | `""` | Secret String | Authentication token for the LLM provider. |
| **Sub-Agent Temperature** | `SUBAGENT_TEMPERATURE` | `0.1` - `0.2` | Float `[0.0 - 1.0]` | Lower values enforce deterministic, hallucination-free extraction from paper abstracts and PDFs. |
| **Orchestrator Temperature** | `ORCHESTRATOR_TEMPERATURE` | `0.3` | Float `[0.0 - 1.0]` | Slightly higher temperature allows creative academic prose and smooth comparative synthesis. |
| **Sub-Agent Max Tokens** | `SUBAGENT_MAX_TOKENS` | `4096` | Integer `[1024 - 8192]` | Upper bound on output tokens per domain sub-agent table. |
| **Orchestrator Max Tokens** | `ORCHESTRATOR_MAX_TOKENS` | `8192` | Integer `[2048 - 16384]` | Upper bound on tokens for the master literature review report. |

---

## 2. Academic Search & Discovery Layer

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Default Search Query** | `DEFAULT_SEARCH_QUERY` | `text-to-motion human motion` | String | Fallback query if no user prompt is supplied. |
| **Enable Semantic Scholar** | `ENABLE_SEMANTIC_SCHOLAR` | `True` | Boolean | Primary single-source-of-truth search engine. |
| **Semantic Scholar API Key** | `SEMANTIC_SCHOLAR_API_KEY` | `""` | Secret String | Increases rate limits from 1 req/s to 10 req/s. |
| **Enable IEEE Xplore** | `ENABLE_IEEE` | `False` | Boolean | Direct IEEE Xplore search (disabled by default in favor of S2 IEEE indexing). |
| **Enable ArXiv Direct** | `ENABLE_ARXIV` | `False` | Boolean | Direct ArXiv API search. |
| **Enable Google Scholar** | `ENABLE_SCHOLAR` | `False` | Boolean | Google Scholar scraping/SerpApi (disabled to prevent captchas). |
| **Fields of Study Filter** | `FIELDS_OF_STUDY` | `Computer Science,Engineering` | Comma-separated | Hard lock preventing cross-domain noise (e.g. sports medicine, thermodynamics). |
| **Publication Year Range** | `YEAR_RANGE` | `None` (or `2018-2026`) | String `YYYY-YYYY` | Restricts discovery to specific temporal windows. |
| **Minimum Citation Threshold** | `MIN_CITATIONS` | `0` | Integer `[0 - 50]` | Hard threshold excluding low-signal or unvetted papers. |
| **Domain Result Limit** | `MAX_RESULTS_PER_DOMAIN` | `5` | Integer `[3 - 15]` | Target number of papers per sub-agent (4 domains $\times$ 5 = 20 total). |

---

## 3. Dual-Bucket Ranking & Scoring Formulas

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Frontier SOTA Ratio** | `FRONTIER_BUCKET_RATIO` | `0.65` (65%) | Float `[0.0 - 1.0]` | Percentage of final papers dedicated to cutting-edge recent works ($\le 2$ years). |
| **Foundational Ratio** | `FOUNDATIONAL_BUCKET_RATIO` | `0.35` (35%) | Float `[0.0 - 1.0]` | Percentage of final papers dedicated to highly-cited seminal milestones. |
| **Recent SOTA Year Threshold** | `RECENT_YEAR_WINDOW` | `2` (years) | Integer `[1 - 4]` | Papers published in $\ge (\text{current\_year} - 2)$ qualify for Frontier ranking. |
| **Influential Citation Multiplier** | `INFLUENTIAL_CITATION_WEIGHT` | `2.5` | Float `[1.0 - 5.0]` | Multiplier for citations marked influential by Semantic Scholar. |
| **Time Delta Epsilon ($\Delta t_{min}$)** | `TIME_DELTA_MIN` | `0.5` | Float `[0.1 - 1.0]` | Minimum time denominator to prevent infinite citation velocity for brand-new papers. |
| **Tier 1 Venue Multiplier** | `VENUE_TIER_1_WEIGHT` | `1.8 - 2.0` | Float `[1.5 - 2.5]` | CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR, SIGGRAPH, ICRA, IROS, TPAMI. |
| **Tier 2 Venue Multiplier** | `VENUE_TIER_2_WEIGHT` | `1.35` | Float `[1.1 - 1.5]` | WACV, 3DV, BMVC, IEEE RA-L, CVIU. |
| **Tier 3 / Baseline Weight** | `VENUE_TIER_3_WEIGHT` | `1.0` | Float | Generic workshops, preprints, or unranked conferences. |
| **Verified Code Score Boost** | `VERIFIED_CODE_BOOST` | `+25.0` | Float `[0.0 - 50.0]` | Score boost awarded to papers with an authenticated, working GitHub repository. |

---

## 4. Artifact & GitHub Code Verification

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Require Verified Code** | `REQUIRE_CODE` | `False` | Boolean | If `True`, strictly drops any paper lacking a verified GitHub repo. |
| **Prefer Verified Code** | `PREFER_CODE` | `True` | Boolean | If `True`, awards `VERIFIED_CODE_BOOST` to rank code-backed papers higher. |
| **GitHub Verification Workers** | `GITHUB_MAX_WORKERS` | `8` | Integer `[1 - 16]` | Number of concurrent threads for parallel repo verification. |
| **HTTP Connect Timeout** | `GITHUB_CONNECT_TIMEOUT` | `2.0` (sec) | Float `[1.0 - 5.0]` | Socket connection timeout for probing GitHub repositories and project pages. |
| **HTTP Read Timeout** | `GITHUB_READ_TIMEOUT` | `3.0` (sec) | Float `[1.0 - 10.0]` | Response read timeout for probing GitHub repositories. |
| **GitHub API Token** | `GITHUB_TOKEN` | `""` | Secret String | Optional GitHub PAT to increase Search API limit from 60 to 5,000 req/hr. |

---

## 5. PDF Acquisition & Ingestion Cascade

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Target Verified PDF Count** | `TARGET_PDF_COUNT` | Derived (`NUM_DOMAINS * MAX_RESULTS_PER_DOMAIN`) | Integer | Automatically computed total target of verified PDFs across all configured sub-agent domains (`NUM_DOMAINS = len(sub_agents)`). |
| **Candidate Buffer Multiplier** | `CANDIDATE_POOL_MULTIPLIER` | `1.5` | Float `[1.2 - 2.0]` | Fetches `max_results_per_domain * 1.5` candidates per domain (e.g. 15 papers) to guarantee full-text quota. |
| **Articles Output Folder** | `ARTICLES_OUTPUT_DIR` | `articles/` | Path | Local directory where binary `.pdf` files are stored. |
| **EZProxy Domain** | `EZPROXY_DOMAIN` | `ezproxy.afeka.ac.il` | String | Institutional proxy host for Afeka College SSO authentication. |
| **Auto 2FA SSO Login** | `AUTO_SSO_LOGIN` | `True` | Boolean | Automatically maintains/renews institutional session cookies via Playwright. |
| **Unpaywall Contact Email** | `UNPAYWALL_EMAIL` | `academic_bot@afeka.ac.il` | Email String | Required email parameter for querying the Unpaywall Open Access API. |
| **PDF Download Timeout** | `PDF_DOWNLOAD_TIMEOUT` | `25` (sec) | Integer `[10 - 60]` | Maximum timeout per PDF download stream. |
| **Max PDF File Size** | `PDF_MAX_SIZE_MB` | `50` (MB) | Integer `[10 - 200]` | Prevents downloading corrupt or gigantic multimedia attachments. |

---

## 6. Dynamic Sub-Agents & Strict Validation

Sub-agents are configured dynamically via the `sub_agents:` list in `pipeline_config.yaml`. The framework supports any number of domain agents ($1 \dots N$).

### Sub-Agent Specification Schema
Each sub-agent entry requires:
- `id`: Unique string key (e.g. `kinematic`, `physics`, `rl`, `pose`)
- `name`: Human-readable title (e.g. `Kinematic Text-to-Motion Models`)
- `search_queries`: Non-empty list of academic query strings
- `system_prompt`: Multi-line Markdown template specifying role, objective, and table columns

### Fail-Fast Schema Validation (`src/core/config_validator.py`)
On startup and reload, the validator enforces that:
- Every sub-agent has all 4 required fields (`id`, `name`, `search_queries`, `system_prompt`).
- No sub-agent IDs are duplicated.
- Master `orchestrator.system_prompt` is defined.
- If any parameter is missing or empty, execution halts immediately with a clear error pinpointing the exact missing parameter.

| Default Sub-Agent | Identifier | Search Queries Count | Role & Specialization |
| :--- | :--- | :--- | :--- |
| **Kinematic Models** | `kinematic` | 3 queries | Evaluates VAEs, Transformers, Vector-Quantized models, latent representations. |
| **Physics & Diffusion** | `physics` | 3 queries | Evaluates physical constraints, contact manifolds, friction cones, loss formulations. |
| **RL Character Control** | `rl` | 3 queries | Evaluates torque-driven policies, tracking rewards, PD control, and MuJoCo/Isaac sim. |
| **Pose & Vision** | `pose` | 3 queries | Evaluates monocular/stereo pose estimation, MediaPipe/SMPL keypoint pipelines. |
| **Master Orchestrator** | `orchestrator` | Synthesizer | Synthesizes all domain reports, compares benchmarks, formulates mathematical equations and thesis research gaps. |

---

## 7. Telemetry, Storage & Output

| Parameter | Environment Variable | Default Value | Type / Range | Description & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Default Markdown Report** | `DEFAULT_OUTPUT_FILE` | `LITERATURE_REVIEW.md` | Path | Target file path for the complete generated literature review. |
| **CLI Logging Enabled** | `ENABLE_CLI_LOGS` | `True` | Boolean | Pretty-prints colored progress bars and sub-agent step telemetry in terminal. |
| **Langfuse Host** | `LANGFUSE_HOST` | `http://192.168.68.53:3005` | URL | Self-hosted Langfuse observability platform endpoint. |
| **Langfuse Public Key** | `LANGFUSE_PUBLIC_KEY` | `""` | Secret String | Langfuse project public tracking key. |
| **Langfuse Secret Key** | `LANGFUSE_SECRET_KEY` | `""` | Secret String | Langfuse project secret key. |

---

## 🛠️ Recommended Profile Configurations (Presets)

### Profile A: *Fast Frontier SOTA (Last 18 Months)*
- `FRONTIER_BUCKET_RATIO = 0.85`
- `RECENT_YEAR_WINDOW = 1`
- `PREFER_CODE = True`
- `MIN_CITATIONS = 0`

### Profile B: *Comprehensive Master's Thesis Foundations (Classic + SOTA)*
- `FRONTIER_BUCKET_RATIO = 0.60`
- `FOUNDATIONAL_BUCKET_RATIO = 0.40`
- `RECENT_YEAR_WINDOW = 2`
- `VENUE_TIER_1_WEIGHT = 2.0`
- `MIN_CITATIONS = 5`

### Profile C: *Code-First Implementation & Reproducibility Audit*
- `REQUIRE_CODE = True`
- `VERIFIED_CODE_BOOST = 50.0`
- `GITHUB_MAX_WORKERS = 12`
