# The standing-posture hook

- **Title:** Hook maintenance contract, Tekmeria
- **Status:** active
- **Authority_level:** maintenance contract for `code_rot_check.sh` and its
  `.codex/` twin. Not a rule owner.
- **Scope:** `.claude/hooks/`, `.codex/hooks/`
- **Relationship_to:**
  - principle: `governance_cluster/canonical_design_principles.md` TDP-012

## What it is

The prevention layer. A `UserPromptSubmit` injection that keeps the working
posture and the pointers resident before and during authoring, every turn. It
acts inside the agent's loop, which is the one place rot creation is actually
preventable. The agent does the looking; the hook orients it.

## What it is not

It is not a guardian, an audit script, or a closure ritual. It does not scan
files, query anything, or block anything.

**It never carries rule text.** The rules live in their owner files. Editing the
hook to inject a rule or a reminder is the restatement disease (R3) the hook
exists to not be. Two display lines, state and pointers.

## Update it when

- A phase is added to or removed from the working sequence.
- An owner file is renamed or a new top-level authority appears.

## Do not update it for

- A new principle, anti-pattern, or rot class. Those live in their registries.
- A reminder about a mistake made once. That is a work report, or a rule with
  an owner.
- Anything that would make it longer than two display lines.

## The twin

`.claude/hooks/code_rot_check.sh` and `.codex/hooks/code_rot_check.sh` are
byte-identical; only the wiring differs. Edit both in the same act. Divergence
between them is itself R3, and there is no mechanical twin-check: that absence
is a present-tense fact, not a silent gap.
