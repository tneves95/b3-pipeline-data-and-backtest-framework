"""Read-only audit of the evidence behind all voluntary exits in corrected PR6.

No eligibility or economic results are rewritten. Historical source receipts
are checked at each June cutoff; findings distinguish contradictions from gaps.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import monthly_contributions as economic
from stage1_select import Evidence, metric
from stage1_resume import canonical
from run_monthly_tax import write

ROOT=economic.ROOT
OUT=ROOT/'research/monthly_fail_audit_2014_2026'
RESULT=ROOT/'research/monthly_policy_corrected_2014_2026'
SELECTION=ROOT/'research/returns_2014_2026_selection'
LEGACY=ROOT/'research/graham_v6_comparison'
VARIANTS={'V0','V10','VVAL'}
MODES=['GROSS','CG_ONLY','CG_PLUS_JCP_CERTIFIED_PARTIAL']
# This exact inheritance is in b00s_variants.simulate; units were omitted by
# stage1_select.run's five-character stock-only filter.
STATUS_SECURITY={'TIET11':'TIET4'}


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def classify(*,false_zeros,known_nonpositive,screen_status,cash_rejection,
             positive_distribution_evidence,source_liquidity,actual_liquidity,complete_positive):
    if known_nonpositive:return 'NONPOSITIVE_PROFIT_DOCUMENTED'
    if false_zeros and complete_positive and screen_status=='PASS':return 'LEGACY_PROFIT_ZERO_CONTRADICTED'
    if cash_rejection and positive_distribution_evidence and screen_status=='PASS':return 'DISTRIBUTION_GAP_DISPUTED'
    if source_liquidity is False and actual_liquidity is True:return 'WRONG_SECURITY_LIQUIDITY'
    if source_liquidity is False and actual_liquidity is False:return 'LIQUIDITY_FILTER_MATCHES'
    return 'INDETERMINATE_FAIL_NOT_PROVED'


def main():
    OUT.mkdir(exist_ok=True)
    # Freeze the actual existing files rather than assume labels prove decisions.
    oldfiles=[p for p in RESULT.rglob('*') if p.is_file()]
    oldfiles += [ROOT/'scripts/monthly_policy_corrected.py',ROOT/'scripts/monthly_corrected_simulate.py']
    protected={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(oldfiles))}
    review=economic.read(ROOT/'research/b00s_four_variants_2014_2026/results/review_ledger.csv')
    screens=economic.read(SELECTION/'screening.csv')
    screen={(int(r['year']),canonical(r['ticker'])):r for r in screens if r['strategy']=='B00S'}
    universe=economic.read(LEGACY/'audit_v13_inputs/universe_v9_snapshot.csv')
    v9={(int(r['entry_year']),canonical(r['ticker'])):r for r in universe}
    cashrows=json.loads((LEGACY/'execution_v11_2_2026_10_07/auditoria_besst_v9/selection_rows.json').read_text())
    cash={(r['year'],canonical(r['ticker'])):r for r in cashrows}
    evidence=Evidence();meta=economic.identities()
    keys=sorted({(int(r['year']),r['ticker']) for r in review if r['variant'] in VARIANTS and r['reason']=='FAIL_EXIT'})
    summaries=[];factrows=[];physical=[];saleaudit=[]
    mode_trades={m:economic.read(RESULT/m/'trades.csv') for m in MODES}
    for year,ticker in keys:
        cutoff=economic.DATES[year];lineage=meta[ticker]['cnpj']
        st=STATUS_SECURITY.get(ticker,canonical(ticker));sr=screen.get((year,st),{})
        legacy=v9.get((year,st),{});cs=cash.get((year,st),{})
        # A corporate lineage can retain the predecessor's key in the engine.
        # Use the contemporaneous issuer's CNPJ for its DFP, never invent history
        # for the predecessor (notably TIET/AURE).
        cnpj=sr.get('cnpj') or ''.join(c for c in legacy.get('cnpj','') if c.isdigit()) or lineage
        index,_,_=evidence.asof(year)
        facts=[];false_zeros=[];nonpositive=[];positive_cash=[]
        for fy in range(year-5,year):
            ni=metric(index,cnpj,fy,'ni');cash_facts=[]
            if ni:
                assert ni['received']<=cutoff and ni['period_end']<=cutoff
                value=ni['value']*1000
                if value<=0:nonpositive.append(fy)
            else:value=None
            lag=year-1-fy;lv=legacy.get(f'profit_l{lag}');lv=float(lv) if lv not in [None,''] else None
            if lv==0 and value is not None and value>0:false_zeros.append(fy)
            facts.append(value)
            r=dict(review_year=year,cutoff=cutoff,ticker=ticker,status_security=st,lineage_cnpj=lineage,
                evidence_issuer_cnpj=cnpj,fiscal_year=fy,metric='NI',value_brl=value,
                legacy_value_brl=lv,legacy_zero_contradicted=fy in false_zeros,
                received=ni['received'] if ni else '',document_id=ni['docid'] if ni else '',
                account=ni['account'] if ni else '',perimeter=ni['perimeter'] if ni else '',
                source=ni['source'] if ni else '',status='KNOWN_NONPOSITIVE' if fy in nonpositive else 'KNOWN_POSITIVE' if ni else 'MISSING')
            factrows.append(r)
            for name in ['distributions','distributions_dmpl','distributions_dva']:
                f=metric(index,cnpj,fy,name,'ind')
                if f:
                    assert f['received']<=cutoff and f['period_end']<=cutoff
                    if abs(f['value'])>0:positive_cash.append(fy)
                    cash_facts.append(f)
                    factrows.append(dict(review_year=year,cutoff=cutoff,ticker=ticker,status_security=st,
                        lineage_cnpj=lineage,evidence_issuer_cnpj=cnpj,fiscal_year=fy,metric=name,
                        value_brl=f['value']*1000,received=f['received'],document_id=f['docid'],
                        account=f['account'],perimeter='ind',source=f['source'],
                        status='NONZERO_STATEMENT_DISTRIBUTION' if f['value'] else 'ZERO_REQUIRES_INTERPRETATION'))
        quote=next((r for r in evidence.market['quotes'] if r['year']==year and r['ticker']==ticker),None)
        if quote:
            actual_pass=quote['sessions']>=math.ceil(.8*126) and quote['median_volume']>=1e6 and quote['close']>=2
            physical.append(dict(year=year,ticker=ticker,cutoff=cutoff,**{k:quote[k] for k in ['isin_code','close','sessions','median_volume','total_volume']},
                liquidity_threshold=1e6,min_sessions=math.ceil(.8*126),min_close=2,liquidity_pass=actual_pass,
                source='research/returns_2014_2026_selection/cache/market.json.gz',
                identity=evidence.identity(quote)[0]))
        else:actual_pass=None
        complete=all(v is not None and v>0 for v in facts)
        sl=None if sr.get('liquidity','')=='' else sr['liquidity']=='True'
        cash_gap_years=[year-5+i for i,v in enumerate(cs.get('dps_norm',[])) if v is None or v==0]
        cash_conflict_years=sorted(set(cash_gap_years)&set(positive_cash))
        classification=classify(false_zeros=false_zeros,known_nonpositive=nonpositive,screen_status=sr.get('status','INDETERMINATE'),
            cash_rejection=bool(cs) and not cs['cash5'],positive_distribution_evidence=bool(cash_conflict_years),
            source_liquidity=sl,actual_liquidity=actual_pass,complete_positive=complete)
        variants=sorted({r['variant'] for r in review if int(r['year'])==year and r['ticker']==ticker and r['reason']=='FAIL_EXIT' and r['variant'] in VARIANTS})
        reason={'LEGACY_PROFIT_ZERO_CONTRADICTED':'v9 zero profits contradicted by positive PIT DFP; local B00S screening PASS',
            'DISTRIBUTION_GAP_DISPUTED':'legacy cash5=0 conflicts with screening PASS and PIT nonzero individual cash-flow/distribution statements; ex-date vs fiscal-year appropriation/payment not reconciled',
            'WRONG_SECURITY_LIQUIDITY':'held unit inherits FAIL from another class; held unit passes the coded liquidity filter; lineage/economic history must not be replaced silently',
            'NONPOSITIVE_PROFIT_DOCUMENTED':'PIT DFP records nonpositive earnings within five-year window',
            'LIQUIDITY_FILTER_MATCHES':'actual held security fails coded liquidity threshold; this validates the mechanical filter, not an independently redefined permanence policy',
            'INDETERMINATE_FAIL_NOT_PROVED':'insufficient evidence to substantiate the inherited FAIL'}[classification]
        row=dict(year=year,cutoff=cutoff,ticker=ticker,status_security=st,lineage_cnpj=lineage,evidence_issuer_cnpj=cnpj,
            variants=';'.join(variants),sale_count=len(variants),screen_status=sr.get('status','MISSING'),
            screen_profit5=sr.get('F3',''),screen_distribution5=sr.get('F4',''),screen_liquidity=sr.get('liquidity',''),
            legacy_preselection_pass=legacy.get('preselection_pass',''),legacy_cash5=cs.get('cash5',''),
            false_zero_years=';'.join(map(str,false_zeros)),cash_gap_years=';'.join(map(str,cash_gap_years)),
            cash_conflict_years=';'.join(map(str,cash_conflict_years)),nonpositive_years=';'.join(map(str,nonpositive)),
            missing_profit_years=';'.join(str(year-5+i) for i,v in enumerate(facts) if v is None),
            actual_security_liquidity_pass=actual_pass,classification=classification,reason=reason)
        summaries.append(row)
        for mode,trades in mode_trades.items():
            found=[r for r in trades if r['side']=='SELL' and r['ticker']==ticker and r['date']==cutoff]
            assert sorted(r['portfolio'] for r in found)==variants,(mode,year,ticker)
            saleaudit.extend(dict(mode=mode,classification=classification,audit_reason=reason,**r) for r in found)
    for mode,trades in mode_trades.items():
        assert len([r for r in saleaudit if r['mode']==mode])==len([r for r in trades if r['side']=='SELL'])
    write(OUT/'exit_evidence_audit.csv',summaries);write(OUT/'pit_facts.csv',factrows)
    write(OUT/'actual_security_liquidity.csv',physical);write(OUT/'sales_audit_all_modes.csv',saleaudit)
    counter=Counter(r['classification'] for r in saleaudit if r['mode']=='GROSS')
    sourcefiles=[ROOT/'scripts/stage1_resume.py',ROOT/'scripts/stage1_select.py',ROOT/'scripts/b00s_variants.py',
        SELECTION/'screening.csv',LEGACY/'audit_v13_inputs/universe_v9_snapshot.csv',
        LEGACY/'execution_v11_2_2026_10_07/auditoria_besst_v9/selection_rows.json',
        ROOT/'research/b00s_four_variants_2014_2026/results/review_ledger.csv']
    sourcefiles+=sorted((SELECTION/'cache').glob('dfp_*.json.gz'))+[SELECTION/'cache/market.json.gz']
    sourcefiles+=[ROOT/'research/returns_2014_2026_inputs/cvm_recovery/recovered_income.csv']
    sourcefiles += [p for p in [SELECTION/'cache/supplement.json.gz',SELECTION/'recovered_facts.json',SELECTION/'cache/treasury_classes.json.gz'] if p.exists()]
    manifest=dict(scope='All18 voluntary sales in each corrected mode;10 issuer/review events;BH0 voluntary sales',
        mode_counts={m:sum(r['mode']==m for r in saleaudit) for m in MODES},gross_classifications=dict(counter),
        no_results_recalculated=True,old_results_protected=protected,
        sources={str(p.relative_to(ROOT)):digest(p) for p in sourcefiles},
        qualifications=['NI cache contains total consolidated or individual profit, not an issuer-attributable normalized-earnings certification',
            'PIT means actual saved receipt<=June cutoff; future restatements excluded',
            'cash5 absence in an event cache does not prove no distribution; statement payments versus appropriations require reconciliation',
            'liquidity validity refers to the existing coded threshold; whether it is a permanence rule must follow coordinator policy'])
    assert all(digest(ROOT/f)==s for f,s in protected.items()),'Prior results changed during audit'
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(unique_events=len(summaries),gross_sales=len(saleaudit)//len(MODES),classifications=dict(counter)),indent=2))

if __name__=='__main__':main()
