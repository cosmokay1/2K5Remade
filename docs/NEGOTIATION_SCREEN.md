# Addon negotiation screen

The UI target is a replacement for the native contract negotiation screen. The
compact HUD is an interim diagnostic, not the final interaction. Keep the game's
visual style and controller conventions; use the retained native renderer rather
than a WebView or separate launcher. This screen belongs to the franchise addon;
the independent engine-sidecar transport does not acquire franchise rules.

## Player flow

1. Open a player's contract negotiation from the normal franchise menu. Resolve
   the current player, team, loaded-save epoch and supported financial revision
   before offering editable controls. Opening or browsing never calls the model.
2. Show annual salaries, signing bonus, supported guarantees, annual cap charges
   and the resulting cap room. Separate cash compensation from cap charges.
   Show sourced performance with its actual window and coverage. Missing counters
   say unavailable; raw saved period/mode codes do not become current-season stats.
   No hidden ratings, numerical personality scores or replacement overall grade.
3. Edit contract terms and supported promises inside the replacement screen.
   A promise specifies the goal, target and observation window. Unsupported
   guarantees/terms cannot be submitted. Preview checks are ordinary accounting,
   not model requests; fresh evidence is required after changes.
4. Explicitly submit one offer. Freeze that submission while it is pending, then
   show the complete player/agent explanation and accepted/rejected/counter terms.
   A counter remains a proposal with its own accounting eligibility. A response
   cannot itself sign, commit promises or fabricate a holdout. Durable offended
   reactions already exist; approach limits and withdrawal remain separate work.
5. Apply an accepted deal only through the verified native transaction boundary,
   fresh remote control, journal and ledger checks. Reconcile the resulting save
   and reload it. Preserve native offseason free-agency waiting and competition;
   a replacement screen must not turn an auction bid into an immediate signing.

B returns to the franchise menu. Leaving during an outstanding request does not
cancel or forget a decision already persisted. Reopening resolves the existing
request; it does not purchase another model call. The existing Steam entry and
Gaming Mode Xbox trigger mapping remain the entry point.

## Input ownership is part of the replacement

An opaque full-screen picture is insufficient: original controls must not run
underneath it. The runtime needs one bounded controller-event bridge after its
host input gathering (including the retained legacy path), before the packet is
written to guest memory. Ownership must be scoped to the verified offer screen
and controlling port, with edge/release handling and an explicit B exit. The
addon owns draft edits, focus and pending state. Rendering never submits an offer
or reads guest memory. The native signing path remains held while addon-controlled
negotiation is active, even when AI is disabled or the addon fails.

Use the existing named addon event/snapshot mechanism. Do not add mod-name
branches, a new IPC service or an independent cap implementation. Original and
SOFTDRINK content are selected by validated data/contract capabilities. The
unchanged vanilla path still operates when addon negotiation is not selected.

## Implemented data boundary

`franchise.negotiation-view.v1` accepts exactly `sizeof(FranchiseNegotiationView)`.
It copies an owned compact status plus the complete transport-validated JSON
context/proposal reply, up to the existing 65,535-byte frame bound. The body keeps
exact schedules, financial previews, performance records, missing-data/source
labels, agent speech and counter/promise proposals already present in that reply.
No second model call, new monetary conversion or reason truncation is introduced.

The compact status may advance through journal preparation/recovery while the
matching context/proposal remains available. Status replies do not replace it
with a smaller journal payload. During a new submission the previous reply is
cleared. Player/offer/source/screen invalidation and shutdown use the existing
visibility and clearing rules. Copies do not borrow transport memory or perform
I/O. Missing/older addons and failed snapshots return an empty replacement view.
The v1 compact display and generic addon ABI are unchanged.

This snapshot is display evidence, not an authorization or an editable source of
truth. Consumers must parse it once per changed body, render only relevant fields
and preserve uncertainty. Empty history must never become zero production. Raw
JSON and internal IDs are not player-facing UI.

## Read-only takeover implementation

The replacement renderer and navigation now compile into the franchise addon,
not the main game. Two optional domain-neutral host messages provide gathered
controller packets and a caller-owned BGRA drawing buffer. The addon never keeps
host buffer pointers. Existing unsupported addons return no handling and leave
the original presentation/input path available.

The preview defaults off. It requires `NFL2K5_FRANCHISE_SCREEN_PREVIEW=1` and an
explicit `NFL2K5_FRANCHISE_SCREEN_PORT=0` through `3`. The configured port controls
the view; other ports cannot operate the covered original menu. The current Deck
will use an explicitly configured port during private testing, not an inferred
team/controller assignment. Negotiation and guest signing must both be off;
conflicting modes reject service startup. The game shim holds native signing
throughout preview mode, including missing/disabled addon and failed rendering.

Contract, Performance and Agent sections use a navy/crimson franchise layout and
Bahnschrift. A vertical section list, structured annual money table and dedicated
scrollable dialogue/evidence panel replace the initial text-only prototype.
The table is used only for supported previews with up to five annual rows;
longer/rejected offers use the full scrollable view so terms/reasons remain
accessible. Colors do not claim team branding without sourced palette metadata. Up/down on the D-pad or left stick selects vertical sections; LT/RT also change sections. The right stick scrolls content; B sends exactly
one native Back packet and dismisses the view. Entry waits for held buttons to be
released before navigation. Sticks use a neutral dead zone and one action per deflection, with hysteresis to prevent drift repeats. Addon failure/invalidation quarantines held controls
until neutral, preventing an old A/trigger press from reaching the native menu.
The host copies no borrowed addon image pointers. Full opaque BGRA frames are
cached; unchanged text does not redraw. Failed painting releases screen ownership.

The preview publishes an empty-response loading snapshot as soon as the offer FSM opens, before the read-only handshake/context reply. It contains no player or financial claims. Failed/closed source state still clears the owned view. Context round-trip, largest owner polling gap and initial paint timing are logged separately from financial evidence.

Terms, exact cap amounts and full player responses/counters/proposed promises
come from the matching snapshot. Historical records remain separate, explicitly marked as having unverified
season/coverage; raw period/mode codes remain in the source payload. Hidden/unsupported performance
metrics refuse display. Editing, inference, application and promise commitment
are absent from this read-only mode. Its controls do not imply verified live-game
input ownership until the actual installed build is exercised.

## Remaining implementation and acceptance

- Validate the authored read-only takeover on the actual Deck, then add the
  controller-owned editor. Retire the compact diagnostic after takeover is verified.
- Use the same draft in financial previews, promise proposals and explicit submit;
  require current player/source/revision and preserve request identity on retry.
- Render actual stats and full explanations at Deck 1280x800 and 1280x720, with
  controller-accessible overflow rather than silently clipped speech or counters.
- Verify cancel, pending exit/reopen, changed player/save, shutdown, original and
  SOFTDRINK capabilities, offseason waiting and in-season free agency.
- Complete a bounded real model response test with writes held, then verify actual
  legal signing, ledger/save agreement and reload before enabling application.

The data-boundary change alone did not deliver a screen. The subsequent read-only
implementation passes Windows rendering fixtures and isolated Proton execution
on the Deck; actual game takeover still needs verification. It does not deliver
editing, a live model test or controlled signing. AI remains disabled.
