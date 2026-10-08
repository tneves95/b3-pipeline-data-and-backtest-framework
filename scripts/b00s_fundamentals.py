"""V2 economic valuation and documentary evidence; no portfolio outcomes imported.

Amounts in financial source tables are issuer facts (BRL), not simulated wealth.
Ratios retain their units explicitly. Missing evidence remains None.
"""
from b00s_variants import INPUT, RESULT, OUT, DATES, candidates, read, write, jsonwrite, sha
from stage1_pit import gzread, norm, num
from stage1_select import Evidence, metric
from b00s_documentary import load_reviews, adjust_profits, profit_interval
from collections import defaultdict
from datetime import date
import json
import math
import statistics

DIMENSIONS=('durability','capital_economics','earnings_reliability','financial_resilience','capital_allocation','governance')

def valuation_gate(pe, evidence, mature=15, premium=25):
    if pe is None or not math.isfinite(pe) or pe<=0:return 'INDETERMINATE'
    if pe<=mature:return 'PASS_MATURE'
    if pe>premium:return 'REJECTED_PRICE'
    keys=['real_eps_cagr','average_payout','return_on_capital_median','inflation_reference','solidity_proven']
    if any(evidence.get(k) is None for k in keys):return 'INDETERMINATE'
    if (evidence['real_eps_cagr']>=.04 and evidence['average_payout']<=.80 and
        evidence['return_on_capital_median']>=evidence['inflation_reference']+.06 and evidence['solidity_proven'] is True):
        return 'PASS_REINVESTOR'
    return 'REJECTED_REINVESTMENT'

def quality_gate(dimensions):
    if set(dimensions)!=set(DIMENSIONS):raise ValueError('Six non-compensatory dimensions required')
    if any(r['status']=='REJECTED_EVIDENCED' and r.get('material_evidence') for r in dimensions.values()):return 'REJECTED_EVIDENCED'
    if any(r['status'] not in ['SATISFACTORY','HIGH'] or not r.get('evidence') for r in dimensions.values()):return 'INDETERMINATE'
    return 'QUALIFIED_HIGH' if all(r['status']=='HIGH' for r in dimensions.values()) else 'QUALIFIED_SATISFACTORY'

def normalized_profit(profits, factors):
    if len(profits)!=5 or len(factors)!=5 or any(x is None or not math.isfinite(x) or x<=0 for x in profits+factors):return None
    return statistics.median(x*f for x,f in zip(profits,factors))

def class_capitalization(classes):
    if not classes or any(r.get('quantity') is None or r['quantity']<0 or r['quantity'] and (r.get('price') is None or r['price']<=0) for r in classes):return None
    return math.fsum(r['quantity']*(r.get('price') or 0) for r in classes)

def source(r):
    return {k:r.get(k,'') for k in ['docid','received','reference','period_end','perimeter','account','description','source','archive_sha256','url']}

def value(r):
    if r is None:return None
    return r['value']*(1000 if r['scale']=='MIL' else 1)

class Fundamentals:
    def __init__(self):
        self.base=Evidence();self.data=gzread(INPUT/'cvm_directed_extract.json.gz')
        self.facts=defaultdict(list);self.fre=defaultdict(list);self.audits=defaultdict(list)
        for r in self.data['facts']:self.facts[r['cnpj']].append(r)
        for r in self.data['fre']:self.fre[r['cnpj']].append(r)
        for r in self.data['audits']:self.audits[r['cnpj']].append(r)
        self.identities=read(OUT/'identity_sector.csv')
        self.ipca={}
        level=1.
        for r in json.loads((INPUT/'ipca_sgs433.json').read_text()):
            day,month,year=map(int,r['data'].split('/'));level*=1+float(r['valor'])/100
            self.ipca[year,month]=level
        self.sources={r['path']:r for r in json.loads((INPUT/'cvm_directed_sources.json').read_text())}
        if (INPUT/'ipca_availability.json').exists():
            for r in json.loads((INPUT/'ipca_availability.json').read_text()):
                if r['release_date']>DATES[r['year']]:raise ValueError('Inflation not known at cutoff')

    def income(self,idx,c,fy,cut):
        rs=[r for r in self.facts[c] if r['year']==fy and r['received']<=cut and r['period_end']<=cut and r['statement']=='DRE'
            and r['period_start'] and (date.fromisoformat(r['period_end'])-date.fromisoformat(r['period_start'])).days>=330]
        attr=[r for r in rs if r['perimeter']=='con' and 'CONTROLADORA' in norm(r['description']) and not r['account'].startswith('3.99')]
        if attr:
            best=max(attr,key=lambda r:(r['received'],r['reference'],r['version']))
            return value(best),source(best),'ATTRIBUTABLE_CONSOLIDATED'
        # Parent-only annual NI is attributable to the issuer's own shareholders,
        # including equity-accounted subsidiaries; never use total consolidated NI.
        old=metric(idx,c,fy,'ni','ind')
        if old:
            evidence=source(old);filename='dfp_cia_aberta_'+old['reference'][:4]+'.zip'
            evidence['archive_sha256']=self.sources.get(filename,{}).get('sha256','')
            evidence['url']=f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DFP/DADOS/{filename}'
            if old['source'].startswith('recovered'):
                evidence['source']='PR3/'+old['source'];evidence['archive_sha256']=''
            return old['value']*1000,evidence,'PARENT_INDIVIDUAL'
        return None,{},'MISSING_ATTRIBUTABLE_PROFIT'

    def capital(self,c,y,cap):
        if not cap:return None,[],['CAPITAL_DOCUMENT_MISSING']
        cut=DATES[y];qs=[r for r in self.identities if r['cnpj']==c and r['year']==str(y)]
        prices={r['ticker'][-1]:float(r['close']) for r in qs if len(r['ticker'])==5}
        classes=[dict(share_class='ON',quantity=cap['on'],price=prices.get('3'))]
        if cap['pn']:
            ids={r['raw']['ID_Capital_Social'] for r in self.fre[c] if r['docid']==cap['docid'] and r['part']=='capital_social'
                 and r['raw']['Tipo_Capital']=='Capital Emitido' and r['raw']['Data_Autorizacao_Aprovacao']==cap['approved']}
            docs=[r for r in self.fre[c] if r['docid']==cap['docid'] and r['part']=='capital_social_classe_acao' and r['raw']['ID_Capital_Social'] in ids]
            byclass={r['raw'].get('Tipo_Classe_Acao_Preferencial'):num(r['raw'].get('Quantidade_Acoes')) for r in docs}
            if len(byclass)>1:
                for cls,q in sorted(byclass.items()):
                    suffix={'Preferencial Classe A':'5','Preferencial Classe B':'6','Preferencial Classe C':'7'}.get(cls)
                    classes.append(dict(share_class=cls,quantity=q,price=prices.get(suffix)))
                if any(q is None for q in byclass.values()) or not math.isclose(sum(q or 0 for q in byclass.values()),cap['pn']):return None,classes,['PN_CLASSES_NOT_RECONCILED']
            else:
                ps=[(k,v) for k,v in prices.items() if k in '45678']
                classes.append(dict(share_class='PN',quantity=cap['pn'],price=ps[0][1] if len(ps)==1 else None))
        missing=[]
        # An issuer's published capital is not adjusted with events first disclosed
        # after the cutoff. Post-receipt capital events require a contemporaneous
        # share-count reconciliation rather than applying an ex-post factor.
        isins={r['isin_code'] for r in qs}
        pending=[e for e in self.base.market['actions'] if e['isin_code'] in isins and e['event_type'] in ['BONUS_SHARES','STOCK_SPLIT','REVERSE_SPLIT'] and cap['received']<e['event_date']<=cut]
        if pending:missing.append('CAPITAL_EVENTS_AFTER_LAST_FRE:'+','.join(sorted({e['event_date'] for e in pending})))
        if class_capitalization(classes) is None:missing.append('UNQUOTED_OR_UNRECONCILED_SHARE_CLASS')
        return (None if missing else class_capitalization(classes)),classes,missing

    def build(self):
        decisions=[];metrics=[];dossiers=[]
        documentary=load_reviews()
        for y in range(2014,2026):
            idx,sectors,caps=self.base.asof(y);cut=DATES[y]
            for candidate in [r for r in candidates() if r['year']==y]:
                c=candidate['cnpj'];t=candidate['ticker'];sector=candidate['sector'];evidence=[];profits=[];income_modes=[]
                for fy in range(y-5,y):
                    n,src,mode=self.income(idx,c,fy,cut);profits.append(n);income_modes.append(mode)
                    if src:evidence.append(dict(fiscal_year=fy,metric='attributable_ni',value=n,**src))
                assessment=documentary.get((y,c))
                reported=adjust_profits(profits,evidence,y,assessment)
                factors=[self.ipca[y,5]/self.ipca[fy,12] for fy in range(y-5,y)]
                ni=normalized_profit(profits,factors)
                interval=profit_interval(profits,factors,y,assessment)
                cap=caps.get(c);mc,classes,missing=self.capital(c,y,cap)
                if ni is None:missing.append('FIVE_COMPARABLE_ATTRIBUTABLE_PROFITS_MISSING')
                if len(set(income_modes))>1 and not (assessment and assessment['valuation'].get('income_modes_reconciled')):
                    missing.append('PARENT_CONSOLIDATED_RECONCILIATION_REQUIRED')
                # Publication metadata and accounts prove availability, not a
                # business/perimeter judgement. Record this review separately.
                fre=[r for r in self.fre[c] if r['received']<=cut]
                payouts=[];dividends=[];payout_sources=[]
                for fy in range(y-5,y):
                    rs=[r for r in fre if r['part']=='distribuicao_dividendos' and r['raw']['Data_Fim_Exercicio_Social']==f'{fy}-12-31']
                    best=max(rs,key=lambda r:(r['received'],r['raw'].get('Data_Referencia',''),r['docid'])) if rs else None
                    payout=num(best['raw'].get('Dividendo_Distribuido_Lucro_Liquido_Ajustado')) if best else None
                    dividend=num(best['raw'].get('Dividendo_Distribuido_Total')) if best else None
                    payouts.append(payout/100 if payout is not None else None);dividends.append(dividend)
                    if best:payout_sources.append(source(best)|{'fiscal_year':fy,'raw':best['raw']})
                avgp=statistics.mean(payouts) if all(v is not None for v in payouts) else None
                eq=metric(idx,c,y-1,'equity','ind');equity=eq['value']*1000 if eq else None
                # Economic ROIC is deliberately not replaced by ROE for utilities.
                roe=[]
                for fy,n in zip(range(y-5,y),profits):
                    a=metric(idx,c,fy-1,'equity','ind');b=metric(idx,c,fy,'equity','ind')
                    roe.append(n/((a['value']+b['value'])*500) if a and b and n is not None and a['value']+b['value']>0 else None)
                roc=statistics.median(roe[-3:]) if sector in ['Bancos','Seguros'] and all(x is not None for x in roe[-3:]) else None
                inflation=self.ipca[y,5]/self.ipca[y-1,5]-1
                pe=mc/ni if mc is not None and ni is not None else None
                mean_ni=statistics.mean(n*f for n,f in zip(profits,factors)) if ni is not None else None
                dy=mean_ni*avgp/mc if mc and mean_ni and avgp is not None else None
                graham=(mc/profits[-1])*(mc/equity) if mc and profits[-1] and equity and equity>0 else None
                # EPS and incremental returns require adjusted class denominators;
                # no premium is granted from growth of aggregate company profit.
                f=dict(year=y,cutoff=cut,ticker=t,cnpj=c,sector=sector,base_status='PASS',
                    normalized_profit=ni,normalization='MEDIAN_FIVE_ANNUAL_NI_IN_KNOWN_MAY_IPCA_PRICES',
                    reported_normalized_profit=normalized_profit(reported,factors),
                    documentary_assessment=assessment,
                    documentary_review_status='ASSESSED' if assessment else 'AWAITING_CHRONOLOGICAL_REVIEW',
                    normalized_profit_interval=interval,
                    income_modes=income_modes,market_cap=mc,capital_classes=classes,capital_source=cap,
                    normalized_pe=pe,real_eps_cagr=None,average_payout=avgp,
                    return_on_capital_median=roc,return_on_capital_kind='ROE_PARENT_AVERAGE_EQUITY' if sector in ['Bancos','Seguros'] else 'ROIC_ND',
                    inflation_reference=inflation,solidity_proven=None,bazin_normalized_dy=dy,
                    bazin_issuer_price_ceiling=mean_ni*avgp/.06 if mean_ni and avgp is not None else None,
                    bazin_mean_distributions_yield=statistics.mean(dividends)/mc if mc and all(v is not None for v in dividends) else None,
                    graham_pe_pb=graham,incremental_return=None,
                    profit_evidence=evidence,payout_evidence=payout_sources,
                    missing=';'.join(missing),quality_category='INDETERMINATE',dossier=f'inputs/dossiers/{c}.json')
                preliminary=valuation_gate(pe,f)
                # Quantitative values alone do not certify the common economic
                # perimeter and extraordinary earnings in the normalized history.
                review_path=INPUT/'valuation_perimeter_reviews.json'
                reviews=json.loads(review_path.read_text()) if review_path.exists() else []
                review=next((r for r in reviews if r['cnpj']==c and y in r['years']),None)
                # Legacy perimeter judgements are historical, superseded by the
                # effective documentary batch. Unreviewed years are not approvals.
                review=assessment['valuation'] if assessment else None
                f['mechanical_valuation_status']=preliminary
                f['perimeter_review']=review
                f['valuation_status']=preliminary if review and review['status']=='COMPARABLE' and not missing else 'INDETERMINATE'
                f['normalized_pe_interval']=None
                if review and review['status']=='COMPARABLE_BOUNDED':
                    # The point from raw accounts is diagnostic, not certified.
                    f['mechanical_normalized_pe']=pe
                    f['normalized_pe']=None;f['normalized_profit']=None
                    if interval and mc is not None and not missing and interval['lower'] and interval['lower']>0:
                        f['normalized_pe_interval']=dict(lower=mc/interval['upper'] if interval['upper'] and interval['upper']>0 else 0,
                                                       upper=mc/interval['lower'])
                        if f['normalized_pe_interval']['upper']<=15:f['valuation_status']='PASS_MATURE'
                    f['bazin_normalized_dy']=None;f['bazin_issuer_price_ceiling']=None
                if not review or review['status'] not in ['COMPARABLE','COMPARABLE_BOUNDED']:f['missing']+=';ECONOMIC_PERIMETER_AND_NONRECURRING_ITEMS_REVIEW'
                if preliminary=='INDETERMINATE' and pe is not None and 15<pe<=25:f['missing']+=';ADJUSTED_REAL_EPS_CAGR;REINVESTMENT_SOLIDITY;'+('ROIC' if sector not in ['Bancos','Seguros'] else 'PRUDENTIAL_CAPITAL_CREDIT_OR_RESERVES')
                decisions.append(f)
                for fy,n,factor,rr in zip(range(y-5,y),profits,factors,roe):
                    metrics.append(dict(year=y,ticker=t,cnpj=c,fiscal_year=fy,attributable_profit=n,ipca_to_known_may=factor,
                        real_profit=n*factor if n is not None else None,roe_parent_average_equity=rr,
                        reported_payout=payouts[fy-(y-5)],reported_distributions=dividends[fy-(y-5)]))
                # Facts available for each dimension; absent qualitative evidence
                # never becomes rejection, a zero score or an approval.
                latest_audits=[a for a in self.audits[c] if a['received']<=cut and a['reference']==f'{y-1}-12-31']
                dims={
                    'durability':dict(status='INDETERMINATE',favorable=sectors.get(c,{}).get('activity',''),
                        missing='Historical concession/contract durability, competitive position and pricing power',evidence=[sectors.get(c,{})]),
                    'capital_economics':dict(status='INDETERMINATE',favorable={'roe_parent_5':roe,'normalized_profit':ni},
                        missing='Cycle-normalized ROIC/incremental returns or risk-adjusted prudential ROE; historical peer/capital comparison',evidence=evidence),
                    'earnings_reliability':dict(status='INDETERMINATE',favorable={'positive_attributable_years':sum(n is not None and n>0 for n in profits),'audit_records':len(latest_audits)},
                        missing='Profit/cash/recurring earnings bridge; provisions and extraordinary items reviewed in dated notes',evidence=[source(a) for a in latest_audits]),
                    'financial_resilience':dict(status='INDETERMINATE',favorable={'parent_equity_latest':equity},
                        missing='BCB Basel/NPL/provision coverage under contemporaneous rules' if sector=='Bancos' else 'SUSEP capital adequacy, technical reserves, claims and underwriting result' if sector=='Seguros' else 'Debt maturity, interest coverage and committed maintenance/expansion CAPEX',evidence=[source(eq)] if eq else []),
                    'capital_allocation':dict(status='INDETERMINATE',favorable={'historical_payout':payouts,'distributions':dividends},
                        missing='Maintenance versus expansion CAPEX, sustainable dividends, adjusted per-share and incremental economic growth',evidence=payout_sources),
                    'governance':dict(status='INDETERMINATE',favorable={'dated_shareholder_right_records':sum(r['part']=='direito_acao' for r in fre),'dated_related_party_records':sum(r['part']=='transacao_parte_relacionada' for r in fre)},
                        missing='Review of material conflicts, related parties and audit opinions before cutoff; no ex-post controversy inference',evidence=[source(a) for a in latest_audits])}
                for d in dims.values():d['contrary_evidence']='No structural rejection established by this extract; missing review is not evidence of poor business quality.'
                if assessment:dims=assessment['dimensions']
                f['quality_category']=quality_gate(dims)
                dossiers.append(dict(year=y,cutoff=cut,ticker=t,cnpj=c,company=candidate['company'],sector=sector,category=quality_gate(dims),
                    assessment_status='ASSESSED' if assessment else 'AWAITING_CHRONOLOGICAL_REVIEW',
                    dimensions=dims,limitation='Documentary economic review of originals' if assessment else 'Structured facts only; economic review outstanding. No quality approval inferred.',
                    special_case='IRBR3 June 2019: only pre-cutoff statements considered; later restatements/scandal cannot be used to reject this entry.' if t=='IRBR3' and y==2019 else ''))
        write(RESULT/'fundamental_metrics_by_fiscal_year.csv',metrics)
        jsonwrite(INPUT/'fundamental_decisions.json',decisions)
        for c in sorted({r['cnpj'] for r in dossiers}):
            group=[r for r in dossiers if r['cnpj']==c];first=group[0]
            # Keep the six-dimension assessment once. Later years carry changed
            # dated facts and evidence, without duplicating unchanged conclusions.
            updates=[]
            for r in group[1:]:
                updates.append({k:r[k] for k in ['year','cutoff','ticker','category','special_case']}|dict(
                    assessment_ref=f'{c}:{r["year"]}' if (r['year'],c) in documentary else None,
                    assessment_status=r['assessment_status'],
                    classification_changed=r['category']!=first['category'] if (r['year'],c) in documentary else None,
                    dimensions=r['dimensions'] if (r['year'],c) in documentary else {},
                    dimension_evidence_updates={k:dict(favorable=v['favorable'],evidence=v['evidence']) for k,v in r['dimensions'].items()}))
            jsonwrite(INPUT/'dossiers'/f'{c}.json',dict(initial_assessment=first,annual_evidence_updates=updates))
        jsonwrite(INPUT/'fundamental_decisions_lock.json',dict(decisions_sha256=sha(INPUT/'fundamental_decisions.json'),
            quantitative_thresholds=[15,25,.04,.20,.06],frozen_before_variant_returns=True,
            documentary_reviews_sha256=sha(INPUT/'economic_reviews.json') if (INPUT/'economic_reviews.json').exists() else None,
            extract_sha256=sha(INPUT/'cvm_directed_extract.json.gz'),ipca_sha256=sha(INPUT/'ipca_sgs433.json')))
        for y in range(2014,2026):
            rs=[r for r in decisions if r['year']==y]
            print(y,{k:sum(r['valuation_status']==k for r in rs) for k in {r['valuation_status'] for r in rs}},'computable PE',sum(r['normalized_pe'] is not None for r in rs))
        return decisions

if __name__=='__main__': Fundamentals().build()
