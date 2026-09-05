import os
import sys
import json
import time
from dotenv import load_dotenv
from src.utils.logger import logger
from src.auth.ezproxy_auth import (
    PROJECT_ROOT,
    COOKIES_FILE_PATH,
    set_host_permissions,
    verify_live_ieee_access,
)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
IEEE_HOME_URL = "https://ieeexplore.ieee.org"


def _find_clickable(page, selectors: list):
    """Tries a list of selectors and returns the first visible element."""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return el
        except Exception:
            pass
    return None


def run_browser_auth_flow(
    username: str = None,
    password: str = None,
    headless: bool = True,
    status_callback: callable = None,
    approval_timeout: int = 90,
) -> tuple:
    """Automates IEEE Xplore Institutional Login via Afeka College SSO with 2FA Push."""
    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not password:
        err = "Missing IEEE_USERNAME or IEEE_PASSWORD in environment."
        if status_callback:
            status_callback(f"❌ {err}")
        return False, err

    clean_username = username.strip().split("@")[0]
    if status_callback:
        status_callback(f"🌐 Launching host browser for user: {clean_username}...")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        err = "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        if status_callback:
            status_callback(f"❌ {err}")
        return False, err

    chrome_path = "/usr/bin/google-chrome"
    exec_path = chrome_path if os.path.exists(chrome_path) else None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                executable_path=exec_path,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            # 1. Open IEEE Xplore
            if status_callback:
                status_callback("🌐 Connecting to IEEE Xplore (https://ieeexplore.ieee.org)...")
            page.goto(IEEE_HOME_URL, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Dismiss cookie consent
            cookie_accept = _find_clickable(page, ['button:has-text("Accept")', '#onetrust-accept-btn-handler', 'button[aria-label="Accept"]'])
            if cookie_accept:
                try:
                    cookie_accept.click()
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

            # 2. Open Institutional Sign In
            if status_callback:
                status_callback("🔑 Opening Institutional Sign In on IEEE Xplore...")
            inst_btn = _find_clickable(page, ['button:has-text("Institutional Sign In")', 'a:has-text("Institutional Sign In")', 'a[href*="wayf"]'])
            if inst_btn:
                inst_btn.click()
            else:
                page.goto("https://ieeexplore.ieee.org/servlet/wayf.jsp", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

            # 3. Select Afeka College
            afeka_btn = _find_clickable(page, ['button:has-text("Afeka College")', 'a:has-text("Afeka College")', 'button:has-text("Afeka")'])
            if afeka_btn:
                afeka_btn.click()
            else:
                search_input = page.query_selector('input#inst-search, input[placeholder*="institution" i], input[type="search"]')
                if search_input:
                    search_input.fill("Afeka")
                    page.wait_for_timeout(1500)
                    item = _find_clickable(page, ['li:has-text("Afeka")', 'a:has-text("Afeka")', 'button:has-text("Afeka")'])
                    if item:
                        item.click()

            # 4. Wait for redirection to Afeka SSO Portal
            if status_callback:
                status_callback("🏛️ Redirecting to Afeka College Identity Provider (sso.afeka.ac.il)...")
            try:
                page.wait_for_url("**/sso.afeka.ac.il/**", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(2000)

            # 5. Fill Afeka Login Credentials
            user_input = page.query_selector('input[name="username"], input[type="text"]')
            pass_input = page.query_selector('input[name="password"], input[type="password"]')
            if user_input and pass_input:
                user_input.fill(clean_username)
                pass_input.fill(password.strip())
                radios = page.query_selector_all('input[type="radio"]')
                if radios:
                    try:
                        radios[0].check()
                    except Exception:
                        pass
                submit_btn = page.query_selector('input[type="submit"], button:has-text("כניסה"), button[type="submit"]')
                if submit_btn:
                    submit_btn.click()

            # 6. Wait for 2FA push notification approval
            push_msg = "📱 Push notification sent to mobile phone! Please approve with your fingerprint..."
            if status_callback:
                status_callback(f"\n{push_msg}\n")

            # 7. Wait for redirect back to IEEE Xplore
            if status_callback:
                status_callback("⏳ Waiting for fingerprint approval and redirect back to IEEE Xplore...")
            try:
                page.wait_for_url("**/ieeexplore.ieee.org/**", timeout=approval_timeout * 1000)
            except Exception:
                pass
            page.wait_for_timeout(3000)

            # 8. Extract authenticated session cookies
            all_cookies = context.cookies()
            cookies_dict = {c["name"]: c["value"] for c in all_cookies}
            if cookies_dict:
                with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cookies_dict, f, indent=2)
                set_host_permissions(COOKIES_FILE_PATH)

            browser.close()

            # 9. Verify live access immediately
            is_valid, probe_reason = verify_live_ieee_access()
            if is_valid:
                succ = f"🎉 Successfully authenticated! {len(cookies_dict)} session cookies saved to {COOKIES_FILE_PATH}"
                if status_callback:
                    status_callback(f"\n{succ}\n")
                return True, succ
            else:
                warn = f"Cookies saved, but live IEEE probe failed: {probe_reason}"
                if status_callback:
                    status_callback(f"\n⚠️ {warn}\n")
                return False, warn

    except Exception as e:
        err = f"Authentication error: {e}"
        if status_callback:
            status_callback(f"\n❌ {err}\n")
        return False, err


if __name__ == "__main__":
    def print_cb(msg: str):
        print(f"[*] {msg}")

    print("==================================================")
    print("🔐 Standalone Afeka SSO Browser Flow (Host Playwright)")
    print("==================================================")
    ok, message = run_browser_auth_flow(status_callback=print_cb)
    print(f"\nResult: {'SUCCESS' if ok else 'FAILED'}")
    print(message)
    sys.exit(0 if ok else 1)
