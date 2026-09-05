"""
Institutional Authentication and EZproxy Session Management Package.
Strictly isolated layer for institutional SSO login, cookie management, and session verification.
"""

__all__ = [
    "COOKIES_FILE_PATH",
    "convert_to_ezproxy_url",
    "load_ezproxy_cookies",
    "check_auth_status",
    "verify_live_ieee_access",
    "prompt_auth_instructions_if_needed",
    "get_institutional_credentials",
    "EZProxyManager",
    "get_authenticated_session",
    "run_browser_auth_flow",
    "login_afeka_sso",
]


def __getattr__(name: str):
    if name in ("EZProxyManager", "get_authenticated_session"):
        from src.auth.ezproxy_session import EZProxyManager, get_authenticated_session
        return locals()[name]

    if name in (
        "COOKIES_FILE_PATH",
        "convert_to_ezproxy_url",
        "load_ezproxy_cookies",
        "check_auth_status",
        "verify_live_ieee_access",
        "prompt_auth_instructions_if_needed",
        "get_institutional_credentials",
    ):
        import src.auth.ezproxy_auth as ea
        return getattr(ea, name)

    if name == "run_browser_auth_flow":
        from src.auth.afeka_sso import run_browser_auth_flow
        return run_browser_auth_flow

    if name == "login_afeka_sso":
        from src.auth.sso_login import login_afeka_sso
        return login_afeka_sso

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
