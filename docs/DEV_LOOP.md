# Fast, economical development loop

The goal is fewer agent turns and fewer full game rebuilds, without weakening
financial checks or claiming unverified game integration. This governs development
cost; the game's inference budget is separate.

1. Choose one usable outcome, such as offer editing plus its cap comparison.
   Include related fixes in the same batch. Start from CURRENT_HANDOFF and the
   relevant worklist item; search history only to resolve a specific uncertainty.
2. Reproduce the issue once. Record the failing case, expected behavior and
   affected component. Avoid exploratory deployment after every small edit.
3. Implement the batch. Use targeted checks during editing:

   | Change | First checks | Rebuild |
   | --- | --- | --- |
   | Python rules/service | Affected tests; cap/signing/recovery tests when relevant | Service source only |
   | Addon/controller/screen | Affected native fixtures and renderer/navigation checks | Owning addon target |
   | Game hooks, ABI or guest headers | Failing regression plus native checks | Owning EXE/addon targets |
   | Documentation | Diff review and whitespace check | None |

   Shared interfaces can require both EXE and addon. Verify dependencies rather
   than assuming a DLL-only deployment is sufficient. Restored source timestamps
   must not leave diagnostic objects in a supposedly clean candidate.
4. Before the Deck installation, run required financial, protocol, shutdown and
   persistence checks affected by the batch, plus paired game validation. Run
   the full regression suite once for a delivery candidate where required; do
   not repeat it for unchanged bytes. Reuse the existing compiler, build tree,
   dependencies and test profiles.
   Before direct CMake game builds, regenerate register-local inputs with
   `python tools/gen-reg-locals.py` (using configured `--gen`/`--out` paths),
   then run the same command with `--check`. Source patch checks alone do not
   verify the generated copy actually compiled into the EXE. This is unnecessary
   for addon-only builds.
5. Run long builds/checks as a predetermined shell sequence with logs on disk,
   exit codes and completion receipts. Inspect completion or a meaningful failure,
   not every compiler line. Space necessary status checks 30–60 seconds apart;
   avoid repeated unchanged CI queries. No scheduled monitor or extra agent.
6. Install once after a normal game exit. Follow one short acceptance plan:
   boot, load the expected franchise, exercise the changed flow, check money,
   then save/reload when persistence changed. Do not infer UI state from consumed
   input or a global screenshot showing another application.
7. Commit/push code and final evidence together once. Update CURRENT_HANDOFF with
   only the verified result, remaining blocker and next action. A completion
   message needs the outcome, checks and unresolved limitation—not a tool diary.

For a fresh focused chat, supply the repository path and ask it to read AGENTS.md
and CURRENT_HANDOFF. Keep detailed historical evidence in WORK_PROGRESS. Do not
start another chat or agent automatically; do not drop required acceptance work
merely to reduce token use.
