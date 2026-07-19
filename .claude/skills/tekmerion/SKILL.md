---
name: tekmerion
description: "Compose a Tekmerion, an evidence-led corpus essay on an Ancient Greek term or locus, for tekmeria.eulogikon.org. Use whenever the user wants to write, extend, or revise a Tekmerion; turn diachronic-term-survey output or a corpus JSON into an essay; write an extended structured essay on any Greek term (philostorgia, phusis, prohairesis, dynamis, or any other); or asks for complete citation coverage of a term within an author, school, period, or domain. Also use when resuming a partly-composed Tekmerion. The composition is judgment work above the mechanical ceiling: excerpt selection, framing, commentary, and arrangement are editorial decisions taken per witness, never generated in one pass. This skill governs the procedure; STYLE.md in the tekmeria repo governs the prose and stays authoritative."
---

# Tekmerion Composer

Compose a Tekmerion from survey data: a sequence of corpus witnesses, each
framed, cited, quoted in Greek, transliterated (ALA-LC), translated, and
commented, arranged along one trajectory so that one corpus question and its
hinge become visible. Works for any term or locus. Designed for chunked,
multi-session composition with a persistent witness ledger, not single-shot
generation.

## Division of authority

- **STYLE.md** (repo root of eulogikon-semeia / tekmeria) is authoritative for
  everything about the prose: what a Tekmerion is, the balance to keep, framing,
  evidence blocks, endings, citations. Read it in full at the start of every
  composition session. Do not work from memory of it; it is revised.
- **This skill** is authoritative for the procedure: the order of work, the
  ledger, batching, verification, and session continuity.
- **README.md** (same repo) is authoritative for file mechanics, URL
  composition, posts.json registration, and sync/deploy.
- **diachronic-term-survey** (separate skill) produces the survey data this
  skill consumes. If no survey exists for the term, run that skill first.

## The ceiling

The mechanical layer (word search, KWIC windows, token counts, DB verification)
is the floor of this work, not the work. What cannot be mechanized, and must be
done per witness by judgment:

- **Excerption.** Which surrounding text goes in and which comes out. The
  excerpt must let a reader see what the word does in the line: its governing
  verb, its object, the words it is paired or contrasted with. A fixed
  character window is never an excerpt. Mark omissions with ellipses in the
  Greek and, where needed, in the translation.
- **Framing.** What kind of witness this is and what the line does locally.
- **Commentary.** What the passage does on the page, in the doing-verbs STYLE.md
  lists (pairs, distinguishes, equates, preserves, quotes, glosses, defines,
  contrasts, omits, redirects, collapses). No hypothetical speculation. Name a
  shift only when it is visible in the witnesses already placed.
- **Arrangement.** One trajectory that makes the hinge readable.

Never produce all witness blocks in a single generation pass. Compose stations
in batches of three to five, re-reading the draft from the top between batches.

## Procedure

### Phase 0: Load

1. Read STYLE.md in full from the tekmeria repo.
2. Read the index of published Tekmeria and the working lexicon
   (eugraphikon_lexicon.md) for prior readings of this term or its neighbours.
   A reading already taken informs the new piece; it is never silently
   reinvented or contradicted.
3. Locate the survey data: diachronic-term-survey output or a corpus JSON
   (e.g. philostorgia_corpus.json). If none exists, stop and run the survey
   skill first.
4. Confirm live DB access (Postgres, eulogikon schema). Every count and every
   quotation in the piece comes from the DB, not from the JSON alone: the JSON
   is a snapshot and may conflate tokens with units.

### Phase 1: Question, hinge, scope (user gate)

Draft one controlling corpus question with a hinge, per STYLE.md. Then confirm
with the user, before any prose:

- the question and hinge;
- the **complete-coverage set**, if any: the subset of attestations the piece
  commits to including exhaustively (e.g. "every unit by a Stoic-affiliated
  author"), as distinct from background and afterlife material selected by
  judgment;
- the trajectory type and rough length.

Do not proceed past this gate without confirmation. This is the one place the
piece's shape is decided.

### Phase 2: Ledger

Build the witness ledger before writing any prose. Format and disposition
vocabulary: `references/ledger.md`. One row per **unit** (a token count is not
an attestation count; fifteen tokens in one Epictetus discourse are one unit).

For every unit in scope, record from the live DB: unit id, eul_wid, ref,
author, affiliation, period, domain, station type, disposition, status.

Disposition rules:

- **station**: will carry a full evidence block.
- **secondary**: cited inline (span.cite) as parallel, cross-reference, or
  corpus-boundary note; not a block.
- **set-aside**: excluded, with a stated reason. Within the complete-coverage
  set, valid reasons are only: proper name (lexical_status, not the concept);
  duplicate station (the same sentence held twice, e.g. a von Arnim fragment
  row and its source author's own text: cite the witness, note the fragment
  number, count once); corrupted or unsegmented unit (flag as a corpus
  boundary, supply the locus by hand); verbatim quotation of an
  already-included witness. Every set-aside inside the complete-coverage set
  is reported in the piece's corpus-boundaries or caveats section. Nothing is
  silently dropped.

Station-type discipline (STYLE.md "Before composing"): doxography is not
original speech; author floruit is not composition date for pseudepigrapha;
test apparent early hits. Record the station type in the ledger, and let it
surface in the framing.

### Phase 3: Trajectory

Order the stations. Chronology is often best, not mandatory; STYLE.md lists the
trajectory types. Mark in the ledger where the period shifts and where the
domain shifts (philosophy to medicine, household counsel to historiography):
each such seam becomes a framing sentence or a section boundary in the draft,
so the reader sees the concept move between times and domains without being
told a theory about it. Write the section skeleton with the hinge stated early.

### Phase 4: Stations, in batches

For each station, in ledger order, three to five per batch:

1. **Fetch fresh.** Pull the unit's text_greek from the DB by unit id. Never
   quote from the JSON, from a previous session's context, or from memory.
2. **Excerpt by judgment** (see The ceiling above). Keep editorial brackets
   as the corpus yields them.
3. **Frame above**: the station (who, what text, what kind of witness) and the
   local fact (what the word is paired with, what receives it, what contrast
   the line makes).
4. **Cite once, above the block**: linked work title + visible wid + ref, per
   STYLE.md Citations. Resolve the URL from the database; never hand-guess a
   slug.
5. **Three lines**: Greek verbatim; ALA-LC transliteration
   (`references/transliteration.md`); English translation with no quotation
   marks around the whole line.
6. **Blacklist check, live.** Before finalizing the translation and the
   commentary, run:

   ```sql
   SELECT signal_key, pattern, patterns, valence, payload, whole_word
   FROM eugraphikon.signal_triggers
   WHERE signal_key LIKE 'blacklist_%' AND enabled = true;
   ```

   Check every drafted English line against every row (whole-word where
   flagged). Treat payload as the rule, patterns as examples. Where a Greek
   term would be flattened by any English rendering, leave it transliterated
   with a bracketed gloss (the philostorgia practice: kata physin, pathos,
   psyche stay Greek).
7. **Comment after** the translation: what the line does on the page. Name a
   diachronic or cross-domain shift only if the witnesses already placed make
   it visible. No speculation, no invented spokesman, no crowning verdict.
8. **Update the ledger row** to drafted.

**Between batches**: re-read the draft from the top. Check: the hinge is still
the center; no shift is announced twice; every station placed so far earns its
place; every interpretive sentence would survive if the reader only checked
the Greek block above it. Fix before continuing. Update ledger statuses.

### Phase 5: Ending

Per STYLE.md Endings: a restrained evidential ending with checkable facts
drawn from the ledger; at most one earned suggestive shape, then caveats.
Any diachronic or sources table is recomputed from the ledger and the DB at
composition time, never hand-typed or carried over. Standard caveats where they
apply: partial vector coverage, author-level floruit vs passage-level dating,
corrupted units, station-type limits, material set aside by method (e.g.
ecclesiastical strand noted as parallel only).

### Phase 6: Verification (mechanical floor, run last)

1. Every quoted Greek span re-fetched by unit id and matched as an exact
   substring of units.text_greek (ellipsis segments matched piecewise).
2. Every ledger row accounted for: stations appear exactly once; secondaries
   cited; set-asides reasoned and, if in the complete-coverage set, reported.
3. Every wid link resolved from the DB.
4. Blacklist scan of the entire English text, live query.
5. No U+2014 anywhere. En dashes in reference ranges are fine.
6. Counts in prose and tables match the ledger.
7. If publishing: follow README (new-post.html skeleton, posts.json,
   sync_tekmeria_site.py, --check).

## Session continuity

The ledger file and the draft are the state; the conversation is not. On
resuming: read STYLE.md, the ledger, and the draft; find the first pending
station; continue the batch cycle. Never recompose a verified station from
memory; if a drafted station must change, re-fetch its unit first.

## Anti-patterns

- Excerpting by fixed window instead of judgment.
- Generating many witness blocks in one pass without re-reading between.
- Writing prose before the ledger is complete and the scope gate confirmed.
- Treating token counts as attestation counts.
- Counting a fragment-collection row and its source author as two witnesses.
- Quoting Greek from the survey JSON or from memory instead of the live DB.
- Announcing a tradition-wide event where naming what the passage does would do.
- Ending with a dictionary definition instead of a checkable landscape.

## Quick-reference checklist

- [ ] STYLE.md read this session; prior Tekmeria and lexicon consulted
- [ ] Question, hinge, complete-coverage set, trajectory confirmed by user
- [ ] Ledger complete before prose; one row per unit; dispositions reasoned
- [ ] Duplicate stations (fragment collection vs source author) counted once
- [ ] Stations composed in batches with a top-to-bottom re-read between
- [ ] Every station: fetched fresh, excerpted by judgment, framed, cited once
      above, three lines, blacklist-checked, commented in doing-verbs
- [ ] Period and domain seams surfaced as framing, not theory
- [ ] Set-asides within the complete-coverage set reported in the piece
- [ ] Ending evidential; tables recomputed from ledger; caveats present
- [ ] Verification pass run: substring match, coverage, links, blacklist,
      no U+2014, counts consistent
