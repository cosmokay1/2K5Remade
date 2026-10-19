"""Explicit local-rules runtime. No SDK, network, credential or save writes.

Quotes are owner-supplied, sourced policy inputs, never taken from the user's
submitted offer. Decisions and their clock/price provenance use the existing
atomic negotiation journal; no second state database or history reset endpoint.
"""
from copy import copy
from fractions import Fraction
import hashlib
import json
from math import gcd
from pathlib import Path

from franchise.cap import Offer, Rejected
from franchise.control import AccessDisabled
from franchise.local_negotiation import LocalNegotiationProvider
from franchise.performance import PerformanceEvidence


def saved_calendar_tick(reader):
    """Supported saved preseason/regular/postseason steps, not wall-clock time.

    Unsaved progress never reopens bargaining. Unknown offseason/auction phases
    remain unsupported rather than treating raw phase codes as elapsed weeks.
    """
    from tools.inspect_franchise_calendar import inspect_calendar
    calendar = inspect_calendar(reader())
    phase = calendar['phase_01_raw']
    periods = {7: (0, 4), 8: (4, 18), 9: (22, 4)}
    if phase not in periods:
        raise Rejected('Local bargaining does not support this saved calendar phase')
    offset, horizon = periods[phase]
    step = calendar['step_05_raw']
    if calendar['step_04_raw'] != horizon or not 0 <= step <= horizon:
        raise Rejected('Unsupported saved bargaining calendar horizon or step')
    return calendar['season_index'] * 32 + offset + step


class LocalRulesRuntime:
    def __call__(self, context):
        return self.evaluate(context)[0]

    def __init__(self, path, *, clock):
        self.path = Path(path)
        self._bytes = self.path.read_bytes()
        self.config = json.loads(self._bytes)
        c = self.config
        if (type(c) is not dict or not {'format', 'enabled', 'signing_enabled', 'team_id', 'quotes'} <= set(c)
                or set(c) - {'format', 'enabled', 'signing_enabled', 'team_id', 'quotes', 'auction'}
                or type(c['format']) is not int or c['format'] != 1
                or type(c['enabled']) is not bool or type(c['signing_enabled']) is not bool
                or type(c['team_id']) is not str or not c['team_id'].strip()
                or type(c['quotes']) is not dict or not c['quotes'] or not callable(clock)):
            raise ValueError('Complete explicit local-rules configuration required')
        self.clock = clock
        self.digest = hashlib.sha256(self._bytes).hexdigest()
        for player, quote in c['quotes'].items():
            if (type(player) is not str or not player.strip() or type(quote) is not dict
                    or not {'offer', 'source'} <= set(quote)
                    or set(quote) - {'offer', 'source', 'performance', 'adjustment'}
                    or type(quote['source']) is not str or not quote['source'].strip()):
                raise ValueError('Sourced local asking contracts required')
            demand = Offer.from_dict(quote['offer'])
            if demand.player_id != player:
                raise ValueError('Quote belongs to another player')
            LocalNegotiationProvider(demand)
            if ('performance' in quote) != ('adjustment' in quote):
                raise ValueError('Performance adjustment needs both evidence and policy')
            if 'performance' in quote:
                evidence = PerformanceEvidence.from_context(quote['performance'])
                adjustment = quote['adjustment']
                if (evidence.player_id != player or evidence.complete_window is not True
                        or type(adjustment) is not dict or set(adjustment) != {'counter', 'reference_per_game', 'minimum_games'}
                        or adjustment['counter'] not in {'passing_yards', 'receiving_yards', 'rushing_yards', 'sacks'}
                        or type(adjustment['reference_per_game']) is not int or adjustment['reference_per_game'] <= 0
                        or type(adjustment['minimum_games']) is not int or not 1 <= adjustment['minimum_games'] <= 32):
                    raise ValueError('Complete sourced performance and bounded pricing policy required')
        if 'auction' in c:
            from franchise.auction import validate_window
            validate_window(c['auction'])
        self.check()

    def check(self, *, signing=False):
        # Removing/disabling/changing this owner-controlled file revokes access.
        # Reloading a changed price/policy requires an explicit service restart.
        try:
            current = self.path.read_bytes()
            if current != self._bytes or not self.config['enabled']:
                raise AccessDisabled('Local rules disabled or configuration changed')
            if signing and not self.config['signing_enabled']:
                raise AccessDisabled('Local signing is not enabled')
        except OSError as exc:
            raise AccessDisabled('Local authorization unavailable') from exc

    def tick(self):
        tick = self.clock()
        if type(tick) is not int or tick < 0:
            raise ValueError('Trusted nonnegative simulation tick required')
        return tick

    def for_team(self, team_id):
        if team_id != self.config['team_id']:
            raise Rejected('Local policy belongs to another team')
        # Each request binds its clock through all access/commit checks.
        session = copy(self)
        session._tick = self.tick()
        return session

    def request_check(self, *, signing=False):
        self.check(signing=signing)
        if self.tick() != self._tick:
            raise Rejected('Saved simulation clock changed during negotiation')

    def evaluate(self, context):
        self.request_check()
        if 'auction' in self.config and context['player_id'] in self.config['auction']['player_ids']:
            raise Rejected('This player requires a pending auction bid, not immediate negotiation')
        demand, price = self.asking_terms(context['player_id'], context.get('contract_format'))
        history = context['history']
        previous = [(i, event['local_rules']) for i, event in enumerate(history) if 'local_rules' in event]
        start, cursor = self._tick, 0
        if previous:
            _, last = previous[-1]
            if self._tick < last['tick']:
                raise Rejected('Saved bargaining clock moved backwards')
            start = last['window_start']
            if self._tick - start >= 2:
                start, cursor = self._tick, len(history)
            else:
                cursor = last['history_start']
        result = LocalNegotiationProvider(demand, history_start=cursor)(context)
        provenance = {'format': 1, 'policy_sha256': self.digest, 'tick': self._tick,
                      'window_start': start, 'history_start': cursor, **price}
        return result, provenance

    def asking_terms(self, player, contract_format=None):
        self.check()
        quote = self.config['quotes'].get(player)
        if quote is None:
            raise Rejected('Sourced local asking contract unavailable for this player')
        demand = Offer.from_dict(quote['offer'])
        factor = Fraction(1)
        if 'performance' in quote:
            # Read only server-owned canonical evidence, never the client's stats.
            e, a = quote['performance'], quote['adjustment']
            observations = e['observations']
            games = observations.get('games', {}).get('value')
            production = observations.get(a['counter'], {}).get('value')
            if games is not None and games >= a['minimum_games'] and production is not None:
                factor = max(Fraction(3, 4), min(Fraction(5, 4),
                    Fraction(production, games * a['reference_per_game'])))
                if contract_format:
                    from franchise.guest_contracts import guest_terms_for_offer
                    terms = guest_terms_for_offer(demand, contract_format=contract_format)
                    # Price in native amount units, then decode its exact salary
                    # and bonus rounding. Do not round modern charges to fit.
                    # The game's bonus proration truncates whole thousands.
                    # Stay on exact allocation multiples rather than emitting
                    # a counter that only looks representable after rounding.
                    step = terms.years // gcd(terms.years, terms.bonus_code) if terms.bonus_code else 1
                    amount = max(step, min(65535 // step * step,
                        (terms.amount_word * factor // step) * step))
                    from franchise.guest_contracts import GuestContractTerms
                    demand = GuestContractTerms(amount, terms.bonus_code, terms.shape_code, terms.years).to_offer(
                        player, contract_format=contract_format)
                else:
                    up = lambda value: (value * factor).__ceil__()
                    demand = Offer(player, tuple(up(v) for v in demand.salaries), up(demand.signing_bonus),
                                   tuple(up(v) for v in demand.guaranteed_salaries))
        price = {'asking_offer': demand.to_dict(), 'source': quote['source'],
                 'performance_factor': [factor.numerator, factor.denominator]}
        if 'performance' in quote:
            price['performance'] = quote['performance']
            price['adjustment'] = quote['adjustment']
        return demand, price


def validate_local_record(story):
    """Validate persisted local provenance while replaying the existing ledger."""
    data = story['local_rules']
    required = {'format', 'policy_sha256', 'tick', 'window_start', 'history_start',
                'asking_offer', 'source', 'performance_factor'}
    if (type(data) is not dict or not required <= set(data)
            or set(data) - required - {'performance', 'adjustment'}
            or type(data['format']) is not int or data['format'] != 1
            or type(data['policy_sha256']) is not str or len(data['policy_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in data['policy_sha256'])
            or any(type(data[key]) is not int or data[key] < 0 for key in ('tick', 'window_start', 'history_start'))
            or not 0 <= data['tick'] - data['window_start'] < 2
            or type(story.get('history_request_ids')) is not list
            or data['history_start'] > len(story['history_request_ids'])
            or type(data['source']) is not str or not data['source'].strip()):
        raise ValueError('Invalid persisted local negotiation provenance')
    demand = Offer.from_dict(data['asking_offer'])
    LocalNegotiationProvider(demand)
    if demand.player_id != story['offer']['player_id']:
        raise ValueError('Local asking terms belong to another player')
    factor = data['performance_factor']
    if (type(factor) is not list or len(factor) != 2
            or any(type(v) is not int or v <= 0 for v in factor)
            or not Fraction(3, 4) <= Fraction(*factor) <= Fraction(5, 4)):
        raise ValueError('Invalid persisted local performance factor')
    if ('performance' in data) != ('adjustment' in data):
        raise ValueError('Incomplete local performance provenance')
    if 'performance' in data:
        evidence = PerformanceEvidence.from_context(data['performance'])
        if evidence.player_id != demand.player_id or evidence.complete_window is not True:
            raise ValueError('Foreign or incomplete local performance provenance')
