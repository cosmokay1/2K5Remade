# Current handoff

Repository: `/Users/cosmokay/Documents/ChatGPT/2k5`
Branch: `codex/franchise-negotiation`. Scheduled task must remain PAUSED.

## Current outcome and next action

Finish startup stability, then one bounded actual negotiation and signing /
cap reconciliation / save-reload test. None of those financial acceptance stages
is verified by a passing compile or fixture.

Startup repair source: `9a61eba`. Fixes stale register-local synchronization over
nested patch-call arguments/return slots. Focused upstream draft PR:
https://github.com/BeyondTomrrow/2K5Remade/pull/7

Verified: 972 local Python tests, 14 portable native tests, Windows/Linux fork CI,
11 private Windows component checks and game `--validate`. Clean main/host
objects were explicitly rebuilt to remove temporary probes. The installed private
candidate displayed the title/settings/VIP screens and team selection on the
Deck. Repeat boot, correct franchise/menu visibility and signing remain unverified.
A later global capture showed another game while NFL2K5 remained alive: establish
which window is visible before sending more inputs.

Private evidence/scripts: `.local-runtime/live-clock-signing-v1/`. Deck base:
`/home/deck/.local/share/2k5-franchise-build`; isolated runtime:
`live-clock-signing-v1/live-profile/runtime`. Existing Steam entry routes there.
Use the existing SSH key and game_test_control tool; identify the exact process
and runtime, not broad command-line substring matches.

Installed EXE SHA256: `337b742a383b425ccbbadf000df1f159030a001f0fbaeb1f80fee457bb54596d`.
Addon SHA256: `3ab8124c91465142fb1834bf8ea4f47dfad22e34c5996758fbf9f989f80517e0`.

Installation preserved all 205 files from its immediate preinstall baseline.
Compared with the initial profile baseline, 203 original save files and the
original franchise DB match; original Partition0/Partition5 changed earlier.
These are the disk header/title cache, retained and recorded without rollback.
See startup-fix-install-receipt.json; do not claim all initial hashes match.

## Controls and pending feature

Existing inference ceiling: one request / 20,000 tokens, same existing budget DB
and scope. Last inspected: zero attempts. Verify current usage before submitting.
User-approved Token Creator grant expired October 16 at 1:30 PM PDT. Do not renew.
A non-refreshing token issued within that window had wrapper expiry 1:41:27 PM PDT;
it may now be expired. Do not print tokens or fall back to owner credentials.
Remote shutdown control and inference ceilings must not be renewed or increased.

Smaller signing bonus adjustments: target 1 percentage point plus dollar amount.
NOT IMPLEMENTED. Native contract encoding currently uses 10% steps. Exact terms,
annual cap charges and save/reload must work before exposing finer precision.
Do not fake a slider that rounds accepted terms back to 10%.
