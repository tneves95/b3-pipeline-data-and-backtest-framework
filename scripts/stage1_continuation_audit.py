"""Offline sensitivities and immutable-prefix checks, without resetting portfolios."""
import hashlib
import itertools
import json
from datetime import date
from stage1_resume import ROOT, OUT, resume, selection, dump, prices, read, gzread, DATES


def verify_frozen():
    for r in json.loads((OUT/'continuation_immutable_inputs.json').read_text()):
        if hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']:
            raise ValueError(('Accepted baseline changed',r['path']))


def main():
    verify_frozen()
    base={p:resume(p,verbose=False)[0] for p in ['R03 B2','B00S B2','B00S BH+entradas']}
    unknown=tuple((y,t) for y in range(2016,2020)
                  for t,s in sorted(selection('R03',y)[0].items()) if s=='INDETERMINATE')
    outcomes=[];paths=[]
    for mask in itertools.product((False,True),repeat=len(unknown)):
        overrides=tuple(u for u,on in zip(unknown,mask) if on)
        a=resume('R03 B2',overrides,save=False,verbose=False)[0]
        label=';'.join(f'{y}:{t}' for y,t in overrides) or 'EVIDENCE_ONLY_BASE'
        outcomes.append(dict(case=label,portfolio='R03 B2',final_pct=a[-1]['cumulative_pct'],
            difference_from_base_pp=a[-1]['cumulative_pct']-base['R03 B2'][-1]['cumulative_pct']))
        paths.extend(dict(case=label,**r) for r in a)
    dump('r03_selection_scenarios.csv',outcomes)
    dump('r03_selection_scenario_paths.csv',paths)
    sensitivities=[]
    def case(label,p,**kw):
        a=resume(p,save=False,verbose=False,**kw)[0]
        sensitivities.append(dict(case=label,portfolio=p,final_pct=a[-1]['cumulative_pct'],
            difference_from_base_pp=a[-1]['cumulative_pct']-base[p][-1]['cumulative_pct'],
            largest_annual_difference_pp=max(abs(r['return_pct']-b['return_pct']) for r,b in zip(a,base[p]))))
    for p in ['B00S B2','B00S BH+entradas']:
        case('IRBR3_PASS_2018_UNPROVED_FY2013',p,overrides=((2018,'IRBR3'),))
        case('OMIT_DOCUMENTED_RIGHTS_AFTER_ACCEPTED_PREFIX',p,
             event_transform=lambda es:[e for e in es if e['kind'] not in ('RIGHT','RIGHT_REINVEST')])
        for sign in (-1,1):
            case(f'GETI_TIM_ROUNDING_{sign:+}',p,event_transform=lambda es,s=sign:[
                dict(e,amount=e['amount']+s*.00005) if e['id']=='GETI_DIST_20150810'
                or (e['id'].startswith('TIMP_GROSS') and e['ex_date']<'2018') else e for e in es])
    def legacy_lineage(year,status,targets):
        if 2021<=year<=2024:
            for t in ('AESB3','TIMS3'): status[t]='FAIL'
        if year==2025:status['TRPL4']='FAIL'
        return status,targets
    case('DIAGNOSTIC_FALSE_FAIL_NEW_CNPJ_OR_RENAMED_TICKER','B00S B2',decision_transform=legacy_lineage)
    case('OMIT_DOCUMENTED_RIGHTS_AFTER_ACCEPTED_PREFIX','R03 B2',
         event_transform=lambda es:[e for e in es if e['kind'] not in ('RIGHT','RIGHT_REINVEST')])
    dump('continuation_sensitivities.csv',sensitivities)
    unresolved=[]
    for strategy,years in [('R03',range(2016,2020)),('B00S',range(2017,2020))]:
        for y in years:
            status,targets=selection(strategy,y)
            for t,s in sorted(status.items()):
                if s=='INDETERMINATE':unresolved.append(dict(strategy=strategy,year=y,ticker=t,
                    treatment='NO_NEW_ENTRY; INHERITED_POSITION_RETAINED',
                    sensitivity='128 R03 entry combinations' if strategy=='R03' else
                    'Full path inclusion scenario' if t=='IRBR3' else 'FY2014 missing; no certified inclusion path'))
    dump('continuation_unresolved_selections.csv',unresolved)
    inventory_rights()
    verify_frozen()
    print('Immutable inputs preserved; R03 scenarios:',len(outcomes))


def inventory_rights():
    """Quantify observed exposure, not an invented entitlement or error bound."""
    quote,_=prices(); events=gzread(OUT/'cache/continuation_events.json.gz')
    covered={(e['ticker'],e['ex_date'][:4]) for e in events if e['kind']=='RIGHT_REINVEST'}
    rows=[]
    for portfolio,stem in [('B00S B2','b00s_b2_continuation'),('B00S BH+entradas','b00s_bh_continuation')]:
        positions=read(OUT/(stem+'_positions.csv'));ledger=read(OUT/(stem+'_ledger.csv'))
        for t in sorted({t for t,d in quote if len(t)==5 and t[-1] in '12'}):
            parent=t[:4]+('4' if t[-1]=='2' else '3')
            ds=sorted(d for u,d in quote if u==t and d>DATES[2015])
            for i,d in enumerate(ds):
                if i and (date.fromisoformat(d)-date.fromisoformat(ds[i-1])).days<=60:continue
                if (t,d[:4]) in covered:continue
                year=int(d[:4])-(d[5:7]<'07');start=DATES[year]
                units={r['ticker']:float(r['units']) for r in positions if r['date']==start and r['phase']=='AFTER_REVIEW'}
                for r in ledger:
                    if start<r['date']<=d:
                        if float(r['units_after']):units[r['ticker']]=float(r['units_after'])
                        else:units.pop(r['ticker'],None)
                # A TIET unit contains one ON and four PN rights.
                n=units.get(parent,0)
                if t.startswith('TIET') and 'TIET11' in units:n+=units['TIET11']*(4 if t[-1]=='2' else 1)
                if not n:continue
                nav=sum(v*quote[u,d] for u,v in units.items())
                rows.append(dict(portfolio=portfolio,parent=parent,right=t,first_observed_date=d,
                    right_close=quote[t,d],parent_units=n,index_total=nav,
                    instantaneous_pp_per_one_right_per_share=100*n*quote[t,d]/nav,
                    status='QUANTITY_OR_RECORD_DATE_NOT_RECONCILED; COEFFICIENT_IS_NOT_A_BOUND'))
    dump('continuation_unresolved_rights.csv',rows)


if __name__=='__main__':main()
