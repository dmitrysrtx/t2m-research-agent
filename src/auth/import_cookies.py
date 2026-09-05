import os
import sys
import json
from src.utils.logger import logger
from src.auth.ezproxy_auth import (
    COOKIES_FILE_PATH,
    set_host_permissions,
    verify_live_ieee_access,
)


def import_cookies_interactively():
    """CLI helper to manually paste browser cookies when running in headless environments."""
    print("==================================================")
    print("🍪 EZproxy Cookie Importer (Headless Server Helper)")
    print("==================================================")
    print("Paste cookies exported from desktop browser (Cookie-Editor or Header string):\n")

    user_input = input("👉 Paste cookies and press Enter:\n").strip()
    if not user_input:
        print("❌ Error: Empty input provided.")
        return False

    parsed_cookies = {}
    if user_input.startswith("[") or user_input.startswith("{"):
        try:
            data = json.loads(user_input)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "name" in item and "value" in item:
                        parsed_cookies[item["name"]] = item["value"]
            elif isinstance(data, dict):
                parsed_cookies = data
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")

    if not parsed_cookies:
        for p in user_input.split(";"):
            if "=" in p:
                k, v = p.strip().split("=", 1)
                if k and v:
                    parsed_cookies[k] = v

    if not parsed_cookies:
        print("❌ Could not extract cookies from the provided input.")
        return False

    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(parsed_cookies, f, indent=2)
    set_host_permissions(COOKIES_FILE_PATH)

    print(f"\n✅ Saved {len(parsed_cookies)} cookies to {COOKIES_FILE_PATH}")
    print("[*] Verifying live access to IEEE Xplore...")
    is_valid, reason = verify_live_ieee_access()
    if is_valid:
        print(f"🎉 SUCCESS! {reason}")
    else:
        print(f"⚠️ Live check note: {reason}")
    return is_valid


if __name__ == "__main__":
    ok = import_cookies_interactively()
    sys.exit(0 if ok else 1)
