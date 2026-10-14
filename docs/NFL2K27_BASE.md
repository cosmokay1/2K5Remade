> Superseded target: the user now prefers SOFTDRINK on Remade if compatible.
> This PS2 migration research is retained as reference. See SOFTDRINK_AI_BASE.md.

# NFL 2K27 franchise AI base migration

On October14,2026, the user explicitly chose NFL 2K27 as the game base rather
than importing its content into the native Xbox Remade build. Windows and Steam
Deck delivery, personality/performance negotiation, modern supported cap/rookie
rules, durable stories/contracts, promises, draft logic and remote shutdown remain
the intended outcome. Changing the base does not make those integrations complete.

## Verified public evidence

The [official release page](https://www.nfl2kmod.com/nfl-2k) advertises NFL 2K27,
released June29,2026, modern rosters/visuals, a17-game season and Steam Deck setup.
These are release claims, not our execution evidence. The [official FAQ](https://www.nfl2kmod.com/)
describes a PCSX2-based mod. The [Xbox Series setup](https://www.nfl2kmod.com/xbox)
requires a PS2 ISO and BIOS; Xbox Series support does not mean the original Xbox
executable used by Remade. The [roster tools page](https://www.nfl2kmod.com/roster-tools)
identifies PS2 memory cards and MAX/PSU save transfer tools.

The official download links to a MediaFire Base_Mod folder. Its browser-text
response does not expose a reliable file listing; an apparently empty template
is not evidence that the distribution is unavailable. No mod/game/BIOS was
downloaded in this investigation, and no permission or endorsement was inferred.

[PCSX2's own PINE implementation](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/PINE.cpp)
exposes emulator/disc metadata, memory access and savestate operations. This is
an option for inspection. It does not identify NFL 2K27 player/contract fields or
provide our atomic negotiation/guest-commit protocol. The project's
[memory-race issue](https://github.com/PCSX2/pcsx2/issues/14589) also cautions against
assuming arbitrary live writes are a safe integration mechanism. Pin the actual
emulator/mod and establish the game boundary before writes or hook claims.

## Reuse and replacement

Retain the Python accounting, rookie/minimum rules, personality initialization,
relationship/story/promise persistence, proposal logic, performance evidence
validation, provider budgets and killswitch. Preserve their tests and provenance.
Revalidate their inputs against the new save/calendar/money scale; old registry
values and historical salary classifications do not transfer automatically.

The Xbox x86 addresses, native presentation hook, original-fxg live adapter and
pinned AIBASELIN/AIGILDON identities are reference-only. Do not claim their
encodings or finance checks work with PS2. Actual PS2 mapping may prove some
shared structure, but only inspected bytes and controlled saves can establish it.
Do not use the old native package as a substitute for the selected mod.

Keep the repository's BeyondTomrrow/2K5Remade attribution intact. Credit NFL 2K27's
mod team separately and inspect distribution terms before publishing combined
assets or binaries. No maintainer message, binary release or unofficial claim of
an endorsed fork is authorized by this migration.

## Inputs and next execution

The user's mod/PS2 ISO/BIOS availability and installation are currently awaiting
clarification. Existing verified assets are Xbox inputs. Deck SSH became
unreachable while sealing the superseded native candidate; do not assume it is
available or stop a running session. Preserve the old game, saves, clones and
staged files. The native staged service preflight passed with32 unchanged teams
and0 model attempts, but its final seal failed on SSH timeout and it was not
installed. It is no longer a deployment target.

Next: inspect the selected mod's real installation/package, establish its pinned
PCSX2/mod identity and start a separately backed-up PS2 franchise. Verify a vanilla
signing/save/reload pair before the adapter commits any terms. Reconcile effective
season length/year, player IDs, salaries, cap and rookie obligations from that
base. The existing legacy exemptions and2004 money-scale choice were tied to the
old roster; obtain a concrete new policy from observed NFL 2K27 data instead of
silently transplanting it.
