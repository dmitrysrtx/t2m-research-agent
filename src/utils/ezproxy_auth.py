import os
import json
from src.utils.logger import logger

COOKIES_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ezproxy_cookies.json")

def convert_to_ezproxy_url(url: str, ezproxy_domain: str = "ezproxy.afeka.ac.il") -> str:
    """
    Converts a standard IEEE Xplore URL into an institutional EZproxy URL.
    Supports domain-rewriting style (e.g. ieeexplore-ieee-org.ezproxy.afeka.ac.il)
    and prefix style (e.g. https://ezproxy.afeka.ac.il/login?url=...).
    """
    if not url:
        return url
        
    if "ezproxy" in url:
        return url  # Already an EZproxy URL

    # Handle IEEE Stamp / PDF URLs
    if "ieeexplore.ieee.org" in url:
        # Convert domain rewriting: ieeexplore.ieee.org -> ieeexplore-ieee-org.ezproxy.afeka.ac.il
        rewritten_domain = f"ieeexplore-ieee-org.{ezproxy_domain}"
        ez_url = url.replace("ieeexplore.ieee.org", rewritten_domain)
        
        # Ensure stampPDF endpoint for direct binary PDF download if it's stamp.jsp
        if "/stamp/stamp.jsp" in ez_url:
            ez_url = ez_url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
            
        return ez_url
        
    # Generic fallback prefix style
    return f"https://{ezproxy_domain}/login?url={url}"


def load_ezproxy_cookies() -> dict:
    """
    Loads EZproxy / IEEE authentication cookies from:
    1. ezproxy_cookies.json file in project root.
    2. EZPROXY_COOKIE environment variable.
    """
    cookies = {}
    
    # 1. Try loading from ezproxy_cookies.json
    if os.path.exists(COOKIES_FILE_PATH):
        try:
            with open(COOKIES_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Check if it's exported in standard cookie JSON format (array of dicts)
                if isinstance(data, list):
                    for cookie in data:
                        if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                            cookies[cookie["name"]] = cookie["value"]
                elif isinstance(data, dict):
                    cookies = data
                    
            logger.info(f"[*] Loaded {len(cookies)} EZproxy cookies from {os.path.basename(COOKIES_FILE_PATH)}")
            return cookies
        except Exception as e:
            logger.error(f"[!] Error loading cookies from {COOKIES_FILE_PATH}: {e}")

    # 2. Try loading from environment variable
    env_cookie = os.getenv("EZPROXY_COOKIE")
    if env_cookie:
        try:
            # Parse Cookie header string ("key1=val1; key2=val2")
            pairs = env_cookie.split(";")
            for p in pairs:
                if "=" in p:
                    k, v = p.strip().split("=", 1)
                    cookies[k] = v
            logger.info(f"[*] Loaded {len(cookies)} cookies from EZPROXY_COOKIE environment variable.")
        except Exception as e:
            logger.error(f"[!] Error parsing EZPROXY_COOKIE env variable: {e}")

    if not cookies:
        logger.warning(" [!] No EZproxy cookies found! Place 'ezproxy_cookies.json' in project root or set EZPROXY_COOKIE in .env.")

    return cookies


def get_authenticated_session(user_agent: str = None):
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
    
    cookies = load_ezproxy_cookies()
    for name, value in cookies.items():
        session.cookies.set(name, value)
        
    return session
