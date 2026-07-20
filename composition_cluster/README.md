# Composition cluster

Extended Tekmerion state and tooling. The per-term SQLite store (`*.db`) is
gitignored working state; the committed Python modules and sidecar JSON/SQL
files are the durable, rebuildable record.

Read [`STYLE.md`](../STYLE.md) § **Formatting cross-check** for field
formatting; [`prose_rules.md`](prose_rules.md) for composition-only
boundaries; [`craft.md`](craft.md) for voice during the composition phase.
Procedure: [`.claude/skills/tekmerion/SKILL.md`](../.claude/skills/tekmerion/SKILL.md).
Published-form prose (balance, framing, endings): [`STYLE.md`](../STYLE.md).

## Three phases

```text
Pre-composition (Phases 0–3)  →  Composition (Phases 4–5)  →  Post-composition (Phases 6–7 + publish)
```

| Phase | Skill steps | Entry / scripts | Done when |
|---|---|---|---|
| **Pre-composition** | 0 Load, 1 gate, 2 candidates/stations, 3 trajectory | [`composition_build_store.py`](composition_build_store.py) from a candidates TSV | Essay, chapters, candidates, stations, `idx`, claims in the store; all stations `pending`; **zero** `block` rows |
| **Composition** | 4 blocks (chunked), 5 ending | [`composition_write_blocks.py`](composition_write_blocks.py), [`composition_write_ending.py`](composition_write_ending.py) | Every station-disposition unit has block(s); ending in chapter VI; stations `drafted`; STYLE § Formatting cross-check, [`prose_rules.md`](prose_rules.md), and [`craft.md`](craft.md) applied. **No** verify, **no** HTML, **no** `posts.json` |
| **Post-composition** | 6 verify, 7 project, publish | [`composition_verify.py`](composition_verify.py), [`composition_project.py`](composition_project.py), then [`site_cluster/posts.json`](../site_cluster/posts.json) + [`site_build_index.py`](../site_cluster/site_build_index.py) | Clean verification report; stations `checked`; HTML under `site_cluster/public/`; index and sitemap in sync |

A **composition-only** agent needs: the store, STYLE § Formatting cross-check,
[`prose_rules.md`](prose_rules.md),
[`craft.md`](craft.md), the whole `idx`, prior-chunk blocks, live corpus DB
(QUOTE/CATALOG), and STYLE for balance. It does not run verify or projection.

## Typical run order (full pipeline)

```bash
python3 composition_cluster/composition_build_store.py      # pre: scaffold only
python3 composition_cluster/composition_write_blocks.py     # composition: blocks
python3 composition_cluster/composition_write_ending.py     # composition: ending + pub metadata
python3 composition_cluster/composition_verify.py --emit-quote-sql
# run philostorgia_quote_check.sql via user-postgres MCP; save philostorgia_quote_check.json
python3 composition_cluster/composition_verify.py           # post: report + checked
python3 composition_cluster/composition_project.py        # post: HTML
python3 site_cluster/site_build_index.py --check           # post: registry sync
```

Sidecars beside the store (quote check SQL/JSON, blacklist rules, catalog URLs,
verification report) are produced or consumed by the post-composition scripts;
see [`composition_verify.py`](composition_verify.py) module docstring.

## Hard requirements

- **Live corpus DB** for composition: fetch every Greek excerpt by `unit_id`; resolve
  titles, wids, refs, URLs by query. Survey JSON is discovery only.
- **Never compose into HTML** during the composition phase. The page is a
  deterministic projection of the store.
- **Single write path**: judgment lives in the writers and the store, not in
  hand-edited projected HTML.
- **Same craft for every term**: STYLE § Formatting cross-check,
  [`prose_rules.md`](prose_rules.md),
  [`craft.md`](craft.md), [`STYLE.md`](../STYLE.md), and this skill's
  **What this is** section apply to the next long-form Tekmerion, not only the
  current prototype.

## Public vs compose-only

| Surface | What the reader sees |
|---|---|
| Primary `station` rows | Full witness block (framing, Greek, translit, translation, commentary) |
| `secondary` rows | One English `<p class="cite">` line (`idx.summary` only) |
| `set-aside` rows | Nothing (reason stays in the store and verification report) |
| Chapters with empty `title` | Skipped by [`composition_project.py`](composition_project.py) |
| Section VI | Closing counts and reader-facing caveats only |

Dating traps, metadata mirages, and verification audit belong in the store,
not in a public chapter.

## Per-term artifacts

| Artifact | Role |
|---|---|
| `{term}_candidates.tsv` | Exhaustive candidate set (pre-composition input) |
| `{term}.db` | Composition store (gitignored) |
| `{term}_catalog.json` | CATALOG URLs for projection |
| `{term}_verification.md` | Phase 6 report |
| `composition_write_blocks.py` | Per-term block judgment (prototype: philostorgia) |
| `composition_write_ending.py` | Per-term ending, pub metadata, compose-only hygiene |

Clone or replace the two writers for each new term until a generic writer
exists; the phase split, store schema, projection rules, and craft docs are
shared.
