# Game test control

`tools/game_test_control.py` runs on Linux, including a Steam Deck over SSH, to
exercise the real Windows game under Proton. It supports Remade's existing
`NFL2K5_PRESS_FILE` input hook and an explicit `--keyboard` backend using the
existing game keyboard mappings from `src/nfl2k5_input_hle.c`. No new native input
system, network server, game-memory writer or launcher is needed. Existing
upstream hooks remain attributed to their original source.

For a private test session, create a private directory and export an absolute
Windows-visible queue path in the existing Steam launch script **before starting
the game**, for example:

```sh
export NFL2K5_PRESS_FILE="Z:/home/deck/test-control/press.txt"
```

Use a dedicated empty queue. Leave normal controller settings alone; do not use
the physical controller concurrently with automated steps. Remove the export
and restart normally to disable test input. The tool does not edit launch scripts
or enable itself. It neither enables AI nor changes signing authorization.

Run with the selected runtime directory and current session log:

```sh
python3 tools/game_test_control.py --runtime /path/to/runtime --log /path/to/session.log status
python3 tools/game_test_control.py --runtime /path/to/runtime press down a
# Already running without a queue? Use its existing keyboard mapping explicitly.
python3 tools/game_test_control.py --runtime /path/to/runtime press --keyboard up
python3 tools/game_test_control.py --runtime /path/to/runtime capture /path/to/new-screen.png
python3 tools/game_test_control.py --runtime /path/to/runtime --log /path/to/session.log \
  wait-log 'Read-only signing context reply:' --offset 12345 --timeout 15
```

Take the log offset from `status` **before** the action being tested. A matching
line before that offset is not new evidence. Check full context identity and
error fields, not just the presence of a message. Log truncation/replacement,
process restart and timeout fail the command.

`press` accepts up to16 supported button names, including triggers. It publishes
an entire batch atomically, refuses pending input and serializes cooperating
drivers. Each button uses the existing game's neutral/press/release timing. The
tool waits for queue consumption and settling, but this is **not** an assertion
that the intended menu was reached. Inspect screenshots or new state evidence
between small batches. Do not blindly replay a long navigation sequence against
unknown menu state. Button injection can make real game choices: test signing,
season advancement and saving on disposable copied franchises with explicit
preconditions and before/after evidence.

`--keyboard` requires one visible ESPN NFL 2K5 window on the target process's
X11 display, focuses it, checks focus before each press and releases every key
in a finally block. It supports the game's existing face buttons, D-pad, start,
back and trigger key mappings; bumpers/stick clicks require the file hook.
Both backends use the same file lock to prevent cooperating drivers from interleaving input.

`capture` uses the existing `gamescopectl screenshot` command, checks that a
complete new PNG arrives and that the game process remains the same. Ordinary
X11 root capture returned black on the tested Deck, so it is not a fallback.
Captures include the compositor output: inspect them to confirm the game is
visible. There is no continuous capture overhead and existing images are never
overwritten. Gamescope capture and keyboard input require their installed CLI
utilities; headless rendering and other desktop compositors are not implemented.
See [Gamescope](https://github.com/ValveSoftware/gamescope) for upstream credits.

This first version handles menu buttons, screenshots and log checkpoints. It
does not synthesize analog-stick trajectories, identify players by OCR, provide
an automatic franchise save/reload test, or claim full unattended game coverage.
Keep scenario-specific assertions outside the generic driver. Asset-free
regressions live in `tests/test_game_test_control.py`.
