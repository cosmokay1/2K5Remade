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
    complete_window: bool | None = None

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in (self.goal_id,self.window,self.source,self.coverage,self.context)):
            raise ValueError('Goal identity, observation coverage and context required')
        if self.complete_window is not None and type(self.complete_window) is not bool:
            raise ValueError('Explicit goal observation completeness flag required')
        if self.value is not None and (type(self.value) is not int):
            raise ValueError('Observed integer value or explicit unknown required')


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
    complete = True
    results = []
    for goal in goals:
        observed = evidence.get(goal.goal_id)
        if observed is not None and observed.window != goal.window:
            raise ValueError('Observation window differs from agreed goal')
        complete = complete and not (observed is not None and observed.complete_window is False)
        value = observed.value if observed is not None else None
        if value is not None and value < 0 and goal.metric not in {'receiving_yards','rushing_yards','passing_yards'}:
            raise ValueError('Opportunity/start/win counts cannot be negative')
        ratio = max(Fraction(0),min(Fraction(value,goal.target),Fraction(1))) if value is not None else None
        if ratio is not None:
            achieved_weight += ratio * goal.importance
            known_weight += goal.importance
        status = ('unknown' if ratio is None else 'incomplete' if window_closed and observed.complete_window is False else 'achieved' if ratio == 1 else 'missed' if window_closed else 'in_progress')
        results.append({'goal_id':goal.goal_id,'metric':goal.metric,'target':goal.target,'importance':goal.importance,
                        'window':goal.window,'agreement_source':goal.source,'observed':value,'achievement':str(ratio) if ratio is not None else None,
                        **({'complete_window':observed.complete_window} if observed is not None and observed.complete_window is not None else {}),
                        'status':status,'evidence_source':observed.source if observed else None,
                        'coverage':observed.coverage if observed else 'unavailable', 'context':observed.context if observed else 'No observation supplied'})
    return {'window_closed':window_closed,'goals':results,'coverage':str(Fraction(known_weight,total_weight)),
            'observed_progress':str(achieved_weight/known_weight) if known_weight else None,
            'final_achievement_score':str(achieved_weight/total_weight) if window_closed and known_weight == total_weight and complete else None,
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


@dataclass(frozen=True)
class TeamResults:
    team_id: str
    window: str
    mode: str
    wins: int | None
    games: int | None
    source: str
    coverage: str
    unavailable_reason: str | None = None
    complete_window: bool = False

    def __post_init__(self):
        from franchise.performance import MODES
        if type(self.complete_window) is not bool:
            raise ValueError('Team coverage completeness flag required')
        if any(type(v) is not str or not v.strip() for v in (self.team_id,self.window,self.source,self.coverage)) or self.mode not in MODES:
            raise ValueError('Identified team results with source and simulation mode required')
        for value in (self.wins,self.games):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('Observed nonnegative team counts required')
        if self.wins is None:
            if type(self.unavailable_reason) is not str or not self.unavailable_reason.strip():
                raise ValueError('Unavailable wins require a reason')
        elif self.unavailable_reason is not None:
            raise ValueError('Known wins cannot also be unavailable')
        if self.wins is not None and self.games is not None and self.wins > self.games:
            raise ValueError('Team wins exceed observed games')


def observe_promises(goals, performance, *, player_id, team_id, context, team_results=None):
    """Map measured counters without deriving starts/targets/pressures from outcomes."""
    from franchise.performance import PerformanceEvidence
    import json
    if not isinstance(performance,PerformanceEvidence) or performance.player_id != player_id:
        raise ValueError('Matching typed player performance required')
    if type(team_id) is not str or not team_id.strip() or type(context) is not str or not context.strip():
        raise ValueError('Team identity and health/coaching context required')
    if type(goals) is not tuple or any(not isinstance(g,PromiseGoal) for g in goals):
        raise ValueError('Immutable typed agreed goals required')
    if team_results is not None and (not isinstance(team_results,TeamResults) or team_results.team_id != team_id):
        raise ValueError('Matching typed team results required')
    if performance.team_id is not None and performance.team_id != team_id:
        raise ValueError('Player evidence belongs to another team')
    counters={o.counter:o for o in performance.observations}
    results=[]
    for goal in goals:
        if goal.window != performance.window:
            raise ValueError('Player evidence does not cover the agreed goal window')
        if goal.metric == 'team_wins':
            if team_results is not None and (team_results.window != goal.window or team_results.mode != performance.mode):
                raise ValueError('Team and player evidence windows/modes disagree')
            complete=team_results.complete_window if team_results else False
            value=team_results.wins if team_results else None
            source=team_results.source if team_results else 'team results unavailable'
            coverage=team_results.coverage if team_results else 'no team result observation supplied'
            detail=(team_results.unavailable_reason or '') if team_results else 'Wins cannot be inferred from player stats'
        else:
            complete=performance.complete_window is True and performance.team_id == team_id
            names=('rush_attempts','receptions') if goal.metric == 'touches' else ('games_started',) if goal.metric == 'starts' else (goal.metric,)
            records=[counters.get(name) for name in names]
            value=sum(r.value for r in records) if all(r is not None and r.value is not None for r in records) else None
            source=json.dumps({name:r.source if r else None for name,r in zip(names,records)},sort_keys=True)
            coverage=performance.coverage
            detail='; '.join(name+': '+(r.unavailable_reason or 'observed') if r else name+': not recorded' for name,r in zip(names,records))
        results.append(GoalObservation(goal.goal_id,goal.window,value,source,coverage,
                       context+'; mode='+performance.mode+'; '+detail,complete_window=complete))
    return tuple(results)


def observe_promise_windows(goals, performances, *, player_id, team_id, context, team_results=()):
    """Map separate declared windows; never sum overlapping snapshots or modes."""
    from franchise.performance import PerformanceEvidence
    if type(goals) is not tuple or not goals or any(not isinstance(g,PromiseGoal) for g in goals):
        raise ValueError('Immutable agreed goals required')
    if len({g.goal_id for g in goals}) != len(goals):
        raise ValueError('Unique goal identities required')
    if type(performances) is not tuple or not performances or any(not isinstance(p,PerformanceEvidence) for p in performances):
        raise ValueError('Immutable typed performance windows required')
    if type(team_results) is not tuple or any(not isinstance(t,TeamResults) for t in team_results):
        raise ValueError('Immutable typed team windows required')
    by_window = {p.window:p for p in performances}
    teams = {t.window:t for t in team_results}
    windows = {g.window for g in goals}
    if len(by_window) != len(performances) or len(teams) != len(team_results):
        raise ValueError('Ambiguous duplicate window snapshots or simulation modes')
    if set(by_window) != windows or not set(teams) <= windows:
        raise ValueError('Exactly one player snapshot per agreed window required')
    observed = {}
    for window,performance in by_window.items():
        subset = tuple(g for g in goals if g.window == window)
        for observation in observe_promises(subset,performance,player_id=player_id,team_id=team_id,
                                           context=context,team_results=teams.get(window)):
            observed[observation.goal_id] = observation
    return tuple(observed[g.goal_id] for g in goals)
