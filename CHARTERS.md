# Capability charters: Tekmeria

- **Title:** Capability charters, Tekmeria (`eulogikon-semeia`)
- **Status:** active
- **Authority_level:** member charters. One file rather than a directory: this
  is a small member with five capabilities, and family law permits the single
  file at this size.
- **Scope:** every capability this repo holds or will hold.
- **Relationship_to:**
  - shape: `governance_cluster/capability_port.md` (TDP-010)
  - placement: `governance_cluster/functional_concern_homes.yaml`

Each charter names one capability, the invariant it holds, its owner, its port,
and its adapters. A capability with no named invariant is not a capability here:
it is a function, and it does not need a charter.

Status vocabulary: **live** (built and holding), **reserved** (chartered, not
yet built), **partial** (built, invariant not yet held by construction).

---

## CH-01 : composition state

**Status:** reserved

**Invariant.** The state of a composition has one writable home, and a station
moves `pending` to `drafted` to `checked` only through the defined operations.
There is no second path to composition state.

**Owner.** The store driver, `composition_cluster/`.

**Port.** Record a candidate set with its generating query, timestamp, and
counts. Open a station with its disposition and anchor set. Write a block.
Append an index row. Register a claim. Record a verification result. Read the
index. Read a chunk's blocks.

**Adapters.** SQLite, today. The shared Postgres schema, later. That second
adapter is why the port exists: the fold is mechanical exactly when the target
is a second adapter behind an existing port.

**Falsifiers.** Composition state written anywhere but through the port. A
status transition performed by an update rather than an operation. An untyped
record crossing the boundary.

---

## CH-02 : corpus read

**Status:** reserved

**Invariant.** Every corpus read in this repo flows through one surface, and
that surface is read-only by construction rather than by intention.

**Owner.** The corpus reader, `composition_cluster/`.

**Port.** Fetch a unit's Greek by id. Resolve catalog fields for a unit.
Resolve a canonical work URL. Run the recorded candidate query. Read the
blacklist rows.

**Adapters.** The shared Postgres, read through `corpus_api`, on a read-only
role derived once and failing closed with no fallback to owner credentials.

**Falsifiers.** A connection opened outside the reader. Corpus SQL composed in
a consumer. A read against a physical `eulogikon` table rather than the
published contract. A credential fallback that silently escalates.

**Present-tense gap.** Composition currently reads physical tables directly via
an MCP tool, with no owner module. That is the partial state this charter
exists to close, and it is why the charter is reserved rather than live.

---

## CH-03 : verification

**Status:** reserved

**Invariant.** A check exists when it has a record. The report is generated
from the store and from live re-checks, never written from memory of having
looked.

**Owner.** The verification producer, `composition_cluster/`.

**Port.** Match every quoted span against the corpus now. Back-check every
translation line against its Greek. Reconcile coverage against the candidate
set. Reproduce every printed count by its recorded query. Check period claims
against station type. Check the claims register against the finished
arrangement. Scan the prose against the live blacklist and for U+2014.

**Adapters.** The store, and the corpus reader (CH-02).

**Falsifiers.** A pass asserted with no per-item line. A report written by hand.
A station marked checked with an empty verification record.

---

## CH-04 : page projection

**Status:** reserved

**Invariant.** The published page is a function of the store. Running the
projection twice on an unchanged store produces an unchanged page, and the page
holds no fact the store does not.

**Owner.** The projector, `composition_cluster/`.

**Port.** Project one completed composition to HTML. Report what a projection
would change without writing.

**Adapters.** The site template and the CSS chrome.

**Falsifiers.** Editorial judgment inside the projection. A hand edit to a
published page that the store would not reproduce. A page fact with no store
row.

---

## CH-05 : site registry

**Status:** live

**Invariant.** `posts.json`, the index cards, and the sitemap agree. They cannot
drift apart silently.

**Owner.** `site_cluster/site_build_index.py`.

**Port.** Sync derived files from `posts.json`. Check without writing.

**Adapters.** None; it is a pure file transform.

**Falsifiers.** A published essay absent from any of the three. A hand edit to a
derived file. CI passing while they disagree.

**Note.** This is the one capability already live, and it is live precisely
because CI fails when the check fails. It is the worked example of what the
other four are aiming at.
