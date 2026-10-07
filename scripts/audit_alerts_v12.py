#!/usr/bin/env python3
"""Classify the frozen 45 alerts and measure separate, explicitly named scenarios.

No baseline, selection, engine or database writes. Requires the local nominal
price database; input evidence and frozen v11.2 are versioned independently.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))
from scripts import simulate_itsa_rights_v11_2 as rights

m = rights.m
BASE = Path('research/graham_v6_comparison/execution_v11_2_2026_10_07')
INPUT = Path('research/graham_v6_comparison/audit_v12_inputs')
OUT = Path('research/graham_v6_comparison/checkpoint_v12_2026_10_07')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rowsha(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def dump(out, name, rows):
    m.write_csv(out/name, rows, list(rows[0]) if rows else ['status'])


def context():
    events = [m.Event(**r) for r in json.loads((BASE/'manutencao_documental_v11_1/eventos_utilizados.json').read_text())]
    book, _, coverage = m.bridge.load_legacy()
    sels = m.selections_source.load_corrected()
    names = {t for s in sels.values() for t in s['R00']+s['R03']}
    names |= {e.asset for e in events} | {a for e in events for a, _ in e.legs} | {'BOVA11','BBSE3'}
    book = m.bridge.expand_with_sqlite(book, names)
    evidence = json.loads((BASE/'direitos_itsa_v11_2/manifesto_direitos.json').read_text())['rights_evidence']
    return book, events, coverage, sels, evidence


def cash_kind(event):
    if event.kind != 'CASH':
        return event.kind
    return 'JCP' if any(x in event.note.upper() for x in ('JCP', 'JUROS', 'INTEREST')) else 'DIV'


def amend(events, change):
    """An addition never reuses an ID; replacement requires an exact old ID."""
    result = list(events)
    if change['action'] == 'KEEP':
        return result
    e = m.Event(**change['event'])
    if change['action'] == 'ADD':
        if any(x.event_id == e.event_id for x in result):
            raise ValueError('Duplicate amendment')
        result.append(e)
    elif change['action'] == 'REPLACE':
        old = [x for x in result if x.event_id == change['old_id']]
        if len(old) != 1 or old[0].asset != e.asset or old[0].record_date != e.record_date:
            raise ValueError('Ambiguous or mismatched replacement')
        result = [e if x.event_id == change['old_id'] else x for x in result]
    else:
        raise ValueError(change['action'])
    return result


def classify(alert, number, events, book, facts, sources):
    t, com = alert['ticker'], alert['date_com']
    amount = float(alert['amount_or_multiplier'])
    ex = book.next_session(com)
    peers = [e for e in events if e.asset == t and e.kind == 'CASH' and e.record_date == com]
    normalized_kind = 'DIV' if alert['kind'] == 'CASH_DIVIDEND' else alert['kind']
    same = [e for e in peers if cash_kind(e) == normalized_kind]
    fact = next((f for f in facts if f['ticker'] == t and f['ex_date'] == ex
                 and f['kind'] == normalized_kind and math.isclose(f['amount'], amount, rel_tol=0, abs_tol=1e-11)), None)
    category, action, explanation = 'DIVERGENCIA_DOCUMENTAL', 'KEEP', 'Diferença nominal; falta aviso que resolva a versão. Preservar baseline.'
    evidence_id = {'ENAT3':'BRAVA_DIV','ITSA3':'ITSA_RI','PNVL3':'PNVL_RI','SLCE3':'SLCE_RI', 'TGMA3':'TGMA_RI'}.get(t,'')
    if t == 'CMIG3':
        assert len(peers) == 1 and math.isclose(peers[0].amount, 2*amount, abs_tol=1e-9)
        category, explanation = 'MESMO_EVENTO_AGREGADO', 'B3 contém uma metade; legado contém as duas parcelas brutas. Não somar novamente.'
        evidence_id = {'2024-09-23':'CMIG_SET24','2024-12-23':'CMIG_DEZ24','2025-04-30':'CMIG_AGO25_FINAL',
                       '2026-03-24':'CMIG_MAR26','2026-06-23':'CMIG_JUN26'}.get(com,'CMIG_AGO26')
    elif t == 'CPLE3' and com == '2024-12-11':
        assert len(same) == 2 and math.isclose(sum(e.amount for e in same), amount, abs_tol=1e-10)
        category, explanation, evidence_id = 'MESMO_EVENTO_AGREGADO', 'B3 soma duas parcelas JCP já separadas no legado.', 'CPLE_RI'
    elif fact:
        evidence_id = fact['source_id']
        if same:
            assert t == 'CPLE3' and len(same) == 1
            category, action, explanation = 'DIVERGENCIA_DOCUMENTAL', 'REPLACE', 'Aviso retificador altera valor por ação por tesouraria; substituir parcela, sem adicionar total.'
        else:
            category, action, explanation = 'TRANCHE_ADICIONAL_CONFIRMADA', 'ADD', 'JCP bruto distinto do dividendo da mesma data; confirmação no documento do emissor.'
    elif t in ('TGMA3','DXCO3'):
        explanation = 'JCP difere do DIV existente; sem exposição no evento. Não inserir sem concluir documento individual.'
    if t == 'PNVL3':
        explanation = 'RI atual mantém 4 parcelas e confirma 0,075125511; B3 0,075087737 pode ser versão anterior. Sem conciliação do aviso original, manter RI/legado e registrar diferença.'
    if t == 'ITSA3':
        explanation = '0,015456 versus 0,01546: diferença compatível com arredondamento, sem prova de parcela adicional.'
    src = sources.get(evidence_id, {})
    source_url = fact['source_url'] if fact else src.get('url','')
    pay = fact.get('pay_date','') if fact else '; '.join(e.note for e in peers)
    event = m.Event(f'V12_ALERT_{number:02d}', ex, 'CASH', t, source_url or 'B3_LOCAL_UNRESOLVED',
                    record_date=com, amount=amount, note=f"{alert['kind']}; bruto; pagamento={pay}; audit alert {number}")
    change = dict(action=action, event=asdict(event), old_id=same[0].event_id if action=='REPLACE' else '')
    row = dict(alert_id=f'A{number:02d}', **alert, share_class='ON', date_ex=ex, pay_date_or_legacy_note=pay,
               date_ex_evidence='RI_CONFRONTADO' if fact else 'CALENDARIO_B3_A_PARTIR_DA_DATA_COM_LOCAL; ver nota/documento',
               amount_basis_evidence='BRUTO_CONFIRMADO_RI' if fact or t=='CMIG3' else 'BRUTO_CONVENCAO_LEGADA; confrontacao documental parcial',
               economic_category=category, classification=category, decision=action,
               nominal_b3=amount, legacy_total=sum(e.amount for e in peers),
               same_kind_total=sum(e.amount for e in same), gross_net='BRUTO; sem conversao automatica por 0,85',
               ratio_b3_to_same_kind=amount/sum(e.amount for e in same) if same else '',
               legacy_event_ids=';'.join(e.event_id for e in peers),
               legacy_event_sources=';'.join(sorted({e.source for e in peers})),
               legacy_events_sha256=rowsha([asdict(e) for e in peers]),
               b3_alert_row_sha256=rowsha(alert), source_id=evidence_id, source_url=source_url,
               source_sha256=fact['source_sha256'] if fact else src.get('sha256',''),
               documentary_status='CONFIRMADO_EM_FONTE_PRIMARIA' if fact or (t=='CMIG3' and src.get('sha256')) else 'CONCILIACAO_PARCIAL',
               explanation=explanation, maintenance_exposure='', renewal_exposure='',
               max_individual_asset_delta_pp=0.0, max_accepted_portfolio_delta_abs_pp=0.0,
               max_named_stress_abs_pp=0.0,
               stress_definition='')
    return row, change, peers, same


class Runner:
    def __init__(self, book, coverage, sels, evidence):
        self.book, self.coverage, self.sels, self.evidence = book, coverage, sels, evidence

    def run(self, events, year, rule, mechanism):
        capital, states = rights.CAPITAL, []
        periods = [year] if mechanism == 'maintain' else range(year, 2026)
        for p in periods:
            a, b = m.bridge.WINDOWS[p]
            if mechanism == 'maintain': b = m.END
            weights = rights.weights_for(self.sels[p], rule)
            state, result, _ = rights.simulate(self.book, events, self.coverage, a, b, weights, capital, self.evidence)
            states.append((p, weights, state))
            capital = result['final_value']
        return capital/rights.CAPITAL-1, states

    def exposure(self, states, ticker, com):
        answer = []
        for p, weights, state in states:
            if state.start <= com < state.last_date:
                date = max((d for d in state.snapshots if d <= com), default='')
                q = state.snapshots.get(date, {}).get(ticker, 0)
                if q > 0:
                    answer.append((p, q, weights.get(ticker, 0)))
        return answer


def main(out):
    if out.exists(): raise FileExistsError(out)
    out.mkdir(parents=True)
    book, events, coverage, sels, evidence = context()
    facts = json.loads((INPUT/'verified_facts.json').read_text())
    sources = {r['id']:r for r in json.loads((INPUT/'sources_manifest.json').read_text())}
    legacy_catalog = json.loads((INPUT/'legacy_source_catalog.json').read_text())
    b3_records = {r['alert_id']:r for r in json.loads((INPUT/'b3_alert_records.json').read_text())}
    alerts = m.read_csv(BASE/'manutencao_documental_v11_1/alertas_documentais.csv')
    assert len(alerts) == 45
    runner = Runner(book, coverage, sels, evidence)
    frozen = {(int(r['start_year']),r['rule']):r for r in m.read_csv(BASE/'direitos_itsa_v11_2/graham_18_coortes.csv')}
    baseline, states, regressions = {}, {}, []
    for y in m.bridge.WINDOWS:
        for rule in rights.RULES:
            for mode in ('maintain','renew'):
                key = y, rule, mode
                baseline[key], states[key] = runner.run(events, *key)
                target = float(frozen[(y,rule)][mode+'_return'])
                assert math.isclose(baseline[key], target, abs_tol=1e-9)
                regressions.append(dict(start_year=y,rule=rule,mechanism=mode,calculated=baseline[key],v11_2=target,status='OK'))
    matrix, impacts, changes, scenario_impacts = [], [], [], []
    for n, alert in enumerate(alerts, 1):
        row, change, peers, same = classify(alert,n,events,book,facts,sources)
        record = b3_records[row['alert_id']]
        row['b3_isin'] = record['raw_sqlite_row']['isin_code']
        row['b3_sqlite_row_sha256'] = record['row_sha256']
        row['b3_provenance'] = record['provenance']
        row['legacy_source_urls'] = ';'.join(sorted({legacy_catalog[s]['url'] for e in peers
              for s in e.source.split(';') if s in legacy_catalog}))
        if not row['source_url']:
            row['source_url'] = row['legacy_source_urls'] or 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/'
        if row['alert_id']=='A04':
            row['explanation'] += ' Residuo de arredondamento do total legado: -0,00000000080 por acao; preservado.'
        exposures = {k:runner.exposure(s,alert['ticker'],alert['date_com']) for k,s in states.items()}
        any_exposure = any(exposures.values())
        if not any_exposure:
            row['classification'], row['decision'] = 'SEM_EXPOSICAO_ECONOMICA', 'KEEP'
            change['action'] = 'KEEP'
        else:
            for mode in ('maintain','renew'):
                row[('maintenance' if mode=='maintain' else 'renewal')+'_exposure'] = ';'.join(
                    f'{y}/{r}:ano{p}' for (y,r,md),x in exposures.items() if md==mode for p,_,_ in x)
        accepted = amend(events,change)
        if change['action'] != 'KEEP': changes.append(dict(alert_id=row['alert_id'],**change))
        stresses = []
        if any_exposure and row['economic_category']=='DIVERGENCIA_DOCUMENTAL' and change['action']=='KEEP':
            # Unknown nominal revision: finite named alternatives, never an upper
            # bound on unknown omitted events or proof that either alternative exists.
            if same:
                closest=min(same,key=lambda e:abs(e.amount-row['nominal_b3']))
                stresses.append(('SUBSTITUIR_PARCELA_MAIS_PROXIMA_POR_B3',dict(action='REPLACE',event=change['event'],old_id=closest.event_id)))
            stresses.append(('ADICIONAR_B3_INTEGRAL_HIPOTESE_NAO_COMPROVADA',dict(action='ADD',event=change['event'])))
        row['stress_definition']=';'.join(s[0] for s in stresses) or 'APENAS_TRATAMENTO_DOCUMENTADO; maximo de lacunas desconhecidas NAO_LIMITADO'
        for key, base in baseline.items():
            y,rule,mode=key
            exposure=exposures[key]
            after=runner.run(accepted,*key)[0] if exposure and change['action']!='KEEP' else base
            values=[after-base]
            for name, stress in stresses:
                alt=runner.run(amend(events,stress),*key)[0] if exposure else base
                values.append(alt-base)
                scenario_impacts.append(dict(alert_id=row['alert_id'],start_year=y,rule=rule,mechanism=mode,
                                             scenario=name,delta_pp=100*(alt-base),applied_to_baseline=False))
            asset_delta=0.0
            for p,q,w in exposure:
                a,b=m.bridge.WINDOWS[p]
                if mode=='maintain':b=m.END
                capital=rights.CAPITAL*w
                _,old,_=rights.simulate(book,events,coverage,a,b,{alert['ticker']:1.0},capital,evidence)
                _,new,_=rights.simulate(book,accepted,coverage,a,b,{alert['ticker']:1.0},capital,evidence)
                asset_delta=max(asset_delta,abs(100*(new['return']-old['return'])))
            impact=dict(alert_id=row['alert_id'],ticker=alert['ticker'],date_com=alert['date_com'],
                        start_year=y,rule=rule,mechanism=mode,exposure=bool(exposure),
                        exposed_periods=';'.join(str(p) for p,_,_ in exposure),
                        entitled_quantity=';'.join(str(q) for _,q,_ in exposure),
                        baseline_return=base,accepted_return=after,accepted_delta_pp=100*(after-base),
                        individual_abs_delta_pp=asset_delta,scenario_min_delta_pp=100*min(values+[0]),
                        scenario_max_delta_pp=100*max(values+[0]),scenario_max_abs_pp=100*max(map(abs,values)),
                        max_unknown_events='NAO_LIMITADO',decision=row['decision'])
            impacts.append(impact)
            row['max_individual_asset_delta_pp']=max(row['max_individual_asset_delta_pp'],asset_delta)
            row['max_accepted_portfolio_delta_abs_pp']=max(row['max_accepted_portfolio_delta_abs_pp'],abs(impact['accepted_delta_pp']))
            row['max_named_stress_abs_pp']=max(row['max_named_stress_abs_pp'],impact['scenario_max_abs_pp'])
        matrix.append(row)
        print(row['alert_id'],row['ticker'],row['classification'],row['decision'],flush=True)
    candidate=events
    for c in changes:candidate=amend(candidate,c)
    joint=[]
    for key,base in baseline.items():
        after,_=runner.run(candidate,*key)
        y,rule,mode=key
        joint.append(dict(start_year=y,rule=rule,mechanism=mode,baseline_v11_2=base,
                          candidate_v12=after,delta_pp=100*(after-base),
                          sum_isolated_deltas_pp=sum(r['accepted_delta_pp'] for r in impacts if (r['start_year'],r['rule'],r['mechanism'])==key),
                          status='CENARIO_DOCUMENTAL_SEPARADO_BASELINE_V11_2_PRESERVADA'))
    # Rankings against unchanged central v9; ties retain deterministic name order.
    comparison=m.read_csv(BASE/'direitos_itsa_v11_2/comparacao_72_cenarios.csv')
    ranks=[]
    for y in m.bridge.WINDOWS:
        for mode in ('maintain','renew'):
            fixed={r['strategy']:float(r[mode]) for r in comparison if int(r['start_year'])==y and r['family']!='Graham' and (r['family']!='BESST' or r['scenario']=='central')}
            old=dict(fixed,**{r:baseline[(y,r,mode)] for r in rights.RULES})
            new=dict(fixed,**{r['rule']:r['candidate_v12'] for r in joint if r['start_year']==y and r['mechanism']==mode})
            for s in old:
                before=sorted(old,key=lambda k:(-old[k],k)).index(s)+1
                after=sorted(new,key=lambda k:(-new[k],k)).index(s)+1
                ranks.append(dict(start_year=y,mechanism=mode,strategy=s,before=before,after=after,changed=before!=after))
            for impact in impacts:
                if impact['start_year']==y and impact['mechanism']==mode:
                    single=dict(old);single[impact['rule']]=impact['accepted_return']
                    impact['rank_before']=sorted(old,key=lambda k:(-old[k],k)).index(impact['rule'])+1
                    impact['rank_after_isolated']=sorted(single,key=lambda k:(-single[k],k)).index(impact['rule'])+1
            for stress in scenario_impacts:
                if stress['start_year']==y and stress['mechanism']==mode:
                    single=dict(old)
                    single[stress['rule']]+=stress['delta_pp']/100
                    stress['rank_before']=sorted(old,key=lambda k:(-old[k],k)).index(stress['rule'])+1
                    stress['rank_after_stress']=sorted(single,key=lambda k:(-single[k],k)).index(stress['rule'])+1
                    stress['rank_changed']=stress['rank_before']!=stress['rank_after_stress']
    dump(out,'matriz_45_alertas_classificados.csv',matrix)
    dump(out,'impacto_alertas_por_carteira.csv',impacts)
    dump(out,'sensibilidades_alertas_nao_aplicadas.csv',scenario_impacts)
    dump(out,'impacto_conjunto_36_carteiras.csv',joint)
    dump(out,'ranking_alertas_96.csv',ranks)
    dump(out,'regressao_v11_2_36.csv',regressions)
    (out/'alteracoes_documentais.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False)+'\n')
    (out/'eventos_cenario_v12.json').write_text(json.dumps([asdict(e) for e in candidate],indent=2,ensure_ascii=False)+'\n')
    summary=dict(baseline='v11.2 provisoria, imutavel',classification_counts=dict(Counter(r['classification'] for r in matrix)),
                 alerts=len(matrix),added=sum(c['action']=='ADD' for c in changes),replaced=sum(c['action']=='REPLACE' for c in changes),
                 rank_changes=sum(r['changed'] for r in ranks),regressions=len(regressions),engine_sha256=sha('graham_v6_event_bridge/motor_eventos.py'),
                 facts_sha256=sha(INPUT/'verified_facts.json'),scenario_not_certified=True,
                 unknown_events_maximum='NAO_LIMITADO; extremos reportados sao apenas dos cenarios explicitamente executados')
    (out/'resumo_alertas.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT)
    main(p.parse_args().out)
