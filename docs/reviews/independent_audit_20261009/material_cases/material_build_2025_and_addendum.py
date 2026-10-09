"""Standalone arithmetic/evidence recorder authored by the independent reviewer.
Reads only the authorized blind packages, its own sealed opinion and libraries.
Does not import repository implementation, portfolio data or returns.
"""
from pathlib import Path
import datetime as dt
import gzip, hashlib, io, json, math, statistics, sys, zipfile
import xml.etree.ElementTree as ET

BASE = Path('/workspaces/b3-pipeline-data-and-backtest-framework/returns_2014_2026_stage1')
PACK = BASE / '.pr4-state/audit-blind-20261009'
OUT = BASE / '.pr4-state/independent-material-cases'
sys.path.insert(0, str(BASE / '.pr4-state/deps'))
from pypdf import PdfReader
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
ledger = []

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read(path, purpose):
    b = path.read_bytes()
    ledger.append({'path': str(path), 'sha256_bytes': sha(b), 'purpose': purpose})
    return b

def js(path, purpose):
    raw = read(path, purpose)
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)

def create(name, data):
    p = OUT / name
    with p.open('x', encoding='utf-8') as f:
        f.write(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    return {'path': str(p), 'sha256': sha(p.read_bytes())}

def factor(ipc, year, cutoff_year):
    rows = ipc['sgs433_known_monthly_values']
    return math.prod(1 + float(r['valor']) / 100 for r in rows
                     if year < int(r['data'][-4:]) and
                     (int(r['data'][-4:]), int(r['data'][3:5])) <= (cutoff_year, 5))

def annual(extract, year):
    rows = [r for r in extract['facts'] if r['year'] == year and
            r['perimeter'] == 'con' and r['statement'] == 'DRE' and
            r['account'] == '3.11.01' and r['period_start'] == f'{year}-01-01' and
            r['period_end'] == f'{year}-12-31' and r['received'] <= '2025-06-30']
    r = max(rows, key=lambda r: (r['received'], r['reference'], r['version']))
    assert r['scale'] == 'MIL'
    return r, r['value'] * 1000

def issued(extract):
    rows = [r for r in extract['fre'] if r.get('part') == 'capital_social' and
            r['raw'].get('Tipo_Capital') == 'Capital Emitido' and r['received'] <= '2025-06-30']
    return max(rows, key=lambda r: (r['received'], r['raw']['Data_Referencia'], int(r['raw']['Versao'])))

def quote(package):
    d = js(package / 'selection_quotes.json', 'Only raw selection-day COTAHIST records; no archive/future prices opened')
    for r in d['quotes']:
        raw = r['raw_record']
        assert sha(raw.encode('ascii')) == r['record_sha256']
        close = int(raw[108:121]) / 100
        qfactor = int(raw[210:217])
        assert close == r['close'] and qfactor == r['quotation_factor']
        r['independent_close'] = close
        r['independent_quotation_factor'] = qfactor
        r['independent_date'] = raw[2:10]
        r['independent_ticker'] = raw[12:24].strip()
        assert r['independent_date'] == r['date'].replace('-', '')
        assert r['independent_ticker'] == r['ticker']
    return d

opened_pages = {
 'PSSA3_2025': {
  ('111606',412): [6,46,65,66,74], ('123439',412): [64,90],
  ('134284',412): [67,93,102,107], ('144776',412): [1,2,3,49,50,57,85,86,90,95,98,102],
  ('147187',192): [3,4,5,7,8,13,14,18,19,29,33]},
 'CSMG3_2025': {
  ('102985',412): [37,38,39,40,68,69], ('124409',412): [4,6,16,31,35,45,48,61,62,63],
  ('145717',412): [23,24,38,39,40,42,50,64,66,67], ('145717',1654): [1,2,3],
  ('147606',192): [1,2,3,4,5], ('147606',193): [18,19]}
}
data = {}
for name in ['PSSA3_2025', 'CSMG3_2025']:
    p = PACK / name
    d = {
      'extract': js(p / 'financial_extract.json', 'Independent selection of latest annual attributable NI and issued class capital; audit text'),
      'sources': js(p / 'sources.json', 'Primary source inventory and original/receipt hashes'),
      'decision': js(p / 'decision.json', 'Frozen decision challenged independently; not treated as authority'),
      'manifest': js(p / 'bundle_manifest.json', 'Transport inventory only'),
      'ipca': js(p / 'ipca_known.json', 'Monthly SGS433 facts known no later than cutoff'),
      'quotes': quote(p)}
    for s in d['sources']:
        assert s['received'] <= '2025-06-30'
        raw = read(p / s['original'], 'Original bytes hash verification; human page review only where listed below')
        unpacked = gzip.decompress(raw)
        assert sha(unpacked) == s['original_sha256'], (name, s['docid'], s['group'])
        if (str(s['docid']), s['group']) in opened_pages[name]:
            page_data = js(p / s['pages'], 'Page text inspection: ' + str(opened_pages[name][(str(s['docid']), s['group'])]))
            s['independently_reviewed_pages'] = opened_pages[name][(str(s['docid']), s['group'])]
            if s['group'] == 1654:
                s['page_semantics'] = 'Logical XML report units; NOT PDF page numbers'
        if s.get('submission'):
            for field, hfield in [('path','sha256'),('metadata','metadata_sha256')]:
                sub = s['submission']
                raw = read(p / sub[field], 'Submission/receipt bytes hash verification')
                assert sha(gzip.decompress(raw)) == sub[hfield]
    d['verified_delivery'] = {}
    relevant_docids = sorted({k[0] for k in opened_pages[name]})
    for doc in relevant_docids:
        receipt_path = p / 'review_originals' / f'cvm_{doc}.delivery.xml.gz'
        if receipt_path.exists():
            receipt = ET.fromstring(gzip.decompress(read(receipt_path, 'Parse primary CVM delivery date/protocol')))
            selected = {e.tag.split('}')[-1]: e.text for e in receipt.iter()
                        if e.tag.split('}')[-1] in ['DataEntrega','ProtocoloEntrega','DataReferenciaDocumento']}
            d['verified_delivery'][doc] = selected
    ip = d['ipca']['known_may_availability']
    pdf = gzip.decompress(read(p / ip['original'], 'Primary IBGE May2025 cover and release date'))
    assert sha(pdf) == ip['sha256']
    cover = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
    assert '10/06/2025' in cover
    d['ipca_primary_release_confirmed'] = '2025-06-10 (original PDF p1: Publicado em 10/06/2025 às 9 horas)'
    d['factors'] = {y: factor(d['ipca'], y, 2025) for y in range(2020,2025)}
    d['annual_rows'] = {y: annual(d['extract'], y)[0] for y in range(2020,2025)}
    d['reported_ni'] = {y: annual(d['extract'], y)[1] for y in range(2020,2025)}
    d['issued'] = issued(d['extract'])
    capraw = d['issued']['raw']
    assert int(capraw['Quantidade_Acoes_Preferenciais']) == 0
    d['market_cap'] = int(capraw['Quantidade_Acoes_Ordinarias']) * d['quotes']['quotes'][0]['independent_close']
    data[name] = d

def ev(name, doc, group, pages, polarity, text):
    d = data[name]
    s = next(s for s in d['sources'] if str(s['docid']) == str(doc) and s['group'] == group)
    return {'docid': str(doc), 'group': group, 'page_or_logical_units': pages,
            'received': s['received'], 'receipt_label': s.get('receipt_label'),
            'original_sha256': s['original_sha256'], 'original': str(PACK/name/s['original']),
            'page_semantics': s.get('page_semantics', 'Original PDF pages, 1-based'),
            'polarity': polarity, 'finding': text}

p = data['PSSA3_2025']
pn = p['reported_ni']; pf = p['factors']
portod = {2023: [59994000,48502000,35162000,30477000,21787000],
          2024: [75000000,285004000,25167000,39925000,4033000,9741000]}
plower = {2020:pn[2020], 2021:None, 2022:None,
          2023:pn[2023]-sum(portod[2023]), 2024:pn[2024]-sum(portod[2024])}
central = pn[2020] * pf[2020]
assert pn[2021]*pf[2021] < central and pn[2022]*pf[2022] < central
assert plower[2023]*pf[2023] > central and plower[2024]*pf[2024] > central
epsfirst = pn[2020] / 648800000
epslow = plower[2024] / 648563000
epshigh = (pn[2024]-39000000) / 648563000
cagr = [(eps/epsfirst/(pf[2020]/pf[2024]))**(1/4)-1 for eps in [epslow,epshigh]]
inflation_ref = math.prod(1+float(r['valor'])/100 for r in p['ipca']['sgs433_known_monthly_values']
              if (2024,5)<(int(r['data'][-4:]),int(r['data'][3:5]))<=(2025,5))-1
roe_lower = min(plower[2023]/11538100000,plower[2024]/13233000000)
portocalc = {'unit':'BRL','cutoff':'2025-06-30','annual_attributable_ni':pn,
 'selected_annual_fact_rows':p['annual_rows'],'ipca_factors_through_known_May2025':pf,
 'issued_class_capital':p['issued'],'selection_quote':p['quotes'],'market_cap':p['market_cap'],
 'positive_items_deducted_gross_no_loss_addbacks':portod,'nominal_lower_bounds':plower,
 '2021_2022_upper_bounds':{2021:pn[2021],2022:pn[2022]},
 'normalization_anchor_conditional_2020':central,'pe_at_anchor':p['market_cap']/central,
 'robust_median_proof':'Two 2021/2022 upper bounds below 2020 real anchor and two 2023/2024 lower bounds above it fix the median, conditional on the admissible 2020 cycle normalization. No arbitrary zero replaces negative infinity.',
 'cycle_limitation':'FY2020 pandemic claims experience is not a permanent forward run rate; no invented retrospective adjustment. Further cycle adjustment does not authorize premium.',
 'ifrs17_bridge':'144776/412 pp49-50: 2023 NI IFRS4 2,266,427k -> IFRS17 2,266,149k; 2024 2,653,946k -> 2,644,845k. Deltas -278k and -9,101k do not reorder the demonstrated bounds.',
 'weighted_attributable_shares_2020_split_adjusted':648800000,
 'weighted_attributable_shares_2024':648563000,'eps_2020':epsfirst,'eps_2024_interval':[epslow,epshigh],
 'real_eps_cagr_4_intervals_5_exercises':cagr,'growth_threshold':0.04,
 'roe_last3_median_lower_bound_from_two_proven_years':roe_lower,
 'inflation_12months_knownMay2025':inflation_ref,'roe_required_inflation_plus_6pp':inflation_ref+0.06,
 'payout_reported_diagnostic_only':[0.50,0.408,0.3448,0.37,0.45],
 'payout_normalized_certification':'Not established by reported payout alone; extraordinary and reserves treatment still needed.',
 'capital_1Q25_million':{'insurance_available':5964,'insurance_required':5297,'insurance_surplus':667,
  'financial_available':2532,'financial_required':2033,'financial_surplus':499,'regulated_surplus':1166,
  'holding_available':2905,'aggregate_available':11401,'aggregate_required':7330,'aggregate_surplus_including_holding':4071},
 'commission_estimate_change_1Q25':{'lower_commission_cost':42100000,'higher_health_net_income':19300000,
 'fraction_of_health_income_growth_74_3m':19300000/74300000},
 'insurance_combined_1Q25_vs_1Q24':[0.927,0.889],'auto_claim_ratio_1Q25_vs_1Q24':[0.601,0.562]}

c=data['CSMG3_2025']; cn=c['reported_ni']; cf=c['factors']
copasad = {2020:[177833000,152838000,15248000],2022:[136868000,78915000,10722000,24852000,818000,477000,38103000,2407000],
           2023:[344324000,67703000,49098000,1160000,153970000,8710000],
           2024:[388700000,43530000,52136000,2428000,10399000,1084000,1428000]}
clower={y:cn[y]-sum(v) for y,v in copasad.items()}
realcl={y:v*cf[y] for y,v in clower.items()}
medianfloor=sorted([float('-inf')]+list(realcl.values()))[2]
copasacalc={'unit':'BRL','annual_attributable_ni':cn,'selected_annual_fact_rows':c['annual_rows'],
 'ipca_factors_through_knownMay2025':cf,'issued_class_capital':c['issued'],'selection_quote':c['quotes'],
 'market_cap':c['market_cap'],'gross_positive_items_deducted_no_loss_addbacks':copasad,
 'nominal_lower_bounds':clower,'2021_bound':'NEGATIVE_INFINITY (unknown; not zero)',
 'real_lower_bounds':realcl,'median_lower_bound':medianfloor,'pe_upper_bound':c['market_cap']/medianfloor,
 'profit_needed_for_pe15':c['market_cap']/15,'profit_bound_gap_to_pe15':medianfloor-c['market_cap']/15,
 'median_logic':'For every possible vector satisfying the four annual lower bounds and one unknown coordinate, the order-statistic median is at least the median of those lower bounds and -infinity. The ratio is therefore an upper bound, not a point P/L; upper bound >15 proves neither rejection nor admission.',
 'ordinary_items_preserved':'2022 amortized-cost accretion R$57.035m separated from financial-asset income R$67.757m; ordinary PIS/COFINS credits R$69.733m/65.462m and JCP tax benefits are not automatically windfalls.',
 'conservative_perimeter_precision':'2022 judicial reversal stress R$38.103m versus consolidated R$38.102m is a R$1k extra deduction. FY2023 construction inventory R$8.710m individual versus R$8.215m consolidated is an extra R$495k deduction. Both weaken the floor conservatively; neither can turn this bound into price certification.',
 'construction_capitalization_not_incremental_return':'Borrowing costs capitalized FY2024 R$122.882m/FY2023 R$117.891m; accounting capitalization is not cash generation or proof of ROIC.',
 'debt_funding':'19th issue R$1.3bn occurred July2024 with 10-year DI+0.90%/IPCA+7.2735% tranches. 20th R$900m authorized March10,2025 is not cash received at March31,2025.',
 'concession_scope':'1Q25: 637 water/308 sewage concessions, 83% revenue contracts after2031; 44 expired+1 void contracts ~4.7% revenue; top10 municipalities49% revenue. Continued billing is not proof of perpetual concession rights.'}

porto_evidence=[
 ev('PSSA3_2025','111606',412,[6,46,74],'PRO','FY2020 comparative NI attributable 1,688.191m, weighted shares648.800m already split adjusted. SELIC272.861m and retrospective Lei do Bem124.643m are FY2021 gains, not retroactive FY2020 deductions. Page74 visually checked because embedded table was absent from text.'),
 ev('PSSA3_2025','134284',412,[67,93,102,107],'MIXED','Tax-note benefit distinction, legal contingencies and Onco/property gains support conservative positive-item deductions; uncertain realization cannot be assumed ordinary earnings.'),
 ev('PSSA3_2025','144776',412,[2,49,50,57,85,86,90,95,98,102],'MIXED','Latest annual attributable NI/IFRS17 bridge and weighted shares verified. Gross judicial reversals285.004m, Onco75m, deposits tax25.167m and other positive lines deducted; no cost/tax addback. Reported payout45% cannot by itself certify normalized historical payout.'),
 ev('PSSA3_2025','147187',192,[3,4,5,7,8,13,14,18,19,29,33],'MIXED','1Q25 group income grows, but insurance income -21.4%, combined92.7% versus88.9% and auto claims60.1% versus56.2%. Sep2024 commission-retention estimate change adds19.3m to health quarterly NI. Bank portfolio sale changes NPL comparability. Original p29 image separates regulated surplus1,166m from holding2,905m.')]

copasa_evidence=[
 ev('CSMG3_2025','102985',412,[38,68,69],'MIXED','FY2020 other operating income177.833m, gross financial152.838m and positive tax15.248m support deliberately conservative lower bound; recurring JCP benefit retained.'),
 ev('CSMG3_2025','124409',412,[16,31,35,45,61,62,63],'MIXED','FY2022 financial accretion57.035m explicitly cost amortized; financial-asset line67.757m is not wholly windfall. Judicial reversal consolidated38.102m and tax incentive24.852m verified; conservative overdeductions retained.'),
 ev('CSMG3_2025','145717',412,[23,24,38,39,42,50,64,66,67],'MIXED','FY2023/24 other income and gross financial totals344.324m/388.700m, tax benefits, reversals and inventories permit independent lower bounds. Noncash capitalized borrowing and dividend50% do not establish economic productivity of CAPEX.'),
 ev('CSMG3_2025','145717',1654,[1],'CON','Grant Thornton unmodified opinion dated21Mar2025 includes emphasis: final judgment on Belo Horizonte street repaving, execution scope/cost not reliably estimable, no impact booked. Expected tariff recovery depends on judicial appraisal; it is not a guaranteed reimbursement. Auditor opinion does not cover the management report.'),
 ev('CSMG3_2025','145717',1654,[1,2],'PRO','PAA revenue/IT/unbilled estimates and investment capitalization were tested. COAUDI contemporary report says control coverage satisfactory and no significant internal-audit failures or independence differences; scope is limited, not a guarantee of future performance.'),
 ev('CSMG3_2025','147606',192,[1,2,3,4,5],'MIXED','Essential demand and extended concessions support durability; expired/void concessions and municipal concentration constrain it. Tariff+6.42%, volumes+4.2%, NI428.509m, EBITDA813.537m do not isolate incremental ROIC.'),
 ev('CSMG3_2025','147606',193,[18,19],'MIXED','Actual19th issue differs from March2025 authorized20th issue. Reported covenants fulfilled; financing capacity is not productive capital allocation proof.')]

opinions=[{
 'case':'PSSA3_2025','audit_status':'PASS','severity':'MEDIUM','vval_recommendation':'INDETERMINATE',
 'vq_recommendation':'QUALIFIED_SATISFACTORY',
 'conclusion':'Frozen no-premium-certification decision withstands material challenge. Normalized anchor P/L16.114 exceeds mature15; real EPS CAGR interval0.587%–4.865% crosses4%, so premium cannot be presumed. This is missing proof, not proof of a bad company.',
 'dimensions':{
  'durability':{'judgment':'SATISFACTORY','basis':'Diversified insurance/health/bank/services with actual recurring revenues and contracts; no inference of moat merely from BESST membership.'},
  'capital_economics':{'judgment':'SATISFACTORY','basis':'Conservative ROE from two latest years supports three-year median above inflation+6pp; this supports business quality, not isolated incremental returns or premium-growth certification.'},
  'earnings_reliability':{'judgment':'SATISFACTORY','audit_qualifier':'LIMITED','basis':'Attributable/perimeter bridge and positive-item deductions traced. Estimate change and quarter comparisons explicitly qualified; group growth cannot override insurance deterioration.'},
  'financial_resilience':{'judgment':'SATISFACTORY','basis':'Regulated capital surplus insurance667m plusfinance499m independently reconciled; holding2,905m separately identified. Reserve/claims/cycle and bank-credit risks remain.'},
  'allocation_and_dividends':{'judgment':'SATISFACTORY','audit_qualifier':'LIMITED','basis':'Reported distributions and investments compatible with mature satisfactory allocation; digital CAPEX/Onco expansion alone does not prove high incremental ROIC or normalized payout premium test.'},
  'governance':{'judgment':'SATISFACTORY','basis':'Timely CVM reports, disclosed accounting estimates, attributable-share bridge and audit extract without qualification; contemporary related-party/estimation risks disclosed. Original independent-auditor attachment not separately included for Porto2024; audit text supplied as primary CVM extracted record, limitation retained.'}},
 'evidence':porto_evidence,'independent_calculation':portocalc,
 'materiality_admission':'No new VVAL purchase certifiable via premium under V2. VQ satisfactory does not require premium metrics or an invented ROE floor. Misstating holding cash as regulated prudential excess overstates financial protection but does not by itself reverse satisfactory VQ.',
 'pending_specific':['Reconcile five annual normalized distributions/retained profit, gross/net JCP, extraordinary reserves, to certify <=80% average payout for premium.','Bound normalized FY2024 attributable EPS tightly enough that real growth threshold4% is wholly passed or failed, including Onco/commission-estimate/cycle effects.','Provide separate original auditor report2024 and trace credit-provision/related-party PAA if higher quality classification is proposed.','Demonstrate separate regulated-capital/claims sensitivities; distinguish holding resources and regulated requirements.']},
 {'case':'CSMG3_2025','audit_status':'PASS','severity':'MEDIUM','vval_recommendation':'INDETERMINATE',
 'vq_recommendation':'INDETERMINATE',
 'conclusion':'Preserved ND is supported. Independent median lower bound620.003m gives P/L upper bound17.154; it proves neither actual P/L>15 nor a mature buy. Gross income stripping is deliberately conservative, not exact normalized NI. Economic return of universalization CAPEX and allocation remains insufficiently established; final BH repaving obligation is additional material uncertainty, not an audit qualification.',
 'dimensions':{
  'durability':{'judgment':'SATISFACTORY','basis':'Essential services and majority long concessions support durability, constrained by expiration/litigation/regulation and49% concentration in ten municipalities.'},
  'capital_economics':{'judgment':'INDETERMINATE','basis':'Tariff/cash earnings and accounting capitalization cannot isolate maintenance/expansion invested capital and incremental returns for new projects/PPP.'},
  'earnings_reliability':{'judgment':'SATISFACTORY','audit_qualifier':'LIMITED','basis':'Attributable accounts and positive-item stress bounds traced; unmodified audit with PAA supports current statements. Judicial BH obligation unbooked due estimate uncertainty remains a material unresolved economic risk.'},
  'financial_resilience':{'judgment':'SATISFACTORY','audit_qualifier':'LIMITED','basis':'Long financing and fulfilled covenants disclosed; mandatory CAPEX/repaving cost and possible tariff recovery cannot be quantified as safe funding.'},
  'allocation_and_dividends':{'judgment':'INDETERMINATE','basis':'Universalization CAPEX, PPP studies, subsidiary results and50% payout lack project/per-share incremental economic return proof. No FCL/payout automatic rejection.'},
  'governance':{'judgment':'SATISFACTORY','audit_qualifier':'LIMITED','basis':'Contemporary COAUDI/auditor and disclosures support present information quality; fiscal/regulatory/controller conflicts need continued scrutiny. No retrospective privatization assumption.'}},
 'evidence':copasa_evidence,'independent_calculation':copasacalc,
 'materiality_admission':'VVAL and VQ new admission not certified. ND does not imply B00S failure, structural rejection, or sale of inherited B2 position. Exact sustainable NI could be higher than the floor; a higher upper P/L is not evidence of expensive actual value.',
 'pending_specific':['Reconcile annual positive components, gross versus net tax and attributable versus consolidated perimeter sufficiently to establish a tighter median interval or exact normal NI.','Separate maintenance/expansion/universalization and PPP obligations, incremental invested capital/returns, tariff recovery schedules, project and per-share economic outcomes.','Quantify BH repaving scope/cost/timetable and tariff-recovery legal mechanism before treating obligation as absorbed or immaterial.','Reconcile debt sources/use, actual receipt dates and funding of mandatory investments; assess subsidiary/COPANOR economic returns.']}]

report={'reviewer':'independent_material_cases','recorded_utc':NOW,'protocol':'V2 redacted supplied package',
 'independence_declaration':'I read only the authorized blind protocol/packages and library files, plus my own preserved initial2014 opinion for seal checks. No implementation, .pr4-work, other audits/checkpoints, GitHub, retrospective news, future returns or portfolios were read or recalculated. 2014 opinions were sealed before opening2025;2025 information is not used to change2014 judgments.',
 'audit_semantics':'PASS means the frozen classification withstands the material documentary challenge, including correct ND; not admission approval. ISSUE means a proven inconsistency. UNRESOLVED means a material proof gap remains. Severity expresses potential decision impact, not investment risk score.',
 'dimension_semantics':'SATISFACTORY and INDETERMINATE are dimension findings; LIMITED is only a textual documentary/normalization qualifier. SATISFACTORY_LIMITED, if encountered in2014 sealed wording, is not a new V2 category or protocol recommendation. Effective VQ final categories remain exactly V2.',
 'opinions':opinions,
 'original_visual_checks':[{'source':'PSSA3_2025/111606/412','page':74,'artifact':'/tmp/independent_PSSA2020_EPS_p74.png','purpose':'Shares/EPS table absent from extraction;648.800m2020 confirmed split-adjusted'}, {'source':'PSSA3_2025/147187/192','page':29,'artifact':'/tmp/independent_PSSA2025_capital_p29.png','purpose':'Holding vs regulated prudential capital disaggregation'}],
 'verified_receipts':{n:d['verified_delivery'] for n,d in data.items()},
 'hash_checks':'All supplied source originals and referenced submission/metadata decompressed hashes verified; reading bytes to checksum is distinguished from human page review.',
 'ipca_known_release':{n:d['ipca_primary_release_confirmed'] for n,d in data.items()},
 'sources_read_ledger':ledger.copy()}
json_receipt=create('material_review_2025.json',report)
lines=['# Revisão material independente —2025', '',
 'Registro UTC: '+NOW+'. Juízo formado após o selo2014; nenhum retorno futuro ou carteira foi lido/recalculado.', '',
 'PASS significa que a classificação congelada resiste ao desafio documental, inclusive quando preserva ND. Não significa autorização de compra. LIMITED é ressalva textual; não é categoria nova da V2.', '']
for o in opinions:
    lines.extend(['## '+o['case'], '', '**'+o['audit_status']+' / '+o['severity']+'**. VVAL: '+o['vval_recommendation']+'; VQ: '+o['vq_recommendation']+'.', '',o['conclusion'],'',o['materiality_admission'],'',
                  '| Dimensão efetiva | Juízo | Fundamento |','|---|---|---|'])
    for k,v in o['dimensions'].items():
        lines.append('|'+k+'|'+v['judgment']+(' (ressalva textual LIMITED)' if v.get('audit_qualifier') else '')+'|'+v['basis']+'|')
    lines.extend(['','Provas pró/contra (hash integral e recebido constam também no JSON):',''])
    for e in o['evidence']:
        lines.append('- '+e['polarity']+' — docid '+e['docid']+', grupo '+str(e['group'])+', páginas/unidades '+str(e['page_or_logical_units'])+', recebido '+e['received']+', SHA256 `'+e['original_sha256']+'`: '+e['finding'])
    lines.extend(['','Pendências específicas:','']+['- '+x for x in o['pending_specific']]+[''])
lines.extend(['## Recálculo independente','',
 '| Caso | Capitalização R$ | Mediana/límite R$ | P/L | Consequência |','|---|---:|---:|---:|---|',
 f'| Porto2025 | {p["market_cap"]:,.2f} | {central:,.2f} (âncora condicional2020) | {p["market_cap"]/central:.9f} | CAGR real por ação {cagr[0]*100:.6f}%–{cagr[1]*100:.6f}% cruza4% |',
 f'| Copasa2025 | {c["market_cap"]:,.2f} | >= {medianfloor:,.2f} | <= {c["market_cap"]/medianfloor:.9f} | Não certifica <=15; não prova reprovação |','',
 'Fatores IPCA2020–2024: '+str(pf)+'. Somente inflação conhecida até maio2025, publicação original de10/06/2025 conferida. Cotação COTAHIST somente de30/06/2025; preço/fator/data/ticker/hash recomputados dos registros brutos. Capital emitido extraído dos FRE recebidos23/05/2025 (Porto148229) e26/05/2025 (Copasa148260); capital autorizado não usado.', '',
 'A lógica da mediana usa -infinito para ano desconhecido e limites anuais comprovados. Não usa zero, não supõe o lucro reportado recorrente e não transforma limite superior acima15 em P/L efetivo. Deduções de todos os positivos e preservação de despesas/impostos produzem pisos conservadores. As divergências de perímetro/precisão da Copasa estão explicitadas no JSON.', '',
 'Declaração de independência: '+report['independence_declaration'], '',
 'Ledger integral de arquivos/hash e unidades/páginas efetivamente examinadas: material_review_2025.json. A verificação dos bytes de todos os originais não equivale à leitura econômica de todas as suas páginas.', ''])
md_receipt=create('material_review_2025.md','\n'.join(lines))
create('material_review_2025_receipt.json',{'sealed_utc':NOW,'files':[json_receipt,md_receipt]})

# Later factual transport adendum: never edit the sealed2014 bytes.
sealed_expected={'material_review_2014_sealed.json':'09b26d015e09965b3f2058da508d580598f2a159e6ce1590f670d1571f731c8f',
 'material_review_2014_sealed.md':'ed927627d059fb5c37a275fc61800495659269a62dc878f587cd14d795232483'}
seal_verified=[]
for name,expected in sealed_expected.items():
    found=sha(read(OUT/name,'Verify own initial2014 opinion remains byte-identical'))
    assert found==expected, (name,found)
    seal_verified.append({'path':str(OUT/name),'sha256':found})
adendum_start=len(ledger)
ad_quotes={}
ipca_doc=[]
for name in ['PSSA3_2014','BBDC4_2014','CSMG3_2014']:
    pack=PACK/name
    ad_quotes[name]=quote(pack)
    ipc=js(pack/'ipca_known.json','2014 addendum: primary IPCA availability facts only')
    meta=ipc['known_may_availability']
    raw=read(pack/meta['original'],'2014 addendum: original May2014 IBGE ZIP hash and PDF cover')
    assert sha(raw)==meta['sha256']
    z=zipfile.ZipFile(io.BytesIO(raw))
    pdfmember=next(x for x in z.namelist() if x.lower().endswith('.pdf'))
    pdf=z.read(pdfmember)
    pr=PdfReader(io.BytesIO(pdf))
    covers=[pr.pages[i].extract_text() for i in range(min(4,len(pr.pages)))]
    ipca_doc.append({'case':name,'zip_sha256':sha(raw),'pdf_member':pdfmember,'pdf_sha256':sha(pdf),
       'pdf_cover_read_pages':[1,2,3,4],'coverage':'May2014 cover independently readable with pypdf. Precise publication June6 is supplied contemporary receipt metadata; not printed as timestamp on cover.',
       'release_date':meta['release_date'],'publication_url_supplied_not_browsed':meta['release_url']})
adendum={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'type':'POST_SEAL_FACTUAL_TRANSPORT_ADDENDUM',
 'initial_2014_sealed_utc':'2026-10-09T13:14:10.616106+00:00',
 'initial_opinions_preserved':seal_verified,
 'scope':'COTAHIST2014 selection-day records arrived after initial seal. This dated addendum only verifies price/factor and original IPCA transport/readability; it does not revise2014 judgements or use2025 facts to judge2014.',
 'selection_quotes':ad_quotes,'ipca_primary_documents':ipca_doc,
 'financial_consequence':'Independent parsed closes match sealed inputs: PSSA3 31.86; BBDC3 ON32.24 plus BBDC4 PN32.05; CSMG3 40.50. Quotation factor1. Therefore original market capitalizations and arithmetic margins remain unchanged. Archived annualZIP may have later records; no annual COTAHIST archive was opened, only isolated cutoff records.',
 'v2_category_clarification':'Any SATISFACTORY_LIMITED wording in the sealed2014 opinion denotes SATISFACTORY with a textual documentary limitation; it is not an added V2 category, not a score, and not a protocol amendment. BBDC2014 VVAL remains INDETERMINATE_PENDING_IFRS_BRIDGE; other effective2014 findings unchanged.',
 'independence':'No future prices/returns/portfolio files, implementation, other audits/checkpoints or retrospectively sourced news were read. Original2014 byte-identical opinions preserved.',
 'sources_read_ledger':ledger[adendum_start:]}
aj=create('material_2014_quotes_and_ipca_addendum.json',adendum)
am=create('material_2014_quotes_and_ipca_addendum.md',
 '# Adendo factual posterior ao selo2014\n\nRegistro UTC: '+adendum['recorded_utc']+'.\n\n'+adendum['scope']+'\n\n'+adendum['financial_consequence']+'\n\n'+adendum['v2_category_clarification']+'\n\nOs hashes originais do parecer2014 foram conferidos e permanecem idênticos. A publicação exata do IPCA2014 (06/06/2014) está nos metadados contemporâneos entregues; a capa PDF original identifica maio2014, sem timestamp próprio. A cobertura primária e o ledger integral estão no JSON do adendo.\n')
create('material_2014_addendum_receipt.json',{'sealed_utc':adendum['recorded_utc'],'files':[aj,am]})
print(json.dumps({'2025_receipts':[json_receipt,md_receipt], '2014_addendum':[aj,am],
 'calculations':{'PSSA_PE':p['market_cap']/central,'PSSA_CAGR':cagr,'PSSA_ROE_floor':roe_lower,
 'CSMG_median_floor':medianfloor,'CSMG_PE_upper':c['market_cap']/medianfloor},'sealed2014_verified':seal_verified},ensure_ascii=False,indent=2))
