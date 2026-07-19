#!/usr/bin/env python3
"""Pre-commit guard: a .eukoine/ change may be committed only when an open write
session authorises it (EKDP-032).

- ``--role canonical`` (EuKoine): the owner opens a session with
  ``scripts/eukoine_spec_lock.py unlock`` (phrase-gated). Authoring is open-ended —
  the post-edit bytes are not known when the session opens — so any open session
  authorises the edit.
- ``--role mirror`` (eulogikon, EuGraphikon): a ``.eukoine/`` commit is allowed only when an open session
  authorises the **exact staged bytes** — every staged ``.eukoine/`` path must hash to the value the
  session records. A hand-edit changes the hash and is rejected; a stale token does not match new bytes.
  The mirror is thus writable only along the sanctioned sync path. ``naming/sync.py`` commits with
  ``--no-verify`` after its own hash verification — member hooks do not gate hub propagation (EKDP-031/032).

Pre-commit is a convention guard, not a cryptographic boundary: ``--no-verify``
bypasses it as it does any hook. Forgery-resistance (a signed token) is a deferred
upgrade (DECISIONS.md). This script is a synchronised enforcement artefact
(naming/sync_manifest.toml) — edit it in the EuKoine hub, never in a mirror.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_EUKOINE_DIR = ".eukoine"
_SESSION_REL = ".eukoine/.write_session"


def _staged_eukoine_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", _EUKOINE_DIR],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        line
        for line in result.stdout.splitlines()
        if line.strip() and line.strip() != _SESSION_REL
    ]


def _staged_sha256(path: str) -> str | None:
    """sha256 of the staged (index) blob, or None if the path is not in the index
    (e.g. staged for deletion — which the guard treats as unauthorised)."""
    result = subprocess.run(
        ["git", "show", f":{path}"], cwd=_ROOT, check=False, capture_output=True
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def _session_authorised(session_path: Path) -> dict[str, str]:
    """{relpath: sha256} the open session authorises. Lines of the form
    ``<sha256>  <relpath>`` (shasum style); other lines (the stamp) are ignored."""
    authorised: dict[str, str] = {}
    for line in session_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if (
            len(parts) == 2
            and len(parts[0]) == 64
            and all(c in "0123456789abcdef" for c in parts[0].lower())
        ):
            authorised[parts[1]] = parts[0].lower()
    return authorised


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def check(role: str, staged: list[str]) -> int:
    if not staged:
        return 0
    session = _ROOT / _SESSION_REL
    listing = "\n".join(f"  - {path}" for path in staged)
    if not session.is_file():
        if role == "mirror":
            return _fail(
                "EKDP-032: .eukoine/ is a hub-synchronised mirror in this repo.\n"
                f"Staged:\n{listing}\n"
                "Only the EuKoine sync tool writes here. Edit the canonical copy in "
                "EuKoine; the sync pushes it. Do not hand-edit the mirror."
            )
        return _fail(
            "CDP-057: no open write session for .eukoine/.\n"
            f"Staged:\n{listing}\n"
            "Run: python scripts/eukoine_spec_lock.py unlock --from-env\n"
            "Then re-lock when done: python scripts/eukoine_spec_lock.py lock"
        )
    if role == "canonical":
        # Authoring is open-ended; an open (phrase-gated) session authorises the edit.
        return 0
    # mirror: every staged path must match the exact bytes the session authorised.
    authorised = _session_authorised(session)
    for path in staged:
        want = authorised.get(path)
        got = _staged_sha256(path)
        if want is None or got is None or not hmac.compare_digest(want, got):
            return _fail(
                "EKDP-032: staged .eukoine/ content is not what the sync session "
                f"authorised ({path}).\n"
                "The mirror is written only by the EuKoine sync tool, byte-identical "
                "to the hub source. Do not hand-edit the mirror."
            )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="EKDP-032 .eukoine/ pre-commit guard")
    parser.add_argument(
        "--role",
        choices=("mirror", "canonical"),
        required=True,
        help="mirror = consumer repo; canonical = EuKoine writer",
    )
    args = parser.parse_args()
    return check(args.role, _staged_eukoine_paths())


if __name__ == "__main__":
    sys.exit(main())
