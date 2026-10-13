"""Read-only draft comparison evidence; does not exercise a pick or reserve money."""
import json
from dataclasses import dataclass
from franchise.cap import Offer, Rejected
from franchise.negotiation import validate_performance
from franchise.performance import PerformanceEvidence


@dataclass(frozen=True)
class Prospect:
    player_id: str
    position: str
    role: str
    competition: str
    source: str
    evidence: tuple[PerformanceEvidence, ...]
    personality: dict
    personality_source: str
    contract_estimate: Offer
    contract_source: str

    def to_context(self):
        for value in (self.player_id, self.position, self.role, self.competition,
                      self.source, self.personality_source, self.contract_source):
            if type(value) is not str or not value.strip():
                raise ValueError('Prospect identity, context and provenance required')
        if type(self.evidence) is not tuple or any(not isinstance(item, PerformanceEvidence) or item.player_id != self.player_id for item in self.evidence):
            raise ValueError('Typed prospect-owned observation windows required')
        if not self.evidence:
            raise ValueError('Declare observed or explicitly unavailable prospect evidence')
        if type(self.personality) is not dict:
            raise ValueError('Sourced personality object required')
        if not isinstance(self.contract_estimate, Offer) or self.contract_estimate.player_id != self.player_id:
            raise ValueError('Prospect-owned contract estimate required')
        result = {'player_id': self.player_id, 'position': self.position, 'role': self.role,
                  'competition': self.competition, 'source': self.source,
                  'performance': [item.to_context() for item in self.evidence],
                  'personality': self.personality, 'personality_source': self.personality_source,
                  'contract_estimate': self.contract_estimate.to_dict(), 'contract_source': self.contract_source}
        validate_performance(result)
        return json.loads(json.dumps(result, allow_nan=False))


def comparison_context(ledger, *, expected_revision, draft_round, overall_pick,
                       prospects, team_needs):
    """Evaluate candidates separately against one revision; offers are estimates.

    Prospect registration/slot assignment must be supplied by a verified adapter.
    Estimates are neither contract commitments nor proof that all future picks fit.
    """
    if type(draft_round) is not int or not 1 <= draft_round <= 7:
        raise ValueError('Draft round must be 1 through 7')
    if type(overall_pick) is not int or overall_pick < 1:
        raise ValueError('Explicit overall pick required')
    if type(prospects) is not tuple or not prospects or any(not isinstance(item, Prospect) for item in prospects):
        raise ValueError('Immutable typed shortlist required')
    if len({item.player_id for item in prospects}) != len(prospects):
        raise ValueError('Duplicate prospect identity')
    if type(team_needs) is not list:
        raise ValueError('Sourced team needs required')
    for need in team_needs:
        if type(need) is not dict or set(need) != {'position', 'role', 'reason', 'source'} or any(type(v) is not str or not v.strip() for v in need.values()):
            raise ValueError('Team needs require position, role, reason and source')
    validate_performance(team_needs)
    needs = json.loads(json.dumps(team_needs, allow_nan=False))
    candidates = []
    for prospect in prospects:
        context = prospect.to_context()
        accounting = ledger.negotiation_context(prospect.player_id)
        if accounting['revision'] != expected_revision or type(expected_revision) is not int:
            raise Rejected('Draft comparison used stale franchise state')
        scale = accounting['rookie_scale']
        if accounting['rookie_type'] != 'drafted' or scale['draft_round'] != draft_round:
            raise ValueError('Candidate lacks matching sourced draft-slot rookie classification')
        try:
            preview = ledger.preview_offer(prospect.contract_estimate, expected_revision)
        except Rejected as exc:
            context['contract_validation'] = {'status': 'ineligible', 'reason': str(exc)}
        else:
            context['contract_validation'] = {'status': 'eligible', 'preview': preview}
        candidates.append(context)
    # Detect a concurrent update across separate durable reads. A later selection
    # will still need an atomic pick/reservation transaction at this revision.
    if ledger.negotiation_context(prospects[0].player_id)['revision'] != expected_revision:
        raise Rejected('Draft comparison used stale franchise state')
    return {'purpose': 'draft_comparison', 'financial_revision': expected_revision,
            'draft_round': draft_round, 'overall_pick': overall_pick,
            'team_needs': needs, 'prospects': candidates,
            'instructions': 'Compare observed production, opportunities, role, competition and sourced personality. Explain uncertainty and missing evidence. Do not infer hidden ratings or treat unavailable counters as zero. Contract estimates are independently previewed and do not reserve cap or rookie allocation.'}
