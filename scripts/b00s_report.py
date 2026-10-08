"""Small numeric checkpoint, generated solely from the experiment CSVs."""
from b00s_variants import *

def table(rows, cols):
    integers={'year','closing_year','periods','above_ibov_years','final_rank','companies','eligible_lineage_slots','entry_decisions_different_from_vval','ano','candidatos','VVAL_aprovadas'}
    def fmt(v,k):
        if v=='':return 'ND'
        if k in integers:return str(int(v))
        if k in {'documento','hash_original'}:return str(v)
        try:return f'{float(v):.4f}'
        except (ValueError,TypeError):return str(v)
    return '\n'.join(['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']+
        ['| '+' | '.join(fmt(r[c],c) for c in cols)+' |' for r in rows])

def dossier_report():
    labels={
        'durability':('Durabilidade','Comprovar posição competitiva, poder de preço, contratos/concessões e exposição regulatória histórica.'),
        'capital_economics':('Economia do capital','Normalizar ciclo e risco; conciliar ROIC/retorno incremental ou ROE prudencial com capital requerido e comparação histórica.'),
        'earnings_reliability':('Resultados confiáveis','Conciliar lucro recorrente, caixa, provisões e extraordinários nas notas conhecidas no corte.'),
        'financial_resilience':('Resiliência financeira',''),
        'capital_allocation':('Alocação e dividendos','Separar manutenção/expansão, ajustar ações e demonstrar sustentabilidade das distribuições e retorno de reinvestimentos.'),
        'governance':('Governança','Revisar materialidade das partes relacionadas, direitos, conflitos e pareceres, sem controvérsias futuras.')}
    text='''# Dossiês PIT — B00S V2

Estas fichas registram a triagem documental de 29 companhias, com avaliação inicial e atualizações de evidência nos cortes B00S PASS. Não equivalem a 29 aprovações de qualidade: as seis conclusões econômicas ainda não estão suficientemente comprovadas. Todas as decisões VQ permanecem `INDETERMINATE`; nenhuma é uma rejeição do negócio.

Os JSONs vinculados contêm os valores por exercício, contas, documentos, recebimentos, URLs e hashes disponíveis. O hash do ZIP original CVM identifica o arquivo que contém a tabela/conta citada; hash ausente é lacuna explicitamente preservada. A atividade cadastral não prova vantagem competitiva, lucro positivo não prova recorrência e patrimônio líquido positivo não prova capital prudencial suficiente.

Não foram usados score, corte de DY, retorno futuro ou escândalo posterior para escolher empresas. A VVAL tem decisão distinta, limitada ao preço de entrada e perímetro dos lucros: somente BBDC4 e TBLE3 em 2014 foram aprovadas neste lote. Aprofundamentos dirigidos e fontes não admitidas estão em [quality_directed_review.json](../research/b00s_four_variants_2014_2026/inputs/quality_directed_review.json) e [valuation_perimeter_reviews.json](../research/b00s_four_variants_2014_2026/inputs/valuation_perimeter_reviews.json).

## Materialidade por ano

Pesos potenciais são os alvos do controle B00S, não os pesos reais de VVAL/VQ. A ordenação documental deve seguir lacunas e materialidade desses pesos, sem escolher nomes pela rentabilidade observada.

'''
    cov=read(RESULT/'coverage_by_year_sector.csv');annual=[]
    for y in range(2014,2026):
        rr=[r for r in cov if r['year']==str(y)]
        annual.append(dict(ano=y,candidatos=sum(int(r['pass_candidates']) for r in rr),
            VVAL_aprovadas=sum(int(r['valuation_approved']) for r in rr),
            VVAL_peso_ND_pct=sum(float(r['valuation_potential_weight_affected_pct']) for r in rr),
            VQ_peso_ND_pct=sum(float(r['quality_potential_weight_affected_pct']) for r in rr)))
    text+=table(annual,['ano','candidatos','VVAL_aprovadas','VVAL_peso_ND_pct','VQ_peso_ND_pct'])+'\n'
    docs=[(p,json.loads(p.read_text())) for p in (INPUT/'dossiers').glob('*.json')]
    for path,d in sorted(docs,key=lambda pair:pair[1]['initial_assessment']['ticker']):
        a=d['initial_assessment'];dims=a['dimensions'];c=a['cnpj']
        data=[r for r in candidates() if r['cnpj']==c]
        facts=dims['earnings_reliability']['favorable'];alloc=dims['capital_allocation']['favorable']
        payouts=alloc.get('historical_payout',[])
        positive=facts.get('positive_attributable_years',0)
        text+=f"\n## {a['ticker']} — {a['company']}\n\n"
        text+=f"CNPJ `{c}`; {a['sector']}; primeiro corte {a['cutoff']}; categoria **{a['category']}**. "
        text+=f"[Ficha com fontes](../research/b00s_four_variants_2014_2026/inputs/dossiers/{path.name}). "
        text+=f"Cortes cobertos: {', '.join(str(r['year']) for r in data)}. Maior peso potencial anual B00S: {100*max(r['base_target'] for r in data):.4f}%.\n\n"
        activity=str(dims['durability']['favorable']).replace('|','/')
        text+=f"Atividade declarada: {activity}. Na avaliação inicial, {positive}/5 lucros atribuíveis positivos recuperados; {sum(x is not None for x in payouts)}/5 exercícios com payout divulgado. Esses fatos são favoráveis à investigação e não resolvem as seis dimensões.\n\n"
        rows=[]
        for k,(label,gap) in labels.items():
            if k=='financial_resilience':
                gap={'Bancos':'Capital de Basileia, crédito inadimplente e cobertura de provisões sob regras vigentes no corte.',
                     'Seguros':'Capital requerido/disponível, sinistralidade, reservas técnicas e resultado técnico sob regras vigentes.'}.get(a['sector'],'Cronograma de dívida, cobertura de juros, CAPEX obrigatório e riscos de concessão conhecidos no corte.')
            rows.append(dict(dimensao=label,estado=dims[k]['status'],prova_pendente=gap))
        text+=table(rows,['dimensao','estado','prova_pendente'])+'\n\n'
        text+='Contraponto: não foi estabelecida rejeição estrutural com o extrato disponível; a ausência de revisão material suficiente impede aprovação. '
        text+=f"Atualizações anuais: {len(d['annual_evidence_updates'])}, ligadas à avaliação inicial, sem repetir integralmente a ficha.\n\n"
        evidence={}
        for dim in dims.values():
            for e in dim['evidence']:
                key=(e.get('docid',''),e.get('source',''),e.get('archive_sha256',''))
                if e.get('docid'):evidence[key]=e
        refs=[]
        for _,e in sorted(evidence.items()):
            source=e.get('url') or (e.get('source') if str(e.get('source','')).startswith('http') else '')
            refs.append(dict(documento=f"[{e['docid']}]({source})" if source else e['docid'],recebido=e['received'],
                             hash_original=e.get('archive_sha256') or 'ND — fonte herdada sem hash neste extrato'))
        text+=table(refs,['documento','recebido','hash_original'])+'\n'
    (ROOT/'docs/dossies_b00s_v2.md').write_text(text)

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
    linked=read(RESULT/'attribution_cumulative.csv') if (RESULT/'attribution_cumulative.csv').exists() else []
    if linked:
        text+='\n## Atribuição acumulada: maiores e menores contribuições\n\n'
        text+='Contribuição anual multiplicada pelo nível da carteira no início de cada janela, expressa em pontos percentuais do índice inicial. A soma por carteira reconcilia com o retorno acumulado. A origem é a posição no início de cada ano; não é rastreamento perpétuo do financiamento. Resgates e sucessoras são preservados na atribuição anual detalhada.\n\n'
        top=[]
        for v in ['V0','V10','VVAL']:
            rr=sorted([r for r in linked if r['variant']==v and r['cnpj']!='NUMERICAL_RESIDUAL'],key=lambda r:float(r['linked_contribution_pp']),reverse=True)
            chosen=rr[:5]+[r for r in rr[-3:] if r not in rr[:5]]
            top.extend(chosen)
        text+=table(top,['variant','tickers','company','linked_contribution_pp'])+'\n'
    text+='\n## Concentração: formação e encerramento\n\n'+table([r for r in risk if (r['year']=='2014' and r['phase']=='AFTER_REVIEW') or (r['year']=='2026' and r['phase']=='PERIOD_END')],['variant','year','companies','eligible_lineage_slots','largest_company_pct','top5_pct','issuer_hhi','sector_hhi'])
    text+='\n\n## Composição inicial, junho/2014 (peso físico %)\n\n'+table([r for r in read(RESULT/'positions_by_june.csv') if r['date']==DATES[2014]],['variant','ticker','weight_pct'])
    text+='\n\n## Composição final, junho/2026 (peso físico %)\n\n'+table([r for r in read(RESULT/'positions_by_june.csv') if r['date']==DATES[2026]],['variant','ticker','weight_pct'])
    text+='\n\n## Giro unilateral (% do NAV)\n\n'+table([dict(year=y,**{v:next((r['one_way_turnover_pct'] for r in turn if r['variant']==v and r['year']==str(y)),'') for v in ['V0','V10','VVAL','VQ']}) for y in range(2015,2026)],['year','V0','V10','VVAL','VQ'])
    text+='''

## Evidência e limitações

O inventário anterior ao cálculo tem 229 decisões empresa/ano e 29 companhias, todas B00S PASS do controle, incluindo cortes 2014, 2017, 2020, 2024 e 2025. `initial_pit_inventory.csv` e `coverage_by_year_sector.csv` mostram documentação, contagem e peso potencial. Lucro consolidado total não substitui lucro atribuível; capital social anterior a bonificação não é denominador validado; ausência documental não reprova qualidade.

As qualificações de seleção e eventos da etapa 1 continuam vigentes. Não foram reabertas pesquisas de proventos, certificados direitos antes incertos ou alterados screeners. A conciliação da V0 não torna a base integralmente certificada PIT. Atribuição inclui linha separada NUMERICAL_RESIDUAL para somar exatamente os decimais publicados, sem alterar retorno de ações. `redemption_transfers.csv` preserva a origem de recursos compulsoriamente transferidos.

## Reprodução e validação do lote 1

`python scripts/b00s_inventory.py`; `python scripts/b00s_variants.py --stage v10`; `python scripts/b00s_report.py`.
Dependências: pandas e `requirements-attribution.txt`. Replay offline, sem SQLite e sem escrita nas pastas protegidas. CSVs são fonte primária; planilha `results/b00s_four_variants.xlsx` contém resumo, retornos, composição, concentração e seleção. Manifesto registra SHA-256 dos insumos e resultados.

Validação inicial: 95 testes passaram (8 do experimento, 64 da atribuição e 23 da continuidade). Proteção SHA-256 dos 271 arquivos herdados verificada antes/depois. Células ND não são retornos zero.
'''
    if any(r['variant']=='VVAL' and r['periods']=='12' for r in stats):
        text+='''

## Lote 2: VVAL executada, cobertura documental restrita

Apenas BBDC4 e TBLE3 tiveram admissão comprovada neste lote, em junho/2014, com pesos de 50% cada. Dos pesos potenciais da B00S-base de 2014, representam 6%; os outros 94% são afetados por indeterminação documental. Bancos e energia são os únicos setores formados. Não há novas admissões comprovadas nos cortes seguintes; incumbentes ficam sob B2, mesmo quando valuation/qualidade atualizados são ND. Não ocorre FAIL-base das duas incumbentes: o giro das revisões é zero. Em junho/2026, os pesos são BBDC4 42,5167% e TBLE3/linhagem Engie 57,4833%, conforme unidades e proventos acumulados. Esta concentração decorre da cobertura, não demonstra superioridade ou inferioridade da filosofia econômica.

A VVAL restrita acumula **+226,0724%**, CAGR **10,3510%**, e supera o IBOV em **5/12** anos. **Não é uma conclusão sobre a VVAL de universo integral.** P/L normalizado inicial: BBDC4 10,9441 e TBLE3 14,4110. A V2 manteve 15/25, 4%, 20% e prêmio nominal sobre inflação de 6 p.p.; nenhum prêmio de reinvestimento foi concedido sem os quatro requisitos documentados. Bazin 6% e Graham 22,5 são somente diagnósticos separados.

Normalização: mediana de cinco lucros anuais atribuíveis, corrigidos do fim de cada exercício até o IPCA de maio já publicado em junho; não entra IPCA de junho. Originais IBGE e série SGS 433 estão arquivados. Capitalização: capital **emitido** por classe, cada qual a seu preço observado, sem proxy ON/PN; convenção conservadora inclui tesouraria, e não é usada como denominador certificado de LPA. Eventos após o último FRE tornam a capitalização ND até conciliação. O payout FRE é o divulgado sobre lucro ajustado; convenções de reservas e JCP líquido impedem tratá-lo automaticamente como retenção bruta comprovada.

O diagnóstico Bazin usa a média do lucro atribuível e payout no nível da emissora; o teto de capitalização e o yield da média de distribuições estão em colunas separadas. A média de DPA e o teto por ação permanecem ND sem reconciliação histórica das classes, direitos e denominadores ajustados. Não se apresenta o diagnóstico agregado como DPA certificado.

As comparativas conhecidas do Bradesco 2010–2012 mantêm exatamente o lucro atribuível entre entregas sucessivas, inclusive após a ênfase IFRS 11. Na Tractebel, usa-se o lucro de 2012 reapresentado (1.490.454 mil, anteriormente 1.499.497 mil), sem alterar o exercício determinante da mediana. Os pareceres e a decisão estão em `inputs/valuation_perimeter_reviews.json`; a aprovação é exclusiva do valuation de entrada de 2014, não de VQ.

PSSA3 permanece ND: ajustes de abertura 2012 e integração/extraordinários exigem ponte histórica. O relatório recuperado registra ganho COFINS de aproximadamente 702 milhões em 2013, mas sua data de criação não certifica a publicação antes do corte. CSMG3 permanece ND pela ponte dos ajustes contábeis e referência do parecer ao ICMS não provisionado. Nenhuma foi rotulada como empresa ruim.

Extrato dirigido: 134.852 fatos contábeis, 26.671 registros FRE e 2.630 registros de pareceres, 32 arquivos CVM com hashes. Há P/L mecânico calculável em 198/229 decisões, mas só 2 decisões de entrada aprovadas neste lote. As restantes 227 estão indeterminadas. Lucro total consolidado, LPA sem ajustes e ROE de não financeiras não são substitutos dos indicadores exigidos. As subclasses PN são vinculadas ao ID do capital emitido, não a linhas de capital autorizado/subscrito de outra composição.

Reprodução adicional: `python scripts/b00s_fundamentals.py`; `python scripts/b00s_variants.py --stage vval`. As decisões JSON e seu SHA-256 são congelados antes do replay. Treze testes adicionais validam classes, lucro real, canais de preço, seis dimensões não compensatórias e bloqueio de fontes futuras. A proteção complementar inclui 286 arquivos do PR #3, além da lista herdada de 271.
'''
    sp=RESULT/'sensitivity_summary.csv'
    if sp.exists():
        sr=read(sp)
        text+='\n## Sensibilidades e impacto das lacunas\n\n'+table(sr[:7],['case','periods','final_pct','difference_pp','entry_decisions_different_from_vval'])
        text+='''

As faixas 12/20, 15/25 e 18/30 usam a mesma exigência de reinvestimento e a mesma cobertura de perímetro. Na faixa conservadora, TBLE3 não passa sem comprovar reinvestimento; isso altera uma compra inicial. O caso principal não é alterado por estes resultados.

Foram executados 65 cenários previamente simétricos: 52 têm 12 janelas. Além dos sete acima, cada uma das 29 companhias é incluída isoladamente na VVAL quando indeterminada e retirada isoladamente da coorte hipotética VQ que admite todos os indeterminados. `sensitivity_annual_pct.csv`, `sensitivity_attribution.csv` e `sensitivity_reviews.csv` detalham retornos, contribuições e compras. São trajetórias condicionais, não limites matemáticos nem nova estratégia principal.

Em 12 inclusões isoladas VVAL, surge uma única entrada elegível em revisão posterior e nenhum incumbente permanece elegível para nova compra. O alvo de 100% para a entrada, aplicado literalmente ao financiador herdado, zeraria incumbentes não FAIL. O motor **bloqueia essa operação**, registrando companhia e ano; não cria uma regra de financiamento após ver rentabilidades. Esses cenários estão ND por `UNRESOLVED_ENTRY_FUNDING_WOULD_LIQUIDATE_NONFAIL`. O 13º cenário sem trajetória é o diagnóstico Bazin, sem posição inicial comprovada. As quatro séries principais não encontram esse caso de financiamento.
'''
    statuses=read(RESULT/'portfolio_status.csv') if (RESULT/'portfolio_status.csv').exists() else []
    if any(r['variant']=='VQ' for r in statuses):
        text+='''

## Lote 3: VQ processada, carteira não formada

As 229 decisões são **INDETERMINATE**, e nenhuma companhia tem as seis conclusões econômicas positivas documentalmente comprovadas na formação de 2014. A saída VQ é portanto **NOT_FORMED**, com 12 células ND; não é uma carteira de caixa com 0%, tampouco uma reprovação das 29 empresas. Não foi utilizado score, DY mínimo, payout mínimo ou antecipação de escândalos. Não há vencedora VQ.

`inputs/dossiers/` contém uma ficha por companhia, com seis dimensões, fatos favoráveis, lacunas/contrapontos, documentos e datas, seguida de atualizações anuais de evidência sem repetir a avaliação integral. `docs/dossies_b00s_v2.md` dá leitura compacta. As lacunas materiais incluem durabilidade de contratos/concessões, retorno incremental por ação, reconciliação de recorrência, capital prudencial/crédito/reservas por setor e revisão das partes relacionadas. Pertencer ao BESST e ter parecer sem ressalva não demonstram conjuntamente as seis dimensões.

Revisão dirigida: PSSA3 tem original arquivado e hash, mas publicação pré-corte e suficiência prudencial não foram atestadas; BBDC4 tem parecer CVM arquivado, mas o download do relatório ampliado localizado foi recusado com HTTP 403; IRBR3 em junho/2019 não é rejeitada com informações de 2020. Seu release de 2018 foi publicado em 07/02/2019, insuficiente sozinho para provar reservas e qualidade. As fontes não admitidas e os motivos estão em `inputs/quality_directed_review.json`. Não houve aprovação com incongruência material pendente, nem revisão adversarial independente inventada.

A inclusão hipotética de todos os indeterminados reproduz a V0 (+402,1320%); as 29 retiradas individuais quantificam a dependência desse resultado dos nomes não certificados. A ausência de seleção VQ verificável impede testar a hipótese de qualidade em uma coorte comparável. A conclusão documental é limitada a este lote; completar os dossiês exige novas provas PIT, mantendo os critérios congelados.

Reprodução final offline: `python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`. A coleta de originais é uma etapa separada, dispensada no replay.

Validação final: 165 testes de regressão e do experimento, cobrindo referências imutáveis, atribuição anual/acumulada, autofinanciamento, concentração por emissora, ND, datas dos dossiês, cenários e correspondência CSV/Excel/manifesto. O CI repete geração offline e exige `git diff --exit-code`.

A comparação integral com `8d394e9` verificou os 840 arquivos rastreados do PR #3 sem uma única alteração. Os insumos, CSVs, Excel e relatórios foram reproduzidos byte a byte no replay final.
'''
    (ROOT/'docs/checkpoint_b00s_four_variants_2014_2026.md').write_text(text)
    if (INPUT/'dossiers').exists():dossier_report()

if __name__=='__main__':main()
