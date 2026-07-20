#!/usr/bin/env python3
"""Guardian: every registered principle has a real home (TDP-012 / TAP-007).

Shape check, not a correctness check. It asserts that each entry in
governance_cluster/registry.yaml names an owner file that exists and contains its
declared owner_marker verbatim. That is what stops a principle drifting into a
number nobody can trace to a statement, and what stops a statement being
quietly moved or reworded out from under its id.

It does NOT check that the rule is followed. Per governance_cluster/script_lifecycle.md,
a guardian is never the evidence that work is right.

Entries carrying `owner_state` are family-owned and mirrored in at enrolment;
they are reported as deferred, not failed, while the mirror is absent.

Exit 0 clean, 1 on any failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

REPO = Path(__file__).resolve().parents[1]
# The registry is a co-worker in this cluster: resolve it beside this file, not
# by a path spelled out from the repo root. That is what keeps the pair movable
# together and is why they live in one home (EKDP-033).
REGISTRY = Path(__file__).resolve().parent / "registry.yaml"


def flatten(text: str) -> str:
    """Collapse runs of whitespace, so a marker may span a markdown line wrap.

    The marker is a claim about what the owner file says, not about how it is
    wrapped. Reflowing a paragraph must not break the binding.
    """
    return re.sub(r"\s+", " ", text)


def main() -> int:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))

    failures: list[str] = []
    deferred: list[str] = []
    checked = 0

    for entry in registry.get("principles", []):
        pid = entry["id"]
        owner = entry.get("owner")
        marker = entry.get("owner_marker")

        if not owner:
            failures.append(f"{pid}: no owner declared")
            continue

        owner_path = (REPO / owner).resolve()

        if entry.get("owner_state"):
            state = "present" if owner_path.exists() else "absent"
            deferred.append(f"{pid}: family-owned, {owner} ({state})")
            continue

        if not owner_path.exists():
            failures.append(f"{pid}: owner file missing: {owner}")
            continue

        if not marker:
            failures.append(f"{pid}: owner {owner} declared with no owner_marker")
            continue

        if flatten(marker) not in flatten(owner_path.read_text(encoding="utf-8")):
            failures.append(f"{pid}: marker not found in {owner}\n      wanted: {marker!r}")
            continue

        checked += 1

    ids = {e["id"] for e in registry.get("principles", [])}
    for ap in registry.get("anti_patterns", []):
        for violated in ap.get("violates", []):
            if violated not in ids:
                failures.append(f"{ap['id']}: violates unknown principle {violated}")

    for line in deferred:
        print(f"  deferred  {line}")
    for line in failures:
        print(f"  FAIL      {line}")

    total = len(registry.get("principles", []))
    print(f"\n{checked}/{total} principles bound to a live owner_marker; "
          f"{len(deferred)} deferred; {len(failures)} failed.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
