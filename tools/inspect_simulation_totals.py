"""Read-only team-season yardage report for the observed Xbox franchise layout.

Reuses this fork's roster/calendar validators. Team stat offsets are documented by
cruuz/2k-football-mod-tools, nfl2k5_franchise_save.py at e19384123c23a3601949dda67c9a3ab754d65fd6
(TEAM_STAT_FIELDS, TEAM_STAT_NAMES, TEAM_GAMES_PLAYED). These are source mappings;
corroborate against an in-game completed-season table before recommending settings.
No unknown stat IDs are assigned invented football labels.
"""
import argparse
import json
from pathlib import Path
import struct

from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import inspect_save, TEAMS

# 0x1D2 was labelled total_yards by the reference. Actual season evidence
# disproves that label (Giants427 vs3562passing+2161rushing). Leave it unnamed.
FIELDS = {'passing_yards': 0x1AA, 'rushing_yards': 0x1AC, 'turnovers': 0x1D4}


def summarize(teams):
    games = sum(team['games_recorded'] for team in teams)
    totals = {name: sum(team['totals'][name] for team in teams) for name in FIELDS}
    totals['passing_plus_rushing_yards'] = totals['passing_yards'] + totals['rushing_yards']
    return {'team_games': games, 'totals': totals,
            'per_team_game': {name: value / games if games else None
                              for name, value in totals.items()},
            'teams_with_games': sum(team['games_recorded'] > 0 for team in teams)}



def inspect_schedule_template(payload):
    """Recognize the creator's documented 256/272-game template, not the year."""
    calendar = inspect_calendar(payload)
    count, relative = struct.unpack_from('<Ii', payload, 0x348)
    start = 0x34C + relative - 1
    if count not in (256, 272) or not relative or start < 0x320 or start + count*8 > calendar['scheduler_offset']:
        raise ValueError('Unsupported regular-season schedule template')
    games = dict.fromkeys(TEAMS, 0)
    for index in range(count):
        record = payload[start+index*8:start+(index+1)*8]
        home, away = record[1:3]
        if home >= 32 or away >= 32 or home == away:
            raise ValueError('Invalid regular-season matchup')
        games[TEAMS[home]] += 1
        games[TEAMS[away]] += 1
    expected = count*2//32
    if any(value != expected for value in games.values()):
        raise ValueError('Unbalanced regular-season schedule template')
    return {'scheduled_games': count, 'scheduled_team_games': count*2,
            'games_per_team': games, 'scope': 'schedule template, not completed games'}



def inspect_regular_scores(payload):
    """Sum both score halves; no assumption about their home/away ordering."""
    calendar = inspect_calendar(payload)
    if calendar['phase_01_raw'] not in (8, 9):
        return None  # Preseason/offseason grids are not regular-season evidence.
    template = inspect_schedule_template(payload)
    weeks = 18 if template['scheduled_games'] == 272 else 17
    start = calendar['scheduler_offset']
    played = points = 0
    for index in range(weeks*17):
        record = payload[start+0x4CA+index*8:start+0x4CA+(index+1)*8]
        if record[0] != 3:
            continue
        if record[1] >= 32 or record[2] >= 32 or record[1] == record[2]:
            raise ValueError('Invalid played regular-season matchup')
        played += 1
        scores = payload[start+0x107A+index*10:start+0x107A+(index+1)*10]
        points += sum(scores)
    if played > template['scheduled_games']:
        raise ValueError('Played schedule exceeds the season template')
    return {'completed_games': played, 'team_games': played*2,
            'combined_points': points,
            'points_per_team_game': points/(played*2) if played else None,
            'regular_season_complete': played == template['scheduled_games'],
            'scope': 'regular-season played-grid scores; no home/away assignment'}


def inspect_totals(payload):
    inspect_save(payload)
    calendar = inspect_calendar(payload)
    teams = []
    for index, name in enumerate(TEAMS):
        base = 0x44A8 + index * 0x1F4
        games = struct.unpack_from('<H', payload, base + 0x1DC)[0]
        totals = {field: struct.unpack_from('<H', payload, base + offset)[0]
                  for field, offset in FIELDS.items()}
        teams.append({'team': name, 'games_recorded': games, 'totals': totals})
    league = summarize(teams)
    scores = inspect_regular_scores(payload)
    return {'scope': 'source-mapped current team-season totals; in-game corroboration pending',
            'calendar': calendar,
            'schedule_template': inspect_schedule_template(payload),
            'settings_minutes': dict(zip(('played', 'simulated'),
                                        struct.unpack_from('<2I', payload, 0x8C))),
            'teams': teams, 'league': league, 'regular_season_scores': scores,
            'team_game_counts_match_regular_grid': (league['team_games'] == scores['team_games']
                                                   if scores is not None else None),
            'limitations': ['Raw calendar display is retail-based; logical SOFTDRINK year is separate.',
                            'Game-count inclusion of preseason/postseason must be checked at checkpoints.',
                            'Passing yardage matches gross QB history in the first trial; combined yardage is not NFL net offense.',
                            'Play counts and player distributions need separate evidence.',
                            'A zero-game snapshot cannot establish simulation accuracy.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_totals(args.save.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
