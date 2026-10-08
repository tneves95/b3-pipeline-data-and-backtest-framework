#!/usr/bin/env python3
"""Fill only columns absent from the first extraction; preserve its cache."""
from stage1_pit import *

def main(root):
    facts=[];capital=[]
    for y in range(2010,2026):
        with ZipFile(root/f'data/cvm/fre_cia_aberta_{y}.zip') as z:
            meta=csvzip(z,f'fre_cia_aberta_{y}.csv')[['ID_DOC','DT_RECEB','LINK_DOC']]
            d=csvzip(z,f'fre_cia_aberta_capital_social_{y}.csv')
            d=d[d.Tipo_Capital.isin(['Capital Integralizado','Capital Subscrito'])].merge(meta,left_on='ID_Documento',right_on='ID_DOC',validate='many_to_one')
            for r in d.to_dict('records'):
                if not r['DT_RECEB']:continue
                capital.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=r['DT_RECEB'],approved=r['Data_Autorizacao_Aprovacao'],
                    on=num(r['Quantidade_Acoes_Ordinarias']),pn=num(r['Quantidade_Acoes_Preferenciais']),docid=r['ID_DOC'],source=r['LINK_DOC'],capital_type=r['Tipo_Capital']))
        with ZipFile(root/f'data/cvm/dfp_cia_aberta_{y}.zip') as z:
            meta=csvzip(z,f'dfp_cia_aberta_{y}.csv')[['CNPJ_CIA','DT_REFER','VERSAO','DT_RECEB','ID_DOC']]
            meta=meta.sort_values(['DT_RECEB','ID_DOC']).drop_duplicates(['CNPJ_CIA','DT_REFER','VERSAO'],keep='last')
            for statement in ['DMPL','DVA']:
                member=f'dfp_cia_aberta_{statement}_ind_{y}.csv'
                if member not in z.namelist():continue
                d=csvzip(z,member)
                ds=d.DS_CONTA.str.strip()
                mask=ds.str.contains(r'dividend|juros.*capital|jcp|jscp',case=False,regex=True)&~ds.str.contains(r'revers|prescrit|n[aã]o controlad',case=False,regex=True)
                if statement=='DVA':mask=d.CD_CONTA.isin(['7.08.04.01','7.08.04.02'])
                d=d[mask].merge(meta,on=['CNPJ_CIA','DT_REFER','VERSAO'],validate='many_to_one')
                for r in d.to_dict('records'):
                    start=r.get('DT_INI_EXERC','');end=r['DT_FIM_EXERC']
                    if not start or not r['DT_RECEB'] or (pd.Timestamp(end)-pd.Timestamp(start)).days<330:continue
                    v=num(r['VL_CONTA'])
                    if v is None or r['ESCALA_MOEDA'] not in ['UNIDADE','MIL']:continue
                    if r['ESCALA_MOEDA']=='UNIDADE':v/=1000
                    facts.append(dict(cnpj=ident(r['CNPJ_CIA']),year=int(end[:4]),period_end=end,received=r['DT_RECEB'],reference=r['DT_REFER'],version=int(r['VERSAO']),docid=r['ID_DOC'],perimeter='ind',metric='distributions_'+statement.lower(),value=v,account=r['CD_CONTA'],description=r['DS_CONTA'],source=member))
        print(y,len(facts),len(capital),flush=True)
    gzwrite(OUT/'cache/supplement.json.gz',dict(facts=facts,capital=capital))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    main(p.parse_args().data_root)
