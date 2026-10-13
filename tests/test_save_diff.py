import unittest
from tools.save_diff import compare


class SaveDiffTests(unittest.TestCase):
    def test_separate_changes_and_final_byte(self):
        report = compare(b"abcdef", b"AbXYeF")
        self.assertEqual(report["changed_bytes"], 4)
        self.assertEqual(
            [(span["offset"], span["length"]) for span in report["spans"]],
            [(0, 1), (2, 2), (5, 1)],
        )
        self.assertEqual(report["spans"][1]["before_hex"], "6364")
        self.assertEqual(report["spans"][1]["after_hex"], "5859")

    def test_identical(self):
        report = compare(b"same", b"same")
        self.assertEqual(report["spans"], [])
        self.assertEqual(report["before_sha256"], report["after_sha256"])

    def test_invalid_inputs(self):
        for before, after in [(b"", b""), (b"a", b"ab"),
                              (b"PK\x03\x04", b"1234")]:
            with self.subTest(before=before, after=after):
                with self.assertRaises(ValueError):
                    compare(before, after)


if __name__ == "__main__":
    unittest.main()
