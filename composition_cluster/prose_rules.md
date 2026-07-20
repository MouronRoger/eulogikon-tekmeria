# Composition prose rules

Operational craft for English fields written during the **composition phase**
(Phases 4–5) of **every extended Tekmerion**: `block.framing`, `block.translation`,
`block.commentary`, `idx.summary` (English for projected secondaries),
chapter `shows` and `body`, essay question/hinge/opening_lead/blurb, and
publication metadata in the per-term ending writer.

Tekmeria is **hermeneutics and the history of ideas** over the
[Eulogikon](https://eulogikon.org/) corpus: what Greek authors meant and how a
term or locus moved through time. The Greek line is the evidence; the translation
line renders it; **interpretation lives in framing and commentary**, visibly the
writer's. This is not diplomatic editing with supplied words marked in brackets.

Balance, framing, endings, and citations as published form stay in
[`STYLE.md`](../STYLE.md). Voice craft (pulse, anti-formula commentary) stays in
[`craft.md`](craft.md). Procedure and verification stay in
[`.claude/skills/tekmerion/SKILL.md`](../.claude/skills/tekmerion/SKILL.md).
This file is the home for Greek-in-English craft at compose time.

Transliteration scheme: ALA-LC per
[`.claude/skills/tekmerion/references/transliteration.md`](../.claude/skills/tekmerion/references/transliteration.md).

---

## Running English (default)

Commentary, framing, chapter leads, secondary pointers, and the ending are
**plain English** for a public reader. See **Words in English fields** below
for the only exceptions (subject word, blacklist terms).

Greek script and ALA-LC transliteration belong in the three evidence lines of
a **primary** witness block only. Do not copy inflected forms from the excerpt
into English fields.

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

## Greek script in English prose

Greek script is allowed when exact form matters (morphology, corpus absence,
lexical contrast, table cells where the form is the datum). **Never leave bare
Greek script without an inline companion.** Every Greek token in running
English must carry one of:

1. **Slash pair** (preferred when the form itself is the point):
   `κατὰ φύσιν/katà phýsin`, `ἡ τετράγωνος ψυχή` does not occur with a gloss
   nearby.
2. **Transliteration plus gloss in running English**: *philostorgía*, family-
   affection (comma or dash, not square brackets).

A single word or short phrase in Greek script with no companion is a defect.
Fix in the **records**, not in the projected HTML.

Translations should usually be English. Greek script in a translation line only
when the untranslated form is itself what the note is about.

---

## Translation lines: no editorial insertions

The translation line is not a place to narrate the scene, identify unstated
referents, or mark supplied words. **No square brackets** in translations. No
`[bird]`, `[the Stoics]`, `[elders]`, `[in accord with physis]`: if the reader
needs that hermeneutic move, it belongs in commentary (or framing when the
station itself requires it).

The translation contains nothing without warrant in the Greek excerpt: no added
subjects, no connectives that assert relations the Greek does not. Where English
would require a supplied word, rephrase to stay within warrant, leave the term
transliterated, or use an ellipsis. Load-bearing terms stay as transliteration
or plain English equivalents the Greek supports.

Interpretation, history-of-ideas argument, and "what this means" belong **below**
the translation, in commentary.

---

## Words in English fields (do not decline)

When a Greek term appears in translation, commentary, framing, or the ending:

1. **The essay's subject word** stays transliterated (*philostorgia*, and its
   forms when you are naming the term itself).
2. **Blacklist-protected words** stay as agreed (*physis*, *psyche*, not
   English "nature" or "soul").
3. **Everything else is plain English.** Not spoudaios but the wise; not storge
   but cherishing; not archē but starting-point; not katà phýsin in commentary
   but by *physis*. Do not copy inflected forms from the excerpt into English.

**Never bare untranslated Greek** in translation, commentary, framing, chapter
prose, secondary pointers, or the ending. Greek script and transliteration
belong in the three evidence lines of a primary witness block (Greek,
transliteration, translation). Secondary `<p class="cite">` lines are English
only.

The transliteration line mirrors Greek grammar; English fields do not.

| Avoid in English fields | Prefer |
|---|---|
| psychai, psychē (inflected) | *psyche*, or plain English |
| phýsei, physikḗ (inflected) | by *physis* |
| spoudaios, phaulos, storge, archē, … | the wise, the base, cherishing, starting-point, … |
| declined phrases from the excerpt | say it in English |

*Physis* is *physis*. *Psyche* is *psyche*. The history of ideas is told in
English; Greek belongs in the three evidence lines above the commentary.

---

## φύσις / physis (blacklist-safe)

The live blacklist (`blacklist_physis_nature`) forbids English **nature** and
**by nature** anywhere in projected English. Do not use them.

When addressing the reader about what φύσις does in the argument, prefer the
**word** and familiar constructions, not an inflected case bare in English:

| Avoid in English fields | Prefer |
|---|---|
| phýsei (dative, bare) | by *physis* |
| "phýsei affection" | affection by *physis*; or by *physis*, affectionate |
| katà phýsin (bare, no gloss) | katà phýsin in the translation; *physis* / by *physis* in commentary |
| nature, by nature | *physis*, by *physis* |

Spelling follows ALA-LC: **physis** (υ standing alone → y), not phusis.

The **transliteration line** of an evidence block may keep case forms that
mirror the Greek (e.g. `phýsei` for φύσει); that line is not running English
prose. Commentary and translation above/below should still use the dictionary
form of the word when explaining the same idea to the reader.

Other load-bearing terms the blacklist protects (*soul*, *substance*, *essence*,
and the rest) stay transliterated in running English; gloss in commentary or
plain apposition, not square brackets. Check live at compose time (see the
tekmerion skill, Phase 4 step 6).

---

## Translation warrant (commentary vs translation)

The translation line contains nothing without warrant in the Greek excerpt (see
**Translation lines: no editorial insertions** above). Interpretation belongs
in the commentary below, where it is visibly the writer's hermeneutic work.

---

## Punctuation

No em dashes (U+2014) in any field this phase writes. Repunctuate with colons,
commas, parentheses, or middle dots (·). En dashes (U+2013) in reference ranges
(1078b17–31) are fine. Details in [`README.md`](../README.md).

---

## What this file does not own

- What a Tekmerion is, balance, framing, endings, station types:
  [`STYLE.md`](../STYLE.md).
- Store schema, chunked composition, verification report sections:
  the tekmerion skill and [`ledger.md`](../.claude/skills/tekmerion/references/ledger.md).
- HTML projection and site registration: post-composition phase;
  [`composition_cluster/README.md`](README.md).
