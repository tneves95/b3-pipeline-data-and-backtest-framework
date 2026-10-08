#!/usr/bin/env python3
"""Incremental PIT reconstruction, separate from the immutable first checkpoint."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/returns_2014_2026_selection'
DATES = {int(r['year']):r['date'] for r in csv.DictReader((ROOT/'research/returns_2014_2026_results/ibov_june_closes.csv').open())}


def ident(x): return re.sub(r'\D','',str(x)).zfill(14)
def norm(x): return ''.join(c for c in unicodedata.normalize('NFKD',str(x).upper()) if not unicodedata.combining(c))
def csvzip(z,n): return pd.read_csv(z.open(n),sep=';',encoding='latin1',dtype=str,keep_default_na=False)
def dump(name,rows):
    if not rows: return
    OUT.mkdir(exist_ok=True,parents=True)
    with (OUT/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def gzwrite(path,data):
    with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as f:f.write(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
def gzread(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def num(v):
    try:
        x=float(v);return x if math.isfinite(x) else None
    except (TypeError,ValueError):return None


def extract_archive(root,year):
    """Keep only screening facts, actual receipt, version, perimeter and period."""
    facts=[]
    fn=root/f'data/cvm/dfp_cia_aberta_{year}.zip'
    with ZipFile(fn) as z:
        meta=csvzip(z,f'dfp_cia_aberta_{year}.csv')
        meta=meta[['CNPJ_CIA','DT_REFER','VERSAO','DT_RECEB','ID_DOC']].drop_duplicates()
        # The statement CSV has no document ID. If metadata reuses its key,
        # the latest receipt is the conservative availability bound.
        key=['CNPJ_CIA','DT_REFER','VERSAO']
        collisions=meta[meta.duplicated(key,keep=False)]
        if not collisions.empty:
            (OUT/'cache'/f'metadata_collisions_{year}.json').write_text(collisions.to_json(orient='records',force_ascii=False))
            meta=meta.sort_values(['DT_RECEB','ID_DOC']).drop_duplicates(key,keep='last')
        for perimeter in ['ind','con']:
            for statement in ['DRE','BPA','BPP','DFC_MI','DFC_MD']:
                member=f'dfp_cia_aberta_{statement}_{perimeter}_{year}.csv'
                if member not in z.namelist():continue
                d=csvzip(z,member)
                ds=d.DS_CONTA.str.strip();cd=d.CD_CONTA
                masks={}
                if statement=='DRE':
                    masks={'ni':cd.str.fullmatch(r'3\.\d{2}') & ds.str.startswith('Lucro') & ds.str.contains('Período'),
                           'revenue':cd.eq('3.01'),
                           'ebit':cd.str.fullmatch(r'3\.\d{2}') & ds.str.startswith('Resultado Antes do Resultado Financeiro')}
                elif statement=='BPA':masks={'assets':cd.eq('1'),'ca':cd.eq('1.01')}
                elif statement=='BPP':
                    masks={'equity':cd.str.fullmatch(r'2\.\d{2}') & ds.str.startswith('Patrimônio Líquido'),
                           'cl':cd.eq('2.01'),'capital':cd.eq('2.03.01'),
                           'debt_current':cd.eq('2.01.04'),'debt_long':cd.eq('2.02.01')}
                else:
                    masks={'ocf':cd.eq('6.01'), 'distributions':cd.str.startswith('6.03') &
                        ds.str.contains(r'dividend|juros.*capital|jcp|jscp',case=False,regex=True) &
                        ~ds.str.contains(r'recebid|investid|n[aã]o controlad|revers|prescrit',case=False,regex=True)}
                for metric,mask in masks.items():
                    selected=d[mask].merge(meta,on=['CNPJ_CIA','DT_REFER','VERSAO'],how='left',validate='many_to_one')
                    for r in selected.to_dict('records'):
                        if not isinstance(r['DT_RECEB'],str) or not r['DT_RECEB']:continue
                        end=r['DT_FIM_EXERC'];start=r.get('DT_INI_EXERC','')
                        # Yearly income/flows: do not mistake a quarter or a transition period for a year.
                        if statement in ['DRE','DFC_MI','DFC_MD'] and (not start or
                            (pd.Timestamp(end)-pd.Timestamp(start)).days < 330):continue
                        value=num(r['VL_CONTA'])
                        if value is None:continue
                        if r['ESCALA_MOEDA']=='UNIDADE':value/=1000
                        if r['ESCALA_MOEDA'] not in ['UNIDADE','MIL']:continue
                        facts.append(dict(cnpj=ident(r['CNPJ_CIA']),year=int(end[:4]),period_end=end,
                            received=r['DT_RECEB'],reference=r['DT_REFER'],version=int(r['VERSAO']),
                            docid=r['ID_DOC'],perimeter=perimeter,metric=metric,value=value,
                            account=r['CD_CONTA'],description=r['DS_CONTA'],source=member))
    return facts


def build(args):
    root=args.data_root.resolve();OUT.mkdir(exist_ok=True,parents=True)
    cache=OUT/'cache';cache.mkdir(exist_ok=True)
    for year in range(2010,2026):
        p=cache/f'dfp_{year}.json.gz'
        if p.exists():continue
        rows=extract_archive(root,year);gzwrite(p,rows)
        print('PIT statement facts',year,len(rows),flush=True)
    registry=[];caps=[]
    for year in range(2010,2026):
        path=cache/f'registry_capital_{year}.json.gz'
        if path.exists():continue
        sectors=[];capital=[];securities=[]
        with ZipFile(root/f'data/cvm/fca_cia_aberta_{year}.zip') as z:
            meta=csvzip(z,f'fca_cia_aberta_{year}.csv')[['ID_DOC','DT_RECEB','LINK_DOC']]
            for kind in ['geral','valor_mobiliario']:
                d=csvzip(z,f'fca_cia_aberta_{kind}_{year}.csv').merge(meta,left_on='ID_Documento',right_on='ID_DOC',how='left',validate='many_to_one')
                for r in d.to_dict('records'):
                    if not isinstance(r['DT_RECEB'],str) or not r['DT_RECEB']:continue
                    if kind=='geral':
                        sectors.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=r['DT_RECEB'],
                            name=r['Nome_Empresarial'],sector=r['Setor_Atividade'],activity=r['Descricao_Atividade'],
                            cvm=r['Codigo_CVM'],docid=r['ID_DOC'],source=r['LINK_DOC']))
                    elif r['Codigo_Negociacao']:
                        securities.append(dict(cnpj=ident(r['CNPJ_Companhia']),ticker=r['Codigo_Negociacao'],received=r['DT_RECEB'],
                            start=r['Data_Inicio_Negociacao'],end=r['Data_Fim_Negociacao'],docid=r['ID_DOC'],source=r['LINK_DOC']))
        with ZipFile(root/f'data/cvm/fre_cia_aberta_{year}.zip') as z:
            meta=csvzip(z,f'fre_cia_aberta_{year}.csv')[['ID_DOC','DT_RECEB','LINK_DOC']]
            d=csvzip(z,f'fre_cia_aberta_capital_social_{year}.csv')
            d=d[d.Tipo_Capital.eq('Capital Emitido')].merge(meta,left_on='ID_Documento',right_on='ID_DOC',how='left',validate='many_to_one')
            for r in d.to_dict('records'):
                if not isinstance(r['DT_RECEB'],str) or not r['DT_RECEB']:continue
                capital.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=r['DT_RECEB'],approved=r['Data_Autorizacao_Aprovacao'],
                    on=num(r['Quantidade_Acoes_Ordinarias']),pn=num(r['Quantidade_Acoes_Preferenciais']),
                    docid=r['ID_DOC'],source=r['LINK_DOC']))
        gzwrite(path,dict(sectors=sectors,capital=capital,securities=securities))
        print('Registry/capital',year,len(sectors),len(capital),flush=True)
    con=sqlite3.connect((root/'b3_market_data.sqlite').as_uri()+'?mode=ro',uri=True);con.execute('PRAGMA query_only=ON')
    con.row_factory=sqlite3.Row
    marketpath=cache/'market.json.gz'
    if not marketpath.exists():
        quotes=[]
        for year in range(2014,2026):
            dt=DATES[year]
            cal=[r[0] for r in con.execute('SELECT distinct date FROM prices WHERE date<=? ORDER BY date DESC LIMIT 126',(dt,))]
            frame=pd.read_sql('SELECT ticker,date,isin_code,close,volume FROM prices WHERE date BETWEEN ? AND ? AND length(ticker)<=6',con,params=(min(cal),dt))
            group=frame.groupby('ticker').agg(sessions=('date','nunique'),median_volume=('volume','median'),total_volume=('volume','sum')).to_dict('index')
            end=frame[frame.date.eq(dt)]
            for r in end.to_dict('records'):
                if not re.fullmatch(r'[A-Z]{4}(3|4|5|6|7|8|11)',r['ticker']):continue
                quotes.append(r|dict(year=year,**group[r['ticker']] ))
            print('Market liquidity',year,len(end),flush=True)
        mappings=[dict(r) for r in con.execute('SELECT * FROM company_tickers_pit')]
        isins=[dict(r) for r in con.execute('SELECT * FROM company_isin_map')]
        companies=[dict(r) for r in con.execute('SELECT * FROM cvm_companies')]
        actions=[dict(r) for r in con.execute("SELECT * FROM corporate_actions WHERE event_date BETWEEN '2009-01-01' AND '2026-06-30'")]
        gzwrite(marketpath,dict(quotes=quotes,mappings=mappings,isins=isins,companies=companies,actions=actions))
    con.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    build(p.parse_args())
