"""Explicit durable request budgets for live franchise runtimes."""
from pathlib import Path
from franchise.inference_budget import InferenceBudget


def runtime_request_budget(database,budget_database,scope,request_limit,token_limit=None):
    if (not isinstance(database,(str,Path)) or not str(database).strip()
            or not isinstance(budget_database,(str,Path)) or not str(budget_database).strip()
            or str(budget_database)==':memory:'):
        raise ValueError('Separate persistent AI budget database required')
    franchise=Path(database).resolve();budget=Path(budget_database).resolve()
    if franchise==budget or (franchise.exists() and budget.exists() and franchise.samefile(budget)):
        raise ValueError('AI usage database must be separate from franchise data')
    return InferenceBudget(budget,scope=scope,request_limit=request_limit,token_limit=token_limit)
