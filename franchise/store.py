"""SQLite-backed transaction history for the supported prototype operations.

Each write rebuilds from immutable bootstrap data under a database write lock.
Contracts, ownership and optional story data commit in one transaction. No
retail game state is imported or modified by this store.
"""
from contextlib import contextmanager, closing
from dataclasses import asdict
import json
import math
from pathlib import Path
import sqlite3
import uuid
from franchise.cap import Ledger, Offer, Rejected, json_amount, money
from franchise.rookie import RookieScale, UndraftedScale
from franchise.books import OpeningBooks, parse_amount
from franchise.cash import CashBook, CashObligation


def from_config(config: dict) -> Ledger:
    config = dict(config)
    if config.get("management_profile") is not None:
        from franchise.management import ManagementProfile
        config["management_profile"] = ManagementProfile.from_dict(config["management_profile"])
    if config.get("rookie_pool_opening") is not None:
        from franchise.rookie_opening import RookiePoolOpening
        config["rookie_pool_opening"] = RookiePoolOpening.from_dict(config["rookie_pool_opening"])
    if config.get("veteran_minimum_profile") is not None:
        from franchise.salary_rules import VeteranMinimumProfile
        config["veteran_minimum_profile"] = VeteranMinimumProfile.from_dict(config["veteran_minimum_profile"])
    if config.get("opening_books") is None:
        raise ValueError("Source opening books are missing; explicit migration required")
    config["existing_charges"] = tuple(parse_amount(value) for value in config["existing_charges"])
    if config.get("opening_books") is not None:
        config["opening_books"] = OpeningBooks.from_dict(config["opening_books"])
    config["signed_player_ids"] = frozenset(config["signed_player_ids"])
    config["veteran_minimums"] = {key: tuple(value) for key, value
                                   in config["veteran_minimums"].items()}
    config["rookies"] = {key: (RookieScale if "draft_round" in value else UndraftedScale)(**{**value,
                              "minimum_salaries": tuple(value["minimum_salaries"])})
                         for key, value in config["rookies"].items()}
    return Ledger(**config)


class FranchiseStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path == ":memory:":
            raise ValueError("Durable franchise state requires a database file")
        with self._connection(write=True) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 3):
                raise ValueError("Unsupported franchise database version")
            db.execute("CREATE TABLE IF NOT EXISTS teams (id TEXT PRIMARY KEY, config TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS ownership (player_id TEXT PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams(id))")
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams(id), request_key TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(team_id, request_key))")
            db.execute("PRAGMA user_version=3")

    @classmethod
    def migrate_v2(cls, path: str | Path, books_by_team: dict[str, OpeningBooks]) -> Path:
        """Attach verified source books without changing recorded financial results.

        Requires every team and exact reconciliation. A consistent SQLite backup
        is taken before writes; any failed reconciliation rolls back the migration.
        """
        path = Path(path)
        if not path.is_file():
            raise ValueError("Migration requires an existing database")
        instance = cls.__new__(cls)
        instance.path = str(path)
        backup = path.with_name(path.stem + ".v2-backup-" + uuid.uuid4().hex + ".sqlite")
        with instance._connection(write=True) as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != 2:
                raise ValueError("Only posting-verified format 2 can use this migration")
            teams = {team for (team,) in db.execute("SELECT id FROM teams")}
            if type(books_by_team) is not dict or set(books_by_team) != teams:
                raise ValueError("Migration requires opening books for every team")
            if any(not isinstance(books, OpeningBooks) for books in books_by_team.values()):
                raise ValueError("Typed source books required")
            # This connection holds the write reservation. A separate read
            # connection can back up the unchanged, committed source consistently.
            with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as target:
                source.backup(target)
            for team, books in books_by_team.items():
                config = json.loads(db.execute("SELECT config FROM teams WHERE id=?", (team,)).fetchone()[0])
                config["opening_books"] = books.to_dict()
                db.execute("UPDATE teams SET config=? WHERE id=?", (json.dumps(config), team))
            for team in teams:
                instance._load(db, team)
            db.execute("PRAGMA user_version=3")
        return backup

    @contextmanager
    def _connection(self, *, write=False):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_team(self, team_id: str, ledger: Ledger):
        if type(team_id) is not str or not team_id.strip():
            raise ValueError("Stable team ID required")
        config = ledger.bootstrap_config()
        if ledger._rookies.keys() & ledger._players and ledger._rookie_pool_opening is None:
            raise ValueError("Durable starting rookie roster requires explicit cohort/pool source")
        if config["opening_books"] is None:
            raise ValueError("Durable teams require source opening books, not aggregate-only balances")
        with self._connection(write=True) as db:
            if db.execute("SELECT 1 FROM teams WHERE id=?", (team_id,)).fetchone():
                raise Rejected("Team already exists; refusing to overwrite financial state")
            db.execute("INSERT INTO teams VALUES (?, ?)", (team_id, json.dumps(config)))
            for player in config["signed_player_ids"]:
                if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (player,)).fetchone():
                    raise Rejected("Player already belongs to another team")
                db.execute("INSERT INTO ownership VALUES (?, ?)", (player, team_id))

    def _load(self, db, team_id) -> Ledger:
        row = db.execute("SELECT config FROM teams WHERE id=?", (team_id,)).fetchone()
        if row is None:
            raise Rejected("Unknown team")
        ledger = from_config(json.loads(row[0]))
        ledger._actors = {}
        ledger._scouting = []
        relationship_sources = set()
        payment_references = set()
        for event_id, kind, serialized in db.execute("SELECT id, kind, payload FROM events WHERE team_id=? ORDER BY id", (team_id,)):
            payload = json.loads(serialized)
            if kind == "sign":
                self._validate_story_evidence(payload["story"])
                data = payload["offer"]
                receipt = ledger.sign(payload["request_id"], Offer.from_dict(data), payload["expected_revision"])
                if ledger._cash is not None:
                    ledger._cash.add_contract(receipt.offer, "sign:" + payload["request_id"], track_components=payload.get("cash_components", False))
                    if payload.get("cash_posting") != ledger.cash_snapshot():
                        raise ValueError("Recorded signing cash disagrees with replay")
                if payload.get("contract_charges") != [json_amount(value) for value in receipt.charges]:
                    raise ValueError("Recorded contract charges disagree with replay")
            elif kind == "cash_open":
                if ledger._cash is not None:
                    raise ValueError("Duplicate opening cash state")
                records = tuple(CashObligation.from_dict(record) for record in payload["records"])
                self._check_opening_cash(ledger, records)
                ledger._cash = CashBook(records, payload["source"])
                self._check_cash_components(ledger)
                ledger.revision += 1
                if payload["cash_posting"] != ledger.cash_snapshot():
                    raise ValueError("Opening cash posting disagrees with records")
            elif kind == "cash_payment":
                if type(payload.get("source")) is not str or not payload["source"].strip():
                    raise ValueError("Recorded payment source is missing")
                if "payment_reference" in payload:
                    reference = payload["payment_reference"]
                    if type(reference) is not str or not reference.strip():
                        raise ValueError("Recorded payment reference is invalid")
                    identity = (payload["source"], reference)
                    if identity in payment_references:
                        raise ValueError("Duplicate recorded payment evidence")
                    payment_references.add(identity)
                if ledger._cash is None:
                    raise ValueError("Payment has no opening cash state")
                ledger._cash.pay(payload["obligation_id"], payload["amount"], payload["expected_cash_revision"], component=payload.get("component"))
                self._check_cash_components(ledger)
                ledger.revision += 1
                if payload["cash_posting"] != ledger.cash_snapshot():
                    raise ValueError("Cash payment posting disagrees with replay")
            elif kind == "actor":
                ledger.negotiation_context(payload["player_id"])
                self._validate_actor(payload["actor"])
                if payload["player_id"] in ledger._actors:
                    raise ValueError("Duplicate actor registration")
                ledger._actors[payload["player_id"]] = payload["actor"]
            elif kind == "relationship":
                identity = (payload["player_id"], payload["relationship"], payload["source_request_id"])
                if identity in relationship_sources:
                    raise ValueError("Relationship consequence already applied")
                relationship_sources.add(identity)
                self._relationship_source(db, team_id, payload["player_id"], payload["source_request_id"], before_revision=ledger.revision, before_event_id=event_id)
                actor = ledger._actors.get(payload["player_id"])
                self._apply_relationship(actor, payload["relationship"], payload["delta"])
                if actor != payload["actor_after"]:
                    raise ValueError("Relationship posting disagrees with replay")
                ledger.revision += 1
            elif kind == "draft_scouting":
                from franchise.draft import validate_scouting
                validate_scouting(payload["event"], ledger)
                ledger._scouting.append(payload["event"])
            elif kind == "dialogue":
                self._validate_dialogue(payload["event"])
            elif kind == "budget":
                ledger.update_budget(**{key: payload[key] for key in ("cap", "roster_reserve", "expected_revision")})
            else:
                raise ValueError("Unknown financial event; refusing to reconstruct state")
            if payload.get("posting") != ledger.financial_snapshot():
                raise ValueError("Recorded financial posting disagrees with replay")
        owned = {player for (player,) in db.execute("SELECT player_id FROM ownership WHERE team_id=?", (team_id,))}
        if owned != set(ledger.financial_snapshot()["signed_players"]):
            raise ValueError("Ownership records disagree with contract history")
        return ledger

    def load_team(self, team_id: str) -> Ledger:
        with self._connection() as db:
            return self._load(db, team_id)

    def roster_components(self, team, *, phase, league_year, classifications,
                          classification_source, selected_top51=None):
        """Read-only phase projection; does not alter signing authority or calendar."""
        from fractions import Fraction
        from franchise.minimums import minimum_salary
        from franchise.roster_accounting import RosterSalary, roster_charge
        if type(classification_source) is not str or not classification_source.strip():
            raise ValueError("Roster classification provenance required")
        ledger = self.load_team(team)
        if ledger._opening_books is None:
            raise Rejected("Original obligation records required")
        if (ledger._veteran_minimum_profile is not None
                and ledger._veteran_minimum_profile.start_year != league_year):
            raise Rejected("Projection year disagrees with salary profile")
        players = set(ledger._active_contracts) | set(ledger._tenders)
        if type(classifications) is not dict or set(classifications) != players:
            raise ValueError("Explicit credited-season/UDFA inputs for every salary entry required")
        entries = []
        gross = Fraction(0)
        for player in sorted(players):
            inputs = classifications[player]
            if type(inputs) is not tuple or len(inputs) != 2:
                raise ValueError("Credited seasons and UDFA status required")
            credits, undrafted = inputs
            minimum = minimum_salary(league_year, credits, "active_inactive")
            if player in ledger._active_contracts:
                contract = ledger._active_contracts[player]
                base = contract.offer.salaries[contract.elapsed_years]
                value = contract.charges()[0]
                source = contract.source
            else:
                if undrafted is not False:
                    raise ValueError("Drafted rookie tender cannot be classified as UDFA")
                base = ledger._tenders[player]
                value = Fraction(base)
                source = "declared unsigned drafted rookie tender"
            gross += value
            entries.append(RosterSalary(player, base, value - base, minimum, undrafted, source))
        result = roster_charge(tuple(entries), phase=phase, selected_top51=selected_top51)
        retained = ledger.charges[0] - gross
        total = Fraction(result["supported_roster_charge"]) + retained
        if total < 0:
            raise Rejected("Phase projection credits exceed modeled liabilities")
        return {**result, "revision": ledger.revision, "league_year": league_year,
                "classification_source": classification_source,
                "retained_and_adjustment_charge": json_amount(retained),
                "projected_modeled_team_charge": json_amount(total),
                "current_authoritative_charge": json_amount(ledger.charges[0]),
                "signing_authority_changed": False}

    def termination_components(self, team, player, *, removed_on, discount, payment_year_offsets):
        """Read-only covered-bonus/base components; no release or cap-room grant."""
        from franchise.guarantees import DiscountProfile, guaranteed_base_liability
        from franchise.termination import signing_bonus_acceleration
        if not isinstance(discount, DiscountProfile):
            raise ValueError("Explicit discount profile required")
        ledger = self.load_team(team)
        contract = ledger.active_contract(player)
        if (ledger._veteran_minimum_profile is not None
                and ledger._veteran_minimum_profile.start_year != discount.league_year):
            raise Rejected("Termination year disagrees with franchise salary profile")
        cash = ledger.guarantee_cash(player)
        if cash is None:
            raise Rejected("Unpaid guarantee allocation is unavailable")
        guarantees = cash["unpaid_guaranteed_base_by_original_year"]
        if any(guarantees[:contract.elapsed_years]):
            raise Rejected("Unsettled prior-year guarantees require separate reconciliation")
        bonus = signing_bonus_acceleration(contract, league_year=discount.league_year,
            removed_on=removed_on, record_id="bonus:" + player)
        base = guaranteed_base_liability(contract,
            unpaid_by_year=tuple(guarantees[contract.elapsed_years:]),
            payment_year_offsets=payment_year_offsets, discount=discount,
            record_id="protected-base:" + player)
        return {"revision": ledger.revision, "player_id": player,
                "bonus_retained_charges": [json_amount(value) for value in bonus.annual_charges],
                "covered_base_present_value_charge": json_amount(base.cap_charge.annual_charges[0]),
                "nominal_unpaid_protected_base": base.nominal_unpaid,
                "nominal_unpaid_signing_bonus": cash["unpaid_signing_bonus"],
                "contract_source": contract.source, "rate_source": discount.rate_source,
                "release_authorized": False,
                "unresolved": ["covered termination facts and guarantee voids/offsets",
                               "earned salary, termination pay and injury protections",
                               "roster replacement/phase accounting"]}

    @staticmethod
    def _check_cash_components(ledger):
        if ledger._cash is None:
            return
        for player, offer in ledger._contracts.items():
            record = ledger._cash.records["contract:" + player]
            if record.paid_components is None:
                continue
            ceilings = {"signing_bonus": offer.signing_bonus,
                        **{"base:" + str(i): salary for i, salary in enumerate(offer.salaries)}}
            if any(key not in ceilings or amount > ceilings[key] for key, amount in record.paid_components):
                raise ValueError("Paid component exceeds or disagrees with original contract")

    @staticmethod
    def _check_opening_cash(ledger, records):
        by_id = {record.obligation_id: record for record in records}
        for player, offer in ledger._contracts.items():
            record = by_id.get("contract:" + player)
            if record is None or record.player_id != player or record.amount != sum(offer.salaries) + offer.signing_bonus:
                raise ValueError("Opening cash must reconcile every original active contract")

    def initialize_cash(self, team_id, records: tuple[CashObligation, ...], *, source: str):
        book = CashBook(records, source)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            if ledger._cash is not None:
                raise Rejected("Cash already initialized; refusing to reset payments")
            self._check_opening_cash(ledger, records)
            ledger._cash = book
            self._check_cash_components(ledger)
            ledger.revision += 1
            payload = {"records": [record.to_dict() for record in records], "source": source,
                       "cash_posting": book.snapshot(), "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, 'cash:opening', 'cash_open', ?)",
                       (team_id, json.dumps(payload, allow_nan=False)))

    def record_payment(self, team_id, request_id, obligation_id, amount, *, expected_cash_revision, source, payment_reference, component=None):
        if type(request_id) is not str or not request_id.strip() or type(source) is not str or not source.strip():
            raise ValueError("Payment request ID and evidence source required")
        if type(payment_reference) is not str or not payment_reference.strip():
            raise ValueError("Stable external payment reference required")
        money(amount)
        payload = dict(obligation_id=obligation_id, amount=amount, source=source, payment_reference=payment_reference,
                       expected_cash_revision=expected_cash_revision, component=component)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            if ledger._cash is None:
                raise Rejected("Cash history is unavailable; explicit initialization required")
            key = "cash:payment:" + request_id
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if prior:
                recorded = json.loads(prior[0])
                if "payment_reference" not in recorded:
                    raise Rejected("Legacy payment lacks external reference; audited migration required")
                if any(recorded[field] != payload[field] for field in ("obligation_id", "amount", "source", "payment_reference")) or recorded.get("component") != component:
                    raise Rejected("Payment request already recorded differently")
                return recorded["cash_posting"]
            for (serialized,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind='cash_payment'", (team_id,)):
                previous = json.loads(serialized)
                if previous.get("payment_reference") == payment_reference and previous["source"] == source:
                    raise Rejected("External payment evidence already recorded under another request")
            ledger._cash.pay(obligation_id, amount, expected_cash_revision, component=component)
            self._check_cash_components(ledger)
            ledger.revision += 1
            payload["cash_posting"] = ledger.cash_snapshot()
            payload["posting"] = ledger.financial_snapshot()
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'cash_payment', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return payload["cash_posting"]

    def preview_offer(self, team_id: str, offer: Offer, expected_revision: int) -> dict:
        with self._connection() as db:
            ledger = self._load(db, team_id)
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected("Player already belongs to a team")
            return ledger.preview_offer(offer, expected_revision)

    def sign(self, team_id: str, request_id: str, offer: Offer, expected_revision: int,
             *, access_check=None, story: dict | None = None):
        if type(request_id) is not str or not request_id.strip():
            raise Rejected("A request ID is required")
        if story is not None and type(story) is not dict:
            raise ValueError("Story must be a JSON object")
        self._validate_story_evidence(story)
        payload = {"request_id": request_id, "offer": offer.to_dict(),
                   "expected_revision": expected_revision, "story": story}
        serialized = json.dumps(payload, allow_nan=False)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            if db.execute("SELECT 1 FROM events WHERE team_id=? AND request_key=?", (team_id, "dialogue:" + request_id)).fetchone():
                raise Rejected("Request already belongs to a recorded negotiation")
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, "sign:" + request_id)).fetchone()
            if prior:
                previous = json.loads(prior[0])
                normalized = json.loads(serialized)
                if previous["offer"] != normalized["offer"] or previous["story"] != normalized["story"]:
                    raise Rejected("Request already committed with different terms or story")
                return ledger.sign(request_id, offer, expected_revision, access_check=access_check)
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected("Player already belongs to a team")
            if story is not None:
                self._check_history(db, team_id, offer.player_id, story)
            receipt = ledger.sign(request_id, offer, expected_revision, access_check=access_check)
            if ledger._cash is not None:
                ledger._cash.add_contract(offer, "sign:" + request_id)
                payload["cash_components"] = True
                payload["cash_posting"] = ledger.cash_snapshot()
            payload["posting"] = ledger.financial_snapshot()
            payload["contract_charges"] = [json_amount(value) for value in receipt.charges]
            serialized = json.dumps(payload, allow_nan=False)
            db.execute("INSERT INTO ownership VALUES (?, ?)", (offer.player_id, team_id))
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'sign', ?)", (team_id, "sign:" + request_id, serialized))
            return receipt

    def update_budget(self, team_id: str, *, cap: int, roster_reserve: int, expected_revision: int):
        payload = dict(cap=cap, roster_reserve=roster_reserve, expected_revision=expected_revision)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            ledger.update_budget(**payload)
            if ledger.revision != expected_revision:
                payload["posting"] = ledger.financial_snapshot()
                db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'budget', ?)", (team_id, f"budget:{expected_revision}", json.dumps(payload)))

    def stories(self, team_id: str) -> list[dict]:
        with self._connection() as db:
            self._load(db, team_id)  # Validate financial reconstruction first.
            return [payload["story"] for (text,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind='sign' ORDER BY id", (team_id,))
                    if (payload := json.loads(text))["story"] is not None]

    @staticmethod
    def _validate_actor(actor):
        from franchise.negotiation import validate_performance
        if type(actor) is not dict or set(actor) != {"personality", "relationships"}:
            raise ValueError("Personality and relationships required")
        if any(type(value) is not dict for value in actor.values()):
            raise ValueError("Actor fields must be JSON objects")
        validate_performance(actor)
        json.dumps(actor, allow_nan=False)

    def bind_actor(self, team_id, player_id, personality, relationships, *, access_check):
        actor = {"personality": personality, "relationships": relationships}
        self._validate_actor(actor)
        actor = json.loads(json.dumps(actor, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            ledger.negotiation_context(player_id)
            access_check()
            key = "actor:" + player_id
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                return ledger._actors[player_id]
            # Player priorities follow the player across clubs; relationships
            # remain team-specific. The write lock serializes first registration.
            existing = db.execute("SELECT payload FROM events WHERE kind='actor' AND request_key=? ORDER BY id LIMIT 1", (key,)).fetchone()
            if existing:
                actor["personality"] = json.loads(existing[0])["actor"]["personality"]
            payload = {"player_id": player_id, "actor": actor, "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'actor', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return actor

    @staticmethod
    def _apply_relationship(actor, key, delta):
        if actor is None or type(key) is not str or key not in actor["relationships"]:
            raise Rejected("Known actor relationship required")
        score = actor["relationships"][key]
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Relationship score must be within zero and one")
        if type(delta) not in (int, float) or not math.isfinite(delta) or delta == 0 or abs(delta) > 0.1:
            raise ValueError("Relationship change must be nonzero and at most 0.1")
        actor["relationships"][key] = round(max(0, min(1, score + delta)), 6)

    @staticmethod
    def _relationship_source(db, team, player, request, *, before_revision, before_event_id=None):
        for event_id, kind, serialized in db.execute("SELECT id,kind,payload FROM events WHERE team_id=? AND request_key IN (?, ?)",
                (team, "sign:" + request, "dialogue:" + request)):
            if before_event_id is not None and event_id >= before_event_id:
                continue
            data = json.loads(serialized)
            event = data["story"] if kind == "sign" else data["event"]
            if event is not None and event["offer"]["player_id"] == player and data["posting"]["revision"] <= before_revision:
                return
        raise Rejected("Recorded negotiation consequence required")

    def negotiation_inputs(self, team, player):
        with self._connection() as db:
            ledger = self._load(db, team)
            if player not in ledger._actors:
                raise Rejected("Registered actor required")
            return ledger._actors[player], ledger.negotiation_context(player)

    def update_relationship(self, team, request_id, player, relationship, delta, *, source_request_id, expected_revision):
        for value in (request_id, player, relationship, source_request_id):
            if type(value) is not str or not value.strip():
                raise ValueError("Stable relationship identities required")
        payload = dict(player_id=player, relationship=relationship, delta=delta, source_request_id=source_request_id)
        with self._connection(write=True) as db:
            ledger = self._load(db, team)
            key = "relationship:" + request_id
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team, key)).fetchone()
            if prior:
                previous = json.loads(prior[0])
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected("Relationship request already recorded differently")
                return previous["actor_after"]
            if type(expected_revision) is not int or expected_revision != ledger.revision:
                raise Rejected("Relationship change is based on stale franchise state")
            for (serialized,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind='relationship'", (team,)):
                previous = json.loads(serialized)
                if all(previous[field] == payload[field] for field in ("player_id", "relationship", "source_request_id")):
                    raise Rejected("Relationship consequence already applied")
            self._relationship_source(db, team, player, source_request_id, before_revision=ledger.revision)
            actor = ledger._actors.get(player)
            self._apply_relationship(actor, relationship, delta)
            ledger.revision += 1
            payload.update(actor_after=actor, posting=ledger.financial_snapshot())
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'relationship', ?)",
                       (team, key, json.dumps(payload, allow_nan=False)))
            return actor

    @staticmethod
    def _validate_story_evidence(story):
        if story is None or "evidence" not in story:
            return  # Existing/manual records carry no model evidence claim.
        from franchise.negotiation import validate_performance
        evidence = story["evidence"]
        if type(evidence) is not dict or set(evidence) != {"personality", "performance", "relationships", "financial_revision"}:
            raise ValueError("Complete model evidence snapshot required")
        if type(evidence["financial_revision"]) is not int or evidence["financial_revision"] < 0:
            raise ValueError("Evidence requires its observed financial revision")
        if any(type(evidence[field]) is not dict for field in ("personality", "performance", "relationships")):
            raise ValueError("Evidence context fields must be JSON objects")
        validate_performance(evidence)
        json.dumps(evidence, allow_nan=False)

    @staticmethod
    def _validate_dialogue(event):
        FranchiseStore._validate_story_evidence(event)
        if type(event) is not dict or event.get("outcome") not in {
                "counteroffer", "player_rejected", "accounting_rejected"}:
            raise ValueError("Noncommitted negotiation event required")
        if type(event.get("request_id")) is not str or not event["request_id"].strip():
            raise ValueError("Negotiation request ID required")
        from franchise.negotiation import Decision
        data = event["offer"]
        Offer.from_dict(data)
        counter = event.get("counter")
        decision = Decision.parse(json.dumps({"action": event["action"], "reason": event["reason"],
            "salaries": counter["salaries"] if counter else None,
            "signing_bonus": counter["signing_bonus"] if counter else None,
            "guaranteed_salaries": counter.get("guaranteed_salaries") if counter else None}), data["player_id"])
        expected = {"counter": "counteroffer", "reject": "player_rejected", "accept": "accounting_rejected"}
        if event["outcome"] != expected[decision.action] or (counter and counter["player_id"] != data["player_id"]):
            raise ValueError("Dialogue decision and outcome disagree")

    @staticmethod
    def _check_history(db, team_id, player_id, event):
        expected = event.get("history_request_ids")
        if expected is None:  # Historical/manual callers without model context.
            return
        if type(expected) is not list or any(type(key) is not str for key in expected):
            raise ValueError("Invalid negotiation history revision")
        actual = []
        for kind, serialized in db.execute("SELECT kind, payload FROM events WHERE team_id=? AND kind IN ('sign', 'dialogue') ORDER BY id", (team_id,)):
            payload = json.loads(serialized)
            previous = payload["event"] if kind == "dialogue" else payload["story"]
            if previous is not None and previous["offer"]["player_id"] == player_id:
                actual.append(previous["request_id"])
        if actual != expected:
            raise Rejected("Response was based on stale negotiation history")

    def record_negotiation(self, team_id, event, *, access_check):
        self._validate_dialogue(event)
        event = json.loads(json.dumps(event, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            access_check()
            key = "dialogue:" + event["request_id"]
            if db.execute("SELECT 1 FROM events WHERE team_id=? AND request_key=?",
                          (team_id, "sign:" + event["request_id"])).fetchone():
                raise Rejected("Request already belongs to a signing")
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if prior:
                recorded = json.loads(prior[0])["event"]
                if recorded != event:
                    raise Rejected("Negotiation request already recorded differently")
                return recorded
            if event.get("evidence") is not None and event["outcome"] != "accounting_rejected":
                if event["evidence"]["financial_revision"] != ledger.revision:
                    raise Rejected("Response was based on stale franchise context")
            self._check_history(db, team_id, event["offer"]["player_id"], event)
            payload = {"event": event, "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'dialogue', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return event

    def record_scouting(self, team_id, event, *, access_check):
        from franchise.draft import validate_scouting
        event = json.loads(json.dumps(event, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            key = "draft-scouting:" + event["request_id"]
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                previous = json.loads(row[0])["event"]
                if previous != event:
                    raise Rejected("Scouting request already recorded differently")
                access_check()
                return previous
            validate_scouting(event, ledger)
            access_check()  # Required inside the final durable transaction.
            payload = {"event": event, "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'draft_scouting',?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return event

    def recalled_scouting(self, team_id, request_id):
        with self._connection() as db:
            self._load(db, team_id)
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",
                             (team_id, "draft-scouting:" + request_id)).fetchone()
            return json.loads(row[0])["event"] if row else None

    def negotiation_history(self, team_id, player_id):
        with self._connection() as db:
            ledger = self._load(db, team_id)
            history = []
            for kind, serialized in db.execute("SELECT kind, payload FROM events WHERE team_id=? ORDER BY id", (team_id,)):
                payload = json.loads(serialized)
                if kind == "dialogue":
                    event = payload["event"]
                elif kind == "sign" and payload["story"] is not None:
                    event = {**payload["story"], "charges": payload["contract_charges"]}
                else:
                    continue
                if event["offer"]["player_id"] == player_id:
                    history.append(event)
            return history

    def recalled_negotiation(self, team_id: str, request_id: str, offer: Offer):
        with self._connection() as db:
            ledger = self._load(db, team_id)
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, "sign:" + request_id)).fetchone()
            if row is None:
                dialogue = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",
                                      (team_id, "dialogue:" + request_id)).fetchone()
                if dialogue is None:
                    return None
                event = json.loads(dialogue[0])["event"]
                if event["offer"] != json.loads(json.dumps(offer.to_dict())):
                    raise Rejected("Negotiation request already recorded with different terms")
                return event
            payload = json.loads(row[0])
            if payload["offer"] != json.loads(json.dumps(offer.to_dict())):
                raise Rejected("Negotiation request already committed with different terms")
            if payload["story"] is None:
                raise Rejected("Request belongs to a signing without negotiation history")
            receipt = ledger.sign(request_id, offer, ledger.revision)
            return {**payload["story"], "charges": [json_amount(value) for value in receipt.charges]}


class StoredLedger:
    """Negotiation-facing view; every operation reads current durable state."""
    def __init__(self, store: FranchiseStore, team_id: str):
        self.store, self.team_id = store, team_id
        store.load_team(team_id)

    def scouting_history(self):
        return self.store.load_team(self.team_id).scouting_history()

    def recalled_scouting(self, request_id):
        return self.store.recalled_scouting(self.team_id, request_id)

    def record_scouting(self, event, *, access_check):
        return self.store.record_scouting(self.team_id, event, access_check=access_check)

    def management_context(self):
        return self.store.load_team(self.team_id).management_context()

    def negotiation_context(self, player_id):
        return self.store.load_team(self.team_id).negotiation_context(player_id)

    def preview_offer(self, offer, expected_revision):
        return self.store.preview_offer(self.team_id, offer, expected_revision)

    def commit_negotiation(self, request_id, offer, expected_revision, *, access_check, story):
        return self.store.sign(self.team_id, request_id, offer, expected_revision,
                               access_check=access_check, story=story)

    def bind_actor(self, player_id, personality, relationships, *, access_check):
        return self.store.bind_actor(self.team_id, player_id, personality, relationships,
                                     access_check=access_check)

    def negotiation_inputs(self, player_id, actor):
        return self.store.negotiation_inputs(self.team_id, player_id)

    def record_negotiation(self, event, *, access_check):
        return self.store.record_negotiation(self.team_id, event, access_check=access_check)

    def negotiation_history(self, player_id):
        return self.store.negotiation_history(self.team_id, player_id)

    def recalled_negotiation(self, request_id, offer):
        return self.store.recalled_negotiation(self.team_id, request_id, offer)

    @property
    def room(self):
        return self.store.load_team(self.team_id).room
