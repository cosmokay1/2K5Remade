"""Save reads retain mutation checks across Windows stat/fstat time semantics."""
from io import BytesIO
from types import SimpleNamespace
import stat
import unittest
from unittest.mock import Mock, patch

from franchise.sidecar import read_guest_save


class GuestSaveReaderTests(unittest.TestCase):
    def read(self, *, path_after=10, descriptor_after=20, **changed):
        def metadata(ctime, **overrides):
            fields=dict(st_mode=stat.S_IFREG,st_dev=1,st_ino=2,st_size=6,
                        st_mtime_ns=30,st_ctime_ns=ctime)
            fields.update(overrides)
            return SimpleNamespace(**fields)
        path=Mock()
        path.stat.side_effect=[metadata(10),metadata(path_after)]
        source=BytesIO(b'second')
        path.open.return_value.__enter__=Mock(return_value=source)
        path.open.return_value.__exit__=Mock(return_value=False)
        source.fileno=Mock(return_value=7)
        with patch('franchise.sidecar.os.fstat',side_effect=[metadata(20),metadata(descriptor_after,**changed)]):
            return read_guest_save(path)

    def test_stable_path_and_descriptor_ctimes_need_not_match(self):
        self.assertEqual(self.read(),b'second')

    def test_path_ctime_change_rejects_read(self):
        with self.assertRaisesRegex(ValueError,'changed during read'):
            self.read(path_after=11)

    def test_descriptor_ctime_change_rejects_read(self):
        with self.assertRaisesRegex(ValueError,'changed during read'):
            self.read(descriptor_after=21)

    def test_descriptor_identity_size_and_mtime_changes_reject_read(self):
        for field in ('st_dev','st_ino','st_size','st_mtime_ns'):
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'changed during read'):
                self.read(**{field:99})
