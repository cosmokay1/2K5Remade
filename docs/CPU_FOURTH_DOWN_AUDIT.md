# Fourth-down audit: evidence before tuning

No CPU preset, Deck setting or save was changed for this audit.

User observation: CPU punted in its opponent's territory, approximately the
30-yard line (earlier described as the 30–40). Distance, score, quarter and clock
are still unknown. This is not enough to reproduce a complete decision.

## Pinned source and disk image

Creator source: [e193841, CPU money downs](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_cpu_money_downs.py),
[Modern2 assembly](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/tools/nfl2k5_cpu_money_downs_m2.S).
Local pack `recipe.cpu_money_downs` is `modern2`. Its disk XBE hashes to
`f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba`.
At VA `0x20B180`, bytes `e9cb0f2d01` jump to `0x014DC150`; the target begins
`9c60e82500000083f801741183f80274`, consistent with the Modern2 entry.
These facts do **not** prove the Deck loaded these bytes or executed the hook.

Modern2 answers ordinary offense, forced field goal, or **retail**. Retail
does not mean punt: it delegates the decision to native FG/punt/go logic.
The baseline go limits at opponent 30/35/40 are 4/6/9 yards, before clock and
score adjustments. A go can also defer to the native Hail Mary decision.

Independent replay of the pinned Python policy, using its exact generated
tables and float32 operations:

| Supplied state | Period length | Result |
| --- | --- | --- |
| Fourth-and-5, opponent 35, tied, Q1 5:00 | 480 seconds | retail |
| Same state | 900 seconds | go |

The source derives clock classes from raw game seconds, including the configured
period length. This establishes sensitivity to short quarters; it does not prove
that time normalization is the desired fix or that this was the user's case.

Other retail paths include non-CPU possession, phase other than scrimmage,
unsupported down/state/direction, distance outside 0–25 yards, invalid clock,
last two minutes of Q2, and overtime states without the expected possession
tracking. Native kicker range and field-goal tests remain relevant after a
retail result.

## Native dispatch review and outstanding proof

`sub_0020B180` begins with `RECOMP_INTERP_GATE(0x0020B180)`. `interp_setup.c`
compares loaded guest bytes against the reconstruction base and marks changed
function entries. The gate uses that bitmap plus `g_interp_active` to dispatch
to the interpreter; the source supports the patched entry in principle.
After the combined broadcast installation on October 17, the normal Steam entry
launched Windows game PID 317534 from the expected live-profile runtime. Its fresh
session reports loaded-image SHA256
`f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba`
(`source_scope=load_image`), the expected SOFTDRINK pack, and an active interpreter
with 1,287 of 31,081 converted functions differing. This confirms the loader's
input identity for this launch, not a readback of every guest byte. The specific
fourth-down entry bytes, dirty bit, actual caller and return category remain
unobserved. `NFL2K5_HIDE_SKIP` is absent from this process environment.

Next acceptance: identify the active pack and loaded image; capture entry bytes,
dirty-bit/gate status and hook entry/return at one CPU fourth-down decision;
record possession, field direction, distance, score, period and clocks; then
compare with the pinned policy and retail FG/punt continuation. Keep diagnostic
reads bounded and do not change presets to mask an unverified dispatch problem.

Private source files and machine-readable disk/source receipt are under
`.local-runtime/broadcast-networks-v1/fourth-down-audit/`. No live execution
claim is implied by those receipts.
