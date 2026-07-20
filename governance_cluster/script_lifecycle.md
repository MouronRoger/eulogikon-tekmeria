# Script lifecycle and provenance closure

- **Title:** Script lifecycle, Tekmeria
- **Status:** active
- **Authority_level:** member governance. Owner of TDP-015.
- **Scope:** every executable in this repo, and every artifact one produces.
- **Relationship_to:**
  - principle: `governance_cluster/canonical_design_principles.md` TDP-015
  - machine check: `scripts/check_script_lifecycle.py`

## Why

An agent writing a script to answer a question is correct. Leaving it is the
rot. Scripts that computed a number, printed it, and asserted nothing accumulate
until a directory of executables exists with no way to tell which are
load-bearing, while the artifact they were supposed to be checking has no
coverage at all. The failure is not untidiness. It is that the shipped thing
looks thoroughly audited and is not.

This repo is at the cheapest possible moment to prevent it: `tools/` is empty
and the store does not exist yet.

## The four terminal states, and the one transient

**A probe is the one transient state**, and it has a deadline: it must reach a
terminal state before the work that created it closes.

| State | Home | Runs when | Holds |
|---|---|---|---|
| **test** | `tests/` | every CI run | is the work correct |
| **producer** | with the concern it serves | when an artifact is rebuilt | how the artifact is made |
| **guardian** | `scripts/audit/` | pre-commit | is the artifact well shaped |
| **chronicle** | `work_reports/`, script deleted | never again | what was true once |

## Choosing the terminal state

Ask, in order:

1. **Would I want CI to fail if this changed?** Then it is a **test**. This is
   most measurements, and the answer is yes far more often than it feels: a
   coverage total, a citation-integrity rate, a count of unanchored rows.
2. **Does it write something else reads?** Then it is a **producer**, homed with
   the concern that owns the artifact, never in a general scripts pile.
3. **Is it a cheap structural check over a shipped artifact?** Then it is a
   **guardian**.
4. **Otherwise** it is a **chronicle**: write the finding down with its numbers
   and delete the script.

A threshold that cannot be asserted is not yet understood well enough to keep
the script.

## A correctness claim is a test

Guardians check shape: does the store's schema hold, does every station row have
an anchor set, is the JSON parseable, is the U+2014 count zero. Tests check
correctness: does this citation denote the passage it names, does the coverage
reconciliation actually total, did the verification report catch what it
claims.

A guardian is never the evidence that work is right. A finding proven only by a
guardian is unverified on every path that does not reach a commit hook.

## Provenance closure

Every shipped or regenerable artifact traces to inputs that are either
committed here or re-fetchable from a pinned recorded identifier. **A
per-session agent sandbox is neither**, and neither is a path under `/tmp`.

Gitignoring a build product is a positive assertion that the chain from a
pinned input to the artifact is unbroken. If the store is gitignored, that
assertion must be true: its inputs are the corpus, pinned by connection target
plus snapshot date, and the recorded generating query with its timestamp.

The store already carries most of this by design, because the candidate table
records its generating query, its run timestamp, and its counts. What that
buys is exactly provenance closure; name it as such rather than rediscovering
it.

## Reject list

- A standing executable with no terminal state.
- A measurement that prints a number and asserts nothing.
- An input path under a session scratchpad or `/tmp`.
- A guardian offered as evidence that the work is correct.
- Keeping a probe because it might be useful.
