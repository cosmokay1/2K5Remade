# Completed-season salary policy

The user selected `game-completed-seasons-v1` for minimum-salary classification.
This is a simulation policy, not reconstructed NFL salary-credit eligibility.
Minimums constrain legal offers; personality, performance and promises determine
negotiation above those floors. Hidden ratings are not inputs.

The supported save's career-period counter is the five-bit field at player+0x24,
bits8–12. A counter of1 represents the first season and maps to zero completed
seasons. Values above1 map to counter minus1. Zero remains unknown. Historical
statistics need not exist to use this explicitly adopted game-season policy.

The exporter supplies annual minimum projections with one additional completed
season per scheduled future year. Those are contract-floor projections, not
records that a future season has already occurred. Real calendar advancement
still requires the supported league transition and refreshed inputs.

New veteran offers use the active/inactive compensation category. Zero-season
players are left for separate drafted/undrafted rookie rules and allocations;
they are never silently classified as veterans. Preserved legacy contracts keep
their existing schedules. Unknown retained cash, guarantees or other obligations
are not filled with invented values by this import.

The existing published minimum table supplies2020–2030 amounts. Original2004
calendar franchises use the approved2026 reference-year/historical-dollar policy;
explicit modern calendar/money context uses its declared modern year. Unsupported
horizons reject. Game/mod names and executable hashes do not choose salary rules.

## Existing franchises

`tools.export_simulation_salary_inputs` exports a declared input bundle from a
pinned save, existing registry and explicit team revision map. It preserves player
IDs and seed, records the actual input payload hash, and refuses to overwrite its
output. Its report lists rookies and unknown counters separately.

```sh
python -m tools.export_simulation_salary_inputs SAVEGAME.DAT bindings.json revisions.json salary-inputs.json
python -m tools.import_salary_classification franchise.sqlite salary-inputs.json
```

The second command previews a private SQLite snapshot, including committed WAL
state. Add `--apply` only for the intended database. The atomic league import
preserves immutable bootstrap rows, existing actor/history events, ownership,
contract charges and cash. It increments each financial revision once. Identical
retries replay the existing batch; changed inputs, stale revisions, partial
coverage, rookie overlap or replacement of existing credit inputs reject.
Prepared guest work blocks the import until recovery resolves it.

Both the CBA table provenance and the simulation classification source remain in
server negotiation accounting. Importing salary inputs grants no AI access or
guest writes and does not certify complete opening books. A configured runtime
must be moved to the new financial revisions and validated separately.
