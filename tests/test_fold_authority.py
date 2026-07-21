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
from greek_normalizer import canonical_lemma, grc_fold, lemma_foldkey  # noqa: E402

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


# The WHOLE-TEXT grain. These are the SAME vectors carried by
# tooling/normalization/grc_fold_test.go — the Python twin must agree byte-for-byte
# with the Go and SQL bindings on every one (STANDARDS.md §2a). Note the punctuation,
# brackets, digits and spaces that SURVIVE: that is what lets a keyed window tell two
# sites apart ("λόγος, δέ" ≠ "λόγος δέ"), the property lemma_foldkey deliberately loses.
GOLDEN_GRCFOLD = {
    "μῆνιν ἄειδε, θεά, Πηληϊάδεω· Ἀχιλῆος": "μηνιν αειδε, θεα, πηληιαδεω· αχιληοσ",
    "λόγος, δέ": "λογοσ, δε",
    "λόγος δέ": "λογοσ δε",
    "λόγῳ": "λογω", "λόγωι": "λογω",
    "μεριμνᾷ": "μεριμνα", "μεριμνᾶι": "μεριμνα",
    "χώραι": "χωραι", "ἥρωϊ": "ηρωι",
    "Ηιι": "ηι", "λόγωιι": "λογωι",  # one adscript iota per vowel; a 2nd bare iota is kept
    "ΒΊΒΛΟΣ": "βιβλοσ", "βίβλος": "βιβλοσ", "βίβλοϲ": "βιβλοσ", "ϐίβλος": "βιβλοσ",
    "ΣΟΦΊΑ σοφία σοφίας": "σοφια σοφια σοφιασ",
    "ὁ ἄνθρωπος (τις) — καὶ [τοῦτο];": "ο ανθρωποσ (τισ) — και [τουτο];",
    "Ἀκουσί[λ]αος": "ακουσι[λ]αοσ",
    "θεός· 42": "θεοσ· 42",
    "ϑεός ϕύσις ϰαί ϱόδον ϖῦρ ϵἶ": "θεοσ φυσισ και ροδον πυρ ει",
}


def test_grc_fold_golden_vectors() -> None:
    """The vendored grc_fold twin folds every whole-text vector to its pinned output."""
    drift = {v: (grc_fold(v), exp) for v, exp in GOLDEN_GRCFOLD.items() if grc_fold(v) != exp}
    assert not drift, f"grc_fold drifted from the Go/SQL binding: {drift}"


def test_grc_fold_word_key_parity() -> None:
    """The two grains are one rule: lettersOnly(grc_fold(t)) == lemma_foldkey(t)."""
    off = {
        v: ("".join(c for c in grc_fold(v) if c.isalpha()), lemma_foldkey(v))
        for v in {**GOLDEN, **GOLDEN_GRCFOLD}
        if "".join(c for c in grc_fold(v) if c.isalpha()) != lemma_foldkey(v)
    }
    assert not off, f"whole-text and word-key grains disagree: {off}"


def test_grc_fold_keeps_punctuation() -> None:
    """The binding-fold regression: two sites split only by punctuation stay distinct
    (the Ninus defect), while the word-key grain collapses them. Same rule, two grains."""
    assert grc_fold("λόγος, δέ") != grc_fold("λόγος δέ")
    assert lemma_foldkey("λόγος, δέ") == lemma_foldkey("λόγος δέ")
