import sys
import argparse
from src.auth.afeka_sso import run_browser_auth_flow

# Backward-compatible alias
login_ieee_via_afeka_browser = run_browser_auth_flow

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated IEEE Institutional Login via Afeka Playwright")
    parser.add_argument("--username", type=str, help="Afeka username/email")
    parser.add_argument("--password", type=str, help="Afeka password")
    args = parser.parse_args()

    ok, msg = login_ieee_via_afeka_browser(username=args.username, password=args.password)
    print(f"Result: {'SUCCESS' if ok else 'FAILED'}")
    print(msg)
    sys.exit(0 if ok else 1)
