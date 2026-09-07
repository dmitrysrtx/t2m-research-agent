import os
import sys
import time
import argparse
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.utils.logger import logger
from src.auth.ezproxy_auth import (
    COOKIES_FILE_PATH,
    set_host_permissions,
    verify_live_ieee_access,
    save_ezproxy_cookies,
    load_ezproxy_cookies,
)

IEEE_HOME_URL = "https://ieeexplore.ieee.org"


def _extract_and_save_cookies(context) -> dict:
    """Extracts institutional cookies from Playwright context and saves cleanly."""
    cookies_dict = {}
    for c in context.cookies():
        name, val, dom = c.get("name", ""), c.get("value", ""), c.get("domain", "")
        if any(d in dom for d in ("ieee.org", "afeka.ac.il", "openathens")) or not dom:
            cookies_dict[name] = val
    if cookies_dict:
        save_ezproxy_cookies(cookies_dict)
    return cookies_dict


def login_afeka_sso(
    username: str = None,
    password: str = None,
    status_callback: callable = None,
    interactive_fallback: bool = True,
    approval_timeout: int = 120,
) -> tuple:
    """Automates IEEE SAML login via Afeka IdP with session cookie re-use to reduce 2FA prompts."""
    logger.info("🔐 IEEE XPLORE INSTITUTIONAL AUTHENTICATOR (AFEKA)")

    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")
    if not username or not username.strip():
        username = input("👤 Enter your Afeka username/email: ").strip() if interactive_fallback else ""
        if not username:
            return False, "Missing IEEE_USERNAME."
    if not password or not password.strip():
        import getpass
        password = getpass.getpass("🔑 Enter your Afeka password: ").strip() if interactive_fallback else ""
        if not password:
            return False, "Missing IEEE_PASSWORD."

    clean_user = username.strip().split("@")[0]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed. Run: pip install playwright && playwright install chromium"

    chrome_path = "/usr/bin/google-chrome"
    exec_path = chrome_path if os.path.exists(chrome_path) else None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=exec_path,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )

            # Pre-populate context with existing session cookies to enable silent SAML renewal
            existing_cookies = load_ezproxy_cookies()
            pw_cookies = []
            for name, val in existing_cookies.items():
                dom = ".afeka.ac.il" if name in {"MRHSession", "LastMRH_Session", "F5_ST", "TS01df1230"} else ".ieee.org"
                pw_cookies.append({"name": name, "value": val, "domain": dom, "path": "/"})
            if pw_cookies:
                try:
                    context.add_cookies(pw_cookies)
                except Exception:
                    pass

            page = context.new_page()
            page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

            # 1. Navigate to IEEE Xplore Institutional Gateway
            logger.info("[*] Connecting to IEEE Xplore Institutional Gateway...")
            if status_callback:
                status_callback("🌐 Connecting to IEEE Xplore Institutional Gateway...")

            page.goto(IEEE_HOME_URL, timeout=25000, wait_until="domcontentloaded")
            time.sleep(2)

            for sel in ["button:has-text('Accept')", ".osano-cm-accept-all", "#onetrust-accept-btn-handler"]:
                try:
                    page.locator(sel).first.click(timeout=1000)
                except Exception:
                    pass

            # Check if institutional access is already active
            page_content = page.content().lower()
            if "afeka" in page_content or "access provided by" in page_content:
                _extract_and_save_cookies(context)
                browser.close()
                is_valid, reason = verify_live_ieee_access()
                if is_valid:
                    succ = "🎉 Session already active with Afeka College access! No 2FA required."
                    logger.info(f"✅ {succ}")
                    if status_callback:
                        status_callback(f"\n{succ}\n")
                    return True, succ

            # 2. Institutional Sign In flow
            page.locator("a:has-text('Institutional Sign In'):visible").first.click()
            time.sleep(1.5)
            page.locator("button:has-text('Access Through Your Institution')").first.click()
            time.sleep(1.5)
            inp = page.locator("input.inst-typeahead-input").first
            inp.click()
            inp.press_sequentially("Afeka", delay=100)
            time.sleep(1.5)
            page.locator("a:has-text('Afeka College')").first.click()

            # 3. Handle Afeka SSO Identity Provider
            logger.info(f"[*] Navigating to Afeka Identity Provider for user: {clean_user}...")
            if status_callback:
                status_callback("🏛️ Navigating to Afeka Identity Provider...")

            page.wait_for_url(lambda u: "sso.afeka.ac.il" in u or "ieeexplore.ieee.org" in u, timeout=30000)
            time.sleep(1.5)

            if "sso.afeka.ac.il" in page.url:
                user_input = page.locator("input[name='username'], input#input_1").first
                user_input.wait_for(state="visible", timeout=15000)
                user_input.fill(clean_user)
                page.locator("input[name='password'], input#input_2").first.fill(password.strip())

                radio_academic = page.locator("input[type='radio'][value='ACADEMIC'], input#input_3_0").first
                if radio_academic.is_visible():
                    try:
                        radio_academic.check()
                    except Exception:
                        pass

                # 4. Prompt user for 2FA Mobile Push and submit
                push_msg = "📱 Push notification sent to mobile phone! Please approve with your fingerprint (Approve)..."
                logger.info(push_msg)
                if status_callback:
                    status_callback(f"\n{push_msg}\n")
                page.locator("input[type='submit'], button:has-text('כניסה')").first.click(no_wait_after=True)

                wait_msg = f"⏳ Waiting up to {approval_timeout}s for mobile approval and redirect back to IEEE..."
                logger.info(wait_msg)
                if status_callback:
                    status_callback(wait_msg)

                page.wait_for_url("**/ieeexplore.ieee.org/**", timeout=approval_timeout * 1000)
                time.sleep(4)

            _extract_and_save_cookies(context)
            browser.close()

            # 5. Verify live access
            is_valid, probe_reason = verify_live_ieee_access()
            succ = "🎉 IEEE Institutional Access authenticated! 'Access provided by Afeka College' is active."
            if is_valid:
                logger.info(f"✅ {succ}")
                if status_callback:
                    status_callback(f"\n{succ}\n")
                return True, succ
            return True, f"Cookies saved, probe status: {probe_reason}"

    except Exception as e:
        err = f"Institutional login error: {e}"
        logger.error(f"[!] {err}")
        if status_callback:
            status_callback(f"\n❌ {err}\n")
        return False, err


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated IEEE Institutional Login via Afeka")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()
    ok, msg = login_afeka_sso(username=args.username, password=args.password, status_callback=print)
    print(f"[{'✅ SUCCESS' if ok else '❌ FAILED'}]: {msg}")
    sys.exit(0 if ok else 1)
