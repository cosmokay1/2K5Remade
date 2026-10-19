"""Deferred veteran free-agency bids using trusted simulation time.

Pending bids are management earmarks, never contracts or guest write permits.
The existing ledger records reactions and accepted proposals atomically with the
auction log. Real-game offseason clock/event binding is a separate adapter.
"""
from fractions import Fraction
import hashlib
import json

from franchise.cap import Offer, Rejected, json_amount
from franchise.control import AccessDisabled
from franchise.local_negotiation import LocalNegotiationProvider, _annual_value, _protected_value, _priority
from franchise.negotiation import Decision
from franchise.negotiation_reactions import reaction_effect
from franchise.promises import goals_from_list


def validate_window(window):
    fields = {'id', 'opens_at', 'closes_at', 'player_ids', 'source'}
    if (type(window) is not dict or set(window) != fields
            or any(type(window[k]) is not str or not window[k].strip() for k in ('id', 'source'))
            or any(type(window[k]) is not int or window[k] < 0 for k in ('opens_at', 'closes_at'))
            or not window['opens_at'] < window['closes_at']
            or type(window['player_ids']) is not list or not window['player_ids']
            or any(type(p) is not str or not p.strip() for p in window['player_ids'])
            or len(set(window['player_ids'])) != len(window['player_ids'])):
        raise ValueError('Explicit sourced auction window and unique veteran identities required')


class LocalAuction:
    def __init__(self, store, runtime, *, access_check=None):
        self.store, self.runtime = store, runtime
        self.access_check = access_check or runtime.check
        self.window = runtime.config['auction']
        policy = {key: value for key, value in runtime.config.items() if key not in ('enabled', 'signing_enabled')}
        self.policy_digest = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
        validate_window(self.window)
        if not set(self.window['player_ids']) <= set(runtime.config['quotes']):
            raise ValueError('Every auction player requires sourced asking terms')
        with store._connection(write=True) as db:
            runtime.check()
            db.execute('CREATE TABLE IF NOT EXISTS local_auction_windows '
                       '(id TEXT PRIMARY KEY, policy_sha256 TEXT NOT NULL, config TEXT NOT NULL, '
                       'last_tick INTEGER NOT NULL, result TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS local_auction_events '
                       '(id INTEGER PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, auction_id TEXT NOT NULL, payload TEXT NOT NULL)')
            row = db.execute('SELECT policy_sha256,config FROM local_auction_windows WHERE id=?', (self.window['id'],)).fetchone()
            config = json.dumps(self.window, sort_keys=True)
            if row:
                if row != (self.policy_digest, config):
                    raise Rejected('Auction identity cannot be restarted with a different policy or deadline')
            else:
                for (saved,) in db.execute('SELECT config FROM local_auction_windows'):
                    other = json.loads(saved)
                    if (set(other['player_ids']) & set(self.window['player_ids']) and
                            max(other['opens_at'], self.window['opens_at']) < min(other['closes_at'], self.window['closes_at'])):
                        raise Rejected('Player already has an overlapping auction window')
                db.execute('INSERT INTO local_auction_windows VALUES(?,?,?,?,NULL)',
                    (self.window['id'], self.policy_digest, config, runtime.tick()))

    def _guard(self, db):
        tick = self.runtime.tick()
        self._check(tick)
        row = db.execute('SELECT last_tick,result FROM local_auction_windows WHERE id=?', (self.window['id'],)).fetchone()
        if tick < row[0]:
            raise Rejected('Auction simulation clock moved backwards')
        return tick, json.loads(row[1]) if row[1] is not None else None

    def _check(self, tick):
        self.runtime.check()
        if self.access_check() is False:
            raise AccessDisabled('Auction access denied')
        if self.runtime.tick() != tick:
            raise Rejected('Auction clock changed during the transaction')

    def _events(self, db):
        return [json.loads(row[0]) for row in db.execute(
            'SELECT payload FROM local_auction_events WHERE auction_id=? ORDER BY id', (self.window['id'],))]

    @staticmethod
    def _latest(events):
        latest = {}
        for event in events:
            latest[event['team_id'], event['player_id']] = event
        return latest

    def _reserved(self, db, team, *, except_player=None, clearing=False):
        latest = {}
        for (serialized,) in db.execute('SELECT payload FROM local_auction_events ORDER BY id'):
            event = json.loads(serialized)
            latest[event['auction_id'], event['team_id'], event['player_id']] = event
        reserve = Fraction(0)
        for event in latest.values():
            if event['team_id'] != team or event['player_id'] == except_player:
                continue
            if event['result']['state'] not in ('pending', 'selected'):
                continue
            if clearing and event['auction_id'] == self.window['id'] and event['result']['state'] == 'pending':
                continue
            if db.execute('SELECT 1 FROM ownership WHERE player_id=?', (event['player_id'],)).fetchone():
                continue  # The ledger now owns the real charge, or another team signed him.
            reserve += Offer.from_dict(event['offer']).charges(5)[0]
        return reserve

    def _preview(self, db, team, offer, revision, *, clearing=False):
        ledger = self.store._load(db, team)
        if offer.player_id in ledger._rookies:
            raise Rejected('This auction supports registered veteran free agents only')
        self.store._check_draft_right(db, team, offer.player_id)
        preview = ledger.preview_offer(offer, revision)
        if Fraction(preview['room_after']) < self._reserved(db, team, except_player=offer.player_id, clearing=clearing):
            raise Rejected('Auction bids exceed cap room after existing auction earmarks')
        return ledger, preview

    def _context(self, db, team, offer, events, *, exclude=None):
        ledger = self.store._load(db, team)
        actor = ledger._actors.get(offer.player_id)
        if actor is None:
            raise Rejected('Initialized player personality and relationships required for bidding')
        recorded = self.store._negotiation_history(db, team, offer.player_id)
        # Lowballs also live in the ordinary ledger. Do not count them twice.
        cutoff = min(self.window['opens_at'], self.runtime.tick() - 1)
        history = [e for e in recorded if e.get('local_rules', {}).get('tick', self.window['opens_at']) >= cutoff]
        seen = {e['request_id'] for e in history}
        recent = [json.loads(row[0]) for row in db.execute(
            'SELECT payload FROM local_auction_events WHERE auction_id<>? ORDER BY id', (self.window['id'],))]
        for event in events + [e for e in recent if e['tick'] >= cutoff]:
            if (event['team_id'] == team and event['player_id'] == offer.player_id and event['kind'] == 'bid'
                    and event['request_id'] != exclude and event['request_id'] not in seen):
                history.append(dict(request_id=event['request_id'], offer=event['offer'],
                                    reaction=event['result'].get('reaction', 'none')))
                seen.add(event['request_id'])
        return dict(player_id=offer.player_id, offer=offer.to_dict(), **actor,
                    performance={}, history=history, promise_goals=[])

    def _story(self, db, team, request, offer, decision, *, price, tick, auction, preview=None, goals=(), contract_format=None):
        ledger = self.store._load(db, team)
        actor = ledger._actors[offer.player_id]
        history = self.store._negotiation_history(db, team, offer.player_id)
        story = dict(request_id=request, offer=offer.to_dict(), action=decision.action,
            reason=decision.reason, counter=decision.counter.to_dict() if decision.counter else None,
            outcome='accepted_proposal' if decision.action == 'accept' else 'player_rejected',
            reaction=decision.reaction, history_request_ids=[e['request_id'] for e in history],
            evidence={**actor, 'performance': {}, 'financial_revision': ledger.revision},
            local_rules=dict(format=1, policy_sha256=self.runtime.digest, tick=tick,
                window_start=tick, history_start=len(history), **price), auction=auction)
        if decision.action == 'accept':
            story.update(decision_mode='proposal', proposal_preview=preview)
        if contract_format is not None:
            from franchise.guest_contracts import guest_offer_encoding
            story.update(decision_mode='proposal', contract_format=contract_format,
                guest_offer=guest_offer_encoding(offer, contract_format=contract_format), guest_counter=None)
        if decision.reaction != 'none':
            story['reaction_effect'] = reaction_effect(actor['relationships'], decision.reaction)
        if goals:
            story.update(promise_goals=goals, counter_promises=None)
        self.store._record_negotiation(db, team, story, access_check=lambda: self._check(tick))
        return story

    def _write(self, db, event, tick):
        self._check(tick)
        db.execute('INSERT INTO local_auction_events(request_id,auction_id,payload) VALUES(?,?,?)',
            (event['request_id'], self.window['id'], json.dumps(event, allow_nan=False)))
        db.execute('UPDATE local_auction_windows SET last_tick=? WHERE id=?', (tick, self.window['id']))

    def bid(self, team, request_id, offer, expected_revision, *, contract_format=None, promise_goals=(), receipt_check=lambda _: None):
        if not isinstance(offer, Offer) or type(request_id) is not str or not request_id.strip():
            raise ValueError('Typed bid and stable request identity required')
        if type(team) is not str or not team.strip() or type(expected_revision) is not int or expected_revision < 0:
            raise ValueError('Stable bidding team and nonnegative financial revision required')
        if offer.player_id not in self.window['player_ids']:
            raise Rejected('Player is outside this auction')
        if type(promise_goals) is not tuple:
            raise ValueError('Immutable promise proposals required')
        from dataclasses import asdict
        goals = [asdict(g) for g in promise_goals]; goals_from_list(goals)
        if contract_format is not None:
            from franchise.guest_contracts import guest_offer_encoding, guest_money_scale
            guest_money_scale(contract_format)
            guest_offer_encoding(offer, contract_format=contract_format)
        command = dict(team_id=team, offer=offer.to_dict(), expected_revision=expected_revision,
                       contract_format=contract_format, promise_goals=goals)
        with self.store._connection(write=True) as db:
            tick, cleared = self._guard(db)
            prior = db.execute('SELECT payload FROM local_auction_events WHERE request_id=?', (request_id,)).fetchone()
            if prior:
                event = json.loads(prior[0])
                if event['auction_id'] != self.window['id'] or event.get('command') != command or event['kind'] != 'bid':
                    raise Rejected('Auction request identity reused with different terms')
                receipt_check(event['result'])
                return event['result']
            if cleared is not None or not self.window['opens_at'] <= tick < self.window['closes_at']:
                raise Rejected('Auction is not accepting bids')
            events = self._events(db)
            self._preview(db, team, offer, expected_revision)
            context = self._context(db, team, offer, events)
            context['promise_goals'] = goals
            demand, price = self.runtime.asking_terms(offer.player_id, contract_format)
            decision = Decision.parse(LocalNegotiationProvider(demand)(context), offer.player_id)
            result = dict(state='pending' if decision.action == 'accept' else 'counteroffer' if decision.action == 'counter' else 'player_rejected',
                reason="We'll review this offer when the free-agency round closes." if decision.action == 'accept' else decision.reason,
                reaction=decision.reaction, counter=decision.counter.to_dict() if decision.counter else None,
                counter_promises=goals if decision.action == 'counter' else None,
                closes_at=self.window['closes_at'], write_authorized=False)
            if decision.counter is not None and contract_format:
                from franchise.guest_contracts import guest_offer_encoding
                guest_offer_encoding(decision.counter, contract_format=contract_format)
            if decision.reaction == 'offended':
                self._story(db, team, request_id, offer, decision, price=price, tick=tick,
                            auction=dict(id=self.window['id'], bid_request_id=request_id), contract_format=contract_format)
            event = dict(auction_id=self.window['id'], request_id=request_id, team_id=team,
                player_id=offer.player_id, kind='bid', tick=tick, offer=offer.to_dict(), command=command, result=result)
            receipt_check(result)
            self._write(db, event, tick)
            return result

    def withdraw(self, team, player, request_id, *, receipt_check=lambda _: None):
        if any(type(v) is not str or not v.strip() for v in (team, player, request_id)):
            raise ValueError('Stable auction withdrawal identities required')
        with self.store._connection(write=True) as db:
            tick, cleared = self._guard(db)
            prior = db.execute('SELECT payload FROM local_auction_events WHERE request_id=?', (request_id,)).fetchone()
            if prior:
                event = json.loads(prior[0])
                if (event['auction_id'], event['team_id'], event['player_id'], event['kind']) != (self.window['id'], team, player, 'withdraw'):
                    raise Rejected('Withdrawal identity reused')
                receipt_check(event['result'])
                return event['result']
            if cleared is not None or not self.window['opens_at'] <= tick < self.window['closes_at']:
                raise Rejected('Auction withdrawal window is closed')
            previous = self._latest(self._events(db)).get((team, player))
            if previous is None or previous['result']['state'] != 'pending':
                raise Rejected('No pending bid to withdraw')
            result = dict(state='withdrawn', reason="We've recorded the withdrawal. There is no agreement.", write_authorized=False)
            event = {**previous, 'kind': 'withdraw', 'request_id': request_id, 'result': result, 'tick': tick}
            receipt_check(result)
            self._write(db, event, tick)
            return result

    def resolve(self, *, receipt_check=lambda _: None):
        """Select affordable offers after closing; record consent, never sign."""
        with self.store._connection(write=True) as db:
            tick, cleared = self._guard(db)
            if cleared is not None:
                receipt_check(cleared)
                return cleared
            if tick < self.window['closes_at']:
                raise Rejected('Players are still considering bids; this round has not closed')
            events = self._events(db)
            latest = self._latest(events)
            outcomes = {}
            for player in sorted(self.window['player_ids']):
                candidates = []
                for (team, candidate_player), event in latest.items():
                    if candidate_player != player or event['result']['state'] != 'pending':
                        continue
                    offer = Offer.from_dict(event['offer'])
                    ledger = self.store._load(db, team)
                    try:
                        _, preview = self._preview(db, team, offer, ledger.revision, clearing=True)
                        context = self._context(db, team, offer, events, exclude=event['request_id'])
                        demand, price = self.runtime.asking_terms(player, event['command']['contract_format'])
                        decision = Decision.parse(LocalNegotiationProvider(demand)(context), player)
                        if decision.action != 'accept':
                            continue
                    except Rejected:
                        continue  # Spending/ownership changed: never force the bid through.
                    security = _priority(context['personality'], 'security')
                    loyalty = _priority(context['personality'], 'loyalty')
                    trust = _priority(context['relationships'], 'trust')
                    # Same asking term required by the bargaining policy. Exact
                    # annual value/security and recorded relationship break ties.
                    score = _annual_value(offer) * (1 + loyalty * trust / 20) + security * Fraction(_protected_value(offer), len(offer.salaries)) / 10
                    candidates.append((score, events.index(event), event, preview, price))
                if not candidates:
                    outcomes[player] = dict(state='unsigned', team_id=None, reason="We haven't agreed to an eligible offer.", write_authorized=False)
                    continue
                _, _, winner, preview, price = sorted(candidates, key=lambda c: (-c[0], c[1]))[0]
                team = winner['team_id']; offer = Offer.from_dict(winner['offer'])
                proposal_id = 'auction-choice:' + self.window['id'] + ':' + winner['request_id']
                reason = "We've considered the offers and chosen your proposal. Let's finalize the agreement."
                decision = Decision('accept', reason, None)
                story = self._story(db, team, proposal_id, offer, decision, price=price, tick=tick,
                    auction=dict(id=self.window['id'], bid_request_id=winner['request_id']), preview=preview,
                    goals=winner['command']['promise_goals'], contract_format=winner['command']['contract_format'])
                selected = {**winner, 'kind': 'selection', 'request_id': proposal_id,
                    'result': dict(state='selected', proposal_request_id=story['request_id'], reason=reason, write_authorized=False)}
                self._write(db, selected, tick)
                outcomes[player] = dict(state='selected', team_id=team, proposal_request_id=proposal_id,
                                        reason=reason, write_authorized=False)
            for (team, player), event in latest.items():
                if event['result']['state'] != 'pending' or outcomes[player].get('team_id') == team:
                    continue
                result = dict(state='not_selected', reason=("We've chosen another team's offer." if outcomes[player]['state'] == 'selected'
                    else "We haven't reached an eligible agreement this round."), write_authorized=False)
                self._write(db, {**event, 'kind': 'resolution',
                    'request_id': 'auction-result:' + self.window['id'] + ':' + event['request_id'], 'result': result}, tick)
            self._check(tick)
            result = dict(auction_id=self.window['id'], state='resolved', outcomes=outcomes, write_authorized=False)
            receipt_check(result)
            self._check(tick)
            db.execute('UPDATE local_auction_windows SET last_tick=?,result=? WHERE id=?',
                       (tick, json.dumps(result), self.window['id']))
            return result

    def status(self, team):
        self.runtime.check()
        with self.store._connection() as db:
            tick, cleared = self._guard(db)
            latest = self._latest(self._events(db))
            return dict(auction_id=self.window['id'], state='resolved' if cleared else 'awaiting_resolution' if tick >= self.window['closes_at'] else 'open' if tick >= self.window['opens_at'] else 'not_open',
                closes_at=self.window['closes_at'], bids={player: event['result'] for (club, player), event in latest.items() if club == team},
                outcomes=cleared['outcomes'] if cleared else None,
                earmarked_cap=json_amount(self._reserved(db, team)), write_authorized=False)
