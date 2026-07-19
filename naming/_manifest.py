"""Load the EuKoine synchronising manifest (naming/sync_manifest.toml).

The manifest is the single declaration of WHAT is synced WHERE. Everything that
pushes or verifies iterates from these declared keys — never a filesystem glob
(EKDP-016 / ROT.md A5). Strict: unknown fields/targets raise rather than silently
defaulting (no silent fallback).

Hub resolution (runnable from every repo). The unlock/sync/relock cycle may be
driven from any family repo, not only the hub. Because the toolchain is synced
byte-identical into every mirror, a script cannot assume *its own* repo is the
hub. The hub is resolved, in order:

1. the ``EUKOINE_HUB`` environment variable (absolute, or relative to the cwd);
2. the invoking repo itself, when its directory name is the manifest's
   ``[hub] name`` (i.e. the tool is being run inside the hub);
3. otherwise the sibling directory ``<invoking-repo>/../<hub-name>``.

Mirror paths, the owner ``.env``, and the write session are all resolved against
the resolved hub, so every repo drives the *same* canonical hub.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_THIS_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST = _THIS_REPO_ROOT / "naming" / "sync_manifest.toml"
_HUB_NAME_DEFAULT = "eukoine"
_HUB_ENV_KEY = "EUKOINE_HUB"


@dataclass(frozen=True)
class Artefact:
    path: str
    kind: str
    locked: bool
    targets: tuple[str, ...]


@dataclass(frozen=True)
class Manifest:
    repo_root: Path  # the resolved HUB root (the canonical source), from any repo
    mirrors: dict[str, Path]  # name -> absolute repo path
    artefacts: tuple[Artefact, ...]

    def locked_paths(self) -> list[str]:
        return [a.path for a in self.artefacts if a.locked]


def _hub_name(data: dict[str, object]) -> str:
    hub = data.get("hub")
    if isinstance(hub, dict):
        name = hub.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return _HUB_NAME_DEFAULT


def _resolve_hub_root(hub_name: str) -> Path:
    """Resolve the canonical hub root from whichever repo the tool runs in."""
    override = os.environ.get(_HUB_ENV_KEY)
    if override:
        candidate = Path(override).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        return candidate.resolve()
    if _THIS_REPO_ROOT.name == hub_name:
        return _THIS_REPO_ROOT
    return (_THIS_REPO_ROOT.parent / hub_name).resolve()


def hub_root() -> Path:
    """Return the resolved hub root (read the local, byte-identical manifest)."""
    data = tomllib.loads(_MANIFEST.read_text(encoding="utf-8"))
    return _resolve_hub_root(_hub_name(data))


def load() -> Manifest:
    data = tomllib.loads(_MANIFEST.read_text(encoding="utf-8"))
    hub = _resolve_hub_root(_hub_name(data))
    mirrors = {name: (hub / rel).resolve() for name, rel in data["mirrors"].items()}
    artefacts: list[Artefact] = []
    for raw in data["artefacts"]:
        art = Artefact(
            path=raw["path"],
            kind=raw["kind"],
            locked=bool(raw["locked"]),
            targets=tuple(raw["targets"]),
        )
        for t in art.targets:
            if t not in mirrors:
                raise ValueError(f"manifest: {art.path} targets unknown mirror {t!r}")
        artefacts.append(art)
    return Manifest(repo_root=hub, mirrors=mirrors, artefacts=tuple(artefacts))
