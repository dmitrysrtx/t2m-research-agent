import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.logger import logger
from src.utils.ezproxy_auth import COOKIES_FILE_PATH

def import_cookies_interactively():
    print("==================================================")
    print("🍪 EZproxy Cookie Importer (Headless Server Helper)")
    print("==================================================")
    print("Since this headless server runs without a graphical desktop,")
    print("the easiest way to authorize access is copying cookies from your desktop browser.\n")
    print("📌 INSTRUCTIONS (takes ~15 seconds):")
    print("1. Open your institutional library portal on your PC browser:")
    print("   https://ieeexplore-ieee-org.ezproxy.afeka.ac.il (or Technion/Kinneret)")
    print("2. Open Developer Tools (F12 ➔ Network / Application) OR the Cookie-Editor extension.")
    print("3. Paste the contents below.\n")
    print("Supported input formats:")
    print(" - Format 1: Cookie header string ('ezproxy=...; JSESSIONID=...; ...')")
    print(" - Format 2: Raw JSON exported from Cookie-Editor\n")
    
    user_input = input("👉 Paste cookies and press Enter:\n").strip()
    
    if not user_input:
        print("❌ Error: Empty input provided.")
        return

    parsed_cookies = {}
    
    # Try parsing as JSON first
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

    # Fallback: parse as standard HTTP Cookie header string
    if not parsed_cookies:
        pairs = user_input.split(";")
        for p in pairs:
            if "=" in p:
                k, v = p.strip().split("=", 1)
                if k and v:
                    parsed_cookies[k] = v

    if not parsed_cookies:
        print("❌ Could not extract cookies from the provided string.")
        return

    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(parsed_cookies, f, indent=2)

    print(f"\n✅ SUCCESS! Saved {len(parsed_cookies)} cookies to:")
    print(f"   {COOKIES_FILE_PATH}")
    print("\nYou can now run 'python3 main.py' — the pipeline will download full IEEE PDFs!")

if __name__ == "__main__":
    import_cookies_interactively()
