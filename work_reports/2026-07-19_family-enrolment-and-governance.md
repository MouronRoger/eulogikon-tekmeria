# 2026-07-19 · Family enrolment and governance stand-up

## What was done

Enrolled `eulogikon-semeia` as the fourth EuKoine family member and stood up the
governance slots required of a doc and data member.

**At the hub** (`../eukoine`), two pathspec commits, the eight unrelated WIP
files left untouched:

- `b566c68` : added `eulogikon-semeia` to `[mirrors]` and to the `targets` of
  the 16 all-member artefacts. The five `grc_fold.*` bindings remain
  eulogikon-only.
- `a226b88` : committed a pre-existing working-tree docstring change to
  `tooling/normalization/greek_normalizer.py`. See Finding 1.

Then `unlock --from-env`, `push --execute`, `verify`. Result: **69 artefact
copies byte-identical across 4 mirrors.** The write session was left **open** at
the owner's instruction; the owner locks.

**In this repo**, the governance slots (family `GOVERNANCE.md` §1): purpose in
`CLAUDE.md` citing the hub apex; `AGENTS.md` twin; `governance_cluster/canonical_design_principles.md`
(TDP-001..015, TAP-001..008); `governance_cluster/registry.yaml`;
`ROT.md` (R1..R6); `governance_cluster/` (capability port, adversarial cross-check,
cold reading); `governance_cluster/script_lifecycle.md`;
`governance_cluster/predicate_lexicon_local.yaml`; `CHARTERS.md` (CH-01..05);
`governance_cluster/functional_concern_homes.yaml`; `work_reports/`; the
`UserPromptSubmit` hook and its `.codex/` twin. Slot 8 is deliberately unfilled
and says so in `CLAUDE.md`.

## Verification run

| Check | Result |
|---|---|
| `naming/sync.py verify` | 69 copies byte-identical, 4 mirrors |
| `governance_cluster/check_registry_owners.py` | 14/15 bound, 1 deferred, 0 failed |
| `scripts/audit/check_eukoine_spec_protected.py --role mirror` | pass |
| `scripts/audit/check_fold_authority.py` | pass |
| `pytest tests/` | 7 passed |

`pytest` was installed into `.venv` in the same pass, because the two fold tests
arrived with the sync and a test nothing runs is decoration.

## Findings

**1. Half-completed fold-authority sync (resolved).** A docstring change to
`lemma_foldkey` had reached eulogikon and EuGraphikon, had not reached
EuMorphikon, and was never committed at the hub. Behaviour byte-identical
(the note records that the fold strips macron U+0304 and breve U+0306).
Surfaced before executing, because `sync.py push` copies the hub working tree
and is all-or-nothing per repo, so the enrolment push would have swept an
unratified fold authority into a member. Resolved by committing it at the hub
first. EuMorphikon has converged.

**2. Agent DB access was owner-credentialed (open).** The Cursor MCP
`DATABASE_URI` uses the `eulogikon` owner role, guarded only by
`postgres-mcp --access-mode=restricted`, a filter on SQL text. Family law
(`ONE_SYSTEM.md` §4.1) requires agent-composed SQL to fail *regardless of the
SQL text*, and EuGraphikon `ADR-006` records the text-scanning guardian as
retired for unsoundness. Not copied. A `tekmeria_ro` SELECT-only role is to be
minted by the owner. **Until then this repo has no live DB access, and the
tekmerion skill's hard requirement means no composition can proceed.**

**3. The U+2014 ban has no scope for quoted evidence (open).** Of about 25 em
dashes in `philostorgia_corpus.json`, one is authored (`status`) and the rest
are inside Greek `kwic` windows: transmitted text and editorial apparatus.
Phase 6 requires a U+2014 count of zero, which a finished Tekmerion carrying
Greek quotations cannot satisfy. The predictable outcome is that the check gets
disabled while the report still claims it ran. The ban needs a scope, authored
prose only and never a quoted span. Not changed: it is a hard boundary owned by
`CLAUDE.md` and `README.md`, and re-scoping one is the owner's call.

**4. Composition anchors were unrecoverable (resolved).** The station ledger
anchored on `units.id` alone, a provisional handle, which
`.eukoine/interim_head_citation.md` §4 forbids for durable records. An `incipit`
column was added to the candidate and station rows, recorded at the moment the
quoted span is matched against `text_greek` (the match already ran; only the
flag was being kept). `philostorgia_candidates.tsv` predates this and needs
regeneration.

## Open

- Mint `tekmeria_ro`; configure the MCP server at user scope, never a
  project `.mcp.json`.
- Rewrite the read path onto `corpus_api` (CH-02), and regenerate
  `philostorgia_candidates.tsv` with `incipit` and `legacy_reference`.
- Scope the U+2014 rule.
- CH-01 through CH-04 are chartered and unbuilt.
- No adversarial pass was run against this session's work. Under TDP-013 that
  means this closure is unsigned.
