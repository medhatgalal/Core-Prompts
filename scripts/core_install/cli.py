"""Install/repair/update command shared by shell wrappers and the capsule."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import planner, providers, transaction


def main(argv=None):
    parser=argparse.ArgumentParser(description='Preview, repair and maintain Core-Prompts skills and agents safely.')
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--allow-nonlocal-target',action='store_true')
    parser.add_argument('--cli',choices=(*providers.PROVIDERS,'all'),default='all')
    parser.add_argument('--slug',action='append',default=[])
    parser.add_argument('--profile',type=Path)
    parser.add_argument('--repair',action='store_true',help='Discover and adopt recognized installed packages, including agents on selected providers')
    parser.add_argument('--with-agents',action='store_true',help='Select current agent packages as well as skills for explicit installation')
    parser.add_argument('--surface-only',action='store_true',help='Manage selected surfaces without updater/launcher refresh (requires --slug)')
    parser.add_argument('--strict-cli',action='store_true')
    parser.add_argument('--dry-run',action='store_true',help='Print the exact JSON plan without target writes')
    parser.add_argument('--apply-plan',type=Path)
    parser.add_argument('--rollback',help='Restore a transaction ID, preserving later edits')
    parser.add_argument('--list-transactions',action='store_true')
    args=parser.parse_args(argv)
    try:
        repo,target=args.repo.expanduser().absolute(),args.target.expanduser().absolute()
        if args.apply_plan and (args.dry_run or args.rollback):
            raise ValueError('INVALID_REQUEST: apply-plan cannot combine with dry-run or rollback')
        if args.surface_only and not args.slug:
            raise ValueError('INVALID_REQUEST: --surface-only requires --slug')
        if args.profile and (args.cli!='all' or args.slug or args.surface_only):
            raise ValueError('INVALID_REQUEST: profile cannot combine with CLI/slug/surface-only selection')
        if args.list_transactions:
            rows=[]
            root=transaction.safe(target,transaction.TRANSACTIONS)
            if root.exists():
                for p in sorted(root.iterdir()):
                    journal=transaction.safe(root,p.name+'/journal.json')
                    if journal.is_file():
                        value=json.loads(journal.read_text());rows.append({'transaction':p.name,'status':value.get('status')})
            print(json.dumps(rows,indent=2));return 0
        if args.rollback:
            result=transaction.rollback(target,args.rollback,args.dry_run)
            print(json.dumps(result,indent=2));return 0
        if args.apply_plan:
            approved=json.loads(args.apply_plan.read_text())
            request=approved['request']
        else:
            state=planner.read_state(target)
            saved=planner.read_json(target,planner.V1_PROFILE) if not state else None
            profile=json.loads(args.profile.read_text()) if args.profile else None
            if args.profile is not None and (not isinstance(profile,dict) or profile.get('schema')!=1 or profile.get('scope')!='skills'):
                raise ValueError('INVALID_PROFILE: expected schema1 skills profile')
            if state is None and transaction.safe(target,planner.V1_PROFILE).exists() and (not isinstance(saved,dict) or saved.get('schema')!=1 or saved.get('scope')!='skills'):
                raise ValueError('INVALID_PROFILE: invalid saved profile')
            request={'mode':'repair' if args.repair or (not state and not saved) else 'sync'}
            if args.profile is not None:
                request.update(profile=profile,providers=profile['targets'],mode='repair')
            elif args.cli!='all':
                request['providers']=[args.cli]
            elif args.repair and saved:
                request['providers']=saved['targets']
            elif not state and not saved:
                binaries={'codex':'codex','kiro':'kiro-cli','claude':'claude','gemini':'gemini','grok':'grok'}
                selected=[p for p,binary in binaries.items() if shutil.which(binary) or (target/f'.{p}/skills').is_dir() or (target/f'.{p}/agents').is_dir() or (p=='codex' and (target/'.agents/skills').is_dir())]
                if not selected:
                    raise ValueError('NO_PROVIDERS: select --cli for an offline or fresh installation')
                request['providers']=selected
            if args.strict_cli:
                strict_providers=request.get('providers')
                if strict_providers is None:
                    strict_providers=saved['targets'] if saved else sorted({k.split(':')[0] for k in state['selection']})
                for p in strict_providers:
                    binary='kiro-cli' if p=='kiro' else p
                    if not shutil.which(binary):
                        raise ValueError('MISSING_CLI: '+binary)
            if args.slug:
                from .catalog import SUCCESSORS
                slugs=[SUCCESSORS.get(s,s) for s in args.slug]
                if None in slugs:
                    request['mode']='repair'
                    request['legacy_slugs']=args.slug
                else:
                    request.update(mode='install',slugs=slugs,kinds=['skill','agent'])
            elif args.with_agents:
                request.update(mode='install',kinds=['skill','agent'])
            request['runtime']=not args.surface_only
            approved=planner.plan(repo,target,request)
        if args.dry_run:
            print(json.dumps(approved,indent=2,sort_keys=True));return 0
        if approved['blockers']:
            print(json.dumps({'status':'blocked','blockers':approved['blockers'],'preserved':approved['preserved']},indent=2));return 1
        result=transaction.apply(repo,target,approved,lambda:planner.plan(repo,target,request))
        print(json.dumps(result,indent=2))
        return 2 if result.get('preserved') else 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'blocked','code':getattr(exc,'code','invalid-installation'),
                          'error':str(exc),'transaction':getattr(exc,'transaction',None)}),file=sys.stderr)
        return 1
