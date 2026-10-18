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

FIELDS = {'passing_yards': 0x1AA, 'rushing_yards': 0x1AC,
          'total_yards': 0x1D2, 'turnovers': 0x1D4}


def summarize(teams):
    games = sum(team['games_recorded'] for team in teams)
    totals = {name: sum(team['totals'][name] for team in teams) for name in FIELDS}
    return {'team_games': games, 'totals': totals,
            'per_team_game': {name: value / games if games else None
                              for name, value in totals.items()},
            'teams_with_games': sum(team['games_recorded'] > 0 for team in teams)}


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
    return {'scope': 'source-mapped current team-season totals; in-game corroboration pending',
            'calendar': calendar,
            'settings_minutes': dict(zip(('played', 'simulated'),
                                        struct.unpack_from('<2I', payload, 0x8C))),
            'teams': teams, 'league': summarize(teams),
            'limitations': ['Raw calendar display is retail-based; logical SOFTDRINK year is separate.',
                            'Game-count inclusion of preseason/postseason must be checked at checkpoints.',
                            'Play counts, scoring and player distributions need separate evidence.',
                            'A zero-game snapshot cannot establish simulation accuracy.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_totals(args.save.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
