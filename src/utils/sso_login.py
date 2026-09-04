import os
import sys
import time
import json
import argparse
import requests
import urllib3
from dotenv import load_dotenv

# Suppress urllib3 TLS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env file automatically
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.utils.logger import logger
from src.utils.ezproxy_auth import COOKIES_FILE_PATH

SSO_URL = "https://sso.afeka.ac.il/my.policy"
LOGIN_POST_URL = "https://sso.afeka.ac.il/my.policy"

def login_afeka_sso(
    username: str = None,
    password: str = None,
    status_callback: callable = None,
    interactive_fallback: bool = True
) -> tuple:
    """
    Authenticates institutional access for IEEE Xplore via Afeka College.
    Primary method: Browser-driven SP-Initiated SAML via Playwright (completes full IEEE handshake).
    Fallback method: Direct F5 BIG-IP APM pure Python login.
    """
    logger.info("==================================================")
    logger.info("🔐 AFEKA / IEEE INSTITUTIONAL AUTHENTICATOR")
    logger.info("==================================================")

    # Precedence Cascade: CLI Arg -> .env File -> Interactive Prompt
    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not username.strip():
        if interactive_fallback:
            username = input("👤 Enter your Afeka username/email: ").strip()
        else:
            msg = "Missing IEEE_USERNAME in environment."
            logger.error(f"[!] {msg}")
            return False, msg

    if not password or not password.strip():
        if interactive_fallback:
            import getpass
            password = getpass.getpass("🔑 Enter your Afeka password: ").strip()
        else:
            msg = "Missing IEEE_PASSWORD in environment."
            logger.error(f"[!] {msg}")
            return False, msg

    # 1. Attempt Browser-driven IEEE SAML Authentication (matches exact user workflow)
    try:
        from src.utils.playwright_login import login_ieee_via_afeka_browser
        logger.info("[*] Launching browser-driven IEEE Institutional workflow...")
        ok, msg = login_ieee_via_afeka_browser(
            username=username,
            password=password,
            status_callback=status_callback
        )
        if ok:
            return ok, msg
        logger.warning(f"[*] Browser login finished with: {msg}. Falling back to direct portal...")
    except Exception as e:
        logger.warning(f"[*] Browser authentication bypass ({e}). Proceeding to direct portal login...")

    # Strip @s.afeka.ac.il domain suffix if provided, as F5 APM expects sAMAccountName with Domain=ACADEMIC
    clean_username = username.strip()
    if "@" in clean_username:
        clean_username = clean_username.split("@")[0]

    domain = os.getenv("IEEE_DOMAIN", "ACADEMIC")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5,he;q=0.3',
    })

    try:
        init_msg = f"Connecting to Afeka SSO portal ({SSO_URL})..."
        logger.info(f"[*] {init_msg}")
        if status_callback:
            status_callback(f"🌐 {init_msg}")

        # Handle initial connection with retry for F5 session resets
        resp = None
        for get_attempt in range(1, 3):
            try:
                resp = session.get(SSO_URL, verify=False, timeout=15)
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
                if get_attempt < 2:
                    logger.warning(f"[*] Initial connection reset by F5 portal ({conn_err}), retrying with fresh session in 2s...")
                    time.sleep(2)
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5,he;q=0.3',
                        'Connection': 'close',
                    })
                else:
                    raise conn_err
        
        payload = {
            'username': clean_username,
            'password': password.strip(),
            'Domain': domain,
            'vhost': 'standard',
        }
        
        sub_msg = f"Submitting credentials for user: {clean_username} (Domain: {domain})..."
        logger.info(f"[*] {sub_msg}")
        if status_callback:
            status_callback(f"🔐 {sub_msg}")

        push_msg = "📱 Push notification requested! Please check your mobile phone and approve with your fingerprint..."
        logger.info(push_msg)
        if status_callback:
            status_callback(f"\n{push_msg}\n")

        # F5 APM with mobile push blocks on POST while waiting for MFA approval
        try:
            auth_resp = session.post(LOGIN_POST_URL, data=payload, verify=False, timeout=50)

            # Check if authentication succeeded directly from POST response
            if "my.policy" not in auth_resp.url or "logout" in auth_resp.text.lower() or "vdesk" in auth_resp.url or "webtop" in auth_resp.url:
                cookies_dict = {c.name: c.value for c in session.cookies}
                if cookies_dict:
                    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cookies_dict, f, indent=2)
                    success_msg = f"✅ Logged in successfully! {len(cookies_dict)} session cookies saved to {COOKIES_FILE_PATH}"
                    logger.info(success_msg)
                    if status_callback:
                        status_callback(f"\n{success_msg}\n")
                    return True, success_msg

            # Check for explicit error in POST response
            if "שגויים" in auth_resp.text or "incorrect" in auth_resp.text.lower():
                err_msg = "Invalid username, password, or domain reported by Afeka SSO portal."
                logger.error(f"[!] {err_msg}")
                if status_callback:
                    status_callback(f"\n❌ {err_msg}\n")
                return False, err_msg

        except requests.exceptions.ReadTimeout:
            logger.info("[*] Initial POST timed out, checking status via polling...")

        # Poll SSO status until push notification is approved
        max_polls = 15
        poll_interval = 3
        
        for attempt in range(1, max_polls + 1):
            time.sleep(poll_interval)
            check_resp = session.get(SSO_URL, verify=False, timeout=10)
            
            # Check if session redirected past login (F5 APM session granted)
            session_granted = (
                "my.policy" not in check_resp.url or
                "logout" in check_resp.text.lower() or
                "vdesk" in check_resp.url or
                "webtop" in check_resp.url
            )
            
            if session_granted:
                cookies_dict = {c.name: c.value for c in session.cookies}
                if cookies_dict:
                    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cookies_dict, f, indent=2)
                    success_msg = f"✅ Logged in successfully! {len(cookies_dict)} session cookies saved to {COOKIES_FILE_PATH}"
                    logger.info(success_msg)
                    if status_callback:
                        status_callback(f"\n{success_msg}\n")
                    return True, success_msg

            poll_update = f"⏳ Waiting for mobile fingerprint approval... ({attempt}/{max_polls})"
            logger.info(poll_update)
            if status_callback:
                status_callback(f"{poll_update}")

        timeout_msg = "❌ Authentication timed out or push notification was not approved."
        logger.warning(timeout_msg)
        if status_callback:
            status_callback(f"\n{timeout_msg}\n")
        return False, timeout_msg

    except requests.exceptions.ConnectionError as ce:
        err_msg = (
            f"SSO Gateway Connection Reset: The Afeka F5 APM gateway closed the connection. "
            f"An active session is likely already authenticated, or rapid reconnects were rate-limited."
        )
        logger.warning(f"[!] {err_msg} ({ce})")
        if status_callback:
            status_callback(f"\nℹ️ {err_msg}\n")
        return False, err_msg
    except Exception as e:
        err_msg = f"SSO Login error: {e}"
        logger.error(f"[!] {err_msg}")
        if status_callback:
            status_callback(f"\n❌ {err_msg}\n")
        return False, err_msg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Afeka SSO Pure Python Authenticator")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    success, message = login_afeka_sso(username=args.username, password=args.password)
    sys.exit(0 if success else 1)
