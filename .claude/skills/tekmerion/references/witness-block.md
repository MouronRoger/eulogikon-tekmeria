# The witness block

One witness = one station = one block = one citation. The citation sits above
the three lines; framing prose may sit above the citation; commentary follows
the translation. Never repeat the reference in the framing and again after the
translation.

## Draft form (markdown, working file)

```
<framing: the station and the local fact, one to three sentences>

Author, *Work Title*, Eulogikon: wid, ref. REF

> Greek exactly as the corpus yields it ... with ellipses marked

*ALA-LC transliteration of the same span*

English translation, no quotation marks around the whole line.

<commentary: what the line does on the page; a shift only if already visible>
```

## Site form (HTML, from the published pieces and new-post.html)

```html
<p>Framing: the station and the local fact.</p>

<p class="witness-ref">Author, <em><a href="https://eulogikon.org/works/SLUG"
   title="Work Title (wid)">Work Title</a></em>, Eulogikon: wid, ref. REF</p>
<blockquote lang="grc" class="grc">Greek text ... exactly as the corpus yields it</blockquote>
<p class="translit"><em>ALA-LC transliteration</em></p>
<p class="translation">English translation.</p>

<p>Commentary: what the passage does.</p>
```

- The work URL is resolved from the database (canonical_work_url or
  eulogikon.v_works_complete); never hand-guess a slug. The link title
  attribute carries "Work Title (wid)".
- Section headings (h2) group stations along the trajectory; a heading is not
  a substitute for framing.
- Secondary pointers (parallel witnesses, cross-references, lexicographical
  glosses, corpus-boundary notes) use inline `<span class="cite">...</span>`
  in running prose, never a witness block.
- Diachronic or sources tables use `<div class="table-scroll"><table
  class="summary diachronic">...` as in the published pieces, and their
  numbers are recomputed from the ledger at composition time.

## Excerption marks

- Omission inside the Greek: `...` (three dots, spaced as the corpus pieces
  do). Mirror the omission in the transliteration; mirror it in the
  translation where the reader would otherwise be misled about continuity.
- Editorial brackets in the source (⟨ ⟩, [ ], † †) are part of the evidence:
  keep them in the Greek line.

## Punctuation rule

No em dashes (U+2014) anywhere in the piece: repunctuate with colons, commas,
parentheses, or middle dots (·). En dashes (U+2013) in reference ranges
(1078b17–31) are fine.
