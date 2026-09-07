import os
import sys
import json
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
from src.utils.logger import logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIES_FILE_PATH = os.path.join(PROJECT_ROOT, "ezproxy_cookies.json")
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

TRACKER_PREFIXES = (
    "_ga", "_gid", "_gat", "_gcl", "_tt", "li_", "bcookie", "lidc",
    "taboola", "demdex", "UserMatch", "CLID", "com.adobe", "kndctr",
    "_fbp", "_uetsid", "_uetvid", "hum_ieee", "_cl", "ttcsid",
)


def _is_clean_cookie(name: str, value: str = "") -> bool:
    """Filters trackers, AWS deletion markers, and ephemeral 30s TS cookies."""
    if any(name.startswith(p) for p in TRACKER_PREFIXES):
        return False
    if name.startswith("TSaf") or value == "_remove_":
        return False
    return bool(name and value)


def set_host_permissions(target_path: str) -> None:
    """Applies host user ownership and standard file/directory permissions."""
    try:
        st = os.stat(PROJECT_ROOT)
        os.chown(target_path, st.st_uid, st.st_gid)
    except Exception:
        pass
    try:
        mode = 0o777 if os.path.isdir(target_path) else 0o666
        os.chmod(target_path, mode)
    except Exception:
        pass


def save_ezproxy_cookies(cookies_dict: dict) -> bool:
    """Sanitizes and saves session cookies to disk with host permissions."""
    clean = {k: v for k, v in cookies_dict.items() if _is_clean_cookie(str(k), str(v))}
    if not clean:
        return False
    try:
        with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)
        set_host_permissions(COOKIES_FILE_PATH)
        return True
    except Exception as e:
        logger.error(f"[!] Failed to save cookies to {COOKIES_FILE_PATH}: {e}")
        return False


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
    """Loads and sanitizes session cookies from disk or explicit valid overrides."""
    file_cookies = {}
    if os.path.exists(COOKIES_FILE_PATH):
        try:
            with open(COOKIES_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for c in data:
                        if isinstance(c, dict) and _is_clean_cookie(c.get("name", ""), c.get("value", "")):
                            file_cookies[c["name"]] = c["value"]
                elif isinstance(data, dict):
                    file_cookies = {k: v for k, v in data.items() if _is_clean_cookie(str(k), str(v))}
        except Exception as e:
            logger.error(f"[!] Error loading cookies from {COOKIES_FILE_PATH}: {e}")

    # Check if explicit override contains active institutional token
    cookie_str = (cookie_override or "").strip()
    if cookie_str and "erights" in cookie_str.lower():
        override_cookies = {}
        try:
            parsed = json.loads(cookie_str)
            if isinstance(parsed, dict):
                override_cookies = {k: v for k, v in parsed.items() if _is_clean_cookie(str(k), str(v))}
        except Exception:
            for pair in cookie_str.split(";"):
                if "=" in pair:
                    k, v = pair.strip().split("=", 1)
                    if _is_clean_cookie(k, v):
                        override_cookies[k] = v
        if any("erights" in k.lower() for k in override_cookies):
            return override_cookies

    return file_cookies


def check_auth_status(valves=None, cookie_override: str = None) -> dict:
    """Checks whether EZproxy authentication cookies exist locally."""
    cookies = load_ezproxy_cookies(valves, cookie_override=cookie_override)
    if not cookies or not any("erights" in k.lower() for k in cookies):
        return {"authenticated": False, "cookie_count": len(cookies), "message": "Institutional token missing"}
    return {"authenticated": True, "cookie_count": len(cookies), "message": f"Loaded {len(cookies)} cookies"}


def verify_live_ieee_access(session=None, valves=None, cookie_override: str = None, timeout: int = 15) -> tuple:
    """Performs resilient live probe to IEEE Xplore using session cookies."""
    cookies = load_ezproxy_cookies(valves=valves, cookie_override=cookie_override)
    if not cookies or not any("erights" in k.lower() for k in cookies):
        return False, "IEEE institutional session token 'ERIGHTS' is missing. Institutional login required."

    if session is None:
        from src.auth.ezproxy_session import get_authenticated_session
        session = get_authenticated_session(valves=valves, cookie_override=cookie_override)

    probe_url = "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=6811462"
    try:
        resp = session.get(probe_url, stream=True, timeout=timeout, allow_redirects=False)

        if resp.status_code in (301, 302, 303, 307):
            loc = resp.headers.get("Location", "")
            if any(k in loc.lower() for k in ["login", "authdecision", "-203", "wayf", "my.policy", "signin"]):
                return False, "Session unauthenticated (IEEE redirected to institutional login)."
            full_loc = urljoin("https://ieeexplore.ieee.org", loc)
            resp = session.get(full_loc, stream=True, timeout=timeout, allow_redirects=True)

        content_type = resp.headers.get("Content-Type", "").lower()
        chunk = next(resp.iter_content(128), b"")

        if resp.status_code == 200 and (chunk.startswith(b"%PDF") or ("pdf" in content_type and b"<html" not in chunk.lower())):
            # Sync fresh session cookies returned by IEEE
            if resp.cookies:
                new_cookies = dict(cookies)
                for c in resp.cookies:
                    if _is_clean_cookie(c.name, c.value):
                        new_cookies[c.name] = c.value
                save_ezproxy_cookies(new_cookies)
            return True, "Full-text PDF access to IEEE Xplore confirmed."

        if "login" in resp.url.lower() or "authdecision" in resp.url.lower() or "html" in content_type:
            return False, "Session unauthenticated (IEEE served login page; institutional session expired)."

        if resp.status_code in (401, 403):
            return False, f"HTTP {resp.status_code}: Access denied by institutional firewall."
        return False, f"Unexpected response status from IEEE server: HTTP {resp.status_code}."
    except requests.exceptions.Timeout:
        return False, "Request timed out while connecting to IEEE Xplore (15s)."
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
    logger.warning("⚠️ Session token missing. Run: python3 -m src.auth.sso_login")
    return False


if __name__ == "__main__":
    print("==================================================")
    print("🔍 LIVE IEEE / EZPROXY AUTHENTICATION HEALTH-CHECK")
    print("==================================================")
    status = check_auth_status()
    print(f"[*] Local cookies found: {status['cookie_count']} ({status['message']})")
    print("[*] Probing IEEE Xplore live endpoint...")
    is_valid, reason = verify_live_ieee_access()
    print(f"[{'✅ SUCCESS' if is_valid else '❌ FAILED'}]: {reason}")
    print("==================================================")
    sys.exit(0 if is_valid else 1)
