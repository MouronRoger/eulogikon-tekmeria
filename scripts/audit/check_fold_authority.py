#!/usr/bin/env python3
"""Enforce the EuKoine Greek-fold authority across an active family repository.

The canonical Python definition of ``lemma_foldkey`` is the EuKoine hub's
``tooling/normalization/greek_normalizer.py``, vendored byte-identical into each
member at the same path (``naming/sync_manifest.toml``).  This guard exempts that
authority path and rejects any *other* definition and the characteristic primitives
of an ad-hoc fold.  (Behavioural drift of the vendored copy itself is caught by the
golden vectors in ``tests/test_fold_authority.py``, not here.)  A legitimate,
kept-distinct normalization may carry a reasoned line comment::

    # fold-authority-exempt: <why this is not the lemma fold>

This file is hub-owned and synchronized byte-identically to the active Eu*
repositories.  Repository-specific policy is deliberately limited to locating
the one authority; the detection rule does not fork by repository.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

AUTHORITY_SUFFIX = Path("tooling/normalization/greek_normalizer.py")
EXEMPTION = re.compile(r"#\s*fold-authority-exempt\s*:\s*(\S.+)")
NFD = re.compile(r"(?:unicodedata\.)?normalize\s*\(\s*['\"]NFD['\"]")
MARK_STRIP = re.compile(
    r"(?:unicodedata\.)?(?:combining|category)\s*\(|"
    r"category\s*\([^)]*\)\s*!?=\s*['\"]Mn['\"]|"
    r"0x0?300\s*<=|isalpha\s*\("
)
CASE_FOLD = re.compile(r"\.(?:lower|casefold)\s*\(")
SIGMA_FOLD = re.compile(
    r"replace\s*\(\s*['\"](?:ς|\\u03c2)['\"]\s*,\s*"
    r"['\"](?:σ|\\u03c3)['\"]\s*\)|"
    r"==\s*['\"]ς['\"]|in\s+['\"][^'\"]*ς[^'\"]*['\"]"
)

SKIP_PARTS = {
    ".claude",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "archive",
    "node_modules",
    "venv",
    "z_no_git",
}

SKIP_FRAGMENTS = {
    ("campaigns", "_closed"),
    ("scripts", "one_off"),
}


def _is_authority(path: Path, root: Path) -> bool:
    try:
        return path.resolve() == (root / AUTHORITY_SUFFIX).resolve()
    except OSError:
        return False


def _exemption(source: str) -> str | None:
    match = EXEMPTION.search(source)
    return match.group(1).strip() if match else None


def _defines_lemma_foldkey(tree: ast.AST) -> bool:
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "lemma_foldkey"
        for node in ast.walk(tree)
    )


def _noncanonical_imports(tree: ast.AST) -> list[str]:
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if any(alias.name == "lemma_foldkey" for alias in node.names):
            if node.module != "greek_normalizer":
                findings.append(node.module or "<relative import>")
    return findings


def _looks_like_fold(source: str) -> bool:
    signals = (
        NFD.search(source),
        MARK_STRIP.search(source),
        CASE_FOLD.search(source),
        SIGMA_FOLD.search(source),
    )
    return sum(signal is not None for signal in signals) >= 3


def scan_file(path: Path, root: Path) -> list[str]:
    """Return blocking findings for one Python file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    if _is_authority(path, root):
        return []

    reason = _exemption(source)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        # Syntax validity belongs to the repository's ordinary parser/linter;
        # this guard must not turn unrelated legacy syntax into fold policy.
        return []

    findings: list[str] = []
    if _defines_lemma_foldkey(tree):
        findings.append(
            f"DRIFT {path}: local lemma_foldkey definition; import the hub authority"
        )
    for module in _noncanonical_imports(tree):
        findings.append(
            f"DRIFT {path}: lemma_foldkey imported through {module}; import the hub greek_normalizer"
        )
    if _looks_like_fold(source) and not reason:
        findings.append(
            f"DRIFT {path}: fold-like normalization primitives without a reasoned exemption"
        )
    return findings


def iter_python(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*.py")
        if not any(
            part in SKIP_PARTS or (part.startswith(".") and part not in {".", ".."})
            for part in path.parts
        )
        and not any(
            all(part in path.parts for part in fragment)
            for fragment in SKIP_FRAGMENTS
        )
    ]


def audit(root: Path) -> list[str]:
    return [finding for path in iter_python(root) for finding in scan_file(path, root)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    findings = audit(root)
    if findings:
        print("fold-authority: FAIL")
        print("\n".join(f"  {finding}" for finding in findings))
        return 1
    print(f"fold-authority: OK — {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
