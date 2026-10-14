# Supported same-year veteran return signing

The durable prototype now supports an explicit return agreement through
FranchiseStore.return_sign, after backed-up format4 migration. The club must have
a known closed released/assigned agreement and known cash history for the player.
Exclusive ownership must be free across the league. The operation creates a new
agreement, allocated cash obligation and cap charges atomically with ownership
and its versioned journal record. Every old obligation and retained charge stays.

PreseasonReturnScope records league_year, signed_on, first_regular_season_game,
healthy=True, exact exclusions and source. Dates must be in the same sourced
league year, before the first game and consistent with established chronology.
The exclusions are extensions, rookie_contracts, guarantee_offsets and
league_year_rollover. Annual minimums and the current cap remain binding; this
operation does not supply economic or calendar facts missing from the ledger.

Agreement identity is contract-gen: plus SHA-256 of compact UTF-8 JSON
[team_id,player_id,request_id]. Its cash obligation uses the same ID. Original
legacy contract:player payment IDs remain valid. Payments resolve each agreement's
own lifecycle ceilings; cancelled unprotected base cannot be paid after release.
Repeated returns create distinct agreements. Old receipts retry without restoring
old contracts or ownership; changed terms/source reject.

Return signing, subsequent release and cash payments record format1 generation
postings in format4 journals. Replay retains the legacy financial view for old
events and validates complete archived obligations for these new operations.
Transaction failures, including failure after ownership insertion, roll back.
Native inspection accepts the new ID and requires its matching cash obligation.

This is an explicit engine operation. AI negotiation and the native pipe do not
yet initiate return signing. Returned-player trade/restructure paths reject until
versioned support exists. New promises/story decisions, season progression,
guarantee offsets, real guest hooks and game save/load remain unfinished. Tests
use synthetic accounting sources and do not prove actual game integration.
