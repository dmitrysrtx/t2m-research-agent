# Gemini Project Guidelines: T2M Academic Research Agent

## Project Context & Overview
The **T2M Academic Research Agent** is a multi-agent framework for automated literature review synthesis in the domain of Text-to-Motion (T2M) human motion generation, physics-guided diffusion, reinforcement learning character control, and 3D pose estimation.

The framework fetches paper metadata from academic engines (IEEE Xplore via EZproxy, ArXiv, Google Scholar / OpenAlex, Semantic Scholar), downloads full-text PDFs into `articles/`, analyzes paper sets across domain-expert sub-agents, synthesizes a master literature review chapter into `LITERATURE_REVIEW.md`, and enriches it with peer-review citation metadata via CrossRef/ArXiv.

## Core Language & Communication Rule
- **Project Codebase & Documentation**: ALL code, docstrings, comments, commit messages, and markdown files within the repository MUST be written in **English**.
- **User Communication**: Chat interactions with the user MUST be in **Russian**.

## Directory & File Structure
```
t2m-research-agent/
├── main.py                     # CLI entry point (runs pipeline runner engine)
├── config.py                   # Environment configuration alias
├── agent_config.py             # Backward-compatible configuration bridge
├── pipeline_config.yaml        # Master YAML Configuration Manifest (Single Source of Truth)
├── Makefile                    # Automation targets (setup, run, enrich, clean)
├── README.md                   # Public repository documentation
├── Gemini.md                   # Agent system guidelines & project map (this file)
├── ezproxy_cookies.json        # Stored session cookies for institutional EZproxy access
├── LITERATURE_REVIEW.md        # Master generated literature review report (Project Root)
├── articles/                   # Target directory reserved EXCLUSIVELY for downloaded PDF papers
├── openwebui/
│   ├── t2m_pipeline.py         # Open WebUI Pipeline runner interface with dynamic reload
│   └── t2m_openwebui_tool.py   # Open WebUI standalone search tool
└── src/
    ├── auth/                   # Layer 1: Institutional Authentication & Session Management
    │   ├── __init__.py         # Package exports & lazy attribute loader
    │   ├── ezproxy_session.py  # Unified EZProxyManager & Session Engine
    │   ├── afeka_sso.py        # Playwright-based browser 2FA SSO automation
    │   ├── ezproxy_auth.py     # URL conversion & live IEEE access verification
    │   ├── import_cookies.py   # Interactive CLI cookie importer helper
    │   ├── playwright_login.py # Backward-compatible browser login alias
    │   └── sso_login.py        # Standalone SSO authentication runner
    ├── fetchers/                 # Layer 2: Metadata Fetchers & Citation Enrichment
    │   ├── arxiv_fetcher.py            # ArXiv API search fetcher
    │   ├── ieee_fetcher.py             # IEEE Xplore (OpenAlex / CrossRef / IEEE API) fetcher
    │   ├── scholar_fetcher.py          # Google Scholar (via OpenAlex) fetcher
    │   ├── semantic_scholar_fetcher.py # Semantic Scholar API fetcher
    │   ├── github_verifier.py          # URL Normalization & Streaming Liveness Prober
    │   ├── github_finder.py            # Multi-Tier GitHub Code Repository Discovery Engine
    │   └── citation_enricher.py        # CrossRef & ArXiv Academic Credibility Enricher
    ├── agents/                 # Layer 3: Domain Agents & Synthesis
    │   ├── orchestrator.py     # Master Orchestrator prompt & synthesis logic
    │   └── sub_agents.py       # Domain expert sub-agents (Kinematic, Physics, RL, Pose)
    ├── core/                   # Layer 4: Configuration & Pipeline Execution Engine
    │   ├── __init__.py         # Core package exports with lazy loading
    │   ├── config_loader.py    # Singleton PipelineConfig, env interpolator & profile switcher
    │   ├── config_validator.py # Strict schema validation & missing parameter diagnostics
    │   └── pipeline_runner.py  # High-level dynamic pipeline coordinator & review assembler
    ├── telemetry/              # Layer 5: Decoupled Telemetry & Event Dispatcher
    │   ├── __init__.py         # Package exports & get_telemetry() factory
    │   ├── events.py           # EventType enum & TelemetryEvent data model
    │   ├── manager.py          # Central TelemetryManager (Event Dispatcher)
    │   └── handlers/           # Modular telemetry sinks
    │       ├── __init__.py     # Handler exports
    │       ├── base.py         # BaseHandler abstract sink interface
    │       ├── terminal.py     # TerminalHandler (rich 1-line progress, zero raw JSON)
    │       ├── langfuse_sink.py# LangfuseHandler (v3 SDK, background thread, no stdout)
    │       └── sse.py          # SSEHandler (thread-safe Queue & SSE stream generator)
    └── utils/                  # Layer 6: Cross-Cutting Utilities
        ├── logger.py           # Logging utility (file-only)
        └── pdf_downloader.py   # PDF downloader engine using authenticated sessions
```

## Architectural Decision Log

### 2026-09-12: Resolution of `[Errno 2]` Race Condition, OpenWebUI Metadata Task Interception & Mutex Concurrency Lock
- **Goal**: Resolve fatal `[Errno 2] No such file or directory: 'Motion Guided 3D Pose Estimation from Videos.pdf'` crash during pipeline startup with `clear_articles_dir: true`, intercept OpenWebUI's nested `body["metadata"]["task"]` requests, enforce single-flight pipeline execution via a global mutex (`_PIPELINE_LOCK`), and make directory deletion in `pipeline_runner.py` completely resilient.
- **Root Causes & Key Changes**:
  1. **OpenWebUI Nested Task Metadata Structure (`openwebui/t2m_pipeline.py`)**:
     - OpenWebUI (`/app/backend/open_webui/routers/tasks.py`) dispatches background utility tasks with `'metadata': {'task': str(TASKS.TITLE_GENERATION), ...}` and `'stream': False`, NOT at the top-level `body["task"]`.
     - In addition, OpenWebUI sends follow-up prompts (`### Task: Suggest 3-5 relevant follow-up questions...`) with `stream: False`. Without catching these, they launched 10-minute research pipelines in the background.
     - **Fix**: Expanded fast-path interception to check `not is_stream or task or "### task:" in msg_content`. Instant metadata responses (titles, tags, suggested follow-ups) are returned within 1 ms without touching `_stream_pipeline`.
  2. **Concurrent Execution & `shutil.rmtree` Race Condition (`src/core/pipeline_runner.py`, `openwebui/t2m_pipeline.py`)**:
     - When the chat completion and title generation ran simultaneously, both called `execute_t2m_research(..., clear_articles_dir=True)`.
     - Both threads invoked `shutil.rmtree(articles_dir)`. Thread 2 deleted files while Thread 1's `os.unlink` was iterating through the directory, triggering `FileNotFoundError: [Errno 2] No such file or directory: 'Motion Guided 3D Pose Estimation from Videos.pdf'`.
     - **Fix 1**: Added `shutil.rmtree(articles_dir, ignore_errors=True)` wrapped in `try...except` to prevent unhandled filesystem exceptions on transient or concurrent file removals.
     - **Fix 2**: Introduced a process-level `_PIPELINE_LOCK = threading.Lock()` in `openwebui/t2m_pipeline.py`. If a research pipeline is already active, subsequent requests yield an informative busy notice displaying the active query and elapsed running time.
     - **Fix 3**: Explicitly bypassed `_PIPELINE_LOCK` for `/login` commands so authentication never blocks or holds the pipeline mutex.
     - **Fix 4**: Placed `_PIPELINE_LOCK.acquire()` immediately before research synthesis and guaranteed release via `try...finally:`.
  3. **Full Exception Traceback Logging (`openwebui/t2m_pipeline.py`)**:
     - Added `traceback.print_exc()` inside `runner_worker()`'s `except Exception as e:` block to ensure future exceptions are visible in container logs.
  4. **File Permissions & Host Ownership**:
     - Maintained `0o666` permissions and `dmitryx:dmitryx` ownership across all modified files.

### 2026-09-12: Elimination of OpenWebUI Valves, YAML SSOT Consolidation, Background Task Interceptor & Articles Cleanup
- **Goal**: Eliminate the dual source-of-truth problem created by OpenWebUI Valves, establish `pipeline_config.yaml` as the sole Single Source of Truth (SSOT) across both CLI (`main.py`) and OpenWebUI (`openwebui/t2m_pipeline.py`), intercept OpenWebUI utility tasks (`title_generation`, `tags_generation`) to prevent concurrent pipeline execution, fix the `clear_articles_dir` parameter evaluation bug, and clean up orphaned PDF articles.
- **Root Causes & Key Changes**:
  1. **OpenWebUI Background Concurrency & Race Condition (`openwebui/t2m_pipeline.py`)**:
     - When users send chat messages, OpenWebUI issues two concurrent requests: the streaming chat completion (`stream: true`) and an internal utility request (`task: "title_generation"`, `stream: false`).
     - Without task interception, `t2m_pipeline` launched two parallel 10-minute research pipelines, causing simultaneous Semantic Scholar requests, triggering HTTP 429 rate limits, inducing divergent fallback candidate pools, and downloading overlapping PDFs into `articles/`.
     - **Fix**: Separated `pipe()` entry point from `_stream_pipeline()`. If `body.get("task") == "title_generation"` (or `tags_generation`), `pipe()` returns an instant string title or tags list within 1 ms without launching the heavy research pipeline.
  2. **Elimination of OpenWebUI Valves in Favor of YAML SSOT (`openwebui/t2m_pipeline.py`, `valves.json`)**:
     - OpenWebUI Valves previously duplicated over 20 parameters and cached outdated values in `valves.json`, overriding `pipeline_config.yaml`.
     - Replaced the verbose `Valves` model with an empty `class Valves(BaseModel): pass` and reset `valves.json` to `{}`.
     - All settings (LLM models, API keys, search toggles, domain counts, prompts, scoring formulas) are now loaded dynamically and exclusively from `pipeline_config.yaml`.
  3. **`clear_articles_dir` Parameter Bug Fix (`src/core/pipeline_runner.py`, `pipeline_config.yaml`, `main.py`)**:
     - `execute_t2m_research` previously checked `if getattr(config, "CLEAR_ARTICLES_DIR", False):` instead of using its own argument `clear_articles_dir: bool`.
     - Exposed `clear_articles_dir: false` (with documentation for `true`) under `pdf_ingestion:` in `pipeline_config.yaml`.
     - Fixed `src/core/pipeline_runner.py` to evaluate `if clear_articles_dir:` and enforce `0o777` directory permissions with `dmitryx:dmitryx` host ownership upon directory recreation.
     - Updated `main.py` CLI runner to explicitly pass `clear_articles_dir=config.CLEAR_ARTICLES_DIR`.
  4. **Orphaned Articles Pruning (`articles/`)**:
     - Removed 11 extraneous PDF files deposited by the concurrent title-generation run, restoring the directory count to exactly 61 verified files matching `LITERATURE_REVIEW.md`.
  5. **Host File Permissions & Ownership**:
     - Applied `0o666` permissions and `dmitryx:dmitryx` ownership across all modified files.

### 2026-09-11: Dynamic YAML-Driven Sub-Agents ($1 \dots N$) & Strict Schema Validation
- **Goal**: Transition from fixed hardcoded 4-subagent architecture to a fully dynamic data-driven framework where domain agents are defined entirely within `pipeline_config.yaml`, and enforce strict fail-fast configuration validation on startup to prevent running with missing prompts, empty search queries, or invalid parameters.
- **Root Causes & Key Changes**:
  1. **Strict Configuration Validator (`src/core/config_validator.py`)**:
     - Implemented `validate_pipeline_config()` and `enforce_valid_config()`.
     - Validates presence, non-emptiness, and unique IDs for all sub-agents.
     - Enforces that every sub-agent has a non-empty `system_prompt`, `name`, and `search_queries` list.
     - Validates `orchestrator.system_prompt`, `llm` settings, bucket ratios ($0.95 \le \text{sum} \le 1.05$), and `pdf_ingestion` parameters.
     - Raises custom `ConfigValidationError` with detailed bulleted error diagnostics pinpointing the exact missing parameter and agent ID.
  2. **Config Loader & Manifest Evolution (`src/core/config_loader.py`, `pipeline_config.yaml`)**:
     - Converted Layer 6 in `pipeline_config.yaml` to a clean `sub_agents:` list and `orchestrator:` section.
     - Integrated validation directly into `cfg.reload()` and `cfg.set_profile()`.
     - Added `cfg.get_sub_agents() -> List[Dict[str, Any]]`.
     - Added transparent backward-compatible resolution in `cfg.get("prompts.<id>")` pointing to `sub_agents[id].system_prompt`.
  3. **Dynamic Derivation (`agent_config.py`)**:
     - Derived `NUM_DOMAINS = len(SUB_AGENTS) if SUB_AGENTS else 4`.
     - Dynamically scaled `TARGET_PDF_COUNT = NUM_DOMAINS * MAX_RESULTS_PER_DOMAIN`.
  4. **Dynamic Execution Loop (`src/core/pipeline_runner.py`)**:
     - Refactored candidate retrieval, PDF acquisition, sub-agent execution, and intermediate markdown generation to iterate dynamically over `configured_sub_agents`.
     - Accepted optional `custom_prompts: Dict[str, str]` while preserving backward-compatible named prompt parameters (`kinematic_prompt`, etc.).
  5. **Generic Domain Agent & Dynamic Orchestration (`sub_agents.py`, `orchestrator.py`)**:
     - Implemented `analyze_domain()` as the universal LLM runner for any domain agent.
     - Upgraded `synthesize_literature_review()` to accept dynamic dictionary `sub_agent_results` while maintaining `*args` support for legacy callers.
  6. **OpenWebUI & CLI Diagnostics (`openwebui/t2m_pipeline.py`, `main.py`)**:
     - Added `ConfigValidationError` handling to both CLI and OpenWebUI runner worker to present human-readable configuration diagnostics without crashing.
     - Registered `config_validator` in dynamic hot-reload block.
  7. **Host Permissions & Ownership**:
     - Applied `0o666` permissions and `dmitryx:dmitryx` ownership across all created and modified files.

### 2026-09-11: Elimination of Redundant `target_pdf_count` & Dynamic Derivation from Domain Count
- **Goal**: Eliminate the redundant `target_pdf_count` parameter from `pipeline_config.yaml`, prevent dual source-of-truth discrepancies, dynamically derive total target verified PDFs as `NUM_DOMAINS * MAX_RESULTS_PER_DOMAIN`, and wire `CANDIDATE_POOL_MULTIPLIER` directly into candidate pool allocation.
- **Root Causes & Key Changes**:
  1. **Dead & Redundant Parameter Removal (`pipeline_config.yaml`)**:
     - `target_pdf_count` was exposed under `pdf_ingestion`, but `pipeline_runner.py` drives PDF downloads strictly per-domain using `max_results_per_domain` across 4 sub-agent domains (`kinematic`, `physics`, `rl`, `pose`).
     - `target_pdf_count` was never read by `pipeline_runner.py`, leading to confusion and out-of-sync configurations.
     - Removed `target_pdf_count` from `pipeline_config.yaml` and documented automatic derivation ($4 \times \text{max\_results\_per\_domain}$).
     - Added environment variable interpolation `${MAX_RESULTS_PER_DOMAIN:-10}` to `search_discovery.max_results_per_domain`.
  2. **Backward-Compatible Dynamic Calculation (`agent_config.py`)**:
     - Defined `NUM_DOMAINS = 4`.
     - Calculated `TARGET_PDF_COUNT = int(cfg.get("pdf_ingestion.target_pdf_count", NUM_DOMAINS * MAX_RESULTS_PER_DOMAIN))`.
     - Automatically adapts when operational profiles (e.g. `thesis_master` with `max_results_per_domain: 15` $\rightarrow$ 60 PDFs) or environment variables override `MAX_RESULTS_PER_DOMAIN`.
  3. **Candidate Pool Multiplier Connection (`src/core/pipeline_runner.py`)**:
     - Replaced hardcoded `1.5` multiplier with `getattr(config, "CANDIDATE_POOL_MULTIPLIER", 1.5)` in `fetch_candidates_for_domain`.
  4. **Documentation Synchronization**:
     - Updated `PIPELINE_PARAMETERS.md` and `README.md` to reflect derived target PDF counts.
     - Maintained permissions `0o666` and ownership `dmitryx:dmitryx`.

### 2026-09-09: Unified Peer-Review Status in `citation_enricher.py`
- **Goal**: Eliminate inconsistent `Peer-Review Status` column values in the generated ACADEMIC CREDIBILITY table — specifically, CORE rank strings (`"CORE A* (Tier 1, H5: 285)"`, `"Top Robotics (Tier 1, H5: 65)"`) appearing in the Status column instead of uniform peer-review labels.
- **Root Causes & Key Changes**:
  1. **BUG: Fallback branch used `v_eval["impact_factor"]` as status** (`citation_enricher.py` line 129):
     - `evaluate_venue()` returns `impact_factor` = CORE/JCR rank string (e.g. `"CORE A* (Tier 1, H5: 285)"`).
     - This was directly placed in the `status` field, polluting the Peer-Review Status column with ranking metadata.
     - **Fix**: Derive status from `v_eval["is_peer_reviewed"]` boolean → `"Peer-Reviewed"` or `"Preprint (arXiv)"`.
  2. **BUG: Non-canonical status strings in multiple branches**:
     - Lines 82, 122: `"ArXiv Preprint"` / `"Peer-Reviewed Journal/Conf"` → normalized to `"Preprint (arXiv)"` / `"Peer-Reviewed"`.
     - Line 104: `"Peer-Reviewed (Journal Ref)"` → normalized to `"Peer-Reviewed"`.
  3. **BUG: Counter predicate mismatch** (line 155):
     - `"Preprint" in meta["status"]` matched interior substrings, not a prefix check.
     - **Fix**: `meta["status"].startswith("Preprint")` — canonical, future-proof.
  4. **Canonical Status Vocabulary** (two values only):
     - `"Peer-Reviewed"` — CrossRef DOI / CrossRef search / ArXiv journal_ref / venue_ranker peer-reviewed venues.
     - `"Preprint (arXiv)"` — ArXiv URL path, `is_peer_reviewed=False` from venue_ranker.

### 2026-09-09: Langfuse SDK v4 Compatibility Fix & Telemetry Activation (`langfuse_sink.py`, `pipeline_config.yaml`)

- **Goal**: Fix silent telemetry failure — traces not reaching Langfuse despite correct credentials and reachable server.
- **Root Causes & Key Changes**:
  1. **BUG #1 — YAML Key Path Mismatch (`pipeline_config.yaml`)**:
     - `telemetry_output` section stored Langfuse credentials under nested dict `langfuse.host / .public_key / .secret_key`.
     - `agent_config.py` reads via flat dot-paths `cfg.get("telemetry_output.langfuse_host")`, which returned `""`.
     - `TelemetryManager.get_telemetry()` checks `if getattr(config, "LANGFUSE_PUBLIC_KEY", "")` → was `""` → `LangfuseHandler` **never registered**.
     - **Fix**: Flattened YAML keys to `langfuse_host`, `langfuse_public_key`, `langfuse_secret_key` matching `agent_config.py` paths.
     - Also fixed `default_output_report` → `default_output_file` to match `agent_config.py` read path.
  2. **BUG #2 — Langfuse SDK v4 requires `@observe()` context (`langfuse_sink.py`)**:
     - `create_event()` and `start_observation()` exist in SDK v4.x but require an active OTEL trace context to attach child spans.
     - Without `@observe()` wrapping, all child observations had no parent trace → silently dropped.
     - **Fix**: Wrapped `_dispatch_event()` call inside `@observe(name=...)` in `handle()`. All events now arrive in Langfuse as properly nested traces.
     - Note: Raw OTEL spans from a custom `tracer.start_as_current_span()` are filtered by Langfuse's `should_export_span` filter unless created via `langfuse-sdk` instrumentation scope.
  3. **Diagnostics Tooling**:
     - Added `test_langfuse_diag.py` — standalone script with `auth_check()`, `@observe()` trace + child spans, and explicit `flush()`.
     - Confirmed HTTP 200 on `POST /api/public/otel/v1/traces` — telemetry now flows end-to-end.
  4. **File Permissions**: `0o666` + `dmitryx:dmitryx` on all modified files.

### 2026-09-09: Master YAML Configuration Manifest (`pipeline_config.yaml`) & Singleton Config Loader (`src/core/config_loader.py`)
- **Goal**: Centralize fragmented system parameters, prompt templates, and scoring weights into a declarative Master YAML manifest (`pipeline_config.yaml`), provide recursive environment variable interpolation (`${VAR_NAME}` / `${VAR_NAME:-default}`), support 1-key behavioral preset switching (`thesis_master`, `frontier_sota`, `code_first`), and maintain 100% backward compatibility via `agent_config.py`.
- **Architectural Components & Key Changes**:
  1. **Master Manifest (`pipeline_config.yaml`)**:
     - Partitioned configuration across 7 distinct layers: `llm`, `search_discovery`, `scoring_ranking`, `code_artifacts`, `pdf_ingestion`, `prompts`, and `telemetry_output`.
     - Secured sensitive API credentials (`OPENROUTER_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `LANGFUSE_SECRET_KEY`) using runtime environment variable interpolation syntax.
     - Embedded clean multi-line Markdown prompt templates for all 4 domain sub-agents and the Master Orchestrator directly into the YAML manifest.
  2. **Singleton Configuration Provider (`src/core/config_loader.py`)**:
     - Implemented `PipelineConfig` singleton with automatic `.env` pre-loading via `python-dotenv`.
     - Implemented recursive regex-based string expansion for `${VAR}` and `${VAR:-default}`.
     - Implemented recursive dictionary deep-merge (`_deep_merge`) supporting both nested dictionaries and dot-notated profile overrides.
     - Added `get(path, default)`, `set_profile(name)`, `get_profile()`, `list_profiles()`, and `to_dict()` methods.
     - Added `cfg.reload()` to guarantee hot-reload on dynamic module reload.
  3. **Backward-Compatible Bridge (`agent_config.py`)**:
     - Refactored all constants (`API_KEY`, `MODEL_NAME`, `MAX_RESULTS_PER_DOMAIN`, etc.) to draw defaults from `cfg.get(...)` while allowing direct environment overrides.
     - Preserved all exports and types, keeping file length at 93 lines (< 150 lines SRP limit).
  4. **Dynamic Hot-Reloading (`openwebui/t2m_pipeline.py`)**:
     - Registered `src.core.config_loader` in the dynamic hot-reload block so YAML configuration edits apply immediately without Docker container restart.
  5. **Agent & Orchestrator Integration (`sub_agents.py`, `orchestrator.py`)**:
     - Default system prompts now bind to `cfg.get("prompts.kinematic")` etc., with inlined fallbacks.
  6. **Host Ownership & Standalone Testability**:
     - Maintained host permissions `0o666` and `dmitryx:dmitryx` ownership across all created/modified files.
     - Included standalone `if __name__ == '__main__':` test blocks in `config_loader.py` and `agent_config.py`.

### 2026-09-08: Concrete Schema Typing in Pipeline.Valves for Multi-Line Textarea Rendering
- **Goal**: Resolve OpenWebUI rendering prompt valves as single-line `<input type="text">` instead of multi-line expandable `<textarea>` elements.
- **Root Causes & Key Changes**:
  1. **Pydantic OpenAPI Schema `anyOf` Elimination (`openwebui/t2m_pipeline.py`)**:
     - `Optional[str]` emits `{"anyOf": [{"type": "string"}, {"type": "null"}]}` instead of top-level `{"type": "string"}`.
     - OpenWebUI's `Valves.svelte` checks `propertySpec.type !== 'string'`, treating `anyOf` schemas as generic inputs and rendering single-line text inputs.
     - Replaced all `Optional[...]` types in `Pipeline.Valves` with concrete types (`str`, `bool`, `int`) and explicit default values.
     - Verified `/t2m_pipeline/valves/spec` emits top-level `{"type": "string"}` for all prompt fields, enabling native multi-line `<textarea>` rendering with resize handles.
  2. **Null Value Sanitization (`openwebui/t2m_pipeline/valves.json`)**:
     - Sanitized `EZPROXY_COOKIE: null` to `""` in stored `valves.json` to prevent Pydantic string validation errors during container startup.
  3. **Container Cycle & Cache Refresh**:
     - Restarted `open-webui-pipelines` and refreshed OpenWebUI in-memory models cache via `/api/models?refresh=true`.
     - Preserved host file ownership `dmitryx:dmitryx` and `0o666` permissions.

### 2026-09-08: Clean Multi-Line Formatting for Sub-Agent System Prompts & OpenWebUI Valves
- **Goal**: Refactor sub-agent and orchestrator system prompt constants into clean, structured multi-line Markdown with explicit section breaks (`### OBJECTIVE:`, `### FORMATTING RULES:`, `### TABLE COLUMNS:`), ensuring OpenWebUI Valves textareas render legible, beautifully spaced prompts instead of compressed single-line strings.
- **Root Causes & Key Changes**:
  1. **Structured Multi-Line Markdown Templates (`src/agents/sub_agents.py` & `src/agents/orchestrator.py`)**:
     - Converted `KINEMATIC_SYSTEM_PROMPT`, `PHYSICS_DIFFUSION_SYSTEM_PROMPT`, `RL_CONTROL_SYSTEM_PROMPT`, and `MEDIAPIPE_POSE_SYSTEM_PROMPT` into clean, human-readable multi-line Markdown templates.
     - Embedded anti-laziness ("Every paper in the prompt must be represented as a row in the table") and GitHub link rules (`[owner/repo](https://github.com/owner/repo)` or `N/A`) directly into the `### FORMATTING RULES:` section, eliminating concatenated strings.
     - Refactored `ORCHESTRATOR_SYSTEM_PROMPT` to feature clean sections (`### OBJECTIVE:`, `### REQUIRED SECTIONS:`, `### STYLE GUIDELINES:`).
  2. **Valve Default Synchronization (`openwebui/t2m_pipeline.py`)**:
     - Verified `Pipeline.Valves` cleanly binds these updated multi-line templates as default values for `KINEMATIC_PROMPT`, `PHYSICS_PROMPT`, `RL_PROMPT`, `POSE_PROMPT`, and `ORCHESTRATOR_PROMPT`.
  3. **Stored Valve JSON Synchronization (`openwebui/t2m_pipeline/valves.json`)**:
     - Synchronized `openwebui/t2m_pipeline/valves.json` to store the new clean multi-line formatting so existing sessions immediately display the beautifully formatted prompts in the OpenWebUI settings panel.
  4. **Standalone Testability & File Length**:
     - Added runnable `if __name__ == '__main__':` test block to `src/agents/orchestrator.py` (54 lines) and validated `src/agents/sub_agents.py` (164 lines), keeping both strictly under 200 lines with `0o666` host permissions (`dmitryx:dmitryx`).

### 2026-09-08: OpenWebUI Model Discovery, Container IP Bridge Cache & LLM Valve Synchronization
- **Goal**: Resolve `Model not found` in OpenWebUI chat, diagnose container bridge IP caching following pipeline container restarts, expose configurable backend LLM settings (`MODEL_NAME`, `API_BASE_URL`, `OPENROUTER_API_KEY`) in OpenWebUI Valves, and fix pipeline registration in the OpenWebUI Pipelines framework.
- **Root Causes & Key Changes**:
  1. **Container Bridge IP & In-Memory Models Cache**: When `open-webui-pipelines` was restarted, its container IP changed (`172.18.0.34` -> `172.18.0.1`), causing `open-webui` to log `Connect call failed ('172.18.0.34', 9099)`. Because `open-webui` caches discovered models in memory (`request.app.state.MODELS`), the failure dropped `t2m_pipeline` from the active model registry. When users chatted with custom model `tex-to-motion` (`base_model_id: t2m_pipeline`), `open-webui` threw `HTTP 400: Error processing chat metadata: Model not found`.
  2. **Model Registry Refresh Trigger**: Discovered that calling `GET /api/models?refresh=true` clears `get_all_models.cache` and repopulates `request.app.state.MODELS` with all 500+ models, restoring `t2m_pipeline` and `tex-to-motion`.
  3. **Pipelines Discovery Framework Bug (`self.type = "pipe"`)**: In `open-webui/pipelines/main.py`, `get_all_pipelines()` inspects `if hasattr(pipeline, "type"):`. If set to `"manifold"` or `"filter"`, it handles them; but if set to `"pipe"`, it had no branch and skipped registration entirely, falling into `else:` only when `self.type` was absent. Kept initialization clean with `self.id = "t2m_pipeline"` and no `self.type`.
  4. **Configurable LLM Valves in OpenWebUI (`openwebui/t2m_pipeline.py`)**: Added `MODEL_NAME`, `API_BASE_URL`, and `OPENROUTER_API_KEY` to `Pipeline.Valves` with default fallbacks to `agent_config.py`. In `pipe()`, synchronized these valve parameters to runtime client bindings in `src.agents.sub_agents.client`, allowing users to inspect and switch models directly from OpenWebUI.
  5. **Permissions**: Ensured `0o666` and host user ownership `dmitryx:dmitryx` on `openwebui/t2m_pipeline.py` and `valves.json`.

### 2026-09-08: Cascading PDF Resolver Re-Ordering, Candidate Replenishment & Full-Text Ingestion Integrity
- **Goal**: Guarantee academic integrity and anti-hallucination by ensuring sub-agents analyze ONLY papers with secured full-text PDFs, prioritize Afeka SSO institutional access on IEEE Xplore via EZProxy session stamping, dynamically replenish candidates from an extended pool ($N \times 1.5$) so target counts (20 papers) are fulfilled, and partition un-ingested candidates into an Appendix.
- **Root Causes & Key Changes**:
  1. **Re-ordered PDF Download Cascade (`src/utils/pdf_downloader.py`)**:
     - Tier 1: Direct OpenAccess PDF (ends with `.pdf`).
     - Tier 2: IEEE EZProxy Stamp (Afeka SSO authenticated session for `10.1109` DOIs, `document/{arnum}`, `arnumber={arnum}`, or `ieee.org` URLs $\rightarrow$ `https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}`). Promoted above ArXiv and Unpaywall to ensure institutional IEEE peer-reviewed versions are acquired first.
     - Tier 3: Unpaywall API via DOI (`email=academic_bot@afeka.ac.il`, 4s timeout).
     - Tier 4: ArXiv direct endpoint (`https://arxiv.org/pdf/{arxiv_id}.pdf`).
     - Added `fulltext_secured: bool` flag to candidate records.
  2. **Candidate Pool Replenishment Loop (`src/core/pipeline_runner.py`)**:
     - Extended candidate retrieval to `candidate_pool_size = max(int(max_results_per_domain * 1.5), 8)`.
     - Ranked candidates via Code-First scoring without truncating early.
     - Implemented candidate replenishment loop: iterates through ranked candidates, attempting PDF acquisition until exactly `max_results_per_domain` full-text verified papers are secured for each domain.
     - If a candidate download fails, the pipeline immediately draws the next ranked candidate from the pool.
  3. **Strict Sub-Agent Ingestion Partitioning (`src/core/pipeline_runner.py`)**:
     - Exclusively passed `secured_by_domain` to sub-agents 1–4 (`kinematic`, `physics`, `rl`, `pose`), completely preventing LLM hallucination on abstracts.
  4. **Un-ingested Candidate Appendix (`src/core/pipeline_runner.py`)**:
     - Created `build_unsecured_appendix()`, formatting uningested candidate papers into a clean Markdown table (`Title (Year)`, `Venue`, `Citations`, `Code Repository`, `Ingestion Status: Paywalled / Unavailable`).
  5. **Summary Header Metrics**:
     - Updated header: `**Unique Papers Processed:** {total_candidates} | **Full-Text RAG Verified:** {secured_count} | **Paywalled/Skipped:** {skipped_count}`.
  6. **OpenWebUI Pipeline Dynamic Reload (`openwebui/t2m_pipeline.py`)**:
     - Registered `src.utils.pdf_downloader` in dynamic hot-reload sequence.
  7. **SRP & File Length Limits**:
     - Maintained `pdf_downloader.py` (195 lines) strictly under 200 lines, with host permissions `0o666` and `dmitryx:dmitryx`.

### 2026-09-08: Standardized Markdown Links, Parallelized Discovery & Cascading PDF Ingestion
- **Goal**: Standardize all GitHub links in sub-agent tables, narrative text, and verification summaries to clean `[owner/repo](https://github.com/owner/repo)` format, resolve the 12/20 PDF download drop-off via multi-tier fallback (Direct OA -> ArXiv -> Unpaywall -> IEEE EZproxy stamp), and parallelize repository discovery via `ThreadPoolExecutor(max_workers=8)` to eliminate sequential network latency.
- **Root Causes & Key Changes**:
  1. **Uniform Markdown Link Formatter (`src/utils/text_formatters.py`)**: Implemented `clean_github_markdown_link()` converting raw GitHub URLs and full-URL anchors into clean `[owner/repo](https://github.com/owner/repo)`.
  2. **Sub-Agent & Orchestrator Prompts (`sub_agents.py`, `orchestrator.py`)**: Standardized system prompts across all 4 sub-agents and orchestrator to mandate `[Title (Year)](URL)` in the first column and `[owner/repo](https://github.com/owner/repo)` or `N/A` in the code column. Updated `ANTI_LAZY_RULE`.
  3. **Table Sanitizer Pipeline Integration (`pipeline_runner.py`)**: Updated `sanitize_markdown_table_github_urls()` to pipe through `clean_github_markdown_link()`, guaranteeing all table links conform to the standard.
  4. **Multi-Tier Cascading PDF Downloader (`src/utils/pdf_downloader.py`)**: Implemented `resolve_fulltext_pdf_url()` and `get_pdf_candidate_urls()` covering Tier 1 (Direct OA), Tier 2 (ArXiv conversion), Tier 3 (Unpaywall via DOI), and Tier 4 (IEEE EZproxy stamp URL). Streamlined to 164 lines.
  5. **Parallel GitHub Resolution (`src/fetchers/github_finder.py`)**: Refactored `enrich_papers_with_github()` to use `ThreadPoolExecutor(max_workers=8)` with thread-safe telemetry and status dispatching via `threading.Lock()`. Reduced network candidate timeouts to `(2.0, 3.0)` seconds, reducing scan time from >10s to <1.5s.
  6. **Candidate Pool Integration (`pipeline_runner.py`)**: Updated `rank_and_filter_candidates()` to leverage concurrent `enrich_papers_with_github()` across the entire candidate pool.
  7. **SRP & File Length Limits**: Maintained `text_formatters.py` (70 lines), `pdf_downloader.py` (164 lines), `github_finder.py` (189 lines), `github_verifier.py` (100 lines), and `sub_agents.py` (143 lines) strictly under 200 lines with `0o666` permissions.

### 2026-09-08: Semantic Scholar Domain Filtering & Code-First Candidate Selection
- **Goal**: Eliminate domain bleeding in academic search (e.g. non-CS disciplines such as sports medicine, cellular biology, and thermodynamics), prevent unranked 1970s database records from unauthenticated Bulk Search, and enforce "Code-First" candidate selection so papers with verified GitHub repositories are prioritized and placed into the top positions.
- **Root Causes & Key Changes**:
  1. **Domain Enforcement (`semantic_scholar_fetcher.py`)**: Explicitly passed `fieldsOfStudy="Computer Science,Engineering"` to all Semantic Scholar queries.
  2. **Standard Search Authority & Adaptive Fallback**: Maintained `/graph/v1/paper/search` as the authoritative primary search endpoint with exponential backoff on 429. Demoted unranked Bulk Search to an emergency fallback and added post-sorting by `(year >= 2019, citations)` descending, guaranteeing high-impact CS papers are returned.
  3. **Metadata Enrichment**: Added `influentialCitationCount` and `publicationVenue` to `S2_FIELDS`, mapping direct citation metrics and venue names into paper records.
  4. **Code-First Candidate Pool Expansion (`pipeline_runner.py`)**: Expanded candidate retrieval per domain to `candidate_pool_size = max(max_results_per_domain * 2, 8)` across all enabled sources before truncation.
  5. **Early Code Discovery & Candidate Scoring**: Resolved GitHub repositories for candidates early and scored candidates via `score = (CODE_ARTIFACT_SCORE_BOOST if has_code else 0.0) + citations + influential_citations * 2.0`. Enforced `prefer_code` (papers with code ranked first) and `require_code` (strictly code-bearing papers).
  6. **Configuration & OpenWebUI Valves**: Added `REQUIRE_CODE`, `PREFER_CODE`, `CODE_SCORE_BOOST`, and `SEMANTIC_SCHOLAR_FIELDS_OF_STUDY` to `agent_config.py`, `.env`, `.env.example`, and exposed `REQUIRE_CODE` and `PREFER_CODE` in `openwebui/t2m_pipeline.py` Valves.
  7. **File Length & Testability**: Kept `semantic_scholar_fetcher.py` at 159 lines, `pipeline_runner.py` modular, and validated all components with standalone test suites.

### 2026-09-08: Multi-Tier GitHub Discovery, Pre-Print Resolution & Dead-Link Elimination
- **Goal**: Eliminate false 404 links (like unreleased preprints) from literature reviews, resolve missing repositories across Semantic Scholar papers, modularize URL verification under 200-line SRP limits, and enforce post-processing table sanitization.
- **Root Causes & Key Changes**:
  1. **Split Verification & Discovery (`github_verifier.py` & `github_finder.py`)**: Extracted URL cleaning, streaming HTTP liveness verification, candidate regex matching, and blacklist definitions into dedicated `src/fetchers/github_verifier.py` (~95 lines). Kept `github_finder.py` focused exclusively on multi-tier resolution (< 196 lines).
  2. **External Identifiers & ArXiv Preprints (`semantic_scholar_fetcher.py`)**: Added `externalIds` to `S2_FIELDS`. Parsed `arxiv_id`, `arxiv_url`, and `doi` into paper dictionaries, allowing papers retrieved from Semantic Scholar to be resolved against their ArXiv preprint pages and author project pages.
  3. **Multi-Tier Resolution (`github_finder.py`)**:
     - Tier 1: Abstract and comment text regex.
     - Tier 2: Author project pages (`*.github.io`) found in metadata.
     - Tier 3: ArXiv landing page and project link discovery via `arxiv_id` or fast title lookup on ArXiv API (`ti:"..."`).
     - Tier 4: Targeted GitHub Search API fallback verifying candidate repo descriptions against paper title keywords with >= 3 word overlap and 200 OK liveness checks (successfully discovers repositories like `STRAPS-3DHumanShapePose` for BMVC 2020).
  4. **Sub-Agent Abstract URL Redaction (`sub_agents.py`)**: Redacted unverified/dead repository links from abstracts before feeding text to the LLM, and updated sub-agent system prompts to strictly require that table cells match `GitHub Code Repo:`.
  5. **Post-Processing Markdown Table Sanitization (`pipeline_runner.py`)**: Added `sanitize_markdown_table_github_urls()` to scan generated sub-agent tables and orchestrator syntheses, replacing any unverified or dead repository links with `N/A`.
  6. **Keyword Extraction Safeguard (`pipeline_runner.py`)**: Added filtering of meta-prompt words (`perform`, `write`, `review`, etc.) in `extract_core_keywords()`, preventing search degradation when user requests vary slightly from canned templates.
  7. **OpenWebUI Pipeline Dynamic Reload**: Registered `github_verifier` in `openwebui/t2m_pipeline.py`'s dynamic hot-reload sequence.
  8. **Host File Permissions & SRP**: All modified files kept strictly under 200 lines with `0o666` permissions and `dmitryx:dmitryx` host ownership.

### 2026-09-08: Core GitHub Extraction & Liveness Verification Refactor (`github_finder.py`)
- **Goal**: Fix core extraction and verification pipeline directly at source without third-party fallback APIs, eliminate false negatives caused by naive `HEAD` requests or CloudFront 403/429 blocking, and handle author project pages (`*.github.io`).
- **Root Causes & Key Changes**:
  1. **Liveness Verification (`is_github_repo_live`)**: Replaced `requests.head()` with streaming `requests.get(..., stream=True)` with browser `User-Agent`. Explicitly distinguishes between `200 OK` (`VERIFIED`), `404 Not Found` (`NOT_FOUND`), and `403/429` (`RATE_LIMITED` - preserved as valid candidate rather than dropped).
  2. **Direct Primary Sources Only (`resolve_paper_github`)**: Resolves directly against:
     - Paper abstract text and ArXiv comment field.
     - Author project pages (`*.github.io`) linked from abstract/comments.
     - ArXiv landing page HTML (`https://arxiv.org/abs/...`).
     - Zero external aggregator API dependencies (e.g. no Papers with Code, no unconstrained Google searches).
  3. **Robust URL Canonicalization (`clean_github_url`)**: Strips enclosing brackets, quotes, trailing punctuation, query parameters, anchors, `.git` extensions, and branch subpaths (`/tree/main`, `/blob/...`).
  4. **Diagnostic Test Suite**: Added standalone diagnostic test covering real-world papers (MDM, MotionDiffuse, EMDM), non-existent 404 repositories, and project page resolution.
  5. **Modular Architecture**: Maintained file length at 193 lines (< 200 lines limit) with `0o666` permissions and `dmitryx:dmitryx` ownership.

### 2026-09-08: Academic Paper Discovery & Hybrid Ranking Engine (`academic_ranking_engine`)
- **Goal**: Implement a production-grade Python package (`academic_ranking_engine`) designed to fetch, filter, rank, and balance academic papers from scholarly APIs (Semantic Scholar Graph API with ArXiv fallback), solving citation-lag bias and cross-domain pollution.
- **Architectural Components & Implementation**:
  1. **Data Models (`models.py`)**: Pydantic v2 `Author` and `PaperMetadata` schemas with calculated properties for publication age ($\Delta t$), citation velocity ($V_{cit}$), and open-source availability (`has_code`).
  2. **Venue Tier Classifier (`venue_classifier.py`)**: Rule-based regex and normalized string matcher assigning venue tiers: Tier 1 ($W_{venue} = 2.0\times$), Tier 2 ($1.35\times$), Tier 3 ($1.0\times$), and Preprints ($0.85\times$).
  3. **Scoring Engine (`scorer.py`)**: Mathematically rigorous non-linear scoring applying $S_{SOTA} = W_{venue} \cdot (1.2 \cdot V_{cit} + 0.5 \cdot \text{InflCit}) + B_{code} + B_{oa} + B_{author}$ for recent works ($\Delta t \le 2.0$) and $S_{Found} = W_{venue} \cdot [0.8 \cdot \ln(1 + C_{cit}) + 0.4 \cdot \text{InflCit}] + \dots$ for historical baselines ($\Delta t > 2.0$).
  4. **Async Scholar Client (`client.py`)**: Asynchronous `httpx` client with domain locking (`Computer Science, Engineering`), unauthenticated bulk search optimization, and automated ArXiv fallback.
  5. **Dual-Bucket Discovery Engine (`discovery_engine.py`)**: Orchestrates 35% Foundational / 65% SOTA ratio blending, cross-stream deduplication via normalized titles, sub-query decomposition for multi-faceted keyword queries, and zero-citation preprint rescue.
  6. **Interactive CLI Demo (`demo.py`)**: Rich color-coded terminal dashboard displaying ranked publications, venue tiers, citation velocities, and score breakdowns.
  7. **Modular Constraints**: All module files maintained under 200 lines with standalone `if __name__ == '__main__':` test runners and `dmitryx:dmitryx` host ownership.

### 2026-09-08: Semantic Scholar Resilience, 429 Rate-Limit Mitigation & Bulk Search Fallback
- **Goal**: Resolve HTTP 429 throttling on Semantic Scholar API that caused Kinematic and Pose/Vision sub-agents to retrieve 0 papers in unauthenticated mode, add official API key authentication, implement adaptive exponential backoff with `Retry-After` header parsing, and add seamless bulk search fallback.
- **Root Causes & Key Changes**:
  1. **HTTP 429 Rate Limiting & Retry Cool-Down**: Fixed flat 5s sleep in `semantic_scholar_fetcher.py`. Introduced adaptive backoff (`[4s, 8s, 14s]`) and dynamic parsing of the `Retry-After` header returned by CloudFront/API Gateway.
  2. **Unauthenticated Strategy — Direct Bulk Search**: CloudFront aggressively throttles `/graph/v1/paper/search` for unauthenticated IPs with HTTP 429, but `/graph/v1/paper/search/bulk` offers high throughput without aggressive throttling. In unauthenticated mode, the fetcher queries Bulk Search directly, completely circumventing 429 errors.
  3. **Bulk Search `tldr` Incompatibility Fix**: Removed `tldr` from `S2_FIELDS`. Semantic Scholar's `/paper/search/bulk` endpoint strictly rejects `tldr` with `HTTP 400: {"error":"Unrecognized or unsupported fields: [tldr]"}`, which previously caused the fallback to fail silently.
  4. **OpenWebUI Pipeline Dynamic Reloading**: Added `src.fetchers.semantic_scholar_fetcher`, `scholar_fetcher`, `ieee_fetcher`, and `arxiv_fetcher` to the `importlib.reload(...)` block in `openwebui/t2m_pipeline.py`, ensuring containerized OpenWebUI instances immediately execute refreshed code without container restarts.
  5. **Official API Key Authentication (`SEMANTIC_SCHOLAR_API_KEY`)**: Centralized API key configuration in `agent_config.py`, `.env`, `.env.example`, and OpenWebUI Valves, transmitting `x-api-key` headers to grant high-throughput access.
  6. **Relaxed Citation Filtering**: Changed default `min_citations` from `2` to `0` (configurable via `SEMANTIC_SCHOLAR_MIN_CITATIONS`), preventing recent (2023–2026) high-value publications from being dropped.
  7. **Pipeline Runner Scholar Integration**: Fixed missing `enable_scholar` branch in `src/core/pipeline_runner.py`'s `fetch_papers_for_domain` loop, ensuring Google Scholar (OpenAlex/Crossref) executes when enabled.

### 2026-09-07: Resilient Institutional Authentication, Session Persistence & 2FA Elimination
- **Goal**: Eliminate repeated 2FA (mobile fingerprint/push approval) prompts on every pipeline run, prevent stale cookie shadowing, auto-synchronize live session tokens back to disk, and sanitize tracking/ephemeral tokens.
- **Root Causes & Key Changes**:
  1. **Session Cookie Re-Use & Early Active Detection (`sso_login.py`):** Pre-populated Playwright browser contexts with existing institutional cookies (`context.add_cookies()`) and added early detection for active Afeka College sessions on IEEE Xplore. If institutional access is already granted, it extracts updated cookies and exits immediately without prompting 2FA or retyping credentials.
  2. **Automated Live Cookie Sync to Disk (`ezproxy_session.py` & `pipeline_runner.py`):** Added `sync_session_cookies_to_disk()` to `EZProxyManager`. Invoked automatically during live health checks and immediately after PDF downloads in `pipeline_runner.py` to persist refreshed tokens (`WLSESSION`, `seqId`, `xpluserinfo`) back to `ezproxy_cookies.json`, preventing session expiration while idle.
  3. **Strict Cookie Sanitization (`ezproxy_auth.py`):** Filtered out ephemeral F5 ASM tokens (`TSaf*` with 30s TTL), AWS removal markers (`AWSALBAPP*=_remove_`), and third-party trackers (`_cl*`, `tt*`, `_ga*`, etc.) on both disk load and disk save.
  4. **Valve Precedence & Process Isolation Fix (`ezproxy_auth.py` & `pipeline_runner.py`):** Guaranteed `ezproxy_cookies.json` is loaded whenever it contains a valid `ERIGHTS` token. Removed global `os.environ["EZPROXY_COOKIE"]` mutation in `pipeline_runner.py` so empty/stale valve inputs no longer poison subsequent runs in the container process.
  5. **Resilient Health Probes (`ezproxy_auth.py`):** Increased live probe timeout from 8s to 15s to eliminate false-positive network timeouts, properly resolved relative redirects via `urljoin`, and merged any refreshed response cookies directly to disk.
  6. **Host File Ownership & Permissions:** Enforced standard host user ownership (`dmitryx:dmitryx`) and proper mode differentiation (`0o777` for directories, `0o666` for files).

### 2026-09-07: Publication Venue Accuracy, DOI Direct Lookup & Verified GitHub Discovery
- **Goal**: Resolve inaccurate venue names (`"Peer-Reviewed Journal"`, false-positive book chapters like `"Human Pose Analysis"`), wrong publication years (2025 instead of 2020), supplementary media artifacts (`.mp4`), and dead/irrelevant GitHub links.
- **Root Causes & Key Changes**:
  1. **Direct DOI CrossRef Lookup (`citation_enricher.py`):** Prioritized direct DOI API queries (`https://api.crossref.org/works/{doi}`) instead of fuzzy title search. Extracted conference names from `container-title`, `event.name` (e.g. CVPR, ICCV, ICRA), `publisher`, and `group-title`. Completely eliminated the hardcoded string `"Peer-Reviewed Journal"`.
  2. **Strict Title Match Safeguard:** Replaced loose 0.4 token threshold with strict `>= 0.75` token overlap and `>= 0.6` character length ratio, preventing short common keywords from matching unrelated book chapters. If CrossRef search lacks high confidence, upstream fetcher metadata is preserved.
  3. **ArXiv & Preprint Categorization:** ArXiv publications without external peer-reviewed DOIs or journal refs are explicitly marked as venue `"arXiv"` and status `"Preprint (arXiv)"`.
  4. **Supplementary Media Filtering:** Filtered non-paper media files (`.mp4`, `.avi`, `.mov`, `.supp`, `.zip`) across `ieee_fetcher.py`, `scholar_fetcher.py`, and `citation_enricher.py`.
  5. **Verified GitHub Liveness & Loose Search Removal (`github_finder.py`):** Removed unconstrained keyword GitHub search API fallback that returned unrelated repos (e.g. market reports). Added `is_github_repo_live` HTTP HEAD verification to ensure candidate repositories exist, are public, and return HTTP 200 before attaching them; otherwise cleanly outputs `N/A`.
  6. **OpenAlex Venue & Citation Enhancement (`scholar_fetcher.py`):** Updated OpenAlex parsing to extract `raw_source_name` and alternate locations when primary `source.display_name` is null, and preserved `cited_by_count`.

### 2026-09-07: Multi-Tier GitHub Code Repository Discovery Engine (`github_finder.py`)
- **Goal**: Automatically discover, extract, and canonicalize GitHub open-source code repositories for academic papers, eliminating universal `N/A` placeholders across Sub-Agent tables and Master Review synthesis.
- **Key Changes**:
  1. **Dedicated Module (`src/fetchers/github_finder.py`):** Implemented multi-tier discovery:
     - **Tier 1 (Instant Abstract/Comment Extraction):** High-precision regex extracts `github.com/{owner}/{repo}` and `{owner}.github.io/{repo}` from abstract and ArXiv `<arxiv:comment>` fields.
     - **Tier 2 (Landing Page HTML Inspection):** Scans download landing pages during PDF acquisition or URL resolution.
     - **Tier 3 (Targeted Search Fallback):** Queries GitHub REST Search API (`in:name,description`) using cleaned title keywords with rate-limit and bot-protection safeguards.
     - **Canonicalization:** Cleans trailing punctuation, strips branch subpaths (`/tree/main`, `/blob/...`, `.git`), and filters out service endpoints (`/topics`, `/features`, `/pricing`).
  2. **Fetchers Integration:** Updated `arxiv_fetcher.py` to parse `<arxiv:comment>`, `ieee_fetcher.py`, `scholar_fetcher.py`, and `semantic_scholar_fetcher.py` to run `extract_github_url` on paper abstracts.
  3. **PDF Downloader Integration (`pdf_downloader.py`):** Scans HTML responses during PDF downloading and attaches discovered repositories to paper dictionaries.
  4. **Pipeline Execution Integration (`pipeline_runner.py`):** Added Step 2.5 (`find_github_repos`) between PDF download and Sub-Agent prompts, dispatching telemetry events to OpenWebUI and Terminal.
  5. **Academic Credibility Table Enrichment (`citation_enricher.py`):** Added `Code Repository` column to the `# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION` table.
  6. **OpenWebUI Pipeline Dynamic Reload:** Added `src.fetchers.github_finder` to hot-reloading list in `openwebui/t2m_pipeline.py`.

### 2026-09-06: Decoupled Telemetry Architecture (Event Dispatcher, Rich Terminal, Langfuse v3, SSE)
- **Goal**: Decouple core agent execution from logging and output handlers following the Event Dispatcher Pattern, eliminate raw JSON terminal clutter, silence background tracing, and provide SSE streaming.
- **Key Changes**:
  1. **Event Dispatcher (`src/telemetry/`):** Created `TelemetryManager` and unified `TelemetryEvent` contract (`THINKING`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`, `RESPONSE`).
  2. **Rich 1-Line Progress Terminal Sink (`TerminalHandler`):** Replaced verbose multi-line stdout dumps with clean, color-coded, 1-line status updates using `rich`. Completely eliminated raw JSON and duplicate line dumps.
  3. **Langfuse v3 SDK Asynchronous Sink (`LangfuseHandler`):** Integrated background event dispatching to self-hosted Langfuse v3 (`http://192.168.68.53:3005`). Silenced `langfuse` logger (`logging.CRITICAL`, non-propagating) to guarantee zero stdout pollution. Handled missing keys and connection timeouts gracefully without blocking the agent.
  4. **Server-Sent Events Sink (`SSEHandler`):** Created thread-safe queue generating compliant SSE streams (`data: {...}\n\n`) ending with `data: [DONE]\n\n` for OpenWebUI and FastAPI integration.
  5. **Core Engine Instrumentation:** Updated `pipeline_runner.py`, `sub_agents.py`, and `orchestrator.py` to emit structured events instead of direct `print` calls.
  6. **Clean Logging:** Configured `logger.py` to write strictly to `research_agent.log`, preventing duplicate trace messages in terminal.
  7. **OpenWebUI Pipeline Integration:** Integrated `OpenWebUIAdapterSink` and `SSEHandler` into `openwebui/t2m_pipeline.py` with dynamic hot-reloading.

### 2026-09-05: IEEE Xplore / Afeka College Institutional SSO Refactor & Cookie Sanitization
- **Goal**: Resolve authentication flow failure, fix Playwright selector deadlock, eliminate synchronous form submit blocking, and prevent HTTP 400 Bad Request caused by cookie bloat.
- **Root Causes & Solutions**:
  1. **Direct WAYF OpenAthens Navigation**: Added direct navigation to `AFEKA_WAYF_URL` (`https://ieeexplore.ieee.org/servlet/wayf.jsp?entityId=https://idp.afeka.ac.il/openathens...`) with resilient fallback to modal typeahead discovery, avoiding brittle Angular UI hierarchies.
  2. **Playwright Form Submission Deadlock**: Replaced blocking `submit.click()` with `no_wait_after=True` and prompt-first notification so the user receives the 2FA push instruction immediately while the browser awaits SAML return (`page.wait_for_url("**/ieeexplore.ieee.org/**")`).
  3. **Cookie Sanitization & CloudFront 400 Fix**: Stripped 3rd-party tracking cookies (Taboola, LinkedIn, TikTok, Adobe, GA) and eliminated duplicate cookie injection on both `.ieee.org` and `ieeexplore.ieee.org`, keeping request headers lean and preventing CloudFront `HTTP 400 Bad Request`.
  4. **Headless Browser Dependencies**: Verified and installed required Linux shared libraries (`libatk-1.0`, `libcups2`, `libgbm1`, etc.) for Playwright Chromium.
  5. **Modular Code Architecture**: Maintained all modules in `src/auth/` under 200 lines with standalone `__main__` diagnostics.

### 2026-09-05: Single Source of Truth (SSOT) Configuration Consolidation
- **Goal**: Eliminate hardcoded fallbacks and duplicate configuration across modules (`main.py`, `openwebui/t2m_pipeline.py`, `src/core/pipeline_runner.py`, `src/fetchers/`), making `config.py` the authoritative Single Source of Truth.
- **Key Changes**:
  1. Centralized all runtime defaults and environment variable overrides in `config.py` (`API_KEY`, `BASE_URL`, `MODEL_NAME`, `MAX_RESULTS_PER_DOMAIN`, `ENABLE_IEEE_DEFAULT`, `ENABLE_SCHOLAR_DEFAULT`, `ENABLE_ARXIV_DEFAULT`, `ENABLE_SEMANTIC_SCHOLAR_DEFAULT`, `DEFAULT_OUTPUT_FILE`, `DEFAULT_SEARCH_QUERY`, `EZPROXY_DOMAIN_DEFAULT`, `AUTO_SSO_LOGIN_DEFAULT`, `IEEE_INSTITUTION_DEFAULT`).
  2. Refactored `openwebui/t2m_pipeline.py` `Valves` schema and fallback resolution to bind strictly to `config.*` constants, and added `config` to dynamic hot-reloading.
  3. Refactored `main.py` and `src/core/pipeline_runner.py` function signatures and caller parameters to use `config.*` defaults.
  4. Updated all fetchers (`src/fetchers/arxiv_fetcher.py`, `ieee_fetcher.py`, `scholar_fetcher.py`, `semantic_scholar_fetcher.py`) to reference unified default query and limit constants.
  5. Updated `.env.example` with full variable definitions and updated `Makefile` `setup` target to safely copy `.env.example` (`cp .env.example .env`).
  6. Added standalone test runner to `config.py` (`python3 config.py`).
  7. Documented `config.py` as the application SSOT in `README.md` and `Gemini.md`.

### 2026-09-05: Configuration Simplification & Import Cleanup
- **Goal**: Eliminate dead-code in `config.py` and replace complex dynamic importlib loading in `src/agents/sub_agents.py` with standard imports.
- **Key Changes**:
  1. Replaced unused `MAX_PAPERS_PER_CATEGORY` with `MAX_RESULTS_PER_DOMAIN = int(os.getenv("MAX_RESULTS_PER_DOMAIN", "5"))` in `config.py`.
  2. Simplified config loading in `src/agents/sub_agents.py` to direct `from config import API_KEY, BASE_URL, MODEL_NAME`.
  3. Cleaned up `main.py` to source `MAX_RESULTS_PER_DOMAIN` from `config`.

### 2026-09-05: Integrated Citation & Peer-Review Enrichment
- **Goal**: Embed academic credibility analysis directly into the pipeline lifecycle and eliminate external root scripts.
- **Key Changes**:
  1. Migrated CrossRef and ArXiv verification logic from `enrich_review.py` into `src/fetchers/citation_enricher.py`.
  2. Integrated `enrich_literature_review()` directly into `src/core/pipeline_runner.py`, enriching the report automatically before saving `LITERATURE_REVIEW.md`.
  3. Removed obsolete root file `enrich_review.py` and updated `main.py` and `Makefile`.
  4. Added standalone module testability to `citation_enricher.py` (`python3 -m src.fetchers.citation_enricher`).

### 2026-09-05: Unified `src/auth/` & Infrastructure Deprecation
- **Goal**: Consolidate scattered authentication logic into a dedicated, modular package following Single Responsibility Principle (SRP) and file length limits (<200 lines).
- **Key Changes**:
  1. Created `src/auth/` package with `EZProxyManager` in `src/auth/ezproxy_session.py` to orchestrate session creation, live health checks, and automated 2FA login.
  2. Migrated browser automation from `infra/auth_service/browser_flow.py` into `src/auth/afeka_sso.py`.
  3. Relocated `ezproxy_auth.py`, `import_cookies.py`, `playwright_login.py`, and `sso_login.py` from `src/utils/` to `src/auth/`.
  4. Fully deprecated and removed `infra/auth_service/` (standalone Flask server on port 8055) in favor of direct in-process execution.
  5. Cleaned up `src/utils/` so only cross-cutting utilities (`logger.py` and `pdf_downloader.py`) remain.
  6. Updated all dependent modules (`src/fetchers/`, `src/core/pipeline_runner.py`, `openwebui/t2m_pipeline.py`).
### 2026-09-05: IEEE PDF Download Engine & Live Auth Verification Fixes
- **Goal**: Resolve silent PDF download failures in OpenWebUI and eliminate false-positive authentication status reports.
- **Root Causes & Solutions**:
  1. **Live Auth False-Positive**: In `src/auth/ezproxy_auth.py`, `verify_live_ieee_access()` evaluated `if "pdf" in loc.lower()` before checking login indicators. When IEEE responded with `302 Found` to `login.jsp?url=%2FstampPDF%2FgetPDF.jsp...&authDecision=-203`, the query string triggered a false-positive pass. Fixed by enabling `allow_redirects=True`, strictly verifying binary `%PDF` streams on 200 responses, and checking for login walls across redirect history.
  2. **OpenAlex `NameError: re`**: Added missing `import re` in `src/fetchers/ieee_fetcher.py`.
  3. **Crossref Malformed Article Numbers**: Replaced broken `.split(".")[0]` logic with regex matching (`r'(\d{6,8})(?:/[^/]+)?$'`) and canonical DOI URL fallback (`https://doi.org/{doi}`).
  4. **PDF Downloader DOI Resolution**: Updated `src/utils/pdf_downloader.py` to follow DOI redirects to `/document/<arnumber>`, resolve to `stampPDF/getPDF.jsp`, strictly enforce binary PDF validation (`is_pdf_bytes`), and accept session / cookie overrides directly from pipeline runner.
  5. **Docker Config Shadowing**: Renamed pipeline reloader to target `agent_config.py` explicitly, avoiding collisions with OpenWebUI's internal `config.py`.

### 2026-09-05: SSO Browser Automation Phantom Status Fix & Multi-Source PDF Downloader
- **Goal**: Eliminate false status callbacks in `afeka_sso.py`, prevent dumping unauthenticated guest cookies into `ezproxy_cookies.json`, fix static header poisoning, and enable direct PDF resolution for ArXiv and open-access publications.
- **Root Causes & Solutions**:
  1. **Phantom 2FA Notification in `afeka_sso.py`**: The status callback reporting mobile push notification was triggered unconditionally even when Angular modal component `<xpl-seamless-access>` was stuck on loading spinner or blocked by third-party storage partitioning. Furthermore, `page.wait_for_url("**/ieeexplore.ieee.org/**")` immediately returned true because the browser was still on IEEE Xplore, dumping unauthenticated guest cookies. Fixed by strictly verifying navigation to `sso.afeka.ac.il`, only sending push notifications when credentials are submitted, and verifying live access with a test session before overwriting `ezproxy_cookies.json`.
  2. **Session Cookie Header Poisoning in `ezproxy_session.py`**: Removed `session.headers["Cookie"] = "; ".join(...)` which sent hardcoded IEEE cookies to foreign domains (ArXiv, CrossRef, DOI resolvers). Restricted cookies to `.ieee.org` in `session.cookies` without duplicate sub-domain binding.
  3. **Multi-Source ArXiv / OpenAccess Resolution in `pdf_downloader.py`**: Added `resolve_direct_pdf_url()` to transform ArXiv abstract URLs (`arxiv.org/abs/...`) to direct binary endpoints (`arxiv.org/pdf/...pdf`), added ArXiv link detection in landing page HTML, added `Referer` headers for IEEE requests, and decoupled requests for non-IEEE sources. Verified direct PDF downloads for ArXiv papers.
  4. **Diagnostic Transparency & Fast Probe Optimization**: In `src/auth/ezproxy_auth.py`, updated `verify_live_ieee_access()` with `allow_redirects=False` for sub-second fail-fast probe checks, and enhanced diagnostic messages to explicitly report when `ezproxy_cookies.json` was parsed successfully but lacks the institutional `ERIGHTS` token.
  5. **IEEE SAML Federated Institutional Authentication Flow (`sso_login.py`)**: Completely refactored the institutional authentication engine in `src/auth/sso_login.py`. Rather than authenticating directly against Afeka (`sso.afeka.ac.il/my.policy`) which only yielded internal IdP cookies (`MRHSession`), the automation begins at `https://ieeexplore.ieee.org`, triggers "Institutional Sign In" -> "Access Through Your Institution", searches for "Afeka College", and redirects into Afeka's SAML IdP with the IEEE authentication request. Once credentials are submitted and the user approves the 2FA push on their mobile phone, the browser completes the SAML callback to IEEE Xplore, acquiring the authentic institutional entitlement token (`ERIGHTS`). All cookies are dumped into `ezproxy_cookies.json`.
  6. **PDF Downloader Session & User-Agent Preservation**: Updated `src/utils/pdf_downloader.py` to route DOI links through `session` so that redirects to `ieeexplore.ieee.org` preserve institutional cookies and browser User-Agent headers, preventing HTTP 420 rate-limiting and paywall re-routing.

## Key Workflows & Execution Modes

### 1. Command Line Interface (CLI)
- Command: `python main.py` or `make run`
- Flow:
  1. `main.py` executes `execute_t2m_research()` from `src/core/pipeline_runner.py`.
  2. `pipeline_runner.py` verifies IEEE access via `EZProxyManager`, queries active search sources, downloads full-text PDFs to `<project_root>/articles/`, runs 4 sub-agent domain analyses, synthesizes findings via Master Orchestrator, automatically enriches the report with the `# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION` table via `citation_enricher.py`, and saves the final output report directly to `<project_root>/LITERATURE_REVIEW.md`.

### 2. Open WebUI Integration
- Pipeline script: `openwebui/t2m_pipeline.py`
- Tool script: `openwebui/t2m_openwebui_tool.py`
- Open WebUI calls `execute_t2m_research()`, which performs identical paper retrieval, PDF downloading to `articles/`, credibility enrichment, and review saving to `LITERATURE_REVIEW.md`. Hot-reloading dynamically reloads `src.auth`, `src.fetchers`, `src.core`, and `src.agents` modules without restarting the container.

## Output Artifact Rules
1. **`LITERATURE_REVIEW.md`**: Saved ONLY at the root of the project workspace (`<project_root>/LITERATURE_REVIEW.md`). Pipeline execution overwrites this file with fresh results rather than appending duplicate headers.
2. **`articles/` Directory**: Reserved strictly for binary full-text `.pdf` files (e.g., `articles/Paper_Title.pdf`). Do NOT duplicate timestamped `.md` files or literature reviews inside `articles/`.
