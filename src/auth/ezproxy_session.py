import os
import sys
import requests
from src.utils.logger import logger
from src.auth.ezproxy_auth import (
    load_ezproxy_cookies,
    save_ezproxy_cookies,
    check_auth_status,
    verify_live_ieee_access,
    _is_clean_cookie,
)


class EZProxyManager:
    """
    Unified Institutional Session & EZproxy Manager.
    - Validates ezproxy_cookies.json on demand.
    - Silent / 2FA automated SAML renewal via Afeka SSO.
    - Produces fully-configured requests.Session objects with automatic disk synchronization.
    """

    def __init__(self, valves=None, cookie_override: str = None):
        self.valves = valves
        self.cookie_override = cookie_override
        self._cached_session = None

    def check_status(self) -> dict:
        """Returns local cookie file status."""
        return check_auth_status(self.valves, self.cookie_override)

    def is_authenticated(self, timeout: int = 15) -> tuple:
        """Runs live health check against IEEE Xplore."""
        session = self.get_session(auto_login=False)
        return verify_live_ieee_access(
            session=session,
            valves=self.valves,
            cookie_override=self.cookie_override,
            timeout=timeout,
        )

    def refresh_session(self, status_callback: callable = None, headless: bool = True) -> tuple:
        """Triggers persistent-context SAML renewal (silent or mobile push)."""
        from src.auth.sso_login import login_afeka_sso

        logger.info("[*] EZProxyManager: Initiating institutional session renewal...")
        if status_callback:
            status_callback("🔐 EZProxyManager: Initiating institutional session renewal...")

        ok, msg = login_afeka_sso(
            status_callback=status_callback,
            interactive_fallback=False,
        )
        if ok:
            self._cached_session = None  # Invalidate cached session to pick up new tokens
        return ok, msg

    def ensure_valid_session(self, auto_login: bool = True, status_callback: callable = None) -> tuple:
        """Validates active session. If invalid, triggers renewal."""
        is_valid, reason = self.is_authenticated()
        if is_valid:
            return True, reason

        if not auto_login:
            return False, reason

        logger.warning(f"[*] Active session invalid ({reason}). Attempting renewal...")
        login_ok, login_msg = self.refresh_session(status_callback=status_callback)
        if not login_ok:
            return False, f"Session renewal failed: {login_msg}"

        return self.is_authenticated()

    def sync_session_cookies_to_disk(self) -> bool:
        """Synchronizes live session cookies from requests.Session back to ezproxy_cookies.json."""
        if not self._cached_session:
            return False
        try:
            current_cookies = load_ezproxy_cookies(self.valves, self.cookie_override)
            for cookie in self._cached_session.cookies:
                if _is_clean_cookie(cookie.name, cookie.value):
                    current_cookies[cookie.name] = cookie.value
            return save_ezproxy_cookies(current_cookies)
        except Exception as e:
            logger.warning(f"Failed to sync session cookies to disk: {e}")
            return False

    def get_session(
        self,
        auto_login: bool = False,
        status_callback: callable = None,
        force_refresh: bool = False,
    ) -> requests.Session:
        """Returns a pre-configured requests.Session with proper domain-bound institutional cookies."""
        if force_refresh or self._cached_session is None:
            if auto_login:
                self.ensure_valid_session(auto_login=True, status_callback=status_callback)

            session = requests.Session()
            session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/pdf,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5,he;q=0.3",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })

            cookies = load_ezproxy_cookies(self.valves, self.cookie_override)
            for name, value in cookies.items():
                if name in {"MRHSession", "LastMRH_Session", "F5_ST", "TS01df1230"}:
                    session.cookies.set(name, value, domain=".afeka.ac.il", path="/")
                elif name in {"oaxsrftkn", "oaloginorg", "oatmpsid", "oalastorg"}:
                    session.cookies.set(name, value, domain=".openathens.net", path="/")
                else:
                    session.cookies.set(name, value, domain=".ieee.org", path="/")

            self._cached_session = session

        return self._cached_session


def get_authenticated_session(user_agent: str = None, valves=None, cookie_override: str = None) -> requests.Session:
    """Convenience helper to retrieve an authenticated requests.Session."""
    manager = EZProxyManager(valves=valves, cookie_override=cookie_override)
    session = manager.get_session(auto_login=False)
    if user_agent:
        session.headers["User-Agent"] = user_agent
    return session


if __name__ == "__main__":
    print("==================================================")
    print("🔐 EZProxyManager Standalone Diagnostic")
    print("==================================================")
    manager = EZProxyManager()
    status = manager.check_status()
    print(f"[*] Cookie status: {status['message']} (Count: {status['cookie_count']})")
    print("[*] Probing live IEEE institutional access...")
    is_authed, reason = manager.is_authenticated()
    print(f"[*] Live Access: {'✅ VALID' if is_authed else '❌ INVALID'}")
    print(f"[*] Probe Note: {reason}")
    if is_authed:
        sync_ok = manager.sync_session_cookies_to_disk()
        print(f"[*] Session sync to disk: {'✅ OK' if sync_ok else '❌ SKIPPED'}")
    print("==================================================")
    sys.exit(0 if is_authed else 1)
