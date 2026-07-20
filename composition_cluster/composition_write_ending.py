"""Phase 5 writer for the philostorgia Tekmerion composition store.

Runs *after* ``composition_build_store.py`` (scaffold) and
``composition_write_blocks.py`` (the heavy evidence layer). It writes the one
piece of composed prose the earlier phases leave open: the **ending**, the
"checkable landscape" that chapter VI of the store is reserved for. It also
repairs scaffold prose and sets opening/chapter craft fields that Phase 7
projects verbatim.

Design (tekmerion skill, Phase 5 / Phase 7; ``craft.md`` for voice):

* The ending is *restrained and evidential*: checkable counts, one earned
  suggestive shape, then caveats. Every count here is CATALOG class, recomputed
  by the query recorded in ``COUNT_QUERIES`` below.
* Chapter ``shows`` lines are reader-facing hooks (not idx-shaped "shows X").
* ``opening_lead`` rearranges expectation once; ``hinge`` states the arc once.
* Chapter III ``body`` and dating-trap set-asides are **philostorgia-only**
  compose hygiene (clear public title, move trap units to set-aside). The next
  term should set aside traps in Phase 2 and never plan a public trap chapter.

The ``.db`` is gitignored working state; this committed module is the durable,
rebuildable record of the ending. It is idempotent: it re-adds columns only
if absent and rewrites the same rows on each run.
"""

from __future__ import annotations

import pathlib
import sqlite3

HERE = pathlib.Path(__file__).resolve().parent
DB = HERE / "philostorgia.db"

# Queries whose results are woven into the ending as CATALOG-class counts.
COUNT_QUERIES: dict[str, str] = {
    "witnesses_read_closely": (
        "SELECT COUNT(*) FROM station WHERE disposition = 'station'"
    ),
    "distinct_authors": (
        "SELECT COUNT(DISTINCT author) FROM station "
        "WHERE disposition = 'station'"
    ),
    "secondaries": (
        "SELECT COUNT(*) FROM station WHERE disposition = 'secondary'"
    ),
    "set_asides": (
        "SELECT COUNT(*) FROM station WHERE disposition = 'set-aside'"
    ),
    "earliest_secure_floruit": (
        "SELECT MIN(fl_from) FROM station "
        "WHERE disposition = 'station' AND station_type != 'testimonium'"
    ),
    "latest_floruit": (
        "SELECT MAX(fl_from) FROM station WHERE disposition = 'station'"
    ),
    "stoa_chapter_witnesses": (
        "SELECT COUNT(*) FROM station "
        "WHERE disposition = 'station' AND section = 'IV'"
    ),
}

OPENING_LEAD: str = (
    "The lexicons equate affectionate with child-loving. That gloss is true "
    "as far as it goes. The corpus will not let you stop at the nursery door."
)

HINGE: str = (
    "Xenophon sees the instinct in a boy's greeting; the Stoa moralises it, "
    "grounds household and city on it, and derives fellowship outward from it; "
    "Epictetus then asks whether an affection that cannot survive loss counts "
    "at all. The name stays conservative; the test does not."
)

CHAPTER_LEADS: dict[str, str] = {
    "I": (
        "Greek already keeps family-affection as its own household of words, "
        "beside desire and friendship, not as a generic 'love'."
    ),
    "II": (
        "Before any school names it, boys, kings, horses, and jackdaws simply "
        "have it: affection by physis, shown in action rather than defined."
    ),
    "IV": (
        "The Stoa takes that instinct, moralises it, makes it the ground of "
        "marriage and citizenship, and then puts it on trial."
    ),
    "V": (
        "After the school the word spreads through essay, history, medicine, "
        "and at the far edge a Christian redirection of the household image."
    ),
}

# Dating-trap units: verified at compose time, withheld from public projection.
SET_ASIDE_TRAP_UNITS: dict[int, str] = {
    744895: "dating trap: pseudo-Pythagorean letter under archaic name",
    136035: "dating trap: pseudo-Pythagorean Doric treatise, late",
    344155: "dating trap: Homeric Allegorist, mis-dated floruit",
    198622: "dating trap: spurious Physiognomics",
    910544: "secondary Clearchus line; dating-trap chapter withheld from page",
    1924481: "bare poetic fragment; dating-trap chapter withheld from page",
}

# Chapter VI: counts and reader-facing caveats only (not verification voice).
CHAPTER_VI_BODY: str = (
    "Twenty-five passages read closely, from seventeen authors, with six "
    "more cited in passing. The earliest secure prose witness is Xenophon, "
    "near the turn of the fourth century; the latest is Hesychius in the fifth "
    "or sixth, reporting a sense long settled. Chrysippus, Antipater, "
    "Posidonius, the Arius Didymus epitome, Epictetus, and Marcus form the "
    "Stoic spine the corpus preserves for this word.\n\n"
    "Two limits worth naming. The derivation from parental affection outward "
    "is reported doxographically (Arius Didymus, and Plutarch from outside the "
    "school), not in surviving first-person Stoic prose. The Antiphon triad "
    "reaches us only through a grammarian's testimonium. Coverage is by "
    "attested token, not by semantic field. Epictetus's unaffectionate "
    "counterpart also appears in the New Testament vice lists (Rom 1:31; "
    "2 Tim 3:3), a parallel outside this corpus."
)

PUB: dict[str, str] = {
    "title": "Φιλοστοργία: from instinct to the root of justice",
    "subtitle": (
        "from a boy, a king, and a horse-herd to the Stoa's keystone and "
        "Epictetus's test"
    ),
    "blurb": (
        "philostorgia before, during, and after the Stoa: the affection by "
        "physis Xenophon saw in a boy, that Chrysippus made the root of justice "
        "and Epictetus turned into a test."
    ),
    "slug": "philostorgia",
    "pub_date": "2026-07-19",
}


def _ensure_columns(cur: sqlite3.Cursor) -> None:
    """Add nullable prose/metadata columns if they are not present."""
    chapter_cols = {row[1] for row in cur.execute("PRAGMA table_info(chapter)")}
    if "body" not in chapter_cols:
        cur.execute("ALTER TABLE chapter ADD COLUMN body TEXT")
    essay_cols = {row[1] for row in cur.execute("PRAGMA table_info(essay)")}
    for col in ("title", "subtitle", "blurb", "slug", "pub_date", "opening_lead"):
        if col not in essay_cols:
            cur.execute(f"ALTER TABLE essay ADD COLUMN {col} TEXT")


def write_ending(con: sqlite3.Connection) -> None:
    """Write ending, opening craft, chapter leads, and pub metadata.

    Idempotent: adds columns only if absent and rewrites the same rows on each
    run.
    """
    cur = con.cursor()
    _ensure_columns(cur)

    cur.execute(
        "UPDATE chapter SET body = ? WHERE section_no = 'VI'",
        (CHAPTER_VI_BODY,),
    )
    cur.execute(
        "UPDATE chapter SET title = NULL, shows = NULL, body = NULL "
        "WHERE section_no = 'III'"
    )
    for unit_id, reason in SET_ASIDE_TRAP_UNITS.items():
        cur.execute(
            "UPDATE station SET disposition = 'set-aside', reason = ? "
            "WHERE unit_id = ?",
            (reason, unit_id),
        )

    for section_no, lead in CHAPTER_LEADS.items():
        cur.execute(
            "UPDATE chapter SET shows = ? WHERE section_no = ?",
            (lead, section_no),
        )

    cur.execute(
        "UPDATE essay SET title = ?, subtitle = ?, blurb = ?, slug = ?, "
        "pub_date = ?, opening_lead = ?, hinge = ?",
        (
            PUB["title"],
            PUB["subtitle"],
            PUB["blurb"],
            PUB["slug"],
            PUB["pub_date"],
            OPENING_LEAD,
            HINGE,
        ),
    )

    cur.execute(
        "UPDATE essay SET question = ?",
        (
            "What did philostorgia mean before the Stoa made it the root of "
            "justice, and what did the Stoics do with it afterward?",
        ),
    )

    cur.execute(
        "UPDATE claim SET claim = ? WHERE n = 3",
        ("pre-Stoic sense is a zoological instinct by physis",),
    )

    con.commit()


def main() -> None:
    """Write the ending into the store and report what was set."""
    if not DB.exists():
        raise SystemExit(
            f"{DB} missing; run composition_build_store.py first"
        )
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        write_ending(con)
        n_chars = con.execute(
            "SELECT length(body) FROM chapter WHERE section_no = 'VI'"
        ).fetchone()[0]
    finally:
        con.close()
    print(
        f"wrote chapter VI ending ({n_chars} chars); "
        "set opening_lead, chapter leads; hid dating-trap chapter"
    )


if __name__ == "__main__":
    main()
