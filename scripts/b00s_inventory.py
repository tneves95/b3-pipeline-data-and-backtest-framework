"""Inventory existing PIT facts before inspecting any variant outcome."""
from b00s_variants import *
from stage1_select import Evidence

def main():
    e=Evidence();rows=[]
    for y in range(2014,2026):
        idx,_,caps=e.asof(y)
        for r in [r for r in candidates() if r['year']==y]:
            c=r['cnpj'];cap=caps.get(c)
            rows.append(dict(year=y,ticker=r['ticker'],cnpj=c,sector=r['sector'],potential_base_weight_pct=100*r['base_target'],
                individual_ni_years=sum((c,fy,'ind','ni') in idx for fy in range(y-5,y)),
                capital_document=cap['docid'] if cap else '',capital_received=cap['received'] if cap else '',
                attributable_ni='REQUIRES_ORIGINAL_DRE_RECONCILIATION',
                class_capitalization='REQUIRES_SHARE_EVENT_AND_CLASS_RECONCILIATION',
                reinvestment='EPS_PAYOUT_ROIC_PRUDENTIAL_EVIDENCE_REQUIRED',quality='SIX_DIMENSION_DOSSIER_REQUIRED'))
    write(RESULT/'initial_pit_inventory.csv',rows)
    summary=[]
    for y in range(2014,2026):
        for sector in sorted({r['sector'] for r in rows}):
            group=[r for r in rows if r['year']==y and r['sector']==sector]
            summary.append(dict(year=y,sector=sector,pass_candidates=len(group),five_year_individual_ni=sum(r['individual_ni_years']==5 for r in group),
                valuation_needing_reconciliation=len(group),quality_needing_dossier=len(group),potential_base_weight_pct=sum(r['potential_base_weight_pct'] for r in group)))
    write(RESULT/'coverage_by_year_sector.csv',summary)
    jsonwrite(INPUT/'base_candidates.json',candidates())
    jsonwrite(INPUT/'protocol_lock.json',dict(commit=PROTOCOL_SHA,
        specification_sha256=sha(ROOT/'docs/experimento_b00s_quatro_variantes_2014_2026.md'),
        coordinator='https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6069027018',
        valuation_thresholds=[15,25],sensitivities=[[12,20],[18,30]],real_eps_cagr_min=.04,retained_profit_min=.20,real_return_premium=.06,
        decision_policy='UNKNOWN_IS_NOT_FAIL; ADDITIONAL_FILTERS_ENTRY_ONLY',coverage_inventory_sha256=sha(RESULT/'initial_pit_inventory.csv')))
    print('Inventory frozen:',len(rows),'company-years;',len({r['cnpj'] for r in rows}),'companies')

if __name__=='__main__': main()
