# CLAUDE.md · eulogikon-semeia

Agent orientation for this repo. It points at authorities; it never restates
them. If this file and one of the docs below disagree, the doc wins and this
file is stale.

## Purpose

Tekmeria serves the family apex to a reader. The family exists to recover what
the Greeks actually meant beneath the Latin filter, and its arc runs preserve
the Greek, purify it, make it computable under one reference grid, then serve
it. This repo holds the last step in its public form: it takes the trustworthy
substrate the other members build and shows, in front of a reader and with the
evidence on the page, where a received understanding does not survive contact
with the corpus. The apex is owned at [`../eukoine/PURPOSE.md`](../eukoine/PURPOSE.md);
this paragraph states only this member's slice of it and defers there for the
rest.

## What this is

This is **Tekmeria** (`tekmeria.eulogikon.org`): a standalone static site of
evidence-led essays reading the [Eulogikon](https://eulogikon.org)
ancient-Greek corpus. Every published essay is one committed HTML file, and
`posts.json` is the only site registry. Extended Tekmeria are composed against
a per-term SQLite store under `composition_cluster/`, from which the page is
projected; short-form pieces need no store.

Two governing docs, each with a fixed job. Read both before writing anything:

- **[`README.md`](README.md)** governs file mechanics: layout, adding a post,
  registering it, syncing derived files, deploying.
- **[`STYLE.md`](STYLE.md)** governs the prose and the evidence: what a
  Tekmerion is, the hinge, the balance between dry and speculative, the
  exemplars to write toward.

This file is a third thing: agent-facing orientation and a couple of hard
boundaries that are easy to violate by accident. It does not duplicate either
doc's content.

## Where this sits in the family

- **[eulogikon](../eulogikon)** holds the canonical Greek corpus in Postgres.
  It is the single source of truth for every citation. This repo never edits
  it and never guesses at it.
- **EuGraphikon** (`../EuGraphikon`) is a separate retrieval/reasoning engine
  over the same corpus, built for its own conversational head. Its
  `.claude/skills/grc-concept-trace` skill encodes the diachronic-sweep
  discipline this repo's Tekmerion skill borrows from (word first, spread
  across authors not the densest work, cite by stable identity key, never a
  display string). That skill's own objective is a generic concept trace; it
  is told afterward, by a separate DB-seeded guide, that the output is a
  Tekmerion. The skill below states the objective up front instead.
- **EuMorphikon** (`../EuMorphikon`) builds shared morphology/tokenisation
  tooling. Nothing here depends on it directly.

- **[eukoine](../eukoine)** is the family hub. It holds the apex, family law,
  and the single source mirrored into every member as `.eukoine/`. Family law
  outranks everything in this repo. A member rule may be stricter; it may never
  contradict.

This repo has an engine: the composition store, the corpus reader, the
verification producer, and the page projector. Family engine discipline
therefore applies to it in full, and is adopted below rather than waved off.

## Governance

Read in this order. Highest wins, and a disagreement between two of them is a
finding to fix, never a difference to average.

1. **Family law** at the hub, and the `.eukoine/` mirror (identity/schema **and**
   the shared code lexicon —
   [`.eukoine/predicate_vocabulary.md`](.eukoine/predicate_vocabulary.md) /
   [`.eukoine/predicate_lexicon.yaml`](.eukoine/predicate_lexicon.yaml)). Every
   member must stay compatible with that lexicon; do not coin retired
   signifiers (`slug`, bare `unit`/`Unit`, bare `witness`, …).
2. **[`governance_cluster/canonical_design_principles.md`](governance_cluster/canonical_design_principles.md)**:
   the TDP principles and TAP anti-patterns.
   [`registry.yaml`](governance_cluster/registry.yaml) binds each to its owner file
   and is checked by `governance_cluster/check_registry_owners.py`.
3. **[`ROT.md`](ROT.md)**: the decay classes, and what stops the turn.
4. **[`governance_cluster/`](governance_cluster/)**: the three non-negotiables.
   [Capability port](governance_cluster/capability_port.md) shape for all engine
   work. [Adversarial cross-check](governance_cluster/adversarial_cross_check.md) at
   the plan gate and the sign-off gate, compulsory, never self-administered.
   [Cold reading](governance_cluster/cold_reading.md) blind, tracer and judge kept
   separate.
5. **[`CHARTERS.md`](CHARTERS.md)**: the five capabilities and the invariant
   each holds.
6. **[`STYLE.md`](STYLE.md)** for prose, **[`README.md`](README.md)** for file
   mechanics, the skill below for procedure.

Where to look for a concern:
[`governance_cluster/functional_concern_homes.yaml`](governance_cluster/functional_concern_homes.yaml).

**Slot 8, formal-logic invariants, is deliberately unfilled.** Family law makes
it optional for a doc and data member, and the invariants this repo holds are
stated in `CHARTERS.md` with their falsifiers. Stating this as a present-tense
fact rather than leaving a silent gap.

## Skills

- **Writing a Tekmerion** ([`.claude/skills/tekmerion/SKILL.md`](.claude/skills/tekmerion/SKILL.md)):
  invoke by asking to write, draft, or produce a Tekmerion on a term, or to
  turn research notes into one. Covers the corpus sweep, the station-checks,
  composing to `STYLE.md`, and publishing per `README.md`.

## Hard boundaries

- **Never fabricate or hand-recall a citation.** Every `wid` + `ref` in a
  published essay must be confirmed against `eulogikon.units` before it goes
  in. This protects the one thing a Tekmerion cannot survive being wrong
  about: the evidence.
- **Never hand-guess a canonical URL display string.** Resolve it from the
  database (see below). Display strings are attributes, not identity; the
  `eul_wid` is the stable key. Reference vocabulary follows the family single
  source (`.eukoine/corpus_identity_and_schema.md`,
  `.eukoine/predicate_vocabulary.md`); never reintroduce retired signifiers.
- **No em dash (U+2014) anywhere in this repo's prose or code comments.**
  Repunctuate with a colon, comma, parenthesis, or middle dot (`·`). Full
  table of substitutions in `README.md`.
- **No new Tekmerion is published without every reference station-checked**
  (floruit vs. composition date for pseudepigrapha, doxography vs. original
  speech). `STYLE.md` § "Before composing" and the skill below give the
  checklist.
- **Do not commit or push without being asked.**

## Composition working store

The store's schema, read protocol, and state machine are owned by
[`.claude/skills/tekmerion/references/ledger.md`](.claude/skills/tekmerion/references/ledger.md)
and are not restated here.

What this file adds: creating and maintaining a store under
`composition_cluster/` (the `*.db` data product is gitignored), and any scratch
markdown beside it, needs no prior permission. It is working state, not a
published document. Only the served payload under `site_cluster/public/` and
`site_cluster/posts.json` are committed as the site.

## Verifying the corpus (Postgres, not Arango)

The corpus lives in the shared `eulogikon` Postgres database, reachable here
through the `user-postgres` MCP `execute_sql` tool (read-only). Arango has
been unreliable for this repo; do not default to it.

Tables used most often:

| Table | Holds | Key columns |
|---|---|---|
| `eulogikon.units` | Textual units (the quotable passages) | `eul_wid`, `ref`, `text_greek` |
| `eulogikon.works` | Work metadata | `eul_wid`, work display string |
| `eulogikon.authors` | Author metadata | `eul_aid`, `fl_from`, `fl_to`, `period` |
| `eulogikon.form_lemma` | Headword resolution + frequency | `headword`, `lemma_id`, `lemma_freq` |

**These are physical tables, and reading them directly is a present-tense gap,
not the target.** Physical `eulogikon.*` tables are private to that member and
mid-rename: `units` dissolves into `sid_text` plus `legacy_reference` overlays.
The published contract for consumers is the `corpus_api` schema, and the corpus
reader charter (CH-02) exists to close this. Rewriting the queries needs a
session with live DB access to confirm the interim `corpus_api` surface carries
every column they use.

Resolve a citation URL from the `eulogikon` repo, never by hand:

```bash
cd ../eulogikon
EULOGIKON_STRICT_DB=1 venv/bin/python -c \
  "from src.core.url_composer import canonical_work_url; print(canonical_work_url('hgw-bj'))"
```

## A standing flag, not yet actioned

`site_cluster/new-post.html` currently holds a duplicate of a published
essay's content rather than a blank `<!-- TODO -->` skeleton (as `README.md`
describes it).
Copying it today would copy that essay by accident. Flagging this rather than
silently fixing it: ask before resetting the skeleton.
