---
name: tekmerion
description: "Compose an extended Tekmerion, an evidence-led corpus essay on an Ancient Greek term or locus, for tekmeria.eulogikon.org. Use whenever the user wants to write, extend, or revise a long-form Tekmerion; turn diachronic-term-survey output or a corpus JSON into an essay; write an extended structured essay on any Greek term (philostorgia, phusis, prohairesis, dynamis, or any other); or asks for complete citation coverage of a term within an author, school, period, or domain. Also use when resuming a partly-composed Tekmerion. The composition is judgment work above the mechanical ceiling: excerpt selection, framing, commentary, and arrangement are editorial decisions taken per witness, never generated in one pass. This skill governs the procedure; STYLE.md governs the prose and stays authoritative."
---

# Tekmerion Composer (extended form)

Compose a long-form Tekmerion from survey data: a sequence of corpus
witnesses, each framed, cited, quoted in Greek, transliterated (ALA-LC),
translated, and commented, arranged along one trajectory so that one corpus
question and its hinge become visible. Works for any term or locus. Designed
for chunked, multi-session composition against a single-owned, auditable
record store, not single-shot generation. The composed text is **Markdown**
in the store's fields; **HTML is produced only by a later, deterministic
conversion** (Phase 7). The agent never writes HTML by hand.

## What this is (read first)

A Tekmerion is **history of ideas through the corpus**: how a Greek term or
locus was used, how its sense shifted, what authors did with it. The reader
learns *philostorgía* (or whatever the term is) by walking the witnesses in
order, not by reading philology.

**You are not writing:**

- Manuscript or digitisation notes (split sigmas, quote-match honesty, corpus
  boundaries under every station)
- Apparatus (square brackets in translations, `(háma ... háma)`, parenthetical
  grammar labels where English would do)
- A station checklist ("this chapter shows…", station-type audit tags, index
  lines pasted onto the page)

**You are writing:**

- Prose a curious reader would keep reading: what this witness adds to the
  story, in plain English
- Framing that orients (who, when, what kind of text) without sounding like
  catalogue metadata
- Commentary that says what the line *does* in the argument: pairs, contrasts,
  moralises, tests, disperses (STYLE.md doing-verbs)
- Greek terms in English fields: the **subject word** of the essay
  (*philostorgia*) and blacklist terms (*physis*, *psyche*). Everything else
  is plain English (the wise, cherishing, starting-point). The transliteration
  line keeps case forms that mirror the Greek

Verification (QUOTE, CATALOG, HAND) protects trust; it is **not** the voice of
the piece. Floruit traps, duplicates, and digitisation quirks are resolved in
the store (set-aside, re-dated first attestation); they do not become a public
chapter or trap-labelled cite lines. The ending may carry a few reader-facing
caveats; external parallels (HAND) are disclosed once there if needed.

**Tone:** Match the published Tekmeria on tekmeria.eulogikon.org (e.g. what
Marcus prays for, ἀεργοί and ἐνεργοί): informative, interesting, evidence-led.
When in doubt, read one exemplar before drafting blocks. Voice guidelines:
`composition_cluster/craft.md` (guidelines, not a compliance checklist).

**Scope.** Short-form Tekmeria are produced inside the EuGraphikon RAG system
and formatting-tweaked in Cursor; they do not need this procedure. This skill
is for the extended form: pieces whose candidate set runs to tens or hundreds
of units, where selection, coverage, and reference integrity cannot be held in
the head or in a conversation. It applies wherever the composition happens
(claude.ai, Claude Code, Cursor): the store below is the state, not the
environment.

## The output is Markdown records, not HTML

The agent composes into the structured record set (the composition store
below), writing each English field in **Markdown**, never directly into essay
HTML. Keeping the output as cross-referenced Markdown records: each witness's
Greek, transliteration, translation, commentary, and its place in the
argument, is what keeps the eye on the narrative rather than on presentation.
The HTML page is a **later, deterministic conversion** of the records
(Phase 7): Markdown fields become HTML by a fixed projection, apparatus
brackets are stripped, citations are composed from CATALOG fields, and no
editorial judgment is exercised. When the records are correct and fully
cross-referenced, the conversion carries no decisions and can be re-run at
will. Compose the argument in Markdown; let the machine make the markup.

Markdown, not HTML, in every English field: use `*term*` for emphasis (the
subject word, *physis*), `>` is not needed (the Greek block is a record field,
not a quote the agent types), and never hand-write `<p>`, `<em>`,
`<blockquote>`, or `<span class="cite">`. The projector emits those.

## Hard requirements

- **Live corpus DB access** (Postgres, eulogikon schema). Without it,
  composition cannot proceed past planning: nothing printable can be verified
  from a JSON snapshot. Say so and stop rather than compose unverifiable prose.
- **STYLE.md**, obtained fresh this session (balance, framing, endings, citations).
  Do not work from memory of it. If absent, request it before composing.
- **Composition phase only:** read
  `STYLE.md` § **Formatting cross-check** for all field formatting rules;
  `composition_cluster/prose_rules.md` for composition-only boundaries;
  `composition_cluster/craft.md` for voice guidelines. If absent, request them
  before writing blocks.

## Division of authority

- **STYLE.md**: authoritative for published-form prose (what a Tekmerion is,
  balance, framing, evidence blocks, endings, citations) and **Formatting
  cross-check** (the single mechanical checklist).
- **composition_cluster/prose_rules.md**: composition-only boundaries
  (ecclesiastical exclusion, translation warrant, blacklist compose-time
  checks). Does not restate formatting cross-check.
- **composition_cluster/craft.md**: voice guidelines for composition (read
  the exemplars; avoid apparatus and philology on the page). Not published-form
  authority.
- **composition_cluster/README.md**: phase map (pre / composition / post) and
  script entry points.
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
  are recorded in the store (the candidate query header, the station row) or
  the verification report.
- **HAND**: anything the DB cannot supply: a locus inside a corrupted unit, a
  standard-collection fragment number (SVF etc.), an external parallel (e.g.
  a New Testament verse). Marked HAND in the store with its source stated;
  surfaced in the piece's caveats where it carries weight.

**The survey JSON is discovery only.** It tells you where to look. Its counts,
kwic windows, tags, and derived fields (era strings, floruits, work titles)
are never the source of anything printed: the JSON conflates tokens with
units, freezes a past DB state, and carries computed fields that can be stale.
Anything that reaches the reader is re-derived under one of the three classes
above.

## Identity and anchors

Works and authors are settled: `eul_wid` and `eul_aid` are the only
identifiers, and a display string, filename, or URL is never one.
Passage identity is **not** settled: `units.id` is a session-scoped pointer
for re-fetching text, re-keyed whenever a passage moves.

So every record this skill produces that outlives its session, the store
above all, carries the durable anchor set: `eul_wid` + quoted Greek +
`legacy_reference`. The rule, its reasoning, and what happens at cutover are
owned by `.eukoine/interim_head_citation.md` §4; read it there rather than
looking for a summary here.

Reads target the published `corpus_api` surface, not the physical
`eulogikon.*` tables, which are private and mid-rename (`units` dissolves into
`sid_text` plus `legacy_reference` overlays). Present-tense gap: the queries in
this skill and in the committed candidates files still read the physical
tables. Rewriting them requires a session with live DB access to verify the
interim `corpus_api` surface carries every column they need.

## The ceiling

The mechanical layer (word search, KWIC windows, token counts, verification)
is the floor of this work, not the work. What cannot be mechanized, and must
be done per witness by judgment:

- **Excerption.** Which surrounding text goes in and which comes out. The
  excerpt must let a reader see what the word does in the line: its governing
  verb, its object, the words it is paired or contrasted with. A fixed
  character window is never an excerpt. Mark omissions with ellipses in the
  Greek and, where needed, in the translation.
- **Framing.** Who is speaking, in what text, and what the line is doing in
  the history you are tracing. Orient the reader; do not audit the station.
- **Commentary.** What this passage shows on the page, in plain English and
  STYLE.md doing-verbs. Hermeneutics for the reader, not notes for the
  verifier. No apparatus, no manuscript analysis, no restating the index line.
- **Arrangement.** One trajectory that makes the hinge readable.

A **station is a unit; a unit may carry more than one evidence block.** When
the piece returns to a rich witness (STYLE.md's focal-author deepening: the
trap laid in one section, sprung in another), each return is its own block
with its own citation, and the station row lists every block. Coverage is
counted at unit level: the station is accounted once, all its blocks verified.

Never produce all witness blocks in a single generation pass. Compose one
chunk (about ten stations) at a time, writing each block into the store and
maintaining the index between chunks (see The composition store).

## The composition store (single-owned state)

The candidate set, the chapter plan, the per-witness evidence blocks, the
running narrative index, and the claims register live in **one SQLite database**
under `composition_cluster/` (a prototype, foldable into the shared Postgres corpus
later). The database is the state that survives across sessions; the
conversation is not, and neither the index nor the station table is ever pasted
into chat. It is a **single-owned capability with an explicit state machine**,
not a pile of ad hoc scripts: every station carries one status (`pending` ->
`drafted` -> `checked`) and state changes only through the operations in Phase
4 and Phase 6. One place to look, one write path (the family one-system
discipline: single owner per invariant; see `.eukoine/` and the member's
governance). Schema and read protocol in `references/ledger.md`.

Two layers solve the single-shot context problem:

- **The index (light layer): the structural memory.** One narrative line per
  station, in trajectory order: the citation, the key Greek phrase, and a
  doing-verb summary of what the station shows. It also carries the **hinge**
  (verbatim, as confirmed at the Phase 1 gate), the **section lines** (what
  each section shows, in doing-verbs), and the **claims register** (every
  cross-station claim with the unit ids it depends on). The index is small
  enough that the whole argument arc stays in context at once; reading it
  replaces re-reading the draft.
- **The blocks (heavy layer).** Per witness: the Greek excerpt,
  transliteration, translation, and commentary. Bulky, so pulled only for the
  current sliding window.

**Chunked composition with a sliding window.** Order the stations
chronologically and cut them into chunks of about ten. To compose station N,
read the **entire index** (the whole arc) plus the **heavy blocks of the prior
chunk** (the overlapping window), then draft, write the new block(s), and
append one index line. The index lets the agent judge the development of the
whole discussion; the window supplies the local detail. This is how a long
piece stays coherent without holding every block in memory at once, and it is
why composition is chronological: each chunk builds on a legible, summarised
past.

A **station is a unit; a unit may carry more than one block**; coverage is
counted at unit level (see The ceiling). At long-form scale, row-by-row
reasoning over every candidate is not required outside the complete-coverage
set: group dispositions there (by author, cluster, or period) are acceptable,
provided every candidate is covered by some disposition and every selected
station still gets its own station row. Inside the complete-coverage set,
dispositions are row-by-row, always. Nothing is silently dropped; every
set-aside inside the coverage set is recorded with its reason and surfaced in
the eventual piece.

**Reference vocabulary is the family's, not this skill's to redefine.**
Identity is `eul_wid` / `eul_aid`; URLs come from display strings (attributes,
not identity); retired signifiers are never reintroduced in schema, code, or
prose. Consult `.eukoine/predicate_vocabulary.md` and
`.eukoine/corpus_identity_and_schema.md` before coining any signifier; do not
restate their rules here (no secondary sources).

## Procedure

Three phases. Phase numbers 0–7 are unchanged; the headings mark which agent
may stop after which work. See `composition_cluster/README.md` for scripts and
done-criteria.

### Pre-composition (Phases 0–3)

Scaffold only: no evidence blocks, no ending prose, no HTML. Stops with every
station `pending`, `idx` filled, zero `block` rows.

#### Phase 0: Load

1. Obtain and read STYLE.md in full (see Hard requirements).
2. Read the index of published Tekmeria and the working lexicon
   (eugraphikon_lexicon.md) for prior readings of this term or its
   neighbours. A reading already taken informs the new piece; it is never
   silently reinvented or contradicted.
3. Locate the survey data (diachronic-term-survey output or corpus JSON). If
   none exists, stop and run the survey skill first.
4. Confirm live DB access with a trivial query. No DB, no composition.

#### Phase 1: Question, hinge, scope (user gate)

Draft one controlling corpus question with a hinge, per STYLE.md. Then
confirm with the user, before any prose:

- the question and hinge;
- the **complete-coverage set**, if any: the exact DB predicate for the subset
  the piece commits to including exhaustively (e.g.
  `authors.affiliation = 'stoic'`), as distinct from background and afterlife
  material selected by judgment;
- the trajectory type and rough length.

Do not proceed past this gate without confirmation.

#### Phase 2: Candidates, then stations

1. Generate the `candidate` rows in the store with one query over the whole
   word-family (all forms, privatives included), no filters, one row per
   unit. Record the query, its timestamp, and the headline counts (the query
   and its result are the CATALOG provenance). Regenerate and diff on every
   resumed session so corpus drift surfaces immediately.
2. Derive the stations. Dispositions:
   - **station**: will carry a full evidence block.
   - **secondary**: cited inline as one English sentence (parallel witness,
     cross-reference); not a block; **no bare Greek** in the projected line.
   - **set-aside**: excluded from the public page, with a stated reason in the
     store. Within the complete-coverage set: proper name (lexical status, not
     the concept); duplicate station (same sentence at two addresses: the source
     author's unit is the station, the collection number is a HAND note,
     counted once); corrupted or unsegmented unit (corpus boundary, locus by
     HAND); verbatim quotation of an included witness; **dating trap**
     (pseudepigraphon, mis-tagged floruit, proper-name hit dressed as an early
     attestation). Resolve traps at compose time; start the public trajectory
     at the first secure witness. Set-asides are verified and recorded in the
     verification report; they are **not** a public chapter and **not**
     trap-labelled cite lines. Nothing is silently dropped.
   - **group set-asides** outside the complete-coverage set are permitted with
     a group reason (e.g. "late-antique epic afterlife, represented by two
     stations").
3. Station-type discipline (STYLE.md "Before composing"): doxography is not
   original speech; author floruit is not composition date for pseudepigrapha;
   test apparent early hits at compose time and **set aside** what cannot be
   honoured as a witness. Do **not** plan a public chapter for dating-trap
   audit; the reader walks the concept's history, not the metadata.

#### Phase 3: Trajectory

Order the stations. Chronology is often best, not mandatory; STYLE.md lists
the trajectory types. Mark in the store where the period shifts and where the
domain shifts (philosophy to medicine, household counsel to historiography):
each seam becomes a framing sentence or a section boundary, so the reader sees
the concept move between times and domains without being told a theory about
it. Write the section skeleton with the hinge stated early.

### Composition (Phases 4–5)

Judgment only: write into the store, never into HTML. Read `STYLE.md` §
**Formatting cross-check**, `composition_cluster/prose_rules.md`, and
`composition_cluster/craft.md` this session before drafting English fields.
Do not run verification or projection in this phase.

#### Phase 4: Stations, in chunks

For each station, in trajectory order, one chunk (about ten stations) at a
time. Before drafting a chunk, read the entire index (the whole arc) and the
heavy blocks of the prior chunk (the sliding window). Then, per station:

1. **Fetch fresh** by unit id (QUOTE class). Never quote from the JSON, a
   previous session, or memory.
2. **Excerpt by judgment** (see The ceiling). Keep editorial brackets as the
   corpus yields them.
3. **Frame above**: the station and the local fact.
4. **Cite once, above the block**: linked work title + visible wid + ref.
   Title, wid, ref, and URL are CATALOG class: resolve them by query now, not
   from the JSON; never hand-guess a display string.
5. **Three lines**: Greek verbatim; ALA-LC transliteration
   (`references/transliteration.md`); English translation with no quotation
   marks around the whole line and **no square brackets** (no editorial
   insertions). **Translation warrant rule** (`prose_rules.md`): the
   translation contains nothing without warrant in the Greek excerpt.
   Interpretation and hermeneutic argument belong in the commentary below the
   block, where they are visibly the writer's. Running-English formatting:
   `STYLE.md` § Formatting cross-check.
6. **Blacklist: transliterate at the source.** The authoritative blacklist
   scan is **not** a manual step here: it is `check_blacklist` in
   `composition_verify.py`, which runs automatically on every verification
   pass (Phase 6) against every English field in the store and fails the
   report on any hit. The compose-time job is therefore to *not create* hits:
   where a Greek term would be flattened by its English gloss, leave it
   transliterated and gloss in commentary (`prose_rules.md`, φύσις / *physis*;
   full table in STYLE § Formatting cross-check).
   The single most common self-inflicted failure is rendering φύσει as "by
   nature": `blacklist_physis_nature` bans bare **nature** and **by nature**
   outright, so write **by *physis*** in every English field, including
   translation lines. If unsure what the live list forbids, read it once:

   ```sql
   SELECT signal_key, patterns, whole_word
   FROM eugraphikon.signal_triggers
   WHERE signal_key LIKE 'blacklist_%' AND enabled = true;
   ```

   but do not rely on eye-checking against it; the verifier is the gate.
7. **Comment after** the translation: what the line **does in the history**,
   in plain English (`craft.md`). A diachronic or cross-domain shift only if
   already visible. No speculation, no invented spokesman, no crowning verdict,
   no verification voice.
8. **Write the block(s) and the index line into the store, and record
   verification in the station row**: the quoted span(s) matched against
   text_greek, the CATALOG fields confirmed, any HAND facts sourced. Record the
   matched incipit in its column: the match is being run anyway, and it is the
   leg of the durable anchor set that survives re-keying. Append one index line
   (citation, key Greek phrase for the store, **English doing-verb summary**
   for projected secondaries). Status: `drafted`.

**Between chunks**: check the chunk against the index and update it (section
lines, claims register). The hinge is still the center; no shift announced
twice; every block earns its place; every interpretive sentence would survive
if the reader only checked the Greek block above it; any new cross-station
claim is registered with the unit ids it depends on. Fix before continuing.
Update station statuses.

**Re-ordering** is allowed at any point: renumber the station `seq`, re-cut the
chunks, update the index's section lines, and re-check every claims-register
line against the new order (forward references are the usual casualty).
Drafted blocks move with their rows unchanged; they were verified against
units, not positions.

#### Phase 5: Ending

Per STYLE.md Endings: restrained, evidential, checkable facts from the store;
at most one earned suggestive shape, then **reader-facing** caveats only
(doxography, coverage limits, HAND parallels). Not a verification dump: no
metadata mirage lecture, no digitisation audit, no trap-labelled secondary
list. Every table and every count is CATALOG class: recomputed by query at
composition time, query recorded. Standard caveats where they apply: partial
vector coverage, author-level floruit vs passage-level dating, corrupted units,
station-type limits, strands set aside by method.

### Post-composition (Phases 6–7 and publish)

No new editorial judgment except fixes forced by failed checks (apply fixes in
the composition writers, then re-run from verify).

#### Phase 6: Verification report (produced, not asserted)

Produce the verification report from the store (recording per-block pass/fail
in the station and block rows, and writing the report beside the database). It
contains, explicitly:

1. **Quote integrity**: per station, unit id, each quoted Greek segment (all
   blocks of a multi-excerpt station), and pass/fail of the exact substring
   match, run now.
2. **Translation fidelity**: per block, in a pass separate from drafting, a
   clause-by-clause back-check of the English against the Greek excerpt:
   flag any content in the translation with no Greek warrant and any omission
   that misleads. Transliterations re-derived against
   `references/transliteration.md` in the same pass.
3. **Bare Greek**: no English field (framing, translation, commentary, chapter
   prose, secondary pointer, ending) carries bare Greek script or a bare
   transliterated form. Every Greek token in running English has an inline
   companion (slash-pair or gloss); only the subject word and blacklist terms
   stand alone (`STYLE.md` § Formatting cross-check). Enforced by the verifier,
   not left to the eye.
4. **Apparatus brackets**: editorial brackets (⟨ ⟩ 〈 〉 [ ] † †) are kept in
   `block.greek` as a faithful record and **stripped on projection**; none may
   reach any English field, and none may survive into the reading surface.
5. **Ecclesiastical exclusion**: no Christian, patristic, or theological
   witness is a station or secondary (christian-affiliated candidates are
   set-aside `ecclesiastical-excluded`), and no English field names one or
   carries theological content. The survey stops at the boundary of the
   ecclesiastical tradition.
6. **Coverage**: every candidate row accounted for at unit level: station
   (all its blocks present and verified), secondary (English pointer if
   projected), set-aside (reasoned in the store; verified, not necessarily on
   the public page), or group set-aside.
7. **Catalog integrity**: the queries reproducing every count, density, table
   row, wid link, and work title printed, with results matching the draft.
8. **Period claims**: every period or era word attached to a witness in the
   prose or a table checked against station type, not just the author's DB
   period tag. Where the station is pseudepigraphic or of contested date
   (letters under early names: the Theano type), set it aside at compose time
   and start the public trajectory at the first secure witness; an "earliest
   attestation" claim never rests silently on an attributed floruit.
9. **Claims register**: every registered cross-station claim checked against
   the finished arrangement and the stations it depends on.
10. **HAND register**: every HAND fact, its source, and where the piece
    discloses it.
11. **Prose scans (automatic)**: `check_blacklist` scans every English field
    in the store against the live rules and fails on any hit; the U+2014 scan
    fails on any em dash (en dashes in ranges are fine). Both run
    unconditionally on every verification pass; neither is an eye-check.

A failed line is fixed and the report regenerated. The piece is publishable
only with a clean report and a completed cold read.

#### Phase 7: Convert to HTML, cold read, publish

1. **Convert the store's Markdown to HTML deterministically.** When every
   station is `checked`, render the essay HTML from the records: block order
   from the station `seq`; each block's Greek (apparatus brackets stripped),
   transliteration, translation, and commentary; Markdown emphasis in English
   fields converted to `<em>`; citations composed from CATALOG fields (display
   string for the URL, `eul_wid` and ref shown); tables recomputed from the
   store. The conversion carries no editorial judgment; if it needs a
   decision, that decision belonged in the records. This is a fixed
   transformation (`composition_project.py`), not a place to rewrite prose.
2. **Cold read** the converted piece as its reader: only the rendered page, no
   store, no DB, ideally a fresh session. Apply STYLE.md's three question lists
   (too broad, too dry, hyperbolic) and one more: does any sentence require
   information that is not on the page? Fix findings in the **records** (the
   Markdown fields), not the HTML, then re-convert.
3. **Publish** per README (skeleton, posts.json, sync script, --check).

## Session continuity

The store is the state; the conversation is not.

**Pre-composition resume:** regenerate the candidate query and diff against
the store's `candidate` table (corpus drift surfaces here); continue from the
first incomplete scaffold step.

**Composition-only resume:** obtain STYLE.md (including § Formatting
cross-check), `composition_cluster/prose_rules.md`, and
`composition_cluster/craft.md`;
read the index (hinge, section lines,
claims register) and the blocks of the current chunk; continue from the first
`pending` station. Never recompose a `checked` station from memory; to change a
drafted station, re-fetch its unit first.

**Post-composition resume:** run verify from recorded sidecars; fix failures in
the composition writers, not in HTML; re-project and sync.

## Anti-patterns

- Excerpting by fixed window instead of judgment.
- Generating many witness blocks in one pass without index maintenance
  between chunks.
- Interpretation smuggled into the translation line instead of the
  commentary.
- Bare Greek script or a bare transliterated form left in an English field
  (mixed readership: every Greek token in prose carries an inline gloss).
- Editorial brackets reaching the reading surface (kept in the store, stripped
  on projection).
- Any Christian, patristic, or theological witness or content on the page, or
  reaching past the surveyed span to mention one.
- Crowning a verdict the Greek on the page has not earned ("the summit of the
  concept", a closing aphorism that restates the thesis as a ruling).
- An "earliest attestation" or period claim resting on an attributed floruit
  without the station type carrying the trap.
- Writing prose before the scope gate is confirmed and the stations derived.
- Printing any fact sourced from the survey JSON.
- Treating token counts as attestation counts.
- Counting a fragment-collection row and its source author as two witnesses.
- Asserting a check without a line in the verification report.
- Announcing a tradition-wide event where naming what the passage does would
  do.
- Ending with a dictionary definition instead of a checkable landscape.
- Composing into HTML by hand, or leaving the narrative as free prose in the
  conversation, instead of writing Markdown records and index lines into the
  store (the HTML is a deterministic conversion, never hand-authored).
- Eye-checking the blacklist instead of letting the verifier gate it, or
  rendering φύσει as "by nature" anywhere in an English field.
- Reintroducing a retired signifier in schema, code, or prose, or coining a
  code signifier without first consulting the family lexicon.
- Building the store as ad hoc, re-run-unsafe scripting instead of one
  single-owned, rebuildable state machine.

## Quick-reference checklist

- [ ] STYLE.md obtained and read this session; prior Tekmeria and lexicon
      consulted
- [ ] Composition phase: STYLE.md § Formatting cross-check,
      `composition_cluster/prose_rules.md`, and `composition_cluster/craft.md`
      read this session
- [ ] Live DB confirmed; question, hinge, complete-coverage predicate,
      trajectory confirmed by user
- [ ] Candidate rows generated by one recorded query; stations derived in the
      store; dispositions row-by-row inside the coverage set, grouped with
      reasons outside it
- [ ] Duplicate stations counted once (source author is the station)
- [ ] Composed into the store, not HTML; blocks written chunk by chunk with
      index maintenance between; claims registered as made; re-orders renumber
      the station seq and re-check the register
- [ ] Every block: fetched fresh, excerpted by judgment, framed, cited once
      above, three lines, translation warrant rule kept, blacklist-checked,
      commented in doing-verbs, written to the store with verification in its
      station row and an index line appended
- [ ] Every printed fact QUOTE, CATALOG, or HAND; nothing from the JSON
- [ ] Family vocabulary kept (eul_wid / eul_aid, display strings); no retired
      signifiers coined in schema, code, or prose
- [ ] Period and domain seams surfaced as framing, not theory; period words
      checked against station type, not floruit alone
- [ ] Set-asides within the coverage set reasoned in the store (not trap chapters on the page)
- [ ] Verification report produced and clean (incl. translation fidelity,
      period claims, claims register); HTML produced only by deterministic
      projection; cold read done before the piece is called done
