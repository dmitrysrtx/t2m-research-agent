"""
Afeka College SSO and Institutional Authentication Wrapper.
Provides backwards-compatible interface for browser-driven SAML/2FA authentication.
"""

import sys
from src.auth.sso_login import login_afeka_sso


def run_browser_auth_flow(
    username: str = None,
    password: str = None,
    headless: bool = True,
    status_callback: callable = None,
    approval_timeout: int = 120,
) -> tuple:
    """
    Automates IEEE Xplore Institutional Login via Afeka College SSO with 2FA Push.
    Delegates to the unified login_afeka_sso workflow.
    """
    return login_afeka_sso(
        username=username,
        password=password,
        status_callback=status_callback,
        interactive_fallback=False,
        approval_timeout=approval_timeout,
    )


if __name__ == "__main__":
    ok, message = run_browser_auth_flow(status_callback=lambda m: print(f"[*] {m}"))
    print(f"\nResult: {'SUCCESS' if ok else 'FAILED'}\n{message}")
    sys.exit(0 if ok else 1)
