#!/usr/bin/env python3
"""Export executed results and selected portfolios to a new reviewable snapshot."""
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0,str(Path.cwd()))
from scripts import graham_corrected_maintenance_v11 as maintenance


def main(out):
    if out.exists():
        raise FileExistsError(f"Snapshot already exists; choose a new destination: {out}")
    work=Path('graham_v6_event_results')
    folders=['manutencao_corrigida_v11','manutencao_documental_v11_1','comparacao_documental_v11_1',
             'sensibilidade_documental_v11','auditoria_fontes_v11','auditoria_besst_v9']
    rights = work/'direitos_itsa_v11_2'
    if rights.exists():
        folders.append('direitos_itsa_v11_2')
    for folder in folders:
        shutil.copytree(work/folder,out/folder,ignore=shutil.ignore_patterns('*.log'))
    shutil.copy2(work/'testes_motor_herdado.txt',out/'testes_motor_herdado.txt')
    for name in ['graham_corrigido_anuais_eventos.csv','graham_corrigido_posicoes_eventos.csv','graham_corrigido_resumo_eventos.csv']:
        shutil.copy2(work/name,out/name)
    selections=maintenance.selections_source.load_corrected()
    rows=[]
    for year,s in selections.items():
        specs={'R00':maintenance.selections_source.equal_weights(s['R00']),
               'R03':maintenance.selections_source.equal_weights(s['R03']),
               'R16':maintenance.selections_source.sector_weights(s['R03'],s['sectors'])}
        for strategy,weights in specs.items():
            for ticker,weight in sorted(weights.items()):
                rows.append(dict(year=year,strategy=strategy,scenario='corrigido',ticker=ticker,weight=weight,
                                 sector=s['sectors'][ticker],source='selecao_corrigida_anterior_preservada'))
    besst_selections=json.loads((work/'auditoria_besst_v9/selection_rows.json').read_text())
    sector={(str(r['year']),r['ticker']):r['sector'] for r in besst_selections}
    for r in maintenance.read_csv(work/'auditoria_besst_v9/posicoes_contribuicoes_besst.csv'):
        if r['mechanism']!='renew':continue
        rows.append(dict(year=r['year'],strategy=r['strategy'],scenario=r['scenario'],ticker=r['ticker'],
                         weight=r['weight'],sector=sector[(r['year'],r['ticker'])],source='pacote_original_Barsi_v9'))
    maintenance.write_csv(out/'carteiras_selecionadas_768_posicoes.csv',rows,list(rows[0]))
    assert len(rows)==768
    # The figure uses only executed central results, with provisional status explicit.
    os.environ.setdefault('MPLCONFIGDIR',str(Path('.cache/matplotlib').resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    comparison_folder='direitos_itsa_v11_2' if rights.exists() else 'comparacao_documental_v11_1'
    version='v11.2' if rights.exists() else 'v11.1'
    data=maintenance.read_csv(out/comparison_folder/'comparacao_72_cenarios.csv')
    selected=[r for r in data if r['start_year']=='2020' and r['scenario']!='conservative']
    selected.sort(key=lambda r:float(r['renew']),reverse=True)
    fig,ax=plt.subplots(figsize=(10,5.5))
    x=list(range(len(selected)))
    for offset,key,label,color in [(-.19,'maintain','Manutenção','#457b9d'),(.19,'renew','Renovação','#e09f3e')]:
        bars=ax.bar([v+offset for v in x],[100*float(r[key]) for r in selected],.38,label=label,color=color)
        ax.bar_label(bars,fmt='%.1f%%',fontsize=8,padding=3)
    ax.set_xticks(x,[r['strategy'] for r in selected]);ax.set_ylabel('Retorno acumulado (%)')
    ax.set_title(f'Barsi × Graham · formação em junho/2020, corte em junho/2026\nGraham {version} e Barsi v9 central — resultados provisórios')
    ax.legend();ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.text(.5,.015,'Reinvestimento e precisão distintos entre famílias; não representa comparação integralmente certificada.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.035,1,1));fig.savefig(out/'comparacao_2020.png',dpi=160);plt.close(fig)
    manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'manifesto_arquivos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(f'{len(rows)} selected positions; {len(manifest)} artifacts exported to {out}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    main(parser.parse_args().out)
