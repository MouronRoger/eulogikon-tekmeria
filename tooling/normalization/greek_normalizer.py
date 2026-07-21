"""Greek text normalization utilities for Eulogikon.

This module provides functions to normalize ancient Greek text for
semantic search and AI processing by:
- Removing Latin apparatus and citations
- Resolving lacunae markers (e.g., ἔ(πρ)αττεν → ἔπραττεν)
- Stripping editorial marks and ellipsis
- Unicode normalization
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Pattern

# Regex patterns for text cleaning
LACUNA_PATTERN: Pattern[str] = re.compile(r"\(([^\)]+)\)")  # (text) in lacunae
ELLIPSIS_PATTERN: Pattern[str] = re.compile(r"\.{2,}|——+|etc\.")  # ellipsis markers
LATIN_CITATION_PATTERN: Pattern[str] = re.compile(
    r"^[A-Z][a-z]+(?:\s+[A-Z]?[a-z]*\.?)*\s+[\dIVX]+[,\.\s]+[\dIVX]*"
)  # Match Latin citations at start
EDITORIAL_NOTE_PATTERN: Pattern[str] = re.compile(
    r"\([A-Z][a-z].*?\)"
)  # Match (Latin editorial notes)
COLUMN_REF_PATTERN: Pattern[str] = re.compile(
    r"Col\.\s+[IVXLCDM]+,\s*\d+"
)  # Match "Col. XXXIX, 3"


def is_greek_char(char: str) -> bool:
    """Check if a character is Greek (including polytonic).

    Args:
        char: Single character to check

    Returns:
        True if character is Greek, False otherwise
    """
    if not char:
        return False
    name = unicodedata.name(char, "")
    return "GREEK" in name


def is_latin_char(char: str) -> bool:
    """Check if a character is Latin.

    Args:
        char: Single character to check

    Returns:
        True if character is Latin, False otherwise
    """
    if not char:
        return False
    # Check if it's a basic Latin letter (A-Z, a-z)
    return char.isalpha() and ord(char) < 0x0370


def is_latin_only(text: str) -> bool:
    """Check if text contains no Greek content.

    Args:
        text: Text to check

    Returns:
        True if text has no Greek characters, False otherwise
    """
    return not any(is_greek_char(char) for char in text)


def has_significant_greek(text: str, min_chars: int = 10) -> bool:
    """Check if text has significant Greek content.

    Args:
        text: Text to check
        min_chars: Minimum number of Greek characters required

    Returns:
        True if text has at least min_chars Greek characters
    """
    greek_count = sum(1 for char in text if is_greek_char(char))
    return greek_count >= min_chars


def extract_greek_only(text: str) -> str:
    """Extract only Greek portions from mixed text.

    Removes all Latin characters while preserving Greek text,
    punctuation, and whitespace.

    Args:
        text: Mixed Greek/Latin text

    Returns:
        Text with only Greek characters and punctuation
    """
    result = []
    for char in text:
        # Keep Greek characters and common punctuation
        if is_greek_char(char) or char in " .,;·()[]{}᾿'":
            result.append(char)
    return "".join(result).strip()


def resolve_lacunae(text: str) -> str:
    """Resolve lacunae markers in papyrus transcriptions.

    Converts editorial lacunae markers like ἔ(πρ)αττεν to ἔπραττεν
    by removing parentheses and keeping the content.

    Args:
        text: Text with lacunae markers

    Returns:
        Text with lacunae resolved
    """

    def resolve_match(match: re.Match[str]) -> str:
        # Keep only Greek content inside parentheses
        content = match.group(1)
        return "".join(char for char in content if is_greek_char(char))

    return LACUNA_PATTERN.sub(resolve_match, text)


def strip_editorial_apparatus(text: str) -> str:
    """Remove editorial apparatus from text.

    Removes:
    - Latin editorial notes in parentheses
    - Ellipsis markers (etc., ....., ——)
    - Column/line references (Col. XXXIX, 3)

    Args:
        text: Text with editorial apparatus

    Returns:
        Text with apparatus removed
    """
    # Remove ellipsis markers
    text = ELLIPSIS_PATTERN.sub("", text)

    # Remove column references
    text = COLUMN_REF_PATTERN.sub("", text)

    # Remove editorial notes (but preserve Greek in parentheses)
    # This is tricky - we want to remove (Latin notes) but keep (Greek lacunae)
    # So we check if content is mostly Latin
    def filter_parentheses(match: re.Match[str]) -> str:
        content = match.group(1)
        # If content starts with capital Latin, it's likely an editorial note
        if content and content[0].isupper() and is_latin_char(content[0]):
            return ""
        # Otherwise keep it (might be Greek lacuna)
        return match.group(0)

    text = re.sub(r"\(([^)]+)\)", filter_parentheses, text)

    return text


def strip_latin_prefix(text: str) -> str:
    """Remove Latin citation prefix from start of text.

    Removes patterns like:
    - "Diog. Laërt. VII 183."
    - "Strabo 1,1,7"
    - "Eusebius praep. evang. XV 13, 8"

    Args:
        text: Text potentially starting with Latin citation

    Returns:
        Text with Latin prefix removed
    """
    # Try to match Latin citation at start
    match = LATIN_CITATION_PATTERN.match(text)
    if match:
        return text[match.end() :].strip()
    return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Collapses multiple spaces into single spaces and removes
    leading/trailing whitespace.

    Args:
        text: Text with irregular whitespace

    Returns:
        Text with normalized whitespace
    """
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """Normalize Unicode representation of Greek text.

    Uses NFC (Canonical Decomposition followed by Canonical Composition)
    to ensure consistent representation of polytonic Greek.

    Args:
        text: Greek text with potentially inconsistent Unicode

    Returns:
        Text with normalized Unicode
    """
    return unicodedata.normalize("NFC", text)


# The combining-marks range (NFD accents/breathings/diaeresis/iota-subscript) the fold strips.
_COMBINING_LO, _COMBINING_HI = 0x0300, 0x036F

# Greek symbol-variant glyphs (the U+03D0–U+03F5 block) that carry a Unicode <compat>
# decomposition to their base letter — the SAME letters (Bailly's French editions write medial
# beta as ϐ), so they must canonicalise for both identity (lemma_id) and the fold. Excludes ϛ
# (U+03DB stigma): no decomposition, a distinct letter/numeral (the numeral 6). The two uppercase
# variants (Ϲ lunate sigma, ϴ theta symbol) are included so the case-preserving canonical form
# covers them; the fold reaches them via .lower() → ϲ/ϑ before the map. (grc_fold.sql mirrors this;
# STANDARDS.md §2a carries the ratified rule.)
_SYMBOL_VARIANTS = {
    "ϐ": "β", "ϑ": "θ", "ϕ": "φ", "ϰ": "κ", "ϱ": "ρ", "ϖ": "π", "ϵ": "ε", "ϲ": "σ",
    "Ϲ": "Σ", "ϴ": "Θ",
}
_SYMBOL_TRANS = str.maketrans(_SYMBOL_VARIANTS)


def canonical_lemma(text: str) -> str:
    """Canonical Greek headword for IDENTITY (lemma_id minting): NFC + fold the Greek
    symbol-variant glyphs (ϐϑϕϰϱϖϵϲ + uppercase Ϲϴ) to their base letters. Accents and case
    are PRESERVED — this is the identity canonicalisation, not the accent-blind fold. So
    ``canonical_lemma("ἀϐαρής") == "ἀβαρής"`` and both mint one lemma id. ϛ stigma is left
    intact (a distinct letter). The minter routes through this so two spellings of one word
    share one identity (the ϐ/β join-breaker fix, 2026-07-09)."""
    return unicodedata.normalize("NFC", text).translate(_SYMBOL_TRANS)

# Iota adscript written for an iota subscript (the join-breaker the subscript path
# already folds away). A bare iota — one carrying no diacritic of its own — standing
# after a long vowel is a subscript context written on the line: ᾳ→ΑΙ, ῃ→ΗΙ, ῳ→ΩΙ.
# η and ω are ALWAYS long, so a bare adscript ι after them is always subscript-context
# (drop it); a genuine ηι/ωι hiatus is always written with a diaeresis on the ι, which
# the bare-ι guard below preserves. After α the ι is dropped only when the α itself
# bears a diacritic — Greek never accents the first element of a diphthong, so an
# accented/circumflexed α before a BARE ι cannot be a diphthong (μεριμνᾶι→μεριμνα). A
# bare α + bare ι (χώραι) is LEFT untouched: orthographically indistinguishable from a
# real -αι (-μαι/-ται, καί) without a length oracle, so collapsing it would over-fold.
# Applied on the NFD string with marks still in place, BEFORE the strip-combining fold.
_ADSCRIPT_IOTA_LONG = re.compile(r"([ηωΗΩ][̀-ͯ]*)[ιΙ](?![̀-ͯ])")
_ADSCRIPT_IOTA_ALPHA = re.compile(r"([αΑ][̀-ͯ]+)[ιΙ](?![̀-ͯ])")


def _drop_adscript_iota(decomposed: str) -> str:
    """Drop an adscript iota standing in for a subscript (η/ω + bare ι, or marked-α + bare ι).

    Applied once to surface text (every consumer folds surface→key, never re-folds a key).
    NOT idempotent on its own output: ἥρωϊ→ηρωι keeps the ι because the diaeresis marks a
    hiatus, but the key ηρωι (diaeresis gone) reads as adscript ωι and would lose the ι on a
    second pass — the same once-only-on-canonical-text discipline archaicize() carries."""
    return _ADSCRIPT_IOTA_ALPHA.sub(r"\1", _ADSCRIPT_IOTA_LONG.sub(r"\1", decomposed))


# ---------------------------------------------------------------------------
# lemma_foldkey — the lexicon/surface merge key. Unlike _archaic_fold_key (which
# KEEPS the diaeresis for diphthong-collapse idempotency), this is the maximally
# folded headword key: every combining mark (accent, breathing, macron, diaeresis,
# iota-subscript) and every non-letter (hyphen, punctuation) is dropped, leaving
# lowercase Greek base letters with final sigma → σ. This is what makes Autenrieth's
# "ἀ-ᾱ́ᾱτος" and Cunliffe's "ἀάατος" collide onto one lemma. Shared by merge_lexica,
# adjudicate_lemma, align_tokens, and the reader's click-to-lemma fold (one definition,
# the single fold owner for every consumer).
# ---------------------------------------------------------------------------
def lemma_foldkey(text: str) -> str:
    """Maximally folded merge key: lowercase Greek base letters only, ς/ϲ/Ϲ/Σ→σ and the
    Greek symbol-variant glyphs folded to their base letters (ϐ→β, ϑ→θ, ϕ→φ, ϰ→κ, ϱ→ρ,
    ϖ→π, ϵ→ε — see _SYMBOL_VARIANTS), all marks and non-letters dropped, with iota adscript
    canonicalised to iota subscript (_drop_adscript_iota) so λόγῳ/λόγωι and μεριμνᾷ/μεριμνᾶι
    fold to one key. Distinct from _archaic_fold_key, which keeps the diaeresis.

    Note: This fold strips ALL combining marks including macron (U+0304) and breve (U+0306)
    quantity marks. Morphology/paradigm code that needs vowel quantity must operate on full
    NFD forms, never on this fold key."""
    out: list[str] = []
    for c in _drop_adscript_iota(unicodedata.normalize("NFD", text)):
        if c.isalpha() and not (_COMBINING_LO <= ord(c) <= _COMBINING_HI):
            b = _SYMBOL_VARIANTS.get(c.lower(), c.lower())   # ϐ→β … ϲ→σ (symbol-variant glyphs)
            out.append("σ" if b == "ς" else b)
    return "".join(out)


_SURFACE_PUNCT = ".,··•;·:·—-–―()[]{}«»‹›“”‘’··∷‧、。'"


def norm_surface_form(form: str | None) -> str:
    """Fold a token surface for cross-witness alignment (treebank probes).

    Single shared helper — every consumer imports this instead of re-copying
    lemma_foldkey + punct normalization locally.
    """
    if not form:
        return ""
    folded = lemma_foldkey(form)
    return folded.strip(_SURFACE_PUNCT).replace("’", "'").replace("ʼ", "'")


# ---------------------------------------------------------------------------
# grc_fold — the WHOLE-TEXT grain of the same character rule. Where lemma_foldkey
# drops every non-letter (the word-key grain, for headword identity), grc_fold
# KEEPS word boundaries, punctuation, digits and Latin — stripping only combining
# marks — so a keyed window can tell "λόγος, δέ" from "λόγος δέ". This is the fold
# for SUBSTRING SEARCH and KEYED-WINDOW BINDING. The Python twin of grc_fold.sql
# and grc_fold.go: the three MUST agree byte-for-byte (STANDARDS.md §2a; golden
# vectors in tests/test_fold_authority.py). A MATCHING fold, never a storage
# transform — stored Greek stays NFC polytonic; never persist grc_fold output.
# The two grains are one rule: lettersOnly(grc_fold(t)) == lemma_foldkey(t).
# ---------------------------------------------------------------------------
def grc_fold(text: str) -> str:
    """Accent-blind, PUNCTUATION-PRESERVING Greek fold (whole-text matching key).

    NFD → canonicalise iota adscript→subscript (_drop_adscript_iota) → strip combining
    marks (U+0300–U+036F) → lowercase → fold sigma (ς/ϲ/Ϲ/Σ→σ) and the Greek symbol-variant
    glyphs (ϐ→β … ϵ→ε; _SYMBOL_VARIANTS). Identical to grc_fold.sql / grc_fold.go on the same
    input. Non-letters (spaces, punctuation, digits, Latin) pass through unchanged — that is
    the whole point of the whole-text grain and the reason it is NOT slice-safe: cut keyed
    windows in FOLDED space, never fold a raw slice (grc_fold.go carries the position-map twin)."""
    out: list[str] = []
    for c in _drop_adscript_iota(unicodedata.normalize("NFD", text)):
        if _COMBINING_LO <= ord(c) <= _COMBINING_HI:
            continue                                         # strip diacritics — accent-blind
        low = c.lower()                                      # ToLower every rune (Ϲ→ϲ, Σ→σ), then map
        b = _SYMBOL_VARIANTS.get(low, low)                   # ϲ→σ, ϐ→β … ; non-letters map to themselves
        out.append("σ" if b == "ς" else b)                  # final sigma ς→σ (not a map key), matching grc_fold.go
    return "".join(out)


def normalize_greek(text: str, preserve_punctuation: bool = True) -> str:
    """Normalize Greek text for semantic search and AI processing.

    This is the main normalization function that applies all cleaning steps:
    1. Strip Latin citation prefix
    2. Strip editorial apparatus
    3. Resolve lacunae markers
    4. Extract Greek only (optional)
    5. Normalize whitespace
    6. Normalize Unicode

    Args:
        text: Raw Greek text with apparatus
        preserve_punctuation: If True, keep Greek punctuation marks

    Returns:
        Clean, normalized Greek text suitable for embeddings
    """
    # Strip Latin prefix if present
    text = strip_latin_prefix(text)

    # Strip editorial apparatus
    text = strip_editorial_apparatus(text)

    # Resolve lacunae
    text = resolve_lacunae(text)

    # Extract Greek only (removes remaining Latin)
    if not preserve_punctuation:
        text = extract_greek_only(text)

    # Normalize whitespace
    text = normalize_whitespace(text)

    # Normalize Unicode
    text = normalize_unicode(text)

    return text


def normalize_for_embedding(text: str) -> str:
    """Normalize text specifically for embedding generation.

    Applies aggressive normalization including:
    - All normalize_greek() steps
    - Removes all punctuation
    - Lowercases (for language models that expect lowercase)

    Args:
        text: Raw Greek text

    Returns:
        Aggressively normalized text for embeddings
    """
    # Apply standard normalization
    text = normalize_greek(text, preserve_punctuation=False)

    # Remove punctuation
    text = re.sub(r"[.,;·᾿'()[\]{}]", "", text)

    # Note: We don't lowercase Greek because case carries meaning
    # in ancient Greek (proper names, emphasis, etc.)

    return text.strip()


def extract_testimonium_prefix(text: str) -> tuple[str, str]:
    """Extract testimonium-source citation prefix from text.

    Args:
        text: Text potentially starting with a testimonium-source citation

    Returns:
        Tuple of (testimonium_prefix, remaining_text)
    """
    match = LATIN_CITATION_PATTERN.match(text)
    if match:
        prefix = text[: match.end()].strip()
        remaining = text[match.end() :].strip()
        return prefix, remaining
    return "", text
