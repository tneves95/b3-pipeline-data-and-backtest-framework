"""Corrected policy checkpoints, using only preserved prices/events/decisions."""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import monthly_contributions as original
from monthly_corrected_simulate import simulate
from monthly_tax_accounting import Fiscal
from monthly_policy_corrected import PROOF, FAIL_REASON, maintenance_evidence
from run_monthly_tax import write

ROOT=original.ROOT
OUT=ROOT/'research/monthly_policy_corrected_2014_2026'
LEGACY=ROOT/'research/monthly_tax_2014_2026'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def guard_legacy():
    manifest=json.loads((LEGACY/'LEGACY_ONLY.json').read_text())
    for row in manifest['files']:
        assert sha(ROOT/row['path'])==row['sha256'],row['path']
    return len(manifest['files'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['GROSS','CG_ONLY','CG_PLUS_JCP_CERTIFIED_PARTIAL'],default='GROSS')
    args=parser.parse_args();mode=args.mode
    OUT.mkdir(parents=True,exist_ok=True);folder=OUT/mode;folder.mkdir(exist_ok=True)
    protected=guard_legacy()
    policy=dict(authority='https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086144108',
        voluntary_sales='Frozen FAIL_EXIT and base_status FAIL in June only; BH none',
        contributions='100000 initial; 144 monthly deposits of2500; available cash proportional positive reference deficits',
        winner='June PIT weight>=1.5/N and trailing12m return>median; flag retained until exit;2/N buy reference only while N>15',
        admission='Frozen candidates; unfunded entry remains eligible; never sell incumbent to fund entry',
        maintenance_proof_sha256=sha(PROOF),legacy_fiscal_evidence_sha256=sha(LEGACY/'inputs/event_tax_evidence_stage2.json'),
        legacy_tax_rules_sha256=sha(LEGACY/'inputs/tax_policy_freeze.json'),
        legacy_tax_policy_scope='Only tax parameters reused; old economic rebalancing superseded',
        zero_funded_shadow='One nominal unit for next June PIT return only; not an actual purchase')
    p=OUT/'policy_freeze.json'
    if p.exists():assert json.loads(p.read_text())==policy,'Frozen corrected policy changed'
    else:p.write_text(json.dumps(policy,indent=2,ensure_ascii=False)+'\n')
    ev=json.loads((LEGACY/'inputs/event_tax_evidence_stage2.json').read_text())
    quote,_=original.load_quotes();events=original.events();comps=original.frozen_compositions()
    sessions=[r['date'] for r in original.read(original.STUDY/'inputs/ibov_daily.csv')]
    expected={r['portfolio']:r for r in original.read(original.STUDY/'consolidated.csv')}
    corrected={} if mode=='GROSS' else {r['portfolio']:r for r in original.read(OUT/'consolidated_policy_corrected.csv')}
    summaries=[];rows=defaultdict(list);checks=[];meta=original.identities()
    for portfolio in original.PORTFOLIOS:
        f=Fiscal(portfolio,ev,sessions,enabled=mode!='GROSS',income_mode='CERTIFIED_PARTIAL' if mode=='CG_PLUS_JCP_CERTIFIED_PARTIAL' else 'NONE')
        run=simulate(portfolio,quote,events,comps,fiscal=f)
        s=dict(mode=mode,**run['summary']);old=expected[portfolio]
        issuer=defaultdict(float);sector=defaultdict(float)
        for c,u in run['book'].items():
            for t,q in u.items():
                value=q*quote[t,original.END]
                issuer['XP_SPINOFF' if t=='XPBR31' else meta.get(t,{}).get('cnpj',c)]+=value
                sector[meta.get(t,{}).get('sector','Unclassified')]+=value
                rows['final_positions'].append(dict(portfolio=portfolio,lineage=c,ticker=t,quantity=q,
                    total_acquisition_cost=f.basis[t],average_cost=f.basis[t]/q,close=quote[t,original.END],value=value))
        s.update(maximum_issuer_weight=max(issuer.values())/s['final_wealth'],issuer_hhi=sum((v/s['final_wealth'])**2 for v in issuer.values()),
            sector_hhi=sum((v/s['final_wealth'])**2 for v in sector.values()),economic_issuers=len(issuer),
            original_pr5_wealth=float(old['final_wealth']),original_pr5_xirr_pct=float(old['xirr_pct']),
            original_pr5_voluntary_sales=int(old['voluntary_sales']),
            original_pr5_maximum_issuer_weight=float(old['maximum_issuer_weight']),
            delta_pr5_wealth=s['final_wealth']-float(old['final_wealth']),delta_pr5_xirr_pp=s['xirr_pct']-float(old['xirr_pct']),
            qualification='CORRECTED_GROSS_FROZEN_EVIDENCE' if mode=='GROSS' else 'CONDITIONAL_CORPORATE_TAX_BASES_AND_INCOME_COVERAGE')
        if mode!='GROSS':
            b=corrected[portfolio];s.update(corrected_gross_wealth=float(b['final_wealth']),corrected_gross_xirr_pct=float(b['xirr_pct']),
                tax_wealth_effect=float(b['final_wealth'])-s['final_wealth'],tax_xirr_effect_pp=float(b['xirr_pct'])-s['xirr_pct'],gross_rank=int(b['rank']))
        assert s['external_capital']==460000 and s['external_contributions']==144
        assert all(t['reason']==FAIL_REASON and t['maintenance_status']=='FAIL' for t in run['trades'] if t['side']=='SELL')
        if portfolio in ['BH padrão','BESST-10 BH']:
            assert s['voluntary_sales']==0
            if mode=='GROSS':assert abs(s['final_wealth']-float(old['final_wealth']))<1e-6
        summaries.append(s)
        for key in ['trades','positions','wealth','event_ledger','junes','annual','contributions']:rows[key].extend(run[key])
        rows['investor_flows'].extend(dict(portfolio=portfolio,date=d,amount=a) for d,a in run['flows'])
        for name,data in [('monthly_tax',f.monthly_rows()),('tax_trades',f.trades),('tax_events',f.event_rows),
                          ('income',f.income_rows),('payments',f.payments),('liquidation_trades',run['liquidation']['rows']),
                          ('liquidation_monthly_tax',run['liquidation']['monthly_tax'])]:rows[name].extend(data)
        for year in range(2014,2027):
            taxed=[r for r in f.taxrows if r['month'].startswith(str(year))]
            paid=sum(r['amount'] for r in f.payments if r['date'].startswith(str(year)))
            retained=sum(r['ordinary_irrf']+r['daytrade_irrf'] for r in taxed)
            income=sum(r['withheld_additional'] for r in f.income_rows if r['date'].startswith(str(year)))
            rows['annual_tax'].append(dict(portfolio=portfolio,year=year,darf_paid=paid,irrf_paid=retained,
                tax_paid=paid+retained,income_withheld=income,total_tax_paid=paid+retained+income,
                tax_assessed=sum(r['assessed_tax'] for r in taxed),exempt_gain=sum(r['exempt_gain'] for r in taxed)))
        checks.append(dict(portfolio=portfolio,contributions=144,capital=460000,voluntary_sales=s['voluntary_sales'],
                           sales_reason=FAIL_REASON if s['voluntary_sales'] else 'NONE',status='PASS'))
        print(mode,portfolio,'wealth',round(s['final_wealth'],2),'XIRR',round(s['xirr_pct'],6),
              'maxweight',round(s['maximum_issuer_weight']*100,4),'sales',s['voluntary_sales'],'CGtax',round(s['tax_paid'],2),flush=True)
    for rank,s in enumerate(sorted(summaries,key=lambda s:-s['final_wealth']),1):s['rank']=rank
    for rank,s in enumerate(sorted(summaries,key=lambda s:-s['liquidation_wealth']),1):s['liquidation_rank']=rank
    name='consolidated_policy_corrected.csv' if mode=='GROSS' else 'consolidated_tax_corrected.csv' if mode=='CG_ONLY' else 'consolidated_income_corrected.csv'
    write(OUT/name,summaries)
    for name,data in rows.items():write(folder/(name+'.csv'),data)
    if mode=='GROSS':write(OUT/'ibov_gross_reference.csv',[original.benchmark()['summary']])
    assert guard_legacy()==protected
    (folder/'validation.json').write_text(json.dumps(dict(status='CALCULATED_CONDITIONAL_DOCUMENTARY_LIMITATIONS',
        protected_legacy_files=protected,checks=checks),indent=2,ensure_ascii=False)+'\n')
    (folder/'manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in sorted(folder.glob('*.csv'))},indent=2)+'\n')

if __name__=='__main__':main()
