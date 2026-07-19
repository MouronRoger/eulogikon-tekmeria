# Write access to `.eukoine/` — EKDP-032 / CDP-057

`.eukoine/` holds the family **single source** — the corpus identity grid, v5 JSON,
database schema, `corpus_api`, and the shared predicate vocabulary — plus this access
note. This explains **how it is protected** and **how it changes**. It does not contain
the authorization phrase.

**The spec:** [`corpus_identity_and_schema.md`](corpus_identity_and_schema.md) ·
[`interim_head_citation.md`](interim_head_citation.md) (pre-settlement head citation) ·
[`predicate_vocabulary.md`](predicate_vocabulary.md) /
[`predicate_lexicon.yaml`](predicate_lexicon.yaml) (shared code lexicon).
**Access / sync / git safety:** this document (`WRITE_ACCESS.md`).
**Governance:** eulogikon **CDP-057** · EuKoine **EKDP-032** (`docs/governance/registry.yaml`).

---

## No secondary sources (EKDP-004 / EKDP-005 / EKDP-032)

The `.eukoine/` directory is the **only** place the family corpus-identity spec and its
change/sync mechanism may be **stated**. Everywhere else — READMEs, rules, campaigns, agent
guides, hooks, comments — **points here**; it does not summarise, explain, reinterpret, or
re-derive.

| Canonical document | States (canonically) |
|---|---|
| [`corpus_identity_and_schema.md`](corpus_identity_and_schema.md) | identity grid, v5, schema, `corpus_api` |
| [`interim_head_citation.md`](interim_head_citation.md) | interim head citation while passage identity is provisional |
| [`predicate_vocabulary.md`](predicate_vocabulary.md) | consult-before-coin obligation for the shared code lexicon |
| [`predicate_lexicon.yaml`](predicate_lexicon.yaml) | positive registry of baptised code signifiers |
| [`WRITE_ACCESS.md`](WRITE_ACCESS.md) | write protection, synchronizing-agent workflow, git safety |

A "helpful summary", a restated subset of rules, a parallel "current understanding", or a
second copy of any `.eukoine/` normative content is a **second source** — rot (G4). Read the
canonical documents; cite them by path; never copy or paraphrase their normative content
elsewhere. Where code and the spec disagree, the code is the defect.

---

## The model: one source, pushed down (not a hand-mirrored copy)

The hub holds the **canonical** `.eukoine/` artefacts — manifest-listed and OS-locked
(`uchg`); any correction uses the unlock cycle below. Members carry **mirrors** written
**only** by `naming/sync.py`, byte-identical to the hub. Do not hand-edit a mirror:
edit the hub canonical copy, then sync. Bytes that did not come from the hub are rejected
by the content-bound guard; where code and the spec disagree, the code is the defect.

**Who may change the spec:** any agent in **any family repo**. There is no repo-bound write
jurisdiction — only the single-source / mirror discipline (EKDP-031/032). The unlock → edit →
push → verify → lock cycle always acts on the one canonical hub copy and propagates
byte-identical mirrors; driving it from eulogikon is the same operation as driving it from EuKoine.

| Repo | Role | Who writes `.eukoine/` |
|------|------|------------------------|
| **EuKoine** | canonical | a **synchronizing agent** (any family repo), via the unlock cycle below |
| **eulogikon** / **EuGraphikon** / **EuMorphikon** | synced mirror | **only** `naming/sync.py` (drivable from any family repo) |

The sync/lock **toolchain** (`naming/sync.py`, `naming/_manifest.py`,
`naming/sync_manifest.toml`, `scripts/eukoine_spec_lock.py`) is itself synced
byte-identical into every member, and each tool resolves the canonical hub from
wherever it runs. Driving the cycle is not hand-writing a mirror: a member's `.eukoine/` is still
written only by the sync tool, byte-identical to the hub.

This replaces the former "read-only mirror / reject every `.eukoine/` commit" rule, which
blocked the legitimate re-sync along with the illegitimate hand-edit. The guard now tells
them apart by **content**.

---

## The enforcement: a content-bound pre-commit guard

`scripts/audit/check_eukoine_spec_protected.py` — one script, synced to every repo — gates
every `.eukoine/` commit:

- **`--role canonical`** (EuKoine): a `.eukoine/` commit needs an open spec write session
  (`.eukoine/.write_session`), created by the unlock script. Authoring is open-ended, so
  the session is existence-gated.
- **`--role mirror`** (members): a `.eukoine/` commit is allowed only when an open session
  authorises the **exact staged bytes** — every staged path must hash to the value the
  session records. A hand-edit changes the hash and is rejected; a stale token does not
  match new bytes. **`naming/sync.py` does not use this path:** it commits with
  `--no-verify` after hub-side hash verification (member hooks govern member work, not
  hub propagation — EKDP-031/032; see [`STANDARDS.md`](../STANDARDS.md) §3).

Pre-commit is a convention guard, not a cryptographic boundary (`--no-verify` bypasses any
hook); a signed-token upgrade is recorded as future work (`DECISIONS.md`). Locked documents
also carry the macOS `uchg` immutable flag as a second, accidental-write guard.

---

## How the spec is changed — from any family repo

The unlock, sync, and lock commands are **the same in every family repo** — EuKoine,
eulogikon, EuGraphikon, EuMorphikon. Run them from whichever repo you are working in;
they always act on the hub's canonical copy and propagate byte-identical mirrors. There is
no separate member workflow.

### Hub resolution

Every tool resolves the canonical hub automatically:

1. **`EUKOINE_HUB`** — if set (absolute path, or relative to the current working
   directory), that directory is the hub;
2. **the invoking repo** — if its directory name matches `naming/sync_manifest.toml`
   `[hub] name` (i.e. you are inside EuKoine);
3. **the sibling hub** — otherwise `../eukoine` relative to the invoking repo (the
   layout declared in `naming/sync_manifest.toml` `[mirrors]`).

Confirm the resolved path before any edit:

```bash
python scripts/eukoine_spec_lock.py status
```

`status` prints the hub path, whether each manifest artefact is locked (`uchg`), and
whether a write session is open.

### The cycle — unlock, edit, synchronize, lock

**Prerequisite:** James has authorized the edit (EKDP-027). James holds the unlock key in
the hub `.env`; any agent may run `unlock` once he has decided. Do not read `.env` or run
`unlock` until then.

**Step 1 — Unlock** (opens a spec write session; clears `uchg` on locked artefacts):

```bash
python scripts/eukoine_spec_lock.py unlock --from-env
python scripts/eukoine_spec_lock.py status    # write session: active; artefacts unlocked
```

**Step 2 — Edit and commit** (hub canonical copy only — never a member mirror):

Edit the hub's `.eukoine/` files (and any other manifest paths). Commit on the hub while
the write session is open — explicit `git add` per path (see §Git safety):

```bash
cd /path/to/eukoine    # or stay in a member repo and edit the resolved hub paths directly
git add .eukoine/WRITE_ACCESS.md              # list each changed path
git diff --cached --stat
git commit -m "sync: …"
```

**Step 3 — Synchronize** (propagate hub → every mirror; runnable from any family repo):

```bash
python naming/sync.py push                    # dry-run: what would change
python naming/sync.py push --execute          # write mirrors + commit in each member repo
python naming/sync.py verify                  # confirm committed byte parity hub == mirrors
```

**Step 4 — Lock** (close the write session; re-apply `uchg` on the hub):

```bash
python scripts/eukoine_spec_lock.py lock
python scripts/eukoine_spec_lock.py status    # write session: none; artefacts uchg
```

**Full cycle in one place** (identical commands whether your shell is in EuKoine or
eulogikon):

```bash
python scripts/eukoine_spec_lock.py status
python scripts/eukoine_spec_lock.py unlock --from-env
# … edit hub canonical artefacts; git add + commit on the hub …
python naming/sync.py push
python naming/sync.py push --execute
python naming/sync.py verify
python scripts/eukoine_spec_lock.py lock
python scripts/eukoine_spec_lock.py status
```

`push --execute` is an irreversible, outward-facing act (it commits inside member repos) —
the reserved class (EKDP-027). For locked artefacts it requires `EUKOINE_SPEC_AUTHORIZE` in
the hub `.env`. It is verify-then-commit, all-or-nothing per repo, and idempotent: re-run to
converge; it reports any repo left behind. Only manifest paths are touched; unrelated member
WIP is neither read nor required green. Mirror commits use `--no-verify`; hub
`naming/sync.py verify` is the authority for byte parity.

**What is synced is declared once** in `naming/sync_manifest.toml` (EuKoine) — the sync
iterates that table, never a filesystem glob. A file under `.eukoine/` not on the manifest
is a finding, not an auto-target.

---

## Synchronizing agent

When changing the synchronising set, follow §How the spec is changed — the same unlock →
edit → synchronize → lock cycle from any family repo. Summary:

1. **Request unlock.** Ask James to authorize the edit (EKDP-027). James holds the key in
   the hub `.env`; any family-repo agent may run `unlock --from-env` once he has decided.
   Do not read `.env` or run unlock until then.
2. **Amend and commit.** Unlock, edit the hub's canonical copies (`.eukoine/` and any
   other manifest entries), commit on the hub while the write session is open — explicit
   `git add` per path; review with `git diff --cached` (see §Git safety).
3. **Synchronize.** `python naming/sync.py push --execute`, then `python naming/sync.py
   verify`.
4. **Lock.** `python scripts/eukoine_spec_lock.py lock`; confirm with `status`.

Never hand-edit `.eukoine/` in a member repo. Never require sibling trees to be clean first.
Found drift in a mirror after push? Re-run step 3; fix broken implementations, never patch the
spec to match broken code.

---

## Git safety (hub and mirrors)

Synchronisation must not disturb unrelated work. Agents have caused panic by stashing sibling
trees, by using broad `git add`, and by committing files James did not intend to include.

### In member repos (mirrors)

**Use only `naming/sync.py push --execute`** for propagating the synchronising set. The tool:

- writes **only** manifest paths (`naming/sync_manifest.toml`);
- commits **only** those paths (pathspec `git commit -- <paths>`);
- leaves other modified and staged files **untouched**;
- never runs `git add -A`, `git add .`, `git commit -a`, `git stash`, `git stash pop`, or
  whole-tree clean-up commands.

Do **not** hand-commit manifest paths in a mirror. Do **not** stash or reset a sibling tree
to "prepare" for sync.

### On the hub (EuKoine)

When committing hub changes (step 2), stage **explicit paths only**:

```bash
git add .eukoine/WRITE_ACCESS.md              # list each path — never git add -A / git add .
git diff --cached --stat                      # review what will enter the commit
git commit -m "sync: …"                       # commits only what you staged
```

**Prohibited on the hub during sync work:** `git add -A`, `git add .`, `git commit -a` (these
stage everything and invite accidental commits). Prefer listing each changed path; use
`git diff --cached` before every commit so nothing enters unnoticed.

**Prohibited in member repos during sync work:** any manual git write except what
`naming/sync.py` performs; any stash/pop/reset to "clean" the tree first.

---

## Authorization (EKDP-027 — not stored here)

James holds the unlock key — `EUKOINE_SPEC_AUTHORIZE` in EuKoine's repo-root `.env`
(gitignored; listed in `.cursorignore`). Only James can authorize a spec edit session.
Any agent in any family repo may run `python scripts/eukoine_spec_lock.py unlock
--from-env` once James has decided to authorize; the script reads the phrase from the hub
`.env`. Agents must not read `.env` themselves, nor run unlock, until James has authorized.
