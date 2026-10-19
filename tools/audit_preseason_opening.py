"""Read-only preseason opening readiness; never backdate a later source book."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from tools.reconcile_pack_contract_source import reconcile_source
from tools.inspect_franchise_cap import inspect_cap
from tools.franchise_snapshot_bindings import binding_money_scale


def audit_opening(bindings,payload,contract_source,*,team,cutoff):
    day=date.fromisoformat(cutoff)
    report=reconcile_source(bindings,payload,contract_source)
    if day.year!=report['start_year'] or team not in report['teams']:
        raise ValueError('Opening cutoff and club must match the saved league')
    snapshot=inspect_cap(payload);scale=binding_money_scale(bindings)
    club=snapshot['teams'][team];source_day=date.fromisoformat(report['as_of'][:10])
    unresolved=report['teams'][team]['unresolved']
    blockers=['Dated preseason roster membership and complete retained/non-roster obligations are not supplied']
    if source_day>day:
        blockers.append('Contract snapshot was updated after the preseason cutoff; it cannot establish opening liabilities')
    if unresolved:
        blockers.append(f'{len(unresolved)} saved contracts do not reconcile with the supplied dated source')
    return dict(format=1,team=team,season_year=day.year,opening_cutoff=cutoff,
        source_as_of=report['as_of'],source_sha256=report['audit_sha256'],
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        saved_league_cap=snapshot['league_cap_dollars']*scale,
        saved_roster_payroll=club['roster_payroll_dollars']*scale,
        saved_cap_room=club['room_if_team_adjustment_requested_dollars']*scale,
        saved_first_year_accumulator=club['original_first_year_accumulator_dollars']*scale,
        retained_liabilities_known=False,complete_opening_books=False,ready_for_signing_test=False,
        write_authorized=False,blockers=blockers,unresolved_contracts=unresolved)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('save','bindings','contract_audit'):p.add_argument(name,type=Path)
    p.add_argument('--team',required=True);p.add_argument('--cutoff',required=True)
    args=p.parse_args()
    try:
        report=audit_opening(json.loads(args.bindings.read_text()),args.save.read_bytes(),
            args.contract_audit.read_bytes(),team=args.team,cutoff=args.cutoff)
    except (OSError,ValueError,KeyError) as error:p.error(str(error))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
