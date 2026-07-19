"""Regular-suite enforcement of the hub-owned Greek-fold standard.

Two protections, both self-contained (no cross-repo `../eukoine` reach, so they hold
in an isolated single-repo checkout / CI):

  * ``test_fold_authority`` — the static guard: no second ``lemma_foldkey`` definition
    and no ad-hoc fold primitives outside a reasoned exemption.
  * ``test_fold_golden_vectors`` — a BEHAVIOURAL drift guard on the vendored authority
    (``tooling/normalization/greek_normalizer.py``, byte-synced from the EuKoine hub).
    The fold guard *exempts* that file by path, so it is the golden vectors that catch a
    hand-edit which changes the fold's output. Regenerate GOLDEN only from the hub
    canonical when the fold rule itself changes (STANDARDS.md §2a; DECISIONS.md).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Import the LOCAL vendored authority (position 0 wins over any same-named module,
# e.g. eulogikon's cluster_greek_quality_gates/oracle/greek_normalizer.py).
sys.path.insert(0, str(ROOT / "tooling" / "normalization"))
from greek_normalizer import canonical_lemma, lemma_foldkey  # noqa: E402

# Canonical fold outputs, generated from the hub authority. Covers sigma (ς/ϲ/Ϲ/Σ→σ),
# the symbol-variant glyphs (ϐϑϕϰϱϖϵ→βθφκρπε) with stigma ϛ PRESERVED, iota adscript→
# subscript with the χώραι residual, mark strip, case, and non-Greek pass-through.
GOLDEN = {
    "μῆνις": "μηνισ", "βιός": "βιοσ", "βίος": "βιοσ", "ἀ-ᾱ́ᾱτος": "ααατοσ",
    "ἀάατος": "ααατοσ", "Ὀδυσσεύς": "οδυσσευσ", "θεὰ": "θεα", "χολωθεὶς": "χολωθεισ",
    "Ἄργεϊ": "αργει", "ᾄδω": "αδω", "ϝοῖνος": "ϝοινοσ", "ἄν1": "αν", "thymos": "thymos",
    "ος": "οσ", "ς": "σ", "ἡρώων,": "ηρωων", "—": "", "": "", "μεριμνᾷ": "μεριμνα",
    "μεριμνᾶι": "μεριμνα", "μεριμνᾶ": "μεριμνα", "λόγῳ": "λογω", "λόγωι": "λογω",
    "τιμῇ": "τιμη", "τιμῆι": "τιμη", "ᾠδή": "ωδη", "ὠιδή": "ωδη", "χώρᾳ": "χωρα",
    "χώραι": "χωραι", "καί": "και", "λύεται": "λυεται", "λύομαι": "λυομαι",
    "ἥρωϊ": "ηρωι", "ΛΟΓΩΙ": "λογω", "ΠΟΝΤΩΙ": "ποντω", "ϐαίνω": "βαινω",
    "ἀϐαρής": "αβαρησ", "περίϐολος": "περιβολοσ", "ϑεός": "θεοσ", "ϴεός": "θεοσ",
    "ϕύσις": "φυσισ", "ϰαί": "και", "ϱόδον": "ροδον", "ϖῖ": "πι", "ϵν": "εν",
    "ϲοφία": "σοφια", "Ϲοφία": "σοφια", "λόγοϲ": "λογοσ", "χϱόνοϛ": "χρονοϛ",
}


def test_fold_authority() -> None:
    guard = ROOT / "scripts" / "audit" / "check_fold_authority.py"
    result = subprocess.run(
        [sys.executable, str(guard), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fold_golden_vectors() -> None:
    """The vendored authority must fold every canonical vector to its pinned output."""
    drift = {v: (lemma_foldkey(v), exp) for v, exp in GOLDEN.items() if lemma_foldkey(v) != exp}
    assert not drift, f"vendored fold drifted from canonical: {drift}"


def test_canonical_lemma_present() -> None:
    """canonical_lemma is exported and applies the symbol-variant map (ϐ→β)."""
    assert canonical_lemma("ϐίβλοϲ") == "βίβλοσ"
