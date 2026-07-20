# The composition store: schema and read protocol

Extended Tekmeria are composed into **one SQLite database** under `composition_cluster/`,
not into notes in the conversation and not into HTML. The database is the state
that survives across sessions; the conversation is not. It is a single-owned,
rebuildable capability with an explicit state machine (every station moves
`pending` -> `drafted` -> `checked`, and only through the Phase 4 and Phase 6
operations), and it makes selection, coverage, and reference integrity
auditable at long-form scale. One place to look, one write path. The essay HTML
is a later deterministic projection of this store (Phase 7), never a parallel
source of truth.

The prototype is foldable into the shared Postgres corpus later; while it is
SQLite it still obeys the family single source. Reference vocabulary is not
this skill's to coin: identity is `eul_wid` / `eul_aid`, URLs come from display
strings (attributes, not identity), and retired signifiers are never used in
schema, code, or prose. Consult `.eukoine/predicate_vocabulary.md` and
`.eukoine/corpus_identity_and_schema.md`; this document does not restate their
rules.

## Two layers, one sliding window

The store separates the argument from its evidence so a long piece can be
composed without holding every block in memory at once:

- **The index (`idx`), light layer.** One narrative row per station, in
  trajectory order, plus the essay's hinge, section lines, and claims register.
  Small enough that the whole arc stays in context at once. Reading it replaces
  re-reading the draft.
- **The blocks (`block`), heavy layer.** Per witness: Greek excerpt,
  transliteration, translation, commentary. Bulky, pulled only for the current
  window.

**Read protocol.** Order stations chronologically; cut them into chunks of
about ten (`station.chunk`). To compose station N: read the **entire `idx`**
(the whole arc) and the **blocks of the prior chunk** (the overlapping window),
draft, write the new block(s), append one `idx` row, set the station
`drafted`. On a resumed session this is the minimum read-in: the whole `idx`
plus the current chunk's blocks.

## The tables

### `essay`

One row. `term`; `display_string` (the URL/filename display, never an
identity); `question` and `hinge` (verbatim, as confirmed at the Phase 1 gate);
`coverage_predicate` (the exact DB predicate defining the complete-coverage
set); `trajectory_type`; `created_at`.

### `candidate` (generated, exhaustive, never hand-curated)

One row per corpus **unit** matching the whole word-family (all forms,
privatives included), no filters. Populated by a single recorded SQL query
against the live DB; regenerated and diffed on every resumed session so corpus
drift surfaces at once. The generating query, its timestamp, and the headline
counts are recorded (the query and its result are the CATALOG provenance).

Columns mirror the grounding query: `unit_id`, `wid`, `ref`, `author`,
`eul_aid`, `affiliation`, `period`, `domain`, `format`, `fl_from`, `fl_to`,
`title`, `token_count`, `length`, `lexical_status`, `headwords`. `token_count`
is the number of word-family tokens in the unit (an occurrence count), kept
distinct from the row: **a token count is never an attestation count**.
Token-level lexical status (a personal name vs the concept) is a judgment the
DB does not hold; it is decided at station time and recorded as a
`station.reason`, never claimed by this table.

### `chapter`

The plan: one row per movement. `section_no`, `title`, `shows` (what the
movement does, in doing-verbs), and the `seq_from` / `seq_to` station range it
spans. Section VI is the closing landscape (counts and reader-facing caveats).
A chapter with empty or null `title` after Phase 5 is **compose-only** and is
skipped by projection: use for internal scaffold, not for dating-trap audit on
the public page.

### `station` (curated; the ledger)

One row per unit that is a **station** or **secondary**, plus one row per
**set-aside** (mandatory inside the complete-coverage set). A station is a
unit; a unit may carry more than one `block`.

- `seq`: trajectory position (Phase 3). Set-asides carry none. Re-ordering
  renumbers `seq`, re-cuts `chunk`, and triggers a claims-register re-check.
- `chunk`: the group of about ten this station composes with (NULL for
  set-aside).
- `section`: the `chapter.section_no` it belongs to.
- `unit_id`: `eulogikon.units.id`. A **session-scoped re-fetch pointer, not
  identity**: re-keyed when a passage moves. Fetch by it within a session;
  never carry it as the anchor.
- `wid`, `ref`, `author`, `fl_from`: CATALOG fields, resolved by query.
- `station_type`: STYLE.md vocabulary (original speech, dialogue, medical
  treatise, doxography, testimonium, fragment-in-later-author, scholium,
  lexicon, commentary, hostile report, letter, historiography). Extend only
  from the evidence.
- `disposition`: `station` | `secondary` | `set-aside`.
- `reason`: required for every set-aside; inside the complete-coverage set the
  only valid values are `proper-name`, `duplicate-station of <unit_id>`,
  `corrupted-unit`, `quotes <unit_id>`.
- `verified`: the per-station verification record, filled at draft time (Phase
  4.8): `Q` when every quoted span of every block matched `text_greek` by
  substring, `C` when title/wid/ref/URL were resolved by query this session,
  `T` when the translation warrant rule was checked for every block,
  `H:<source>` for any hand-supplied fact (e.g. `Q C T H:SVF-iii-731`). Empty
  means unverified: not publishable.
- `status`: `pending` | `drafted` | `checked` (verification report clean).

### `block` (heavy layer)

Zero or more per station. `block_seq` (order within the station), `framing`
(local frame above the citation: author, station kind, hook), `greek` (the
verbatim excerpt), `translit` (ALA-LC, per `references/transliteration.md`),
`translation`, `commentary` (what the line does on the page), and the check
flags `quote_ok` / `trans_ok` set in Phase 6. When the piece returns to a rich
witness (a trap laid in one section, sprung in another), each return is its own
block; coverage still counts the unit once and every block is verified.

### `idx` (light layer)

One row per station in trajectory order (`seq`): `station_id`, `unit_id`,
`citation`, `key_phrase` (the key Greek phrase, for the store), and `summary`
(a doing-verb line in **English** for projected secondaries; what the station
shows for the composer). This is the structural memory the agent reads to judge
the development of the whole discussion.

### `claim` (the claims register)

One row per cross-station claim in the prose (a forward reference, an "earliest
attestation" claim, any cross-section comparison): `claim`, `depends_on` (the
unit ids it rests on), `section`, `status`. Registered when the sentence is
written; re-checked on every re-order and in the verification report.

## The durable anchor set

Every row that outlives its session carries `wid` + quoted Greek incipit +
`ref`. Family law (`.eukoine/interim_head_citation.md` §4) forbids a durable
record pinned only to a provisional `unit_id`, because it cannot be recovered
after re-keying; read the rule there rather than looking for a summary here. At
cutover the store re-anchors to a settled `sid` by unique content match.

## Verification (Phase 6), recorded in the store

The report is produced from the store, per-block pass/fail written back into
`block.quote_ok` / `block.trans_ok` and `station.verified` / `station.status`,
and the report written beside the database. A check with no record did not
happen. Sections:

1. **Quote integrity**: per block, `unit_id`, the quoted Greek segment (or its
   first/last words when long), match pass/fail, run now.
2. **Translation fidelity**: per block, in a pass separate from drafting, a
   clause-by-clause back-check of the English against the Greek; unwarranted
   content or misleading omission is a failure; transliteration re-derived in
   the same pass.
3. **Coverage**: every `candidate` row reconciled at unit level (stations +
   secondaries + set-asides = candidate rows; per station, every block
   present); any remainder is a failure.
4. **Catalog integrity**: each count, density, table row, wid link, and title,
   with the query that reproduces it and the value obtained now.
5. **Period claims**: every period/era word attached to a witness checked
   against station type; pseudepigrapha and contested dates are **set aside**
   at compose time with a reason; no "earliest attestation" claim rests
   silently on an attributed floruit.
6. **Claims register**: each `claim`, the stations it depends on, pass/fail
   against the finished arrangement.
7. **HAND register**: every hand-supplied fact, its source, and where the piece
   discloses it. The survey JSON is never a valid HAND source: it is discovery
   only.
8. **Prose scans**: blacklist result (live query, zero hits or listed
   exceptions with justification), U+2014 count (must be zero).

## Duplicate stations

The corpus can hold the same sentence at two addresses: a fragment-collection
work (a von Arnim volume under the fragmentary author's wid) and the quoting
source's own text (e.g. Diogenes Laertius). One witness, two stations. Rule:
the **source author's unit is the station** (the witness that actually
survives); the collection unit is `set-aside: duplicate-station of <unit_id>`;
the collection's fragment number is a HAND note in the station's citation or
commentary. Never count the pair as two attestations in any table.

## Corrupted or unsegmented units

A unit whose text concatenates many passages under one ref (anomalous length,
internal citations) cannot supply a citation from its `ref`. Mark it
`corrupted-unit`; locate the passage inside it and supply the locus by HAND
from the internal apparatus; report the defect in the piece's corpus-boundaries
section; flag it upstream to the corpus project.
