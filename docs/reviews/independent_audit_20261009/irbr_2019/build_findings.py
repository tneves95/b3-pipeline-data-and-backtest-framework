"""Materializa o primeiro parecer; criação exclusiva impede sobrescrita acidental."""
import hashlib
import json
from datetime import datetime, timezone
from review_reader import PACKAGE, OUT

registry=json.loads((PACKAGE/'sources.json').read_text())
calc=json.loads((OUT/'independent_calculations.json').read_text())
def cites(specs):
    out=[]
    for doc,group,pages in specs:
        s=next(s for s in registry if s['docid']==str(doc) and s['group']==group)
        out.append({k:s[k] for k in ['docid','group','received','original_sha256','original','url']} |
                   {'pages_1_based':pages,'page_kind':'logical_xml_unit' if s.get('source_format')=='original_xml' else 'pdf_page'})
    return out

dimensions=[
 ('durability',[(67429,412,[28,29]),(81090,1653,[4,5,6]),(82684,192,[1,4])],
  'Franquia doméstica, escala e demanda contratual demonstradas; negócio satisfatório.',
  'Expansão exterior e dependência de seguradoras acionistas; vantagem doméstica não comprova moat internacional.'),
 ('capital_economics',[(67429,412,[28,29,30]),(71429,412,[21,22,23]),(81090,412,[16,18,19,20,67,68,69,74,75]),(81090,1653,[6,7,8])],
  'ROE recalculado 26,14/26,78/32,15%, capital excedente e resultados técnicos positivos; sensibilidade limitada conserva rentabilidade coerente.',
  'Rentabilidade externa cai, resultado financeiro e efeitos fiscais/atuariais afetam comparação; retorno incremental não certificado.'),
 ('earnings_reliability',[(81090,412,[30,31,32,67,68,69,74,75]),(81090,1654,[1,2,3,5]),(82684,193,[30,31,32]),(81090,0,[1]),(82684,0,[1])],
  'Auditoria específica dos prêmios e provisões, XML original reconciliado, recebimentos efetivos e aging dão prova afirmativa suficiente para SAT.',
  'Estimados crescem, PDD é revertida, PREViRB e benefícios fiscais são positivos não extrapoláveis; diferença narrativa de provisões sem ponte, pequena para admissão.'),
 ('financial_resilience',[(81090,412,[5,6,7,8,9,10,11,12,16,17,50,51,52,53,54,89]),(82684,193,[15,16]),(82684,192,[5])],
  'PLA/CMR 3,209 e 2,715, TAP sem insuficiência, retrocessão e ativos vinculados divulgados.',
  'Excedente cai16,1%; liquidez depende de direitos creditórios; crescimento internacional e sinistralidade aumentam risco. Sem descumprimento prudencial demonstrado.'),
 ('capital_allocation',[(67429,412,[31]),(81090,412,[21,61,62]),(81090,1653,[8]),(82684,192,[1]),(82684,193,[15,58])],
  'Pagadora madura com distribuição e excedentes compatíveis no corte; oferta secundária corretamente atribuída ao vendedor.',
  'Payout bruto73,30% depende de lucro com itens excepcionais; prêmio reinvestidor não comprovado.'),
 ('governance',[(71429,1653,[7]),(81090,412,[54,55,61]),(81090,1653,[9,10]),(81090,1654,[6,9,10]),(82684,207,[1,2,3,6])],
  'Órgãos de fiscalização e trabalhos de auditoria/comitê efetivamente descritos; prestação de contas satisfatória.',
  'Cedentes acionistas, incentivo ligado a valor de mercado, serviços adicionais de auditor e golden share; conflitos potenciais sem abuso material provado.')
]
dimout=[{'dimension':name,'review_status':'PASS','vq_status_supported':'SATISFACTORY',
         'favorable':favor,'contrary':contra,'material_unresolved_alert':False,'sources':cites(spec)}
        for name,spec,favor,contra in dimensions]
findings=[
 {'id':'IRB19-F01','status':'PASS','severity':'none','topic':'valuation_bound',
  'summary':'Reexecução independente confirma rejeição por preço sob os dois canais15/25.',
  'economic_materiality':'Decisiva para nova compra VVAL; P/L mínimo25,456017 sem tesouraria.',
  'blocks_admission':False,'potential_admission_impact':'Corrobora REJECTED_PRICE; não se calcula lucro pontual nem se concede premium.',
  'sources':cites([(67429,412,[28,29,30,31,85,86,87,88]),(71429,412,[3,21,22,23,74,75,76]),(82684,193,[58])]),
  'calculation_reference':'independent_calculations.json:valuation',
  'limitations':'Tetos econômicos condicionais ao tratamento consistente de custos ordinários; folga limitada. Não resolve sensibilidade18/30.',
  'pending_action':'Reabrir prova apenas se despesa extraordinária PIT não coberta for demonstrada; preservar componentes e IPCA.'},
 {'id':'IRB19-F02','status':'UNRESOLVED','severity':'low','topic':'reserve_audit_narrative_bridge',
  'summary':'Narrativa do auditor R$8.823,037mi versus balanço/notas v4 R$8.805,895mi; diferença R$17,142mi sem ponte.',
  'economic_materiality':'0,195% das provisões,1,41% do lucro,0,571% do PLA,0,829% do excedente2018; não altera suficiência por si.',
  'blocks_admission':False,'potential_admission_impact':'Nenhuma mudança demonstrada em VQ; pendência documental não equivale a provisões gravemente insuficientes.',
  'sources':cites([(81090,1654,[2]),(81090,412,[5,16,54]),(81090,0,[1])]),
  'pending_action':'Anexar ponte de versões ou explicação histórica que reconcilie o saldo narrativo; não substituir por texto posterior.'},
 {'id':'IRB19-F03','status':'ISSUE','severity':'medium','topic':'foreign_economic_deterioration_disclosure',
  'summary':'Contraponto congelado merece quantificar margem externa: R$376,000mi→R$194,011mi, apesar de expansão de prêmios.',
  'economic_materiality':'Queda48,4%; margem/prêmio ganho22,75%→8,27%; sinistros brutos/prêmio externo69,25%→84,75%.',
  'blocks_admission':False,'potential_admission_impact':'Veda extrapolação otimista ou HIGH; não demonstra perda estrutural duradoura. Margem externa positiva e recuperação trimestral dão contraponto favorável.',
  'sources':cites([(81090,412,[18,19]),(82684,193,[17,18])]),
  'pending_action':'Adicionar valores e distinguir visão contábil bruta de sinistralidade retida gerencial nas dimensões1,2,4.'},
 {'id':'IRB19-F04','status':'ISSUE','severity':'medium','topic':'credit_conversion_and_gross_aging_precision',
  'summary':'Queda de estimados não prova recebimento da mesma coorte; aging líquido deve preservar débitos compensados e crédito bruto.',
  'economic_materiality':'Estimados/RVNE agregados de R$2.868,098mi em2018 e R$2.795,163mi no1T19; créditos vencidos brutos R$671,800mi versus líquido R$320,602mi.',
  'blocks_admission':False,'potential_admission_impact':'Aumenta cautela sobre lucros/cobertura; auditoria específica e notas de compensação sustentam SAT, sem reprovação material comprovada.',
  'sources':cites([(81090,412,[11,12,31,32,86]),(82684,193,[30,31,32]),(81090,1654,[2,3])]),
  'pending_action':'Explicitar conversão estimado→efetivo, recebimentos efetivos e três parcelas do aging. Se houver prova PIT de falha de compensação/estimativa, reavaliar.'},
 {'id':'IRB19-F05','status':'PASS','severity':'none','topic':'prudential_capital_and_liquidity',
  'summary':'Capital e liquidez positivos pela metodologia regulatória histórica divulgada; dependência de direitos creditórios foi quantificada.',
  'economic_materiality':'PLA/CMR2,715 emmarço, excedenteR$1,734bi; excluir direitos creditórios da liquidez é cenário, não regra nova.',
  'blocks_admission':False,'potential_admission_impact':'SAT com acompanhamento; sem capital insuficiente demonstrado.',
  'sources':cites([(81090,412,[16,17,54,89]),(82684,193,[15,16])]),'pending_action':'Monitorar mix, arrecadação e capital com dados PIT novos; não atualizar este corte com fatos futuros.'},
 {'id':'IRB19-F06','status':'PASS','severity':'none','topic':'cash_and_nonrecurring_profit',
  'summary':'CFO consolidado original e subtotais analíticos conferem; PREViRB/PDD não foram tratados como lucros perpetuáveis.',
  'economic_materiality':'Remoção bruta estreita R$212,834mi deixa lucroR$1.005,962mi, ROE26,54% e payout88,81%; não normalização completa.',
  'blocks_admission':False,'potential_admission_impact':'SAT pagadora madura; não certifica premium reinvestidor.',
  'sources':cites([(81090,0,[1]),(82684,0,[1]),(81090,412,[62,67,68,69,74,75])]),
  'pending_action':'Preservar ressalva da ponte de caixa e separar demais efeitos fiscais/atuariais se pretender normalização pontual.'},
 {'id':'IRB19-F07','status':'PASS','severity':'none','topic':'governance_conflicts',
  'summary':'Conflitos potenciais específicos cotejados com fiscalização e informações históricas; sem abuso material demonstrado.',
  'economic_materiality':'Cedentes acionistas27,89% dos prêmios2018; incentivo de valor de mercado e serviços adicionais36% dos honorários.',
  'blocks_admission':False,'potential_admission_impact':'Não sustenta HIGH, fraude ou rejeição estrutural; SAT com contrapontos.',
  'sources':cites([(71429,1653,[7]),(81090,412,[54,55,61]),(81090,1653,[9,10]),(81090,1654,[6,9,10]),(82684,207,[1,2,3,6])]),
  'pending_action':'Preservar os conflitos na ficha; investigar apenas fatos pontuais historicamente publicados.'}
]
result={
 'reviewer_role':'independent_adversarial','ticker':'IRBR3','cnpj':'33376989000191','cutoff':'2019-06-28',
 'first_opinion_frozen_at_utc':datetime.now(timezone.utc).isoformat(),
 'review_decision':'PASS','quality_review_decision':'PASS','valuation_review_decision':'PASS',
 'quality_category_supported':'QUALIFIED_SATISFACTORY','valuation_category_supported':'REJECTED_PRICE',
 'six_dimensions_sufficient':True,'material_unresolved_admission_alert':False,
 'company_rejection_proved':False,'fraud_inferred':False,'thresholds_changed':False,'portfolios_reclassified':False,
 'report':'first_opinion.md','calculations':'independent_calculations.json','read_log':'read_log.jsonl',
 'dimensions':dimout,'findings':findings,
 'scope_declaration':{
  'authorized_package':str(PACKAGE),'protocol':str(PACKAGE.parent/'protocol_v2_redacted.md'),
  'only_authorized_documents_and_new_review_artifacts_accessed':True,
  'github_accessed':False,'conversation_history_accessed':False,'future_returns_accessed':False,
  'portfolio_results_accessed':False,'future_irb_news_used':False,'post_cutoff_company_documents_accessed':False,
  'web_browsing_used':False,'pr4_work_accessed':False,'implementation_participation':False,
  'parent_merits_feedback_before_first_opinion':False,
  'numeric_source_complements_during_review':['ipca_known.json','selection_quote.json','selection_quote_record.txt'],
  'source_paths_mentioned_inside_metadata_but_not_opened':['COTAHIST_A2019.ZIP','continuation_irb_quotes_2019.json.gz','ipca_may_2019.pdf.gz'],
  'historical_pre_cutoff_share_performance_mentions':'Inerentes a relatórios históricos autorizados; não usadas no julgamento.'},
 'limitations':[
  'Revisão dirigida; não auditoria integral de cada página ou recálculo atuarial a partir dos contratos.',
  'PDFs: extrações fornecidas, integridade dos originais e leitura visual das tabelas críticasp31; renderização integral não realizada.',
  'Algumas saídas agregadas iniciais truncadas; não reivindicadas como leitura substantiva integral.',
  'Proveniência do ZIP anual e disponibilidade SGS/IBGE aceitas pela trilha entregue, sem reabrir arquivos externos.',
  'Nenhum lucro normalizado pontual, CAGR real5anos, retenção média ou retorno incremental certificado.',
  'Limite de P/L condicionado ao tratamento econômico de custos ordinários e à ausência de extraordinário elegível não coberto nas fontes examinadas.'
 ],
 'numeric_source_provenance':[
  {'path':str(PACKAGE/n),'sha256':hashlib.sha256((PACKAGE/n).read_bytes()).hexdigest()}
  for n in ['ipca_known.json','selection_quote.json','selection_quote_record.txt']],
 'source_catalog':registry
}
with (OUT/'first_findings.json').open('x') as f:
    json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')

with (OUT/'first_opinion.md').open('a') as f:
    f.write('\nRegistro de fontes primárias e hashes SHA-256 dos originais descompactados:\n\n')
    f.write('| Documento/grupo | Recebimento | Páginas/unidades | SHA-256 original |\n|---|---|---:|---|\n')
    for s in registry:
        f.write(f"| {s['docid']}/{s['group']} | {s['received']} | {s['page_count']} | {s['original_sha256']} |\n")
    f.write('\nOs endereços CVM e caminhos dos originais, junto das páginas usadas por achado, estão em `first_findings.json`. ')
    f.write('Complementos: IPCA `12c48fbccc3b165c86a3dc0947b3afde605bf6c392052879ef2cb3bb43005274`; ')
    f.write('metadados da cotação `05cdeddffd731c2224913b774a76fcef6f90b85463102eaabb402065836503f2`; ')
    f.write('registro bruto COTAHIST `a1cadc7b034084886fb24feb7c87e5e0702400e070599070d2ded4cb8c1d00ea`.\n')

files=['first_opinion.md','first_findings.json','independent_calculations.json','read_log.jsonl','integrity_checks.json']
seal={'created_at_utc':datetime.now(timezone.utc).isoformat(),'first_opinion_preserved':True,
      'merits_feedback_received':False,
      'sha256':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in files}}
with (OUT/'first_opinion_seal.json').open('x') as f:
    json.dump(seal,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'review_decision':result['review_decision'],'quality':result['quality_category_supported'],
                  'valuation':result['valuation_category_supported'],'pe_lower_outstanding':calc['valuation']['pe_lower_outstanding'],
                  'seal':seal},ensure_ascii=False,indent=2))
