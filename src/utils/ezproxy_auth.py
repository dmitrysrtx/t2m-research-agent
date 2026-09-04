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


def load_ezproxy_cookies(valves=None, cookie_override: str = None) -> dict:
    """
    Loads EZproxy / IEEE authentication cookies from:
    1. Direct parameter override (cookie_override)
    2. OpenWebUI Valves (EZPROXY_COOKIE override)
    3. EZPROXY_COOKIE environment variable (.env)
    4. ezproxy_cookies.json file in project root.
    """
    cookies = {}

    # Check parameter override or Valves
    env_cookie = None
    if cookie_override and cookie_override.strip():
        env_cookie = cookie_override.strip()
    elif valves and hasattr(valves, "EZPROXY_COOKIE") and valves.EZPROXY_COOKIE.strip():
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


def check_auth_status(valves=None, cookie_override: str = None) -> dict:
    """
    Checks if EZproxy authentication cookies exist locally.
    """
    cookies = load_ezproxy_cookies(valves, cookie_override=cookie_override)
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


def verify_live_ieee_access(session=None, valves=None, cookie_override: str = None, timeout: int = 6) -> tuple:
    """
    Performs a fast live probe (1-2s) to IEEE Xplore using the current authenticated session.
    Checks whether full-text access is granted without downloading an entire file.
    
    Returns:
        (True, "OK: Valid institutional access verified.") if access is confirmed.
        (False, reason_description) if missing, expired, or blocked.
    """
    import requests
    cookies = load_ezproxy_cookies(valves=valves, cookie_override=cookie_override)
    if not cookies:
        return False, "Session cookies not found (ezproxy_cookies.json is missing or empty)."

    if session is None:
        session = get_authenticated_session(valves=valves, cookie_override=cookie_override)

    # Standard small IEEE paper PDF endpoint to test institutional entitlement
    probe_url = "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=6811462"
    
    try:
        resp = session.get(probe_url, stream=True, timeout=timeout, allow_redirects=False)
        
        # 1. 301/302 Redirect to login page
        if resp.status_code in (301, 302, 303, 307):
            loc = resp.headers.get("Location", "")
            if "login" in loc.lower() or "authdecision" in loc.lower() or "-203" in loc:
                return False, "Session expired or unauthenticated (IEEE redirected to login authDecision=-203)."
            return False, f"Redirected to authentication page: {loc[:60]}..."

        # 2. 401 / 403 Forbidden
        if resp.status_code in (401, 403):
            return False, f"HTTP {resp.status_code}: Access denied by institutional firewall."

        # 3. HTTP 200 OK -> Check if it's really binary PDF or an HTML login page
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "").lower()
            if "pdf" in content_type:
                return True, "Full-text PDF access to IEEE Xplore confirmed."
                
            # Read first 128 bytes to check for %PDF magic bytes
            chunk = next(resp.iter_content(128), b"")
            if chunk.startswith(b"%PDF"):
                return True, "Full-text PDF access to IEEE Xplore confirmed."
                
            if "html" in content_type or b"<html" in chunk.lower():
                return False, "Received HTML login page instead of PDF binary stream."

        return False, f"Unexpected response status from IEEE server: HTTP {resp.status_code}."
        
    except requests.exceptions.Timeout:
        return False, "Request timed out while connecting to IEEE Xplore."
    except requests.exceptions.RequestException as e:
        return False, f"Network connection error to IEEE: {str(e)[:80]}."


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
        logger.info(f"[*] Local cookies: {auth_status['cookie_count']} loaded.")
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


def get_authenticated_session(user_agent: str = None, valves=None, cookie_override: str = None):
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
    
    cookies = load_ezproxy_cookies(valves, cookie_override=cookie_override)
    for name, value in cookies.items():
        session.cookies.set(name, value)
        
    return session


if __name__ == "__main__":
    print("==================================================")
    print("🔍 LIVE IEEE / EZPROXY AUTHENTICATION HEALTH-CHECK")
    print("==================================================")
    status = check_auth_status()
    print(f"[*] Local cookies found: {status['cookie_count']}")
    
    print("[*] Probing IEEE Xplore live endpoint...")
    is_valid, reason = verify_live_ieee_access()
    if is_valid:
        print(f"✅ SUCCESS: {reason}")
    else:
        print(f"❌ FAILED: {reason}")
    print("==================================================")
