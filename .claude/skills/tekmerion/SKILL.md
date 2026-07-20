---
name: tekmerion
description: "Compose an extended Tekmerion, an evidence-led corpus essay on an Ancient Greek term or locus, for tekmeria.eulogikon.org. Use whenever the user wants to write, extend, or revise a long-form Tekmerion; turn diachronic-term-survey output or a corpus JSON into an essay; write an extended structured essay on any Greek term (philostorgia, phusis, prohairesis, dynamis, or any other); or asks for complete citation coverage of a term within an author, school, period, or domain. Also use when resuming a partly-composed Tekmerion. The composition is judgment work above the mechanical ceiling: excerpt selection, framing, commentary, and arrangement are editorial decisions taken per witness, never generated in one pass. This skill governs the procedure; STYLE.md governs the prose and stays authoritative."
---

# Tekmerion Composer (extended form)

Compose a long-form Tekmerion from survey data: a sequence of corpus
witnesses, each framed, cited, quoted in Greek, transliterated (ALA-LC),
translated, and commented, arranged along one trajectory so that one corpus
question and its hinge become visible. Works for any term or locus. Designed
for chunked, multi-session composition with generated, auditable tracking
artifacts, not single-shot generation.

**Scope.** Short-form Tekmeria are produced inside the EuGraphikon RAG system
and formatting-tweaked in Cursor; they do not need this procedure. This skill
is for the extended form: pieces whose candidate set runs to tens or hundreds
of units, where selection, coverage, and reference integrity cannot be held in
the head or in a conversation. It applies wherever the composition happens
(claude.ai, Claude Code, Cursor): the artifacts below are the state, not the
environment.

## Hard requirements

- **Live corpus DB access** (Postgres, eulogikon schema). Without it,
  composition cannot proceed past planning: nothing printable can be verified
  from a JSON snapshot. Say so and stop rather than compose unverifiable prose.
- **STYLE.md**, obtained fresh this session from wherever this composition has
  it (repo checkout, project files, upload). It is revised over time; do not
  work from memory of it. If absent, request it before composing.

## Division of authority

- **STYLE.md**: authoritative for the prose (what a Tekmerion is, balance,
  framing, evidence blocks, endings, citations).
- **This skill**: authoritative for procedure, tracking, and verification.
- **README.md** (tekmeria repo): file mechanics, URL composition, posts.json,
  sync/deploy, when publishing.
- **diachronic-term-survey** (separate skill): produces the survey data this
  skill consumes. If no survey exists for the term, run it first.

## Provenance classes

Every fact printed in the piece belongs to exactly one class, and the class
determines how it is verified:

- **QUOTE**: Greek text. Sourced only from `units.text_greek` fetched by
  unit id; verified by exact substring match (ellipsis segments piecewise).
- **CATALOG**: author names, work titles, wids, refs, URLs, periods, domains,
  affiliations, floruits, and every count or density in prose or tables.
  Sourced only from a query run at composition time; the query and its result
  are recorded in the ledger header or the verification report.
- **HAND**: anything the DB cannot supply: a locus inside a corrupted unit, a
  standard-collection fragment number (SVF etc.), an external parallel (e.g.
  a New Testament verse). Marked HAND in the ledger with its source stated;
  surfaced in the piece's caveats where it carries weight.

**The survey JSON is discovery only.** It tells you where to look. Its counts,
kwic windows, tags, and derived fields (era strings, floruits, work titles)
are never the source of anything printed: the JSON conflates tokens with
units, freezes a past DB state, and carries computed fields that can be stale.
Anything that reaches the reader is re-derived under one of the three classes
above.

## The ceiling

The mechanical layer (word search, KWIC windows, token counts, verification)
is the floor of this work, not the work. What cannot be mechanized, and must
be done per witness by judgment:

- **Excerption.** Which surrounding text goes in and which comes out. The
  excerpt must let a reader see what the word does in the line: its governing
  verb, its object, the words it is paired or contrasted with. A fixed
  character window is never an excerpt. Mark omissions with ellipses in the
  Greek and, where needed, in the translation.
- **Framing.** What kind of witness this is and what the line does locally.
- **Commentary.** What the passage does on the page, in the doing-verbs
  STYLE.md lists (pairs, distinguishes, equates, preserves, quotes, glosses,
  defines, contrasts, omits, redirects, collapses). No hypothetical
  speculation. Name a shift only when it is visible in the witnesses already
  placed.
- **Arrangement.** One trajectory that makes the hinge readable.

Never produce all witness blocks in a single generation pass. Compose stations
in batches of three to five, re-reading the draft from the top between batches.

## Tracking artifacts

Three files beside the draft; formats in `references/ledger.md`:

1. **`<term>_candidates.tsv`**: the exhaustive candidate set, generated by one
   recorded SQL query against the live DB, one row per unit. Never hand-edited.
   Header carries the query text, the run timestamp, and the headline counts.
   Regenerated and diffed on every resumed session so corpus drift surfaces
   immediately.
2. **`<term>_ledger.md`**: the curated station ledger, derived from the
   candidates file. Every station and secondary gets a row; dispositions and
   reasons live here; per-station verification records live here.
3. **`<term>_verification.md`**: the produced verification report (Phase 6).
   The piece is not done until this report exists and is clean. A check that
   is not recorded here did not happen.

At long-form scale, row-by-row hand reasoning over every candidate is not
required outside the complete-coverage set: group dispositions there (by
author, cluster, or period) are acceptable, provided every unit is covered by
some disposition and every selected station still gets its own ledger row.
Inside the complete-coverage set, dispositions are row-by-row, always.

## Procedure

### Phase 0: Load

1. Obtain and read STYLE.md in full (see Hard requirements).
2. Read the index of published Tekmeria and the working lexicon
   (eugraphikon_lexicon.md) for prior readings of this term or its
   neighbours. A reading already taken informs the new piece; it is never
   silently reinvented or contradicted.
3. Locate the survey data (diachronic-term-survey output or corpus JSON). If
   none exists, stop and run the survey skill first.
4. Confirm live DB access with a trivial query. No DB, no composition.

### Phase 1: Question, hinge, scope (user gate)

Draft one controlling corpus question with a hinge, per STYLE.md. Then
confirm with the user, before any prose:

- the question and hinge;
- the **complete-coverage set**, if any: the exact DB predicate for the subset
  the piece commits to including exhaustively (e.g.
  `authors.affiliation = 'stoic'`), as distinct from background and afterlife
  material selected by judgment;
- the trajectory type and rough length.

Do not proceed past this gate without confirmation.

### Phase 2: Candidates, then ledger

1. Generate `<term>_candidates.tsv` with one query over the whole word-family
   (all lemmata, privatives included), no filters. One row per unit. Record
   the query, timestamp, and counts in its header.
2. Derive the ledger. Dispositions:
   - **station**: will carry a full evidence block.
   - **secondary**: cited inline as parallel, cross-reference, or
     corpus-boundary note; not a block.
   - **set-aside**: excluded, with a stated reason. Within the
     complete-coverage set the only valid reasons are: proper name
     (lexical status, not the concept); duplicate station (same sentence at
     two addresses, e.g. a fragment-collection row and its source author:
     the source author's unit is the station, the collection number is a HAND
     note, counted once); corrupted or unsegmented unit (flag as corpus
     boundary, locus supplied by HAND); verbatim quotation of an included
     witness. Every set-aside inside the complete-coverage set is reported in
     the piece. Nothing is silently dropped.
   - **group set-asides** outside the complete-coverage set are permitted with
     a group reason (e.g. "late-antique epic afterlife, represented by two
     stations").
3. Station-type discipline (STYLE.md "Before composing"): doxography is not
   original speech; author floruit is not composition date for pseudepigrapha;
   test apparent early hits. Record station type per row.

### Phase 3: Trajectory

Order the stations. Chronology is often best, not mandatory; STYLE.md lists
the trajectory types. Mark in the ledger where the period shifts and where the
domain shifts (philosophy to medicine, household counsel to historiography):
each seam becomes a framing sentence or a section boundary, so the reader sees
the concept move between times and domains without being told a theory about
it. Write the section skeleton with the hinge stated early.

### Phase 4: Stations, in batches

For each station, in ledger order, three to five per batch:

1. **Fetch fresh** by unit id (QUOTE class). Never quote from the JSON, a
   previous session, or memory.
2. **Excerpt by judgment** (see The ceiling). Keep editorial brackets as the
   corpus yields them.
3. **Frame above**: the station and the local fact.
4. **Cite once, above the block**: linked work title + visible wid + ref.
   Title, wid, ref, and URL are CATALOG class: resolve them by query now, not
   from the JSON; never hand-guess a slug.
5. **Three lines**: Greek verbatim; ALA-LC transliteration
   (`references/transliteration.md`); English translation with no quotation
   marks around the whole line.
6. **Blacklist check, live**:

   ```sql
   SELECT signal_key, pattern, patterns, valence, payload, whole_word
   FROM eugraphikon.signal_triggers
   WHERE signal_key LIKE 'blacklist_%' AND enabled = true;
   ```

   Check every drafted English line against every row (whole-word where
   flagged); payload is the rule, patterns are examples. Where a Greek term
   would be flattened by any English rendering, leave it transliterated with a
   bracketed gloss.
7. **Comment after** the translation: what the line does on the page. A
   diachronic or cross-domain shift only if already visible. No speculation,
   no invented spokesman, no crowning verdict.
8. **Record verification in the ledger row**: the quoted span(s) matched
   against text_greek, the CATALOG fields confirmed, any HAND facts sourced.
   Status: drafted.

**Between batches**: re-read the draft from the top. The hinge is still the
center; no shift announced twice; every station earns its place; every
interpretive sentence would survive if the reader only checked the Greek block
above it. Fix before continuing. Update ledger statuses.

### Phase 5: Ending

Per STYLE.md Endings: restrained, evidential, checkable facts from the ledger;
at most one earned suggestive shape, then caveats. Every table and every count
is CATALOG class: recomputed by query at composition time, query recorded.
Standard caveats where they apply: partial vector coverage, author-level
floruit vs passage-level dating, corrupted units, station-type limits, strands
set aside by method.

### Phase 6: Verification report (produced, not asserted)

Write `<term>_verification.md`. It contains, explicitly:

1. **Quote integrity**: per station, unit id, each quoted Greek segment, and
   pass/fail of the exact substring match, run now.
2. **Coverage**: every candidates row accounted for: station (appears exactly
   once in the draft), secondary (cited), set-aside (reasoned; reported in the
   piece if inside the complete-coverage set), or group set-aside.
3. **Catalog integrity**: the queries reproducing every count, density, table
   row, wid link, and work title printed, with results matching the draft.
4. **HAND register**: every HAND fact, its source, and where the piece
   discloses it.
5. **Prose scans**: blacklist scan of the full English (live query); U+2014
   scan (must be zero; en dashes in ranges fine).

A failed line is fixed and the report regenerated. The piece is publishable
only with a clean report. If publishing, follow README (skeleton, posts.json,
sync script, --check).

## Session continuity

The candidates file, ledger, draft, and verification report are the state; the
conversation is not. On resuming: obtain STYLE.md; regenerate the candidates
query and diff against `<term>_candidates.tsv` (corpus drift surfaces here);
read the ledger and draft; continue from the first pending station. Never
recompose a verified station from memory; to change a drafted station,
re-fetch its unit first.

## Anti-patterns

- Excerpting by fixed window instead of judgment.
- Generating many witness blocks in one pass without re-reading between.
- Writing prose before the scope gate is confirmed and the ledger derived.
- Printing any fact sourced from the survey JSON.
- Treating token counts as attestation counts.
- Counting a fragment-collection row and its source author as two witnesses.
- Asserting a check without a line in the verification report.
- Announcing a tradition-wide event where naming what the passage does would
  do.
- Ending with a dictionary definition instead of a checkable landscape.

## Quick-reference checklist

- [ ] STYLE.md obtained and read this session; prior Tekmeria and lexicon
      consulted
- [ ] Live DB confirmed; question, hinge, complete-coverage predicate,
      trajectory confirmed by user
- [ ] Candidates file generated by one recorded query; ledger derived;
      dispositions row-by-row inside the coverage set, grouped with reasons
      outside it
- [ ] Duplicate stations counted once (source author is the station)
- [ ] Stations in batches with a top-to-bottom re-read between
- [ ] Every station: fetched fresh, excerpted by judgment, framed, cited once
      above, three lines, blacklist-checked, commented in doing-verbs,
      verification recorded in its ledger row
- [ ] Every printed fact QUOTE, CATALOG, or HAND; nothing from the JSON
- [ ] Period and domain seams surfaced as framing, not theory
- [ ] Set-asides within the coverage set reported in the piece
- [ ] Verification report produced and clean before the piece is called done
