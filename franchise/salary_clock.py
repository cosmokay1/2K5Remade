"""Bind simulation salary periods to a captured, pinned native scheduler.

18 regular-season periods are a simulation rule, not evidence of cash payment.
The descriptor fingerprints identify scheduler semantics, never a mod's name.
"""
import hashlib
import json
from franchise.legacy_amendments import InSeasonAmendmentScope
from tools.inspect_franchise_calendar import inspect_calendar
from tools.franchise_snapshot_bindings import _snapshot_year

DESCRIPTORS = {
    7: ('69c41493c1af9ce5906a001edeae0c3b965b3eb4bfb37ff8d60cdfab8378c124', 4),
    8: ('b2369a42ef0376c5ec1946a6e860feb2843fedc5bbe4fdeba314bcb9f630771c', 18),
    9: ('a622d22d55ed255315a0a6b733b60299edd55e7a49113eb499e7d34b0e65c9d6', 4),
}

def bind_salary_clock(bindings, payload, observation, clock):
    if (type(clock) is not dict or set(clock) != {'source_epoch','descriptor_hex'} or
            type(clock['source_epoch']) is not int or not 0 < clock['source_epoch'] < 2**64):
        raise ValueError('Fresh decoded-source epoch and captured phase descriptor required')
    saved = inspect_calendar(payload)
    calendar = observation['calendar']
    fields = {'season_index','display_year','phase_01_raw','phase_02_raw','step_04_raw','step_05_raw','counter_08_raw'}
    if type(calendar) is not dict or set(calendar) != fields or any(type(v) is not int or v != saved[k] for k,v in calendar.items()):
        raise ValueError('Salary clock differs from the pinned live calendar')
    raw=clock['descriptor_hex']
    if type(raw) is not str or len(raw)!=32 or any(c not in '0123456789abcdef' for c in raw):
        raise ValueError('Canonical captured phase descriptor required')
    phase = calendar['phase_01_raw']
    descriptor = DESCRIPTORS.get(phase)
    # C4E40 stores the phase horizon at step04; C4E60 resets the progress at
    # step05. Only the three inspected descriptors are supported.
    if (descriptor is None or hashlib.sha256(bytes.fromhex(raw)).hexdigest() != descriptor[0] or
            calendar['step_04_raw'] != descriptor[1] or not 0 <= calendar['step_05_raw'] <= descriptor[1]):
        raise ValueError('Unsupported salary phase, horizon or progress')
    elapsed = 0 if phase == 7 else calendar['step_05_raw'] if phase == 8 else 18
    source = dict(format='native-salary-clock-v1',clock=clock,calendar=calendar,
                  payload_sha256=hashlib.sha256(payload).hexdigest())
    digest = hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return InSeasonAmendmentScope(_snapshot_year(bindings,payload),elapsed,18,'native-salary-clock-v1:'+digest)
