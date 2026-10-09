"""Provent classification overlay; never changes an accepted economic event."""
from collections import defaultdict
from copy import deepcopy
from datetime import date
import json
import math
import re
import unicodedata

from monthly_contributions import events, security, ROOT, OUT, gzread
from monthly_tax_freeze import TAX
from b00s_variants import jsonwrite, sha


def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn').upper()


def historical_jcp_rate(tax_date):return .175 if tax_date>='2026-01-01' else .15


def dividend_tax(monthly_total,year,transition=False):
    return monthly_total*.10 if year>=2026 and monthly_total>50000 and not transition else 0.


def jcp_retention(value,basis,tax_date,*,unknown_gross=False):
    if basis=='NET_ALREADY_WITHHELD':return 0.
    if basis=='GROSS' or unknown_gross:return value*historical_jcp_rate(tax_date)
    return 0.


def overlay():
    original=json.loads((TAX/'inputs/event_tax_evidence.json').read_text());result=deepcopy(original)
    raw=gzread(OUT/'cache/market.json.gz');isin_t={r['isin_code']:security(r['ticker']) for r in raw['isins']}
    bykey=defaultdict(list)
    for r in raw['actions']:
        if r['event_type'] in ['JCP','CASH_DIVIDEND']:
            bykey[isin_t.get(r['isin_code']),r['event_date']].append(r)
    legacy={}
    for name in ['checkpoint_v12_2026_10_07/eventos_cenario_v12.json','checkpoint_v13_2026_10_07/eventos_utilizados.json']:
        for r in json.loads((ROOT/'research/graham_v6_comparison'/name).read_text()):legacy[r['event_id']]=r
    bonus_sources=json.loads((TAX/'inputs/sources/pr2_structural_sources.json').read_text())
    bonus_itsa=next(r for r in bonus_sources if r['id']=='ITSA_BONUS_COST')
    bonus_pssa=next(r for r in bonus_sources if r['id']=='PSSA_BONUS_COST')
    source_rows=[]
    for es in events().values():
        for e in es:
            r=result[e['id']];t=e['ticker'];d=e['ex_date'];old=legacy.get(e.get('legacy_id'),{})
            note=old.get('note','');text=norm(note+' '+old.get('event_id',''))
            if e['kind']=='SHARES':
                if t=='ITSA3':
                    dates=[x for x in bonus_itsa['facts'] if 0<(date.fromisoformat(d)-date.fromisoformat(x)).days<=4]
                    if len(dates)==1:r.update(unit_basis=bonus_itsa['facts'][dates[0]],share_kind='BONUS_SHARES',fiscal_status='DECLARED_BONUS_COST_PR2',evidence=bonus_itsa['url']+'; preserved PR2 source ITSA_BONUS_COST.gz; record '+dates[0])
                if t=='PSSA3' and d==bonus_pssa['facts']['date_ex']:
                    r.update(unit_basis=bonus_pssa['facts']['unit_cost'],share_kind='BONUS_SHARES',fiscal_status='DECLARED_BONUS_COST_PR2',evidence=bonus_pssa['url']+'; preserved PR2 source PSSA_BONUS_COST.gz')
                if old.get('kind') in ['BONUS','SPLIT'] and not r['share_kind']:
                    r['share_kind']='BONUS_SHARES' if old['kind']=='BONUS' else 'STOCK_SPLIT'
                    if old['kind']=='SPLIT':r.update(unit_basis=0,fiscal_status='TOTAL_COST_PRESERVED')
                continue
            if e['kind']!='DISTRIBUTION':continue
            if r['payment_date'] and '/' in r['payment_date']:
                dd,mm,yy=r['payment_date'].split('/');r['payment_date']=f'{yy}-{mm}-{dd}'
            found=re.search(r'(?:pagamento|payment)=([0-9]{4}-[0-9]{2}-[0-9]{2}(?:;[0-9]{4}-[0-9]{2}-[0-9]{2})*)',note,re.I)
            if found:r['payment_date']=found[1]
            matches=[a for a in bykey[t,e.get('record_date')] if math.isclose(a['value'],e['amount'],rel_tol=1e-10,abs_tol=1e-12)]
            types={a['event_type'] for a in matches}
            if len(types)==1 and not r['original_type']:
                r['original_type']=next(iter(types));r['evidence']='Exact ticker/record date/nominal amount match to frozen SQLite/B3'
            label=norm(note.split(';')[0]+' '+old.get('event_id',''))
            if 'CAPITAL_REDUCTION' in label or 'RESTITUICAO' in label or '_REST_' in label:
                r['original_type']='CAPITAL_RETURN';r['fiscal_status']='UNRESOLVED_CAPITAL_RETURN_COST'
            elif 'JCP' in label:r['original_type']='JCP'
            elif 'DIV' in label:r['original_type']='CASH_DIVIDEND'
            typ=norm(r['original_type'])
            if 'JCP' in typ:r['distribution_type']='JCP'
            elif 'DIV' in typ:r['distribution_type']='DIVIDEND'
            elif typ=='CAPITAL_RETURN':r['distribution_type']='CAPITAL_RETURN'
            else:r['distribution_type']='UNKNOWN'
            if 'BRUTO' in text:r.update(amount_basis='GROSS',evidence=note)
            elif 'LIQUIDO' in text and 'NAO LIQUIDO' not in text:r.update(amount_basis='NET_ALREADY_WITHHELD',evidence=note)
            # Ex-date entitlement is not proof of taxable credit. When all known
            # candidate dates share the same legal rate, the rate is unambiguous.
            pd=r['payment_date'].split(';') if r['payment_date'] else []
            rd=old.get('record_date',e.get('record_date',d))
            if pd and len({historical_jcp_rate(x) for x in pd+[rd,d]})==1:
                r['rate_status']='CERTIFIED_SAME_RATE_WINDOW';r['tax_rate']=historical_jcp_rate(pd[0])
            else:r['rate_status']='UNRESOLVED_PAYMENT_OR_CREDIT_DATE';r['tax_rate']=None
            if t in ['ITUB3','ITUB4'] and math.isclose(e['amount'],.015,abs_tol=1e-12):
                r.update(distribution_type='JCP',amount_basis='NET_ALREADY_WITHHELD',
                    evidence='inputs/sources/itau_monthly_net_fact.json; recurring net monthly amount; overrides inherited CASH_DIVIDEND label',
                    fiscal_status='NO_DOUBLE_WITHHOLDING_ISSUER_NET_POLICY')
            if t=='XPBR31':r.update(distribution_type='FOREIGN_BDR_DISTRIBUTION',amount_basis='GROSS',fiscal_status='UNRESOLVED_FOREIGN_INCOME_TAX',evidence='PR5 explicitly reinvests gross USD distribution translated by PTAX; no tax-residency/foreign-credit proof')
            if r['distribution_type']=='JCP' and r['amount_basis']=='GROSS' and r['tax_rate'] is not None:
                r['fiscal_status']='JCP_GROSS_RATE_SUPPORTED_PAYMENT_CREDIT_TIMING_QUALIFIED'
            r['legacy_note']=note
    jsonwrite(TAX/'inputs/event_tax_evidence_stage2.json',result)
    for p in (TAX/'inputs/sources').glob('*'):
        source_rows.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
    jsonwrite(TAX/'inputs/stage2_sources.json',source_rows)
    return result


if __name__=='__main__':
    r=overlay()
    from collections import Counter
    print(Counter((x.get('distribution_type'),x['amount_basis']) for x in r.values() if x['economic_kind']=='DISTRIBUTION'))
