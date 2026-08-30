import os
import json
from playwright.sync_api import sync_playwright
from src.utils.logger import logger
from src.utils.ezproxy_auth import COOKIES_FILE_PATH

def generate_ezproxy_session(target_url="https://ieeexplore-ieee-org.ezproxy.afeka.ac.il", headless=False):
    """
    Launches a Playwright browser session for institutional authentication (Afeka EZproxy).
    Exports cookies to 'ezproxy_cookies.json' in the project root.
    """
    logger.info("==================================================")
    logger.info("🔐 Playwright EZproxy Session Manager")
    logger.info("==================================================")
    logger.info(f"[*] Opening browser to target: {target_url}")
    logger.info("[*] Please complete the login/2FA in the browser window if prompted.")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(target_url, wait_until="networkidle")
            
            logger.info("[*] Page loaded. Extracting authenticated session cookies...")
            cookies = context.cookies()
            
            with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
                
            logger.info(f"✅ Saved {len(cookies)} cookies to: {COOKIES_FILE_PATH}")
            browser.close()
            return True
    except Exception as e:
        logger.error(f"[!] Playwright session initialization error: {e}")
        return False

if __name__ == "__main__":
    generate_ezproxy_session()
