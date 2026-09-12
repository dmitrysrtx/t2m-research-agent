"""
title: T2M Academic Research Pipeline (SSOT YAML Manifest)
author: Dmitry Strizhak
version: 2.1.0
license: MIT
description: Multi-agent academic research pipeline configured exclusively via pipeline_config.yaml.
"""

import os
import sys
import queue
import threading
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel

# Ensure agent project directory is in python path
AGENT_PATHS = [
    "/app/t2m-agent",
    "/home/user/projects/RL/Maya_Project/t2m-research-agent",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
]
for p in AGENT_PATHS:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from src.core.pipeline_runner import execute_t2m_research, extract_core_keywords
import agent_config as config

_PIPELINE_LOCK = threading.Lock()
_CURRENT_PIPELINE = {
    "query": "",
    "started_at": 0.0,
}


class Pipeline:
    class Valves(BaseModel):
        """Zero-configuration Valves: pipeline_config.yaml is the Single Source of Truth."""
        pass

    def __init__(self):
        self.id = "t2m_pipeline"
        self.name = "T2M Multi-Agent Academic Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print("[*] T2M Research Pipeline v2.1 (SSOT) initialized successfully.")

    async def on_shutdown(self):
        print("[*] T2M Research Pipeline shut down.")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # 🛡️ Fast-path: Intercept ALL OpenWebUI background utility tasks (stream=False / tasks)
        is_stream = body.get("stream", True) if isinstance(body, dict) else True
        task = None
        if isinstance(body, dict):
            task = body.get("task") or body.get("metadata", {}).get("task")

        msg_content = (user_message or "").lower()

        # Intercept if non-streaming, explicit task, or internal OpenWebUI prompt
        if not is_stream or task or "### task:" in msg_content:
            # 1. Title Generation
            if task == "title_generation" or "title" in msg_content or "summarize" in msg_content:
                raw_text = user_message.strip()
                if messages:
                    for m in messages:
                        if m.get("role") == "user":
                            raw_text = m.get("content", "").strip()
                            break
                short_title = extract_core_keywords(raw_text)[:45].strip().title()
                return f"T2M: {short_title}" if short_title else "T2M Academic Research"

            # 2. Tags Generation
            if task == "tags_generation" or "tag" in msg_content:
                return '["text-to-motion", "robotics", "physics-rl"]'

            # 3. Follow-up suggestions or query generation
            if "follow" in msg_content or "suggest" in msg_content or "questions" in msg_content:
                return (
                    "1. How do physics-guided diffusion models enforce ground contact constraints?\n"
                    "2. What are the key benchmark differences between HumanML3D and KIT-ML datasets?\n"
                    "3. How do RL controllers bridge the gap between kinematic trajectory planning and physical simulation?"
                )

            return ""

        return self._stream_pipeline(user_message, model_id, messages, body)

    def _stream_pipeline(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Generator[str, None, None]:

        # 🔄 Dynamic module reload on each execution (Hot-Reloading without Docker restart)
        try:
            import importlib
            import src.core.config_validator
            import src.core.config_loader
            import src.auth.ezproxy_auth
            import src.auth.ezproxy_session
            import src.auth.afeka_sso
            import src.auth.sso_login
            import src.fetchers.semantic_scholar_fetcher
            import src.fetchers.scholar_fetcher
            import src.fetchers.ieee_fetcher
            import src.fetchers.arxiv_fetcher
            import src.fetchers.citation_enricher
            import src.fetchers.github_verifier
            import src.fetchers.github_finder
            import src.utils.text_formatters
            import src.utils.pdf_downloader
            import src.core.pipeline_runner
            import src.agents.sub_agents
            import src.agents.orchestrator
            import src.telemetry

            importlib.reload(src.core.config_validator)
            importlib.reload(src.core.config_loader)
            importlib.reload(config)
            importlib.reload(src.auth.ezproxy_auth)
            importlib.reload(src.auth.ezproxy_session)
            importlib.reload(src.auth.afeka_sso)
            importlib.reload(src.auth.sso_login)
            importlib.reload(src.fetchers.semantic_scholar_fetcher)
            importlib.reload(src.fetchers.scholar_fetcher)
            importlib.reload(src.fetchers.ieee_fetcher)
            importlib.reload(src.fetchers.arxiv_fetcher)
            importlib.reload(src.fetchers.citation_enricher)
            importlib.reload(src.fetchers.github_verifier)
            importlib.reload(src.fetchers.github_finder)
            importlib.reload(src.utils.text_formatters)
            importlib.reload(src.utils.pdf_downloader)
            importlib.reload(src.telemetry)
            importlib.reload(src.agents.sub_agents)
            importlib.reload(src.agents.orchestrator)
            importlib.reload(src.core.pipeline_runner)
        except Exception as e:
            print(f"[!] Hot reload warning: {e}")

        query = user_message.strip() if user_message else config.DEFAULT_SEARCH_QUERY

        # Explicit /login command handling
        if query.lower() in ["/login", "login", "/auth", "auth"]:
            yield "🔐 **Initiating Afeka SSO Authentication...**\n\n"
            auth_queue = queue.Queue()

            def auth_cb(m: str):
                auth_queue.put(m)

            def auth_worker():
                import src.auth.sso_login
                ok, msg = src.auth.sso_login.login_afeka_sso(
                    status_callback=auth_cb,
                    interactive_fallback=False
                )
                auth_queue.put(("DONE", ok, msg))

            t_auth = threading.Thread(target=auth_worker)
            t_auth.start()

            while t_auth.is_alive() or not auth_queue.empty():
                try:
                    item = auth_queue.get(timeout=0.5)
                    if isinstance(item, tuple) and item[0] == "DONE":
                        ok, msg = item[1], item[2]
                        if ok:
                            yield f"\n\n---\n\n🎉 **Login Successful!** {msg}\nInstitutional access is now active. You can now submit your research questions."
                        else:
                            yield f"\n\n---\n\n❌ **Login Failed:** {msg}"
                        return
                    else:
                        yield f"{item}\n"
                except queue.Empty:
                    continue
            return

        import time

        if not _PIPELINE_LOCK.acquire(blocking=False):
            active_q = _CURRENT_PIPELINE.get("query") or "Academic Research"
            st_time = _CURRENT_PIPELINE.get("started_at", 0.0)
            elapsed = int(time.time() - st_time) if st_time else 0
            mins, secs = elapsed // 60, elapsed % 60
            elapsed_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            yield (
                f"⚠️ **T2M research pipeline is currently running!**\n\n"
                f"- **Active Query:** `{active_q}`\n"
                f"- **Running For:** `{elapsed_str}`\n\n"
                f"Please wait for the active analysis to complete before starting a new one. "
                f"You can monitor real-time progress in the original chat session.\n"
            )
            return

        _CURRENT_PIPELINE["query"] = query[:60]
        _CURRENT_PIPELINE["started_at"] = time.time()

        # Synchronize LLM client from pipeline_config.yaml
        src.agents.sub_agents.MODEL_NAME = config.MODEL_NAME
        src.agents.sub_agents.BASE_URL = config.BASE_URL
        src.agents.sub_agents.API_KEY = config.API_KEY
        src.agents.sub_agents.client = src.agents.sub_agents.OpenAI(
            base_url=config.BASE_URL,
            api_key=config.API_KEY
        )

        msg_queue = queue.Queue()
        sse_sink = src.telemetry.SSEHandler()

        class OpenWebUIAdapterSink(src.telemetry.BaseHandler):
            def handle(self, event):
                etype = event.event_type
                src_name = event.source
                payload = event.payload or {}
                if etype == "THINKING":
                    t = payload.get("thought") or payload.get("message")
                    if t:
                        msg_queue.put(f"🤔 *[{src_name}]* {t}")
                elif etype == "TOOL_CALL":
                    tool = payload.get("tool", "tool")
                    args = payload.get("args") or payload.get("query", "")
                    msg_queue.put(f"🔍 *[{src_name}]* Calling `{tool}` ({args})")
                elif etype == "TOOL_RESULT":
                    tool = payload.get("tool", "tool")
                    res = payload.get("result", "Done")
                    dur = payload.get("duration")
                    dur_s = f" ({dur:.2f}s)" if dur is not None else ""
                    msg_queue.put(f"✅ *[{src_name}]* `{tool}` -> {res}{dur_s}")
                elif etype == "ERROR":
                    err = payload.get("error", "Error")
                    msg_queue.put(f"❌ *[{src_name}]* {err}")

        # Decoupled Telemetry Dispatcher
        pipe_tm = src.telemetry.TelemetryManager([OpenWebUIAdapterSink(), sse_sink])
        if getattr(config, "ENABLE_CLI_LOGS", True):
            pipe_tm.register_handler(src.telemetry.TerminalHandler())
        if getattr(config, "LANGFUSE_PUBLIC_KEY", ""):
            pipe_tm.register_handler(src.telemetry.LangfuseHandler(
                host=getattr(config, "LANGFUSE_HOST", "http://192.168.68.53:3005"),
                public_key=getattr(config, "LANGFUSE_PUBLIC_KEY", ""),
                secret_key=getattr(config, "LANGFUSE_SECRET_KEY", ""),
            ))

        def cb(m: str):
            msg_queue.put(m)

        def runner_worker():
            try:
                # All operational parameters are drawn directly from pipeline_config.yaml (SSOT)
                res = src.core.pipeline_runner.execute_t2m_research(
                    query=query,
                    enable_ieee=config.ENABLE_IEEE_DEFAULT,
                    enable_scholar=config.ENABLE_SCHOLAR_DEFAULT,
                    enable_arxiv=config.ENABLE_ARXIV_DEFAULT,
                    enable_semantic_scholar=config.ENABLE_SEMANTIC_SCHOLAR_DEFAULT,
                    max_results_per_domain=config.MAX_RESULTS_PER_DOMAIN,
                    require_code=config.REQUIRE_CODE_DEFAULT,
                    prefer_code=config.PREFER_CODE_DEFAULT,
                    ezproxy_cookie=getattr(config, "EZPROXY_COOKIE_OVERRIDE", ""),
                    ezproxy_domain=config.EZPROXY_DOMAIN_DEFAULT,
                    save_output_file=True,
                    auto_sso_login=config.AUTO_SSO_LOGIN_DEFAULT,
                    clear_articles_dir=config.CLEAR_ARTICLES_DIR,
                    status_callback=cb,
                    telemetry=pipe_tm,
                )
                msg_queue.put(("RESULT", res))
            except src.core.config_validator.ConfigValidationError as cve:
                msg_queue.put(("ERROR", f"**Configuration Error (pipeline_config.yaml):**\n\n```\n{cve}\n```"))
            except Exception as e:
                import traceback
                traceback.print_exc()
                msg_queue.put(("ERROR", str(e)))

        t = threading.Thread(target=runner_worker)
        t.start()

        try:
            while t.is_alive() or not msg_queue.empty():
                try:
                    item = msg_queue.get(timeout=0.5)
                    if isinstance(item, tuple):
                        if item[0] == "RESULT":
                            yield f"\n\n{item[1]}"
                            return
                        elif item[0] == "ERROR":
                            yield f"\n\n❌ **Execution Error:** {item[1]}\n"
                            return
                    else:
                        yield f"{item}\n"
                except queue.Empty:
                    continue
        finally:
            _CURRENT_PIPELINE["query"] = ""
            _CURRENT_PIPELINE["started_at"] = 0.0
            if _PIPELINE_LOCK.locked():
                _PIPELINE_LOCK.release()
