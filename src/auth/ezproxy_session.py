import os
import sys
import requests
from src.utils.logger import logger
from src.auth.ezproxy_auth import (
    load_ezproxy_cookies,
    check_auth_status,
    verify_live_ieee_access,
)


class EZProxyManager:
    """
    Unified Institutional Session & EZproxy Manager.
    - Validates ezproxy_cookies.json on demand.
    - Auto-refreshes credentials via Afeka 2FA browser flow if cookies are expired.
    - Produces fully-configured requests.Session objects for fetchers and downloaders.
    """

    def __init__(self, valves=None, cookie_override: str = None):
        self.valves = valves
        self.cookie_override = cookie_override
        self._cached_session = None

    def check_status(self) -> dict:
        """Returns local cookie file status."""
        return check_auth_status(self.valves, self.cookie_override)

    def is_authenticated(self, timeout: int = 6) -> tuple:
        """Runs live health check against IEEE Xplore."""
        return verify_live_ieee_access(
            session=self._cached_session,
            valves=self.valves,
            cookie_override=self.cookie_override,
            timeout=timeout,
        )

    def refresh_session(self, status_callback: callable = None, headless: bool = True) -> tuple:
        """Triggers browser 2FA flow to refresh credentials."""
        from src.auth.afeka_sso import run_browser_auth_flow

        logger.info("[*] EZProxyManager: Initiating automated browser 2FA login...")
        if status_callback:
            status_callback("🔐 EZProxyManager: Initiating automated browser 2FA login...")

        ok, msg = run_browser_auth_flow(
            headless=headless,
            status_callback=status_callback,
        )
        if ok:
            self._cached_session = None  # Invalidate cached session
        return ok, msg

    def ensure_valid_session(self, auto_login: bool = True, status_callback: callable = None) -> tuple:
        """
        Validates the active session. If invalid and auto_login is True,
        triggers the 2FA flow and verifies again.
        """
        is_valid, reason = self.is_authenticated()
        if is_valid:
            return True, reason

        if not auto_login:
            return False, reason

        logger.warning(f"[*] Active session invalid ({reason}). Attempting 2FA auto-login...")
        login_ok, login_msg = self.refresh_session(status_callback=status_callback)
        if not login_ok:
            return False, f"Auto-login failed: {login_msg}"

        return self.is_authenticated()

    def get_session(
        self,
        auto_login: bool = False,
        status_callback: callable = None,
        force_refresh: bool = False,
    ) -> requests.Session:
        """Returns a pre-configured requests.Session with headers and institutional cookies."""
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
                "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5,he;q=0.3",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })

            cookies = load_ezproxy_cookies(self.valves, self.cookie_override)
            for name, value in cookies.items():
                session.cookies.set(name, value, domain=".ieee.org", path="/")
                session.cookies.set(name, value, domain="ieeexplore.ieee.org", path="/")
                session.cookies.set(name, value)

            if cookies:
                session.headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())

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

    sess = manager.get_session()
    cookie_header_len = len(sess.headers.get("Cookie", ""))
    print(f"[*] Prepared Session Header length: {cookie_header_len} chars")
    print("==================================================")
    sys.exit(0 if is_authed else 1)
