"""Inspect one bounded renderer capture; never infer a camera from the screen alone."""
import argparse
import json
import math
from pathlib import Path


def vector(value, count=4):
    if not isinstance(value, list) or len(value) != count or any(
            type(x) not in (float, int) or not math.isfinite(x) for x in value):
        raise ValueError('Finite captured vector required')
    return value


def read_capture(path):
    path = Path(path)
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Capture exceeds diagnostic bound')
    def invalid_constant(value):
        raise ValueError('Nonstandard JSON float: ' + value)
    rows = [json.loads(line, parse_constant=invalid_constant) for line in path.read_text().splitlines()]
    if len(rows) < 2 or rows[0].get('type') != 'header' or rows[0].get('schema') != 1:
        raise ValueError('Renderer capture schema 1 required')
    if rows[-1].get('type') != 'end' or rows[-1].get('truncated') is not False:
        raise ValueError('Complete, untruncated frame required')
    draws = {}
    triangles = 0
    for row in rows[1:-1]:
        if row.get('type') == 'draw':
            key = row['draw']
            if type(key) is not int or key in draws or not 0 < row['width'] <= 4096 or not 0 < row['height'] <= 4096:
                raise ValueError('Invalid/duplicate draw or dimensions')
            if len(row['constants']) != 192:
                raise ValueError('All captured constant rows required')
            draws[key] = {**row, 'samples': []}
        elif row.get('type') == 'triangle':
            if row['draw'] not in draws or len(row['vertices']) != 3:
                raise ValueError('Triangle without its draw')
            for vertex in row['vertices']:
                vector(vertex['input']); vector(vertex['screen']); vector(vertex['uv'])
            draws[row['draw']]['samples'].extend(row['vertices'])
            triangles += 1
        else:
            raise ValueError('Unexpected capture record')
    if len(draws) != rows[-1].get('draws') or triangles != rows[-1].get('triangles'):
        raise ValueError('Capture totals do not match the end record')
    return rows[0], draws, rows[-1]['present_target']


def project(matrix, viewport, value):
    q = [sum(a*b for a, b in zip(row, value)) for row in matrix]
    if abs(q[3]) < 1e-8:
        raise ValueError('Invalid projected W')
    x, y = q[0]/q[3], q[1]/q[3]
    if viewport:
        scale, offset = viewport
        x, y = x*scale[0]+offset[0], y*scale[1]+offset[1]
    return x, y, q[3]


def matches(matrix, viewport, samples):
    if not samples:
        return False
    try:
        for sample in samples:
            x, y, w = project(matrix, viewport, sample['input'])
            target = sample['screen']
            if abs(x-target[0]) > .15 or abs(y-target[1]) > .15 or abs(w-target[3]) > .001*max(1, abs(target[3])):
                return False
        return True
    except ValueError:
        return False


def camera_candidates(draw, draws, plane_axis, plane_height):
    constants = draw['constants']
    for start in range(189):
        try:
            matrix = [vector(row) for row in constants[start:start+4]]
            viewport = [vector(constants[58]), vector(constants[59])]
        except ValueError:
            continue
        for mode, view in [('screen_matrix', None), ('viewport_58_59', viewport)]:
            if not matches(matrix, view, draw['samples']):
                continue
            off_plane = []
            for other in draws.values():
                if other['program'] != draw['program'] or other['target'] != draw['target'] or not other['depth_test']:
                    continue
                if other['constants'][start:start+4] != matrix:
                    continue
                if view and [other['constants'][58], other['constants'][59]] != view:
                    continue
                samples = [s for s in other['samples'] if abs(s['input'][plane_axis]-plane_height) > 1e-3]
                if matches(matrix, view, samples):
                    off_plane.extend(samples)
            yield {'constant_start': start, 'mode': mode, 'matrix': matrix, 'viewport': view,
                   'off_plane_validation_vertices': len(off_plane),
                   'verified_for_box': len(off_plane) >= 3}


def analyze(path):
    header, draws, target = read_capture(path)
    candidates = []
    for draw in draws.values():
        samples = draw['samples']
        if draw['target'] != target or not draw['depth_test'] or not draw['texture'] or len(samples) < 6:
            continue
        if any(abs(s['screen'][3]) < 1e-8 or abs(s['input'][3]-1) > 1e-6 for s in samples):
            continue
        lower = [min(s['input'][axis] for s in samples) for axis in range(3)]
        upper = [max(s['input'][axis] for s in samples) for axis in range(3)]
        extent = [b-a for a, b in zip(lower, upper)]
        axis = min(range(3), key=extent.__getitem__)
        if extent[axis] > 1e-5*max(1, max(extent)) or any(extent[i] < 1e-6 for i in range(3) if i != axis):
            continue
        area = 0
        for i in range(0, len(samples), 3):
            a, b, c = [s['screen'] for s in samples[i:i+3]]
            area += abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
        if area < draw['width']*draw['height']*.02:
            continue
        candidates.append({'draw': draw['draw'], 'texture': draw['texture'], 'program': draw['program'],
                           'depth_write': draw['depth_write'], 'plane_axis': 'XYZ'[axis], 'plane_height_raw': lower[axis],
                           'bounds_raw': [lower, upper], 'sampled_screen_area': area,
                           'cameras': list(camera_candidates(draw, draws, axis, lower[axis]))})
    return {'frame': header['frame'], 'present_target': target,
            'scope': 'Candidate planar draws only; visual identification of the field is required. Raw game units.',
            'candidates': sorted(candidates, key=lambda row: row['sampled_screen_area'], reverse=True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.capture), indent=2))


if __name__ == '__main__':
    main()
