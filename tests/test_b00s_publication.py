"""Cross-artifact checks on the published V2 experiment, including ND semantics."""
import json
import sys
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b00s_variants as m

def test_published_references_are_literal_and_unreviewed_years_are_blank():
    annual=m.read(m.RESULT/'annual_returns_pct.csv')
    old=m.read(m.BASE/'annual_returns_pct.csv')
    assert len(annual)==12
    for r,o in zip(annual,old):
        for v,key in [('V0','B00S B2'),('IBOV','IBOV'),('R03 B2','R03 B2'),('BH padrão','BH padrão')]:
            assert r[v]==o[key]
        if int(r['year'])>m.reviewed_through():assert r['VQ']=='' and r['VVAL']==''
        else:assert r['VQ']!='' and r['VVAL']!=''
    status=[r for r in m.read(m.RESULT/'portfolio_status.csv') if r['variant']=='VQ']
    assert len(status)==12
    assert all(r['status']=='AWAITING_CHRONOLOGICAL_REVIEW' for r in status if int(r['year'])>m.reviewed_through())
    stats={r['variant']:r for r in m.read(m.RESULT/'consolidated_pct.csv')}
    assert stats['VQ']['final_pct']=='' and int(stats['VQ']['periods'])==m.reviewed_through()-2013
    assert stats['VVAL']['final_rank']==''

def test_published_attribution_reconciles_annual_and_compounded():
    with localcontext() as ctx:
        ctx.prec=60
        annual=m.read(m.RESULT/'annual_returns_pct.csv');cum=m.read(m.RESULT/'cumulative_returns_pct.csv')
        holdings=m.read(m.RESULT/'holdings_by_june.csv');linked=m.read(m.RESULT/'attribution_cumulative.csv')
        for v in ['V0','V10','VVAL','VQ']:
            for a in annual:
                if a[v]=='':continue
                assert sum((Decimal(r['contribution_pp']) for r in holdings if r['variant']==v and r['year']==a['year']),Decimal(0))==Decimal(a[v])
            assert abs(sum((Decimal(r['linked_contribution_pp']) for r in linked if r['variant']==v),Decimal(0))-Decimal(next(r[v] for r in reversed(cum) if r[v]!='')))<Decimal('1e-45')
        assert any(r['variant']=='VQ' for r in holdings+linked)

def test_published_weights_risk_and_turnover_use_actual_continuity():
    groups=defaultdict(list)
    for r in m.read(m.RESULT/'positions_by_june.csv'):groups[r['variant'],r['date'],r['phase']].append(r)
    risk={(r['variant'],r['date'],r['phase']):r for r in m.read(m.RESULT/'risk_concentration.csv')}
    for key,rows in groups.items():
        w=[float(r['weight_pct']) for r in rows]
        assert sum(w)==pytest.approx(100)
        byissuer=defaultdict(float)
        for r in rows:
            issuer='XP_SPINOFF' if r['ticker']=='XPBR31' else m.identities()[r['ticker']]['cnpj']
            byissuer[issuer]+=float(r['weight_pct'])
        assert float(risk[key]['largest_company_pct'])==pytest.approx(max(byissuer.values()))
        assert float(risk[key]['issuer_hhi'])==pytest.approx(sum((v/100)**2 for v in byissuer.values()))
    for r in m.read(m.RESULT/'turnover_by_year.csv'):
        if r['formation']=='False':
            assert float(r['purchases_pct'])==pytest.approx(float(r['sales_pct']),abs=1e-10)
    final=groups['VVAL',m.DATES[m.reviewed_through()+1],'PERIOD_END']
    assert {'PSSA3','CSMG3','SBSP3'}<={r['ticker'] for r in final}
    assert all(float(r['one_way_turnover_pct'])==0 for r in m.read(m.RESULT/'turnover_by_year.csv') if r['year']=='2014')

def test_sensitivities_cover_each_issuer_without_silent_failed_series():
    rows=m.read(m.RESULT/'sensitivity_summary.csv');bycase={r['case']:r for r in rows}
    issuers={r['cnpj'] for r in m.candidates() if r['year']<=m.reviewed_through()}
    assert len(rows)==7+2*len(issuers)
    assert {c.removeprefix('VVAL_INCLUDE_') for c in bycase if c.startswith('VVAL_INCLUDE_')}==issuers
    assert {c.removeprefix('VQ_ALL_EXCEPT_') for c in bycase if c.startswith('VQ_ALL_EXCEPT_')}==issuers
    failed={r['case'] for r in rows if r['periods']=='0'}
    for r in m.read(m.RESULT/'sensitivity_annual_pct.csv'):
        if r['case'] in failed:assert r['return_pct']=='' and r['cumulative_pct']==''
    frozen=m.read(m.RESULT/'annual_returns_pct.csv')[0]['V0']
    for case in ['VVAL_ALL_UNKNOWN_INCLUDED','VQ_ALL_UNKNOWN_INCLUDED']:
        first=next(r for r in m.read(m.RESULT/'sensitivity_annual_pct.csv') if r['case']==case and r['year']=='2014')
        assert float(first['return_pct'])==pytest.approx(float(frozen),abs=1e-10)

def test_reference_entry_never_liquidates_nonfail():
    rows=json.loads((m.INPUT/'fundamental_decisions.json').read_text())
    ds={(r['year'],r['ticker']):r for r in rows}
    # Synthetic decisions isolate funding from the economic judgements.
    for r in ds.values():r['valuation_status']='PASS_MATURE' if r['year']==2014 and r['ticker'] in ['BBDC4','TBLE3'] else 'INDETERMINATE'
    # Former counterexample: a sole new entrant no longer requests 100% NAV.
    run=m.simulate('VVAL',ds,include=lambda r,d:r['cnpj']=='00001180000126' and d['valuation_status']=='INDETERMINATE',end_year=2025)
    assert run['funding']
    for r in run['reviews']:
        if r['before']>0 and r['base_status']!='FAIL':assert r['after']>0

def test_excel_and_manifest_match_published_sources():
    import openpyxl
    book=openpyxl.load_workbook(m.RESULT/'b00s_four_variants.xlsx',read_only=True,data_only=True)
    for sheet in book.worksheets:
        records=m.read(m.RESULT/(sheet.title+'.csv'));actual=list(sheet.values)
        assert list(actual[0])==list(records[0])
        assert len(actual)==len(records)+1
        for rr,values in zip(records,actual[1:]):
            for (key,value),cell in zip(rr.items(),values):
                if value=='':assert cell is None
                elif isinstance(cell,(float,int)):assert float(value)==pytest.approx(cell,rel=1e-14)
                else:assert value==cell
    book.close()
    manifest=json.loads((m.RESULT/'manifest.json').read_text())
    assert manifest['variants']==dict(V0=12,V10=12,VVAL=m.reviewed_through()-2013,VQ=m.reviewed_through()-2013)
    for r in manifest['inputs']+manifest['outputs']:assert m.sha(m.ROOT/r['path'])==r['sha256']

def test_dossiers_preserve_dates_and_all_six_dimensions():
    paths=list((m.INPUT/'dossiers').glob('*.json'))
    assert len(paths)==29
    expected={'durability','capital_economics','earnings_reliability','financial_resilience','capital_allocation','governance'}
    for p in paths:
        d=json.loads(p.read_text());a=d['initial_assessment']
        assert set(a['dimensions'])==expected
        for assessment,key in [(a,'dimensions')]+[(u,'dimension_evidence_updates') for u in d['annual_evidence_updates']]:
            for dim in assessment[key].values():
                for e in dim['evidence']:
                    if e.get('received'):assert e['received']<=assessment['cutoff']
    text=(m.ROOT/'docs/dossies_b00s_v2.md').read_text()
    assert all(p.name in text for p in paths)
