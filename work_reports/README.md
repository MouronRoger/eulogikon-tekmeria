# Work reports

- **Title:** Chronicle, Tekmeria
- **Status:** active
- **Authority_level:** chronicle. Binding on nothing.
- **Scope:** what was true once in this repo.
- **Relationship_to:**
  - lifecycle: `governance_cluster/script_lifecycle.md`
  - gates: `governance_cluster/adversarial_cross_check.md`

Governing documents state the present fact and never carry history. History
lives here, linked from a governing document when relevant, never embedded in
one. A dated note inside a rule file is the contamination this directory exists
to prevent.

One file per entry, named `YYYY-MM-DD_<slug>.md`.

## What belongs here

- A closure: what was done, what was verified, what remains open.
- An adversarial pass: the attacks run, what survived, what was found. Recorded
  as a table of attack, finding, and disposition. A bare verdict is not a
  record.
- A cold read: the findings and their dispositions (collapse, integrate, track,
  load-bearing).
- A one-time measurement whose script was deleted: the numbers, and how they
  were obtained.
- A tracked alarm: a defect deferred deliberately, named, so the deferral is
  visible rather than silent.

## What does not

- A rule. Rules have owner files.
- A summary of a rule. That is a second source.
- A plan for future work that nothing has committed to.
