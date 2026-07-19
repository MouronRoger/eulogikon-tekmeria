# The witness ledger

The ledger is the persistent state of a Tekmerion composition. It is built in
full before any prose is written, updated as stations are drafted and
verified, and read first on every resumed session. It is a working file, not
part of the published piece; keep it beside the draft as
`<term>_ledger.md`.

## Format

A markdown table, one row per corpus **unit** (not per token). Columns:

| # | unit_id | wid | ref | author | affil | period | domain | station_type | disposition | reason | status |

- **#**: sequence position in the trajectory (assigned in Phase 3; blank until
  then). Set-asides keep no sequence number.
- **unit_id**: eulogikon.units.id, the verification anchor. The ref string is
  for humans; the unit id is what quotations are checked against.
- **station_type**: what kind of witness this is. Use the STYLE.md vocabulary:
  original speech, dialogue, medical treatise, doxography, testimonium,
  fragment-in-later-author, scholium, lexicon, commentary, hostile report,
  letter, historiography. Add to this list only from the evidence, not from
  convenience.
- **disposition**: `station` | `secondary` | `set-aside`.
- **reason**: required for every `set-aside`; recommended for `secondary`.
  Within the declared complete-coverage set the only valid set-aside reasons
  are: `proper-name`, `duplicate-station of <unit_id>`, `corrupted-unit`,
  `quotes <unit_id>`.
- **status**: `pending` | `drafted` | `verified`.

## Header block

Above the table, record once:

- term and word-family queried (all lemmata, including privatives)
- controlling question and hinge (as confirmed at the Phase 1 gate)
- complete-coverage set definition (the exact DB predicate, e.g.
  `authors.affiliation = 'stoic'`)
- trajectory type
- date of the ledger build and the DB counts at that date (units matched,
  tokens, distinct authors), so drift is detectable on resume

## Duplicate stations

The corpus can hold the same sentence at two addresses: a fragment-collection
work (e.g. a von Arnim volume under the fragmentary author's wid) and the
quoting source's own text (e.g. Diogenes Laertius). These are one witness at
two stations. Rule: the **source author's unit is the station** (the witness
that actually survives); the fragment-collection unit is `set-aside:
duplicate-station of <unit_id>`, and the fragment number is noted in the
station's citation or commentary so the reader can find it in the standard
collection. Never count the pair as two attestations in any table.

## Corrupted or unsegmented units

A unit whose text is a concatenation of many passages under one ref (visible
by anomalous length or internal citations) cannot supply a citation from its
ref field. Mark it `corrupted-unit`; locate the relevant passage inside it and
supply the locus by hand from the internal apparatus; report the defect in the
piece's corpus-boundaries section; and flag it upstream to the corpus project.
