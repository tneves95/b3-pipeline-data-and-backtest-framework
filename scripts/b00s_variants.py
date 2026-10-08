"""PR #4 V2: offline selective-renewal experiment; PR #3 is read-only.

Selection consumes frozen PIT decisions. No outcome is an input to selection.
All values are dimensionless index units or percentages, never monetary capital.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, localcontext
from functools import lru_cache
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import statistics

from stage1_pit import ROOT, OUT, DATES, gzread
from stage1_resume import canonical, selection, prices, event_day
from stage1_continuity import renew_b2
from stage1_attribution import aggregate, attribute_day, assert_units, verify_frozen as verify_stage1

HOME = ROOT / 'research/b00s_four_variants_2014_2026'
INPUT = HOME / 'inputs'
RESULT = HOME / 'results'
BASE = ROOT / 'research/returns_2014_2026_results'
PROTOCOL_SHA = '7fea064530bd494fb3edf9410c63980908a2197c'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)

def jsonwrite(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_frozen():
    count=verify_stage1()
    path=INPUT/'protected_pr3.json'
    if path.exists():
        for r in json.loads(path.read_text())['files']:
            if sha(ROOT/r['path'])!=r['sha256']:raise ValueError(('PR3 changed',r['path']))
    return count

@lru_cache(maxsize=1)
def candidates():
    """Exactly the accepted control's PASS universe, not a rerun of its screener."""
    identities = {(int(r['year']), canonical(r['ticker'])): r for r in read(OUT/'identity_sector.csv')}
    legacy_sectors = {(int(r['year']), canonical(r['ticker'])):r['sector'] for r in read(BASE/'conditional_legacy_weights.csv') if r['strategy']=='B00S'}
    rows = []
    for year in range(2014, 2026):
        status, targets = selection('B00S', year)
        if year == 2014:
            targets = {r['ticker']: float(r['weight']) for r in read(OUT/'established_selections.csv')
                       if r['strategy'] == 'B00S' and r['year'] == '2014'}
        for t, weight in sorted(targets.items()):
            r = identities[year, t]
            rows.append(dict(year=year, cutoff=DATES[year], ticker=t, observed_ticker=r['ticker'],
                cnpj=r['cnpj'], company=r['company'], sector=legacy_sectors.get((year,t),r['besst']), base_status='PASS',
                base_target=weight, median_volume=float(r['median_volume']),
                sessions=int(r['sessions']), total_volume=float(r['total_volume']), close=float(r['close']),
                identity_source=r['identity_source'], sector_docid=r['sector_docid'],
                sector_received=r['sector_received']))
    return rows

@lru_cache(maxsize=1)
def identities():
    data = {}
    for r in read(OUT/'identity_sector.csv'):
        t = canonical(r['ticker'])
        if r['cnpj'] and r['besst']:
            data[t] = dict(cnpj=r['cnpj'], company=r['company'], sector=r['besst'])
    for r in candidates():
        data[r['ticker']] = {k:r[k] for k in ['cnpj','company','sector']}
    # Corporate descendants inherit the slot of their existing economic lineage.
    # XP is a compulsory spin-off, disclosed separately in issuer concentration.
    for child, parent in [('TIET11','GETI4'), ('TIET4','GETI4'), ('AESB3','GETI4'),
                          ('AURE3','GETI4'), ('TIMS3','TIMP3'), ('VIVT3','VIVT4'),
                          ('XPBR31','ITUB4'), ('AXIA7','ELET3')]:
        data[child] = dict(data[parent], lineage_parent=parent)
    return data

def weights(rows):
    sectors = {r['sector'] for r in rows}
    return {r['ticker']: 1/len(sectors)/sum(q['sector']==r['sector'] for q in rows) for r in rows}

def select_ten(rows, holdings, status, metadata=None):
    metadata = metadata or identities()
    surviving = {t for t in holdings if status.get(t) != 'FAIL'}
    occupied = defaultdict(set)
    for t in surviving:
        m = metadata[t]; occupied[m['sector']].add(m['cnpj'])
    chosen, decisions = [], []
    for sector in sorted({r['sector'] for r in rows}):
        ranked = sorted((r for r in rows if r['sector']==sector),
                        key=lambda r: (-r['median_volume'], -r['sessions'], -r['total_volume'], r['ticker']))
        for rank, r in enumerate(ranked, 1):
            held = r['cnpj'] in occupied[sector]
            admit = held or len(occupied[sector]) < 2
            reason = 'INCUMBENT_LINEAGE_RETAINED' if held else 'VACANT_SLOT_PIT_LIQUIDITY' if admit else 'SECTOR_SLOTS_OCCUPIED'
            if admit:
                occupied[sector].add(r['cnpj'])
                # No second class of an inherited legal/economic issuer.
                t = next((t for t in sorted(surviving) if metadata[t]['cnpj']==r['cnpj']), r['ticker'])
                chosen.append(dict(r, ticker=t))
            decisions.append(dict(year=r['year'], ticker=r['ticker'], variant='V10',
                                  decision='ELIGIBLE' if admit else 'EXCLUDED', reason=reason, liquidity_rank=rank))
    assert all(len(v)<=2 for v in occupied.values())
    return weights(chosen), decisions

def select_filtered(rows, holdings, decisions, variant):
    key = 'valuation_status' if variant.startswith('VVAL') else 'quality_category'
    allowed = {'PASS_MATURE','PASS_REINVESTOR'} if variant.startswith('VVAL') else {'QUALIFIED_HIGH','QUALIFIED_SATISFACTORY'}
    selected = [r for r in rows if decisions[r['year'],r['ticker']][key] in allowed]
    return represented_targets(selected, holdings)

def represented_targets(selected, holdings):
    targets = weights(selected)
    # Preserve the traded representation already owned, never buy its second class.
    for r in selected:
        old = next((t for t in holdings if identities()[t]['cnpj']==r['cnpj']), None)
        if old and old != r['ticker']:
            targets[old] = targets.pop(r['ticker'])
    return targets

@lru_cache(maxsize=1)
def market():
    q, _ = prices(); q = q.copy()
    for y in (2014,2015):
        for r in gzread(OUT/f'cache/b00s_initial_quotes_{y}.json.gz')['quotes']:
            k=canonical(r['ticker']),r['date']
            if k in q and q[k]!=r['close']:
                raise ValueError(('Incompatible accepted quote', k))
            q[k]=r['close']
    events = gzread(OUT/'cache/b00s_initial_events.json.gz') + [
        e for e in gzread(OUT/'cache/continuation_events.json.gz') if e['ex_date']>DATES[2015]]
    if len({e['id'] for e in events}) != len(events):
        raise ValueError('Duplicate accepted event')
    bydate=defaultdict(list)
    for e in events: bydate[e['ex_date']].append(e)
    return q, bydate

def concentration(variant, year, phase, values):
    nav=math.fsum(values.values()); issuer=defaultdict(float); sector=defaultdict(float); slots=set()
    for t,v in values.items():
        m=identities()[t]
        # The XP spin-off is its own issuer for economic concentration, and an
        # inherited ITUB slot for the constrained entry rule.
        company='XP_SPINOFF' if t=='XPBR31' else m['cnpj']
        issuer[company]+=v/nav; sector['Outros (cisão)' if t=='XPBR31' else m['sector']]+=v/nav
        slots.add((m['sector'],m['cnpj']))
    ws=sorted(issuer.values(),reverse=True)
    return dict(variant=variant,year=year,date=DATES[year],phase=phase,securities=len(values),
        companies=len(issuer),eligible_lineage_slots=len(slots),sectors=len(sector),
        largest_company_pct=100*ws[0],top5_pct=100*sum(ws[:5]),
        issuer_hhi=sum(w*w for w in ws),sector_hhi=sum(w*w for w in sector.values()),
        sector_weights_pct=json.dumps({s:100*w for s,w in sorted(sector.items())},ensure_ascii=False,sort_keys=True))

def simulate(variant, frozen=None, include=None):
    quote, bydate=market(); units={}; annual=[]; holdings=[]; positions=[]; reviews=[]; risk=[]; decisions=[]; transfers=[]
    cands=candidates(); frozen=frozen or {}
    for year in range(2014,2026):
        start,end=DATES[year],DATES[year+1]
        rows=[r for r in cands if r['year']==year]
        status,base_targets=selection('B00S',year); status=status.copy()
        if year==2014: base_targets={r['ticker']:r['base_target'] for r in rows}; status.update({t:'PASS' for t in base_targets})
        if 'TIET11' in units: status['TIET11']=status.get('TIET4','INDETERMINATE')
        before={t:n*quote[t,start] for t,n in units.items()}
        if variant=='V0':
            targets=base_targets.copy()
            if 'TIET11' in units and 'TIET4' in targets: targets['TIET11']=targets.pop('TIET4')
        elif variant=='V10':
            targets,d=select_ten(rows,before,status);decisions.extend(d)
        else:
            targets=select_filtered(rows,before,frozen,variant)
            if include:
                selected=[r for r in rows if any(identities()[t]['cnpj']==r['cnpj'] for t in targets) or include(r,frozen[r['year'],r['ticker']])]
                targets=represented_targets(selected,before)
        if not units:
            if year!=2014 or not targets:
                annual.append(dict(variant=variant,year=year,start=start,end=end,return_pct='',cumulative_pct='',status='NOT_FORMED'))
                continue
            after=targets;review=[dict(ticker=t,before=0,after=w,change=w,reason='FORMATION') for t,w in targets.items()]
        else:
            # Representation-equivalent candidates inherit their PASS source.
            for t in targets:
                if t not in base_targets and t in units and status.get(t)!='FAIL':status[t]='PASS'
            after,review=renew_b2(before,status,targets)
            if any(v<=0 and status.get(t)!='FAIL' for t,v in after.items()):
                raise ValueError(('UNRESOLVED_ENTRY_FUNDING_WOULD_LIQUIDATE_NONFAIL',variant,year))
        nav=math.fsum(after.values());units={t:v/quote[t,start] for t,v in after.items()}
        for r in review:reviews.append(dict(variant=variant,year=year,base_status=status.get(r['ticker'],'INDETERMINATE'),nav=nav,**r))
        risk.append(concentration(variant,year,'AFTER_REVIEW',after))
        for t,n in sorted(units.items()):positions.append(dict(variant=variant,date=start,phase='AFTER_REVIEW',ticker=t,units=n,weight_pct=100*after[t]/nav))
        sleeves={t:{t:n} for t,n in units.items()}; seen=defaultdict(set)
        for day, ev in sorted(bydate.items()):
            if not start<day<=end: continue
            spawned={e['successor'] for e in ev if e['kind']=='RIGHT' and e['ticker'] in units}
            relevant=[e for e in ev if e['ticker'] in units or e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned]
            if not relevant:continue
            for origin, u in sleeves.items():seen[origin].update(e['id'] for e in relevant if e['ticker'] in u)
            units=event_day(units,relevant,quote,day)
            sleeves,moved=attribute_day(sleeves,relevant,quote,day)
            transfers.extend(dict(variant=variant,year=year,**r) for r in moved)
            assert_units(aggregate(sleeves),units)
        final={t:n*quote[t,end] for t,n in units.items()};nav1=math.fsum(final.values())
        ret=100*(nav1/nav-1)
        annual.append(dict(variant=variant,year=year,start=start,end=end,return_pct=ret,cumulative_pct=100*(nav1-1),status='QUALIFIED_INHERITED_EVENTS'))
        risk.append(concentration(variant,year+1,'PERIOD_END',final))
        for t,n in sorted(units.items()):positions.append(dict(variant=variant,date=end,phase='PERIOD_END',ticker=t,units=n,weight_pct=100*final[t]/nav1))
        for t,v in sorted(after.items()):
            endvalue=math.fsum(n*quote[u,end] for u,n in sleeves[t].items());m=identities()[t]
            holdings.append(dict(variant=variant,year=year,start=start,end=end,row_type='HOLDING',ticker=t,
                cnpj='XP_SPINOFF' if t=='XPBR31' else m['cnpj'],company=m['company'] if t!='XPBR31' else 'XP (cisão compulsória)',
                sector=m['sector'],base_status=status.get(t,'INDETERMINATE'),initial_units=after[t]/quote[t,start],
                initial_weight_pct=100*v/nav,final_weight_pct=100*endvalue/nav1,exposure_return_pct=100*(endvalue/v-1),
                contribution_pp=100*(endvalue-v)/nav,descendants=';'.join(sorted(sleeves[t])),event_ids=';'.join(sorted(seen[t]))))
    return dict(annual=annual,holdings=holdings,positions=positions,reviews=reviews,risk=risk,decisions=decisions,transfers=transfers)

def reconcile(rows, annual):
    result=[]
    with localcontext() as ctx:
        ctx.prec=50
        for a in annual:
            group=[r for r in rows if r['variant']==a['variant'] and r['year']==a['year']]
            if a['return_pct']=='':continue
            residual=Decimal(str(a['return_pct']))-sum((Decimal(str(r['contribution_pp'])) for r in group),Decimal(0))
            if abs(residual)>Decimal('1e-9'):raise ValueError(('Attribution mismatch',a,residual))
            r={k:'' for k in group[0]};r.update(variant=a['variant'],year=a['year'],start=a['start'],end=a['end'],
                row_type='NUMERICAL_RESIDUAL',contribution_pp=str(residual))
            result.extend(group+[r])
    return result

def workbook():
    import xlsxwriter
    b=xlsxwriter.Workbook(RESULT/'b00s_four_variants.xlsx',{'strings_to_urls':False,'strings_to_formulas':False})
    b.set_properties({'title':'Experimento B00S V2','created':datetime(2026,10,8)})
    for filename in ['consolidated_pct','annual_returns_pct','cumulative_returns_pct','risk_concentration','turnover_by_year','holdings_by_june','selection_decisions','coverage_by_year_sector']:
        p=RESULT/(filename+'.csv')
        if not p.exists():continue
        rows=read(p);ws=b.add_worksheet(filename[:31]);keys=list(rows[0]);ws.freeze_panes(1,2)
        ws.write_row(0,0,keys);ws.autofilter(0,0,len(rows),len(keys)-1);ws.set_column(0,len(keys)-1,20)
        for i,r in enumerate(rows,1):
            for j,k in enumerate(keys):
                v=r[k]
                if k not in ('cnpj','ticker','company','descendants'):
                    try: v=float(v)
                    except ValueError:pass
                ws.write(i,j,v)
    b.close()

def publish(runs):
    RESULT.mkdir(parents=True,exist_ok=True)
    frozen=read(BASE/'annual_returns_pct.csv');frozen_cum=read(BASE/'cumulative_returns_pct.csv')
    annual=[r for v in runs.values() for r in v['annual']]
    # Replay checks the immutable control; publication retains its exact decimals.
    for a in runs['V0']['annual']:
        expected=frozen[a['year']-2014]['B00S B2']
        if not math.isclose(a['return_pct'],float(expected),abs_tol=1e-10):raise ValueError(('V0 mismatch',a,expected))
        a['return_pct']=expected
    ac=[];cu=[]
    for y in range(2014,2026):
        a=dict(year=y,start=DATES[y],end=DATES[y+1]);c=dict(closing_year=y+1,date=DATES[y+1])
        for v in ['V0','V10','VVAL','VQ']:
            r=next((r for r in annual if r['year']==y and r['variant']==v),None)
            a[v]=r['return_pct'] if r else '';c[v]=r['cumulative_pct'] if r else ''
        for v in ['IBOV','R03 B2','BH padrão']:a[v]=frozen[y-2014][v]
        # Derived reference accumulation is tied to the frozen annual decimals.
        for v in ['V0','IBOV','R03 B2','BH padrão']:
            key='B00S B2' if v=='V0' else v
            matches=[r for r in frozen_cum if r.get('year')==str(y+1) or r.get('end')==DATES[y+1] or r.get('date')==DATES[y+1]]
            c[v]=matches[0][key] if matches else 100*(math.prod(1+float(r[key])/100 for r in frozen[:y-2014+1])-1)
        ac.append(a);cu.append(c)
    write(RESULT/'annual_returns_pct.csv',ac);write(RESULT/'cumulative_returns_pct.csv',cu)
    write(RESULT/'portfolio_status.csv',[dict(variant=r['variant'],year=r['year'],status=r['status']) for r in annual])
    stats=[]
    for v in ['V0','V10','VVAL','VQ','IBOV','R03 B2','BH padrão']:
        vals=[float(r[v]) for r in ac if r[v]!=''];levels=[1]+[1+float(r[v])/100 for r in cu if r[v]!='']
        complete=len(vals)==12;final=100*(levels[-1]-1) if complete else ''
        stats.append(dict(variant=v,periods=len(vals),final_pct=final,cagr_pct=100*(levels[-1]**(1/12)-1) if complete else '',
            mean_annual_pct=statistics.mean(vals) if vals else '',median_annual_pct=statistics.median(vals) if vals else '',
            positive_years=sum(x>0 for x in vals) if vals else '',negative_years=sum(x<0 for x in vals) if vals else '',
            above_ibov_years=sum(float(r[v])>float(r['IBOV']) for r in ac) if complete else '',
            worst_year_pct=min(vals) if vals else '',best_year_pct=max(vals) if vals else '',
            annual_population_std_pct=statistics.pstdev(vals) if vals else '',
            annual_close_max_drawdown_pct=100*min(x/max(levels[:i+1])-1 for i,x in enumerate(levels)) if complete else '',
            vs_v0_pp=final-float(cu[-1]['V0']) if complete else '',vs_ibov_pp=final-float(cu[-1]['IBOV']) if complete else '',
            final_rank='',mean_annual_rank='',coverage='INHERITED_QUALIFIED' if v in ['V0','V10','R03 B2','BH padrão'] else 'FROZEN_REFERENCE' if v=='IBOV' else 'EVIDENCE_ONLY_NOT_COMPARABLE_TO_FULL_UNIVERSE' if complete else 'NOT_FORMED_OR_PENDING'))
    for s in stats:
        if s['periods']==12:
            # Exclude evidence-limited portfolios from an unconditional winner ranking.
            peers=[q for q in stats if q['periods']==12 and not q['coverage'].startswith('EVIDENCE_ONLY')]
            if s in peers:
                s['final_rank']=1+sum(q['final_pct']>s['final_pct'] for q in peers)
                s['mean_annual_rank']=statistics.mean(1+sum(float(a[q['variant']])>float(a[s['variant']]) for q in peers) for a in ac)
    write(RESULT/'consolidated_pct.csv',stats)
    write(RESULT/'holdings_by_june.csv',reconcile([r for v in runs.values() for r in v['holdings']],annual))
    for name,key in [('positions_by_june','positions'),('review_ledger','reviews'),('risk_concentration','risk'),('redemption_transfers','transfers')]:
        write(RESULT/(name+'.csv'),[r for v in runs.values() for r in v[key]])
    turnover=[]
    for v,data in runs.items():
        for y in range(2014,2026):
            rs=[r for r in data['reviews'] if r['year']==y]
            if not rs:continue
            buys=math.fsum(max(0,r['change']) for r in rs);sales=math.fsum(max(0,-r['change']) for r in rs)
            turnover.append(dict(variant=v,year=y,one_way_turnover_pct=100*sales/rs[0]['nav'],
                purchases_pct=100*buys/rs[0]['nav'],sales_pct=100*sales/rs[0]['nav'],formation=y==2014,
                note='Initial allocation; no prior positions to sell' if y==2014 else 'Sales/NAV; purchases= sales; no general equalization'))
    write(RESULT/'turnover_by_year.csv',turnover)
    dec={(r['year'],r['ticker']):r for r in runs['V10']['decisions']}
    facts=json.loads((INPUT/'fundamental_decisions.json').read_text()) if (INPUT/'fundamental_decisions.json').exists() else []
    facts={(r['year'],r['ticker']):r for r in facts}
    rows=[]
    for r in candidates():
        d=dec[r['year'],r['ticker']];f=facts.get((r['year'],r['ticker']),{})
        rows.append(dict(r,v10_decision=d['decision'],v10_reason=d['reason'],liquidity_rank=d['liquidity_rank'],
            valuation_status=f.get('valuation_status','PENDING'),normalized_profit=f.get('normalized_profit'),
            normalized_pe=f.get('normalized_pe'),market_cap=f.get('market_cap'),real_eps_cagr=f.get('real_eps_cagr'),
            average_payout=f.get('average_payout'),return_on_capital_median=f.get('return_on_capital_median'),
            bazin_normalized_dy=f.get('bazin_normalized_dy'),graham_pe_pb=f.get('graham_pe_pb'),
            quality_category=f.get('quality_category','PENDING'),missing=f.get('missing',''),dossier=f.get('dossier','')))
    write(RESULT/'selection_decisions.csv',rows)
    workbook()
    manifest=dict(protocol_commit=PROTOCOL_SHA,baseline_commit='8d394e9ab563daebe43603a3e85f35f43c1402bc',
        protected_stage1_files=verify_frozen(),variants={v:sum(r['return_pct']!='' for r in d['annual']) for v,d in runs.items()},
        inputs=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sorted(INPUT.rglob('*')) if p.is_file()],
        outputs=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sorted(RESULT.iterdir()) if p.is_file() and p.name!='manifest.json'])
    jsonwrite(RESULT/'manifest.json',manifest)
    print(json.dumps(stats,ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['v10','vval','all'],default='all');args=p.parse_args()
    verify_frozen()
    runs={v:simulate(v) for v in ['V0','V10']}
    if args.stage!='v10':
        lock=json.loads((INPUT/'fundamental_decisions_lock.json').read_text())
        if sha(INPUT/'fundamental_decisions.json')!=lock['decisions_sha256']:raise ValueError('Decision lock mismatch')
        ds=json.loads((INPUT/'fundamental_decisions.json').read_text());ds={(r['year'],r['ticker']):r for r in ds}
        runs.update({v:simulate(v,ds) for v in (['VVAL','VQ'] if args.stage=='all' else ['VVAL'])})
    publish(runs)

if __name__=='__main__':main()
