# The witness block

One block = one citation. A station (a unit) usually carries one block, but a
rich witness the piece returns to may carry several, each at its own point in
the trajectory, each with its own citation above it (the reader must never
have to scroll back to know what they are reading). The station row lists every
block; coverage counts the unit once. Within a block: the
citation sits above the three lines; framing prose may sit above the
citation; commentary follows the translation. Never repeat the reference in
the framing and again after the translation.

## Block content (the record fields: greek, translit, translation, commentary)

```
<framing: the station and the local fact, one to three sentences>

Author, *Work Title*, Eulogikon: wid, ref. REF

> Greek exactly as the corpus yields it ... with ellipses marked

*ALA-LC transliteration of the same span*

English translation, no quotation marks around the whole line. No square
brackets: no editorial insertions. Hermeneutics and history-of-ideas argument
belong in framing and commentary, not in the translation line.

<commentary: what the line does on the page; a shift only if already visible>
```

## Projected form (HTML, from the published pieces and new-post.html)

The HTML is produced by deterministic projection at Phase 7, never composed by
hand. The work URL below is the composed display path resolved from the DB.

```html
<p>Framing: the station and the local fact.</p>

<p class="witness-ref">Author, <em><a href="https://eulogikon.org/works/WORK-DISPLAY-STRING"
   title="Work Title (wid)">Work Title</a></em>, Eulogikon: wid, ref. REF</p>
<blockquote lang="grc" class="grc">Greek text ... exactly as the corpus yields it</blockquote>
<p class="translit"><em>ALA-LC transliteration</em></p>
<p class="translation">English translation.</p>

<p>Commentary: what the passage does.</p>
```

- The work URL is resolved from the database (canonical_work_url or
  eulogikon.v_works_complete); never hand-guess a display string. The link
  title attribute carries "Work Title (wid)".
- Section headings (h2) group stations along the trajectory; a heading is not
  a substitute for framing.
- Secondary pointers (parallel witnesses, cross-references, lexicographical
  glosses, corpus-boundary notes) use inline `<span class="cite">...</span>`
  in running prose, never a witness block.
- Diachronic or sources tables use `<div class="table-scroll"><table
  class="summary diachronic">...` as in the published pieces, and their
  numbers are recomputed from the store at composition time.

## Excerption marks

- Omission inside the Greek: `...` (three dots, spaced as the corpus pieces
  do). Mirror the omission in the transliteration; mirror it in the
  translation where the reader would otherwise be misled about continuity.
- Editorial brackets in the source (⟨ ⟩, 〈 〉, [ ], † †) are part of the
  witness: **keep them in the store's `block.greek` field**, so the record
  stays faithful to the corpus. They are **stripped on projection** and must
  never appear on the reading surface (Phase 7 removes them; the verifier
  fails any that survive). The reader sees clean Greek; the store keeps the
  apparatus. This is the same store-versus-surface split the skill applies to
  `units.id`: preserved upstream, never shown.

## Punctuation rule

No em dashes (U+2014) anywhere in the piece: repunctuate with colons, commas,
parentheses, or middle dots (·). En dashes (U+2013) in reference ranges
(1078b17–31) are fine.
