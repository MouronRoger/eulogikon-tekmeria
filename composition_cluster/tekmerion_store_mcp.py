"""Tekmerion composition-store MCP server (stdio, local).

Exposes the per-term SQLite composition store under ``composition_cluster/`` as
typed, record-level operations, so an agent composes and verifies a Tekmerion
through the store's own state machine rather than by hand-editing writer
modules or, worse, hand-authoring HTML.

This is the "single-owned capability with an explicit state machine" the
tekmerion skill describes: every station moves pending -> drafted -> checked,
and it moves only through the operations here. The server is the one write
path; the store is the one source of truth.

Design notes:

* **Local stdio, synchronous.** The store is a local SQLite file. There is no
  network and no async I/O; tools are plain synchronous functions returning
  JSON text. That is the honest shape for a file-backed capability.
* **Term-scoped.** One store per term (``<term>.db``). Every tool takes a
  ``term`` and resolves ``COMPOSITION_DIR / f"{term}.db"``. The composition
  directory is fixed by ``TEKMERION_COMPOSITION_DIR`` (falling back to a path
  beside this file), never taken from tool input, so a caller cannot point the
  server at an arbitrary database.
* **Deterministic scripts stay authoritative.** ``build_store``,
  ``run_verification``, and ``project`` shell the committed
  ``composition_*.py`` modules rather than reimplementing them: one
  implementation, invoked, not duplicated. The record-level write tools
  operate on the store directly for the fields the writers would set, so
  composition can happen live without editing Python.
* **Verification is the gate.** ``run_verification`` runs the real
  ``composition_verify.py`` (blacklist, bare-Greek, apparatus-bracket,
  ecclesiastical, quote, coverage, and the rest) and returns the full report;
  ``project`` refuses unless the store is clean and every station is checked
  (the script's own guard). Nothing here can flip a station to checked except
  a clean verification run.
"""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import subprocess
import sys
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Location: fixed composition directory, term-scoped stores. Never from input.
# --------------------------------------------------------------------------- #

_DEFAULT_DIR = pathlib.Path(__file__).resolve().parent
COMPOSITION_DIR = pathlib.Path(
    os.environ.get("TEKMERION_COMPOSITION_DIR", str(_DEFAULT_DIR))
).resolve()

# Committed deterministic scripts (invoked, never reimplemented).
BUILD_SCRIPT = "composition_build_store.py"
VERIFY_SCRIPT = "composition_verify.py"
PROJECT_SCRIPT = "composition_project.py"

mcp = FastMCP("tekmerion_store_mcp")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _db_path(term: str) -> pathlib.Path:
    """Resolve the store path for a term, guarding against path escapes."""
    safe = "".join(c for c in term if c.isalnum() or c in ("_", "-"))
    if not safe or safe != term:
        raise ValueError(
            f"invalid term {term!r}: use letters, digits, underscore, hyphen"
        )
    path = (COMPOSITION_DIR / f"{term}.db").resolve()
    if path.parent != COMPOSITION_DIR:
        raise ValueError("term resolves outside the composition directory")
    return path


def _connect(term: str, *, write: bool) -> sqlite3.Connection:
    """Open a term's store; read-only unless write is requested."""
    path = _db_path(term)
    if not path.exists():
        raise FileNotFoundError(
            f"store for {term!r} not found at {path.name}; run build_store"
        )
    if write:
        con = sqlite3.connect(path)
        con.execute("PRAGMA foreign_keys = ON")
    else:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    """Materialise a cursor as a list of plain dicts."""
    return [dict(r) for r in cur.fetchall()]


def _run_script(term: str, script: str, *args: str) -> dict[str, Any]:
    """Run a committed composition script for a term and capture its output.

    The scripts are per-term prototypes (they hardcode the term's DB name), so
    ``term`` selects which script directory layout to run; today there is one
    set beside the store. Returns exit code, stdout, and stderr.
    """
    script_path = COMPOSITION_DIR / script
    if not script_path.exists():
        raise FileNotFoundError(f"{script} not found in {COMPOSITION_DIR}")
    proc = subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=str(COMPOSITION_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {
        "script": script,
        "args": list(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _ok(payload: dict[str, Any]) -> str:
    """Serialise a success payload."""
    return json.dumps({"ok": True, **payload}, ensure_ascii=False, indent=2)


def _err(message: str, **extra: Any) -> str:
    """Serialise an actionable error payload."""
    return json.dumps(
        {"ok": False, "error": message, **extra}, ensure_ascii=False, indent=2
    )


# --------------------------------------------------------------------------- #
# Input models
# --------------------------------------------------------------------------- #


class TermInput(BaseModel):
    """A bare term selector."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    term: str = Field(..., description="Essay term, e.g. 'philostorgia'",
                      min_length=1, max_length=64)


class QueryInput(BaseModel):
    """A read-only SQL query against a term's store."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    sql: str = Field(..., description="A single read-only SELECT statement",
                    min_length=1, max_length=4000)


class UnitInput(BaseModel):
    """A term plus a unit id (a passage anchor)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    unit_id: int = Field(..., description="eulogikon.units.id of the passage",
                        ge=1)


class WriteBlockInput(BaseModel):
    """One evidence block written into a station's heavy layer, as Markdown.

    English fields are Markdown (``*term*`` for emphasis), never HTML. The Greek
    is verbatim from the corpus (apparatus brackets kept here; projection strips
    them). Warrant, gloss, and blacklist rules are enforced by run_verification,
    not here: this tool records what you compose; the verifier gates it.
    """

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    unit_id: int = Field(..., description="Station unit id (must be a station "
                        "disposition row)", ge=1)
    block_seq: int = Field(default=1, description="1-based block order within "
                          "the station (a rich witness may carry several)",
                          ge=1, le=20)
    framing: str = Field(default="", description="Markdown frame above the "
                        "citation (who, what text, local hook); may be empty",
                        max_length=4000)
    greek: str = Field(..., description="Verbatim Greek excerpt, an exact "
                      "substring of the unit's text_greek (apparatus brackets "
                      "kept; ellipsis ' ... ' between omitted spans)",
                      min_length=1, max_length=8000)
    translit: str = Field(..., description="ALA-LC transliteration of the same "
                         "span", min_length=1, max_length=8000)
    translation: str = Field(..., description="English translation, warrant-"
                            "faithful, no square brackets, no bare Greek",
                            min_length=1, max_length=8000)
    commentary: str = Field(..., description="Markdown commentary: what the "
                           "line does in the history, doing-verbs, no crowning "
                           "verdict", min_length=1, max_length=8000)


class MarksInput(BaseModel):
    """Verification marks and status for a station row."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    unit_id: int = Field(..., description="Station unit id", ge=1)
    verified: str = Field(..., description="Space-joined marks: Q (quote), C "
                         "(catalog), T (translation warrant), H:<src> (hand). "
                         "e.g. 'Q C T' or 'Q C T H:SVF-iii-731'",
                         max_length=200)
    status: str = Field(default="drafted", description="pending | drafted | "
                       "checked (checked is set only by a clean verification "
                       "run; use drafted here)")


class DispositionInput(BaseModel):
    """Change a station's disposition (and reason for set-aside)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    unit_id: int = Field(..., description="Station unit id", ge=1)
    disposition: str = Field(..., description="station | secondary | set-aside")
    reason: Optional[str] = Field(default=None, description="Required for "
                                 "set-aside: the reason (e.g. "
                                 "'ecclesiastical-excluded', 'duplicate-station "
                                 "of 2120777', 'proper-name', 'dating trap: ...')",
                                 max_length=500)


class FixIndexInput(BaseModel):
    """Correct a station's index line (light layer)."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")
    term: str = Field(..., description="Essay term", min_length=1, max_length=64)
    unit_id: int = Field(..., description="Station unit id", ge=1)
    key_phrase: Optional[str] = Field(default=None, description="Corrected key "
                                     "Greek phrase (must match text_greek if it "
                                     "may be projected inline)", max_length=2000)
    summary: Optional[str] = Field(default=None, description="Corrected English "
                                  "doing-verb summary (no bare Greek, no 'by "
                                  "nature': use by *physis*)", max_length=2000)


# --------------------------------------------------------------------------- #
# Read tools
# --------------------------------------------------------------------------- #


@mcp.tool(
    name="store_status",
    annotations={"title": "Store status", "readOnlyHint": True,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def store_status(params: TermInput) -> str:
    """Summarise a term's composition store: essay, phase, and station tallies.

    Reports the essay question/hinge, the coverage predicate, per-disposition
    and per-status station counts, block and index counts, and whether a
    verification report exists beside the store. Use this first on any resume
    to see where composition stands.
    """
    try:
        con = _connect(params.term, write=False)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        essay = con.execute(
            "SELECT term, question, hinge, coverage_predicate, trajectory_type "
            "FROM essay"
        ).fetchone()
        by_disp = _rows(con.execute(
            "SELECT disposition, COUNT(*) n FROM station GROUP BY disposition"))
        by_status = _rows(con.execute(
            "SELECT status, COUNT(*) n FROM station GROUP BY status"))
        n_blocks = con.execute("SELECT COUNT(*) FROM block").fetchone()[0]
        n_idx = con.execute("SELECT COUNT(*) FROM idx").fetchone()[0]
        n_cand = con.execute("SELECT COUNT(*) FROM candidate").fetchone()[0]
    finally:
        con.close()
    report = _db_path(params.term).with_name(
        f"{params.term}_verification.md")
    return _ok({
        "term": essay["term"],
        "question": essay["question"],
        "hinge": essay["hinge"],
        "coverage_predicate": essay["coverage_predicate"],
        "trajectory_type": essay["trajectory_type"],
        "candidates": n_cand,
        "stations_by_disposition": {r["disposition"]: r["n"] for r in by_disp},
        "stations_by_status": {r["status"]: r["n"] for r in by_status},
        "blocks": n_blocks,
        "index_lines": n_idx,
        "verification_report_present": report.exists(),
    })


@mcp.tool(
    name="get_index",
    annotations={"title": "Get narrative index", "readOnlyHint": True,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def get_index(params: TermInput) -> str:
    """Return the whole light-layer index in trajectory order (the argument arc).

    This is the structural memory: one line per station (citation, key Greek
    phrase, doing-verb summary), plus the hinge and the claims register. Read
    it before composing any chunk; it is small enough to hold the whole arc in
    context and replaces re-reading the draft.
    """
    try:
        con = _connect(params.term, write=False)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        idx = _rows(con.execute(
            "SELECT seq, unit_id, citation, key_phrase, summary FROM idx "
            "ORDER BY seq"))
        hinge = con.execute("SELECT hinge FROM essay").fetchone()["hinge"]
        claims = _rows(con.execute(
            "SELECT n, claim, depends_on, section, status FROM claim ORDER BY n"))
        sections = _rows(con.execute(
            "SELECT section_no, title, shows FROM chapter ORDER BY section_no"))
    finally:
        con.close()
    return _ok({"hinge": hinge, "sections": sections, "index": idx,
                "claims_register": claims})


@mcp.tool(
    name="get_station",
    annotations={"title": "Get station", "readOnlyHint": True,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def get_station(params: UnitInput) -> str:
    """Return one station row with its blocks and its index line.

    Full detail for a single witness: disposition, verification marks, status,
    every evidence block (framing/greek/translit/translation/commentary), and
    the light-layer summary. Use before revising a block.
    """
    try:
        con = _connect(params.term, write=False)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        st = con.execute(
            "SELECT * FROM station WHERE unit_id = ?", (params.unit_id,)
        ).fetchone()
        if st is None:
            return _err(f"no station for unit_id {params.unit_id}")
        blocks = _rows(con.execute(
            "SELECT block_seq, framing, greek, translit, translation, "
            "commentary, quote_ok, trans_ok FROM block WHERE station_id = ? "
            "ORDER BY block_seq", (st["id"],)))
        idx = con.execute(
            "SELECT citation, key_phrase, summary FROM idx WHERE unit_id = ?",
            (params.unit_id,)).fetchone()
    finally:
        con.close()
    return _ok({"station": dict(st), "blocks": blocks,
                "index": dict(idx) if idx else None})


@mcp.tool(
    name="query",
    annotations={"title": "Read-only SQL", "readOnlyHint": True,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def query(params: QueryInput) -> str:
    """Run one read-only SELECT against a term's store and return the rows.

    For ad hoc inspection the typed tools do not cover. The connection is
    opened read-only, so writes fail; a statement that is not a single SELECT
    is rejected before execution.
    """
    stripped = params.sql.strip().rstrip(";").strip()
    low = stripped.lower()
    if not low.startswith("select") and not low.startswith("with"):
        return _err("only a single SELECT (or WITH ... SELECT) is allowed")
    if ";" in stripped:
        return _err("only one statement is allowed (no ';')")
    try:
        con = _connect(params.term, write=False)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        rows = _rows(con.execute(stripped))
    except sqlite3.Error as e:
        return _err(f"SQL error: {e}")
    finally:
        con.close()
    return _ok({"row_count": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# Write tools (record-level composition)
# --------------------------------------------------------------------------- #


@mcp.tool(
    name="write_block",
    annotations={"title": "Write evidence block", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def write_block(params: WriteBlockInput) -> str:
    """Insert or replace one evidence block on a station (idempotent by seq).

    The station must exist and hold the ``station`` disposition. Writing does
    not verify: it records the composed Markdown/Greek. Run run_verification to
    check quote integrity, translation warrant, blacklist, bare-Greek,
    apparatus brackets, and the rest, and to move the station to checked.
    Re-writing the same (unit_id, block_seq) overwrites that block.
    """
    try:
        con = _connect(params.term, write=True)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        st = con.execute(
            "SELECT id, disposition FROM station WHERE unit_id = ?",
            (params.unit_id,)).fetchone()
        if st is None:
            return _err(f"no station for unit_id {params.unit_id}")
        if st["disposition"] != "station":
            return _err(
                f"unit {params.unit_id} is '{st['disposition']}', not a "
                "station; only station-disposition rows carry blocks. Use "
                "set_disposition first if it should be a station.")
        cols = {r[1] for r in con.execute("PRAGMA table_info(block)")}
        if "framing" not in cols:
            con.execute("ALTER TABLE block ADD COLUMN framing TEXT")
        con.execute(
            "DELETE FROM block WHERE station_id = ? AND block_seq = ?",
            (st["id"], params.block_seq))
        con.execute(
            "INSERT INTO block (station_id, block_seq, framing, greek, "
            "translit, translation, commentary) VALUES (?,?,?,?,?,?,?)",
            (st["id"], params.block_seq, params.framing, params.greek,
             params.translit, params.translation, params.commentary))
        con.commit()
        n = con.execute(
            "SELECT COUNT(*) FROM block WHERE station_id = ?", (st["id"],)
        ).fetchone()[0]
    finally:
        con.close()
    return _ok({"unit_id": params.unit_id, "block_seq": params.block_seq,
                "blocks_on_station": n,
                "note": "recorded; run_verification gates it"})


@mcp.tool(
    name="set_station_marks",
    annotations={"title": "Set verification marks", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def set_station_marks(params: MarksInput) -> str:
    """Set a station's verification marks and status (draft-time bookkeeping).

    Records the Q/C/T/H marks you assert at draft time and sets status
    (normally 'drafted'). This does not itself verify; 'checked' is reserved
    for a clean run_verification, which sets it. Setting status='checked' here
    is refused.
    """
    if params.status == "checked":
        return _err("status 'checked' is set only by a clean verification "
                    "run; use 'drafted' here and call run_verification")
    if params.status not in ("pending", "drafted"):
        return _err("status must be 'pending' or 'drafted'")
    try:
        con = _connect(params.term, write=True)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        cur = con.execute(
            "UPDATE station SET verified = ?, status = ? WHERE unit_id = ?",
            (params.verified, params.status, params.unit_id))
        con.commit()
        if cur.rowcount == 0:
            return _err(f"no station for unit_id {params.unit_id}")
    finally:
        con.close()
    return _ok({"unit_id": params.unit_id, "verified": params.verified,
                "status": params.status})


@mcp.tool(
    name="set_disposition",
    annotations={"title": "Set disposition", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def set_disposition(params: DispositionInput) -> str:
    """Change a station's disposition; require a reason for set-aside.

    station | secondary | set-aside. A set-aside must carry a reason (it is
    recorded in the store and checked by verification). Use this to exclude a
    christian-affiliated candidate ('ecclesiastical-excluded'), mark a
    duplicate or dating trap, or promote a row to a full station.
    """
    if params.disposition not in ("station", "secondary", "set-aside"):
        return _err("disposition must be station | secondary | set-aside")
    if params.disposition == "set-aside" and not (params.reason or "").strip():
        return _err("set-aside requires a reason")
    try:
        con = _connect(params.term, write=True)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        cur = con.execute(
            "UPDATE station SET disposition = ?, reason = ? WHERE unit_id = ?",
            (params.disposition,
             params.reason if params.disposition == "set-aside" else None,
             params.unit_id))
        con.commit()
        if cur.rowcount == 0:
            return _err(f"no station for unit_id {params.unit_id}")
        # A set-aside carries no blocks on the reading surface; drop any.
        if params.disposition == "set-aside":
            sid = con.execute("SELECT id FROM station WHERE unit_id = ?",
                             (params.unit_id,)).fetchone()[0]
            con.execute("DELETE FROM block WHERE station_id = ?", (sid,))
            con.commit()
    finally:
        con.close()
    return _ok({"unit_id": params.unit_id, "disposition": params.disposition,
                "reason": params.reason if params.disposition == "set-aside"
                else None})


@mcp.tool(
    name="fix_index",
    annotations={"title": "Fix index line", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def fix_index(params: FixIndexInput) -> str:
    """Correct a station's light-layer index line (key phrase and/or summary).

    The summary is English (no bare Greek, 'by *physis*' not 'by nature'); the
    key phrase, if it may be projected inline for a secondary, must match
    text_greek. At least one field must be supplied.
    """
    if params.key_phrase is None and params.summary is None:
        return _err("supply key_phrase and/or summary")
    try:
        con = _connect(params.term, write=True)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e))
    try:
        sets, vals = [], []
        if params.key_phrase is not None:
            sets.append("key_phrase = ?")
            vals.append(params.key_phrase)
        if params.summary is not None:
            sets.append("summary = ?")
            vals.append(params.summary)
        vals.append(params.unit_id)
        cur = con.execute(
            f"UPDATE idx SET {', '.join(sets)} WHERE unit_id = ?", vals)
        con.commit()
        if cur.rowcount == 0:
            return _err(f"no index line for unit_id {params.unit_id}")
    finally:
        con.close()
    return _ok({"unit_id": params.unit_id, "updated": sets})


# --------------------------------------------------------------------------- #
# Pipeline tools (invoke the committed deterministic scripts)
# --------------------------------------------------------------------------- #


@mcp.tool(
    name="build_store",
    annotations={"title": "Build store (scaffold)", "readOnlyHint": False,
                 "destructiveHint": True, "idempotentHint": True,
                 "openWorldHint": False},
)
def build_store(params: TermInput) -> str:
    """Run composition_build_store.py: (re)create the scaffold from candidates.

    Drops and rebuilds essay, chapters, candidates, stations, idx, and claims;
    leaves every station pending with zero blocks. Destructive to the store's
    scaffold tables (not to the committed writer modules). Run once at the
    start, or on a resumed session to pick up corpus drift.
    """
    try:
        result = _run_script(params.term, BUILD_SCRIPT)
    except FileNotFoundError as e:
        return _err(str(e))
    return _ok(result)


@mcp.tool(
    name="run_verification",
    annotations={"title": "Run verification", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": False,
                 "openWorldHint": False},
)
def run_verification(params: TermInput) -> str:
    """Run composition_verify.py and return the full report and pass/fail.

    Runs every check automatically: quote integrity, translation fidelity,
    bare-Greek, apparatus brackets, ecclesiastical exclusion, blacklist,
    U+2014, coverage, catalog counts, period claims, claims register, HAND.
    On a fully clean run the script promotes drafted stations to checked. The
    quote-integrity check needs the live-corpus results file; if it is missing
    this tool reports which step to run (emit the SQL, run it via the corpus
    Postgres MCP, save the JSON), then call again.
    """
    try:
        result = _run_script(params.term, VERIFY_SCRIPT)
    except FileNotFoundError as e:
        return _err(str(e))
    report_path = COMPOSITION_DIR / f"{params.term}_verification.md"
    report = report_path.read_text(encoding="utf-8") if report_path.exists() \
        else None
    clean = result["returncode"] == 0 and "FAIL" not in (result["stdout"] or "")
    return _ok({**result, "clean": clean, "report": report})


@mcp.tool(
    name="emit_quote_sql",
    annotations={"title": "Emit quote-check SQL", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def emit_quote_sql(params: TermInput) -> str:
    """Run composition_verify.py --emit-quote-sql and return the generated SQL.

    Writes the quote-integrity SQL (needles byte-exact from the store) beside
    the store. Run the returned SQL read-only via the corpus Postgres MCP and
    save its rows to ``<term>_quote_check.json``; then run_verification will
    consume them for the quote-integrity check.
    """
    try:
        result = _run_script(params.term, VERIFY_SCRIPT, "--emit-quote-sql")
    except FileNotFoundError as e:
        return _err(str(e))
    sql_path = COMPOSITION_DIR / f"{params.term}_quote_check.sql"
    sql = sql_path.read_text(encoding="utf-8") if sql_path.exists() else None
    return _ok({**result, "quote_sql": sql,
                "next": f"run this SQL via the corpus Postgres MCP; save rows "
                        f"to {params.term}_quote_check.json"})


@mcp.tool(
    name="project",
    annotations={"title": "Project to HTML", "readOnlyHint": False,
                 "destructiveHint": False, "idempotentHint": True,
                 "openWorldHint": False},
)
def project(params: TermInput) -> str:
    """Run composition_project.py: convert the store to HTML deterministically.

    Refuses (via the script's own guard) unless every station/secondary is
    checked, i.e. verification is clean. Strips apparatus brackets, converts
    Markdown emphasis, composes citations from CATALOG, recomputes tables. The
    conversion carries no editorial judgment; fix findings in the records and
    re-run, never in the HTML.
    """
    try:
        result = _run_script(params.term, PROJECT_SCRIPT)
    except FileNotFoundError as e:
        return _err(str(e))
    return _ok(result)


if __name__ == "__main__":
    mcp.run()
