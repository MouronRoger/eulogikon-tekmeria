# Canonical design principles: Tekmeria (TDP)

- **Title:** Canonical design principles, Tekmeria (`eulogikon-semeia`)
- **Status:** active
- **Authority_level:** member canonical principles. Below family law
  (`../eukoine/ONE_SYSTEM.md`, `../eukoine/PURPOSE.md`, `.eukoine/`), above this
  repo's specifications and skills.
- **Scope:** the `eulogikon-semeia` repo: the composition store, the scripts
  that read and project it, the published Tekmeria, and the governing prose.
- **Relationship_to:**
  - family law: `../eukoine/GOVERNANCE.md` §3 (authority order), `ONE_SYSTEM.md` §4
  - registry: `governance_cluster/registry.yaml` (ids, owners, checks)
  - rot doctrine: `ROT.md`
  - prose authority: `STYLE.md`
  - procedure authority: `.claude/skills/tekmerion/SKILL.md`

Each principle states one rule, names the invariant it protects, and says how a
violation is detected. A principle that names no invariant is not a principle
here: see TAP-008.

Where a rule binds more than one family member it is family law and lives at the
hub. This document cites those; it never re-mints them under a TDP number.

---

## Evidence and provenance

### TDP-001 : every printed fact carries a provenance class

**Rule:** Every fact that reaches a reader is exactly one of QUOTE (Greek from
the corpus, verified by substring match), CATALOG (names, identifiers,
references, URLs, counts, resolved by a query run at composition time), or HAND
(what the corpus cannot supply, marked with its source). The class determines
how the fact is verified and is recorded with it.

**Invariant:** No assertion in a published Tekmerion is unattributable to a
checkable source.

**Violation:** A printed fact with no class. A count in prose or a table that no
recorded query reproduces.

**Owner:** `.claude/skills/tekmerion/SKILL.md` § Provenance classes.

### TDP-002 : discovery data is never a source

**Rule:** Survey output (a corpus JSON, a KWIC dump, a prior session's notes)
tells the composition where to look and supplies nothing that reaches the
reader. The flow is one way: the live corpus supplies printed facts; discovery
artifacts supply only candidate locations.

**Invariant:** Nothing printed rests on a frozen snapshot of a moving corpus.

**Violation:** A count, an era string, a floruit, a work title, or a Greek
quotation taken from a survey artifact rather than re-derived under TDP-001.

**Owner:** `.claude/skills/tekmerion/SKILL.md` § Provenance classes.

**Cites:** the same directional shape as eulogikon CDP-042 (canonical to
derived, never the reverse).

### TDP-003 : verification is produced, never asserted

**Rule:** A check exists when it has a record in the store or the verification
report. The report is generated from the store, not written from memory of
having looked. A piece is publishable only on a clean report and a completed
cold read.

**Invariant:** The claim "this was checked" is always backed by the artifact of
the check.

**Violation:** A station marked verified with no per-block record. A report
section asserting a pass with no line per item. "I checked those."

**Owner:** `.claude/skills/tekmerion/references/ledger.md` § Verification.

**Note:** this is the local form of the family rule that a correctness claim is
a test and never a shape check (EuMorphikon FR-28). Applied here, the
verification report is the test; a guardian over the store's shape is not
evidence that the citations are right.

### TDP-004 : durable records carry the durable anchor set

**Rule:** Every record that outlives its session anchors on `eul_wid` plus a
quoted Greek incipit plus `legacy_reference`. A provisional `unit_id` is a
session-scoped pointer for re-fetching and is never the anchor.

**Invariant:** Every stored witness re-anchors to a settled `sid` by unique
content match at corpus cutover.

**Violation:** A store row, a ledger line, or a published citation recoverable
only through a provisional id.

**Owner:** family law, `.eukoine/interim_head_citation.md` §4. Not restated
here.

### TDP-005 : identity is never reconstructed from a display string

**Rule:** `eul_wid` and `eul_aid` are the only identifiers. A title, filename,
URL segment, or reference string is an attribute resolved *from* the
identifier, never a substitute for it and never parsed back into one. Canonical
URLs are resolved from the corpus, never composed by hand.

**Invariant:** One signifier, one referent, across the family.

**Violation:** A key, join, or citation composed from a display string. A
column or field named `slug` or `file_id`. A URL guessed rather than resolved.

**Owner:** family law, eulogikon CDP-038 and CDP-050 (`slug` and `file_id` are
retired signifiers family-wide). Not restated here.

---

## Composition

### TDP-006 : the mechanical layer is the floor, not the work

**Rule:** Search, windowing, counting, and matching are mechanism. Excerption,
framing, commentary, and arrangement are judgment taken per witness. A fixed
character window is not an excerpt; a generated batch of blocks is not a
composition.

**Invariant:** Editorial judgment is exercised where a reader will hold the
piece responsible for it.

**Violation:** Blocks produced in one pass without per-witness judgment.
Excerpts cut to a character budget. Commentary that names a shift no placed
witness shows.

**Owner:** `.claude/skills/tekmerion/SKILL.md` § The ceiling.

### TDP-007 : interpretation lives in the commentary

**Rule:** A translation line carries nothing without warrant in the Greek
excerpt above it: no added subject, no supplied connective asserting a relation
the Greek does not, no interpretive gloss. Interpretation goes below the block,
where it is visibly the writer's.

**Invariant:** A reader checking only the Greek can falsify any claim made
about it.

**Violation:** A reading smuggled into the translation line. A connective that
manufactures the argument the commentary then reports.

**Owner:** `.claude/skills/tekmerion/SKILL.md` Phase 4, translation warrant rule.

### TDP-008 : the store is the state

**Rule:** The composition store holds the candidate set, the plan, every
evidence block, the narrative index, and the claims register. The conversation
holds none of it. A resumed session reads the store, not the transcript.

**Invariant:** No composition depends on a context window surviving.

**Violation:** A station recomposed from memory. A claim registered only in
conversation. State pasted between sessions rather than read from the store.

**Owner:** `.claude/skills/tekmerion/references/ledger.md`.

### TDP-009 : the published page is a projection

**Rule:** The essay HTML is a deterministic projection of the store, produced
after the records are correct. It is never composed into directly and never
holds a fact the store does not.

**Invariant:** One source of truth for the argument and its evidence; the page
can be regenerated at will without editorial loss.

**Violation:** An edit to a published page that changes a quotation, an
identifier, a reference, or a count without the store and its verification
record changing in the same act. This is the most serious class available here:
it silently detaches published evidence from the check that backs it, and it is
surfaced and stopped on, never logged and continued.

**Owner:** `.claude/skills/tekmerion/SKILL.md` § The output is the record set.

---

## Engine

These bind the store, the scripts that read and project it, and any future
service around them. They do not bind the prose: see TDP-012.

### TDP-010 : capability port shape, by construction

**Rule:** Where the store sits behind a seam, single ownership is realised as
**driver plus narrow typed port plus adapters**. The driver holds the invariant
in one place and there is no second path to the effect. The port is the
behaviour boundary and no storage or infrastructure shape leaks through it. An
adapter carries provider mechanics only and has no power over the invariant: it
returns a typed result or raises a genuine transport error, and can neither
hold nor break the guarantee.

The shape is Go-translatable: the driver compiles to one struct, the port to
one interface, adapters to the only thing that varies. All new engine code is
capability-port by construction and every improvement moves existing code
toward the port shape.

**Invariant:** The SQLite store and the later shared-Postgres store are two
adapters behind one port, so the fold is mechanical and never a rewrite.

**Violation:** An invariant held in two places. An untyped row bag crossing the
boundary. An adapter that can end or fail the guaranteed outcome. Two parallel
paths left standing. A guard added downstream where the owner could preclude
the violation. If you cannot write the port signature, you do not have a port.

**Owner:** `governance_cluster/capability_port.md`.

**Cites:** family direction, `../EuGraphikon/go-port/PROGRAM.md`. Not negotiable.

### TDP-011 : a derived fact is carried, never recomputed

**Rule:** An identifier is the thing. It is carried and joined on, never
reconstructed from a description. Each derived fact has exactly one producing
owner; re-derivation anywhere else is rot.

**Invariant:** One referent never acquires two names, the minted one and the
recomputed one.

**Violation:** Recomputing an identifier from a reference, a position, or a
display string. A second module that recalculates a count, a fold, or a
citation the owner already produces.

**Owner:** family law, `../eukoine/schema_naming_law.md` §1. Not restated here.

### TDP-012 : parsimony, and where it stops

**Rule:** Prefer the smallest structure that carries the work: one owner, one
home, one statement. This binds the store schema, the scripts, and the
governing prose alike, and it is itself singly owned. It is stated here and
cited elsewhere; a restatement of it in another document is a violation of
itself.

The rule stops at the reader-facing page, where certain repetition is required
rather than tolerated: every evidence block carries its own full citation even
when it repeats the block above, because a reader must never scroll back to
learn what they are reading; a rich witness legitimately carries several blocks
in several sections. Repetition serving a reader is correct and is never
collapsed as duplication.

**Invariant:** Economy is applied to the machinery and never to the evidence a
reader needs in front of them.

**Violation:** The same rule stated in two governing documents. Two writable
sources of one fact. A citation removed from a block because it repeats an
earlier one. Collapsing a witness's several blocks into one because the unit is
the same.

**Owner:** this document. Prose economy for the essays is `STYLE.md`, which is
this principle applied to writing, not a second statement of it.

**Note:** the engine test for rot is two *writable* sources of one fact that can
drift, never two *read* paths over one owner.

---

## Gates

### TDP-013 : adversarial cross-check, compulsory at both gates

**Rule:** Before a plan stands, and before a sign-off stands, an **independent
read-only sub-agent** primed to **falsify, not confirm** attacks it. The author
is never their own adversary. The adversary returns the attacks it ran and what
survived or what defect it found. A bare "looks fine" is a non-run, and "low
risk" is not the agent's call.

For a Tekmerion the two gates are: the Phase 1 question, hinge, and coverage
predicate, attacked before any prose exists; and the finished piece against its
verification report, attacked before publication.

**Invariant:** No plan and no closure stands on the judgment of the party that
produced it.

**Violation:** A plan or a publication with no recorded falsifying pass. A pass
recorded as a verdict rather than as attacks run.

**Owner:** `governance_cluster/adversarial_cross_check.md`.

### TDP-014 : cold reading before collapse

**Rule:** Discovery of what a thing actually does is run **blind**: a reader
with no briefing on the intended structure, no file list, no prior-session
context, and no rubric, reporting only what it finds with a citation for every
claim. The tracer and the judge are different passes. Discovery never patches.
Absence of a current violator is not proof of safety, and a cold reader is an
instrument whose claims are re-checked before any of them is surfaced as a
defect.

Applied to a finished Tekmerion, the reader gets the page and nothing else and
answers: what does this claim, and what does each claim rest on. Applied to the
repo, it is how ownership topology is established before anything is collapsed.

**Invariant:** What exists is established before anyone interprets what it means.

**Violation:** Handing the reader the store, the report, or the style guide.
Being both tracer and judge. Ending a cold read in a backlog note rather than a
disposition.

**Owner:** `governance_cluster/cold_reading.md`.

### TDP-015 : every script reaches a terminal state

**Rule:** An executable is a **test** (a correctness claim, run by CI), a
**producer** (it builds a committed artifact, homed with the concern it
serves), a **guardian** (a cheap shape check at pre-commit), or a **chronicle**
(its finding is recorded in `work_reports/` and the script is deleted). A
**probe** is the one transient state and terminates before the work that
created it closes.

Every shipped or regenerable artifact traces to inputs either committed here or
re-fetchable from a pinned recorded identifier. A per-session agent sandbox is
neither.

**Invariant:** Nothing load-bearing depends on a script no one can classify, and
a gitignored build product is genuinely rebuildable.

**Violation:** A standing script with no terminal state. A measurement that
prints a number and asserts nothing. An input path under a session scratchpad.

**Owner:** `governance_cluster/script_lifecycle.md`.

---

## Anti-patterns (TAP)

Detection and remediation live in `governance_cluster/registry.yaml`.

- **TAP-001** : an "earliest attestation" or period claim resting on an
  attributed floruit, with the station type not carrying the trap. Violates
  TDP-001.
- **TAP-002** : a token count presented as an attestation count. Violates
  TDP-001.
- **TAP-003** : composing into the published page instead of the store.
  Violates TDP-008, TDP-009.
- **TAP-004** : interpretation smuggled into the translation line. Violates
  TDP-007.
- **TAP-005** : a fact printed from survey or discovery data. Violates TDP-002.
- **TAP-006** : a durable record pinned to a provisional identifier. Violates
  TDP-004.
- **TAP-007** : a second source. A helpful summary, a restated subset, a
  parallel current understanding, or a second copy of a rule owned elsewhere.
  Violates TDP-012.
- **TAP-008** : blocking pettifogging. Invoking or inventing a rule that names
  no invariant, only to obstruct sensible reversible work. The test is
  mechanical: a rule that names the invariant it protects stays; a rule that
  names none is this anti-pattern and is cut. The agent is fully empowered and
  this doctrine is its instrument, never a gate on sensible work.
