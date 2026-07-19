# CLAUDE.md · eulogikon-semeia

Agent orientation for this repo. It points at authorities; it never restates
them. If this file and one of the docs below disagree, the doc wins and this
file is stale.

## What this is

This is **Tekmeria** (`tekmeria.eulogikon.org`): a standalone static site of
short, evidence-led essays reading the [Eulogikon](https://eulogikon.org)
ancient-Greek corpus. There is no database here, no generator, no build step.
Every essay is one committed HTML file; `posts.json` is the only registry.

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
  discipline this repo's Tekmerion skill borrows from (lemma first, spread
  across authors not the densest work, cite by stable identity key, never a
  display string). That skill's own objective is a generic concept trace; it
  is told afterward, by a separate DB-seeded guide, that the output is a
  Tekmerion. The skill below states the objective up front instead.
- **EuMorphikon** (`../EuMorphikon`) builds shared morphology/tokenisation
  tooling. Nothing here depends on it directly.

Those two sibling repos carry a large amount of engine-specific governance
(campaigns, regulators, capability ports, invariant registries). None of that
transfers here: this repo has no engine, no writes, no service to keep
correct at runtime. Importing that apparatus onto a folder of HTML essays
would be governance with no invariant behind it. What *does* transfer, and is
adopted below, is the pattern: an orientation file, an explicit skill for the
recurring task, and hard boundaries that name what they protect.

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
- **Never hand-guess a canonical URL slug.** Resolve it from the database
  (see below). Display strings change; `eul_wid` does not.
- **No em dash (U+2014) anywhere in this repo's prose or code comments.**
  Repunctuate with a colon, comma, parenthesis, or middle dot (`·`). Full
  table of substitutions in `README.md`.
- **No new Tekmerion is published without every reference station-checked**
  (floruit vs. composition date for pseudepigrapha, doxography vs. original
  speech). `STYLE.md` § "Before composing" and the skill below give the
  checklist.
- **Do not create a new markdown document without being asked.** This
  applies to `README.md`/`STYLE.md`/this file too: propose the change, get
  it confirmed, then write it.
- **Do not commit or push without being asked.**

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
| `eulogikon.form_lemma` | Lemma/headword resolution + frequency | `headword`, `lemma_id`, `lemma_freq` |

Resolve a citation URL from the `eulogikon` repo, never by hand:

```bash
cd ../eulogikon
EULOGIKON_STRICT_DB=1 venv/bin/python -c \
  "from src.core.url_composer import canonical_work_url; print(canonical_work_url('hgw-bj'))"
```

## A standing flag, not yet actioned

`new-post.html` currently holds a duplicate of a published essay's content
rather than a blank `<!-- TODO -->` skeleton (as `README.md` describes it).
Copying it today would copy that essay by accident. Flagging this rather than
silently fixing it: ask before resetting the skeleton.
