# Project instructions

Keep implementations YAGNI. Abstractions and complexity must earn their existence.
Preserve unrelated edits, game assets, saves, ledgers and upstream attribution.
Authenticated `gh`/Git operations require leaving the sandbox.

## Development loop

Read `docs/DEV_LOOP.md` and `docs/CURRENT_HANDOFF.md` first. Read only the relevant
WORKLIST section and source files next; use WORK_PROGRESS as historical evidence,
not mandatory reading in full on every turn.

Use one agent by default. Batch related changes into one testable outcome. Run
checks appropriate to the affected component while editing; run broader required
checks once before delivery. Do not rebuild the game EXE for sidecar-only edits.
Do not poll unchanged compiler/CI state repeatedly or rerun passing checks without
a new change or unresolved concern. Keep logs in files; return concise results.

Commit/push a validated batch once. Do not create separate evidence-only commits
for each passing check. Combine Deck changes into one installation and test plan.
Never replace loaded binaries. Distinguish compilation, boot, negotiation,
signing, cap reconciliation and save/reload evidence.

Keep the scheduled task off. Do not renew controls, IAM grants or inference
budgets without explicit user approval. Use offline fixtures during development and existing bounded inference
only for an explicitly authorized integration test.
