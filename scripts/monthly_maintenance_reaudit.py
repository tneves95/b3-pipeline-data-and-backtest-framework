"""Revoke contradicted exits and follow their actual successors at each June.

The original price/event/purchase-reference engines stay frozen. Only the four
audited lineages are re-examined after their first disputed exit; other proven
exits retain the audit's PIT evidence. No missing fact becomes a zero.
"""
from collections import defaultdict
import hashlib
import json
import math
import monthly_contributions as economic
from monthly_policy_corrected import BH, FAIL_REASON, maintenance_evidence as inherited
from stage1_select import Evidence, metric, status
from run_monthly_tax import write

ROOT=economic.ROOT
OUT=ROOT/'research/monthly_reaudited_2014_2026'
AUDIT=ROOT/'research/monthly_fail_audit_2014_2026'
REVIEW=OUT/'maintenance_reviews.csv'
REVISIT={'TIET11':2016,'CPFE3':2020,'BRSR6':2021,'SBSP3':2024}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def guard_prior():
    m=json.loads((AUDIT/'manifest.json').read_text())
    for section in ['old_results_protected','sources']:
        for path,digest in m[section].items():assert sha(ROOT/path)==digest,path
    return len(m['old_results_protected'])


def physical_path(ticker,year,events):
    """Actual voluntary-purchase security after accepted compulsory conversions."""
    for day,rows in sorted(events.items()):
        if day>economic.DATES[year]:break
        for r in rows:
            if r['ticker']==ticker and r['kind']=='CONVERSION':ticker=r['legs'][0][0]
    return ticker


def flags_for(index,issuer,year,evidence,quote,conversion_short_window=False,successor_first_year=None):
    profits=[];distributions=[];facts=[]
    for fy in range(year-5,year):
        ni=metric(index,issuer,fy,'ni')
        profits.append(None if ni is None else ni['value']*1000)
        flow=[metric(index,issuer,fy,k,'ind') for k in ['distributions','distributions_dmpl','distributions_dva']]
        if fy in evidence.divyears[issuer] or any(f is not None and abs(f['value'])>0 for f in flow):d=True
        else:d=False if all(f is not None for f in flow) else None
        if d is False and successor_first_year is not None and fy<successor_first_year:
            # Blank/shell distributions before the economic conversion do not
            # prove the held predecessor stopped distributing. No backfilled
            # predecessor cash event or fabricated successor history is used.
            d=None
        distributions.append(d)
        facts.extend(f for f in [ni]+flow if f is not None)
    positive=False if any(v is not None and v<=0 for v in profits) else True if all(v is not None for v in profits) else None
    payout=False if False in distributions else True if all(v is True for v in distributions) else None
    liquidity=None
    if quote:
        if quote['median_volume']<1e6 or quote['close']<2:liquidity=False
        elif quote['sessions']>=math.ceil(.8*126):liquidity=True
        elif not conversion_short_window:liquidity=False
        # A newly listed successor's short record does not establish that the
        # predecessor/successor economic lineage ceased to be liquid.
    return positive,payout,liquidity,profits,distributions,facts


def build():
    OUT.mkdir(parents=True,exist_ok=True);guard_prior()
    ev=Evidence();meta=economic.identities();events=economic.events()
    audited=economic.read(AUDIT/'exit_evidence_audit.csv')
    bad={r['lineage_cnpj'] for r in audited if r['classification'] in {
        'LEGACY_PROFIT_ZERO_CONTRADICTED','DISTRIBUTION_GAP_DISPUTED','WRONG_SECURITY_LIQUIDITY'}}
    assert bad=={meta[t]['cnpj'] for t in REVISIT}
    decisions=[];facts=[]
    for (portfolio,year,c),proof in sorted(inherited().items()):
        if c in bad:continue
        a=next(r for r in audited if r['lineage_cnpj']==c and int(r['year'])==year)
        assert a['classification'] in {'NONPOSITIVE_PROFIT_DOCUMENTED','LIQUIDITY_FILTER_MATCHES'}
        decisions.append(dict(portfolio=portfolio,year=year,date=economic.DATES[year],lineage=c,
            ticker=proof['source_ticker'],issuer_cnpj=a['evidence_issuer_cnpj'],status='FAIL',
            fail_basis=a['classification'],scope='UNCHANGED_EXIT_VALIDATED_IN_PRIOR_AUDIT',
            source='research/monthly_fail_audit_2014_2026/exit_evidence_audit.csv',
            nonpositive_years=a['nonpositive_years']))
    quotes={(r['year'],economic.security(r['ticker'])):r for r in ev.market['quotes']}
    for year in range(2016,2026):
        idx,_,_=ev.asof(year);cutoff=economic.DATES[year]
        for origin,first in sorted(REVISIT.items()):
            if year<first:continue
            c=meta[origin]['cnpj'];t=physical_path(origin,year,events);q=quotes.get((year,t))
            issuer,identity=ev.identity(q) if q else ('','MISSING_QUOTE_IDENTITY')
            short=any(r['kind']=='CONVERSION' and r['legs'][0][0]==t and
                      day[:4]==str(year) and day<=cutoff for day,rs in events.items() for r in rs)
            successor_years=[int(day[:4]) for day,rs in events.items() for r in rs
                if r['kind']=='CONVERSION' and r['legs'][0][0]==t and day<=cutoff]
            successor_first=min(successor_years) if successor_years else None
            p,d,l,ni,ds,fs=flags_for(idx,issuer,year,ev,q,short,successor_first)
            st=status([p,d,l]) if issuer else 'INDETERMINATE'
            # Payment/appropriation/ex-date reconciliation in CPFE's original
            # five-year cash test is disputed: retain without certifying PASS.
            if origin=='CPFE3' and year==2020 and st!='FAIL':st='INDETERMINATE'
            basis='NONPOSITIVE_PROFIT_DOCUMENTED' if p is False else 'ACTUAL_SECURITY_LIQUIDITY' if l is False else 'STATEMENT_DISTRIBUTION_ZERO' if d is False else 'NO_PROVEN_FAIL'
            base=dict(year=year,date=cutoff,lineage=c,ticker=t,issuer_cnpj=issuer,status=st,
                fail_basis=basis,scope='AUDITED_LINEAGE_AND_LATER_JUNES',source='PRESERVED_PIT_DFP_AND_B3_CACHE',
                origin_ticker=origin,identity_method=identity,profit5=p,distribution5=d,liquidity=l,
                nonpositive_years=';'.join(str(year-5+i) for i,v in enumerate(ni) if v is not None and v<=0),
                missing_profit_years=';'.join(str(year-5+i) for i,v in enumerate(ni) if v is None),
                close=q['close'] if q else None,sessions=q['sessions'] if q else None,
                median_volume=q['median_volume'] if q else None,successor_short_window=short,
                missing_history_does_not_prove_failure=True)
            for portfolio in ['V0','V10','VVAL']:decisions.append(dict(portfolio=portfolio,**base))
            for f in fs:
                assert f['received']<=cutoff and f['period_end']<=cutoff
                facts.append(dict(review_year=year,cutoff=cutoff,lineage=c,actual_ticker=t,issuer_cnpj=issuer,
                    fiscal_year=f['year'],metric=f['metric'],value_brl=f['value']*1000,
                    received=f['received'],period_end=f['period_end'],document_id=f['docid'],
                    account=f['account'],perimeter=f['perimeter'],source=f['source']))
    decisions.sort(key=lambda r:(r['portfolio'],r['year'],r['lineage']))
    assert len({(r['portfolio'],r['year'],r['lineage']) for r in decisions})==len(decisions)
    write(REVIEW,decisions);write(OUT/'maintenance_pit_facts.csv',facts)
    liquidity=[]
    for (year,t),q in sorted(quotes.items()):
        if t in meta:liquidity.append(dict(year=year,ticker=t,lineage=meta[t]['cnpj'],sector=meta[t]['sector'],
            median_volume=q['median_volume'],sessions=q['sessions'],total_volume=q['total_volume']))
    write(OUT/'admission_liquidity.csv',liquidity)
    manifest=dict(scope='Invalidate nine contradicted/unproved sales; revisit their four lineages through June2025; unchanged other audited exits',
        audited_exit_sha256=sha(AUDIT/'exit_evidence_audit.csv'),
        files={str(p.relative_to(ROOT)):sha(p) for p in [REVIEW,OUT/'maintenance_pit_facts.csv',OUT/'admission_liquidity.csv']},
        inherited_inputs=json.loads((AUDIT/'manifest.json').read_text())['sources'],
        qualifications=['No new cash event or quote invented','Coded liquidity convention inherited, not a newly certified maintenance definition',
            'V10 incumbent slots retained; new candidates cannot displace PASS/INDETERMINATE',
            'Newly listed compulsory successor short window is indeterminate, not economic FAIL',
            'CNPJ of actual successor used for DFP; absent history remains missing, not zero'])
    (OUT/'maintenance_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    guard_prior();print('Reaudited June decisions',len(decisions),'PIT facts',len(facts),flush=True)


def maintenance_evidence():
    result={}
    for line,r in enumerate(economic.read(REVIEW),2):
        result[r['portfolio'],int(r['year']),r['lineage']]=dict(status=r['status'],reason=FAIL_REASON if r['status']=='FAIL' else 'INCUMBENT_PRESERVED',
            source=str(REVIEW.relative_to(ROOT)),source_line=line,source_ticker=r['ticker'],source_reason=r['fail_basis'])
    return result


def review_members(portfolio,year,buyers,candidates,evidence):
    if portfolio in BH:return buyers.copy(),{},set()
    exits={c:evidence[portfolio,year,c] for c in buyers if evidence.get((portfolio,year,c),{}).get('status')=='FAIL'}
    desired={c:t for c,t in buyers.items() if c not in exits}
    proposed={c:t for c,t in candidates.items() if c not in buyers and evidence.get((portfolio,year,c),{}).get('status')!='FAIL'}
    if portfolio=='V10':
        meta=economic.identities();occupied=defaultdict(set)
        for c,t in desired.items():occupied[meta[t]['sector']].add(c)
        ranks={r['ticker']:r for r in economic.read(OUT/'admission_liquidity.csv') if int(r['year'])==year}
        ordered=sorted(proposed,key=lambda c:(meta[proposed[c]]['sector'],
            -float(ranks.get(proposed[c],{}).get('median_volume',0)),
            -float(ranks.get(proposed[c],{}).get('sessions',0)),
            -float(ranks.get(proposed[c],{}).get('total_volume',0)),proposed[c]))
        admitted={}
        for c in ordered:
            t=proposed[c];sector=meta[t]['sector']
            if len(occupied[sector])<2:admitted[c]=t;occupied[sector].add(c)
        proposed=admitted
        assert all(len(v)<=2 for v in occupied.values())
    entries=set(proposed);desired.update(proposed)
    return desired,exits,entries


if __name__=='__main__':build()
