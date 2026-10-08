"""Small numeric checkpoint, generated solely from the experiment CSVs."""
from b00s_variants import *

def table(rows, cols):
    def fmt(v):
        if v=='':return 'ND'
        try:return f'{float(v):.4f}'
        except (ValueError,TypeError):return str(v)
    return '\n'.join(['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']+
        ['| '+' | '.join(fmt(r[c]) for c in cols)+' |' for r in rows])

def main():
    annual=read(RESULT/'annual_returns_pct.csv');cum=read(RESULT/'cumulative_returns_pct.csv');stats=read(RESULT/'consolidated_pct.csv')
    risk=read(RESULT/'risk_concentration.csv');turn=read(RESULT/'turnover_by_year.csv');holds=read(RESULT/'holdings_by_june.csv')
    text='''# Checkpoint — B00S V2, PR #4

Protocolo exclusivo: `7fea064`. Base imutável: `8d394e9` (PR #3). Somente retorno total bruto percentual, junho/2014 a junho/2026, com decisões PIT e B2 seletiva. Sem IR, aportes, custos ou patrimônio em reais. PR draft, sem merge.

## Lote 1: V0 e V10 concluídos

O replay das 12 janelas V0 coincide com o controle; os CSVs publicam literalmente seus retornos. A V10 escolhe por mediana de volume financeiro nos 126 pregões, depois sessões, volume total e ticker. Incumbentes PASS/INDETERMINATE ocupam vagas. Apenas FAIL comprovado autoriza saída; novas entradas são autofinanciadas pela função B2 herdada, conservando NAV e proporções dos sobreviventes.

As nove empresas iniciais V10 são BBDC4, ITUB4, CMIG4, TBLE3, CSMG3, SBSP3, PSSA3, TIMP3 e VIVT4. Seguros tem somente PSSA3, com 20%; cada outro setor tem duas posições de 10%. TBLE3 supera CPFE3 pela mediana histórica (24.744.079,5 contra 21.274.561,5), conforme cache congelado. As unidades e os pesos evoluem continuamente.

O spin-off compulsório XPBR31 pertence à vaga econômica herdada ITUB4, mas conta como emissora distinta na concentração. Não é uma nova compra BESST. Por isso o número físico de emissoras pode superar o de vagas voluntárias; ambos estão publicados. Tickers usam os aliases aceitos na etapa 1; direitos, classes e sucessoras acompanham a origem na atribuição.

## Retornos anuais (%)

'''+table(annual,['year','V0','V10','VVAL','VQ','IBOV','R03 B2','BH padrão'])
    text+='\n\n## Acumulados em cada junho (%)\n\n'+table(cum,['closing_year','V0','V10','VVAL','VQ','IBOV','R03 B2','BH padrão'])
    text+='\n\n## Comparação consolidada\n\n'+table(stats,['variant','periods','final_pct','cagr_pct','above_ibov_years','annual_close_max_drawdown_pct','annual_population_std_pct','final_rank'])
    text+='\n\nO drawdown acima usa somente fechamentos anuais; não mede a pior perda intradiária/diária. O desvio é populacional descritivo das 12 observações. O ranking só compara séries completas e compatíveis; nenhum caso com lacuna fundamentalista é declarado vencedor.\n'
    text+='\n## Concentração: formação e encerramento\n\n'+table([r for r in risk if (r['year']=='2014' and r['phase']=='AFTER_REVIEW') or (r['year']=='2026' and r['phase']=='PERIOD_END')],['variant','year','companies','eligible_lineage_slots','largest_company_pct','top5_pct','issuer_hhi','sector_hhi'])
    text+='\n\n## Composição final, junho/2026 (peso físico %)\n\n'+table([r for r in read(RESULT/'positions_by_june.csv') if r['date']==DATES[2026]],['variant','ticker','weight_pct'])
    text+='\n\n## Giro unilateral (% do NAV)\n\n'+table([dict(year=y,**{v:next((r['one_way_turnover_pct'] for r in turn if r['variant']==v and r['year']==str(y)),'') for v in ['V0','V10','VVAL','VQ']}) for y in range(2015,2026)],['year','V0','V10','VVAL','VQ'])
    text+='''

## Evidência e limitações

O inventário anterior ao cálculo tem 229 decisões empresa/ano e 29 companhias, todas B00S PASS do controle, incluindo cortes 2014, 2017, 2020, 2024 e 2025. `initial_pit_inventory.csv` e `coverage_by_year_sector.csv` mostram documentação, contagem e peso potencial. Lucro consolidado total não substitui lucro atribuível; capital social anterior a bonificação não é denominador validado; ausência documental não reprova qualidade.

As qualificações de seleção e eventos da etapa 1 continuam vigentes. Não foram reabertas pesquisas de proventos, certificados direitos antes incertos ou alterados screeners. A conciliação da V0 não torna a base integralmente certificada PIT. Atribuição inclui linha separada NUMERICAL_RESIDUAL para somar exatamente os decimais publicados, sem alterar retorno de ações. `redemption_transfers.csv` preserva a origem de recursos compulsoriamente transferidos.

## Reprodução e validação do lote 1

`python scripts/b00s_inventory.py`; `python scripts/b00s_variants.py --stage v10`; `python scripts/b00s_report.py`.
Dependências: pandas e `requirements-attribution.txt`. Replay offline, sem SQLite e sem escrita nas pastas protegidas. CSVs são fonte primária; planilha `results/b00s_four_variants.xlsx` contém resumo, retornos, composição, concentração e seleção. Manifesto registra SHA-256 dos insumos e resultados.

Validação inicial: 95 testes passaram (8 do experimento, 64 da atribuição e 23 da continuidade). Proteção SHA-256 dos 271 arquivos herdados verificada antes/depois. VVAL e VQ continuam em processamento nos próximos lotes deste mesmo PR; células ND neste checkpoint não são retornos zero.
'''
    (ROOT/'docs/checkpoint_b00s_four_variants_2014_2026.md').write_text(text)

if __name__=='__main__':main()
