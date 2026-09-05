import os
import sys
import argparse
from dotenv import load_dotenv
from src.utils.logger import logger
from src.auth.afeka_sso import run_browser_auth_flow
from src.auth.ezproxy_auth import PROJECT_ROOT

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def login_afeka_sso(
    username: str = None,
    password: str = None,
    status_callback: callable = None,
    interactive_fallback: bool = True,
) -> tuple:
    """Authenticates institutional access for IEEE Xplore via Afeka College SSO."""
    logger.info("==================================================")
    logger.info("🔐 AFEKA / IEEE INSTITUTIONAL AUTHENTICATOR")
    logger.info("==================================================")

    username = username or os.getenv("IEEE_USERNAME")
    password = password or os.getenv("IEEE_PASSWORD")

    if not username or not username.strip():
        if interactive_fallback:
            username = input("👤 Enter your Afeka username/email: ").strip()
        else:
            msg = "Missing IEEE_USERNAME in environment."
            logger.error(f"[!] {msg}")
            return False, msg

    if not password or not password.strip():
        if interactive_fallback:
            import getpass
            password = getpass.getpass("🔑 Enter your Afeka password: ").strip()
        else:
            msg = "Missing IEEE_PASSWORD in environment."
            logger.error(f"[!] {msg}")
            return False, msg

    return run_browser_auth_flow(
        username=username,
        password=password,
        status_callback=status_callback,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Afeka SSO Authenticator")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    success, message = login_afeka_sso(username=args.username, password=args.password)
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    print(message)
    sys.exit(0 if success else 1)
