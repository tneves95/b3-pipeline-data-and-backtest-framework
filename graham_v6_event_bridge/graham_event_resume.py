#!/usr/bin/env python3
"""Retomada Graham: motor legado v6, complementos B3 e carteiras corrigidas.

Execute da raiz do repositório: python graham_v6_event_bridge/graham_event_resume.py
Para testar apenas paridade do pacote original: --legacy-only.
O script NÃO modifica scripts anteriores, a base SQLite nem as seleções.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math, sqlite3, sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from motor_eventos import Event, Engine, PriceBook, Coverage

WINDOWS = {
    2020: ('2020-06-30', '2021-06-30'),
    2021: ('2021-06-30', '2022-06-30'),
    2022: ('2022-06-30', '2023-06-30'),
    2023: ('2023-06-30', '2024-06-28'),
    2024: ('2024-06-28', '2025-06-30'),
    2025: ('2025-06-30', '2026-06-30'),
}
LEGACY_RETURNS = {
    2020: {'R00':-.10805958695585346,'R03':.2446490194308152,'R16':.37682595688601533},
    2021: {'R00':.1970115521926642,'R03':.09267160243531747,'R16':.09267160243531747},
    2022: {'R00':.370888778944839,'R03':.5439827954420227,'R16':.5338595774190839},
    2023: {'R00':.15339450821712253,'R03':.14476178316388344,'R16':.14863502225019032},
    2024: {'R00':.5077432369983123,'R03':.33138657046461983,'R16':.2915252198882591},
    2025: {'R00':.15820923892087735,'R03':.3275467969582439,'R16':.2871067513831422},
}
# Datas-com confirmadas; fatores são multiplicadores da quantidade de ações.
# Eventos B3 encontrados para a mesma data-com prevalecem, após normalização.
KNOWN_STOCK = [
    ('ITSA3','2021-12-20','BONUS',1.05,'ITAUSA_HIST'),
    ('ITSA3','2022-11-10','BONUS',1.10,'ITAUSA_HIST'),
    ('ITSA3','2023-11-27','BONUS',1.05,'ITAUSA_HIST'),
    ('ITSA3','2024-12-02','BONUS',1.05,'ITAUSA_HIST'),
    ('ITSA3','2025-12-18','BONUS',1.02,'ITAUSA_RI_2025'),
    ('UNIP3','2024-04-18','BONUS',1.10,'B3_2024'),
    ('SBSP3','2025-12-23','BONUS',1.029646975,'SBSP_RI_2025'),
    ('SBSP3','2026-03-19','BONUS',1.00160980322,'B3_2026'),
    ('SBSP3','2026-04-28','SPLIT',5.0,'SBSP_RI_2026'),
]

def writecsv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0]) if rows else ['status','detail']
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def readcsv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def load_legacy():
    with gzip.open(HERE/'legacy_v6_inputs.json.gz','rt',encoding='utf-8') as f: d=json.load(f)
    book=PriceBook(d['prices'],d['calendar'])
    events=[Event(**r) for r in d['events']]
    coverage=[Coverage(**r) for r in d['coverage']]
    return book,events,coverage

def next_trade(calendar, date_com):
    from bisect import bisect_right
    i=bisect_right(calendar,date_com)
    return calendar[i] if i<len(calendar) else None

def event_id(prefix, *parts):
    s='|'.join(map(str,parts)).encode()
    return prefix+'_'+hashlib.sha256(s).hexdigest()[:20]

def load_extra_events(calendar, legacy_events):
    """Arquivos CSV existentes: não refaz a coleta B3 e não transforma preço ajustado."""
    cash_path=ROOT/'graham_v6_extra_cash.csv'
    stock_path=ROOT/'graham_v6_extra_stock.csv'
    for p in (cash_path,stock_path):
        if not p.is_file():raise FileNotFoundError(f'{p} ausente; não refazer etapas já concluídas')
    cash=readcsv(cash_path); stock=readcsv(stock_path)
    added=[];audit=[];issues=[]; cash_seen=set(); existing_cash={}
    for e in legacy_events:
        if e.kind=='CASH':existing_cash.setdefault((e.asset,e.record_date),[]).append(e)
    for r in cash:
        tick=r['ticker'].strip();dc=r['event_date'].strip();typ=r['event_type'].strip()
        value=float(r['value']);
        if not math.isfinite(value) or value<=0:issues.append({'status':'CASH_INVALIDO','detail':str(r)});continue
        unique=(tick,dc,typ,round(value,11));
        if unique in cash_seen:continue
        cash_seen.add(unique)
        ex=next_trade(calendar,dc)
        if not ex:issues.append({'status':'SEM_DATA_EX','detail':str(unique)});continue
        # O catálogo antigo já conciliou os pagamentos dessas datas-com.
        if (tick,dc) in existing_cash:
            audit.append(dict(ticker=tick,com_date=dc,ex_date=ex,kind='CASH',value=value,
                              source=r['source'],status='PREFERIDO_V6',info=typ));continue
        e=Event(event_id('b3_cash',tick,dc,typ,value),ex,'CASH',tick,
                r.get('source') or 'B3',record_date=dc,amount=value,
                note=f'{typ}; coluna event_date interpretada como DATA-COM; direito nominal da B3')
        added.append(e)
        audit.append(dict(ticker=tick,com_date=dc,ex_date=ex,kind='CASH',value=value,
                          source=e.source,status='ADICIONADO_B3',info=typ))
    actions={}
    for r in stock:
        if r['action_type']!='BONUS_SHARES':
            issues.append({'status':'ACAO_ESTRUTURAL_NAO_MAPEADA','detail':str(r)});continue
        tick=r['ticker'];dc=r['ex_date'] # O campo nomeado ex_date contém, nestes registros, a DATA-COM.
        mult=1.0+float(r['factor'])/100.0
        if mult<=0 or not math.isfinite(mult):issues.append({'status':'FATOR_INVALIDO','detail':str(r)});continue
        actions[(tick,dc,'BONUS')]=(mult,r.get('source') or 'B3','B3_PCT')
    for tick,dc,kind,mult,source in KNOWN_STOCK:
        key=(tick,dc,kind)
        if key in actions:
            prior=actions[key][0]
            if not math.isclose(prior,mult,rel_tol=1e-7,abs_tol=1e-8):
                issues.append({'status':'FATOR_DIVERGENTE','detail':f'{key}: B3={prior}; referência={mult}'})
        else:actions[key]=(mult,source,'COMPLEMENTO_DOCUMENTADO')
    existing_struct={(e.asset,e.date,e.kind) for e in legacy_events if e.kind in {'BONUS','SPLIT'}}
    for (tick,dc,kind),(mult,src,origin) in sorted(actions.items()):
        ex=next_trade(calendar,dc)
        if not ex:issues.append({'status':'SEM_DATA_EX','detail':str((tick,dc,kind))});continue
        if (tick,ex,kind) in existing_struct:
            audit.append(dict(ticker=tick,com_date=dc,ex_date=ex,kind=kind,value=mult,source=src,
                              status='PREFERIDO_V6',info=origin));continue
        e=Event(event_id('corp',tick,dc,kind,mult),ex,kind,tick,src,
                record_date='',factor=mult,note=f'data-com={dc}; origem={origin}; conversão para multiplicador de ações')
        added.append(e)
        audit.append(dict(ticker=tick,com_date=dc,ex_date=ex,kind=kind,value=mult,source=src,
                          status='ADICIONADO',info=origin))
    return added,audit,issues

def legacy_parity(book, events):
    eng=Engine(book,events)
    original=readcsv(HERE/'legacy_v6_selections.csv')
    results=[]
    for y,(start,end) in WINDOWS.items():
        for rule in ('R00','R03','R16'):
            w={r['ticker']:float(r['weight']) for r in original if int(r['year'])==y and r['rule']==rule}
            st=eng.initialize(start,w);eng.advance(st,end)
            got=eng.result(st,require_complete=False)['return'];ref=LEGACY_RETURNS[y][rule]
            results.append({'year':y,'rule':rule,'calculated':got,'reference_v6':ref,'difference':got-ref,
                            'status':'OK' if abs(got-ref)<=1e-9 else 'FAIL'})
    return results

def expand_with_sqlite(legacy_book, tickers):
    """Preços NOMINAIS. Cotação original v6 tem precedência onde já conciliada."""
    db=ROOT/'b3_market_data.sqlite'
    if not db.is_file():raise FileNotFoundError(db)
    prices={t:dict(v) for t,v in legacy_book.prices.items()}
    calendar=set(legacy_book.calendar)
    with sqlite3.connect(db) as con:
        fields={r[1] for r in con.execute('PRAGMA table_info(prices)')}
        if not {'ticker','date','close'}.issubset(fields):raise RuntimeError(f'Colunas de preços ausentes: {fields}')
        names=sorted(tickers)
        for k in range(0,len(names),70):
            batch=names[k:k+70];marks=','.join('?'*len(batch))
            sql=(f'SELECT ticker,date,close FROM prices WHERE ticker IN ({marks}) '
                 "AND date BETWEEN '2020-06-30' AND '2026-06-30' AND close>0")
            for ticker,d,p in con.execute(sql,batch):
                try: price=float(p)
                except (TypeError,ValueError):continue
                if math.isfinite(price) and price>0:
                    prices.setdefault(ticker,{}).setdefault(d,price)
                    calendar.add(d)
    return PriceBook(prices,sorted(calendar))

def compute_corrected(book, events, coverage):
    import graham_recalc_returns_2020_2026 as original
    # Importa apenas seleções/pesos já corrigidos. NÃO importa cálculo adj_close.
    sels=original.load_corrected()
    eng=Engine(book,events,coverage)
    annual=[];positions=[];issues=[]
    for year,(start,end) in WINDOWS.items():
        s=sels[year]
        weights={
            'R00':original.equal_weights(s['R00']),
            'R03':original.equal_weights(s['R03']),
            'R16':original.sector_weights(s['R03'],s['sectors']),
        }
        annual_row={'year':year,'start':start,'end':end,'BOVA11':book.exact('BOVA11',end)/book.exact('BOVA11',start)-1}
        for rule,w in weights.items():
            returns={}; coverage_gaps=[];failures=[]
            for ticker,weight in sorted(w.items()):
                try:
                    st=eng.initialize(start,{ticker:1.0});eng.advance(st,end)
                    result=eng.result(st,require_complete=False)
                    returns[ticker]=result['return']
                    coverage_gaps.extend(result['coverage_gaps'])
                    positions.append({'year':year,'rule':rule,'ticker':ticker,'weight':weight,
                                      'return_value':result['return'],'contribution':weight*result['return'],
                                      'source_coverage':'V6_COBERTO' if not result['coverage_gaps'] else 'NOVO_NAO_CONCILIADO',
                                      'status':'CALCULADO'})
                except Exception as ex:
                    failures.append(ticker)
                    issues.append({'year':year,'rule':rule,'ticker':ticker,'kind':type(ex).__name__,'detail':str(ex)})
                    positions.append({'year':year,'rule':rule,'ticker':ticker,'weight':weight,
                                      'return_value':'','contribution':'','source_coverage':'INCOMPLETO','status':'FALHOU'})
            if failures:
                annual_row[rule]='';annual_row[rule+'_status']='INCOMPLETO'
                annual_row[rule+'_unverified']=';'.join(sorted(set(failures)))
            else:
                annual_row[rule]=sum(w[t]*returns[t] for t in w)
                annual_row[rule+'_status']='CALCULADO_PROVISORIO' if coverage_gaps else 'COBERTURA_V6'
                annual_row[rule+'_unverified']=';'.join(sorted({g['asset'] for g in coverage_gaps}))
                # Validação: o motor multiativo precisa bater com a soma das posições.
                try:
                    st=eng.initialize(start,w);eng.advance(st,end)
                    direct=eng.result(st,require_complete=False)['return']
                    if not math.isclose(direct,annual_row[rule],rel_tol=1e-10,abs_tol=1e-9):
                        issues.append({'year':year,'rule':rule,'ticker':'CARTEIRA','kind':'DIVERGENCIA_MULTIATIVO',
                                       'detail':f'individual={annual_row[rule]} multiativo={direct}'})
                        annual_row[rule+'_status']='INCONSISTENTE'
                except Exception as ex:
                    issues.append({'year':year,'rule':rule,'ticker':'CARTEIRA','kind':type(ex).__name__,
                                   'detail':'falha na validação multiativo: '+str(ex)})
                    annual_row[rule+'_status']='INCONSISTENTE'
        annual.append(annual_row)
    return annual,positions,issues

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--legacy-only',action='store_true');a=parser.parse_args()
    out=ROOT/'graham_v6_event_results';out.mkdir(exist_ok=True)
    book,ev,cov=load_legacy()
    parity=legacy_parity(book,ev)
    writecsv(out/'paridade_original_v6.csv',parity)
    print('Paridade original v6:',sum(r['status']=='OK' for r in parity),'/',len(parity),'OK')
    if any(r['status']=='FAIL' for r in parity):
        print('ABORTADO: motor/base não reproduz os 18 legados');return 2
    if a.legacy_only:return 0
    extra,audit,issues=load_extra_events(book.calendar,ev)
    writecsv(out/'eventos_extra_normalizados.csv',audit)
    print('Complementos:',len(extra),'|',dict(Counter(e.kind for e in extra)))
    import graham_recalc_returns_2020_2026 as original
    selections=original.load_corrected();ticker_set={t for d in selections.values() for t in (d['R00']+d['R03'])}
    ticker_set|={'BOVA11'}|{e.asset for e in ev+extra}|{a for e in ev for a,_ in e.legs}
    mergedbook=expand_with_sqlite(book,ticker_set)
    # O motor v6 não é modificado; apenas recebe eventos adicionais com IDs rastreáveis.
    all_events=ev+extra
    annual,positions,failures=compute_corrected(mergedbook,all_events,cov)
    writecsv(out/'graham_corrigido_anuais_eventos.csv',annual)
    writecsv(out/'graham_corrigido_posicoes_eventos.csv',positions)
    writecsv(out/'graham_corrigido_pendencias_eventos.csv',failures+[
        {'year':'','rule':'','ticker':'','kind':r['status'],'detail':r['detail']} for r in issues])
    summary=[]
    for rule in ['R00','R03','R16','BOVA11']:
        x=[r[rule] for r in annual if isinstance(r.get(rule),(float,int))]
        if len(x)!=len(WINDOWS):
            summary.append({'rule':rule,'return_2020_2026':'','cagr':'','status':'INCOMPLETO'});continue
        f=math.prod(1+v for v in x)
        status='CALCULADO_PROVISORIO' if any(r.get(rule+'_status')!='COBERTURA_V6' for r in annual) and rule!='BOVA11' else 'COBERTURA_V6'
        summary.append({'rule':rule,'return_2020_2026':f-1,'cagr':f**(1/6)-1,'status':status})
    writecsv(out/'graham_corrigido_resumo_eventos.csv',summary)
    print('Resumo indicativo (ainda sem certificação documental):')
    for r in summary:print(' ',r)
    print('Anomalias/pendências:',len(failures)+len(issues),'| saídas em',out)
    return 0

if __name__=='__main__':raise SystemExit(main())
