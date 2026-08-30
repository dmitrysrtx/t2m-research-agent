import os
import json
import sys
from dotenv import load_dotenv
from src.utils.logger import logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIES_FILE_PATH = os.path.join(PROJECT_ROOT, "ezproxy_cookies.json")

# Load .env file automatically
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def get_institutional_credentials(valves=None) -> dict:
    """
    Retrieves institutional credentials following the Precedence Cascade:
    1. OpenWebUI Valves (UI overrides)
    2. Environment variables / .env file
    3. Fallback defaults
    """
    institution = os.getenv("IEEE_INSTITUTION", "afeka")
    username = os.getenv("IEEE_USERNAME", "")
    password = os.getenv("IEEE_PASSWORD", "")

    if valves:
        if hasattr(valves, "IEEE_INSTITUTION") and valves.IEEE_INSTITUTION and valves.IEEE_INSTITUTION.strip():
            institution = valves.IEEE_INSTITUTION.strip()
        if hasattr(valves, "IEEE_USERNAME") and valves.IEEE_USERNAME and valves.IEEE_USERNAME.strip():
            username = valves.IEEE_USERNAME.strip()
        if hasattr(valves, "IEEE_PASSWORD") and valves.IEEE_PASSWORD and valves.IEEE_PASSWORD.strip():
            password = valves.IEEE_PASSWORD.strip()

    return {
        "institution": institution,
        "username": username,
        "password": password
    }


def convert_to_ezproxy_url(url: str, ezproxy_domain: str = None) -> str:
    """
    Preserves direct IEEE Xplore URLs (ieeexplore.ieee.org) so authenticated session cookies
    are sent directly to IEEE Xplore without failing on non-existent EZproxy DNS hosts.
    """
    if not url:
        return url
        
    # Ensure stampPDF endpoint for direct binary PDF download if it's stamp.jsp
    if "ieeexplore.ieee.org" in url and "/stamp/stamp.jsp" in url:
        return url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
        
    return url


def load_ezproxy_cookies(valves=None) -> dict:
    """
    Loads EZproxy / IEEE authentication cookies from:
    1. OpenWebUI Valves (EZPROXY_COOKIE override)
    2. EZPROXY_COOKIE environment variable (.env)
    3. ezproxy_cookies.json file in project root.
    """
    cookies = {}

    # Check Valves first
    env_cookie = None
    if valves and hasattr(valves, "EZPROXY_COOKIE") and valves.EZPROXY_COOKIE.strip():
        env_cookie = valves.EZPROXY_COOKIE.strip()
    else:
        env_cookie = os.getenv("EZPROXY_COOKIE")

    if env_cookie and env_cookie.strip():
        cookie_str = env_cookie.strip()
        # 1. Try parsing JSON (Array or Dict)
        try:
            data = json.loads(cookie_str)
            if isinstance(data, list):
                for cookie in data:
                    if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                        cookies[cookie["name"]] = cookie["value"]
            elif isinstance(data, dict):
                cookies = {str(k): str(v) for k, v in data.items()}
            if cookies:
                return cookies
        except Exception:
            pass

        # 2. Fallback to standard Cookie header string
        try:
            pairs = cookie_str.split(";")
            for p in pairs:
                if "=" in p:
                    k, v = p.strip().split("=", 1)
                    cookies[k] = v
            if cookies:
                return cookies
        except Exception as e:
            logger.error(f"[!] Error parsing EZPROXY_COOKIE header string: {e}")

    # Fallback to local ezproxy_cookies.json file
    if os.path.exists(COOKIES_FILE_PATH):
        try:
            with open(COOKIES_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    for cookie in data:
                        if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                            cookies[cookie["name"]] = cookie["value"]
                elif isinstance(data, dict):
                    cookies = data
                    
            return cookies
        except Exception as e:
            logger.error(f"[!] Error loading cookies from {COOKIES_FILE_PATH}: {e}")

    return cookies


def check_auth_status(valves=None) -> dict:
    """
    Checks if EZproxy authentication cookies exist.
    """
    cookies = load_ezproxy_cookies(valves)
    if not cookies:
        return {
            "authenticated": False,
            "cookie_count": 0,
            "message": "Cookies missing"
        }
    return {
        "authenticated": True,
        "cookie_count": len(cookies),
        "message": f"Loaded {len(cookies)} EZproxy cookies"
    }


def prompt_auth_instructions_if_needed(valves=None):
    """
    Checks EZproxy authentication at pipeline startup.
    Prints clear instructions if cookies are missing.
    """
    auth_status = check_auth_status(valves)
    
    logger.info("==================================================")
    logger.info("🔐 EZPROXY / IEEE XPLORE AUTHENTICATION CHECK")
    logger.info("==================================================")
    
    if auth_status["authenticated"]:
        logger.info(f"✅ Auth status: OK ({auth_status['cookie_count']} cookies loaded)\n")
        return True
    
    banner = (
        "⚠️ WARNING: Session file 'ezproxy_cookies.json' NOT FOUND!\n\n"
        "The pipeline will search metadata and abstracts, but CANNOT\n"
        "automatically download full-text PDFs without active session cookies.\n\n"
        "👉 HOW TO AUTHENTICATE (One-time setup):\n"
        "----------------------------------------------------------------------\n"
        "Run terminal SSO login command:\n"
        "  python3 src/utils/sso_login.py\n"
        "----------------------------------------------------------------------\n"
    )
    logger.warning(banner)
    return False


def get_authenticated_session(user_agent: str = None, valves=None):
    """
    Returns a requests.Session pre-configured with EZproxy cookies and proper browser headers.
    """
    import requests
    session = requests.Session()
    
    headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5,he;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    session.headers.update(headers)
    
    cookies = load_ezproxy_cookies(valves)
    for name, value in cookies.items():
        session.cookies.set(name, value)
        
    return session
