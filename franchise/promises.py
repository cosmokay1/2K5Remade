"""Nonfinancial negotiated-goal definitions and source-backed fulfillment scoring."""
from dataclasses import dataclass
from fractions import Fraction

METRICS = frozenset({'touches','starts','receiving_yards','rushing_yards','passing_yards','team_wins'})


@dataclass(frozen=True)
class PromiseGoal:
    goal_id: str
    metric: str
    target: int
    importance: int
    window: str
    source: str

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in (self.goal_id,self.window,self.source)) or self.metric not in METRICS:
            raise ValueError('Identified metric, performance window and agreement source required')
        if type(self.target) is not int or self.target <= 0 or type(self.importance) is not int or not 1 <= self.importance <= 100:
            raise ValueError('Positive target and authored importance from 1 through 100 required')


@dataclass(frozen=True)
class GoalObservation:
    goal_id: str
    window: str
    value: int | None
    source: str
    coverage: str
    context: str

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in (self.goal_id,self.window,self.source,self.coverage,self.context)):
            raise ValueError('Goal identity, observation coverage and context required')
        if self.value is not None and (type(self.value) is not int or self.value < 0):
            raise ValueError('Observed nonnegative count or explicit unknown required')


def score_promises(goals, observations, *, window_closed):
    """Achievement score measures promises, never a player's hidden ability.

    Touches must be observed carries plus receptions; targets are opportunities,
    not touches. Starts are actual starts; team wins are team outcomes. Context is
    retained for trust evaluation but does not invent excuses or adjust counters.
    """
    if type(window_closed) is not bool or type(goals) is not tuple or not goals or any(not isinstance(g,PromiseGoal) for g in goals):
        raise ValueError('Immutable goals and explicit period closure required')
    if len({g.goal_id for g in goals}) != len(goals):
        raise ValueError('Unique goal identities required')
    if type(observations) is not tuple or any(not isinstance(o,GoalObservation) for o in observations):
        raise ValueError('Immutable observed goal records required')
    evidence = {o.goal_id:o for o in observations}
    if len(evidence) != len(observations) or not evidence.keys() <= {g.goal_id for g in goals}:
        raise ValueError('Unique observations for agreed goals required')
    achieved_weight = Fraction(0)
    known_weight = 0
    total_weight = sum(g.importance for g in goals)
    results = []
    for goal in goals:
        observed = evidence.get(goal.goal_id)
        if observed is not None and observed.window != goal.window:
            raise ValueError('Observation window differs from agreed goal')
        value = observed.value if observed is not None else None
        ratio = min(Fraction(value,goal.target),Fraction(1)) if value is not None else None
        if ratio is not None:
            achieved_weight += ratio * goal.importance
            known_weight += goal.importance
        status = ('unknown' if ratio is None else 'achieved' if ratio == 1 else 'missed' if window_closed else 'in_progress')
        results.append({'goal_id':goal.goal_id,'metric':goal.metric,'target':goal.target,'importance':goal.importance,
                        'window':goal.window,'agreement_source':goal.source,'observed':value,'achievement':str(ratio) if ratio is not None else None,
                        'status':status,'evidence_source':observed.source if observed else None,
                        'coverage':observed.coverage if observed else 'unavailable', 'context':observed.context if observed else 'No observation supplied'})
    return {'window_closed':window_closed,'goals':results,'coverage':str(Fraction(known_weight,total_weight)),
            'observed_progress':str(achieved_weight/known_weight) if known_weight else None,
            'final_achievement_score':str(achieved_weight/total_weight) if window_closed and known_weight == total_weight else None,
            'financial_effect':None}


def goals_from_list(data):
    if type(data) is not list:
        raise ValueError('Complete promise goal list required')
    fields = {'goal_id','metric','target','importance','window','source'}
    if any(type(item) is not dict or set(item) != fields for item in data):
        raise ValueError('Unexpected promise goal fields')
    goals = tuple(PromiseGoal(**item) for item in data)
    if len({goal.goal_id for goal in goals}) != len(goals):
        raise ValueError('Unique promise identities required')
    return goals


GOAL_SCHEMA = {'type':'object','additionalProperties':False,
    'properties':{'goal_id':{'type':'string'},'metric':{'type':'string','enum':sorted(METRICS)},
                  'target':{'type':'integer'},'importance':{'type':'integer'},
                  'window':{'type':'string'},'source':{'type':'string'}},
    'required':['goal_id','metric','target','importance','window','source']}
