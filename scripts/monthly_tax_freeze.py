"""Freeze PR6 policy/evidence from local accepted inputs, before monetary runs."""
from datetime import date
import json
import re
from monthly_contributions import events, security, ROOT, OUT, gzread, identities
from b00s_variants import jsonwrite, sha

TAX = ROOT/'research/monthly_tax_2014_2026'
POLICY = dict(
    baseline_commit='e3b7c597c83454da34f6461ab68aeb206b0135be',
    initial_capital=100000, monthly_contribution=2500, contributions=144,
    ordinary_rate=.15, daytrade_rate=.20, monthly_stock_exemption=20000,
    ordinary_irrf=.00005, ordinary_irrf_waiver=1, daytrade_irrf=.01, minimum_darf=10,
    jcp_rate_through_2025=.15, jcp_rate_from_2026=.175,
    dividend_2026_monthly_issuer_threshold=50000, dividend_2026_rate=.10,
    cpf='Separate alternative CPF per portfolio, one broker, no external income',
    sale_settlement='Same-close internal funding inherited from PR5; no new D+2 strategy',
    payment_calendar='Last B3 session of following month, explicit bank-calendar proxy; final June liability July31',
    irrf_credit='Same-year ordinary/daytrade credits separately; year-end unused credit exported for DIRPF/refund, no fictitious refund',
    reservation='Assess known month sales and reserve liability before reinvestment; IRRF credited once',
    minimum_darf_rule='Carry sub-BRL10 amounts separately by revenue code, fully reserved',
    daytrade='Match same-day exchange buys/sales before weighted old inventory; entitlement is not exchange purchase',
    june_financing='PR5 gross sale targets; scale positive purchase deficits to available cash after reserve; no tax optimization',
    unknown_bonus_basis='UNRESOLVED: zero incremental cost central; ex-close incremental cost sensitivity, not certified bounds',
    unknown_share_kind='UNRESOLVED: total cost preserved central; positive noninteger increment treated as bonus only in cost sensitivity',
    xp_spinoff='UNRESOLVED: allocate parent basis by observed ex-date relative values; zero-child-allocation sensitivity',
    axia_bonus='UNRESOLVED: zero central / ex-close cost sensitivity; do not import different PR2 ex-date',
    redemption='UNRESOLVED: separate GCAP15 positive gains, no bolsa loss offset or20k exemption; 35k sale exemption sensitivity',
    conversion_boot='UNRESOLVED: cost allocated cash/shares by observed values; positive cash-leg gain GCAP; zero cash-cost sensitivity',
    unknown_jcp='No deduction in CERTIFIED_PARTIAL; separate unknown-gross and unknown-net sensitivities',
    unknown_payment_date='Ownership record date is not certified taxable credit; ex-date rate only conditional sensitivity',
    dividend_2026='Aggregate known pay/credit dates by payer; unknown dates separately ex-date proxy; external CPF income unavailable',
    units='Fractional theoretical quantities; moving total basis per security/class; no transaction costs',
    reporting='Holding NAV net of paid taxes and unpaid liability; separate liquidation on actual taxed units/bases',
    sources=[
      'https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/'+s
      for s in ['bolsa-de-valores','compensacoes','isencoes','retencoes']]+[
      'https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=67494',
      'https://www.planalto.gov.br/ccivil_03/leis/l9249.htm',
      'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm',
      'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm'])


def freeze():
    target=TAX/'inputs/tax_policy_freeze.json'
    if target.exists():
        if json.loads(target.read_text())!=POLICY:raise ValueError('Policy already frozen')
        return
    (TAX/'inputs').mkdir(parents=True,exist_ok=True)
    jsonwrite(target,POLICY)


def classify():
    raw=gzread(OUT/'cache/market.json.gz');meta=identities()
    isin_t={r['isin_code']:security(r['ticker']) for r in raw['isins']}
    fre=[];sources=[]
    for name in ['owned_capital_events_fre.json','continuation_capital_events_fre.json','b00s_initial_capital_events_fre.json']:
        p=OUT/name;sources.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
        fre.extend(dict(r,cache_file=str(p.relative_to(ROOT))) for r in json.loads(p.read_text()))
    result={}
    for es in events().values():
        for e in es:
            t=e['ticker'];d=e['ex_date'];kind=e['kind']
            row=dict(event_id=e['id'],ticker=t,ex_date=d,economic_kind=kind,source=e['source'],
                original_type=e.get('original_type',''),amount_basis='UNKNOWN',fiscal_status='UNRESOLVED',
                payment_date=e.get('payment_date',''),credit_date='',unit_basis=None,evidence='',share_kind='')
            if kind=='SHARES':
                matches=[r for r in raw['actions'] if isin_t.get(r['isin_code'])==t
                    and r['event_date']==e.get('record_date') and r['factor'] is not None
                    and abs(1+float(r['factor'])/100-e['factor'])<1e-8]
                typ={r['event_type'] for r in matches}
                if len(typ)==1:row['share_kind']=next(iter(typ));row['evidence']='Frozen SQLite/B3 action type'
                cn=meta.get(t,{}).get('cnpj','');candidates=[]
                for r in fre:
                    if re.sub(r'\D','',r.get('CNPJ_Companhia',''))!=cn:continue
                    rd=r.get('Data_Deliberacao',r.get('Data_Aprovacao',''))
                    if not rd or rd[:4]!=d[:4] or not 0<=(date.fromisoformat(d)-date.fromisoformat(rd)).days<180:continue
                    if 'Tipo_Evento' in r:
                        before=float(r.get('Quantidade_Total_Acoes_Antes_Aprovacao') or 0)
                        after=float(r.get('Quantidade_Total_Acoes_Depois_Aprovacao') or 0)
                        if before and abs(after/before-e['factor'])<1e-6:
                            row['share_kind']={'Bonificação':'BONUS_SHARES','Desdobramento':'STOCK_SPLIT','Grupamento':'REVERSE_SPLIT'}.get(r['Tipo_Evento'],r['Tipo_Evento'])
                            row['evidence']=r['cache_file']+'; FRE '+r['ID_Documento']+' '+r['Tipo_Evento']
                    wording=(r.get('Criterio_Determinacao_Preco_Emissao','')+' '+r.get('Forma_Integralizacao','')).lower()
                    ratio=float(r.get('Subscricao_Capital_Anterior') or 0)/100;price=float(r.get('Preco_Emissao') or 0)
                    if abs(1+ratio-e['factor'])<1e-6 and price>0 and 'custo' in wording and ('bonific' in wording or row['share_kind']=='BONUS_SHARES'):
                        if r.get('Fator_Cotacao')=='R$ por Lote de Mil':price/=1000
                        candidates.append((price,r))
                prices={v for v,r in candidates}
                if len(prices)==1:
                    price,r=candidates[0];row.update(unit_basis=price,share_kind='BONUS_SHARES',fiscal_status='DECLARED_BONUS_COST',evidence=r['cache_file']+'; FRE '+r['ID_Documento']+'; '+r['Criterio_Determinacao_Preco_Emissao'])
                elif row['share_kind'] in ['STOCK_SPLIT','REVERSE_SPLIT']:row.update(unit_basis=0,fiscal_status='TOTAL_COST_PRESERVED')
            elif kind=='RIGHT':row.update(unit_basis=0,fiscal_status='GRANTED_RIGHT_ZERO_ACQUISITION_COST')
            elif kind=='RIGHT_REINVEST':row.update(fiscal_status='ORDINARY_RIGHT_SALE_NO_20K_EXEMPTION')
            elif kind=='CONVERSION' and not e.get('amount'):row.update(fiscal_status='CONDITIONAL_COST_CARRYOVER')
            result[e['id']]=row
    jsonwrite(TAX/'inputs/event_tax_evidence.json',result)
    jsonwrite(TAX/'inputs/evidence_sources.json',sources)
    print('Frozen policy and event evidence',len(result),flush=True)


if __name__=='__main__':freeze();classify()
