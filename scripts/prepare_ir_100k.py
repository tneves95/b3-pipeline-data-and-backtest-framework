#!/usr/bin/env python3
"""Read-only extraction of frozen selections/events and local nominal SQLite prices."""
import ast, csv, gzip, hashlib, json, sqlite3, sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.audit_alerts_v12 import context, m, rights
from scripts.reconstruct_barsi_v13 import load_events, FAMILIES
ROOT=Path('research/ir_100k_inputs')
V13=Path('research/graham_v6_comparison/checkpoint_v13_2026_10_07')
U13=Path('research/graham_v6_comparison/audit_v13_inputs')
def read(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def yes(v):return str(v).lower() in ('true','1','1.0')
def literal(p,name):
    tree=ast.parse(Path(p).read_text())
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def prepare():
    stdout=sys.stdout;book,ge,_,sels,re=context();sys.stdout=stdout
    sourcefiles=[Path('graham_final_%s.csv'%y) for y in range(2022,2026)]+[Path('graham_full_universe_2021_triage.csv')]
    sourcefiles += [U13/'universe_v9_snapshot.csv',U13/'build_selection_v9_reference.py',V13/'alternativas_barsi_v13_por_posicao.csv',ROOT/'selection_rows.json',ROOT/'eventos_quantidade_herdados.csv',ROOT/'eventos_retorno_besst2020_v8.csv',ROOT/'compute_besst.py']
    sources=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sourcefiles]
    windows={str(y):list(w) for y,w in m.bridge.WINDOWS.items()}
    selections={};sectors={};eligibility={};evidence=[]
    for y,s in sels.items():
        for rule in ['R00','R03','R16']:
            key=f'{y}|{rule}|central';selections[key]=s['R00' if rule=='R00' else 'R03'];sectors.update({f'{y}|{t}':sec for t,sec in s['sectors'].items()})
        if y==2020:continue
        rows=read('graham_full_universe_2021_triage.csv' if y==2021 else f'graham_final_{y}.csv')
        for r in rows:
            t=r['ticker'];sectors[f'{y}|{t}']=r['sector']
            for rule in ['R00','R03','R16']:
                rr='R00' if rule=='R00' else 'R03';status='INDETERMINATE';reason='Filtros incompletos/nao conclusivos'
                if t in s[rr]:status='PASS';reason='Selecao corrigida congelada'
                else:
                    con=yes(r['concessionaria']);fs=['F1_con' if con else 'F1_non','F2_con' if con else 'F2_'+rr+'_non']
                    if any(r.get(f)=='False' for f in fs):status='FAIL';reason='Reprovacao financeira explicita: '+','.join(f for f in fs if r.get(f)=='False')
                    elif r.get('F3_'+rr)=='False' and r.get('nonpositive_years'):status='FAIL';reason='Lucros nao positivos documentados'
                    elif y==2021 and r.get('F5_growth')=='False' and r.get('growth') not in ('','nan',None):status='FAIL';reason='Crescimento calculado no screener 2021 reprovado'
                    elif r.get('F5_restated_pit')=='False' and r.get('F5_source_refyears') not in ('','incompleto',None):status='FAIL';reason='Crescimento PIT reprovado'
                    elif r.get('F6' if y==2021 else 'F6_final')=='False' and r.get('pe_x_pb') not in ('','nan',None) and yes(r.get('capital_resolved')):status='FAIL';reason='Limite de valuation reprovado com capital resolvido'
                eligibility[f'{y}|{rule}|central|{t}']=[status,reason]
                evidence.append(dict(year=y,rule=rule,scenario='central',ticker=t,status=status,reason=reason,source=str(sourcefiles[4] if y==2021 else sourcefiles[y-2022]),fields=r))
    universe=read(U13/'universe_v9_snapshot.csv');sr=json.loads((ROOT/'selection_rows.json').read_text());sr={(r['year'],r['ticker']):r for r in sr}
    for r in read(V13/'alternativas_barsi_v13_por_posicao.csv'):
        if r['mechanism']!='annual':continue
        selections.setdefault(f"{r['year']}|{r['strategy']}|{r['scenario']}",[]).append(r['ticker'])
    for r in universe:
        y=int(r['entry_year']);t=r['ticker'];sectors[f'{y}|{t}']=r['besst_sector'];s=sr.get((y,t))
        for sc in ['central','conservative']:
            status='INDETERMINATE';reason='Historico fundamental/dividendos incompleto'
            if s is not None:
                status='PASS' if s['cash5' if sc=='central' else 'conservative_b00'] else 'FAIL';reason='Filtro B00 congelado; teto B06 so para compras'
            elif r['profits_known']=='5' and int(r['profits_positive'])<5:status='FAIL';reason='Cinco exercicios conhecidos; lucro nao positivo'
            elif r['sector_admissible']=='0':status='FAIL';reason='Setor fora BESST'
            for rule in ['B00','B00S','B06','B06S']:eligibility[f'{y}|{rule}|{sc}|{t}']=[status,reason]
            evidence.append(dict(year=y,rule='B00/B06',scenario=sc,ticker=t,status=status,reason=reason,source=str(U13/'universe_v9_snapshot.csv'),fields=r))
    events=[asdict(e) for e in ge]+[asdict(e) for e in load_events()[0]]
    known={e['asset'] for e in events}; protected=known|{'BBSE3'}
    for f in json.loads(Path('research/graham_v6_comparison/audit_v12_inputs/verified_facts.json').read_text()):
        if f['ticker']=='BBSE3' and '2020-06-30'<f['ex_date']<='2026-06-30':
            events.append(dict(event_id='V12_BBSE_'+f['ex_date'],date=f['ex_date'],kind='CASH',asset='BBSE3',record_date=book.previous_session(f['ex_date']),amount=f['amount'],source=f['source_url'],note=f['kind']))
    for r in read(ROOT/'eventos_retorno_besst2020_v8.csv'):
        if r['asset'] in protected:continue
        e=dict(event_id=r['event_id'],date=r['effective_date'],kind=r['kind'],asset=r['asset'],source=r['source_url'] or r['source_id'],note='HERDADO_V8; '+r['note'])
        if e['kind']=='CASH':e.update(record_date=r['cum_date'],amount=float(r['amount']))
        elif e['kind']=='QTY':e.update(kind='SPLIT' if float(r['factor'])==10 else 'BONUS',factor=float(r['factor']))
        elif e['kind']=='CONVERSION':e['legs']=[[r['new_asset'],float(r['ratio'])]]
        events.append(e)
    # Additional quantity facts already present in the v9 package; never double-count v8.
    sid={r['ticker']:r['sid'] for r in universe};qs=read(ROOT/'eventos_quantidade_herdados.csv')
    originalnames={t for ss in selections.values() for t in ss}
    residual=originalnames-protected
    for t in residual:
        for r in qs:
            if r['sid']!=sid.get(t) or not '2021-06-30'<r['date']<='2026-06-30' or float(r['q'])==1:continue
            events.append(dict(event_id=f"V9Q_{t}_{r['date']}",date=r['date'],kind='SPLIT' if float(r['q']) in (2,3,4,5,10) else 'BONUS',asset=t,factor=float(r['q']),source='eventos_quantidade_herdados.csv',note='HERDADO; classificacao fiscal da quantidade PROXY'))
    def add(id,d,kind,t,**kw):events.append(dict(event_id=id,date=d,kind=kind,asset=t,source='structural_sources.json',**kw))
    add('IR_AES_AURE','2024-11-01','CONVERSION','AESB3',legs=[['AURE3',.67498865568]],amount=1.18438832610,cash_date='2024-11-08',note='Opcao 1 herdada; novas acoes disponiveis 05/11; base fiscal da parcela em dinheiro PROXY')
    add('IR_TRPL_ISAE','2024-11-18','CONVERSION','TRPL4',legs=[['ISAE4',1]])
    add('IR_ELET_AXIA','2025-11-10','CONVERSION','ELET3',legs=[['AXIA3',1]])
    add('IR_CPLE6_5','2025-11-10','CONVERSION','CPLE6',legs=[['CPLE5',1]])
    add('IR_CPLE5_3','2025-12-22','CONVERSION','CPLE5',legs=[['CPLE3',1]],amount=.7749,cash_date='2025-12-30',note='CPLE7 resgatada; alocacao fiscal PROXY')
    add('IR_AXIA_BONUS','2025-12-26','BONUS_OTHER','AXIA3',record_date='2025-12-19',legs=[['AXIA7',.2628378881074]],unit_cost=49.44,note='B3 OC059/2025 + emissor 08/12/2025; entrega 26/12; cotacoes nominais AXIA7 comprovam negociacao')
    add('IR_NEOE_EXIT','2026-05-15','CASH_OUT','NEOE3',price=34.02,venue='GCAP',note='Resgate compulsorio; disponibilidade efetiva em 15/05')
    # Preserve v9 cash approximation where individual events were never reconstructed.
    D=literal(U13/'build_selection_v9_reference.py','D')
    # Execute only the literal dictionaries and explicit setdefault(...).update literals.
    tree=ast.parse((ROOT/'compute_besst.py').read_text());ns={'D':D}
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('T','WINDOW_CASH','H1_2026') for t in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),'<v9-dictionaries>','exec'),ns)
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='update' and isinstance(n.value.func.value,ast.Call) and isinstance(n.value.func.value.func,ast.Attribute) and isinstance(n.value.func.value.func.value,ast.Name) and n.value.func.value.func.value.id in ('D','T'):exec(compile(ast.Module(body=[n],type_ignores=[]),'<v9-dictionaries>','exec'),ns)
    T=ns['T'];wc=ns['WINDOW_CASH'];h1=ns['H1_2026']
    def dps(t,y):return T.get('ISAE4' if t=='TRPL4' and y>=2025 else t,{}).get(y,0) or 0
    for y in range(2021,2026):
        start,end=windows[str(y)]
        for t in sorted(residual|{'AESB3','AURE3'}):
            if t=='TIET4' or (t=='AESB3' and y>=2024) or (t=='AURE3' and y<2024):continue
            et={'TRPL4':'ISAE4' if y>=2024 else t,'ELET3':'AXIA3' if y==2025 else t}.get(t,t)
            fac=1
            for r in qs:
                if r['sid']==sid.get(t) and start<r['date']<=end:fac*=float(r['q'])
            cps=wc.get((y,t),.5*dps(t,y)+(.5*dps(et,y+1) if y<2025 else h1.get(t,.5*dps(t,y)))*fac)
            ed=end; keep=False
            if t=='NEOE3' and y==2025:cps=.8930651324;ed='2026-05-04';keep=True
            if t=='ELET3' and y==2025:cps=3.647180054
            if t=='CPLE6' and y==2025:cps=.5*dps(t,y);ed='2025-11-07';et=t # actual CPLE3 cash follows conversion
            if t=='AURE3' and y==2025:cps=0
            if cps:
                add(f'PROXY_CASH_{y}_{t}',ed,'CASH',et,amount=cps/fac,reinvest='KEEP_CASH' if keep else '',note='PROXY_ANNUAL_CASH: balde contabil junho; nao e data-ex/pagamento documental',proxy=True)
    # No exact nominal price is replaced by forward fill. A small replay fixture is portable to CI.
    names=originalnames|{e['asset'] for e in events}|{t for e in events for t,f in e.get('legs',[])}|{'BOVA11','ITSA3'}
    con=sqlite3.connect('file:b3_market_data.sqlite?mode=ro',uri=True)
    prices=defaultdict(dict)
    for t in sorted(names):
        for d,p in con.execute("select date,close from prices where ticker=? and date between '2020-06-30' and '2026-07-31' and close>0",(t,)):prices[t][d]=p
    cal=[r[0] for r in con.execute("select distinct date from prices where date between '2020-06-30' and '2026-07-31' order by date")];con.close()
    # Frozen nominal prices take precedence, as in v11.2; retain SQL values separately only if divergent.
    discrepancies=[]
    for t,ds in book.prices.items():
        if t not in names:continue
        for d,p in ds.items():
            if d<'2020-06-30' or d>'2026-06-30':continue
            if d in prices[t] and abs(prices[t][d]-p)>1e-8:discrepancies.append(dict(ticker=t,date=d,sqlite=prices[t][d],frozen=p))
            prices[t][d]=p
    facts=json.loads(Path('research/graham_v6_comparison/itsa_rights_verified_2026_10_07.json').read_text())
    cache=ROOT/'rights_quotes.json'
    if cache.exists():
        qc=json.loads(cache.read_text());quotes=qc['quotes'];archives=qc['archives']
    else:
        quotes,archives=rights.collect_quotes(Path('data/raw'),facts)
        cache.write_text(json.dumps(dict(quotes=[q for q in quotes if any(r['available_from']<=q['date']<=r['exercise_deadline_issuer'] for r in facts) and q['ticker']!='ITSA3'],archives=archives),sort_keys=True))
    for r in re:
        for ticker,market,name in [('ITSA1','010','standard_quote'),('ITSA1F','020','fractional_quote')]:
            candidates=[q for q in quotes if q['ticker']==ticker and q['market']==market and q['isin']==r['rights_isin'] and rights.traded(q) and r['available_from']<=q['date']<=r['exercise_deadline_issuer']]
            q=min(candidates,key=lambda z:z['date']);assert q['date']==r['sale_date'];r[name]=q
    data=dict(windows=windows,prices=prices,calendar=cal,selections=selections,sectors=sectors,eligibility=eligibility,events=sorted(events,key=lambda e:(e['date'],e.get('order',50),e['event_id'])),rights=re,source_hashes=sources,price_conflicts=discrepancies,archives=archives)
    ROOT.mkdir(exist_ok=True,parents=True)
    (ROOT/'replay.json.gz').write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,sort_keys=True).encode(),mtime=0))
    (ROOT/'eligibility_evidence.json.gz').write_bytes(gzip.compress(json.dumps(evidence,ensure_ascii=False,sort_keys=True).encode(),mtime=0))
    print('prepared',len(events),'events',len(names),'securities',sum(map(len,prices.values())),'quotes',len(discrepancies),'conflicts',flush=True)
if __name__=='__main__':prepare()
