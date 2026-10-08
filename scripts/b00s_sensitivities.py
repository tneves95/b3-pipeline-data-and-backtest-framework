"""Predeclared thresholds and symmetric missing-evidence inclusion experiments.

These are conditional scenarios, never retrospectively promoted to main cases.
Every frozen issuer receives the same leave-one-out / include-one treatment.
"""
from b00s_variants import *
from b00s_fundamentals import valuation_gate
from copy import deepcopy

def coverage(ds):
    base={(r['year'],r['ticker']):r for r in candidates()};rows=[]
    for y in range(2014,2026):
        for sector in ['Bancos','Energia','Saneamento','Seguros','Telecom']:
            group=[r for r in ds if r['year']==y and r['sector']==sector]
            nd=[r for r in group if r['valuation_status']=='INDETERMINATE'];qnd=[r for r in group if r['quality_category']=='INDETERMINATE']
            rows.append(dict(year=y,sector=sector,pass_candidates=len(group),computable_normalized_pe=sum(r['normalized_pe'] is not None for r in group),
                valuation_approved=sum(r['valuation_status'].startswith('PASS') for r in group),valuation_indeterminate=len(nd),
                valuation_indeterminate_candidate_pct=100*len(nd)/len(group) if group else None,
                valuation_potential_weight_affected_pct=100*sum(base[y,r['ticker']]['base_target'] for r in nd),
                quality_qualified=sum(r['quality_category'].startswith('QUALIFIED') for r in group),quality_indeterminate=len(qnd),
                quality_potential_weight_affected_pct=100*sum(base[y,r['ticker']]['base_target'] for r in qnd),
                interpretation='Potential control target weight, not actual alternative portfolio weight'))
    write(RESULT/'coverage_by_year_sector.csv',rows)
    write(RESULT/'indeterminate_queue.csv',[dict(year=r['year'],ticker=r['ticker'],cnpj=r['cnpj'],sector=r['sector'],
        potential_base_weight_pct=100*base[r['year'],r['ticker']]['base_target'],normalized_pe=r['normalized_pe'],
        mechanical_valuation_status=r['mechanical_valuation_status'],valuation_status=r['valuation_status'],missing=r['missing'],
        quality_category=r['quality_category'],six_dimension_dossier=r['dossier'],
        income_documents=';'.join(sorted({e['docid'] for e in r['profit_evidence']})),
        latest_income_receipt=max((e['received'] for e in r['profit_evidence']),default='')) for r in ds])

def main():
    raw=json.loads((INPUT/'fundamental_decisions.json').read_text());ds={(r['year'],r['ticker']):r for r in raw}
    coverage(raw);paths=[];summaries=[];contributions=[];trades=[];decision_diff=[]
    base=simulate('VVAL',ds);base_final=base['annual'][-1]['cumulative_pct'];v0=simulate('V0');v0final=v0['annual'][-1]['cumulative_pct']
    base_buys={(r['year'],r['ticker']) for r in base['reviews'] if r['reason'] in ['FORMATION','PASS_ENTRY']}
    def conditional_run(variant, scenario, include):
        try:return simulate(variant,scenario,include=include)
        except ValueError as e:
            if not e.args or not isinstance(e.args[0],tuple) or e.args[0][0]!='UNRESOLVED_ENTRY_FUNDING_WOULD_LIQUIDATE_NONFAIL':raise
            return dict(annual=[dict(variant=variant,year=y,start=DATES[y],end=DATES[y+1],return_pct='',cumulative_pct='',
                status=str(e.args[0])) for y in range(2014,2026)],reviews=[],holdings=[])
    def record(case,run,kind,comparison,conditional=True):
        aa=run['annual'];formed=sum(r['return_pct']!='' for r in aa);final=aa[-1]['cumulative_pct'] if formed==12 else ''
        buys={(r['year'],r['ticker']) for r in run['reviews'] if r['reason'] in ['FORMATION','PASS_ENTRY']}
        summaries.append(dict(case=case,kind=kind,periods=formed,final_pct=final,cagr_pct=100*((1+final/100)**(1/12)-1) if formed==12 else '',
            compared_with='VVAL_EVIDENCE_ONLY' if comparison==base_final else 'V0_AS_ALL_QUALITY_UNKNOWN_INCLUDED',
            difference_pp=final-comparison if formed==12 else '',entry_decisions_different_from_vval=len(buys^base_buys),conditional=conditional,
            limitation='Hypothetical eligibility; not evidence of actual quality, not a return bound, not a fifth main strategy' if formed==12 else aa[-1]['status']))
        paths.extend(dict(case=case,**r) for r in aa)
        trades.extend(dict(case=case,**r) for r in run['reviews'])
        contributions.extend(dict(case=case,**r) for r in reconcile(run['holdings'],aa))
    for mature,premium in [(12,20),(15,25),(18,30)]:
        scenario=deepcopy(ds)
        for k,r in scenario.items():
            if r['perimeter_review'] and r['perimeter_review']['status']=='COMPARABLE' and not r['missing']:
                r['valuation_status']=valuation_gate(r['normalized_pe'],r,mature,premium)
            decision_diff.append(dict(case=f'VVAL_{mature}_{premium}',year=r['year'],ticker=r['ticker'],
                main_decision=ds[k]['valuation_status'],scenario_decision=r['valuation_status'],different=r['valuation_status']!=ds[k]['valuation_status']))
        record(f'VVAL_{mature}_{premium}',simulate('VVAL',scenario),'FIXED_PE_THRESHOLDS_SAME_EVIDENCE',base_final)
    # Separate Bazin/Graham diagnostics; they do not alter the four main cases.
    for name,predicate in [('BAZIN_6_DIAGNOSTIC',lambda r:r['bazin_normalized_dy'] is not None and r['bazin_normalized_dy']>=.06),
                           ('GRAHAM_22_5_DIAGNOSTIC',lambda r:r['graham_pe_pb'] is not None and r['graham_pe_pb']<=22.5)]:
        scenario=deepcopy(ds)
        for r in scenario.values():
            if r['valuation_status'].startswith('PASS') and not predicate(r):r['valuation_status']='INDETERMINATE_DIAGNOSTIC'
        record(name,simulate('VVAL',scenario),'DIAGNOSTIC_ONLY_MISSING_IS_NOT_ZERO',base_final)
    record('VVAL_ALL_UNKNOWN_INCLUDED',simulate('VVAL',ds,include=lambda r,d:d['valuation_status']=='INDETERMINATE'),'DOCUMENTATION_INCLUSION',base_final)
    allq=simulate('VQ',ds,include=lambda r,d:d['quality_category']=='INDETERMINATE')
    if any(not math.isclose(a['return_pct'],b['return_pct'],abs_tol=1e-10) for a,b in zip(allq['annual'],v0['annual'])):raise ValueError('All-unknown scenario must reproduce base')
    record('VQ_ALL_UNKNOWN_INCLUDED',allq,'DOCUMENTATION_INCLUSION_NOT_QUALIFIED',v0final)
    for c in sorted({r['cnpj'] for r in raw}):
        record('VVAL_INCLUDE_'+c,conditional_run('VVAL',ds,include=lambda r,d,c=c:r['cnpj']==c and d['valuation_status']=='INDETERMINATE'),
               'ONE_ISSUER_UNKNOWN_INCLUDED',base_final)
        # Starting from the all-unknown hypothetical cohort makes this symmetric
        # and avoids pretending a single issuer can survive every B00S FAIL.
        conditional=deepcopy(ds)
        record('VQ_ALL_EXCEPT_'+c,simulate('VQ',conditional,include=lambda r,d,c=c:r['cnpj']!=c and d['quality_category']=='INDETERMINATE'),
               'ONE_ISSUER_WITHHELD_FROM_ALL_UNKNOWN_COHORT',v0final)
    write(RESULT/'sensitivity_summary.csv',summaries);write(RESULT/'sensitivity_annual_pct.csv',paths)
    write(RESULT/'sensitivity_attribution.csv',contributions);write(RESULT/'sensitivity_reviews.csv',trades)
    write(RESULT/'valuation_threshold_decisions.csv',decision_diff)
    print('Scenarios',len(summaries),'twelve-period scenarios',sum(r['periods']==12 for r in summaries))

if __name__=='__main__':main()
