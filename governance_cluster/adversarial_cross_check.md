# Adversarial cross-check

- **Title:** Adversarial cross-check doctrine, Tekmeria
- **Status:** active
- **Authority_level:** member doctrine. Owner of TDP-013. Compulsory.
- **Scope:** every plan and every sign-off in this repo: a Tekmerion's scope
  gate, a Tekmerion's publication, and any change to the store, the scripts, or
  the governing documents.
- **Relationship_to:**
  - principle: `governance_cluster/canonical_design_principles.md` TDP-013
  - pairs with: `governance_cluster/cold_reading.md`

## The rule

Before a plan stands and before a sign-off stands, an **independent read-only
sub-agent** inspects it, primed to **falsify, not confirm**.

You are not your own adversary. The party that produced the work cannot
adjudicate it, because the completion drive that produced it is the same drive
that will find it adequate.

The adversary returns **the attacks it ran and what survived, or the defect it
found**. It does not return a verdict. **A bare "looks fine" is a non-run**, and
so is silence. "Low risk" and "close enough" are not agent judgements.

## The two gates

**The plan gate.** For a Tekmerion this is Phase 1, before any prose exists:
the question, the hinge, and the coverage predicate. For an engine change it is
the port plan, before any code. The adversary attacks the plan itself.

**The sign-off gate.** For a Tekmerion this is the finished piece against its
verification report, before publication. For an engine change it is the diff
against the claim made about it. The object is the claim, never the prose.

## Priming: three registers

An adversary primed on fewer registers is an adversary in costume. Prime it on
all three:

1. **The principles and the hard boundaries** (`governance_cluster/canonical_design_principles.md`,
   `CLAUDE.md` hard boundaries).
2. **The anti-patterns and the rot classes** (`governance_cluster/registry.yaml`,
   `ROT.md`).
3. **The evidential discipline** (`STYLE.md`, and the provenance classes in the
   tekmerion skill).

## What the adversary attacks, for a Tekmerion

At the plan gate:

- Is the hinge already the received reading, so the piece finds nothing?
- Does the coverage predicate actually close, or does it leak a class of
  witness the piece will silently omit?
- Is the trajectory an artifact of survival bias rather than a development?
- Does a station type undermine a claim the shape of the piece depends on?

At the sign-off gate:

- Take three claims at random and try to break them against the store.
- Does any period word rest on an attributed floruit (TAP-001)?
- Does any translation line carry content with no Greek warrant (TAP-004)?
- Is any printed count reproducible by the recorded query, run now?
- Does the coverage reconciliation actually total, or does a remainder hide in
  a group set-aside?

## Bounds

The adversary is bounded so it cannot loop: at most two independent passes plus
one verify pass scoped to the corrections. Every finding is corrected in the
same pass or rejected with falsifiable evidence. A finding is never deferred
silently.

Findings terminate. Each one exits as a fix now, a new principle, a new
anti-pattern, or an accepted risk that records why no mechanical check can
preclude it.

## Reject list

- Being your own adversary.
- An adversary primed on one register.
- A verdict with no attacks recorded.
- A finding parked in a note instead of corrected or rejected.
- Re-scoping to make a finding disappear. A re-budget must survive being
  stated without the word "scope".
