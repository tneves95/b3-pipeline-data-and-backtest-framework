#!/usr/bin/env python3
"""Limited, reproducible availability checks; not a new historical screening."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from scripts.reconstruct_barsi_v13 import INPUT,OUT,m,dump


def main():
    universe=m.read_csv(INPUT/'universe_v9_snapshot.csv')
    rows=[]
    for r in universe:
        receipt,cutoff=r['dfp_receipt'],r['availability_cutoff']
        rows.append(dict(year=r['entry_year'],ticker=r['ticker'],share_class=r['class'],
                         formation=r['entry_date'],receipt=receipt,cutoff=cutoff,
                         document_id=r['ID_DOC'],document_url=r['LINK_DOC'],
                         receipt_available=bool(receipt),receipt_before_cutoff=bool(receipt) and receipt<=cutoff,
                         preselection_pass=r['preselection_pass'],
                         scope='METADADO_HERDADO; NAO_REVALIDA_TODOS_OS_LUCROS_NEM_COMPLETUDE_DO_UNIVERSO'))
    dump(OUT,'disponibilidade_universo_v9_206.csv',rows)
    tim=[r for r in universe if r['ticker'] in ('TIMP3','TIMS3')]
    report=dict(universe_rows=len(rows),missing_receipt=sum(not r['receipt_available'] for r in rows),
                receipt_after_cutoff=sum(r['receipt_available'] and not r['receipt_before_cutoff'] for r in rows),
                tim_rows=tim,tim_years_absent=sorted(set(range(2020,2026))-{int(r['entry_year']) for r in tim}),
                tim_risk='Historico de lucro com zeros/lacunas e troca de CNPJ; nao tratar como continuidade economica validada. Selecao congelada, sem substituicao ex post.',
                conclusion='EVIDENCIA_PIT_PARCIAL; NAO_CERTIFICA_AUSENCIA_DE_LOOKAHEAD_OU_SOBREVIVENCIA')
    (OUT/'auditoria_selecao_resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Universe:',len(rows),'missing:',report['missing_receipt'],'late:',report['receipt_after_cutoff'])


if __name__=='__main__':main()
