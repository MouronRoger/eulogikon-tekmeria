# Interim head citation — before the SID grid settles

**Status:** Authoritative and complete. This document defines how **cognitive heads**
(RAG agents, translators, memory machinery) cite and anchor passage identity while the
SID grid remains **provisional** (§1.4 settlement gate not yet closed for a work). It is
part of the `.eukoine/` single source (EKDP-032 / CDP-057): one canonical copy, edited at the EuKoine
hub and synchronized byte-identical into eulogikon, EuGraphikon, and EuMorphikon (a mirror is never
hand-edited). The identity grid, v5 format, schema,
and `corpus_api` contract remain in
[`.eukoine/corpus_identity_and_schema.md`](corpus_identity_and_schema.md).

**Scope:** consumer citation and durable-memory behaviour during the pre-settlement regime
only. When a work's SIDs are **settled** (§1.4), heads cite by `sid` / `rid` as that
spec defines; this document does not apply to settled passage identity.

---

## 1. Settled identity today — `eul_aid`, `eul_wid`

`eul_aid` and `eul_wid` are **settled rigid designators today**. Heads cite authors and
works by these keys and may store them in **durable memory** (translation decisions, memory
facts, adjudicated readings). Display strings are attributes fetched *from* the key, never
substitutes for it (CDP-038 / CDP-050).

---

## 2. No settled passage identity yet

There is **no settled passage identity** to cite while the SID grid for a work remains
provisional. A head **locates** a passage by the conjunction:

| anchor | role |
|---|---|
| `eul_wid` | which work |
| quoted Greek | which clause-group (content fingerprint) |
| `legacy_reference` | when present — the scholar's coordinate (overlay grain; not a key) |

A head **never manufactures a SID** — never assigns, coins, or persists a provisional
`sid`, ordinal, or display-block id *as if* it were passage identity.

---

## 3. Session-scoped handles — re-fetch only, never citation

The published interim surface (§3.5 of the identity spec) exposes provisional row handles:

- `{eul_wid}#{ordinal}` — retrieval doc-key form
- provisional `sid = units.id` — display-block stand-in
- `sort_key` — reading order within a work

These are **in-session pointers to re-fetch text** from `corpus_api`. They are:

- **not** citations;
- **not** written to durable memory as identity;
- **not** durable aliases ("para id", "passage number", "block id").

Wave B re-keys anything keyed on provisional handles when the grid settles (§3.6 of the
identity spec).

---

## 4. Forward recoverability — mandatory for durable records

Every durable record that references a passage must anchor to **migration-stable handles**
so that at SID cutover it can re-anchor to the settled `sid` by unique content match —
the same forward-recoverability principle as sigil restoration (identity spec §2.4:
`overlay_window` + unique content match survives re-segmentation).

**Required durable anchor set:** `eul_wid` + quoted Greek + `legacy_reference` (when
present).

A record pinned **only** to a provisional ordinal, provisional `sid`, or `sort_key`
**cannot** be recovered after re-keying and is **forbidden**.

---

## 5. Honesty at the surface

When presenting a passage, the head **states that passage identity is provisional**. It
**never** implies that an ordinal, display-block `sid`, or `sort_key` is permanent. It
**coins no durable alias** for a provisional handle.

---

## 6. Relationship to the identity spec

| concern | owner document |
|---|---|
| what a SID is; settlement gate; provisional vs settled | [`corpus_identity_and_schema.md`](corpus_identity_and_schema.md) §1.4, §3.4 |
| interim API grain (`corpus_api.sid_text` over display blocks) | same, §3.5 |
| how heads cite meanwhile | **this document** |

Implementations (EuGraphikon apparatus, EuMorphikon tokenisation/`tid` pipeline, memory stores,
translation pipelines) **conform here** during the pre-settlement regime; where an implementation
treats a provisional handle as durable citation identity, the implementation is the defect.
