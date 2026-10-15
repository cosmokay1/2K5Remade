"""Pinned original-save player bindings for later franchise bootstrap.

IDs are issued once in a local franchise namespace. Slots and biography guards
are lookup constraints, not proof of identity across bank rebuilds/year changes.
No ledger, live game state or existing actor history is imported or modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import uuid

from franchise.initialization import initial_actor, validate_seed
from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE
from tools.inspect_franchise_calendar import inspect_calendar
from tools.franchise_game_context import context_fields, raw_context, validate_context

LEGACY_VERSION = 'original-save-bindings-v1'
VERSION = 'original-save-bindings-v2'
SOFTDRINK_PROFILE = 'softdrink-2k28-v0.6-opening'
SOFTDRINK_XBE_SHA256 = 'f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba'


def binding_money_scale(bindings):
    if 'game_context' in bindings:
        return context_fields(bindings['game_context'])['money_scale']
    # Read-only compatibility for already-persisted v1 registries/journals.
    # New creation never derives units or calendar from an executable identity.
    profile = bindings.get('game_profile')
    if profile is None and 'game_profile' not in bindings:
        return 1
    if (type(profile) is not dict or
            profile != {'id': SOFTDRINK_PROFILE, 'xbe_sha256': SOFTDRINK_XBE_SHA256}):
        raise ValueError('Unsupported pinned game profile')
    return 4


def _snapshot_year(bindings, payload):
    if 'game_context' in bindings:
        return validate_context(bindings['game_context'], payload)['season_year']
    calendar = inspect_calendar(payload)
    if binding_money_scale(bindings) == 1:
        return calendar['display_year']
    # Only the verified opening season is supported. Do not infer future pack
    # aging, phase mapping or a calendar migration from a scheduled-game byte.
    from tools.inspect_franchise_cap import inspect_cap
    if calendar['season_index'] != 0 or inspect_cap(payload)['league_cap_dollars'] != 75300000:
        raise ValueError('Verified SOFTDRINK opening calendar and cap required')
    return 2026


def _identity_guard(first_name, last_name, pbp_photo_raw, dob_region_raw):
    material = json.dumps([first_name, last_name, pbp_photo_raw, dob_region_raw],
                          ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(material).hexdigest()


def _members(payload, roster):
    result = {}
    for team, players in [*roster['teams'].items(), ('free_agents', roster['free_agents'])]:
        for player in players:
            slot = player['source_slot']
            record = PLAYER_START + slot * PLAYER_STRIDE
            # Name plus raw PBP/photo and DOB-region bytes. No birthdays or
            # real-world uniqueness are inferred from these packed bytes.
            result[slot] = {**player, 'team': team,
                            'identity_guard_sha256': _identity_guard(
                                player['first_name'], player['last_name'],
                                payload[record+4:record+8].hex(),
                                payload[record+0x19:record+0x1C].hex())}
    return result


def create_bindings(payload: bytes, *, seed=None, game_xbe=None, game_context=None) -> dict:
    roster = inspect_save(payload)
    context = raw_context(payload) if game_context is None else context_fields(game_context)
    if game_xbe is not None:
        if type(game_xbe) is not bytes or not game_xbe:
            raise ValueError('Nonempty executable bytes required for provenance')
        digest = hashlib.sha256(game_xbe).hexdigest()
        if 'source_image_sha256' in context and context['source_image_sha256'] != digest:
            raise ValueError('Executable differs from explicit context provenance')
        context['source_image_sha256'] = digest
    context = validate_context(context, payload)
    if context['season_year'] != roster['year']:
        raise ValueError('Schedule year differs from explicit calendar; verified context/migration required')
    seed = secrets.token_hex(32) if seed is None else seed
    validate_seed(seed)
    return {'game_context': context, 'version': VERSION, 'franchise_id': uuid.uuid4().hex,
            'baseline_payload_sha256': roster['payload_sha256'],
            'baseline_year': roster['year'], 'personality_seed': seed,
            'players': [{'source_slot': slot, 'player_id': uuid.uuid4().hex,
                         'identity_guard_sha256': player['identity_guard_sha256']}
                        for slot, player in sorted(_members(payload, roster).items())]}


def migrate_context(bindings, payload):
    """Return a new registry representation; never reroll IDs or alter a store.

    Old registries remain readable for durable recovery. Publishing/replacing a
    configured registry is separate from this lossless, copy-only conversion.
    """
    resolve_bindings(bindings, payload)
    migrated = json.loads(json.dumps(bindings))
    if bindings['version'] == VERSION:
        return migrated
    context = raw_context(payload)
    context['season_year'] = _snapshot_year(bindings, payload)
    context['money_scale'] = binding_money_scale(bindings)
    if 'game_profile' in bindings:
        context['source_image_sha256'] = bindings['game_profile']['xbe_sha256']
    migrated.pop('game_profile', None)
    migrated.update(version=VERSION, game_context=validate_context(context, payload))
    resolve_bindings(migrated, payload)
    return migrated


def _hex(value, size):
    return type(value) is str and len(value) == size and all(c in '0123456789abcdef' for c in value)


def resolve_bindings(bindings: dict, payload: bytes) -> dict:
    roster = inspect_save(payload)
    fields = {'version', 'franchise_id', 'baseline_payload_sha256',
              'baseline_year', 'personality_seed', 'players'}
    if type(bindings) is not dict or not (
            (bindings.get('version') == VERSION and set(bindings) == fields | {'game_context'}) or
            (bindings.get('version') == LEGACY_VERSION and set(bindings) in (fields, fields | {'game_profile'}))):
        raise ValueError('Complete versioned original-save bindings required')
    if not _hex(bindings['franchise_id'], 32) or not _hex(bindings['baseline_payload_sha256'], 64):
        raise ValueError('Unsupported binding origin')
    validate_seed(bindings['personality_seed'])
    if type(bindings['baseline_year']) is not int or bindings['baseline_year'] != roster['year']:
        raise ValueError('Year change requires verified identity migration; refusing automatic remapping')
    if _snapshot_year(bindings, payload) != bindings['baseline_year']:
        raise ValueError('Saved season changed; verified identity migration required')
    members = _members(payload, roster)
    if type(bindings['players']) is not list or len(bindings['players']) != len(members):
        raise ValueError('Roster membership change requires verified identity migration')
    result, ids = {}, set()
    for binding in bindings['players']:
        if type(binding) is not dict or set(binding) != {'source_slot', 'player_id', 'identity_guard_sha256'}:
            raise ValueError('Malformed player binding')
        slot, player_id = binding['source_slot'], binding['player_id']
        if type(slot) is not int or slot not in members or slot in result or not _hex(player_id, 32) or player_id in ids:
            raise ValueError('Unique supported player binding required')
        if binding['identity_guard_sha256'] != members[slot]['identity_guard_sha256']:
            raise ValueError('Player biography guard changed; refusing slot reuse or automatic remapping')
        ids.add(player_id)
        result[slot] = {**members[slot], 'player_id': player_id}
    return result


def initial_profiles(bindings: dict, payload: bytes) -> dict:
    """Bootstrap previews only; ongoing relationships belong to FranchiseStore."""
    return {player['player_id']: initial_actor(bindings['personality_seed'], player['player_id'])
            for player in resolve_bindings(bindings, payload).values()}


def resolve_signing_candidate(bindings: dict, payload: bytes, observation: dict) -> dict:
    """Match read-only live biography to a pinned snapshot, never authorize writes.

    Active game/franchise selection, calendar and financial revision still need
    independent reconciliation. A matching name or slot alone is insufficient.
    """
    if type(observation) is not dict or set(observation) != {
            'source_slot', 'first_name', 'last_name', 'pbp_photo_raw', 'dob_region_raw'}:
        raise ValueError('Complete signing biography observation required')
    slot = observation['source_slot']
    if type(slot) is not int or type(observation['first_name']) is not str or type(observation['last_name']) is not str:
        raise ValueError('Typed signing identity required')
    if not _hex(observation['pbp_photo_raw'], 8) or not _hex(observation['dob_region_raw'], 6):
        raise ValueError('Complete raw signing biography bytes required')
    members = resolve_bindings(bindings, payload)
    player = members.get(slot)
    guard = _identity_guard(observation['first_name'], observation['last_name'],
                            observation['pbp_photo_raw'], observation['dob_region_raw'])
    if player is None or guard != player['identity_guard_sha256']:
        raise ValueError('Live signing biography does not match pinned player')
    return {'candidate_player_id': player['player_id'], 'source_slot': slot,
            'scope': 'matching pinned biography; active franchise/calendar/financial state unconfirmed'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('bindings', type=Path)
    parser.add_argument('--game-xbe', type=Path, help='Record executable provenance without selecting rules')
    parser.add_argument('--game-context', type=Path, help='Explicit verified calendar, raw cap and money units JSON')
    parser.add_argument('--migrate-context', type=Path, help='Write a new context registry preserving every existing identity')
    parser.add_argument('--create', action='store_true', help='Explicitly create once; never overwrite/reroll')
    args = parser.parse_args(argv)
    try:
        if (args.game_xbe or args.game_context) and not args.create:
            raise ValueError('Executable/context inputs are only supported with explicit creation')
        if args.create and args.migrate_context:
            raise ValueError('Creation and context migration are separate operations')
        payload = args.save.read_bytes()
        if args.create:
            bindings = create_bindings(payload, game_xbe=args.game_xbe.read_bytes() if args.game_xbe else None,
                game_context=json.loads(args.game_context.read_text(encoding='utf-8')) if args.game_context else None)
            with args.bindings.open('x', encoding='utf-8') as writer:
                json.dump(bindings, writer, indent=2)
                writer.write('\n')
        else:
            bindings = json.loads(args.bindings.read_text(encoding='utf-8'))
        players = resolve_bindings(bindings, payload)
        if args.migrate_context:
            converted = migrate_context(bindings, payload)
            with args.migrate_context.open('x', encoding='utf-8') as writer:
                json.dump(converted, writer, indent=2); writer.write('\n')
    except (ValueError, OSError) as exc:
        parser.exit(2, f'franchise_snapshot_bindings: {exc}\n')
    print(json.dumps({'franchise_id': bindings['franchise_id'], 'matched_members': len(players),
                      'scope': 'pinned same-year bindings; no game/ledger import or rebuild verification'}, indent=2))


if __name__ == '__main__':
    main()
