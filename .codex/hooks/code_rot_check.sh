#!/bin/sh
# TDP-012: session state and pointers only. At most two display lines, never
# rule text. Rule text here would be a second copy of the law (R3), which is
# the thing this hook exists to not be.
STATE="armed: gate -> store -> compose -> verify -> cold-read | no printed fact without provenance | the store is the state"
cat <<JSON
{"continue":true,"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[Tekmeria] ${STATE}\\nRead CLAUDE.md; principles: governance_cluster/canonical_design_principles.md; rot: ROT.md"}}
JSON
