"""Immutable team-book identity, independent of contract terms and payments."""
from dataclasses import dataclass
import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from franchise.books import ActiveContract
    from franchise.releases import ReleasePlan
    from franchise.trades import TradePlan
    from franchise.restructures import RestructurePlan


@dataclass(frozen=True)
class GenerationIdentity:
    generation_id: str
    player_id: str
    cash_obligation_id: str

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in
               (self.generation_id,self.player_id,self.cash_obligation_id)):
            raise ValueError('Stable contract generation, player and cash identities required')


def legacy_identity(team_id, player_id):
    if any(type(value) is not str or not value.strip() for value in (team_id,player_id)):
        raise ValueError('Stable team and player identities required')
    material = json.dumps([team_id,player_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return GenerationIdentity('legacy-contract:' + hashlib.sha256(material).hexdigest(),
                              player_id,'contract:' + player_id)


@dataclass(frozen=True)
class GenerationAgreement:
    """One immutable agreement version; cash settlement stays in its cash book."""
    identity: GenerationIdentity
    original_contract: "ActiveContract"
    contract: "ActiveContract"
    release: "ReleasePlan | None" = None
    outgoing_trade: "TradePlan | None" = None
    incoming_trade: "TradePlan | None" = None
    restructure: "RestructurePlan | None" = None

    def __post_init__(self):
        from franchise.books import ActiveContract
        if (not isinstance(self.identity, GenerationIdentity)
                or not isinstance(self.original_contract, ActiveContract)
                or not isinstance(self.contract, ActiveContract)
                or self.original_contract.offer.player_id != self.identity.player_id
                or self.contract.offer.player_id != self.identity.player_id
                or (self.release is not None and self.outgoing_trade is not None)):
            raise ValueError('Typed consistent generation agreement required')
        from franchise.releases import ReleasePlan
        from franchise.trades import TradePlan
        from franchise.restructures import RestructurePlan
        for plan, kind in ((self.release, ReleasePlan), (self.outgoing_trade, TradePlan),
                           (self.incoming_trade, TradePlan), (self.restructure, RestructurePlan)):
            if plan is not None and not isinstance(plan, kind):
                raise ValueError('Typed generation lifecycle plan required')
        if ((self.release is not None and self.release.original_contract != self.contract)
                or (self.outgoing_trade is not None and self.outgoing_trade.original_contract != self.contract)
                or (self.restructure is not None and (self.restructure.contract != self.contract
                    or self.restructure.original_contract != self.original_contract))
                or (self.incoming_trade is not None and self.incoming_trade.buyer_contract != self.original_contract)):
            raise ValueError('Generation lifecycle plan disagrees with agreement')

    @property
    def status(self):
        return 'released' if self.release is not None else 'assigned' if self.outgoing_trade is not None else 'active'

    @property
    def retained_records(self):
        if self.release is not None:
            return self.release.retained
        return (self.outgoing_trade.retained_bonus,) if self.outgoing_trade is not None else ()

    def annual_charges(self):
        from fractions import Fraction
        if self.status == 'active':
            return self.contract.charges()
        records = self.retained_records
        return tuple(sum((r.annual_charges[i] if i < len(r.annual_charges) else Fraction(0)
                          for r in records), Fraction(0))
                     for i in range(max((len(r.annual_charges) for r in records), default=0)))

    def payment_ceilings(self):
        ceilings = self.contract.compensation_components()
        if self.status != 'active':
            guarantees = self.contract.offer.guaranteed_salaries or (0,) * len(self.contract.offer.salaries)
            for i in range(self.contract.elapsed_years, len(guarantees)):
                ceilings['base:' + str(i)] = guarantees[i] if self.status == 'released' else 0
        return ceilings
