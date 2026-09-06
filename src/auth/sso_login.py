import os
import sys
import time
import json
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
    _is_tracker_cookie,
)

IEEE_HOME_URL = "https://ieeexplore.ieee.org"
AFEKA_WAYF_URL = (
    "https://ieeexplore.ieee.org/servlet/wayf.jsp?"
    "entityId=https://idp.afeka.ac.il/openathens&url=https%3A%2F%2Fieeexplore.ieee.org%2FXplore%2Fhome.jsp"
)


def login_afeka_sso(
    username: str = None,
    password: str = None,
    status_callback: callable = None,
    interactive_fallback: bool = True,
    approval_timeout: int = 120,
) -> tuple:
    """Automates IEEE SAML login via Afeka IdP with mobile 2FA push approval."""
    logger.info("==================================================")
    logger.info("🔐 IEEE XPLORE INSTITUTIONAL AUTHENTICATOR (AFEKA)")
    logger.info("==================================================")

    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not username.strip():
        if interactive_fallback:
            username = input("👤 Enter your Afeka username/email: ").strip()
        else:
            return False, "Missing IEEE_USERNAME in environment."

    if not password or not password.strip():
        if interactive_fallback:
            import getpass
            password = getpass.getpass("🔑 Enter your Afeka password: ").strip()
        else:
            return False, "Missing IEEE_PASSWORD in environment."

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
            page = context.new_page()
            page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

            # 1. Connect to Afeka SSO via direct WAYF endpoint or interactive UI fallback
            logger.info("[*] Connecting to IEEE Xplore Institutional Gateway...")
            if status_callback:
                status_callback("🌐 Connecting to IEEE Xplore Institutional Gateway...")

            landed_on_sso = False
            try:
                page.goto(AFEKA_WAYF_URL, timeout=20000, wait_until="domcontentloaded")
                time.sleep(2)
                if "sso.afeka.ac.il" in page.url:
                    landed_on_sso = True
            except Exception:
                pass

            if not landed_on_sso:
                logger.info("[*] Navigating via Institutional Sign In dialog...")
                page.goto(IEEE_HOME_URL, timeout=25000, wait_until="domcontentloaded")
                time.sleep(2)
                try:
                    b = page.query_selector("button:has-text('Accept'), .osano-cm-accept-all, #onetrust-accept-btn-handler")
                    if b and b.is_visible():
                        b.click()
                except Exception:
                    pass
                page.locator("a:has-text('Institutional Sign In'):visible").first.click()
                time.sleep(2)
                page.locator("button:has-text('Access Through Your Institution'), button.stats-Global_Inst_sign_in_seamlessaccess_access_through_your_institution_btn").first.click()
                time.sleep(2)
                inp = page.locator("input.inst-typeahead-input").first
                inp.click()
                inp.press_sequentially("Afeka", delay=120)
                time.sleep(2)
                page.locator("a:has-text('Afeka College'), a#Afeka\\ College").first.click()

            # 2. Fill credentials on Afeka SSO
            logger.info(f"[*] Submitting credentials on Afeka SSO for user: {clean_user}...")
            if status_callback:
                status_callback("🏛️ Redirecting to Afeka College Identity Provider (sso.afeka.ac.il)...")
            page.wait_for_url("**/sso.afeka.ac.il/**", timeout=30000)
            time.sleep(1.5)

            user_input = page.locator("input[name='username'], input#input_1").first
            user_input.wait_for(state="visible", timeout=15000)
            user_input.fill(clean_user)

            pass_input = page.locator("input[name='password'], input#input_2").first
            pass_input.fill(password.strip())

            radio_academic = page.locator("input[type='radio'][value='ACADEMIC'], input#input_3_0").first
            if radio_academic.is_visible():
                try:
                    radio_academic.check()
                except Exception:
                    pass

            # 3. Prompt user for 2FA Mobile Push and submit
            push_msg = "📱 Push notification sent to mobile phone! Please approve with your fingerprint (Approve)..."
            logger.info(push_msg)
            if status_callback:
                status_callback(f"\n{push_msg}\n")

            page.locator("input[type='submit'], button:has-text('כניסה')").first.click(no_wait_after=True)

            wait_msg = f"⏳ Waiting up to {approval_timeout}s for mobile approval and redirect back to IEEE Xplore..."
            logger.info(wait_msg)
            if status_callback:
                status_callback(wait_msg)

            # 4. Wait for redirect back to IEEE Xplore
            page.wait_for_url("**/ieeexplore.ieee.org/**", timeout=approval_timeout * 1000)
            time.sleep(4)

            # 5. Extract session cookies (filtered from 3rd party trackers)
            all_cookies = context.cookies()
            cookies_dict = {}
            for c in all_cookies:
                name, val, dom = c.get("name", ""), c.get("value", ""), c.get("domain", "")
                if _is_tracker_cookie(name):
                    continue
                if "ieee.org" in dom or "afeka.ac.il" in dom or "openathens" in dom or not dom:
                    cookies_dict[name] = val

            if cookies_dict:
                with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cookies_dict, f, indent=2)
                set_host_permissions(COOKIES_FILE_PATH)
                logger.info(f"✅ Saved {len(cookies_dict)} session cookies to {COOKIES_FILE_PATH}")

            browser.close()

            # 6. Verify live access
            is_valid, probe_reason = verify_live_ieee_access()
            if is_valid:
                succ = "🎉 IEEE Institutional Access authenticated! 'Access provided by Afeka College' is active."
                logger.info(f"✅ {succ}")
                if status_callback:
                    status_callback(f"\n{succ}\n")
                return True, succ
            else:
                warn = f"Cookies saved, but live IEEE check reported: {probe_reason}"
                logger.warning(f"[!] {warn}")
                if status_callback:
                    status_callback(f"\n⚠️ {warn}\n")
                return True, warn

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
    ok, msg = login_afeka_sso(username=args.username, password=args.password)
    sys.exit(0 if ok else 1)
