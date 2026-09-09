#!/usr/bin/env python3
"""
Langfuse Diagnostic Script v4 — T2M Research Agent
===================================================
SDK v4.x: uses @observe() from `langfuse` (not `langfuse.decorators`).

Usage:
    python3 test_langfuse_diag.py
"""
import os
import sys
import logging
import time

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

os.environ.setdefault("LANGFUSE_DEBUG", "True")
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
                    stream=sys.stdout)

HOST       = os.getenv("LANGFUSE_HOST", "http://192.168.68.53:3005")
PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")

print("\n" + "="*60)
print("🔍  LANGFUSE DIAGNOSTICS (SDK v4 / @observe)")
print("="*60)
print(f"  HOST       : {HOST}")
print(f"  PUBLIC_KEY : {PUBLIC_KEY[:14]}...  (len={len(PUBLIC_KEY)})")
print(f"  SECRET_KEY : {SECRET_KEY[:14]}...  (len={len(SECRET_KEY)})")
print("="*60 + "\n")

if not PUBLIC_KEY or not SECRET_KEY:
    print("❌  ABORT: Keys not set!"); sys.exit(1)

import urllib.request
health_url = HOST.rstrip("/") + "/api/public/health"
print(f"🌐  Checking: {health_url}")
try:
    with urllib.request.urlopen(health_url, timeout=5) as r:
        print(f"✅  HTTP {r.status} — {r.read().decode()}")
except Exception as e:
    print(f"❌  {e}"); sys.exit(1)

try:
    from langfuse import Langfuse, observe
except ImportError as e:
    print(f"❌  {e}"); sys.exit(1)

print("\n📦  Init Langfuse client …")
lf = Langfuse(public_key=PUBLIC_KEY, secret_key=SECRET_KEY, host=HOST, debug=True)
print("✅  Client OK")

print("\n🔑  auth_check() …")
ok = lf.auth_check()
print(f"{'✅' if ok else '❌'}  auth_check() → {ok}")
if not ok: sys.exit(1)

@observe(name="diag-root-trace")
def run_trace():
    """Creates a root trace + child events using Langfuse SDK v4 API."""
    # create_event is called inside @observe context → attached as child
    lf.create_event(
        name="diag-network-check",
        input={"url": health_url},
        output={"status": "ok"},
        metadata={"ts": time.strftime("%Y-%m-%d %H:%M:%S")},
    )

    span = lf.start_observation(
        name="diag-tool-span",
        as_type="tool",
        input={"tool": "arxiv_fetcher", "query": "t2m human motion"},
    )
    time.sleep(0.05)
    span.update(output={"papers": 3})
    span.end()

    lf.start_observation(
        name="diag-generation",
        as_type="generation",
        output={"content": "Synthesis complete."},
        usage_details={"total": 42},
    ).end()

    return "ok"

print("\n📝  Creating trace with @observe() + create_event() + start_observation() …")
try:
    result = run_trace()
    print(f"✅  Trace dispatched, result={result!r}")
except Exception as e:
    print(f"❌  Failed: {e}")
    import traceback; traceback.print_exc()

print("\n💾  Flushing …")
try:
    lf.flush()
    print("✅  Flush OK — check Langfuse dashboard now!")
except Exception as e:
    print(f"❌  Flush failed: {e}")

print(f"\n🏁  Done. Open: {HOST}")
