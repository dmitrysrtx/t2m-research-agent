# 🤖 Agent Standing Instructions & Architectural Rules

## 🎯 Primary Directives
You are an expert AI Coding Assistant operating on this project. You must strictly follow the architectural principles and operational rules listed below.

---

## 🏗️ 1. Modular Architecture & Single Responsibility (SRP)
- **File Length Limit:** Keep individual files under 150–200 lines. If a file grows larger, split it logically.
- **Strict Layer Isolation:**
  - `src/auth/`: EXCLUSIVELY handles EZproxy authentication, SSO login, Cookie importing, and browser session validation.
  - `src/fetchers/`: EXCLUSIVELY handles paper metadata querying (IEEE, Google Scholar, ArXiv, Semantic Scholar).
  - `src/agents/`: EXCLUSIVELY contains system prompts, sub-agent definitions, and LLM synthesis calls.
  - `src/core/`: Handles high-level pipeline execution, orchestrating Auth -> Fetch -> Agents -> Output.
  - `src/utils/`: Shared cross-cutting concerns (e.g., `logger.py`).

---

## 📝 2. Automatic Self-Documentation (Mandatory)
- **EVERY TIME** you modify, add, or refactor code, modules, or configurations:
  - You **MUST** automatically update `README.md` to reflect new directory structures, usage commands, or configuration flags.
  - You **MUST** update `Gemini.md` (or architectural decision logs) with a brief log of the refactoring done.
- **Never wait for the user to remind you to update documentation.**

---

## 🔒 3. Host File Ownership & Permissions Rule
- When writing output files (`.md` reports, downloaded PDFs, articles directory):
  - Always determine host user ownership via `st = os.stat(project_root)` (`st.st_uid`, `st.st_gid`).
  - Apply `os.chown(path, st.st_uid, st.st_gid)` to match host user (`dmitryx:dmitryx`).
  - Set permissions `0o666` for created files and `0o777` for created directories.

---

## 🧪 4. Standalone Module Testability
- Every non-trivial file in `src/auth/`, `src/fetchers/`, `src/core/` **MUST** include a runnable `if __name__ == '__main__':` test block at the bottom.
- Developers must be able to run `python -m src.auth.ezproxy_session` directly to verify functionality in isolation without launching OpenWebUI or full LLM agents.
