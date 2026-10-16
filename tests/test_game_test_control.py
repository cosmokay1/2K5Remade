"""Driver safeguards: stale evidence and pending input cannot look like success."""
from pathlib import Path
import tempfile
import subprocess
import os
from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.game_test_control import capture, control_lock, keyboard_press, publish_press, running_game, wait_log


class GameTestControlTests(unittest.TestCase):
    def test_queue_is_complete_and_cannot_replace_pending_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'press.txt'
            publish_press(path, ['down', 'a', 'lt'])
            self.assertEqual(path.read_text(), 'down a lt\n')
            with self.assertRaisesRegex(RuntimeError, 'already pending'):
                publish_press(path, ['b'])
            self.assertEqual(path.read_text(), 'down a lt\n')
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ['press.txt'])

    def test_bad_or_oversized_batches_do_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'press.txt'
            for buttons in ([], ['a'] * 17, ['down a'], ['a\nb'], ['unknown']):
                with self.assertRaises(ValueError):
                    publish_press(path, buttons)
            self.assertFalse(path.exists())

    def test_process_discovery_ignores_launchers_and_other_runtimes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pid, executable, runtime in [('1', 'steam.exe', '/game'),
                                              ('2', r'Z:\game\NFL2K5.exe', '/game'),
                                              ('3', 'NFL2K5.exe', '/other')]:
                process = root / pid
                process.mkdir()
                (process / 'cmdline').write_bytes(executable.encode() + b'\0--run\0')
                (process / 'environ').write_bytes(('NFL2K5_ROOT=Z:' + runtime + '\0DISPLAY=:1\0').encode())
            unconfigured = root / '4'
            unconfigured.mkdir()
            (unconfigured / 'cmdline').write_bytes(b'NFL2K5.exe\0--run\0')
            (unconfigured / 'environ').write_bytes(b'DISPLAY=:1\0')
            with self.assertRaisesRegex(RuntimeError, 'found 0'):
                running_game(Path.cwd(), root)
            self.assertEqual(running_game(Path('/game'), root)[0], 2)
            with self.assertRaisesRegex(RuntimeError, 'found 0'):
                running_game(Path('/missing'), root)
            (root / '3' / 'environ').write_bytes(b'NFL2K5_ROOT=Z:/game\0')
            with self.assertRaisesRegex(RuntimeError, 'found 2'):
                running_game(Path('/game'), root)

    @patch('tools.game_test_control.running_game', return_value=(12, {}))
    def test_log_wait_does_not_accept_old_success(self, _):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.log'
            path.write_bytes(b'old context received\n')
            with self.assertRaises(TimeoutError):
                wait_log(Path('/game'), path, 'context received', path.stat().st_size, .001)
            result = wait_log(Path('/game'), path, 'context received', 0, .1)
            self.assertTrue(result['matched'])
            with self.assertRaisesRegex(ValueError, 'offset'):
                wait_log(Path('/game'), path, 'received', 1000, .1)

    @patch('tools.game_test_control.running_game', return_value=(12, {}))
    def test_log_truncation_is_a_failure(self, _):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.log'
            path.write_bytes(b'prefix content')
            with patch('tools.game_test_control.time.sleep', side_effect=lambda _: path.write_bytes(b'')):
                with self.assertRaisesRegex(RuntimeError, 'truncated'):
                    wait_log(Path('/game'), path, 'never', 0, .1)

    def test_log_wait_rejects_process_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.log'
            path.write_bytes(b'context received')
            with patch('tools.game_test_control.running_game', side_effect=[(12, {}), (13, {})]):
                with self.assertRaisesRegex(RuntimeError, 'Game changed'):
                    wait_log(Path('/game'), path, 'received', 0, .1)

    @patch('tools.game_test_control.running_game', return_value=(12, {}))
    @patch('tools.game_test_control.subprocess.run')
    def test_capture_refuses_old_evidence_without_requesting_another_image(self, run, _):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'existing.png'
            output.write_bytes(b'existing screenshot')
            with self.assertRaises(ValueError):
                capture(Path('/game'), output)
            run.assert_not_called()
            self.assertEqual(output.read_bytes(), b'existing screenshot')

    @patch('tools.game_test_control.time.sleep')
    @patch('tools.game_test_control.running_game', return_value=(12, {'DISPLAY': ':1'}))
    def test_keyboard_releases_key_when_injection_fails(self, _, sleep):
        commands = []
        def run(args, **kwargs):
            commands.append(args[1:])
            if args[1] == 'keydown':
                raise subprocess.CalledProcessError(1, args)
            return SimpleNamespace(stdout='99')
        with tempfile.TemporaryDirectory() as directory:
            with patch('tools.game_test_control.subprocess.run', side_effect=run), patch(
                    'tools.game_test_control.control_lock', return_value=nullcontext()):
                with self.assertRaises(subprocess.CalledProcessError):
                    keyboard_press(Path(directory), ['a'])
        self.assertEqual(commands[-2:], [['keydown', 'z'], ['keyup', 'z']])

    @unittest.skipUnless(os.name == 'posix', 'Input driver lock is Linux-only')
    def test_two_drivers_cannot_interleave_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.lock'
            with control_lock(path):
                with self.assertRaisesRegex(RuntimeError, 'Another test driver'):
                    with control_lock(path):
                        self.fail('Second driver acquired the active queue')
            with control_lock(path):
                pass  # Closing the first session releases ownership.


if __name__ == '__main__':
    unittest.main()
