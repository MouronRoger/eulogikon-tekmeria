# The Corpus TLA grid, the v5 Format, and the API — the single source

**Status:** Authoritative and complete. This is **the** specification of the corpus —
the identity system (AID / WID / SID / TID / RID), the v5.0 canonical work JSON, the
database schema, and the published `corpus_api`. It is self-contained: there is no other
specification, no parallel draft, and no separate discussion. Implementations **conform to
this document**; where an implementation and this document disagree, the implementation is
the defect. This is the family's single **synchronized** copy: it is edited at the EuKoine hub — the
synchronization point — and pushed byte-identical into eulogikon, EuGraphikon, and EuMorphikon so no
mirror drifts. EuKoine does not author or hold what the spec *describes*; the corpus, the v5 JSON, the
database, and the `corpus_api` implementation are **held in** the producing members (below). **CDP-057**
governs the synchronization mechanism — one canonical copy, hub-pushed mirrors, authorization-gated edits
(see `.cursor/rules/eukoine-single-source-readonly.mdc`).

**Conforming implementations (code that must match this spec — not parallel sources):**

| Layer | Implementation that conforms |
|---|---|
| v5.0 JSON validator | `SCHEMA_V5` / `validate_json_v5` in eulogikon `src/core/json_schema.py` |
| Database schema | the eulogikon Postgres DDL (`sid_text`, `token`, `overlay`, …) |
| Published API | the `corpus_api.*` views/functions — DDL is eulogikon's (`eulogikon/scripts/database/corpus_api_surface.sql`), run in eulogikon's Postgres; EuGraphikon reads them only |

The binding principles underneath everything here: **CDP-038** (`eul_wid`/`eul_aid` are
the sole identity keys), **CDP-050** (display strings are attributes, not identity),
**CDP-051** (baptismal naming), **CDP-054** (the Index Inversion — the text indexes its
references), **CDP-055** (no free-floating signifiers; no segmentation by legacy
references), **CDP-056** (schema identifiers declare their referent; the
declared-polymorphic-table exception), **CDP-057** (this document is the sole spec; one canonical copy
synchronized from the hub into byte-identical mirrors, authorization-gated edits).

---

## Part 1 — The TLA grid

Every addressable thing in the corpus is a **TLA** (Textual Location Address). Most are stable,
permanent, never-reused **proper names** (Kripkean rigid designators) — you read identity *off*
the name, never rebuilt from a description like "Iliad, book 1, line 9". The one exception is the
`rid`, which **is** a description (a range over SIDs, §1.8), not a name.

### 1.1 The TLA family

| Name | Code | Parts | Example | Names |
|---|---|---|---|---|
| **Author ID** | `aid` | 1 | `abe` | the author (Homer) |
| **Work ID** | `wid` | 2 | `abe-ac` | the work (the Iliad) |
| **Work ID** (subdivision) | `wid` | 2 | `abe-aca` | a book-subdivided work (Iliad book 1) |
| **Semantic ID** | `sid` | 3 | `abe-aca-aaa` | one clause — a unit of meaning |
| **Token ID** (*reserved*) | `tid` | 4 | `abe-aca-aaa-d` | one word inside a clause (down the road) |
| **Syllable ID** (*reserved*) | `lid` | 5 | `abe-aca-aaa-d-a` | one syllable inside a token (`{tid}-{idx}`) |
| **Phoneme ID** (*reserved*) | `fid` | 6 | `abe-aca-aaa-d-a-a` | one phoneme inside a syllable (`{lid}-{idx}`) |
| **Range ID** | `rid` | pair | `abe-aca-aaa..abe-aca-aag` (rel. `aaa..aag`) | an inclusive range of SIDs, `start..end` (a *description*, §1.8) |

> **Reserved sorts.** `tid`/`lid`/`fid` are declared here, not minted in eulogikon — Euepikon (Homer) mints `lid` (syllable) live; `fid` (phoneme) is later. **Lexeme** is *not* a TLA: it is a cross-cutting dictionary id (`lem-…`), a headword, not a location.

**Parse rules.** `eul_aid` is the first component; `eul_wid` is the first two. Owning
identity is always parseable from a **global** address by slicing the prefix — no lookup
(`eul_aid_of(sid) = sid.split("-")[0]`); the `eul_wid` begins with its `eul_aid` by
construction. **Within one work** (a v5 file, a URL) the address is serialized
**work-relative**: the `eul_wid` is stated once as the enclosing context (file head / URL path)
and the leading `{eul_wid}-` is elided (`aaa`, not `bww-br-aaa`). A single **SID composer**
re-qualifies relative → global at every boundary that leaves the work (§1.4); the relative form
is a *serialization* of the SID, **not** a second identifier — the referent is the global SID,
and the prefix-parse rule holds on the composed global form.

### 1.2 AID — the author identifier (chronological, opaque)

An `eul_aid` is **three lowercase letters** (`aaa`–`zzz`), encoding a base-26 integer
`a×676 + b×26 + c`. It is **opaque** — not derived from the author's name (Homer is
`abe`, Plato of Athens is `ffk`). Two properties:

- **Chronological allocation.** AIDs are assigned in approximate order of the author's
  *floruit*. Earliest authors (8th–7th c. BCE) get the lowest values; Byzantine/
  post-Classical the highest. The chronological reference is the WID manifest CSV under
  `work_reports/wid_manifest_*.csv` (AID-ascending = chronological order).
- **Step-of-10 spacing for insertion.** Consecutive AIDs are spaced **10 apart** in
  base-26 value, leaving 9 free slots between each pair, reserved for later authors whose
  date falls between. To insert: find the two bracketing AIDs in the manifest, take the
  midpoint of the gap, confirm it is absent from the `authors` table, assign.

### 1.3 WID — the work identifier

An `eul_wid` is the `eul_aid` followed, after a hyphen, by 2–3 positional letters (`abe-aa`,
`abe-ab`, `abe-ac`); the whole string is the work's **baptised name**. The trailing letters are
**positional, not semantic**, and are **not separately named**; the `eul_aid` is recoverable as the
leading hyphen-delimited prefix, and is itself opaque. A subdivided work is a distinct, longer
`eul_wid` (`abe-ac` and `abe-aca` are two separate baptised names); the longer sorts after the
shorter lexicographically. There is no separate "unit" layer — structural depth lives in the WID itself.

### 1.4 SID — the semantic identifier (the atom of the SID grid)

A **SID** names the **smallest addressable unit of meaning** — a clause (genre-adjusted:
a verse line, a speaker turn, a clause-group in prose, one surviving fragment). It is the
**substrate row** and the alignment/index atom.

**Encoding (the insertion grammar).** A work-relative SID is **three letters minimum**,
extensible rightward to any length:

```
aaa, aab, aac, … aaz, aba, abb, …
```

- A **three-letter** SID is original to the SID grid; a **four-letter** SID (`aawa`) is a first-round
  insertion *between* `aaw` and `aax`; a **five-letter** SID is an insertion into an
  insertion. Length carries the editorial history; no padding character is used.
- **Once issued, never reused, never moved** (once *settled* — see §3.4 on the provisional
  phase). Insertions append to the **preceding** SID: `aaw aawa aawb … aax`.

**Work-relative serialization + one composer (§1.1).** A SID's identity is the global
`{eul_wid}-{relative}` (e.g. `bww-br-aaa`). Inside a single-work context — a v5 file (§2.2) or a
URL — it is written **work-relative**, the leading `{eul_wid}-` elided because the `eul_wid` is
the enclosing context (`aaa`). This relative string is a *serialization* of the SID, never a
second identifier: the referent is the global SID (do not rename SID). A single shared **SID
composer** — mirroring `url_composer` — prepends the file's `eul_wid` to re-qualify relative →
global at **every boundary that leaves the work**: the DB PK (`sid_text.sid` is corpus-wide), the
`corpus_api`, and every cross-work consumer. Re-qualification lives in that one composer; a bare
relative reference is never emitted into a cross-work context. This is **composition** (`eul_wid`
+ relative), not reconstruction-from-a-description.

**Lexicographic sort = reading order.** Standard string comparison sorts the SID grid into
textual order under one convention: **a shorter string sorts before any string that
extends it.**

```
aaw < aawa < aawb < aawz < aawza < aax
```

Postgres, Python, JavaScript, and POSIX `sort` all implement this natively — no custom
comparator.

**Boundary policy (CDP-054 / CDP-055).** SID boundaries **follow the text's own
structure** (clauses). Do **not** let Stephanus pages, Bekker numbers, DK/SVF labels, page
breaks, or source table cells decide where a SID begins or ends. *We do not segment by
legacy references.* A legacy reference is a marginal locator that attaches to whichever
SID/RID it lands across; coincidence with a real break confers no causal role on the
reference.

**Settlement gate.** The full SID grid for a work is gated on **EuLogikon's substrate
cleaning** — the text-cleaning project that segments display blocks into clause-SIDs on
clean Greek, written through the published `corpus_api` surface. Boundaries cannot be
settled on uncleaned text (residual Latin, OCR artefacts, mis-segmentation), so SIDs
remain **provisional** — and are **re-keyed** when they move — until that work's clauses
are cleaned and frozen. A SID is **settled** (permanent, §3.4) when the cleaning project
has fixed that work's clause grid.

### 1.5 TID — the token identifier (down the road)

**Reserved — not minted in eulogikon.** Euepikon mints it live for the Homer slice;
**EuMorphikon is the corpus-scale minter** — it holds (is the custodian of) the single frozen tokenisation spec from
which `tid` derives. **EuGraphikon consumes `tid`-keyed data; it does not mint `tid`.**

A **TID** is one word inside a clause: `{sid}-{base26(token_position)}`, **dash-delimited**
— e.g. `bww-br-aaa-d` (token 4 of clause `aaa`). The dash is **load-bearing**: a dash-less
form would collide with the interpolated SID `aawa` (the first
insertion after `aaw`) — one signifier, two referents. The dash resolves it, and because
`-` (U+002D) sorts below every letter, "plain string comparison = reading order" extends to
the token grid for free (`aaw-d < aawa-a < aawb-a`).

TID is **derived, never stored in the canonical**: `TID = (sid, token_idx)` is
deterministic on (frozen text, frozen SID grid, one tokenisation spec). Storing a token
array would couple the inviolable record to a tokeniser version.

The dash-delimited `{sid}-{token}` is canonical (a dash-less form collides with an
interpolated SID, as above). A TID never collides with an RID **by construction**: the location
chain (SID/TID/LID) is `-`-joined, an RID range carries the `..` operator (§1.6) — `aaa-d` (TID)
and `aaa..aag` (RID) are categorically distinct, read from the string itself, with no part-count
or context disambiguation.

### 1.6 RID — any qualified range (how blocks are built)

An **RID** is the pair `(sid_start, sid_end)` — **the same structural type at any size,
qualified by a role**. It is serialized `start..end` with the **`..` range operator**, both ends
at the same grain: global `abe-aca-aaa..abe-aca-aag`, or work-relative `aaa..aag` (§1.4).
Splitting on `..` yields the two end SIDs directly. The `..` marks a **range** (a pair),
categorically distinct from the `-`-joined location chain, so an RID never collides with a TID
(§1.5); a single SID (`aaa`) **is** the degenerate RID.

**This is how SIDs and RIDs build blocks of text.** A block — a verse line, a sentence, a
speaker turn, a paragraph, a quoted passage, a whole book, an embedding chunk — is *the
same construct*: a RID over a contiguous run of SIDs, differing only in its **role
qualifier**. There is no separate "block" type.

- A single-clause block is the **degenerate RID** (`abe-aca-aaa`, start = end).
- A multi-clause block is a real range (`abe-aca-aai..abe-aca-aaj`; work-relative `aai..aaj`).
- The role qualifier names what the range plays: `render_block` (display), `chunk`
  (retrieval), `verse`, `quotation`, `book`. The *embedding granule is one role an RID
  plays, not its definition.*

### 1.7 Worked example — Homer's proem (SID atoms → RID blocks)

Homer = `abe`; Iliad = `abe-ac`; Iliad book 1 = `abe-aca`. Segment by clause:

```
Iliad 1.1–1.9                                       SID          block status
─────────────────────────────────────────────────────────────────────────────
1  μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος                aaa          1 clause
2  οὐλομένην, ἣ μυρί' Ἀχαιοῖς ἄλγε' ἔθηκε,          aab          1 clause
…  …                                                …            …
7  Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.        aag          1 clause
8  τίς τ' ἄρ σφωε θεῶν ἔριδι ξυνέηκε μάχεσθαι;       aah          1 clause
9  Λητοῦς καὶ Διὸς υἱός·                             aai  ┐       1 verse,
   ὃ γὰρ βασιλῆϊ χολωθεὶς …                          aaj  ┘       2 clauses
```

The *same atoms* yield every block, by choosing the span and the role:

| Block | SID span | RID | role |
|---|---|---|---|
| Verse line 1 | `aaa` | `abe-aca-aaa` (degenerate) | `verse` |
| Verse line 9 | `aai…aaj` | `abe-aca-aai..abe-aca-aaj` | `verse` |
| The invocation sentence (1–7) | `aaa…aag` | `abe-aca-aaa..abe-aca-aag` | `render_block`/`paragraph` |
| The whole proem (1–9) | `aaa…aaj` | `abe-aca-aaa..abe-aca-aaj` | `quotation` |

A legacy reference rides *on* the block, never defines it: `Il. 1.9` is a
`legacy_reference` overlay anchored to `abe-aca-aai..abe-aca-aaj`. You find the verse by its RID and
read off `Il. 1.9`; you never search `Il. 1.9` to find the verse (CDP-054).

### 1.8 The aliasing ban — a rigid name is not a description, and neither is aliased

Two kinds of address, held apart:

- **`SID`, `AID`, `WID`, `TID` are rigid designators** — Kripkean proper names. A SID names
  one clause in every context; it is baptised once, never re-derived from a description,
  never reused, never moved (once settled). You read identity *off* it.
- **An `RID` is a description**, not a name: "the run of SIDs from `sid_start` to `sid_end`,
  in role *R*." It denotes *compositionally* — by the SIDs it spans and its role qualifier —
  and is computed or quoted, never baptised.

From this, one ban: **a signifier denotes exactly one referent — no aliasing.** An address
is never equated with a chain of other names or descriptions:

```
rid  ≠  «a clause's trailing letters»  ≠  unit_ref  ≠  «the King of France»  ≠  «Big Mac and fries»
```

And a description **never hardens into identity**: an RID used *as the name of its range* is
"the King of France" wearing a proper name's clothes — a description masquerading as a rigid
designator. The legacy **`unit_ref` is the disease named**: one slot that was at once a
locator, a key, a label, and a row-identity. The cure is the split this document makes — the
**SID is the only identity**; the **RID describes** a run of SIDs and is always role-qualified
(`render_block` | `chunk` | `verse` | …); a **legacy reference attaches** (CDP-054), never
names. A description never mutates into a name, and no name ever carries two referents
(CDP-055). Every column, table, and address obeys it: self-identifying, one referent, no alias.

**No part of a designator is given a substitute name.** An AID's value is not a "code"; a WID's
work-distinguishing letters are not a "suffix"; a SID's work-relative letters are not a "tail." Each
rung is named only as the designator it is, and where its construction must be described it is
described **positionally** ("the `eul_aid` followed by 2–3 letters"), never baptised with a borrowed
noun. Answering a correction with a *new* synonym is the disease, not the cure: **delete the noun, do
not rename it.**

---

## Part 2 — The v5.0 canonical work JSON

**Status: PROPOSED and gated.** No live work is v5 yet; the live validator still requires
v3.0. `validate_json_v5` (eulogikon `src/core/json_schema.py`) is the conforming reference
implementation behind `format_version: "v5.0"` and does not yet replace `SCHEMA_V3`. v4.0
(inline `{sid_abc}` markers) is **skipped**.

### 2.1 Why v5 exists

v5 is **the Index Inversion made physical** (CDP-054): pristine monolingual Greek keyed by
settled SID in the flat `sid_text` SID grid; everything else — references, speakers, display
blocks, apparatus, Latin, translations — is a **keyed overlay**, never inline pollution.
The v3 `units[]` array **dissolves** (it is not renamed): a "unit" was the source edition's
*display block*, a free-floating signifier hiding a grain confusion (CDP-055).

### 2.2 The SID grid (v5 JSON)

One file per work: `data/works/grc/{work_display_string}-{eul_wid}.json` (CDP-050), written
only after SIDs are settled.

```json
{
  "eul_wid": "bww-br",
  "eul_aid": "bww",
  "format_version": "v5.0",
  "sid_text": [
    { "sid": "aaa", "text": "Καὶ οὐκ εἶπε τῇ μητρὶ τοῦ τέκνου τὴν μέλλουσαν σφαγήν" },
    { "sid": "aab", "text": "…", "sid_type": "content" },
    { "sid": "aac", "text": "", "sid_type": "lacuna", "gap_extent": { "chars_est": 40 } }
  ]
}
```

`eul_wid` is stated once at the head; every `sid` (and overlay `rid`) is the **work-relative
serialization** (§1.4) — the leading `{eul_wid}-` elided, the composer re-qualifying to the global
`bww-br-aaa` at every boundary that leaves the file. Each row of the SID grid carries **only** `sid`
+ `text`, plus optional `sid_type` and `gap_extent`.

### 2.3 The total SID grid — `sid_type`

Every addressable position is on the SID grid; damaged text is **typed, never dropped**.
Embeddability is *derived* (`embeddable ⇔ sid_type = 'content'`), not an authored tag.

| `sid_type` | `text` | embedded | role |
|---|---|---|---|
| `content` (default) | clean Greek clause | yes | a semantic unit |
| `scrap` | surviving sub-clausal ink | no | real transmitted text, too broken to cohere |
| `lacuna` | `""` (empty) | no | a known gap; `gap_extent` records the loss |

### 2.4 The overlays — one polymorphic array

`overlays[]` is **one polymorphic array** discriminated by `overlay_kind`. Every column is
`overlay_`-qualified under the **CDP-056 declared-polymorphic-table exception**: the
`overlay_kind` discriminator supplies each wrapper column's referent at row grain.

```json
{
  "overlays": [
    { "rid": "aaa..aab",
      "overlay_kind": "render_block", "overlay_class": "paragraph" },
    { "rid": "aaa",
      "overlay_kind": "legacy_reference", "overlay_scheme": "stephanus",
      "overlay_value": "327a", "overlay_display": "show" },
    { "rid": "aaa",
      "overlay_kind": "sigil", "overlay_class": "deletion",
      "overlay_window": "Τάχα δέ [γε] ἐπειδὰν", "overlay_display": "suppress" }
  ]
}
```

The closed kind-set and what each populates:

| `overlay_kind` | anchor (`rid`) | populated columns |
|---|---|---|
| `legacy_reference` | SID / range | `overlay_scheme`, `overlay_value`, `overlay_display` |
| `render_block` | range (`start..end`) | `overlay_class` (`line`\|`paragraph`\|`turn`\|`title`\|`hypothesis`\|`prologue`\|`subscriptio`\|`list`\|`list_item`\|`stanza`) |
| `speaker` | SID (turn-start) | `overlay_value` (the name) |
| `marginalia` | SID / range | `overlay_value` |
| `sigil` | SID + `overlay_window` (sub-token) | `overlay_class` (`supplement`\|`deletion`\|`crux`\|`lacuna`), `overlay_window`, `overlay_display` |
| `citing_author` | SID / range | `overlay_value` (citing author/work); home of the FGrH capital-`T` testimonia |
| `latin_apparatus` | SID / range | `overlay_value` (the relocated Latin text) |

Notes that matter:

- `legacy_reference` schemes: `line`\|`book_line`\|`book_chapter_line`\|`stephanus`\|`bekker`\|`dk`\|`svf`\|`fgrh`\|`page`\|`folio`.
- **`testimonium` is not a kind** — testimonia fold into `citing_author` (the FGrH witness family).
- **Sigils anchor by content-window, not position.** Editorial marks (`[ ] ⟨ ⟩ †`) sit
  *sub-token* (`Ἀκουσί[λ]αος`), below the token grain, so they anchor by a clean-Greek
  context window located by *unique content match* (the keyed-window binding). The
  `overlay_window` carries the mark **in place** (bound, not stripped-and-restored); the
  projector renders it at the located position. This survives re-segmentation; raw
  character offsets would not.
- **Legacy references anchor at SID/RID granularity, never sub-SID** — a Stephanus number
  is a coordinate on a printed page, not a pointer to a word.
- **The overlay anchor is the `rid`** (a work-relative SID, or `start..end`), replacing
  `sid_start`/`sid_end`; the loader splits on `..` and the composer qualifies both ends.
- **Provenance is the file's, not the row's.** One v5 file is **one edition/manuscript**, so the
  source is a property of the file (its work-edition), stated once — never an `overlay_source` on
  every row. The build-time `overlay_anchor` (a folded-Greek alignment aid) likewise leaves canonical
  v5 for a build audit; both are recoverable there, neither is canonical meaning.

### 2.5 What the validator enforces

`validate_json_v5` ([`src/core/json_schema.py`](../../src/core/json_schema.py)) asserts:

- required `eul_wid`, `eul_aid`, `format_version` (`^v5\.0$`), non-empty `sid_text`;
- `eul_aid == eul_wid.rsplit("-", 1)[0]`;
- each `sid` is a **bare work-relative token** (no `{eul_wid}-` prefix — the head supplies it),
  is **unique**, and is **strictly ascending** (= SID grid order);
- valid `sid_type`; `gap_extent` only on a `lacuna`; a `lacuna`'s text is `""`; non-lacuna
  text is non-empty;
- `text` is **NFC** and carries **no Latin letter** (CDP-053);
- every overlay carries a `rid` (a work-relative SID, or `start..end`) whose ends resolve to a
  **known sid under the work** (no dangling anchors); the **per-kind required fields** hold (§2.4);
  valid `render_block`/`sigil` class; a `sigil`'s `overlay_window` is unique within its SID.

### 2.6 Keyed translation overlay (Layer 2)

Translation is a **pure `rid` → phrase map** on the settled SID grid — no Greek copy, no
post-hoc alignment (`no_alignment_after_translation`). The key is a **work-relative RID**: a
bare SID (the degenerate RID — a range of one) or a range `start..end` (§1.6). A range keys one
phrase to several Greek clauses at once — a translation unit need not be one clause, which
removes the false "one Greek clause ↔ one English sentence" constraint. The RIDs **partition**
the grid — non-overlapping (no SID translated twice) over known SIDs; drift detection is one set
comparison, the SIDs the RIDs span vs the Greek content grid (a content SID no RID covers is
untranslated, never double-covered).

```json
{
  "eul_wid": "bww-br", "eul_aid": "bww", "format_version": "v5.0", "lang": "en",
  "phrases": {
    "aaa": "And he did not tell the child's mother of the impending slaughter",
    "aab..aac": "the rest of the sentence, spanning two Greek clauses"
  }
}
```

---

## Part 3 — The database schema (target v5 shape)

The DDL below is the **target shape**, not a migration to apply as-is. The DB is the shared
corpus store; it is held in and written by eulogikon, and every other family member reads it.

### 3.1 The SID grid (database) — `eulogikon.sid_text`

The computable mirror of the v5 SID grid; the successor to `units_index`'s clean-text column,
now keyed by `sid` rather than a free-text `unit_ref`.

```sql
CREATE TABLE eulogikon.sid_text (
    sid         TEXT PRIMARY KEY,                       -- 'bww-br-aaa'; permanent once settled
    eul_wid     TEXT NOT NULL REFERENCES eulogikon.works(eul_wid) ON DELETE CASCADE,
    text        TEXT NOT NULL,                          -- NFC, transmitted, punctuated ('' for lacuna)
    sid_type    TEXT NOT NULL DEFAULT 'content'
                CHECK (sid_type IN ('content','scrap','lacuna')),
    gap_extent  JSONB,                                  -- lacuna only
    sort_key    TEXT NOT NULL                           -- = sid; lexicographic = reading order
);
```

`eul_wid` is stored as an FK guard but is *derivable* from `sid` (the FK is never the
identity source). There is **no embedding column** and **no stored fold**: `grc_fold` (the
accent-blind form) is a *functional index expression* over `text`, computed at query time,
never authored.

### 3.2 The token grid — `eulogikon.token` (derived from `sid_text.text`)

```sql
CREATE TABLE eulogikon.token (
    sid         TEXT NOT NULL REFERENCES eulogikon.sid_text(sid) ON DELETE CASCADE,
    token_idx   INTEGER NOT NULL,                       -- 0-based, within sid
    surface     TEXT NOT NULL,                          -- NFC word form
    char_start  INTEGER NOT NULL,                       -- offset into the frozen sid_text.text
    char_end    INTEGER NOT NULL,
    tok_ver     SMALLINT NOT NULL,
    lemma       TEXT, upos TEXT, feats JSONB,           -- morphology (Phase 2+)
    PRIMARY KEY (sid, token_idx, tok_ver)
);
```

A token is a **surface word** (a maximal run of Greek letters + diacritics + a trailing
elision apostrophe). Crasis (`κἀγώ`) and elision (`δ’`) are **one surface token each**;
lexical decomposition is a UD-style multi-word annotation in the morphology layer, never a
re-tokenisation. Tokens are versioned (`tok_ver`); re-tokenisation is the only event that
moves a token index.

### 3.3 The overlay store — `eulogikon.overlay`

> The CDP-056 declared-polymorphic-table exception in action — one dense table, one XOR
> dispatch on `overlay_kind`, per-kind `CHECK` constraints.

```sql
CREATE TABLE eulogikon.overlay (
    id             BIGSERIAL PRIMARY KEY,
    sid            TEXT NOT NULL REFERENCES eulogikon.sid_text(sid) ON DELETE CASCADE,
    sid_end        TEXT REFERENCES eulogikon.sid_text(sid),  -- set ⇒ anchor is the RID sid..sid_end
    overlay_kind   TEXT NOT NULL,        -- legacy_reference|render_block|speaker|marginalia|
                                         -- sigil|citing_author|latin_apparatus
    overlay_window TEXT,                 -- sigil only: the sub-token content-window
    is_insertion   BOOLEAN NOT NULL DEFAULT FALSE,
    overlay_scheme TEXT,                 -- legacy_reference: stephanus|bekker|dk|svf|fgrh|page|folio|…
    overlay_class  TEXT,                 -- sigil / render_block subtype
    overlay_value  TEXT,                 -- the payload (citation|speaker|content|citing author|Latin)
    overlay_display TEXT NOT NULL DEFAULT 'show',  -- show|suppress (per-kind default otherwise)
    confidence     REAL,
    align_ver      SMALLINT NOT NULL,
    CONSTRAINT overlay_scheme_required_for_legacy_reference
        CHECK (overlay_kind <> 'legacy_reference' OR overlay_scheme IS NOT NULL)
);
```

`overlay_source` and `overlay_anchor` are **not** columns: one v5 file is one edition, so provenance
is the work-edition (`work_editions`), recorded once; `overlay_anchor` is a build-time aid kept in the
build audit. Both are recoverable off-canonical; neither is downstream meaning. The overlay's `rid`
(v5, work-relative) loads to the composed global `sid`/`sid_end` above.

**Sigil disposition** (the substrate stays bare Greek; marks become overlay rows):

| Sigil | Editorial act | In substrate? | Overlay |
|---|---|---|---|
| `⟨X⟩` | editor **supplied** X | X absent | `sigil`/`supplement`, `is_insertion`, `overlay_value=X` |
| `[X]` | suspected interpolation | X present | `sigil`/`deletion`, `overlay_window` over X |
| `†X†` | crux (corrupt) | X present | `sigil`/`crux`, `overlay_window` over X |
| lacuna | text lost | nothing / stub SID | `sigil`/`lacuna`, `is_insertion` |

### 3.4 Layer-2 authored analysis, and embeddings

```sql
CREATE TABLE eulogikon.concept_tag (        -- e.g. #φύσις on a SID
    sid TEXT NOT NULL REFERENCES eulogikon.sid_text(sid) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (sid, tag)
);
CREATE TABLE eulogikon.translation (        -- keyed-translation overlay, RID-keyed (§2.6)
    sid_start TEXT NOT NULL REFERENCES eulogikon.sid_text(sid) ON DELETE CASCADE,
    sid_end   TEXT NOT NULL REFERENCES eulogikon.sid_text(sid) ON DELETE CASCADE,
                                             -- = sid_start for a degenerate RID (a range of one)
    lang  TEXT NOT NULL,                     -- 'greole-en'|'de'|'ru'…
    text  TEXT NOT NULL, notes JSONB,
    PRIMARY KEY (sid_start, sid_end, lang),
    CHECK (sid_start <= sid_end)             -- a range; degenerate when equal
);
```

- **Morphology** lives on `token` (`lemma`, `upos`, `feats`).
- **Embeddings** live on **`embedding_chunk`** (a size-bounded RID, ≤1500 chars), vector
  **`rid_embedding`** (`vector(768)`) — *never* a `sid_text` column, because a per-clause
  vector cannot compose a chunk vector. `search_*_semantic` still *returns* SIDs.
- `concept_tag` is a domain-held annotation keyed to a SID; `translation` is keyed to a **RID**
  (§2.6 — a range of one for a single clause) — both **not** overlay kinds.

**Provisional vs settled SIDs.** During the substrate build (§1.4 settlement gate), SIDs
are *provisional* (an unsettled name) and may move through a settling phase; embeddings
and overlays ride provisional SIDs and are **re-keyed** when one moves. SIDs are cast as
**settled** (permanent, never reused, never moved — §1.4) only when EuLogikon's substrate
cleaning has fixed that work's clause grid. The v5 *JSON* is written only with settled
SIDs. While passage identity remains provisional, cognitive heads obey
[`.eukoine/interim_head_citation.md`](interim_head_citation.md).

### 3.5 The published contract — `corpus_api.*`

**`corpus_api_version 0.4.0`.** This document **defines and versions** the API **contract** — the
names/signatures/version — as the family's synchronized statement of it. The **implementation is held in
eulogikon**: the canonical DDL (`eulogikon/scripts/database/corpus_api_surface.sql`), the apply, and the
live-DB-vs-DDL drift guard (`eulogikon/scripts/audit/check_corpus_api_drift.py`) — the bytes always run
in eulogikon's Postgres (EKDP-001). A DDL-vs-contract drift is an eulogikon-side defect. EuGraphikon **consumes it read-only**. Physical `eulogikon.*`
tables are private; consumers read the `corpus_api` schema only. A change to the published
names/signatures is a change to this document and a version bump — nowhere else.

**Published views** (over private physical tables): `corpus_api.authors`,
`corpus_api.works`, `corpus_api.work_editions`, `corpus_api.sid_text`, and **`corpus_api.overlay`** —
the keyed attachment surface (legacy_reference, speaker; §2.4/§3.3) that consumers JOIN to a `sid`,
never the spine.

**Published functions:**

| function | status | returns |
|---|---|---|
| `get_work_sids(eul_wid)` | live | `setof sid_text` in reading order |
| `search_sids_fulltext(query, max_rows)` | live | accent-sensitive FTS |
| `search_sids_trigram(query, max_rows)` | live | accent-blind via `grc_fold` |
| `search_sids_semantic(query_embedding vector, max_rows)` | **reserved** (fails loud) | until row-grain `vector(768)` embeddings land |
| `search_sids_lemma(query, max_rows)` | **reserved** (fails loud) | until the token/lemma grid is built |
| `get_sid_context(sid, window)` | live | ±window neighbours |

**Status is the 0.4.0 *contract* state, not a live-DB claim.** The 0.4.0 surface is realized in the
live DB when the DDL (`eulogikon/scripts/database/corpus_api_surface.sql`) is applied; before that apply
`search_sids_fulltext`/`_trigram` ran in their prior 0.3.0 shape and `get_work_sids` /
`get_sid_context` (new at 0.4.0) were not yet present. A reserved function **raises** rather than
returning wrong rows (Modus Tollens, never a silent stub — CDP-037).

**Phase-1 interim grain (important).** Until the §1.4 settlement gate closes for a work,
the published `corpus_api.sid_text` view exposes one **`units` display-block** per row,
with a *provisional* `sid = units.id`. **A display-block is not a final SID, and a
passage is never a SID.** At the v5 cutover the view body repoints (`units` → the
segmented SID grid) and one display-block becomes *many* SIDs; the published signatures
do **not** change. **How cognitive heads cite meanwhile** —
[`.eukoine/interim_head_citation.md`](interim_head_citation.md) (blessed here; not
re-stated).

**Phase-1 interim published columns.** Until the grid mint, the two published views expose a *reduced*
column set (declared here so the surface is not shipped-but-undeclared): `corpus_api.sid_text` publishes
`(sid, eul_wid, text, sid_type, sort_key)` — `gap_extent` (§3.1) arrives with the lacuna model, and the
interim **adds** `sort_key` to carry reading order (the provisional `sid = units.id` does not string-sort
into it). `corpus_api.overlay` publishes `(sid, sid_end, overlay_kind, overlay_value)`; `overlay_scheme`
(the §3.3 `CHECK`-required field for `legacy_reference`) and the remaining §3.3 columns arrive when the
real `eulogikon.overlay` table replaces the interim `units.ref` / `units.speaker` projection. Published
signatures do **not** change then (§3.5).

### 3.6 Dissolution + rename map (live → corpus_api / v5)

Every retired physical identifier and the canonical name that replaces it. The `corpus_api.*`
published names are the stable interface — they do **not** change across the v5 cutover (§3.5); under
the hood they map to the live schema today and repoint to the SID/RID grid at v5. A consumer naming a
left-column identifier is bound to a name the contract retires (propagation matrix:
`tooling/graphspine/propagation_matrix/retired-schema-names.md`).

**Tables and columns:**

| live (from) | v5 (to) | verb |
|---|---|---|
| `units_index` (table) | **becomes `sid_text`** (re-keyed `unit_ref` → `sid`) | re-key |
| `units` (table) | **dissolves** → `sid_text` (clauses) + `render_block` overlay + `speaker` overlay | split |
| `units.ref`, `units_index.unit_ref` | `legacy_reference` overlay rows | relocate, then delete the column |
| `units_index.reference_context` | **dissolves** (a denormalized join-cache) | delete |
| `units_index.has_witness` | `has_citing_author` (derived: presence of a `citing_author` overlay) | de-Latinize |
| `work_editions.recension` | **`edition`** (in-place column rename; PK `(eul_wid, edition, lang)`) | rename |

**Published functions** (the consumer re-points to the `corpus_api` name; the §3.5 signatures are
stable across the cutover):

| live (from) | corpus_api (to) | verb |
|---|---|---|
| `get_work_units(eul_wid)` | `get_work_sids(eul_wid)` | rename |
| `search_units_fulltext(query, …)` | `search_sids_fulltext(query, max_rows)` | rename |
| `search_units_trigram(query, …)` | `search_sids_trigram(query, max_rows)` | rename |
| `get_unit_context(…)` | consumer calls `get_sid_context(sid, window)` | re-point — eulogikon's own `get_unit_context` **stays** (it serves eulogikon's generators); only the cross-repo call moves |

**Wave B — `pending_research`, waits for the SID/RID grid to freeze** (re-keying before the RID key
exists would mint against an unsettled grid):

| live (from) | v5 (to) | verb |
|---|---|---|
| `embedding_units(ordinal)` (EuGraphikon) | `embedding_chunk` keyed by `rid` (`ordinal → rid`) | re-key |

**De-Latinization of the metalanguage:** `witness` → `citing_author`/`citing_work` — **the attestation
sense only** (the `has_witness` flag / FGrH citing family); a *corroboration-source* "witness" (e.g. an
independent line count used to cross-check) is a **different referent**, named locally, not this rename.
`testimonium` → `testimony` (a classification value, never an overlay kind); `recension` → `edition`.
Naturalised English with Latin roots (`fragment`, `edition`, `author`) stays. **No external scheme is
ever an identity layer** — CTS-URN, TLG canonical refs, TEI citation are rejected; legacy schemes are a
one-way courtesy crosswalk frozen at ingestion (an external scheme is a gravity well — it crashed
Eulogikon v1).

---

## Part 4 — How the implementations line up

The v5 JSON `sid_text` array and the DB `sid_text` table are two **implementations** of the one SID grid
defined in Part 1. They differ in **one** deliberate way — the JSON serialises identity **work-relative**
(the `eul_wid` is the file head), the DB stores it **global** (the corpus-wide PK) — and the single SID
composer (§1.4) maps between them; otherwise they conform field-for-field:

| concept | this spec | v5 JSON (`SCHEMA_V5`) | DB `eulogikon.sid_text` |
|---|---|---|---|
| identity | global `sid` (`{eul_wid}-{rel}`) | `sid` = **work-relative** (`aaa`) | `sid` = **global** (PK), composed |
| containing identity | `eul_wid`/`eul_aid` | `eul_wid`/`eul_aid` (head, once) | `eul_wid` (FK guard) |
| text | `text` | `text` | `text` |
| type | `sid_type` | `sid_type` | `sid_type` |
| gap | `gap_extent` | `gap_extent` | `gap_extent` |

The overlay wrapper columns are `overlay_`-qualified identically in the JSON `overlays[]` and the DB
`eulogikon.overlay` table; the JSON's work-relative `rid` maps to the DB's composed global
`sid`/`sid_end` (§3.3). Neither carries `overlay_source` (the file's edition) or `overlay_anchor` (a
build aid). Three points an implementation must match (settled here, not
negotiated elsewhere): the SID grid uses `sid_type`/`gap_extent`, never bare `type`/`extent`;
a TID is dash-delimited (`bww-br-aaa-d`), never dash-less; there is **no per-SID embedding**
— the vector lives on `embedding_chunk` as `rid_embedding`.

---

## Part 5 — Conforming implementations

This document is the source. The following code conforms to it, and is corrected (never the
reverse) if it diverges:

- **v5 JSON validator** — `SCHEMA_V5` / `validate_json_v5`, eulogikon `src/core/json_schema.py`.
- **Database DDL + published API** — the physical substrate (`eulogikon.sid_text` / `token` /
  `overlay` / `concept_tag` / `translation`) is eulogikon's, under eulogikon `scripts/database/`; the
  **`corpus_api.*` surface DDL is eulogikon's** (`eulogikon/scripts/database/corpus_api_surface.sql`),
  eulogikon-applied, with the live-DB-vs-DDL drift guard at `eulogikon/scripts/audit/check_corpus_api_drift.py`.
- **Read-only consumer** — EuGraphikon's corpus query seam (`corpus_query_eulogikon.py`).

The interim head-citation contract while passage identity is provisional lives in
[`.eukoine/interim_head_citation.md`](interim_head_citation.md) (blessed by §3.4/§3.5
here). There is no other companion specification, inventory, or ADR to keep in sync.
