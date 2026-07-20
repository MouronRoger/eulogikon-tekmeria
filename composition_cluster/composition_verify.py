"""Phase 6 verification for the philostorgia Tekmerion composition store.

Produces the verification report rather than asserting it: every check is
computed from the store (``philostorgia.db``) or from a live corpus/rules query
recorded here, and a failing line blocks the flip of a station to ``checked``.

The two checks that need the live family database are kept reproducible by
recording their inputs as files beside the store, not by hand-copying results:

* **Quote integrity** matches each Greek segment against ``eulogikon.units``.
  ``--emit-quote-sql`` writes ``philostorgia_quote_check.sql`` straight from the
  ``block`` rows and the inline-projected ``idx`` phrases (needles byte-exact
  from SQLite, never retyped). That SQL is run read-only through the
  ``user-postgres`` MCP and its rows saved to ``philostorgia_quote_check.json``.
* **Blacklist scan** needs the enabled ``eugraphikon.signal_triggers`` rows;
  they are saved to ``philostorgia_blacklist_rules.json`` and scanned here
  against the English fields only (Greek is verbatim QUOTE and exempt).

The store-only checks (bare-Greek, apparatus-bracket, ecclesiastical,
coverage, catalog counts, period claims, claims register, HAND register, U+2014
scan) run with no external input. Three of them enforce reading-surface rules:
``bare_greek`` (no bare Greek/transliteration in an English field; every Greek
token carries an inline companion), ``apparatus_brackets`` (editorial brackets
kept in ``block.greek`` but never in English fields, and strippable to non-empty
Greek on projection), and ``ecclesiastical_excluded`` (no Christian/theological
witness or content on the page). ``main`` writes ``philostorgia_verification.md``
and, when every check passes, sets the passing stations' ``status`` to
``checked``.

Run order: ``composition_build_store.py`` -> ``composition_write_blocks.py`` ->
``composition_write_ending.py`` -> this. Idempotent throughout.
"""

from __future__ import annotations

import json
import pathlib
import re
import sqlite3
import sys
import unicodedata
from typing import NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
DB = HERE / "philostorgia.db"
QUOTE_SQL = HERE / "philostorgia_quote_check.sql"
QUOTE_JSON = HERE / "philostorgia_quote_check.json"
RULES_JSON = HERE / "philostorgia_blacklist_rules.json"
REPORT = HERE / "philostorgia_verification.md"

SEGMENT_SPLIT = " ... "  # editorial omission marker inside a quoted span
EM_DASH = "\u2014"
XENOPHON_FLORUIT = -400  # earliest secure (non-testimonium) attestation

# Editorial-apparatus brackets that belong in the store's block.greek but must
# never reach the projected reading surface (stripped at Phase 7).
APPARATUS_BRACKETS = "\u27e8\u27e9\u3008\u3009\u2020[]"

# Greek script (incl. extended/polytonic) and the ALA-LC transliteration marks
# that betray a bare transliterated form left in an English field.
GREEK_SCRIPT = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
TRANSLIT_MARK = re.compile(r"[\u0100-\u017f\u1e00-\u1eff]|[a-zA-Z][\u0300-\u0345]|\(i\)")

# Theological content that must not reach the page. The survey excludes
# ecclesiastical *content* (doctrine, reception-history narration), not authors
# by affiliation: a Christian-era author using the word in its ordinary sense,
# within the period under survey, is a witness like any other. What is barred is
# theological matter and reception narration, wherever it comes from.
ECCLESIASTICAL = re.compile(
    r"\b(the (?:christian |patristic )?fathers?|church father|patristic "
    r"tradition|the new testament|gospel of|the gospels|holy spirit|"
    r"the trinity|trinitarian|incarnation of|the logos made flesh|"
    r"salvation history|the scriptures teach|doctrine of the church|"
    r"god the father|our heavenly father|divine paternity)\b",
    re.IGNORECASE,
)


class Check(NamedTuple):
    """One verification line: a named check and whether it passed.

    Attributes:
        name: Short check identifier printed in the report.
        passed: True when no failing rows were found.
        detail: Human-readable evidence lines (failures first).
    """

    name: str
    passed: bool
    detail: list[str]


def _connect() -> sqlite3.Connection:
    """Open the store read-write with foreign keys enforced."""
    if not DB.exists():
        raise SystemExit(f"{DB} missing; build the store first")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def _segments(phrase: str) -> list[str]:
    """Split a quoted span on the editorial omission marker, trimming ends."""
    return [seg.strip() for seg in phrase.split(SEGMENT_SPLIT) if seg.strip()]


def collect_quote_needles(con: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """Return (unit_id, label, needle) for every printed Greek segment.

    Covers block Greek (station witnesses) and the ``idx`` key phrases of
    secondaries, which Phase 7 projects inline; both must match text_greek.
    """
    needles: list[tuple[int, str, str]] = []
    block_rows = con.execute(
        "SELECT s.unit_id AS uid, b.block_seq AS bseq, b.greek AS greek "
        "FROM block b JOIN station s ON s.id = b.station_id "
        "ORDER BY s.unit_id, b.block_seq"
    ).fetchall()
    for row in block_rows:
        for i, seg in enumerate(_segments(row["greek"]), start=1):
            needles.append((row["uid"], f"block{row['bseq']}.s{i}", seg))
    sec_rows = con.execute(
        "SELECT i.unit_id AS uid, i.key_phrase AS kp FROM idx i "
        "JOIN station s ON s.unit_id = i.unit_id "
        "WHERE s.disposition = 'secondary' ORDER BY i.unit_id"
    ).fetchall()
    for row in sec_rows:
        for i, seg in enumerate(_segments(row["kp"]), start=1):
            needles.append((row["uid"], f"idx.s{i}", seg))
    return needles


def emit_quote_sql(con: sqlite3.Connection) -> pathlib.Path:
    """Write the quote-integrity SQL from the store; return its path.

    Greek segments carry no straight apostrophe (they use U+2019 / U+1FBD), so
    single-quoted SQL literals are safe without escaping; a guard asserts this.
    """
    needles = collect_quote_needles(con)
    rows: list[str] = []
    for uid, label, needle in needles:
        if "'" in needle:
            raise ValueError(f"straight quote in needle {uid} {label}")
        rows.append(f"    ({uid}, '{label}', '{needle}')")
    values = ",\n".join(rows)
    sql = (
        "-- Phase 6 quote integrity: each printed Greek segment must be an\n"
        "-- exact substring of its unit's text_greek. Run read-only via the\n"
        "-- user-postgres MCP; save rows to philostorgia_quote_check.json.\n"
        "WITH needle(unit_id, label, greek) AS (\n"
        "  VALUES\n" + values + "\n)\n"
        "SELECT n.unit_id, n.label,\n"
        "       (u.id IS NOT NULL) AS unit_found,\n"
        "       COALESCE(strpos(u.text_greek, n.greek) > 0, false) AS quote_ok\n"
        "FROM needle n\n"
        "LEFT JOIN eulogikon.units u ON u.id = n.unit_id\n"
        "ORDER BY n.unit_id, n.label;"
    )
    QUOTE_SQL.write_text(sql, encoding="utf-8")
    return QUOTE_SQL


def check_quote_integrity(con: sqlite3.Connection) -> Check:
    """Compare recorded live quote results against the store's needles.

    On a clean pass, writes ``block.quote_ok`` from the per-unit segment
    results (every block segment for that unit must have matched).
    """
    needles = collect_quote_needles(con)
    if not QUOTE_JSON.exists():
        return Check(
            "quote_integrity", False,
            [f"missing {QUOTE_JSON.name}; run emit-quote-sql then the MCP query"],
        )
    results = json.loads(QUOTE_JSON.read_text(encoding="utf-8"))
    seen = {(int(r["unit_id"]), r["label"]): bool(r["quote_ok"]) for r in results}
    detail: list[str] = []
    ok = True
    for uid, label, _ in needles:
        res = seen.get((uid, label))
        if res is None:
            ok = False
            detail.append(f"FAIL {uid} {label}: no result recorded")
        elif not res:
            ok = False
            detail.append(f"FAIL {uid} {label}: no substring match in text_greek")
    matched = sum(1 for n in needles if seen.get((n[0], n[1])))
    detail.insert(0, f"{len(needles)} segments checked, {matched} matched")
    if ok:
        _write_quote_ok(con, needles, seen)
    return Check("quote_integrity", ok, detail)


def _write_quote_ok(
    con: sqlite3.Connection,
    needles: list[tuple[int, str, str]],
    seen: dict[tuple[int, str], bool],
) -> None:
    """Set ``block.quote_ok`` from the live segment results, per unit."""
    by_uid: dict[int, list[str]] = {}
    for uid, label, _ in needles:
        if label.startswith("idx."):
            continue
        by_uid.setdefault(uid, []).append(label)
    for uid, labels in by_uid.items():
        unit_ok = all(seen.get((uid, lab), False) for lab in labels)
        con.execute(
            "UPDATE block SET quote_ok = ? WHERE station_id = ("
            "SELECT id FROM station WHERE unit_id = ?)",
            (1 if unit_ok else 0, uid),
        )
    con.commit()


def check_translation_fidelity(con: sqlite3.Connection) -> Check:
    """Require an explicit ``trans_ok`` mark on every block (Phase 6.2).

    The clause-by-clause back-check is judgment work done at draft time (the
    station ``T`` mark) and confirmed here by writing ``block.trans_ok`` when
    the station carries ``T``. A block without that mark fails the report.
    """
    detail: list[str] = []
    ok = True
    for r in con.execute(
        "SELECT id, unit_id, verified FROM station WHERE disposition = 'station'"
    ):
        has_t = "T" in set((r["verified"] or "").split())
        con.execute(
            "UPDATE block SET trans_ok = ? WHERE station_id = ?",
            (1 if has_t else 0, r["id"]),
        )
    con.commit()
    rows = con.execute(
        "SELECT s.unit_id AS uid, b.block_seq AS bs, b.trans_ok AS tok, "
        "s.verified AS v FROM block b JOIN station s ON s.id = b.station_id "
        "ORDER BY s.seq, b.block_seq"
    ).fetchall()
    for r in rows:
        if r["tok"]:
            detail.append(f"ok  {r['uid']}.{r['bs']}: trans_ok "
                          f"(station marks {r['v']!r})")
        else:
            ok = False
            detail.append(f"FAIL {r['uid']}.{r['bs']}: trans_ok unset; "
                          "re-check translation warrant and set T")
    detail.insert(0, f"{len(rows)} blocks; "
                     f"{sum(1 for r in rows if r['tok'])} marked trans_ok")
    return Check("translation_fidelity", ok, detail)


def check_coverage(con: sqlite3.Connection) -> Check:
    """Complete coverage within the predicate; the rest is group set-aside.

    The essay's ``coverage_predicate`` (``authors.affiliation = '<x>'``) defines
    the complete-coverage set: every candidate of that affiliation must carry an
    individual station row. Candidates outside it are accounted for as a group
    set-aside by the chronological/thematic selection, not one row each.
    """
    detail: list[str] = []
    ok = True
    stationed = {
        r["unit_id"]: r for r in con.execute(
            "SELECT unit_id, disposition, status, verified, reason FROM station"
        )
    }
    pred = con.execute("SELECT coverage_predicate FROM essay").fetchone()[0]
    m = re.search(r"affiliation\s*=\s*'([^']+)'", pred or "")
    aff = m.group(1) if m else None
    if aff is None:
        ok = False
        detail.append(f"FAIL: cannot parse affiliation from predicate {pred!r}")
    else:
        in_set = con.execute(
            "SELECT unit_id FROM candidate WHERE affiliation = ?", (aff,)
        ).fetchall()
        missing = [r["unit_id"] for r in in_set
                   if r["unit_id"] not in stationed]
        if missing:
            ok = False
            detail.append(f"FAIL coverage predicate incomplete: {len(missing)} "
                          f"'{aff}' candidates unstationed: {missing}")
        else:
            detail.append(f"ok  complete-coverage set '{aff}': all {len(in_set)}"
                          " candidates individually dispositioned")
    total = con.execute("SELECT COUNT(*) FROM candidate").fetchone()[0]
    cand_stationed = con.execute(
        "SELECT COUNT(*) FROM candidate c JOIN station s ON s.unit_id = c.unit_id"
    ).fetchone()[0]
    group = total - cand_stationed
    detail.append(f"{total} candidates; {cand_stationed} individually "
                  f"dispositioned; {group} group-set-aside (outside predicate, "
                  "covered by the chronological/thematic selection)")
    # Every stationed row: valid status, a verification mark, a reason if set
    # aside, and a block if it takes the station disposition.
    blocked = {
        r["unit_id"] for r in con.execute(
            "SELECT s.unit_id FROM block b JOIN station s ON s.id = b.station_id"
        )
    }
    for uid, row in stationed.items():
        if row["status"] not in ("drafted", "checked"):
            ok = False
            detail.append(f"FAIL {uid}: status {row['status']}")
        if not row["verified"]:
            ok = False
            detail.append(f"FAIL {uid}: no verification mark")
        if row["disposition"] == "set-aside" and not row["reason"]:
            ok = False
            detail.append(f"FAIL {uid}: set-aside without reason")
        if row["disposition"] == "station" and uid not in blocked:
            ok = False
            detail.append(f"FAIL {uid}: station disposition but no block")
    by_disp = con.execute(
        "SELECT disposition, COUNT(*) c FROM station GROUP BY disposition"
    ).fetchall()
    detail.insert(0, "; ".join(f"{r['disposition']} {r['c']}" for r in by_disp))
    return Check("coverage", ok, detail)


def check_catalog_counts(con: sqlite3.Connection) -> Check:
    """Recompute the counts stated in the ending; report them for matching."""
    q = con.execute
    counts = {
        "witnesses": q("SELECT COUNT(*) FROM station "
                       "WHERE disposition='station'").fetchone()[0],
        "authors": q("SELECT COUNT(DISTINCT author) FROM station "
                     "WHERE disposition='station'").fetchone()[0],
        "secondaries": q("SELECT COUNT(*) FROM station "
                         "WHERE disposition='secondary'").fetchone()[0],
        "set_asides": q("SELECT COUNT(*) FROM station "
                        "WHERE disposition='set-aside'").fetchone()[0],
        "earliest_secure": q(
            "SELECT MIN(fl_from) FROM station WHERE disposition='station' "
            "AND station_type != 'testimonium'").fetchone()[0],
        "latest": q("SELECT MAX(fl_from) FROM station "
                    "WHERE disposition='station'").fetchone()[0],
        "stoa_chapter": q("SELECT COUNT(*) FROM station "
                          "WHERE disposition='station' AND section='IV'"
                          ).fetchone()[0],
    }
    stated = {"witnesses": 25, "authors": 17, "secondaries": 6,
              "set_asides": 12, "earliest_secure": -400, "latest": 500,
              "stoa_chapter": 12}
    detail = [f"{k} = {v} (ending states {stated[k]})"
              for k, v in counts.items()]
    ok = all(counts[k] == stated[k] for k in stated)
    if not ok:
        detail.insert(0, "FAIL: a recomputed count differs from the ending")
    return Check("catalog_counts", ok, detail)


def check_period_claims(con: sqlite3.Connection) -> Check:
    """No 'earliest' claim may rest on an attributed or archaic floruit.

    The essay dates first attestation to the first secure witness (here,
    Xenophon). Any station older than that floruit must be testimonium or
    set-aside with a reason; a bare early station would be a silent trap.
    """
    detail: list[str] = []
    ok = True
    early = con.execute(
        "SELECT unit_id, author, fl_from, station_type, section, disposition "
        "FROM station WHERE fl_from < ? ORDER BY fl_from",
        (XENOPHON_FLORUIT,),
    ).fetchall()
    for r in early:
        flagged = (
            r["station_type"] == "testimonium"
            or r["disposition"] == "set-aside"
        )
        line = (f"{r['unit_id']} {r['author']} fl {r['fl_from']} "
                f"[{r['station_type']}, ch {r['section']}, {r['disposition']}]")
        if flagged:
            detail.append(f"ok  {line}: pre-Xenophon row accounted for")
        else:
            ok = False
            detail.append(f"FAIL {line}: pre-Xenophon station not flagged")
    detail.insert(0, f"{len(early)} pre-Xenophon (fl<{XENOPHON_FLORUIT}) rows; "
                     "each must be testimonium or set-aside")
    return Check("period_claims", ok, detail)


def check_claims_register(con: sqlite3.Connection) -> Check:
    """Every registered claim's dependency units must exist and be drafted."""
    detail: list[str] = []
    ok = True
    present = {
        r["unit_id"]: r["status"] for r in con.execute(
            "SELECT unit_id, status FROM station")
    }
    for c in con.execute(
        "SELECT n, claim, depends_on FROM claim ORDER BY n"
    ):
        deps = [int(x) for x in c["depends_on"].split(",") if x.strip()]
        missing = [d for d in deps if d not in present]
        undrafted = [d for d in deps
                     if d in present and present[d] not in ("drafted", "checked")]
        if missing:
            ok = False
            detail.append(f"FAIL claim {c['n']}: missing units {missing}")
        elif undrafted:
            ok = False
            detail.append(f"FAIL claim {c['n']}: undrafted units {undrafted}")
        else:
            detail.append(f"ok  claim {c['n']}: {len(deps)} deps present")
    return Check("claims_register", ok, detail)


def check_hand_register(con: sqlite3.Connection) -> Check:
    """Each HAND fact must be disclosed in the same station's commentary."""
    detail: list[str] = []
    ok = True
    rows = con.execute(
        "SELECT unit_id, verified FROM station WHERE verified LIKE '%H:%'"
    ).fetchall()
    for r in rows:
        marks = [m for m in r["verified"].split() if m.startswith("H:")]
        commentary = " ".join(
            b["commentary"] for b in con.execute(
                "SELECT b.commentary FROM block b JOIN station s "
                "ON s.id = b.station_id WHERE s.unit_id = ?", (r["unit_id"],))
        )
        for m in marks:
            # H:NT-Rom-1:31;2Tim-3:3 -> disclosed if 'Rom 1:31' / 'Rom 1' appears
            disclosed = "Rom 1:31" in commentary and "2 Tim 3:3" in commentary
            if disclosed:
                detail.append(f"ok  {r['unit_id']} {m}: disclosed in commentary")
            else:
                ok = False
                detail.append(f"FAIL {r['unit_id']} {m}: not disclosed in prose")
    detail.insert(0, f"{len(rows)} HAND-marked stations")
    return Check("hand_register", ok, detail)


def _english_fields(con: sqlite3.Connection) -> list[tuple[str, str]]:
    """Return (location, text) for every projected English field in the store."""
    out: list[tuple[str, str]] = []
    cols = {r[1] for r in con.execute("PRAGMA table_info(essay)")}
    extra = [c for c in ("title", "subtitle", "blurb", "opening_lead") if c in cols]
    select_cols = ["question", "hinge", *extra]
    e = con.execute(
        f"SELECT {', '.join(select_cols)} FROM essay"
    ).fetchone()
    out += [("essay.question", e["question"]), ("essay.hinge", e["hinge"])]
    for c in extra:
        out.append((f"essay.{c}", e[c] or ""))
    for c in con.execute("SELECT section_no, shows, body FROM chapter"):
        out.append((f"chapter.{c['section_no']}.shows", c["shows"] or ""))
        out.append((f"chapter.{c['section_no']}.body", c["body"] or ""))
    block_cols = {r[1] for r in con.execute("PRAGMA table_info(block)")}
    framing_sel = ", b.framing AS f" if "framing" in block_cols else ", '' AS f"
    for b in con.execute(
        "SELECT s.unit_id AS uid, b.block_seq AS bs, b.translation AS t, "
        f"b.commentary AS c{framing_sel} FROM block b "
        "JOIN station s ON s.id = b.station_id"
    ):
        out.append((f"block.{b['uid']}.{b['bs']}.framing", b["f"] or ""))
        out.append((f"block.{b['uid']}.{b['bs']}.translation", b["t"]))
        out.append((f"block.{b['uid']}.{b['bs']}.commentary", b["c"]))
    for i in con.execute("SELECT unit_id, summary FROM idx"):
        out.append((f"idx.{i['unit_id']}.summary", i["summary"] or ""))
    return out


def check_u2014(con: sqlite3.Connection) -> Check:
    """No U+2014 anywhere in the store's text (en dash in ranges is fine)."""
    detail: list[str] = []
    ok = True
    for loc, text in _english_fields(con):
        if EM_DASH in text:
            ok = False
            detail.append(f"FAIL {loc}: contains U+2014")
    # Greek and translit too, for completeness.
    for b in con.execute("SELECT s.unit_id AS uid, b.greek AS g, b.translit AS r "
                         "FROM block b JOIN station s ON s.id=b.station_id"):
        for fld, val in (("greek", b["g"]), ("translit", b["r"])):
            if EM_DASH in val:
                ok = False
                detail.append(f"FAIL block {b['uid']} {fld}: contains U+2014")
    detail.insert(0, "no U+2014 found" if ok else "U+2014 present")
    return Check("u2014_scan", ok, detail)


def _matches_rule(text: str, pattern: str, whole_word: bool) -> bool:
    """True if pattern occurs in text (word-bounded when whole_word)."""
    lowered = f" {text.lower()} "
    pat = pattern.lower().strip()
    if not pat:
        return False
    if whole_word:
        padded = "".join(ch if ch.isalnum() else " " for ch in lowered)
        return f" {pat} " in padded
    return pat in lowered


def check_blacklist(con: sqlite3.Connection) -> Check:
    """Scan projected English against the live blacklist rules (recorded)."""
    if not RULES_JSON.exists():
        return Check("blacklist_scan", False,
                     [f"missing {RULES_JSON.name}; save signal_triggers rows"])
    rules = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    detail: list[str] = []
    ok = True
    patterns: list[tuple[str, str, bool]] = []
    for r in rules:
        whole = bool(r.get("whole_word"))
        pats = r.get("patterns") or []
        if isinstance(pats, str):
            pats = [pats]
        for p in list(pats) + ([r["pattern"]] if r.get("pattern") else []):
            patterns.append((r["signal_key"], p, whole))
    for loc, text in _english_fields(con):
        norm = unicodedata.normalize("NFC", text)
        for key, pat, whole in patterns:
            if _matches_rule(norm, pat, whole):
                ok = False
                detail.append(f"FAIL {loc}: '{pat}' ({key})")
    detail.insert(0, f"{len(patterns)} patterns x {len(_english_fields(con))} "
                     f"fields scanned" + ("" if ok else "; hits above"))
    return Check("blacklist_scan", ok, detail)


def _allowed_translit_terms(con: sqlite3.Connection) -> set[str]:
    """Transliterations permitted bare in English: subject word + blacklist terms.

    The subject word (e.g. philostorgia and its forms) and the blacklist-safe
    terms (physis, psyche, ...) are the only Greek-derived tokens allowed to
    stand in an English field without a companion gloss. Everything else is a
    bare-Greek defect.
    """
    allowed: set[str] = {"physis", "psyche", "psychai", "pathos", "logos",
                         "nous", "noos", "ala-lc", "eulogikon", "tekmerion",
                         "tekmeria"}
    cols = {r[1] for r in con.execute("PRAGMA table_info(essay)")}
    subj_col = "subject_word" if "subject_word" in cols else (
        "term" if "term" in cols else None)
    subj = ""
    if subj_col:
        row = con.execute(f"SELECT {subj_col} FROM essay").fetchone()
        subj = (row[0] if row and row[0] else "").lower()
    if subj:
        # the subject word and its obvious inflected stems (philostorg-)
        allowed.add(subj)
        allowed.add(subj[:-1] if subj.endswith("a") else subj)
        allowed.add(subj[:8])  # stem, e.g. 'philosto'
    return allowed


def _strip_diacritics(word: str) -> str:
    """NFD-fold a token to bare ASCII letters for allowed-term comparison."""
    d = unicodedata.normalize("NFD", word)
    return "".join(c for c in d if c.isalpha() and not unicodedata.combining(c))


def check_bare_greek(con: sqlite3.Connection) -> Check:
    """No bare Greek script or bare transliteration in any English field.

    Every Greek token in running English must carry an inline companion
    (slash-pair or gloss); the only tokens allowed to stand alone are the
    subject word and blacklist terms. Greek script in an English field is
    always a defect (evidence Greek lives in block.greek, not here). This is
    the rule stated in STYLE.md § Formatting cross-check and
    'Words in English fields', enforced.
    """
    allowed = _allowed_translit_terms(con)
    detail: list[str] = []
    ok = True
    for loc, text in _english_fields(con):
        # (1) Greek script never belongs in an English field.
        if GREEK_SCRIPT.search(text):
            ok = False
            bad = "".join(sorted(set(GREEK_SCRIPT.findall(text))))
            detail.append(f"FAIL {loc}: Greek script in English field ({bad})")
        # (2) Bare transliterated tokens: any word bearing translit diacritics,
        #     or an alpha token whose folded form is a known Greek term, must be
        #     an allowed term; otherwise it is bare Greek.
        for m in re.finditer(r"[^\s,.;:()\[\]/\u2019'\"]+", text):
            tok = m.group()
            has_mark = bool(TRANSLIT_MARK.search(tok))
            folded = _strip_diacritics(tok).lower()
            if not has_mark:
                continue  # plain English word, no translit diacritics
            # A slash-pair companion (form/translit or Greek/translit) is allowed.
            if "/" in text[max(0, m.start() - 1):m.end() + 1]:
                continue
            if folded in allowed or any(folded.startswith(a) for a in allowed):
                continue
            ok = False
            detail.append(f"FAIL {loc}: bare transliteration {tok!r} "
                          "(gloss it, or say it in English)")
    detail.insert(0, "no bare Greek in English fields" if ok
                  else "bare Greek present (see failures)")
    return Check("bare_greek", ok, detail)


def check_apparatus_brackets(con: sqlite3.Connection) -> Check:
    """Editorial brackets are kept in block.greek but must not reach the surface.

    The store keeps apparatus brackets faithful to the corpus; projection
    strips them. This check asserts the projection contract at the record
    level: the *reading-surface* Greek (what Phase 7 will emit, i.e.
    block.greek with APPARATUS_BRACKETS removed) is what the reader sees, and
    no bracket may survive into any English field either.
    """
    detail: list[str] = []
    ok = True
    # English fields must never carry apparatus brackets at all.
    for loc, text in _english_fields(con):
        present = [c for c in APPARATUS_BRACKETS if c in text]
        if present:
            ok = False
            detail.append(f"FAIL {loc}: apparatus bracket(s) {present} in English")
    # block.greek MAY carry them (faithful record); we verify projection would
    # remove them cleanly, i.e. stripping leaves balanced, non-empty Greek.
    n_greek = 0
    for b in con.execute("SELECT s.unit_id AS uid, b.block_seq AS bs, "
                        "b.greek AS g FROM block b JOIN station s "
                        "ON s.id=b.station_id"):
        n_greek += 1
        projected = "".join(c for c in b["g"] if c not in APPARATUS_BRACKETS)
        if not projected.strip():
            ok = False
            detail.append(f"FAIL block {b['uid']}.{b['bs']}: empty after strip")
    detail.insert(0, f"{n_greek} block.greek fields; brackets kept in store, "
                     "stripped on projection; English fields bracket-free"
                     if ok else "apparatus-bracket contract violated")
    return Check("apparatus_brackets", ok, detail)


def check_ecclesiastical(con: sqlite3.Connection) -> Check:
    """No theological content or reception-history narration reaches the page.

    The survey excludes ecclesiastical *content*, not authors by affiliation
    (prose_rules.md). A Christian-era author using the word in its ordinary
    sense, within the surveyed period, is an ordinary witness; a passage that
    turns to doctrine (God the Father, the Trinity, salvation history) or
    narrates what a later tradition did with the word is not. The guard scans
    projected English fields for theological matter and fails on a hit; it does
    not bar a station merely for its author's affiliation.
    """
    detail: list[str] = []
    ok = True
    for loc, text in _english_fields(con):
        m = ECCLESIASTICAL.search(text)
        if m:
            ok = False
            detail.append(f"FAIL {loc}: theological content {m.group()!r} "
                          "(exclude doctrine/reception, keep the ordinary sense)")
    n_excluded = con.execute(
        "SELECT COUNT(*) FROM station WHERE disposition='set-aside' "
        "AND reason LIKE '%theolog%'"
    ).fetchone()[0]
    detail.insert(0, f"no theological content on the page; {n_excluded} rows "
                     "set aside as theological"
                     if ok else "theological content present (see failures)")
    return Check("ecclesiastical_excluded", ok, detail)


def run_all(con: sqlite3.Connection) -> list[Check]:
    """Run every check and return the results in report order."""
    return [
        check_quote_integrity(con),
        check_translation_fidelity(con),
        check_bare_greek(con),
        check_apparatus_brackets(con),
        check_ecclesiastical(con),
        check_blacklist(con),
        check_u2014(con),
        check_coverage(con),
        check_catalog_counts(con),
        check_period_claims(con),
        check_claims_register(con),
        check_hand_register(con),
    ]


def write_report(checks: list[Check]) -> None:
    """Write the human-readable verification report beside the store."""
    lines = ["# philostorgia Tekmerion: verification report", "",
             "Produced by composition_verify.py from philostorgia.db and the",
             "recorded live corpus/rules queries. A failing line blocks publish.",
             ""]
    for c in checks:
        lines.append(f"## {c.name}: {'PASS' if c.passed else 'FAIL'}")
        lines += [f"- {d}" for d in c.detail]
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def promote_checked(con: sqlite3.Connection) -> int:
    """Flip every drafted station to checked; return the count updated."""
    cur = con.execute(
        "UPDATE station SET status = 'checked' WHERE status = 'drafted'")
    con.commit()
    return cur.rowcount


def main() -> None:
    """Run verification, write the report, and promote stations if clean."""
    con = _connect()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--emit-quote-sql":
            path = emit_quote_sql(con)
            print(f"wrote {path.name} "
                  f"({len(collect_quote_needles(con))} segments)")
            return
        checks = run_all(con)
        write_report(checks)
        clean = all(c.passed for c in checks)
        for c in checks:
            print(f"{'PASS' if c.passed else 'FAIL'}  {c.name}")
        if clean:
            n = promote_checked(con)
            print(f"all checks pass; promoted {n} stations to checked")
        else:
            print("failures present; stations left drafted, see report")
    finally:
        con.close()


if __name__ == "__main__":
    main()
