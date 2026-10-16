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

Contract, Performance, Personality and Agent sections use a navy/crimson franchise layout and
Bahnschrift. A vertical section list, structured annual money table and dedicated
scrollable dialogue/evidence panel replace the initial text-only prototype.
Contract terms use the annual table whenever an offer can be decoded, including
active-player/rejected offers and long contracts. Columns show year, base salary,
guaranteed base, bonus cap and cap hit. Unsupported/unavailable preview amounts
stay unknown, never zero; a rejected offer keeps its available terms visible.
Long tables scroll with the right stick. The cap-room figure is shown only when
an authoritative supported preview exists, retaining its opening-liability caveat.

`NFL2K5_FRANCHISE_SCREEN_EDIT=1` additionally enables local contract drafting;
it defaults off and requires the read-only takeover configuration above. On
Contract, A opens the editor. D-pad/left-stick up/down selects total, years,
bonus share or salary schedule; left/right adjusts it. Hold RT for larger value
steps. X explicitly checks the draft and returns the service's exact annual
table or rejection. B cancels editing without leaving the offer screen. Editing
and checking never contact a player, change their opinion, call a model, reserve
cap room or alter the native offer/save. Actual submission remains unavailable.

The initial editor supports one through seven years, bonus shares in ten-percent
steps and the calibrated Balanced/Descending schedules. An existing schedule can
be retained without inventing a name for it. The displayed editable total is
approximate because the native salary schedule rounds annual amounts; the checked
table remains authoritative. Unsupported bonus allocation and accounting rules
still reject through the service, and a rejected draft can be edited again.
Both supported dollar scales use the same format-driven editor.

Only one check can be pending. The UI queues copied terms against its displayed
context generation; the transport owner revalidates player, native offer,
calendar, finances and loaded source before sending a read-only request. Screen,
player/source changes and shutdown discard obsolete drafts/replies. Pending checks
block repeated X requests; held controls must return to neutral before operating
a newly opened editor or the surrounding screen. No generic addon ABI or native
game financial entry point is added for editing.

Performance uses football stat tables for Receiving (G/REC/YDS/TD), Passing
(G/CMP/ATT/YDS/TD/INT), Rushing (G/ATT/YDS/TD) and mapped Defense (G/SCK).
Only categories with observed values are shown; games-only evidence has an
appearances table. Rows join only identical saved period/mode keys. Repeated
metric entries remain separate, without summing or guessing a season. Missing
cells use a dash; a known zero stays zero. Unmapped pressure/QB-hit fields do not
appear as speculative columns. The YEAR column maps validated saved calendar candidates through the pinned
franchise season year; an unavailable mapping remains a dash. Current MyNFL1
resolves Dart to2025 and Nabers to2024/2025, rather than exposing raw title years.
Height, weight and age at season start are read from the pinned player record and
shown beside the name. Injury tendency remains explicitly insufficient history
until sourced injury/availability observations are connected.
The header places compact icon-only references to the two leading saved traits
on the same row as height, weight and age. Each trait retains its own authored
line icon: pay (coin), security (shield), playing time (stopwatch), winning (trophy)
and loyalty (linked rings). A dedicated Personality section repeats each icon
beside its name and short description so players can learn the symbols. The
shared priority ordering agrees with the compact display; the replacement
screen does not combine them into a Priorities sentence or show a fictional-traits
label. Missing initialized personality stays unavailable on its detail page.

Personality also shows separate labeled bars for team trust, respect and
connection. Each bar reads the saved value on the same zero-to-one range, with a
neutral midpoint marker; missing values remain Unknown rather than appearing as
a known zero. Numeric traits and hidden gameplay ratings are not printed. Trait
descriptions and bars share the existing scrollable detail panel.

Agent uses a bottom-aligned conversation layout. The captured submitted offer
appears on the right with sender You; the full player/agent response appears on
the left with its counter and proposed promises intact. A draft preview never
becomes a sent message. Before a response exists, the empty state says there is
no conversation yet and submission is off. The current captured exchange is
shown; older exchanges and typed free-form chat are not connected. Long messages
scroll without truncating the response. No timestamps or conversations are
invented. Age-conditioned generation, personality evolution, teammate
relationships and market momentum remain pending.
The raw Record list, unit suffixes and long missing-metric inventories are removed
from the player page. Agent explanations keep their dedicated scrollable prose. Colors do not claim team branding without sourced palette metadata. Up/down on the D-pad or left stick selects vertical sections; LT/RT also change sections. The right stick scrolls content; B sends exactly
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
on the Deck; actual Dart/Nabers takeover is verified on the previous installed build. The
new table-only addon still needs installation and actual game verification. It does not deliver
editing, a live model test or controlled signing. AI remains disabled.


## Delivery rule for remaining systems

This screen evolves with the remaining negotiation systems. Completion includes
visible sourced state, useful comparisons, controller-operated actions, pending
and failure states, natural-language outcomes and save/reload verification.
Current/proposed contracts, promises, agent stance/timing, fifth-year options and
injury evidence must join this interface as their engine paths become usable.
Do not represent backend plumbing or disconnected controls as a finished feature.
