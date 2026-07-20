# Capability port shape

- **Title:** Capability port doctrine, Tekmeria
- **Status:** active
- **Authority_level:** member doctrine. Owner of TDP-010. Downstream of family
  direction, `../EuGraphikon/go-port/PROGRAM.md`.
- **Scope:** the composition store, the scripts that read and project it, and
  any service built around them. Not the essay prose (TDP-012).
- **Relationship_to:**
  - principle: `governance_cluster/canonical_design_principles.md` TDP-010
  - gate: `governance_cluster/adversarial_cross_check.md` (attacks the plan)

## Why the shape, and why it is not negotiable

The system is being ported to Go. Python is the current implementation, not the
target, and every structure written now is written to survive translation.
This is what stops an engine accreting into a switchboard of conditionals that
only its author can trace: a shape that must compile in a language with no
duck typing, no ambient dictionaries, and no runtime monkey-patching cannot
absorb that kind of accretion.

The shape is therefore forward-binding. All new engine code is capability-port
by construction, and every improvement to existing engine code moves it toward
the port shape. Behaviour before structure, one concern at a time, net
subtractive, never big-bang, never two parallel paths standing.

## The three parts

**Driver, the owner.** The single component that holds the invariant in one
place. There is no second path to the effect. If two components can both
produce the effect, one of them is the defect.

**Port, the boundary.** A narrow typed protocol the driver calls. No storage or
infrastructure shape leaks through it: no untyped row bag, no raw cursor, no
driver payload at the boundary. The port names behaviour, never mechanism.

**Adapters, the mechanics.** Provider-specific work only. An adapter has no
power over the invariant: it returns a typed result behind the port or raises a
genuine transport error. It can neither hold the guarantee nor break it.

**If you cannot write the port signature, you do not have a port.**

A pure single-owner consolidation with no infrastructure seam has an owner but
no port. Say so explicitly rather than manufacturing one.

## The worked shape here

The composition store is the case that makes this concrete.

- **Invariant:** the state of a composition (candidates, plan, stations,
  blocks, index, claims) has one writable home, and every station moves
  `pending` to `drafted` to `checked` only through the defined operations.
- **Driver:** the store owner, holding that state machine.
- **Port:** the composition operations. Record a candidate set with its query
  and timestamp. Open a station. Write a block. Append an index row. Register a
  claim. Record a verification result. Read the index. Read a chunk's blocks.
- **Adapters:** SQLite today. The shared Postgres schema later.

That second adapter is the whole argument. The store is declared foldable into
the shared corpus, and a fold is mechanical exactly when the fold target is a
second adapter behind an existing port, and a rewrite exactly when it is not.
The port is not ceremony bought against a hypothetical: it is what makes the
declared next step cheap.

## Falsifiers

A plan is rejected if it trips any of these:

- an invariant held in two or more places, or smeared across copies;
- an untyped record bag crossing the boundary;
- the projection to HTML reading the store through anything but the port;
- an adapter that can end or fail the guaranteed outcome;
- a sync or transport decision taken at runtime rather than at the boundary;
- a mutable side-channel splitting ownership;
- two parallel paths left standing, or a big-bang rewrite;
- a guard added downstream where the owner could preclude the violation by
  construction.

## The Go-shape check

Before code, confirm on paper:

- [ ] The owner compiles to one struct.
- [ ] The port compiles to one interface.
- [ ] The adapters are the only thing that varies.
- [ ] No untyped map at a boundary, no runtime transport decision, no mutable
      side-channel splitting ownership.

## Reject list

- A fix at the site where the symptom surfaced, with the owner never inspected.
- A special case keyed on a particular author, work, or term.
- Threading a parameter or a conditional through existing modules with no
  driver, port, and adapter named.
- Targeting a line count. Report it; the criterion is sound structure carrying
  its work, not small structure carrying anything.
