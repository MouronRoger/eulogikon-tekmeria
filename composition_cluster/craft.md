# Composition craft (voice guidelines)

For **every extended Tekmerion** during the **composition phase**. Read after
the **What this is** section of
[`.claude/skills/tekmerion/SKILL.md`](../.claude/skills/tekmerion/SKILL.md)
and alongside [`prose_rules.md`](prose_rules.md).

This is not published-form authority ([`STYLE.md`](../STYLE.md)). It is not
field mechanics (Greek-in-English, blacklist). It is a short set of **guidelines**
for writing prose a reader would keep reading.

Before drafting blocks, skim a published exemplar on tekmeria.eulogikon.org
(e.g. what Marcus prays for, ἀεργοί and ἐνεργοί).

---

## The job

An **interesting walk through the history of a concept** over the
[Eulogikon](https://eulogikon.org/) corpus: how witnesses use the term or
locus, what changes, what survives. Not philology. Not manuscript analysis.
Not a concordance with comments. Not dry literal glossing with nothing at
stake for the reader.

---

## Guidelines

**Write for the reader, not the verifier.** Commentary says what the line
shows in the argument. Corpus traps, digitisation quirks, HAND parallels, and
quote discipline belong in the composition store and verification report, not
on the public page. The ending may carry a few reader-facing caveats
(doxography, coverage limits); it is not a verification dump.

**Plain English on the page.** The subject word of the essay and blacklist
terms (*physis*, *psyche*) may stay transliterated; every other Greek word
becomes English (the wise, not spoudaios; cherishing, not storge). **Never
bare untranslated Greek** in framing, commentary, chapter prose, secondary
pointers, or the ending. Greek belongs in the three evidence lines of a primary
witness block.

**No ecclesiastical material.** Christian, patristic, and theological
witnesses are outside the survey: not stations, not afterlife colour, not a
closing flourish, never discussed within the entry. Do not reach past the
surveyed span to reach them ("the word travels one step further into the
Christian writers" is off the map). Full rule and enforcement in
[`prose_rules.md`](prose_rules.md).

**Show, do not crown.** Commentary says what the line shows; it does not award
verdicts the Greek on the page has not earned. No "this is the summit of the
concept," no closing aphorism that rephrases the thesis as a ruling. The one
allowed pulse sentence (below) is drawn straight from the Greek just above, not
from the arc as a whole.

**One hook, not two theses.** Opening rearranges expectation once; the hinge
states the arc once; chapter leads are full sentences, not index lines with
"This chapter" pasted on. The ending recounts counts and caveats; it does not
re-walk the whole arc.

**Earn a pulse sentence** after a decisive station if the material gives you
one (cf. STYLE Marcus exemplar: "The word is conservative; the content is
not."). Not in the opening; earned from the Greek just above.

**Cold-read before post-composition.** Read projected HTML only. If it reads
like an annotated station list or a verification report, return to
composition and rewrite commentary for interest.

---

## Store fields (reminder)

| Field | Voice job |
|---|---|
| `block.framing` | Orient: who, what text, local hook |
| `block.translation` | Warrant-faithful English; no editorial insertions |
| `block.commentary` | Hermeneutics: what this line does in the history |
| `chapter.shows` | Reader-facing chapter hook |
| `idx.summary` | English for you; projected secondaries print this line only |
