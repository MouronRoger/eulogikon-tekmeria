#!/usr/bin/env python3
"""Unlock/lock the ``.eukoine/`` locked artefacts (EKDP-032) for a spec write session.

Runnable from every repo. The tool always acts on the *resolved hub* (see
``naming/_manifest.hub_root``): whether invoked inside the hub or inside a synced
member, unlock/lock/status target the hub's canonical ``.eukoine/`` artefacts and
read the authorization phrase from the hub's ``.env``. There is one canonical source;
any family repo may drive the unlock/sync/relock cycle against it.

The authorization phrase lives in the hub repo-root ``.env`` as ``EUKOINE_SPEC_AUTHORIZE``
(gitignored; listed in ``.cursorignore``). Opening a session lets the canonical
guard (``--role canonical``) admit ``.eukoine/`` edits; authoring is open-ended, so
the session stamp is existence-based. Mirror pushes commit with ``--no-verify``
after hub hash verification (``naming/sync.py``); member hooks do not gate hub
propagation.

Locked artefacts are read from ``naming/sync_manifest.toml`` (``locked = true``).

Usage::

    python scripts/eukoine_spec_lock.py unlock --from-env   # phrase already in .env
    python scripts/eukoine_spec_lock.py unlock "your-phrase"
    python scripts/eukoine_spec_lock.py lock
    python scripts/eukoine_spec_lock.py status

Exit codes: 0 success, 1 refusal / chflags failure / usage error.
"""

from __future__ import annotations

import argparse
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "naming"))
import _manifest  # noqa: E402

_HUB_ROOT = _manifest.hub_root()
_SESSION_PATH = _HUB_ROOT / ".eukoine" / ".write_session"
_ENV_PATH = _HUB_ROOT / ".env"
_ENV_KEY = "EUKOINE_SPEC_AUTHORIZE"


def _locked_paths() -> list[Path]:
    return [_HUB_ROOT / p for p in _manifest.load().locked_paths()]


def _load_env_key(env_path: Path, key: str) -> str | None:
    if not env_path.is_file():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or not line.startswith(f"{key}="):
            continue
        value = line.split("=", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        return value
    return None


def _phrase_authorized(supplied: str) -> bool:
    expected = _load_env_key(_ENV_PATH, _ENV_KEY)
    if not expected:
        print(f"REFUSED: set {_ENV_KEY} in {_ENV_PATH} (see .env.example).", file=sys.stderr)
        return False
    if not secrets.compare_digest(supplied, expected):
        print("REFUSED: authorization phrase does not match.", file=sys.stderr)
        return False
    return True


def _darwin() -> bool:
    return sys.platform == "darwin"


def _chflags(flag: str, path: Path) -> bool:
    """True on success; prints and returns False on failure — never silent (EKDP-021)."""
    result = subprocess.run(
        ["chflags", flag, str(path)], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: chflags {flag} failed for {path}: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def _set_immutable(*, lock: bool) -> bool:
    if not _darwin():
        print("WARN: not macOS — skipping chflags (session stamp only).", file=sys.stderr)
        return True
    flag = "uchg" if lock else "nouchg"
    ok = True
    for path in _locked_paths():
        if not path.is_file():
            print(f"WARN: locked artefact missing: {path}", file=sys.stderr)
            continue
        ok = _chflags(flag, path) and ok
    return ok


def cmd_status() -> int:
    print(f"hub: {_HUB_ROOT}")
    paths = _locked_paths()
    print(f"locked artefacts ({len(paths)}):")
    for path in paths:
        flags = "-"
        if _darwin() and path.is_file():
            result = subprocess.run(
                ["stat", "-f", "%Sf", str(path)], check=False, capture_output=True, text=True
            )
            flags = result.stdout.strip() or "-"
        state = "OK" if path.is_file() else "MISSING"
        print(f"  {state:8} {flags:10} {path.relative_to(_HUB_ROOT)}")
    print(f"write session: {'active' if _SESSION_PATH.is_file() else 'none'}")
    return 0


def cmd_unlock(phrase: str) -> int:
    if not _phrase_authorized(phrase):
        return 1
    ok = _set_immutable(lock=False)
    stamp = f"unlocked_at={datetime.now(timezone.utc).isoformat()}\nby=sync-agent\n"
    _SESSION_PATH.write_text(stamp, encoding="utf-8")
    print("UNLOCKED: .eukoine/ locked artefacts (write session open — run lock when done)")
    return 0 if ok else 1


def cmd_lock() -> int:
    if _SESSION_PATH.is_file():
        _SESSION_PATH.unlink()
    ok = _set_immutable(lock=True)
    print("LOCKED: .eukoine/ locked artefacts" if ok else "LOCKED WITH ERRORS (see above)")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="EKDP-032 unlock/lock for .eukoine/")
    sub = parser.add_subparsers(dest="command", required=True)
    unlock = sub.add_parser("unlock", help="authorize and open a write session")
    unlock.add_argument("phrase", nargs="?", help="authorization phrase (omit with --from-env)")
    unlock.add_argument("--from-env", action="store_true", help=f"read phrase from {_ENV_KEY} in .env")
    sub.add_parser("lock", help="close write session and re-lock the artefacts")
    sub.add_parser("status", help="show lock and session state")
    args = parser.parse_args()

    if args.command == "status":
        return cmd_status()
    if args.command == "lock":
        return cmd_lock()
    if args.command == "unlock":
        if args.from_env:
            phrase = _load_env_key(_ENV_PATH, _ENV_KEY)
            if not phrase:
                print(f"REFUSED: --from-env requires {_ENV_KEY} in {_ENV_PATH}", file=sys.stderr)
                return 1
        elif args.phrase:
            phrase = args.phrase
        else:
            print("REFUSED: supply a phrase or use --from-env.", file=sys.stderr)
            return 1
        return cmd_unlock(phrase)
    return 1


if __name__ == "__main__":
    sys.exit(main())
