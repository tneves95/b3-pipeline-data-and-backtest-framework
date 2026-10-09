"""Revisão cega independente. Lê apenas o pacote autorizado; não usa retornos.

Execução: PYTHONDONTWRITEBYTECODE=1 python .../review_channels.py
Todas as saídas novas ficam na pasta deste script. Imports de código do projeto
limitam-se às duas cópias locais dos bundles B2 autorizados.
"""
import collections
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent / 'audit-blind-20261009'
DIMENSIONS = ('durability', 'capital_economics', 'earnings_reliability',
              'financial_resilience', 'capital_allocation', 'governance')
ACCESSES = {}

def read(rel):
    p = BUNDLE / rel
    raw = p.read_bytes()
    ACCESSES[rel] = {'path': str(p), 'sha256_file': hashlib.sha256(raw).hexdigest(),
                     'bytes': len(raw), 'operation': 'read_only'}
    return raw

def jread(rel):
    return json.loads(read(rel))

def save(name, obj):
    if (HERE / name).exists():
        assert json.loads((HERE / name).read_text()) == obj, 'Refusing to overwrite existing output'
        return
    with (HERE / name).open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def csave(name, rows):
    if not rows:
        return
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    for row in rows:
        w.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                    if isinstance(v, (dict, list)) else v for k, v in row.items()})
    if (HERE / name).exists():
        assert (HERE / name).read_bytes() == f.getvalue().encode(), 'Refusing to overwrite existing output'
        return
    with (HERE / name).open('x', newline='') as dest:
        dest.write(f.getvalue())

read('protocol_v2_redacted.md')
for name in ['b00s_fundamentals.py', 'b00s_incremental.py', 'b00s_documentary.py',
             'b00s_funding.py', 'stage1_continuity.py', 'b2_protocol.md',
             'b2_callsite.txt', 'b2_simulation_callsite.txt', 'funding_policy_2015.json']:
    read('systemic/' + name)
rows = jread('systemic/decisions.json')
assert len(rows) == 229

# Controle PIT em cada decisão isoladamente: nunca transferir prova posterior.
pit_issues = []
def dates_walk(obj, cutoff, root, keypath=''):
    if isinstance(obj, dict):
        for key, value in obj.items():
            kp = keypath + '.' + key
            if key in ('received', 'period_end', 'cutoff') and isinstance(value, str) and value:
                if value[:10] > cutoff:
                    pit_issues.append({'decision': root, 'field': kp, 'date': value, 'cutoff': cutoff})
            dates_walk(value, cutoff, root, kp)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            dates_walk(value, cutoff, root, keypath + f'[{i}]')

for r in rows:
    dates_walk(r, r['cutoff'], f"{r['ticker']}:{r['year']}")
save('pit_metadata_check.json', {'decisions': 229, 'issues': pit_issues,
     'limitation': 'Metadados de fontes sistêmicas conferidos; PDFs sistêmicos fora dos dois casos não estão no escopo.'})

def metric_class(r, k):
    v = r.get(k)
    if v is None:
        return 'ND_FALTA_PROVA'
    if k == 'real_eps_cagr':
        return 'PASS_NECESSARIO' if v >= .04 else 'FAIL_NECESSARIO'
    if k == 'average_payout':
        return 'PASS_MECANICO_RETENCAO_RECURRENCIA_A_VERIFICAR' if v <= .80 else 'FAIL_MECANICO_RECURRENCIA_A_VERIFICAR'
    if k == 'return_on_capital_median':
        return 'PASS_NECESSARIO' if v >= r['inflation_reference'] + .06 else 'FAIL_NECESSARIO'
    return 'PASS_NECESSARIO' if v is True else 'FAIL_NECESSARIO'

premium = []
for r in rows:
    pe = r.get('normalized_pe')
    interval = r.get('normalized_pe_interval')
    mechanical = r.get('mechanical_normalized_pe')
    intersects = bool(interval and interval['lower'] <= 25 and
                      (interval['upper'] is None or interval['upper'] > 15))
    if not ((pe is not None and 15 < pe <= 25) or intersects or
            (mechanical is not None and 15 < mechanical <= 25)):
        continue
    assessment = r['documentary_assessment']
    vs = assessment['valuation']['status']
    certification = ('INTERVALO_CERTIFICADO' if interval else
                     'PONTO_CERTIFICADO' if vs == 'COMPARABLE' and not r['missing'].startswith('UNQUOTED')
                     else 'PL_SOMENTE_MECANICO')
    evidence = assessment['valuation']['evidence']
    premium.append(dict(year=r['year'], ticker=r['ticker'], sector=r['sector'],
        price_certification=certification, normalized_pe=pe,
        normalized_pe_interval=interval, mechanical_normalized_pe=mechanical,
        decision=r['valuation_status'], eps=r.get('real_eps_cagr'),
        eps_judgement=metric_class(r, 'real_eps_cagr'), payout=r.get('average_payout'),
        payout_judgement=metric_class(r, 'average_payout'),
        roc=r.get('return_on_capital_median'), roc_kind=r.get('return_on_capital_kind'),
        threshold=r['inflation_reference']+.06,
        roc_judgement=metric_class(r, 'return_on_capital_median'),
        solidity=r.get('solidity_proven'), solidity_judgement=metric_class(r, 'solidity_proven'),
        independent_conclusion='FAIL_NECESSARIO_DOCUMENTADO' if r['valuation_status']=='REJECTED_REINVESTMENT'
            else 'ND_NAO_ZERO_ECONOMICO',
        reason=assessment['valuation']['reason'], sources=evidence,
        admission_impact='Pendente pode abrir compra; reprovação necessária exige correção da prova para mudar.'
            if r['valuation_status']=='REJECTED_REINVESTMENT' else
            'Completar prova pode admitir premium; intervalos que cruzam15 podem admitir via madura; incumbência não exige nova aprovação.'))
csave('premium_inventory.csv', premium)
save('premium_inventory.json', premium)

# Classificação humana explícita da natureza do contrário, depois de ler todos
# os contrários ND e as razões das referências genéricas. Não é score de qualidade.
# Na categoria LACUNA o texto exige demonstração/recorrência/comutatividade; não
# estabelece resultado econômico adverso adicional. ALERTA identifica restrição,
# queda/perda, dívida/obrigação ou conflito concreto; não prova falha estrutural.
gap_keys = set()
for r in rows:
    t,y = r['ticker'],r['year']
    if t == 'CSMG3':
        for d in ['capital_economics','capital_allocation']:
            if y <= 2023:
                gap_keys.add((y,t,d))
    if t == 'COCE5':
        gap_keys.add((y,t,'governance'))
    if t == 'CPLE6' and y <= 2023:
        gap_keys.update((y,t,d) for d in ['capital_economics','financial_resilience','capital_allocation'])
    if t == 'BRSR6' and 2018 <= y <= 2020:
        gap_keys.update((y,t,d) for d in ['capital_economics','capital_allocation','governance'])
    if t == 'ITUB4' and y >= 2018:
        gap_keys.add((y,t,'governance'))
    if t == 'BBAS3' and 2018 <= y <= 2019:
        gap_keys.update((y,t,d) for d in ['capital_economics','capital_allocation','governance'])
    if t == 'SANB4' and 2021 <= y <= 2023:
        gap_keys.add((y,t,'capital_allocation'))
    if t == 'NEOE3' and y in [2021,2022,2023,2024]:
        gap_keys.add((y,t,'governance'))
    if t == 'VIVT3' and y == 2024:
        gap_keys.add((y,t,'governance'))
dimension_rows = []
judgements = []
for r in rows:
    nds=[]
    for name,d in r['documentary_assessment']['dimensions'].items():
        nd=d['status']=='INDETERMINATE'
        if nd:
            nds.append(name)
        category=('LACUNA_DE_PROVA_SEM_ALERTA_ADVERSO_ADICIONAL' if (r['year'],r['ticker'],name) in gap_keys
                  else 'ALERTA_ECONOMICO_COM_PROVA_DE_QUALIDADE_INSUFICIENTE') if nd else 'DIMENSAO_APROVADA_COM_CONTRAPONTOS'
        dimension_rows.append(dict(year=r['year'], ticker=r['ticker'], sector=r['sector'],
            dimension=name, status=d['status'], independent_nd_nature=category,
            sufficient_structural_rejection=bool(d.get('material_evidence')) and d['status']=='REJECTED_EVIDENCED',
            favorable=d.get('favorable',d.get('favorable_evidence')), contrary=d['contrary_evidence'],
            reason=d['reason'], missing=d.get('missing'),
            current_incremental_review=d.get('review_'+str(r['year'])),
            sources=d['evidence']))
    judgements.append(dict(year=r['year'], ticker=r['ticker'], cnpj=r['cnpj'], sector=r['sector'],
        frozen_quality_category=r['quality_category'], independent_quality_judgement=
            'ND_DOCUMENTAL_MANTIDO_SEM_REJEICAO_FORCADA' if nds else 'APROVACAO_COMPATIVEL_COM_GATE_FONTES_NAO_REAUDITADAS',
        unresolved_dimensions=nds, prior_to_cutoff_metadata_clean=not any(
            q['decision']==f"{r['ticker']}:{r['year']}" for q in pit_issues),
        limitation='Metadados e coerência do juízo congelado; reauditoria de original limitada a TIMP3/SBSP3 2014.'))
csave('vq_dimension_inventory.csv', dimension_rows)
save('independent_judgements_229.json', judgements)

coverage=[]
for y in range(2014,2026):
    for sector in ['Bancos','Energia','Saneamento','Seguros','Telecom']:
        candidates=[r for r in rows if r['year']==y and r['sector']==sector]
        v=dict(year=y,sector=sector,total=len(candidates),
            qualified=sum(r['quality_category'].startswith('QUALIFIED') for r in candidates),
            nd=sum(r['quality_category']=='INDETERMINATE' for r in candidates),
            rejected=sum(r['quality_category']=='REJECTED_EVIDENCED' for r in candidates))
        v['nd_pct']=100*v['nd']/v['total'] if v['total'] else None
        v.update({d+'_nd':sum(r['documentary_assessment']['dimensions'][d]['status']=='INDETERMINATE'
                              for r in candidates) for d in DIMENSIONS})
        coverage.append(v)
csave('vq_coverage_sector_year.csv', coverage)
summary = dict(total=229, valuation=dict(collections.Counter(r['valuation_status'] for r in rows)),
    mechanical_valuation=dict(collections.Counter(r['mechanical_valuation_status'] for r in rows)),
    quality=dict(collections.Counter(r['quality_category'] for r in rows)),
    premium_price_categories=dict(collections.Counter(r['price_certification'] for r in premium)),
    indicator_present={k:sum(r.get(k) is not None for r in rows) for k in
        ['real_eps_cagr','average_payout','return_on_capital_median','solidity_proven']},
    dimensions={d:dict(collections.Counter(r['documentary_assessment']['dimensions'][d]['status'] for r in rows))
                for d in DIMENSIONS},
    nd_contrary_nature=dict(collections.Counter(d['independent_nd_nature'] for d in dimension_rows if d['status']=='INDETERMINATE')),
    nd_contrary_nature_by_dimension={dim:dict(collections.Counter(d['independent_nd_nature'] for d in dimension_rows
        if d['status']=='INDETERMINATE' and d['dimension']==dim)) for dim in DIMENSIONS},
    sector={s:dict(collections.Counter(r['quality_category'] for r in rows if r['sector']==s))
            for s in ['Bancos','Energia','Saneamento','Seguros','Telecom']},
    nd_pct=100*181/229)
save('coverage_summary.json', summary)

# Releitura efetiva dos originais dos dois casos. Hash PDF descomprimido e
# pdftotext independente da extração transportada; nenhum download externo.
originals=[]
original_text=[]
for case in ['TIMP3_2014','SBSP3_2014']:
    decision=jread(case+'/decision.json')
    jread(case+'/financial_extract.json')
    manifest=jread(case+'/bundle_manifest.json')
    srcs=jread(case+'/sources.json')
    refs={}
    for section in [decision['documentary_assessment']['valuation'],
                    *decision['documentary_assessment']['dimensions'].values()]:
        for ref in section['evidence']:
            refs.setdefault((ref['docid'],ref['group']),set()).update(ref['pages'])
    for src in srcs:
        raw=gzip.decompress(read(case+'/'+src['original']))
        digest=hashlib.sha256(raw).hexdigest()
        assert digest==src['original_sha256']
        assert src['received']<=decision['cutoff']
        pages=json.loads(gzip.decompress(read(case+'/'+src['pages'])))
        assert len(pages)==src['page_count']
        assert raw.startswith(b'%PDF-')
        try:
            proc=subprocess.run(['pdftotext','-layout','-','-'],input=raw,capture_output=True,check=True)
            independent=proc.stdout.decode('utf-8',errors='replace').split('\f')
        except FileNotFoundError:
            independent=None
        wanted=sorted(refs.get((src['docid'],src['group']),set()))
        originals.append(dict(case=case,docid=src['docid'],group=src['group'],
            received=src['received'],receipt_label=src['receipt_label'],cutoff=decision['cutoff'],
            original_sha256=digest,hash_verified=True,page_count=len(pages),reviewed_pages=wanted,
            url=src['url'],method='PDF descomprimido, assinatura/hash verificados; leitura das páginas textuais transportadas',
            independent_reextraction_available=independent is not None,
            limitation='pdftotext e bibliotecas PDF ausentes; não houve renderização visual nem reextração independente.'))
        for pg in wanted:
            original_text.append(dict(case=case,docid=src['docid'],group=src['group'],page=pg,
                received=src['received'],sha256=digest,
                transported_extraction=pages[pg-1],independent_pdf_text=independent[pg-1] if independent else None))
save('original_receipts_hashes.json', originals)
save('case_original_pages.json', original_text)

# Cópias locais isoladas dos únicos dois módulos de projeto importados.
sys.dont_write_bytecode=True
modules={}
for name in ['b00s_funding','stage1_continuity']:
    raw=read('systemic/'+name+'.py')
    dest=HERE/(name+'_bundle.py')
    with dest.open('xb') as f:
        f.write(raw)
    spec=importlib.util.spec_from_file_location(name+'_blind_bundle',dest)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    modules[name]=module
fund=modules['b00s_funding']
continuity=modules['stage1_continuity']
policy=jread('systemic/funding_policy_2015.json')
assert hashlib.sha256(read('systemic/b00s_funding.py')).hexdigest()==policy['code_sha256']
ids={
    'A3':{'cnpj':'A','sector':'Bancos'}, 'A4':{'cnpj':'A','sector':'Bancos'},
    'AR':{'cnpj':'A','sector':'Bancos'}, 'AS':{'cnpj':'A','sector':'Bancos'},
    'B3':{'cnpj':'B','sector':'Bancos'}, 'B4':{'cnpj':'B','sector':'Bancos'},
    'C3':{'cnpj':'C','sector':'Energia'}, 'D3':{'cnpj':'D','sector':'Telecom'},
    'E3':{'cnpj':'E','sector':'Seguros'}, 'F3':{'cnpj':'F','sector':'Saneamento'}}
tests=[]
def run_test(name, fn, expected_error=None):
    try:
        details=fn()
        assert expected_error is None, 'Expected ValueError'
        tests.append(dict(name=name,status='PASS',details=details))
    except ValueError as err:
        assert expected_error and expected_error in str(err), str(err)
        tests.append(dict(name=name,status='PASS',expected_error=str(err)))

def scenario(holdings,status,qualified,expected):
    requests=fund.reference_entries(holdings,status,qualified,ids)
    after,ledger=fund.renew_reference_entries(holdings,status,requests)
    assert set(after)==set(expected)
    assert all(math.isclose(after[t],v,abs_tol=1e-10) for t,v in expected.items())
    assert math.isclose(sum(holdings.values()),sum(after.values()),abs_tol=1e-10)
    survivors=[t for t in holdings if status.get(t)!='FAIL']
    assert all(after[t]>0 for t in survivors)
    factors=[after[t]/holdings[t] for t in survivors]
    assert not factors or all(math.isclose(v,factors[0],abs_tol=1e-12) for v in factors)
    return dict(before=holdings,status_by_ticker=status,qualified=qualified,
                requests=requests,after=after,ledger=ledger)

run_test('single_new_empty_sector_no_FAIL',lambda:scenario({'A3':100},{'A3':'PASS','C3':'PASS'},['C3'],{'A3':80,'C3':20}))
run_test('same_sector_retained_ND_incumbent',lambda:scenario({'A3':100},{'A3':'INDETERMINATE','B3':'PASS'},['B3'],{'A3':90,'B3':10}))
run_test('incumbent_missing_base_status_preserved',lambda:scenario({'A3':100},{'B3':'PASS'},['B3'],{'A3':90,'B3':10}))
run_test('FAIL_proceeds_insufficient',lambda:scenario({'A3':95,'D3':5},{'A3':'PASS','D3':'FAIL','C3':'PASS'},['C3'],{'A3':80,'C3':20}))
run_test('FAIL_proceeds_exceed_request',lambda:scenario({'A3':50,'D3':50},{'A3':'PASS','D3':'FAIL','C3':'PASS'},['C3'],{'A3':50,'C3':50}))
run_test('multiple_entries_not_rebalanced',lambda:scenario({'A3':60,'AR':10,'D3':30},{'A3':'PASS','AR':'INDETERMINATE','D3':'PASS','B3':'PASS','C3':'PASS'},['B3','C3'],{'A3':42,'AR':7,'D3':21,'B3':10,'C3':20}))
run_test('CNPJ_second_class_no_entry',lambda:scenario({'A3':80,'AR':10,'AS':10},{'A3':'PASS','AR':'INDETERMINATE','AS':'INDETERMINATE','A4':'PASS'},['A4'],{'A3':80,'AR':10,'AS':10}))
run_test('two_new_classes_blocked',lambda:fund.reference_entries({'C3':100},{'C3':'PASS','B3':'PASS','B4':'PASS'},['B3','B4'],ids),'Two classes')
run_test('FAIL_base_new_purchase_blocked',lambda:fund.reference_entries({'A3':100},{'A3':'PASS','C3':'FAIL'},['C3'],ids),'Only base PASS')
run_test('ND_base_new_purchase_blocked',lambda:fund.reference_entries({'A3':100},{'A3':'PASS','C3':'INDETERMINATE'},['C3'],ids),'Only base PASS')
run_test('same_lineage_FAIL_PASS_conflict_blocked',lambda:fund.reference_entries({'A3':100},{'A3':'FAIL','A4':'PASS'},['A4'],ids),'Conflicting FAIL and PASS')
run_test('no_entry_buy_filter_ND_preserves',lambda:scenario({'A3':70,'D3':30},{'A3':'PASS','D3':'PASS'},[],{'A3':70,'D3':30}))
run_test('no_entry_with_FAIL_only_redistribution',lambda:scenario({'A3':70,'D3':30},{'A3':'INDETERMINATE','D3':'FAIL'},[],{'A3':100}))
run_test('all_FAIL_without_destination_blocked',lambda:fund.renew_reference_entries({'A3':100},{'A3':'FAIL'},{}),'All holdings FAIL')
run_test('all_FAIL_eligible_destination',lambda:scenario({'A3':100},{'A3':'FAIL','C3':'PASS'},['C3'],{'C3':100}))

# Avaliação do callsite de seleção, só funções puras e metadados sintéticos.
namespace={'identities':lambda:ids}
exec(compile(read('systemic/b2_callsite.txt').decode(),'authorized_b2_selection_callsite','exec'),namespace)
def callsite_nd():
    rs=[{'year':2015,'ticker':'A3','cnpj':'A','sector':'Bancos'},
        {'year':2015,'ticker':'C3','cnpj':'C','sector':'Energia'}]
    dec={(2015,'A3'):{'valuation_status':'INDETERMINATE','quality_category':'INDETERMINATE'},
         (2015,'C3'):{'valuation_status':'INDETERMINATE','quality_category':'INDETERMINATE'}}
    for variant in ['VVAL','VQ']:
        targets=namespace['select_filtered'](rs,{'A3':100},dec,variant)
        assert targets=={}
        after,_=fund.renew_reference_entries({'A3':100},{'A3':'PASS','C3':'PASS'},targets)
        assert after=={'A3':100}
    return {'buy_filter_ND': 'zero_new_buy', 'incumbent_A3':100}
run_test('buy_filter_ND_callsite_no_forced_exit',callsite_nd)
def callsite_repr():
    row={'year':2015,'ticker':'A4','cnpj':'A','sector':'Bancos'}
    selected=namespace['represented_targets']([row],{'A3':100})
    assert selected=={'A3':1}
    requests=fund.reference_entries({'A3':100},{'A3':'INDETERMINATE','A4':'PASS'},selected,ids)
    assert requests=={}
    return {'targets':selected,'requests':requests}
run_test('callsite_same_CNPJ_traded_representation',callsite_repr)
def old_failure():
    after,_=continuity.renew_b2({'A3':100},{'A3':'PASS','C3':'PASS'},{'C3':1})
    assert after['A3']==0 and after['C3']==100
    return {'old_generic_after':after,'issue':'Zeroing survivor when only entrant has normalized weight1; active VVAL/VQ callsite routes through reference_entries instead.'}
run_test('legacy_B2_singleton_target_regression_demonstrated',old_failure)
save('b2_synthetic_tests.json',{'status':'PASS','count':len(tests),'tests':tests,
    'no_future_returns':True,'nav_units':'synthetic dimensionless100; not real wealth',
    'funding_code_sha256':policy['code_sha256'],
    'limitation':'CNPJ/lineage metadata source itself not transported; tests use explicit synthetic accepted lineages.'})
save('scope_access_log.json', {'authorized_root':str(BUNDLE),'accessed':list(ACCESSES.values()),
    'output_root':str(HERE),'read_only_inputs':True,'portfolio_returns_accessed':False,
    'portfolio_simulations_run':False,'market_series_accessed':False,
    'forbidden_paths_accessed':[], 'network_calls':0,
    'imports_project_code':['b00s_funding_bundle.py','stage1_continuity_bundle.py'],
    'libraries':'Python standard library; tentativa pdftotext (ausente); nenhum pacote instalado',
    'shell_discovery':'pwd; rg unavailable; find only the three authorized subdirectories; wc/cat/sed/python only authorized inputs',
    'note':'b2_simulation_callsite.txt é excerto autorizado: contém declaração de variáveis de resultados, mas nenhuma série, resultado ou cálculo de retorno foi lido/executado.'})
print(json.dumps({'premium':dict(collections.Counter(r['price_certification'] for r in premium)),
    'nd_contrary':summary['nd_contrary_nature'],'pit_issues':pit_issues,'b2_tests':len(tests),
    'original_pdfs_verified':len(originals),'original_pages':len(original_text)},ensure_ascii=False))
