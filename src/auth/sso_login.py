import os
import sys
import time
import json
import argparse
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.utils.logger import logger
from src.auth.ezproxy_auth import COOKIES_FILE_PATH, set_host_permissions

SSO_URL = "https://sso.afeka.ac.il/my.policy"
LOGIN_POST_URL = "https://sso.afeka.ac.il/my.policy"


def login_afeka_sso(
    username: str = None,
    password: str = None,
    status_callback: callable = None,
    interactive_fallback: bool = True,
) -> tuple:
    """
    Authenticates institutional access for Afeka College via direct F5 APM 2FA mobile push.
    Submits credentials to https://sso.afeka.ac.il/my.policy, which automatically triggers
    a mobile push notification on the user's phone. Polls until fingerprint approval is received.
    """
    logger.info("==================================================")
    logger.info("🔐 AFEKA INSTITUTIONAL 2FA AUTHENTICATOR")
    logger.info("==================================================")

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

    clean_username = username.strip()
    if "@" in clean_username:
        clean_username = clean_username.split("@")[0]

    domain = os.getenv("IEEE_DOMAIN", "ACADEMIC")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5,he;q=0.3',
    })

    try:
        init_msg = f"Connecting to Afeka SSO portal ({SSO_URL})..."
        logger.info(f"[*] {init_msg}")
        if status_callback:
            status_callback(f"🌐 {init_msg}")

        # Initialize session on F5 portal
        session.get(SSO_URL, verify=False, timeout=15)

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

        push_msg = "📱 Push notification sent to your mobile phone! Please approve with your fingerprint..."
        logger.info(push_msg)
        if status_callback:
            status_callback(f"\n{push_msg}\n")

        # F5 APM triggers mobile push on POST
        try:
            auth_resp = session.post(LOGIN_POST_URL, data=payload, verify=False, timeout=50)

            # Check if immediately granted
            if "my.policy" not in auth_resp.url or "logout" in auth_resp.text.lower() or "vdesk" in auth_resp.url or "webtop" in auth_resp.url:
                cookies_dict = {c.name: c.value for c in session.cookies}
                if cookies_dict:
                    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cookies_dict, f, indent=2)
                    set_host_permissions(COOKIES_FILE_PATH)
                    succ = f"✅ Logged in successfully! {len(cookies_dict)} session cookies saved."
                    logger.info(succ)
                    if status_callback:
                        status_callback(f"\n{succ}\n")
                    return True, succ

            if "שגויים" in auth_resp.text or "incorrect" in auth_resp.text.lower():
                err = "Invalid username or password reported by Afeka SSO portal."
                logger.error(f"[!] {err}")
                if status_callback:
                    status_callback(f"\n❌ {err}\n")
                return False, err
        except requests.exceptions.ReadTimeout:
            logger.info("[*] Initial POST timed out, polling status for mobile approval...")

        # Poll SSO status until mobile push is approved
        max_polls = 15
        poll_interval = 3

        for attempt in range(1, max_polls + 1):
            time.sleep(poll_interval)
            check_resp = session.get(SSO_URL, verify=False, timeout=10)

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
                    set_host_permissions(COOKIES_FILE_PATH)
                    succ = f"✅ Logged in successfully! {len(cookies_dict)} session cookies saved."
                    logger.info(succ)
                    if status_callback:
                        status_callback(f"\n{succ}\n")
                    return True, succ

            poll_update = f"⏳ Waiting for mobile fingerprint approval... ({attempt}/{max_polls})"
            logger.info(poll_update)
            if status_callback:
                status_callback(poll_update)

        timeout_msg = "❌ Authentication timed out: mobile push was not approved."
        logger.warning(timeout_msg)
        if status_callback:
            status_callback(f"\n{timeout_msg}\n")
        return False, timeout_msg

    except Exception as e:
        err_msg = f"SSO Login error: {e}"
        logger.error(f"[!] {err_msg}")
        if status_callback:
            status_callback(f"\n❌ {err_msg}\n")
        return False, err_msg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Afeka SSO Authenticator")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    success, message = login_afeka_sso(username=args.username, password=args.password)
    sys.exit(0 if success else 1)
