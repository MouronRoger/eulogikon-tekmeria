# Rot doctrine: Tekmeria

- **Title:** Rot doctrine, Tekmeria (`eulogikon-semeia`)
- **Status:** active
- **Authority_level:** member doctrine. Names the decay classes this repo is
  actually subject to and what stops on sight.
- **Scope:** the composition store, the scripts, the published Tekmeria, and the
  governing documents.
- **Relationship_to:**
  - principles: `governance_cluster/canonical_design_principles.md`
  - registry: `governance_cluster/registry.yaml`
  - discovery instrument: `governance_cluster/cold_reading.md`

## What rot is

**Rot is displaced responsibility for an invariant. Rotting is that distance
growing through local compensation.**

The defining property is that **rot is invisible at the diff.** No single change
contains it. The damage is legible only across an accumulation that no
individual contributor ever saw whole, which is why every instrument that fires
at or after a change is structurally blind to it, and why the plan and the cold
read are where it is actually caught.

## The classes

### R1 : citation rot

A published citation whose backing check no longer exists, no longer passes, or
never happened. Includes a quotation that no longer matches the corpus, a
reference that resolves elsewhere, a count no recorded query reproduces, and a
verification report whose piece has since been edited.

*Evidence:* a published page whose claims cannot be regenerated clean from the
store today.

**This is the class this repo exists to be free of. It is the one a Tekmerion
cannot survive being wrong about.**

### R2 : anchor rot

A durable record recoverable only through a provisional identifier. It looks
correct for as long as the corpus does not move, and becomes unrecoverable the
moment it does, silently.

*Evidence:* a store row or ledger line with a unit id and no incipit.

### R3 : restatement rot

One rule stated in two places. The copies agree at the moment of writing and
drift after. A helpful summary, a restated subset, a parallel current
understanding.

*Evidence:* two documents that both state a rule normatively, rather than one
stating and one citing.

### R4 : projection rot

The published page and the store disagree, because the page was edited
directly. The store stops being the source of truth without anyone deciding
that it should.

*Evidence:* a fact on a page that regeneration from the store would not produce.

### R5 : orphan script rot

An executable no one can classify: not a test, not a producer, not a guardian,
not deleted. It computes something and asserts nothing, and the artifact it was
supposed to be checking has no coverage.

*Evidence:* a standing script with a `__main__` and no terminal state.

### R6 : face-orphan

A document section that cannot name which end-product requirement it serves. It
was true when written, no longer bears on anything, and is still read as
binding.

*Evidence:* a governing paragraph whose deletion would change no obligation.

## What stops the turn

Most findings are triaged: fixed now, tracked with a named alarm, or recorded
as load-bearing with the reason. Some are not triaged at all. Surface these
immediately and stop:

- An **R1 finding on a published piece.** Published evidence detached from its
  check is the most serious state available here.
- An **ungoverned writer of a published page**: anything that can mutate a
  quotation, an identifier, a reference, or a count on a published page without
  the store and its verification record changing in the same act (TDP-009).
- A **fabricated or hand-recalled citation**, at any stage.
- A **contradiction between two governing documents.** Fix the wrong document;
  never average two rules.

## The inverse failure

Rot is displaced responsibility. Its opposite failure is **over-zealous
rule-invocation**: invoking or inventing a rule that names no invariant, only to
block sensible reversible work. That is TAP-008, and it is a violation, not a
virtue.

The test is mechanical. **A rule that names the invariant it guards stays. A
rule that names none is the anti-pattern and is cut.** The doctrine in this repo
is the agent's instrument, never a gate on sensible work, and the agent is fully
empowered to do and report.

## Where the parsimony rule does not reach

Applying subtraction to the reader-facing page is itself a defect. Every
evidence block carries its own full citation though it repeats the one above; a
rich witness carries several blocks across several sections; the caveats restate
what the piece already showed. That repetition serves a reader and is never
collapsed as duplication.

The engine test for rot is **two writable sources of one fact that can drift**,
never two read paths over one owner, and never richness on the page. If you
cannot tell which layer a repeated structure sits on, that ambiguity is itself
the finding: resolve the layer before classifying.
