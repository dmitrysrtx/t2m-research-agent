import os
import sys
import json
import requests
from dotenv import load_dotenv
from src.utils.logger import logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIES_FILE_PATH = os.path.join(PROJECT_ROOT, "ezproxy_cookies.json")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def set_host_permissions(target_path: str) -> None:
    """Applies host user ownership and standard file permissions."""
    try:
        st = os.stat(PROJECT_ROOT)
        os.chown(target_path, st.st_uid, st.st_gid)
    except Exception:
        pass
    try:
        os.chmod(target_path, 0o666)
    except Exception:
        pass


def get_institutional_credentials(valves=None) -> dict:
    """Retrieves institutional credentials following Precedence Cascade."""
    inst = getattr(valves, "IEEE_INSTITUTION", None) or os.getenv("IEEE_INSTITUTION", "afeka")
    user = getattr(valves, "IEEE_USERNAME", None) or os.getenv("IEEE_USERNAME", "")
    pwd = getattr(valves, "IEEE_PASSWORD", None) or os.getenv("IEEE_PASSWORD", "")
    return {"institution": str(inst).strip(), "username": str(user).strip(), "password": str(pwd).strip()}


def convert_to_ezproxy_url(url: str, ezproxy_domain: str = None) -> str:
    """Preserves direct IEEE Xplore URLs and ensures stampPDF endpoint for binary download."""
    if not url:
        return url
    if "ieeexplore.ieee.org" in url and "/stamp/stamp.jsp" in url:
        return url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
    return url


def load_ezproxy_cookies(valves=None, cookie_override: str = None) -> dict:
    """Loads EZproxy/IEEE authentication cookies from parameter, Valves, .env, or disk."""
    cookies = {}
    env_cookie = None

    if cookie_override and cookie_override.strip():
        env_cookie = cookie_override.strip()
    elif valves and hasattr(valves, "EZPROXY_COOKIE") and valves.EZPROXY_COOKIE.strip():
        env_cookie = valves.EZPROXY_COOKIE.strip()
    else:
        env_cookie = os.getenv("EZPROXY_COOKIE")

    if env_cookie and env_cookie.strip():
        cookie_str = env_cookie.strip()
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
    """Checks whether EZproxy authentication cookies exist locally."""
    cookies = load_ezproxy_cookies(valves, cookie_override=cookie_override)
    if not cookies:
        return {"authenticated": False, "cookie_count": 0, "message": "Cookies missing"}
    return {"authenticated": True, "cookie_count": len(cookies), "message": f"Loaded {len(cookies)} EZproxy cookies"}


def verify_live_ieee_access(session=None, valves=None, cookie_override: str = None, timeout: int = 6) -> tuple:
    """
    Performs a fast live probe to IEEE Xplore using session cookies.
    Returns (True, msg) on success, (False, reason) on failure.
    """
    cookies = load_ezproxy_cookies(valves=valves, cookie_override=cookie_override)
    if not cookies:
        return False, "Session cookies not found (ezproxy_cookies.json is missing or empty)."

    cookie_keys = set(cookies.keys())
    if cookie_keys and any(k in cookie_keys for k in ["MRHSession", "LastMRH_Session"]):
        try:
            f5_s = requests.Session()
            f5_s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
            for k, v in cookies.items():
                f5_s.cookies.set(k, v)
            chk = f5_s.get("https://sso.afeka.ac.il/my.policy", verify=False, timeout=timeout, allow_redirects=False)
            if chk.status_code in (301, 302, 303, 307) or "logout" in chk.text.lower() or "webtop" in chk.text.lower() or "vdesk" in chk.url:
                return True, "Afeka institutional SSO session confirmed active."
            return False, "Afeka institutional SSO session expired. Needs 2FA renewal."
        except Exception as e:
            return False, f"Afeka SSO connection error: {e}"

    if session is None:
        from src.auth.ezproxy_session import get_authenticated_session
        session = get_authenticated_session(valves=valves, cookie_override=cookie_override)

    probe_url = "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=6811462"
    try:
        # Check initial response first (fast fail if redirected to login)
        resp = session.get(probe_url, stream=True, timeout=timeout, allow_redirects=False)

        has_erights = any("erights" in k.lower() for k in cookie_keys)
        erights_hint = "" if has_erights else f" (ezproxy_cookies.json has {len(cookies)} cookies, but missing institutional token 'ERIGHTS')"

        if resp.status_code in (301, 302, 303, 307):
            loc = resp.headers.get("Location", "").lower()
            if any(k in loc for k in ["login", "authdecision", "-203", "wayf", "my.policy", "signin"]):
                return False, f"Session unauthenticated (IEEE redirected to login){erights_hint}."
            # Follow legitimate redirect (e.g. to PDF CDN)
            resp = session.get(resp.headers["Location"], stream=True, timeout=timeout, allow_redirects=True)

        content_type = resp.headers.get("Content-Type", "").lower()
        chunk = next(resp.iter_content(128), b"")

        # True authenticated response returns 200 and binary PDF stream
        if resp.status_code == 200 and (chunk.startswith(b"%PDF") or ("pdf" in content_type and b"<html" not in chunk.lower())):
            return True, "Full-text PDF access to IEEE Xplore confirmed."

        # Detect HTML login / auth walls
        if "login" in resp.url.lower() or "authdecision" in resp.url.lower() or "html" in content_type or b"<html" in chunk.lower():
            return False, f"Session unauthenticated (IEEE served login page){erights_hint}."

        if resp.status_code in (401, 403):
            return False, f"HTTP {resp.status_code}: Access denied by institutional firewall."

        return False, f"Unexpected response status from IEEE server: HTTP {resp.status_code}."
    except requests.exceptions.Timeout:
        return False, "Request timed out while connecting to IEEE Xplore."
    except requests.exceptions.RequestException as e:
        return False, f"Network connection error to IEEE: {str(e)[:80]}."


def prompt_auth_instructions_if_needed(valves=None) -> bool:
    """Checks EZproxy authentication at pipeline startup and logs guidance if missing."""
    auth_status = check_auth_status(valves)
    logger.info("==================================================")
    logger.info("🔐 EZPROXY / IEEE XPLORE AUTHENTICATION CHECK")
    logger.info("==================================================")
    if auth_status["authenticated"]:
        logger.info(f"[*] Local cookies: {auth_status['cookie_count']} loaded.")
        return True
    logger.warning(
        "⚠️ WARNING: Session file 'ezproxy_cookies.json' NOT FOUND!\n"
        "Run terminal SSO login command:\n"
        "  python3 -m src.auth.ezproxy_session\n"
    )
    return False


if __name__ == "__main__":
    print("==================================================")
    print("🔍 LIVE IEEE / EZPROXY AUTHENTICATION HEALTH-CHECK")
    print("==================================================")
    status = check_auth_status()
    print(f"[*] Local cookies found: {status['cookie_count']}")
    print("[*] Probing IEEE Xplore live endpoint...")
    is_valid, reason = verify_live_ieee_access()
    print(f"[{'✅ SUCCESS' if is_valid else '❌ FAILED'}]: {reason}")
    print("==================================================")
    sys.exit(0 if is_valid else 1)
