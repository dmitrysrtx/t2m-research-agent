import os
import sys
import time
import json
import argparse
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.utils.logger import logger
from src.utils.ezproxy_auth import COOKIES_FILE_PATH, verify_live_ieee_access

IEEE_HOME_URL = "https://ieeexplore.ieee.org"

def login_ieee_via_afeka_browser(
    username: str = None,
    password: str = None,
    headless: bool = True,
    status_callback: callable = None,
    approval_timeout: int = 90
) -> tuple:
    """
    Automates the complete SP-Initiated IEEE Xplore Institutional Login via Afeka College:
    1. Launches Chromium/Google-Chrome.
    2. Navigates to IEEE Xplore (ieeexplore.ieee.org).
    3. Clicks 'Institutional Sign In' -> 'Access Through Afeka College' (SeamlessAccess/Shibboleth).
    4. Auto-fills Afeka SSO credentials (username, password, selects 'סטודנטים').
    5. Submits form to trigger 2FA push notification to user's mobile phone.
    6. Waits for mobile fingerprint approval and automatic redirect back to IEEE Xplore.
    7. Captures authenticated IEEE session cookies (WLSESSION, IEEE_AUTH, etc.) and saves to ezproxy_cookies.json.
    8. Validates live PDF entitlement.
    """
    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not password:
        err = "Missing IEEE_USERNAME or IEEE_PASSWORD in environment."
        logger.error(f"[!] {err}")
        if status_callback:
            status_callback(f"❌ {err}")
        return False, err

    clean_username = username.strip()
    if "@" in clean_username:
        clean_username = clean_username.split("@")[0]

    logger.info("==================================================")
    logger.info("🌐 AUTOMATED IEEE XPLORE INSTITUTIONAL AUTH (BROWSER)")
    logger.info("==================================================")
    logger.info(f"[*] Starting browser-driven SAML authentication for user: {clean_username}...")

    init_msg = "Launching browser to authenticate with IEEE Xplore via Afeka College..."
    if status_callback:
        status_callback(f"🌐 {init_msg}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        err = "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        logger.error(f"[!] {err}")
        return False, err

    chrome_path = "/usr/bin/google-chrome"
    exec_path = chrome_path if os.path.exists(chrome_path) else None

    try:
        with sync_playwright() as p:
            launch_kwargs = {
                "headless": headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ]
            }
            if exec_path:
                launch_kwargs["executable_path"] = exec_path

            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # 1. Navigate to IEEE Xplore
            step1_msg = "Connecting to IEEE Xplore (https://ieeexplore.ieee.org)..."
            logger.info(f"[*] {step1_msg}")
            if status_callback:
                status_callback(f"🌐 {step1_msg}")

            page.goto(IEEE_HOME_URL, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Dismiss cookie consent dialog if present
            try:
                cookie_accept = page.query_selector('button:has-text("Accept"), #onetrust-accept-btn-handler, button[aria-label="Accept"]')
                if cookie_accept and cookie_accept.is_visible():
                    cookie_accept.click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            # 2. Click 'Institutional Sign In'
            step2_msg = "Opening Institutional Sign In modal on IEEE Xplore..."
            logger.info(f"[*] {step2_msg}")
            if status_callback:
                status_callback(f"🔑 {step2_msg}")

            inst_btn = page.query_selector('button:has-text("Institutional Sign In"), a:has-text("Institutional Sign In"), text="Institutional Sign In"')
            if not inst_btn:
                # Direct fallback to WAYF endpoint if button not immediately queryable
                page.goto("https://ieeexplore.ieee.org/servlet/wayf.jsp", timeout=20000)
            else:
                inst_btn.click()

            page.wait_for_timeout(2500)

            # 3. Select Afeka College (SeamlessAccess or Search)
            afeka_btn = page.query_selector('button:has-text("Afeka College"), text="Access Through Afeka College", text="Afeka College"')
            if afeka_btn:
                logger.info("[*] Found 'Access Through Afeka College' button, clicking...")
                afeka_btn.click()
            else:
                logger.info("[*] Searching for 'Afeka' in institution search...")
                search_input = page.query_selector('input#inst-search, input[placeholder*="institution" i], input[type="search"]')
                if search_input:
                    search_input.fill("Afeka")
                    page.wait_for_timeout(1500)
                    result_item = page.query_selector('text="Afeka Academic College", text="Afeka College", text="Afeka"')
                    if result_item:
                        result_item.click()

            # 4. Wait for redirection to Afeka SSO Portal
            step4_msg = "Redirecting to Afeka College Identity Provider (sso.afeka.ac.il)..."
            logger.info(f"[*] {step4_msg}")
            if status_callback:
                status_callback(f"🏛️ {step4_msg}")

            try:
                page.wait_for_url("**/sso.afeka.ac.il/**", timeout=20000)
            except Exception:
                logger.warning("[*] URL did not immediately match sso.afeka.ac.il, checking current page...")

            page.wait_for_timeout(2000)

            # 5. Fill Afeka Login Credentials
            logger.info(f"[*] Submitting credentials for user: {clean_username}...")
            user_input = page.query_selector('input[name="username"], input[type="text"]')
            pass_input = page.query_selector('input[name="password"], input[type="password"]')

            if user_input and pass_input:
                user_input.fill(clean_username)
                pass_input.fill(password.strip())

                # Select 'סטודנטים' radio button (default or first radio)
                radios = page.query_selector_all('input[type="radio"]')
                if radios:
                    try:
                        radios[0].check()
                    except Exception:
                        pass

                # Click 'כניסה' (Submit)
                submit_btn = page.query_selector('input[type="submit"], button:has-text("כניסה"), button[type="submit"]')
                if submit_btn:
                    submit_btn.click()
                    logger.info("[*] Login form submitted.")

            # 6. Wait for mobile 2FA push notification approval
            push_msg = "📱 Push notification sent to your mobile phone! Please approve with your fingerprint..."
            logger.info(push_msg)
            if status_callback:
                status_callback(f"\n{push_msg}\n")

            # 7. Wait for redirect back to IEEE Xplore after push approval
            wait_msg = "⏳ Waiting for fingerprint approval and redirect back to IEEE Xplore..."
            logger.info(wait_msg)
            if status_callback:
                status_callback(wait_msg)

            page.wait_for_url("**/ieeexplore.ieee.org/**", timeout=approval_timeout * 1000)
            page.wait_for_timeout(3000)

            # 8. Extract authenticated session cookies
            logger.info("[*] Returned to IEEE Xplore! Extracting authenticated session cookies...")
            all_cookies = context.cookies()
            cookies_dict = {}

            for c in all_cookies:
                cookies_dict[c["name"]] = c["value"]

            if cookies_dict:
                with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cookies_dict, f, indent=2)

                logger.info(f"✅ Saved {len(cookies_dict)} session cookies to {COOKIES_FILE_PATH}")

            browser.close()

            # 9. Verify live access immediately
            is_valid, probe_reason = verify_live_ieee_access()
            if is_valid:
                succ = "🎉 IEEE Institutional Access successfully authenticated! 'Access provided by Afeka College' is now active."
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
        err = f"Browser authentication error: {e}"
        logger.error(f"[!] {err}")
        if status_callback:
            status_callback(f"\n❌ {err}\n")
        return False, err

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated IEEE Institutional Login via Afeka")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    ok, msg = login_ieee_via_afeka_browser(username=args.username, password=args.password)
    sys.exit(0 if ok else 1)
