# Startup divide-by-zero evidence

The intermittent startup fault in `sub_003CAD50` remains unresolved. The existing
crash report prints guest register globals, but generated code can hold its
current working values in native registers before updating those globals. The
exact executable's disassembly must be used to interpret a fault address.

For a private Windows/Proton diagnostic run, set
`NFL2K5_CRASH_GUEST_CONTEXT=1` before launching a build containing the capture.
It defaults off. It does not change exception handling, divide by a substitute
value, enable AI or grant signing authority.

Only an integer-divide-by-zero exception produces the extra capture. The log
includes native integer registers and fixed96-byte windows around eligible low
guest-RAM candidates, plus the guest stack. Registers may contain ordinary
integers rather than pointers; the output does not assign object meanings to
them. Reads use `ReadProcessMemory` against the current process, reject candidates
outside the configured primary guest RAM, and report unreadable windows without
directly dereferencing them. No window extends beyond that RAM bound. Execution
still follows the existing fatal-exception path.

Interpret the captured native instruction and register values together with
the matching generated routine. A zero divisor identifies the failed condition,
not why initialization produced it. The capture does not freeze other threads
or establish an atomic snapshot of a mutable object.

The asset-free Windows `game_crash_context` CTest checks expected zero-divisor
words, native register values, high-address rejection, unreadable pages and
unchanged memory. Run it through the existing native bridge CTest build.
Actual fault capture and a verified initialization repair remain open; passing
the fixture or booting once does not close either requirement.
