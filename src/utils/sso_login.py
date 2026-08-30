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

def login_afeka_sso(username: str = None, password: str = None) -> bool:
    """
    Authenticates with Afeka College SSO (F5 BIG-IP APM) using pure Python requests.
    Reads credentials from .env if omitted.
    Handles mobile push notification (fingerprint approval) automatically.
    Saves session cookies to ezproxy_cookies.json.
    """
    logger.info("==================================================")
    logger.info("🔐 AFEKA COLLEGE SSO AUTHENTICATION (PURE PYTHON)")
    logger.info("==================================================")

    # Precedence Cascade: CLI Arg -> .env File -> Interactive Prompt
    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not username.strip():
        username = input("👤 Enter your Afeka username/email: ").strip()
    if not password or not password.strip():
        import getpass
        password = getpass.getpass("🔑 Enter your Afeka password: ").strip()

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5,he;q=0.3',
    })

    try:
        logger.info(f"[*] Initializing SSO connection to {SSO_URL}...")
        resp = session.get(SSO_URL, verify=False, timeout=15)
        
        payload = {
            'username': username,
            'password': password,
            'v5a8894d0': '1'
        }
        
        logger.info(f"[*] Submitting credentials for user: {username}...")
        auth_resp = session.post(LOGIN_POST_URL, data=payload, verify=False, timeout=15)

        logger.info("📱 Push notification sent to your mobile phone!")
        logger.info("👉 Please approve the prompt on your phone with your fingerprint...")
        
        # Poll SSO status until push notification is approved
        max_polls = 20
        poll_interval = 3
        authenticated = False
        
        for attempt in range(1, max_polls + 1):
            time.sleep(poll_interval)
            check_resp = session.get(SSO_URL, verify=False, timeout=10)
            
            # Check if session redirected past login (F5 APM session granted)
            if "my.policy" not in check_resp.url or "Logout" in check_resp.text or check_resp.status_code == 200:
                cookies_dict = {c.name: c.value for c in session.cookies}

                if cookies_dict:
                    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cookies_dict, f, indent=2)
                    logger.info(f"✅ Logged in successfully! {len(cookies_dict)} session cookies saved to {COOKIES_FILE_PATH}")
                    authenticated = True
                    break

            logger.info(f"[...] Waiting for fingerprint approval on mobile phone... ({attempt}/{max_polls})")

        if not authenticated:
            cookies_dict = {c.name: c.value for c in session.cookies}
            if cookies_dict:
                with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cookies_dict, f, indent=2)
                logger.info(f"[*] Saved {len(cookies_dict)} session cookies to {COOKIES_FILE_PATH}")

        return authenticated

    except Exception as e:
        logger.error(f"[!] SSO Login error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Afeka SSO Pure Python Authenticator")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    login_afeka_sso(username=args.username, password=args.password)
