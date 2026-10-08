#!/usr/bin/env python3
"""Screen historical June universes using only facts received by each cutoff."""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from stage1_pit import ROOT,OUT,DATES,dump,gzread,gzwrite,ident,norm

# Historical security roots. CNPJ/sector/name evidence comes from FCA files
# received by the formation date; the security itself must occur in COTAHIST.
ALIASES={
 'TBLE':'02474103000119','AEDU':'04310392000146','ALLL':'02387241000160',
 'ABRE':'02541982000154','KROT':'02800026000140','BRIN':'11721921000160',
 'VAGR':'05799312000120','BICB':'07450604000189','BPNM':'59285411000113',
 'HRTP':'10629105000168','IDNT':'02365069000144','BISA':'07700557000184',
 'BHGR':'08723106000125','AORE':'10345009000198','INET':'00359742000108',
 'JBDU':'60637238000154','MLFT':'60543816000193','PTPA':'91820068000172',
 'RNAR':'86550951000150','SGAS':'33228024000151','SNSL':'04065791000199',
 'VVAR':'33041260065290','CMGR':'03467321000199','BTTL':'42331462000131',
 'PARC':'42278473000103','DMMO':'08926302000105',
}
EXCLUDE_UNIT_ROOTS={'BBTG'}  # BBTG11 represented two separate legal issuers.


def classify(sector,activity,name):
    s=norm(sector);a=norm(activity+' '+name)
    besst=None;block=None
    if 'ENERGIA ELETRICA' in s:besst='Energia';block='Utilidades públicas'
    elif 'SANEAMENTO' in s:besst='Saneamento';block='Utilidades públicas'
    elif 'TELECOMUNICACOES' in s:besst='Telecom'
    elif 'SEGURADORAS' in s:besst='Seguros';block='Financeiro'
    elif 'BANCOS' in s:besst='Bancos';block='Financeiro'
    elif any(x in s for x in ['INTERMEDIACAO FINANCEIRA','BOLSAS DE VALORES','ARRENDAMENTO MERCANTIL','CREDITO IMOBILIARIO']):block='Financeiro'
    if any(x in s for x in ['MAQUINAS, EQUIPAMENTOS','MAQS., EQUIP.','SERVICOS TRANSPORTE']):block='Bens industriais'
    if 'SERVICOS MEDICOS' in s or ('FARMACEUTICO' in s and any(x in a for x in ['MEDICAMENTO','FARMACEUT','BIOLAB'])):block='Saúde'
    if 'COMERCIO' in s and any(x in a for x in ['MEDICAMENTO','DROGARIA','FARMACIA','FARMACEUT']):block='Saúde'
    if 'ITAUSA' in a and 'SEM SETOR' in s:block='Financeiro'
    # Same strict BESST taxonomy as the preserved v13 screen.
    if any(x in a for x in ['CORRETAGEM','CORRETORA','ADMINISTRACAO DE BENEFICIOS','ADMINISTRADORA DE BENEFICIOS','QUALICORP','WIZ ']):besst=None
    if 'SANEAMENTO' in s and 'GAS' in a and not any(x in a for x in ['ESGOTO','ABASTECIMENTO DE AGUA']):besst=None
    if 'SANEAMENTO' in s and any(x in a for x in ['RESIDUO','AMBIENTAL']) and 'AGUA' not in a:besst=None
    return besst,block


class Evidence:
    def __init__(self):
        self.facts=[];self.sectors=defaultdict(list);self.capital=defaultdict(list)
        for y in range(2010,2026):
            self.facts.extend(gzread(OUT/f'cache/dfp_{y}.json.gz'))
            d=gzread(OUT/f'cache/registry_capital_{y}.json.gz')
            for r in d['sectors']:self.sectors[r['cnpj']].append(r)
            for r in d['capital']:self.capital[r['cnpj']].append(r)
        extra=OUT/'cache/supplement.json.gz'
        if extra.exists():
            d=gzread(extra);self.facts.extend(d['facts'])
            for r in d['capital']:self.capital[r['cnpj']].append(r)
        # Reject same-code/different-account collisions in banking charts.
        descriptions={'ca':'ATIVO CIRCULANTE','cl':'PASSIVO CIRCULANTE','capital':'CAPITAL SOCIAL'}
        self.facts=[r for r in self.facts if r['metric'] not in descriptions or norm(r['description']).startswith(descriptions[r['metric']])]
        # Already recovered originals repair NI gaps without changing SQLite.
        recovered=ROOT/'research/returns_2014_2026_inputs/cvm_recovery/recovered_income.csv'
        for r in csv.DictReader(recovered.open()):
            self.facts.append(dict(cnpj=ident(r['cnpj']),year=int(r['period_end'][:4]),period_end=r['period_end'],
                received=r['received'],reference=r['period_end'],version=1,docid=r['document_id'],
                perimeter={'1':'ind','2':'con'}[r['information_type_code']],metric='ni',value=float(r['statement_value']),
                account=r['account'],description=r['description'],source='recovered_original_'+r['document_id']))
        supplemental=OUT/'recovered_facts.json'
        if supplemental.exists():self.facts.extend(json.loads(supplemental.read_text()))
        # ENET may serialize an undisclosed comparative income column as all
        # zeros. Such a column is missing evidence, not a proven zero profit.
        dre=defaultdict(list)
        for r in self.facts:
            if r['metric'] in ['ni','revenue','ebit']:
                dre[r['cnpj'],r['docid'],r['year'],r['perimeter']].append(r)
        blank={k for k,rs in dre.items() if any(r['metric']=='revenue' for r in rs) and all(r['value']==0 for r in rs)}
        self.blank_income_columns=sorted(blank)
        self.facts=[r for r in self.facts if not (r['metric'] in ['ni','revenue','ebit'] and (r['cnpj'],r['docid'],r['year'],r['perimeter']) in blank)]
        self.market=gzread(OUT/'cache/market.json.gz')
        treasury=OUT/'cache/treasury_classes.json.gz'
        self.treasury=gzread(treasury)['treasury'] if treasury.exists() else []
        self.foundations=gzread(treasury).get('foundations',[]) if treasury.exists() else []
        self.tmap=defaultdict(list);self.imap=defaultdict(set)
        for r in self.market['mappings']:self.tmap[r['ticker']].append(r)
        for r in self.market['isins']:self.imap[r['isin_code']].add(ident(r['cnpj']))
        self.facts.sort(key=lambda r:(r['received'],r['reference'],r['version'],r['source'].startswith('recovered_original')))
        self.divyears=defaultdict(set)
        # Historical distributions on all known ISIN classes prove recurrence at
        # issuer level, never fill a missing event with a zero.
        for r in self.market['actions']:
            if r['event_type'] not in ['CASH_DIVIDEND','JCP'] or not r['value'] or r['value']<=0:continue
            for c in self.imap[r['isin_code']]:self.divyears[c].add(int(r['event_date'][:4]))

    def identity(self,r):
        t=r['ticker'];dt=r['date']
        if t[:4] in ALIASES:return ALIASES[t[:4]],'COTAHIST_FCA_HISTORICAL_ROOT'
        cs={ident(x['cnpj']) for x in self.tmap[t] if (not x['start_date'] or x['start_date']<=dt) and (not x['end_date'] or x['end_date']>=dt)}
        if len(cs)==1:return next(iter(cs)),'FCA_TICKER_INTERVAL'
        cs=self.imap[r['isin_code']]
        if len(cs)==1:return next(iter(cs)),'OBSERVED_ISIN_CNPJ'
        return '', 'UNRESOLVED_IDENTITY'

    def asof(self,year):
        dt=DATES[year];idx={};flows=defaultdict(list)
        for r in self.facts:
            if r['received']<=dt and r['period_end']<=dt:
                key=(r['cnpj'],r['year'],r['perimeter'],r['metric'])
                if r['metric'].startswith('distributions'):
                    flows[key].append(r)
                else:idx[key]=r
        for key,rs in flows.items():
            latest=max((r['received'],r['reference'],r['version']) for r in rs)
            current=[r for r in rs if (r['received'],r['reference'],r['version'])==latest]
            idx[key]=max(current,key=lambda r:abs(r['value']))
        sectors={};caps={}
        for c,rs in self.sectors.items():
            valid=[r for r in rs if r['received']<=dt]
            if valid:sectors[c]=max(valid,key=lambda r:r['received'])
        for c,rs in self.capital.items():
            valid=[r for r in rs if r['received']<=dt and r['approved'] and r['approved']<=dt and r['on'] is not None and r['pn'] is not None]
            if valid:caps[c]=max(valid,key=lambda r:(r['approved'],r['received']))
        self.treasury_asof={}
        for r in sorted(self.treasury,key=lambda r:(r['received'],r['reference'])):
            if r['received']<=dt and r['composition_date']<=dt and r['last_change']<=dt:self.treasury_asof[r['cnpj']]=r
        self.founded_asof={}
        for r in sorted(self.foundations,key=lambda r:r['received']):
            if r['received']<=dt and r['founded']:self.founded_asof[r['cnpj']]=r
        return idx,sectors,caps


def metric(idx,c,y,name,perimeter=None):
    if perimeter:return idx.get((c,y,perimeter,name))
    # An empty IFRS comparative DRE can coexist with a reported balance sheet.
    # Choose the perimeter per statement, never use its empty NI as a loss.
    availability='ni' if name in ['ni','revenue','ebit'] else 'assets'
    scope='con' if (c,y,'con',availability) in idx else 'ind'
    return idx.get((c,y,scope,name))
def val(idx,c,y,name,perimeter=None):
    r=metric(idx,c,y,name,perimeter);return None if r is None else r['value']
def status(flags):
    if any(v is False for v in flags):return 'FAIL'
    if all(v is True for v in flags):return 'PASS'
    return 'INDETERMINATE'


def run():
    e=Evidence();rows=[];caprows=[];idrows=[];selected=[];traces=[]
    fxpath=OUT/'bcb_ptax.json'
    d=json.loads(fxpath.read_text())['data']['value']
    fx={y:sum(r['cotacaoVenda'] for r in d if r['dataHoraCotacao'].startswith(str(y)))/sum(r['dataHoraCotacao'].startswith(str(y)) for r in d) for y in range(2013,2020)}
    fx.update({2020:5.1556,2021:5.3964,2022:5.1623,2023:4.9941,2024:5.3910})
    for y in range(2014,2026):
        idx,sectors,caps=e.asof(y);dt=DATES[y];start=max(2009,y-10)
        quotes=[r for r in e.market['quotes'] if r['year']==y and len(r['ticker'])==5 and r['ticker'][-1] in '345678']
        groups=defaultdict(list)
        for r in quotes:
            c,how=e.identity(r);r=r|dict(cnpj=c,identity_source=how)
            sec=sectors.get(c,{})
            bs,block=classify(sec.get('sector',''),sec.get('activity',''),sec.get('name',''))
            r.update(sector=sec.get('sector',''),company=sec.get('name',''),sector_received=sec.get('received',''),sector_docid=sec.get('docid',''),besst=bs,block=block)
            idrows.append(r)
            if c:groups[c].append(r)
        for c,qs in groups.items():
            cap=caps.get(c);sector=qs[0]['sector'];rep=max(qs,key=lambda r:r['total_volume'])
            tradable=rep['sessions']>=math.ceil(.8*126) and rep['median_volume']>=1e6 and rep['close']>=2
            if cap and y==2014:
                ps={r['ticker'][-1]:r['close'] for r in qs}
                on=ps.get('3');pn=ps.get('4')
                if pn is None:
                    pns=[ps[k] for k in '5678' if k in ps]
                    if len(pns)==1:pn=pns[0]
                mc=(cap['on']*(on or 0)+cap['pn']*(pn or 0)) if (on is not None or cap['on']==0) and (pn is not None or cap['pn']==0) else None
                upper=None;cap_status='REPORTED_CAPITAL_PENDING_EVENT_RECONCILIATION';cap_note=''
                if c=='90400888000142':
                    # May FRE still reports the pre-June 55:1 capital. Only an
                    # exclusion bound is needed; do not publish a fictitious
                    # multi-trillion actual market cap or fractional share count.
                    upper=(cap['on']+cap['pn']+19002100957)/55*max(ps.values())
                    mc=None;cap_status='POST_REVERSE_SPLIT_UPPER_BOUND';cap_note='Bonificação de 19002100957 PN e grupamento 55:1 em 02/06/2014; https://www.santander.com.br/document/wps/AGE_Edital_Convocacao_Bonificacao_Grupamento_Units.pdf ; https://cms.santander.com.br/sites/WRI/documentos/url-rel-fr-url6/19-09-11_142232_fr%202014%20v22.pdf'
                caprows.append(dict(cnpj=c,company=rep['company'],block=rep['block'],ticker=rep['ticker'],
                    on_shares=cap['on'],pn_shares=cap['pn'],on_price=on,pn_price=pn,company_market_cap=mc,
                    capital_received=cap['received'],capital_approved=cap['approved'],capital_docid=cap['docid'],
                    sector_received=rep['sector_received'],sector_docid=rep['sector_docid'],source=cap['source'],
                    market_cap_upper_bound=upper,capital_status=cap_status,capital_note=cap_note))
            def distributions(yr):
                if yr in e.divyears[c]:return True
                rs=[metric(idx,c,yr,k,'ind') for k in ['distributions','distributions_dmpl','distributions_dva']]
                if any(r is not None and abs(r['value'])>0 for r in rs):return True
                return False if all(r is not None for r in rs) else None
            def trace(strategy,ticker,first):
                facts=[]
                for fy in range(first,y):
                    for key in ['ni','assets','ca','cl','capital','debt_current','debt_long','ocf','ebit','equity','revenue']:
                        r=metric(idx,c,fy,key)
                        if r is not None:facts.append(r)
                    for key in ['ni','equity','distributions','distributions_dmpl','distributions_dva']:
                        r=metric(idx,c,fy,key,'ind')
                        if r is not None and r not in facts:facts.append(r)
                traces.append(dict(year=y,date=dt,strategy=strategy,ticker=ticker,cnpj=c,
                    market=next(r for r in qs if r['ticker']==ticker),capital=cap,
                    treasury=e.treasury_asof.get(c),foundation=e.founded_asof.get(c),facts=facts,
                    distribution_years_b3=sorted(fy for fy in e.divyears[c] if first<=fy<y)))
            # B00S does not shorten its five-year requirements.
            bs=rep['besst'];n5=[val(idx,c,fy,'ni') for fy in range(y-5,y)]
            d5=[distributions(fy) for fy in range(y-5,y)]
            positive5=False if any(v is not None and v<=0 for v in n5) else (True if all(v is not None for v in n5) else None)
            founded=e.founded_asof.get(c,{}).get('founded','')
            if founded and int(founded[:4])>y-5:positive5=False
            bflags=[tradable,bs is not None,positive5,False if False in d5 else (True if all(v is True for v in d5) else None)]
            br=dict(year=y,date=dt,strategy='B00S',ticker=rep['ticker'],cnpj=c,company=rep['company'],sector=bs or sector,
                status=status(bflags),liquidity=tradable,F1=None,F2=None,F3=positive5,F4=bflags[-1],F5=None,F6=None,
                history_start=y-5,missing_earnings=';'.join(str(fy) for fy,v in zip(range(y-5,y),n5) if v is None),
                missing_distributions=';'.join(str(fy) for fy,v in zip(range(y-5,y),d5) if v is None),
                growth=None,pe_pb=None,source_ids=';'.join(sorted({metric(idx,c,fy,'ni')['docid'] for fy in range(y-5,y) if metric(idx,c,fy,'ni')})))
            rows.append(br)
            if br['status']=='PASS':
                selected.append(br)
                if y<=2016:trace('B00S',rep['ticker'],y-5)
            on=next((r for r in qs if r['ticker'].endswith('3')),None)
            if not on:continue
            trade=on['sessions']>=math.ceil(.8*126) and on['median_volume']>=1e6 and on['close']>=2
            sec=norm(sector);concession=any(s in sec for s in ['ENERGIA ELETRICA','SANEAMENTO','TELECOMUNICACOES']) or on['ticker'][:4] in ['CCRO','ECOR']
            size=val(idx,c,y-1,'assets' if concession else 'revenue')
            f1=None if size is None else size>= (50000 if concession else 100000)*fx[y-1]
            ca,cl=val(idx,c,y-1,'ca'),val(idx,c,y-1,'cl')
            debt1,debt2,capital=val(idx,c,y-1,'debt_current'),val(idx,c,y-1,'debt_long'),val(idx,c,y-1,'capital')
            f2=(None if None in [debt1,debt2,capital] else debt1+debt2<=2*capital) if concession else (None if ca is None or cl is None or cl<=0 else ca/cl>=1.5)
            ni=[val(idx,c,fy,'ni') for fy in range(start,y)]
            f3=None
            known_losses={start+j for j,v in enumerate(ni) if v is not None and v<=0}
            # A known violation proves failure even if another year is missing.
            known_failure=(any(v is not None and v<=0 for v in ni[-3:]) or
                any(fy+1 in known_losses for fy in known_losses) or
                len(ni)-len(known_losses)<math.ceil(.8*len(ni)))
            if all(v is not None for v in ni):
                loss=[start+i for i,v in enumerate(ni) if v<=0]
                support=True
                for fy in loss:
                    ocf,ebit,eq,cay,cly=[val(idx,c,fy,k) for k in ['ocf','ebit','equity','ca','cl']]
                    checks=[None if v is None else v>0 for v in [ocf,ebit,eq,cly]]
                    checks.append(None if cay is None or cly is None or cly<=0 else cay/cly>=1)
                    support=False if support is False or False in checks else (None if support is None or None in checks else True)
                basic=sum(v>0 for v in ni)>=math.ceil(.8*len(ni)) and all(fy+1 not in loss for fy in loss) and all(v>0 for v in ni[-3:]) and sum(ni)>0
                f3=False if not basic else support
            if known_failure:f3=False
            if founded and int(founded[:4])>start:f3=False
            divs=[distributions(fy) for fy in range(start,y)]
            f4=False if False in divs else (True if all(v is True for v in divs) else None)
            early=[val(idx,c,fy,'ni','ind') for fy in range(start,start+3)]
            late=[val(idx,c,fy,'ni','ind') for fy in range(y-3,y)]
            growth=None if any(v is None for v in early+late) or sum(early)<=0 else sum(late)/sum(early)-1
            f5=None if growth is None else growth>=.33
            eq=val(idx,c,y-1,'equity','ind');earn=val(idx,c,y-1,'ni','ind')
            pepb=None if cap is None or eq is None or earn is None or eq<=0 or earn<=0 else (on['close']*(cap['on']+cap['pn']))**2/(eq*earn*1e6)
            # Gross capital is an upper bound; a pass is safe, a failure needs treasury evidence.
            f6=True if pepb is not None and 0<pepb<=22.5 else None
            treasury=e.treasury_asof.get(c);pepb_ex=None
            if pepb is not None and treasury is not None:
                gross=cap['on']+cap['pn'];tr=treasury['quantity']
                if 0<=tr<gross:
                    pepb_ex=pepb*((gross-tr)/gross)**2
                    f6=0<pepb_ex<=22.5
            gr=dict(year=y,date=dt,strategy='R03',ticker=on['ticker'],cnpj=c,company=on['company'],sector=sector,
                status=status([trade,f1,f2,f3,f4,f5,f6]),liquidity=trade,F1=f1,F2=f2,F3=f3,F4=f4,F5=f5,F6=f6,
                history_start=start,missing_earnings=';'.join(str(fy) for fy,v in zip(range(start,y),ni) if v is None),
                missing_distributions=';'.join(str(fy) for fy,v in zip(range(start,y),divs) if v is None),growth=growth,pe_pb=pepb,
                source_ids=';'.join(sorted({r['docid'] for fy in range(start,y) for r in [metric(idx,c,fy,'ni'),metric(idx,c,fy,'ni','ind')] if r})))
            rows.append(gr)
            if gr['status']=='PASS':
                selected.append(gr)
                if y<=2015:trace('R03',on['ticker'],start)
        print(y, {s:[r['ticker'] for r in selected if r['year']==y and r['strategy']==s] for s in ['R03','B00S']},flush=True)
    dump('screening.csv',rows);dump('selected.csv',selected);dump('identity_sector.csv',idrows);dump('market_cap_2014.csv',caprows)
    established=[]
    for strategy,years in [('R03',[2014,2015]),('B00S',[2014,2015,2016])]:
        for y in years:
            subset=[r for r in selected if r['strategy']==strategy and r['year']==y]
            assert not [r for r in rows if r['strategy']==strategy and r['year']==y and r['status']=='INDETERMINATE']
            sectors={r['sector'] for r in subset}
            for r in subset:
                w=1/len(subset) if strategy=='R03' else 1/len(sectors)/sum(x['sector']==r['sector'] for x in subset)
                established.append(dict(year=y,date=DATES[y],strategy=strategy,ticker=r['ticker'],cnpj=r['cnpj'],sector=r['sector'],weight=w,status='ESTABLISHED_IN_SCREENED_UNIVERSE'))
    dump('established_selections.csv',established)
    gzwrite(OUT/'established_selection_evidence.json.gz',traces)
    for block in ['Bens industriais','Financeiro','Utilidades públicas','Saúde']:
        rank=sorted([r for r in caprows if r['block']==block and r['company_market_cap'] is not None],key=lambda r:r['company_market_cap'],reverse=True)
        print('BH2014',block,[(r['ticker'],round(r['company_market_cap']/1e9,3)) for r in rank[:6]],flush=True)


if __name__=='__main__':run()
