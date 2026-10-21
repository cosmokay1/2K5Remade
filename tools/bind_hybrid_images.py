"""Bind club portraits to verified native records or approved official assets.

This prepares a byte-constrained preview. It neither imports the corrupt source
free-agent pool nor authorizes signing or declares title-level compatibility.
"""
from hashlib import sha256
import struct

from tools.inspect_roster_save import inspect_roster


def bind_club_images(native, source, identities, official_receipt, cache):
    native_count = inspect_roster(native)['player_record_count']
    source_roster = inspect_roster(source)
    source_count = source_roster['player_record_count']
    club_slots = {p['source_slot'] for players in source_roster['teams'].values() for p in players}
    if (sha256(native).hexdigest() != identities['native_sha256']
            or sha256(source).hexdigest() != identities['source_sha256']
            or identities.get('source_free_agents_included') is not False):
        raise ValueError('Pinned roster pair and explicit exclusion of source free agents required')
    bindings, missing, seen_slots, seen_ids = [], [], set(), set()
    official = {}
    for row in official_receipt['bindings']:
        if row['gsis_id'] in official:
            raise ValueError('Duplicate official identity')
        official[row['gsis_id']] = row
    textures = {row['name']:row for row in official_receipt['slots']}
    output = bytearray(source)
    allowed = set()
    for row in identities['matched'] + identities['unresolved_source']:
        unresolved = 'player' in row
        player = row['player'] if unresolved else row
        slot = player['source_slot']
        gsis = row.get('gsis_id')
        if not gsis or slot in seen_slots or gsis in seen_ids:
            raise ValueError('Unique verified club identity and record slot required')
        seen_slots.add(slot);seen_ids.add(gsis)
        if type(slot) is not int or not 0 <= slot < source_count:
            raise ValueError('Invalid source record slot')
        at = 0xAFA8+slot*0x54+6
        if not unresolved:
            if type(row['native_slot']) is not int or not 0 <= row['native_slot'] < native_count:
                raise ValueError('Invalid native record slot')
            native_at = 0xAFA8+row['native_slot']*0x54+6
            photo = struct.unpack_from('<H',native,native_at)[0]
            if photo != row['preserve_native_photo_id']:
                raise ValueError('Native photo binding changed')
            basis = 'softdrink_native'
        elif row['reason'] == 'no_verified_native_image_record' and gsis in official:
            asset = official[gsis];photo = asset['photo_id']
            key = str(photo)
            # Cache names follow the native team-creator dispatch format.
            entry = textures.get(key)
            data = cache.get(key)
            if (asset['source_slot'] != slot or not asset['source_url'].startswith('https://static.www.nfl.com/')
                    or not entry or data is None or len(data) != entry['size']
                    or sha256(data).hexdigest() != entry['sha256']):
                raise ValueError('Missing, stale or unapproved official portrait asset')
            basis = 'official_nfl_asset'
        else:
            missing.append(dict(gsis_id=gsis,source_slot=slot,reason=row['reason']))
            continue
        if type(photo) is not int or not 0 <= photo <= 65535:
            raise ValueError('Native uint16 photo ID required')
        struct.pack_into('<H',output,at,photo)
        allowed.update((at,at+1))
        bindings.append(dict(gsis_id=gsis,source_slot=slot,photo_id=photo,basis=basis))
    if seen_slots != club_slots:
        raise ValueError('Identity report must cover exactly the source club records')
    if any(a!=b and index not in allowed for index,(a,b) in enumerate(zip(source,output))):
        raise ValueError('Unexpected non-portrait edit')
    return bytes(output), dict(bindings=bindings,unresolved=missing,
        all_club_images_bound=not missing,source_free_agent_pool_excluded=True,
        source_sha256=sha256(source).hexdigest(),preview_sha256=sha256(output).hexdigest(),
        ready_for_franchise_test=False,game_dispatch_verified=False,signing_authorized=False)
