# Composition prose rules

Boundaries that apply during the **composition phase** (Phases 4–5) of **every
extended Tekmerion** and are not restated elsewhere.

**Formatting cross-check:** all mechanical rules (Greek in English, witness
blocks, citations, punctuation, titles/meta, blacklist-safe surface English)
live in one place: [`STYLE.md`](../STYLE.md) § **Formatting cross-check**.
Read and run that checklist before sign-off; do not hunt across files.

**Voice:** [`craft.md`](craft.md). **Published form** (balance, framing,
endings): [`STYLE.md`](../STYLE.md). **Procedure:** the tekmerion skill and
[`ledger.md`](../.claude/skills/tekmerion/references/ledger.md).

---

## Ecclesiastical and theological material is excluded

A Tekmerion surveys the term across the Greek-speaking span **outside** the
ecclesiastical tradition. Christian, patristic, and theological witnesses
(corpus `affiliation = 'christian'`, and any doctrinally theological content
whatever the tag) are **excluded from construction, from validation, and from
output entirely**. They are not stations, not secondaries, not afterlife
colour, not a closing flourish, and they are **never discussed within an
entry**, not even to note that the word reached them.

This is a hard boundary, not a matter of emphasis. Do not reach past the
surveyed span to say "the word travels one step further into the Christian
writers": that step is off the map. If a Christian author is the *only* later
attestation of a sense, the sense is reported from its non-ecclesiastical
witnesses or not at all. A New Testament or patristic parallel is not a
reader-facing note; it does not belong in the ending either.

Set-aside dispositions for `christian`-affiliated candidates are recorded in
the store with reason `ecclesiastical-excluded` and are **not** surfaced on
the page (unlike coverage-set set-asides, which are). The verifier fails any
projected field that names a Christian author or theological content.

---

## Translation warrant

The translation line is not a place to narrate the scene, identify unstated
referents, or mark supplied words. **No square brackets** in translations. No
`[bird]`, `[the Stoics]`, `[elders]`, `[in accord with physis]`: if the reader
needs that hermeneutic move, it belongs in commentary (or framing when the
station itself requires it).

The translation contains nothing without warrant in the Greek excerpt: no added
subjects, no connectives that assert relations the Greek does not. Where English
would require a supplied word, rephrase to stay within warrant, leave the term
transliterated, or use an ellipsis.

Interpretation, history-of-ideas argument, and "what this means" belong **below**
the translation, in commentary.

---

## φύσις / physis at compose time

The live blacklist (`blacklist_physis_nature`) forbids English **nature** and
**by nature** anywhere in projected English. Surface spellings and the full
cross-check table are in [`STYLE.md`](../STYLE.md) § Formatting cross-check.

When drafting, prefer the **word** and familiar constructions:

| Avoid in English fields | Prefer |
|---|---|
| phýsei (dative, bare) | by *physis* |
| "phýsei affection" | affection by *physis*; or by *physis*, affectionate |
| katà phýsin (bare, no gloss) | katà phýsin in the translation; *physis* / by *physis* in commentary |
| nature, by nature | *physis*, by *physis* |

Check the live blacklist at compose time (tekmerion skill, Phase 4 step 6).
Other load-bearing terms the blacklist protects (*soul*, *substance*, *essence*,
and the rest) follow the same cross-check: transliterate in running English;
gloss in commentary or plain apposition, not square brackets.
