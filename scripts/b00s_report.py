"""Numerical checkpoint and company judgements from the frozen offline inputs."""
from b00s_variants import *

def table(rows, cols):
    def fmt(v):
        if v is None or v=='':return 'ND'
        if isinstance(v,float):return f'{v:.4f}'
        s=str(v).replace('|','/').replace('\n',' ')
        try:
            if '.' in s:return f'{float(s):.4f}'
        except ValueError:pass
        return s
    return '\n'.join(['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']+
        ['| '+' | '.join(fmt(r.get(c,'')) for c in cols)+' |' for r in rows])

def dossier_report():
    decisions=json.loads((INPUT/'fundamental_decisions.json').read_text())
    text='''# Avaliações fundamentalistas e valuation — primeiro lote cronológico

Corte: junho/2014. Cada decisão abaixo usa originais publicados até o corte, com páginas, data e hash. As seis dimensões são não compensatórias: SAT satisfatória; ND indeterminada; não há soma de pontos. Os fatos contrários são examinados mesmo nas aprovações. A VVAL tem decisão própria; aprovar qualidade não sana falta de preço por classe ou lucro comparável.

As fichas futuras mantêm fatos contábeis coletados, mas **não representam avaliação econômica concluída**. O próximo corte é junho/2015. Reaproveitar esta tese exige examinar mudanças materiais conhecidas naquele corte; uma classificação de 2014 não é automaticamente válida até 2026. IRB/2019 não pode ser rejeitada por eventos de 2020.

'''
    for f in sorted((r for r in decisions if r['year']==2014),key=lambda r:r['ticker']):
        a=f['documentary_assessment'];name=f['ticker'];path=f"../research/b00s_four_variants_2014_2026/{f['dossier']}"
        text+=f"\n## {name}\n\nVQ: **{f['quality_category']}**. VVAL: **{f['valuation_status']}**. [Ficha e atualizações]({path}).\n\n"
        if not a:raise ValueError(('Missing initial company review',name))
        text+=a['valuation']['reason']+'\n\n'
        if f.get('normalized_pe_interval'):
            b=f['normalized_pe_interval'];text+=f"P/L certificado por intervalo: [{b['lower']:.4f}; {b['upper']:.4f}]. Lucro/P/L pontual permanecem ND; aprovação somente se todo o intervalo cabe no limite 15.\n\n"
        elif f['normalized_pe'] is not None:
            text+=f"P/L calculado: {f['normalized_pe']:.4f}; só é admissível com perímetro e itens não recorrentes resolvidos.\n\n"
        for key,d in a['dimensions'].items():
            text+=f"**{key} — {d['status']}.** Favorável: {d['favorable']} Contraponto: {d['contrary_evidence']} Julgamento: {d['reason']}"
            if d.get('missing'):text+=' Pendente: '+d['missing']
            refs=[f"[{e['docid']}/g{e['group']}, p.{','.join(map(str,e['pages']))}]({e['url']}) (publicado {e['received']})" for e in d['evidence']]
            text+=' Fontes: '+'; '.join(refs)+'.\n\n'
        text+='Fontes valuation: '+'; '.join(f"[{e['docid']}/g{e['group']}, p.{','.join(map(str,e['pages']))}]({e['url']})" for e in a['valuation']['evidence'])+'.\n'
    text+='\n## Continuação cronológica\n\nOs dossiês abaixo preservam a indexação por empresa e os extratos das datas futuras. Somente o corte marcado como avaliado constitui decisão fundamentalista.\n\n'
    for p in sorted((INPUT/'dossiers').glob('*.json')):
        a=json.loads(p.read_text())['initial_assessment'];text+=f"- [{a['ticker']} / {a['cnpj']}](../research/b00s_four_variants_2014_2026/inputs/dossiers/{p.name})\n"
    (ROOT/'docs/dossies_b00s_v2.md').write_text(text)

def main():
    if reviewed_through()>2014:
        from b00s_incremental_report import main as incremental_report
        return incremental_report()
    annual=read(RESULT/'annual_returns_pct.csv');stats=read(RESULT/'consolidated_pct.csv')
    summary=read(RESULT/'checkpoint_summary.csv');hold=read(RESULT/'holdings_by_june.csv')
    risk=read(RESULT/'risk_concentration.csv');positions=read(RESULT/'positions_by_june.csv')
    facts=[r for r in json.loads((INPUT/'fundamental_decisions.json').read_text()) if r['year']==2014]
    text='''# PR #4 — formação de junho/2014 e primeiro retorno realizado

Protocolo V2 exclusivo no commit `7fea064`; revisão do coordenador [6069878965](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6069878965). PR draft, sem merge. PR #3 preservado integralmente. V0/V10 mantêm retornos, pesos, concentração, giro e atribuição aceitos no commit `3c1dfa5`, comparados literalmente em 11 tabelas.

Este lote fecha a avaliação empresa por empresa dos 20 candidatos de junho/2014 e calcula suas carteiras até junho/2015, antes da próxima seleção. Junho/2015–2025 exige revisão incremental das mudanças materiais; as células futuras VVAL/VQ ficam vazias, não zero. Não se projeta a análise de 2014 por doze anos. O [checkpoint anterior](reviews/checkpoint_before_2014_review_3c1dfa5.md) foi preservado como histórico e não representa o estado documental atual.

Retorno total bruto, sem custos, IR ou aportes; eventos, unidades e linhagens herdados do PR #3, com as mesmas qualificações. Critérios 15/25, LPA real 4%, retenção 20%, retorno econômico acima da inflação + 6 pp e solidez não foram alterados. Não se concedeu prêmio de reinvestimento sem provas. DY 6% e Graham 22,5 são apenas diagnósticos; VQ não usa score.

## Resultado do lote: junho/2014 → junho/2015

'''+table(summary,['variant','return_pct','vs_ibov_pp','vs_v0_pp','initial_companies','initial_top5_pct','final_largest_pct','final_top5_pct'])
    freeze=json.loads((INPUT/'decision_freeze_record.json').read_text())
    text+=f"\n\nCongelamento anterior ao replay: `{freeze['decision_commit'][:7]}`; {len(json.loads((INPUT/'review_original_sources.json').read_text()))} originais arquivados."
    text+='\n\nDiferenças em pontos percentuais. As carteiras são efetivamente selecionadas com a documentação disponível; não são cenários que aprovam lacunas. Não há revisão intermediária neste primeiro período: giro unilateral de vendas é zero e compras iniciais são formação, não giro. Não se infere superioridade estrutural de uma única janela.\n'
    text+='\n## Composição inicial e atribuição do primeiro período\n\n'+table([r for r in hold if r['year']=='2014' and r['variant'] in ['VVAL','VQ']],['variant','row_type','ticker','initial_weight_pct','final_weight_pct','exposure_return_pct','contribution_pp'])
    text+='\n\nAtribuição em pontos percentuais, incluindo resíduo numérico separado; soma exatamente o retorno publicado. Setores representados têm o mesmo peso na formação e as empresas dividem igualmente seu setor, conforme regra original. Não se usam pesos do B00S-base para simular uma carteira filtrada.\n'
    text+='\n## Concentração no lote\n\n'+table([r for r in risk if r['variant'] in ['VVAL','VQ']],['variant','date','phase','companies','largest_company_pct','top5_pct','issuer_hhi','sector_hhi','sector_weights_pct'])
    rows=[]
    for r in facts:
        d=r['documentary_assessment'];iv=r.get('normalized_pe_interval')
        rows.append(dict(ticker=r['ticker'],VVAL=r['valuation_status'],PL=r['normalized_pe'],PL_max=iv['upper'] if iv else None,
                         VQ=r['quality_category'],SAT=sum(x['status'] in ['SATISFACTORY','HIGH'] for x in d['dimensions'].values()),ND=sum(x['status']=='INDETERMINATE' for x in d['dimensions'].values())))
    text+='\n## Decisões efetivas antes dos retornos\n\n'+table(rows,['ticker','VVAL','PL','PL_max','VQ','SAT','ND'])
    text+='\n\n[Tabela auditável da formação](../research/b00s_four_variants_2014_2026/results/formation_2014_review.csv): setor, P/L antes/depois, efeito do ajuste, decisões e razões, documentos/datas/páginas e ND específico.\n'
    coverage=read(RESULT/'coverage_by_year_sector.csv')
    initial_coverage=[r for r in coverage if r['year']=='2014']
    text+='\n### Cobertura por setor em 2014\n\n'+table(initial_coverage,['sector','pass_candidates','valuation_approved','valuation_potential_weight_affected_pct','quality_qualified','quality_potential_weight_affected_pct'])
    text+='\n\nAdmissões VVAL passam de 2 para 10, e VQ de 0 para 5. O peso potencial B00S coberto por admissões VVAL passa de 6% para 56%; na VQ chega a 34%. Esses pesos medem cobertura do universo original, não exposição das carteiras filtradas. Permanecem 44% e 66% do peso-base sem admissão, respectivamente. As 120 dimensões de qualidade têm 71 conclusões satisfatórias e 49 indeterminadas específicas.\n'
    text+='''

[As seis avaliações de cada empresa](dossies_b00s_v2.md) explicam fatos favoráveis, contrapontos, julgamentos, páginas e datas. [Revisão adversarial independente](reviews/adversarial_2014.json) registra contestação de perímetros e reavaliações antes dos retornos. O manifesto conserva o hash dos PDFs originais; o congelamento das fichas precede o replay.

Porto: lucro recorrente atribuível2013 de R$703,5 mi, em vez do lucro contábil R$ 1.405,207 mi; P/L passa de13,7883 para14,1690. O ganho fiscal não é removido pelo valor bruto isolado. Copasa: ganho atuarial 2010 identificado no original; efeitos fiscais/reversões tratados por intervalos conservadores sobre a mesma mediana de cinco lucros reais. Não são uma nova fórmula ou um ponto estimado. TIM: crédito fiscal 2010 retirado, mas sua faixa de preço ainda exige todas as provas de reinvestimento. Vivo: incorporação 2011 e ganhos de torres impedem comparar mecanicamente os cinco exercícios; conflito societário conhecido também é contraponto da governança.

O limite superior do P/L é usado somente para demonstrar que toda a faixa documental cabe no canal maduro. Intervalos que cruzam 15 não recebem aprovação nem migram automaticamente ao canal de reinvestimento. Ajustes de ganhos não autorizam adicionar perdas operacionais, de crédito ou hidrológicas. O cálculo corrige cada exercício apenas pelo IPCA conhecido no corte; capitalização continua por quantidade e preço de cada classe.

## Controles aceitos — doze períodos, até junho/2026

'''+table([r for r in stats if r['variant'] in ['V0','V10','IBOV']],['variant','periods','final_pct','cagr_pct','above_ibov_years','annual_close_max_drawdown_pct','annual_population_std_pct'])
    text+='\n\nDrawdown e desvio acima usam fechamentos anuais, não observações diárias. VVAL/VQ ainda não têm resultado de doze períodos validado neste lote.\n\n'+table(annual,['year','V0','V10','VVAL','VQ','IBOV'])
    sr=read(RESULT/'sensitivity_summary.csv')
    text+='\n\n## Sensibilidades predefinidas no mesmo período\n\n'+table(sr[:7],['case','periods','final_pct','difference_pp'])
    text+=f'\n\nSão {len(sr)} cenários: faixas 12/20, 15/25 e 18/30, dois diagnósticos, inclusões de lacunas e tratamentos simétricos dos 20 emissores deste corte. Cada retirada VQ realmente remove a empresa, inclusive quando já qualificada. Cenários não alteram as decisões principais nem constituem limites de retorno.\n'
    text+='''

## Reprodução e próximo corte

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Replay offline; PDFs originais, páginas extraídas, datas e hashes arquivados. O coletor online é separado e nunca executado no CI. Testes cobrem fontes posteriores, alteração de originais, medianas/intervalos, preço por classe, reinvestimento, seis dimensões sem compensação, preservação exata V0/V10, atribuição, concentração, continuidade B2 e bloqueio de liquidação de não FAIL. CSVs são fonte da planilha; manifesto confere os hashes. O CI repete a geração e exige ausência de diff.

Próximo lote: junho/2015, reutilizando as vinte teses iniciais e examinando mudanças materiais de lucro/perímetro, crédito/capital, seca/tarifa/concessões, CAPEX e relações com controladores. Só depois dessa revisão será calculada a seleção seguinte; nenhum critério será calibrado ao retorno deste lote.
'''
    (ROOT/'docs/checkpoint_b00s_four_variants_2014_2026.md').write_text(text)
    dossier_report()

if __name__=='__main__':main()
