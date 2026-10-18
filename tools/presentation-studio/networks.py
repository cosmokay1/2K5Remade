"""Deterministic broadcast windows for the observed Xbox franchise schedule.

Schedule record mapping: cruuz/2k-football-mod-tools,
mod_editor/core/nfl2k5_franchise_save.py (Game), tools/nfl2k5_franchise_schedule.py.
This is an editable simulation coverage policy, not a claim of licensed TV rights.
"""
import datetime
import json
import struct

TEAMS = ('49ers','Bears','Bengals','Bills','Broncos','Browns','Buccaneers','Cardinals',
         'Chargers','Chiefs','Colts','Cowboys','Dolphins','Eagles','Falcons','Giants',
         'Jaguars','Jets','Lions','Packers','Panthers','Patriots','Raiders','Rams',
         'Ravens','Commanders','Saints','Seahawks','Steelers','Texans','Titans','Vikings')
AFC = {2,3,4,5,8,9,10,12,16,17,21,22,24,28,29,30}
NETWORKS = ('CBS', 'FOX', 'NBC', 'ESPN', 'Prime', 'NFL Network')


def assignment(raw, postseason=False, preseason=False):
    _, home, away, month, day, year, hour, minute = raw
    date = datetime.date(2000 + year, month, day)
    if home >= 32 or away >= 32 or home == away or hour > 12 or minute > 59:
        raise ValueError('Invalid schedule record')
    weekday = date.weekday()
    if preseason:
        return ('CBS', 'Preseason regional coverage (AFC home team)') if home in AFC else ('FOX', 'Preseason regional coverage (NFC home team)')
    evening = 7 <= hour <= 11 and not (hour == 9 and minute == 30)
    if weekday == 0:
        return 'ESPN', 'Monday night window'
    if weekday == 6 and evening:
        return 'NBC', 'Sunday night window'
    if weekday == 3:
        if month == 11 and 22 <= day <= 28:
            if evening:
                return 'NBC', 'Thanksgiving night window'
            return ('CBS', 'Thanksgiving early window') if hour in (0, 12, 1, 2) else ('FOX', 'Thanksgiving late window')
        return ('NBC', 'Opening Thursday night window') if month == 9 and day <= 10 else ('Prime', 'Thursday night window')
    if weekday == 5 and not postseason:
        return 'NFL Network', 'Saturday regular-season window'
    if weekday == 6 and hour == 9 and minute == 30:
        return 'NFL Network', 'Sunday morning window (9:30 schedule convention)'
    return ('CBS', 'AFC visiting-team coverage') if away in AFC else ('FOX', 'NFC visiting-team coverage')


def schedule_token(grid, season, weeks):
    # Same bounded FNV-1a identity as broadcast_schedule.h; ignores played status
    # and scores, which change during the season. Never used for authentication.
    value = 14695981039346656037
    for byte in bytes((season, weeks)) + b''.join(grid[i+1:i+8] for i in range(0, weeks*17*8, 8)):
        value = ((value ^ byte) * 1099511628211) & ((1 << 64)-1)
    return f'{value:016x}'


def read_schedule(payload):
    if len(payload) != 720044 or payload[0x2E0:0x2E4] != b'ROST' or payload[0x30C:0x310] != b'ROST':
        raise ValueError('Unsupported Xbox franchise save')
    size = struct.unpack_from('<I', payload, 0x2E4)[0] + 0x20
    start = 0x2E0 + size + (size & 1)
    if start + 0x83DC + 0x165B0 != len(payload) or payload[start] != 2 or payload[start+3] != 32:
        raise ValueError('Unsupported franchise scheduler')
    count = struct.unpack_from('<I', payload, 0x348)[0]
    if count not in (256, 272):
        raise ValueError('Unsupported season length')
    weeks = 18 if count == 272 else 17
    season = payload[start+6]
    phase = payload[start+1]
    if phase not in (7, 8, 9):
        raise ValueError('No active preseason, regular season or postseason schedule')
    grid = payload[start+0x4CA:start+0x4CA+22*17*8]
    token = schedule_token(grid, season, 5 if phase == 7 else weeks)
    games = []
    for cell in range((5 if phase == 7 else 22)*17):
        raw = grid[cell*8:cell*8+8]
        if raw[0] not in (0, 3) or not any(raw[1:5]):
            continue
        # Future postseason placeholders and the Pro Bowl have no valid matchup.
        try:
            network, reason = assignment(raw, phase != 7 and cell//17 >= weeks, phase == 7)
        except ValueError:
            continue
        game = dict(key=f'{token}:{cell}:{raw[1:].hex()}', week=cell//17+1,
                    home=TEAMS[raw[1]], away=TEAMS[raw[2]],
                    date=datetime.date(2000+raw[5],raw[3],raw[4]).isoformat(),
                    kickoff=f'{raw[6] or 12}:{raw[7]:02d}',
                    network=network, reason=reason, played=raw[0] == 3,
                    postseason=phase != 7 and cell//17 >= weeks, preseason=phase == 7)
        games.append(game)
    if not games:
        raise ValueError('No supported scheduled games')
    return dict(token=token, games=games, season_index=season, phase=phase)


def load_settings(path):
    if not path.exists():
        return dict(version=1, enabled=True, overrides={}, packages={})
    result = json.loads(path.read_text())
    if (not isinstance(result, dict) or result.get('version') != 1 or
            type(result.get('enabled')) is not bool or
            not isinstance(result.get('overrides'), dict) or not isinstance(result.get('packages'), dict)):
        raise ValueError('Invalid broadcast settings')
    return result


def save_settings(path, settings):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(settings, indent=2) + '\n')
    temp.replace(path)
