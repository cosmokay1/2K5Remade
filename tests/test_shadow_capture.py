import json
import tempfile
import unittest
from pathlib import Path
from tools.analyze_shadow_capture import analyze, project


class ShadowCaptureTests(unittest.TestCase):
    def fixture(self):
        constants = [[0, 0, 0, 0] for _ in range(192)]
        constants[:4] = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 4], [0, 0, 1, 10]]
        constants[58], constants[59] = [320, -240, 1, 0], [320, 240, 0, 0]
        rows = [{'type': 'header', 'schema': 1, 'frame': 42}]
        points = [[-2, -2, 0, 1], [2, -2, 0, 1], [2, 2, 0, 1], [-2, 2, 0, 1]]
        for draw in (1, 2):
            rows.append(dict(type='draw', draw=draw, target=1234, texture=55, program=12,
                             width=640, height=480, depth_test=1, depth_write=1, constants=constants))
            for indices in ((0, 1, 2), (0, 2, 3)):
                vertices = []
                for index in indices:
                    point = list(points[index]); point[2] = draw-1
                    x, y, w = project(constants[:4], [constants[58], constants[59]], point)
                    vertices.append({'input': point, 'screen': [x, y, .4, w], 'uv': [0, 0, 0, 1]})
                rows.append(dict(type='triangle', draw=draw, vertices=vertices))
        rows.append(dict(type='end', draws=2, triangles=4, truncated=False, present_target=1234))
        return rows

    def run_capture(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'frame.jsonl'
            path.write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
            return analyze(path)

    def test_real_capture_structure_and_independent_off_plane_validation(self):
        result = self.run_capture(self.fixture())
        self.assertEqual(result['frame'], 42)
        first = result['candidates'][0]
        self.assertEqual(first['plane_axis'], 'Z')
        camera = next(c for c in first['cameras'] if c['constant_start'] == 0)
        self.assertEqual(camera['mode'], 'viewport_58_59')
        self.assertTrue(camera['verified_for_box'])
        self.assertEqual(camera['off_plane_validation_vertices'], 6)

    def test_ground_without_depth_writes_is_still_a_candidate(self):
        rows=self.fixture()
        for row in rows:
            if row['type']=='draw':row['depth_write']=0
        result=self.run_capture(rows)
        self.assertTrue(result['candidates'])
        self.assertEqual(result['candidates'][0]['depth_write'],0)

    def test_planar_fit_alone_does_not_authorize_a_box(self):
        rows = self.fixture()[:4]
        rows.append(dict(type='end', draws=1, triangles=2, truncated=False, present_target=1234))
        cameras = self.run_capture(rows)['candidates'][0]['cameras']
        self.assertTrue(cameras)
        self.assertFalse(any(c['verified_for_box'] for c in cameras))

    def test_incomplete_truncated_and_inconsistent_counts_reject(self):
        for mode in ('missing_end', 'truncated', 'wrong_count'):
            with self.subTest(mode=mode):
                rows = self.fixture()
                if mode == 'missing_end': rows.pop()
                if mode == 'truncated': rows[-1]['truncated'] = True
                if mode == 'wrong_count': rows[-1]['triangles'] = 3
                with self.assertRaises(ValueError): self.run_capture(rows)

    def test_nonfinite_and_duplicate_draw_reject(self):
        rows = self.fixture(); rows[2]['vertices'][0]['screen'][0] = float('nan')
        with self.assertRaises(ValueError): self.run_capture(rows)
        rows = self.fixture(); rows.insert(2, dict(rows[1]))
        with self.assertRaises(ValueError): self.run_capture(rows)

    def test_wrong_target_and_nonworld_draws_not_selected(self):
        rows = self.fixture(); rows[-1]['present_target'] = 999
        self.assertEqual(self.run_capture(rows)['candidates'], [])
        rows = self.fixture()
        for row in rows:
            if row['type'] == 'draw': row['depth_test'] = 0
        self.assertEqual(self.run_capture(rows)['candidates'], [])

    def test_changed_projection_fails_camera_match(self):
        rows = self.fixture(); rows[2]['vertices'][0]['screen'][0] += 5
        first = next(c for c in self.run_capture(rows)['candidates'] if c['draw'] == 1)
        self.assertEqual(first['cameras'], [])


if __name__ == '__main__':
    unittest.main()
