#!/usr/bin/env python3
"""EuKoine sync — push the synchronising set (naming/sync_manifest.toml) to members.

Operational subcommands: ``status``, ``verify``, ``push`` (dry-run unless ``--execute``).

Runnable from every repo. The hub is resolved by ``naming/_manifest.hub_root`` —
this repo when it is the hub, otherwise the sibling hub (or ``EUKOINE_HUB``) — and
the canonical source, mirror paths, and owner ``.env`` are all taken from that
resolved hub. So a member can drive the same hub→mirrors push the hub itself does;
the canonical source is always the one hub, never the invoking repo.

Workflow, git safety, and the no-secondary-sources rule:
``.eukoine/WRITE_ACCESS.md`` (§Synchronizing agent · §Git safety · §No secondary sources).
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _manifest  # noqa: E402


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head_sha(repo_root: Path, relpath: str) -> str | None:
    """sha256 of the COMMITTED (HEAD) blob, or None if the path is not in HEAD.

    The sync invariant is committed parity: a clean checkout / CI of the mirror must
    see the hub's content. Comparing the mirror's working tree would call a doc that
    sits modified-but-uncommitted 'in sync' when it is not."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{relpath}"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def _is_ignored(repo_root: Path, relpath: str) -> bool:
    """True if the target repo gitignores this path (so it cannot be committed there)."""
    return _run(["git", "check-ignore", relpath], repo_root).returncode == 0


def _artefact_sha(repo_root: Path, relpath: str) -> str | None:
    """The parity hash for a target. Committed (HEAD) parity is the invariant for tracked
    files; for a path the target *gitignores*, committed parity is impossible — so
    working-tree byte-presence is the achievable invariant (the file is still functional,
    e.g. a Cursor rule the editor reads from disk)."""
    if _is_ignored(repo_root, relpath):
        return _sha256(repo_root / relpath)
    return _head_sha(repo_root, relpath)


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), check=False, capture_output=True, text=True
    )


def _darwin() -> bool:
    return sys.platform == "darwin"


def _chflags(flag: str, path: Path) -> bool:
    if not _darwin():
        return True
    result = subprocess.run(
        ["chflags", flag, str(path)], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: chflags {flag} {path}: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def _load_env_key(repo_root: Path, key: str) -> str | None:
    env = repo_root / ".env"
    if not env.is_file():
        return None
    for raw_line in env.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith(f"{key}="):
            value = line.split("=", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                return value[1:-1]
            return value
    return None


def _rows(m: _manifest.Manifest):
    """Yield (mirror_name, artefact, hub_sha, mirror_sha)."""
    for art in m.artefacts:
        hub_sha = _sha256(m.repo_root / art.path)
        for target in art.targets:
            yield target, art, hub_sha, _artefact_sha(m.mirrors[target], art.path)


def cmd_status(m: _manifest.Manifest) -> int:
    print(f"hub: {m.repo_root}")
    for name, root in sorted(m.mirrors.items()):
        suffix = "" if root.is_dir() else "  (MISSING)"
        print(f"mirror: {name} -> {root}{suffix}")
    print()
    for target, art, hub_sha, mir_sha in _rows(m):
        state = (
            "MISSING"
            if mir_sha is None
            else ("MATCH" if mir_sha == hub_sha else "DRIFT")
        )
        print(
            f"  [{state:7}] {target:12} {art.path}   ({'locked' if art.locked else 'open'})"
        )
    return 0


def cmd_verify(m: _manifest.Manifest) -> int:
    bad = [(t, art, mir) for t, art, hub, mir in _rows(m) if mir != hub]
    if bad:
        print("DIVERGENCE — mirrors not byte-identical to hub:", file=sys.stderr)
        for target, art, mir in bad:
            print(
                f"  {target:12} {art.path}  ({'missing' if mir is None else 'drift'})",
                file=sys.stderr,
            )
        return 1
    copies = sum(len(a.targets) for a in m.artefacts)
    print(
        f"OK — {copies} artefact copies byte-identical across {len(m.mirrors)} mirrors"
    )
    return 0


def _paths_need_commit(root: Path, paths: list[str]) -> bool:
    """True if any path is new to HEAD or differs from HEAD."""
    if not paths:
        return False
    for p in paths:
        if (root / p).is_file() and _head_sha(root, p) is None:
            return True
    return _run(["git", "diff", "--quiet", "HEAD", "--", *paths], root).returncode != 0


def _foreign_staged(root: Path, allowed: frozenset[str]) -> list[str]:
    """Staged paths outside the manifest set (left untouched by sync commits)."""
    result = _run(["git", "diff", "--cached", "--name-only"], root)
    return [
        line
        for line in result.stdout.splitlines()
        if line.strip() and line not in allowed
    ]


def _commit_manifest_paths(root: Path, repo_name: str, paths: list[str]) -> bool:
    """Commit only manifest paths via pathspec; never pick up other staged files."""
    if not paths:
        return True
    if not _paths_need_commit(root, paths):
        return True
    foreign = _foreign_staged(root, frozenset(paths))
    if foreign:
        preview = ", ".join(foreign[:5])
        suffix = "…" if len(foreign) > 5 else ""
        print(
            f"  {repo_name}: other staged files present ({preview}{suffix}) — "
            "sync commit will NOT include them",
        )
    msg = "sync: update synchronising set from EuKoine hub\n\n" + "\n".join(
        f"- {p}" for p in paths
    )
    add_res = _run(["git", "add", "--", *paths], root)
    if add_res.returncode != 0:
        print(
            f"ERROR: {repo_name}: git add failed: {add_res.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    # Pathspec commit: only these paths enter the commit; pre-existing staged WIP stays
    # staged. No git add -A, no stash, no whole-tree operations (EKDP-031/032).
    commit_res = _run(["git", "commit", "--no-verify", "-m", msg, "--", *paths], root)
    if commit_res.returncode != 0:
        print(
            f"ERROR: {repo_name}: commit failed: {commit_res.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def _push_repo(
    m: _manifest.Manifest, name: str, items: list[tuple[_manifest.Artefact, str]]
) -> bool:
    """items: (artefact, hub_sha). True only when synced artefacts are committed (or no-op)."""
    root = m.mirrors[name]
    if not (root / ".git").is_dir():
        print(f"ERROR: {name}: not a git repo at {root}", file=sys.stderr)
        return False
    locked = [a for a, _ in items if a.locked]

    for art in locked:  # a) unlock
        path = root / art.path
        if path.is_file():
            _chflags("nouchg", path)
    for art, _ in items:  # b) write byte-identical
        dst = root / art.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(m.repo_root / art.path, dst)
    for art, hub_sha in items:  # c) verify BEFORE any commit
        if _sha256(root / art.path) != hub_sha:
            print(
                f"ERROR: {name}: verify failed for {art.path} — aborting before commit",
                file=sys.stderr,
            )
            for x in locked:
                _chflags("uchg", root / x.path)
            return False

    paths = [a.path for a, _ in items]  # d) commit manifest paths only (pathspec)
    tracked = [p for p in paths if not _is_ignored(root, p)]
    if not _commit_manifest_paths(root, name, tracked):
        for x in locked:
            _chflags("uchg", root / x.path)
        return False

    relock_ok = all(  # e) re-lock (loud)
        _chflags("uchg", root / a.path) for a in locked if (root / a.path).is_file()
    )

    if not relock_ok:
        print(f"ERROR: {name}: re-lock failed — mirror left writable", file=sys.stderr)
        return False
    return True


def cmd_push(m: _manifest.Manifest, execute: bool) -> int:
    worklist: list[tuple[str, _manifest.Artefact, str]] = []
    for art in m.artefacts:
        hub_sha = _sha256(m.repo_root / art.path)
        if hub_sha is None:
            print(f"ERROR: hub source missing: {art.path} — aborting", file=sys.stderr)
            return 1
        for target in art.targets:
            if _artefact_sha(m.mirrors[target], art.path) != hub_sha:
                worklist.append((target, art, hub_sha))

    if not worklist:
        print("in sync — nothing to push")
        return 0
    print("pushing:" if execute else "would update:")
    for target, art, _ in worklist:
        print(f"  {target:12} {art.path}")
    if not execute:
        print("\n(dry-run — pass --execute to apply)")
        return 0

    if any(art.locked for _, art, _ in worklist):
        if not _load_env_key(m.repo_root, "EUKOINE_SPEC_AUTHORIZE"):
            print(
                "REFUSED: locked artefacts in the worklist require EUKOINE_SPEC_AUTHORIZE in .env.",
                file=sys.stderr,
            )
            return 1

    by_repo: dict[str, list[tuple[_manifest.Artefact, str]]] = {}
    for target, art, hub_sha in worklist:
        by_repo.setdefault(target, []).append((art, hub_sha))

    failures = [
        name for name in sorted(by_repo) if not _push_repo(m, name, by_repo[name])
    ]
    print()
    verify_rc = cmd_verify(m)
    if failures:
        print(
            f"INCOMPLETE — repos left behind: {', '.join(failures)}. "
            "Re-run `python naming/sync.py push --execute` to converge.",
            file=sys.stderr,
        )
        return 1
    return verify_rc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="EuKoine sync — push the synchronising set to members"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="show per-artefact mirror state")
    sub.add_parser("verify", help="exit 0 iff mirrors are byte-identical to the hub")
    push = sub.add_parser(
        "push", help="push the synchronising set (dry-run unless --execute)"
    )
    push.add_argument(
        "--execute",
        action="store_true",
        help="perform the push (reserved/irreversible)",
    )
    args = parser.parse_args()

    m = _manifest.load()
    if args.cmd == "status":
        return cmd_status(m)
    if args.cmd == "verify":
        return cmd_verify(m)
    if args.cmd == "push":
        return cmd_push(m, args.execute)
    return 1


if __name__ == "__main__":
    sys.exit(main())
