"""Mutation fixtures proving that the fold-authority guard fails closed."""

from __future__ import annotations

import importlib.util
from pathlib import Path

GUARD_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "audit"
    / "check_fold_authority.py"
)
SPEC = importlib.util.spec_from_file_location("check_fold_authority", GUARD_PATH)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "candidate.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_rejects_local_authority_definition(tmp_path: Path) -> None:
    path = _write(tmp_path, "def lemma_foldkey(text):\n    return text\n")
    assert any("local lemma_foldkey definition" in item for item in GUARD.scan_file(path, tmp_path))


def test_rejects_fold_primitive_pipeline(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """import unicodedata
def private_fold(text):
    text = unicodedata.normalize("NFD", text).lower()
    return "".join(c for c in text if not unicodedata.combining(c)).replace("ς", "σ")
""",
    )
    assert any("fold-like normalization primitives" in item for item in GUARD.scan_file(path, tmp_path))


def test_rejects_member_local_reexport_import(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "from member.oracle.greek_normalizer import lemma_foldkey\n",
    )
    assert any("imported through member.oracle" in item for item in GUARD.scan_file(path, tmp_path))


def test_accepts_reasoned_kept_distinct_normalization(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# fold-authority-exempt: quantity-preserving metre witness, not a lemma key
import unicodedata
def metre_form(text):
    text = unicodedata.normalize("NFD", text).lower()
    return "".join(c for c in text if not unicodedata.combining(c)).replace("ς", "σ")
""",
    )
    assert GUARD.scan_file(path, tmp_path) == []
