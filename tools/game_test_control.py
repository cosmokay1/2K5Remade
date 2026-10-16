"""Linux/Proton test driver for the existing NFL2K5_PRESS_FILE input hook.

Run locally on the Deck (including over SSH). No server or game-memory writes.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

BUTTONS = frozenset('a b x y start back up down left right black white lb rb lt rt l3 r3'.split())


def unix_path(value):
    value = value.replace('\\', '/')
    return value[2:] if value[:2].lower() == 'z:' else value


def running_game(runtime, proc=Path('/proc')):
    """Identify the actual title process, not Steam's launcher or this command."""
    matches = []
    for item in proc.iterdir():
        if not item.name.isdecimal():
            continue
        try:
            args = (item / 'cmdline').read_bytes().split(b'\0')
            executable = unix_path(os.fsdecode(args[0]))
            if Path(executable).name.lower() != 'nfl2k5.exe':
                continue
            environment = dict(os.fsdecode(entry).split('=', 1)
                               for entry in (item / 'environ').read_bytes().split(b'\0') if b'=' in entry)
            if environment.get('NFL2K5_ROOT') and Path(unix_path(environment['NFL2K5_ROOT'])).resolve() == runtime.resolve():
                matches.append((int(item.name), environment))
        except (OSError, ValueError):
            continue
    if len(matches) != 1:
        raise RuntimeError(f'Expected one running game for this runtime; found {len(matches)}')
    return matches[0]


@contextmanager
def control_lock(path):
    import fcntl  # Linux runner only; asset-free helpers remain testable elsewhere.
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Another test driver owns the input queue') from error
        yield


def publish_press(path, buttons):
    """Publish a complete queue atomically, refusing to overwrite pending input."""
    if not 1 <= len(buttons) <= 16 or any(button not in BUTTONS for button in buttons):
        raise ValueError('Choose 1–16 supported button names')
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.press-', delete=False) as output:
        temporary = Path(output.name)
        output.write((' '.join(buttons) + '\n').encode('ascii'))
    try:
        os.link(temporary, path)
    except FileExistsError as error:
        raise RuntimeError('Input is already pending; refusing to overwrite it') from error
    finally:
        temporary.unlink()


def press(runtime, buttons):
    pid, environment = running_game(runtime)
    configured = environment.get('NFL2K5_PRESS_FILE')
    if not configured:
        raise RuntimeError('Game was not launched with NFL2K5_PRESS_FILE')
    path = Path(unix_path(configured))
    if not path.is_absolute() or not path.parent.is_dir():
        raise RuntimeError('Configured input queue must have an existing absolute parent')
    with control_lock(runtime / '.game-test-control.lock'):
        publish_press(path, buttons)
        deadline = time.monotonic() + 3
        while path.exists():
            if running_game(runtime)[0] != pid:
                raise RuntimeError('Game changed while input was pending')
            if time.monotonic() >= deadline:
                raise TimeoutError('Game did not consume input; inspect the queue before continuing')
            time.sleep(.05)
        # file_press consumes at most one button per 250ms neutral + 200ms press.
        # This is a settling bound, not evidence that a particular menu was reached.
        deadline = time.monotonic() + .6 * len(buttons) + .3
        while time.monotonic() < deadline:
            if running_game(runtime)[0] != pid:
                raise RuntimeError('Game changed while input was settling')
            time.sleep(.1)
    return dict(pid=pid, buttons=buttons, queue_consumed=True, screen_verified=False)


def wait_log(runtime, path, pattern, offset, timeout):
    if not pattern or len(pattern) > 512 or offset < 0 or not 0 < timeout <= 60:
        raise ValueError('Require a nonempty bounded pattern, nonnegative offset and timeout up to 60s')
    pid = running_game(runtime)[0]
    deadline = time.monotonic() + timeout
    with path.open('rb') as source:
        identity = os.fstat(source.fileno())
        if offset > identity.st_size:
            raise ValueError('Log offset exceeds the current file')
        source.seek(offset)
        tail = b''
        needle = pattern.encode()
        while True:
            current = path.stat()
            if (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino) or current.st_size < source.tell():
                raise RuntimeError('Log was replaced or truncated; take a fresh checkpoint')
            if running_game(runtime)[0] != pid:
                raise RuntimeError('Game changed while waiting for evidence')
            block = source.read(65536)
            if needle in tail + block:
                return dict(pid=pid, pattern=pattern, offset=offset, matched=True)
            tail = (tail + block)[-(len(needle) - 1):] if len(needle) > 1 else b''
            if time.monotonic() >= deadline:
                raise TimeoutError('Expected new log evidence did not arrive')
            time.sleep(.05)


def capture(runtime, output):
    pid, environment = running_game(runtime)
    if output.suffix.lower() != '.png' or output.exists():
        raise ValueError('Choose a new .png output path')
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if environment.get('XDG_RUNTIME_DIR'):
        env['XDG_RUNTIME_DIR'] = environment['XDG_RUNTIME_DIR']
    subprocess.run(['gamescopectl', 'screenshot', str(output)], env=env, check=True, timeout=5)
    deadline = time.monotonic() + 5
    while True:
        if running_game(runtime)[0] != pid:
            raise RuntimeError('Game changed during capture; image is not accepted as test evidence')
        image = output.read_bytes() if output.exists() else b''
        if image.startswith(b'\x89PNG\r\n\x1a\n') and image.endswith(b'IEND\xaeB`\x82'):
            import struct
            width, height = struct.unpack('>II', image[16:24])
            return dict(pid=pid, path=str(output), width=width, height=height,
                        scope='Gamescope output; inspect image to confirm the game is visible')
        if time.monotonic() >= deadline:
            raise TimeoutError('Compositor did not produce a complete PNG')
        time.sleep(.05)


KEYS = dict(a='z', b='x', x='c', y='v', start='Return', back='BackSpace',
            up='Up', down='Down', left='Left', right='Right', lt='q', rt='e')


def keyboard_press(runtime, buttons):
    if not 1 <= len(buttons) <= 16 or any(button not in KEYS for button in buttons):
        raise ValueError('Choose 1–16 buttons supported by the existing keyboard mapping')
    pid, environment = running_game(runtime)
    if not environment.get('DISPLAY'):
        raise RuntimeError('Game has no keyboard display')
    env = dict(os.environ, DISPLAY=environment['DISPLAY'])
    if environment.get('XAUTHORITY'):
        env['XAUTHORITY'] = environment['XAUTHORITY']
    def command(*args):
        return subprocess.run(['xdotool', *args], env=env, check=True,
                              capture_output=True, text=True, timeout=5).stdout.strip()
    windows = command('search', '--onlyvisible', '--name', '^ESPN NFL 2K5$').splitlines()
    if len(windows) != 1:
        raise RuntimeError('Expected one visible game window on its display')
    with control_lock(runtime / '.game-test-control.lock'):
        window = windows[0]
        command('windowfocus', '--sync', window)
        for button in buttons:
            if running_game(runtime)[0] != pid or command('getwindowfocus') != window:
                raise RuntimeError('Game changed or lost focus; no more keys sent')
            key = KEYS[button]
            try:
                command('keydown', key)
                time.sleep(.2)
            finally:
                command('keyup', key)
            time.sleep(.3)
    return dict(pid=pid, buttons=buttons, keyboard=True, screen_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--log', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    button_parser = commands.add_parser('press')
    button_parser.add_argument('buttons', nargs='+', choices=sorted(BUTTONS))
    button_parser.add_argument('--keyboard', action='store_true', help='Explicit existing keyboard mapping; requires game focus')
    capture_parser = commands.add_parser('capture')
    capture_parser.add_argument('output', type=Path)
    log_parser = commands.add_parser('wait-log')
    log_parser.add_argument('pattern')
    log_parser.add_argument('--offset', type=int, required=True)
    log_parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args()
    try:
        if args.command == 'status':
            pid, env = running_game(args.runtime)
            result = dict(pid=pid, press_file=env.get('NFL2K5_PRESS_FILE'), display=env.get('DISPLAY'),
                          log_bytes=args.log.stat().st_size if args.log else None)
        elif args.command == 'press':
            result = (keyboard_press if args.keyboard else press)(args.runtime, args.buttons)
        elif args.command == 'capture':
            result = capture(args.runtime, args.output)
        else:
            if args.log is None:
                raise ValueError('--log is required for wait-log')
            result = wait_log(args.runtime, args.log, args.pattern, args.offset, args.timeout)
        print(json.dumps(result))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
