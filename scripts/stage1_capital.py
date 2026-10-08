#!/usr/bin/env python3
"""PIT treasury/class evidence, incrementally supplementing existing capital."""
from stage1_pit import *

def main(root):
    rows=[];classes=[];foundations=[]
    for y in range(2010,2026):
        with ZipFile(root/f'data/cvm/fca_cia_aberta_{y}.zip') as z:
            meta=csvzip(z,f'fca_cia_aberta_{y}.csv')[['ID_DOC','DT_RECEB','LINK_DOC']]
            d=csvzip(z,f'fca_cia_aberta_geral_{y}.csv').merge(meta,left_on='ID_Documento',right_on='ID_DOC',validate='many_to_one')
            for r in d.to_dict('records'):
                foundations.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=r['DT_RECEB'],founded=r['Data_Constituicao'],docid=r['ID_DOC'],source=r['LINK_DOC']))
        with ZipFile(root/f'data/cvm/fre_cia_aberta_{y}.zip') as z:
            meta=csvzip(z,f'fre_cia_aberta_{y}.csv')[['ID_DOC','DT_RECEB','LINK_DOC']]
            d=csvzip(z,f'fre_cia_aberta_posicao_acionaria_{y}.csv')
            mask=d.Acionista.str.contains('tesouraria',case=False)|d.CNPJ_Companhia.map(ident).eq(d.CPF_CNPJ_Acionista.map(ident))
            d=d[mask & d.ID_Acionista_Relacionado.eq('')].merge(meta,left_on='ID_Documento',right_on='ID_DOC',validate='many_to_one')
            for r in d.to_dict('records'):
                q=num(r['Quantidade_Total_Acoes_Circulacao'])
                if q is None:continue
                rows.append(dict(cnpj=ident(r['CNPJ_Companhia']),quantity=q,received=r['DT_RECEB'],reference=r['Data_Referencia'],
                    composition_date=r['Data_Composicao_Capital_Social'],last_change=r['Data_Ultima_Alteracao'],docid=r['ID_DOC'],source=r['LINK_DOC']))
            d=csvzip(z,f'fre_cia_aberta_capital_social_classe_acao_{y}.csv').merge(meta,left_on='ID_Documento',right_on='ID_DOC',validate='many_to_one')
            for r in d.to_dict('records'):
                classes.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=r['DT_RECEB'],docid=r['ID_DOC'],capital_id=r['ID_Capital_Social'],pn_class=r['Tipo_Classe_Acao_Preferencial'],quantity=num(r['Quantidade_Acoes']),source=r['LINK_DOC']))
    gzwrite(OUT/'cache/treasury_classes.json.gz',dict(treasury=rows,classes=classes,foundations=foundations))
    print('Treasury',len(rows),'class rows',len(classes))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);main(p.parse_args().data_root)
