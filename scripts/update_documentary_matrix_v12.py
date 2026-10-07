#!/usr/bin/env python3
"""Update all twelve asset/year records without certifying undocumented absences."""
import argparse
from datetime import datetime
import gzip
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from bs4 import BeautifulSoup
from scripts.audit_alerts_v12 import BASE,INPUT,OUT,context,dump,sha,m,rights,cash_kind,Runner


def dt(value):
    return datetime.strptime(value[:10],'%d/%m/%Y').date().isoformat()


def main(out):
    book,events,coverage,sels,evidence=context()
    sources={r['id']:r for r in json.loads((INPUT/'sources_manifest.json').read_text())}
    known=[]
    # Parse the independently downloaded original HTML; duplicates between fiscal
    # year tables are one entitlement, retaining an explicit evidence key.
    html=gzip.decompress(Path(sources['ITSA_RI']['stored_gzip']).read_bytes()).decode()
    seen=set()
    for table in BeautifulSoup(html,'html.parser').select('table'):
        for tr in table.select('tr'):
            c=[x.get_text(' ',strip=True) for x in tr.select('td')]
            if len(c)<6 or not (c[0].startswith('JCP') or c[0].startswith('Dividendos')):continue
            com,pay=dt(c[2]),dt(c[3]);amount=float(c[4].replace(',','.'))
            kind='JCP' if c[0].startswith('JCP') else 'DIV'
            k=com,pay,kind,amount
            if k in seen:continue
            seen.add(k)
            if '2022-06-30'<=com<'2026-06-30':
                known.append(dict(ticker='ITSA3',record_date=com,ex_date=book.next_session(com),pay_date=pay,
                                  kind=kind,amount=amount,source_id='ITSA_RI',provenance='HTML_ORIGINAL_COLETADO'))
    for r in m.read_csv(Path('research/graham_v6_comparison/ri_events_verified_2026_10_07.csv')):
        if r['ticker']=='UNIP3':
            known.append(dict(ticker='UNIP3',record_date=r['date'],ex_date=book.next_session(r['date']),
                              pay_date=r['payment_date'],kind='DIV',amount=float(r['amount']),source_id='UNIP_RI',
                              provenance='TRANSCRICAO_WEB_V11; download original ainda 403'))
    specifics=[
        ('CSAN3','2023-05-18','2023-05-31','DIV',.42857979,'CSAN_AVISO23'),
        ('SBSP3','2025-12-23','2026-04-30','JCP',2.643892990,'SBSP_JCP25_FINAL'),
        ('SBSP3','2026-03-19','2026-04-30','JCP',.83342453884,'SBSP_JCP26_FINAL'),
        ('TGMA3','2025-08-07','2025-08-19','DIV',1.21,'TGMA_AGO25'),
        ('TGMA3','2025-08-07','2025-08-19','JCP',.14,'TGMA_AGO25'),
        ('TGMA3','2025-11-06','2025-11-18','DIV',.79,'TGMA_NOV25'),
        ('TGMA3','2025-11-06','2025-11-18','JCP',.18,'TGMA_NOV25'),
        ('TGMA3','2025-12-02','2025-12-29','DIV',1.52,'TGMA_DEZ25'),
        ('ALOS3','2025-11-18','2025-12-02','DIV',.102167180,'ALOS_AVISO25'),
        ('ALOS3','2025-11-18','2025-12-02','DIV',.192314691,'ALOS_AVISO25'),
    ]
    for t,com,pay,kind,amount,src in specifics:
        known.append(dict(ticker=t,record_date=com,ex_date=book.next_session(com),pay_date=pay,kind=kind,
                          amount=amount,source_id=src,provenance='AVISO_EMISSOR_COLETADO' if src!='ALOS_AVISO25' else 'AVISO_EMISSOR_COPIA_HOSPEDADA_TERCEIRO'))
    comparisons=[]
    for f in known:
        src=sources[f['source_id']]
        matches=[e for e in events if e.asset==f['ticker'] and e.record_date==f['record_date'] and
                 e.kind=='CASH' and cash_kind(e)==f['kind'] and math.isclose(e.amount,f['amount'],rel_tol=0,abs_tol=5e-7)]
        # Preserve documented cash types and exact dates. The small tolerance only
        # accommodates display precision; never marks structural completeness.
        comparisons.append(dict(**f,source_url=src['url'],source_sha256=src.get('sha256',''),
                                status='PRESENTE_NO_BASELINE' if len(matches)==1 else 'REVISAR',
                                matching_ids=';'.join(e.event_id for e in matches),
                                amount_delta=matches[0].amount-f['amount'] if len(matches)==1 else ''))
    dump(out,'fatos_12_confrontados.csv',comparisons)
    prior=m.read_csv(BASE/'auditoria_fontes_v11/matriz_12_ativo_ano.csv')
    matched={r['matching_ids'] for r in comparisons if r['status']=='PRESENTE_NO_BASELINE'}
    notes={
        'ITSA3':('HTML original coletado; caixa bruto por com/ex/pagamento e bonificacoes conferidos; direitos v11.2 reutilizados sem nova rodada.',
                 'Nenhuma ausencia global inferida; direitos 2023/2025 ja simulados conforme politica aprovada.',
                 'Completar catalogo independente de eventos societarios por janela; nao confundir direitos liquidados com dividendos na ex.'),
        'UNIP3':('Transcricao factual e parcelas distintas v11.1 preservadas; acesso direto continua HTTP 403.',
                 'Sem ausencia global documentada.', 'Coletar avisos originais e catalogo estrutural; transcricao e hash de CSV nao substituem original.'),
        'SBSP3':('Dois JCP confirmados nos avisos finais: 2,643892990 e 0,83342453884; valores brutos anteriores ao split, pagamentos 30/04/2026.',
                 'Nao multiplicar novamente JCP pelo split; ausencia de outras distribuicoes requer catalogo.',
                 'Fechar catalogo integral; preservar duas bonificacoes e split 1:5 ja corroborados na v11; nao usar versoes anteriores dos JCP.'),
        'TGMA3':('Cinco proventos confirmados em tres avisos originais. Tabela dev de RI diverge em valores/datas; avisos prevalecem.',
                 'RCA 27/11/2025: aumento de capital SEM emissao de acoes. Release 2T26: sem JCP abril/2026, alcance limitado a esse tipo/mes.',
                 'Completar catalogo ate junho/2026; ausencia de JCP em abril nao prova ausencia de dividendos nem eventos societarios.'),
        'CSAN3':('Aviso original 27/04/2023 confirma 0,42857979; com 18/05, ex 19/05 e pagamento 31/05/2023; supera tabela arredondada 0,43.',
                 'Nenhuma ausencia estrutural global documentada.', 'Fechar catalogo completo de estrutura e demais eventos da janela.'),
        'SYNE3':('HTML original coletado; tabela nao lista distribuicao entre 30/06/2022 e 30/06/2023; restituições posteriores permanecem na manutencao v11.2.',
                 'Ausencia apenas na tabela de dividendos consultada, nao em catalogo independente de todos os eventos.',
                 'Revisar documentos societarios e cobertura integral; nao promover ausencia de linha a ausencia de evento.'),
        'ALOS3':('Duas parcelas de novembro/2025 confirmadas em copia de aviso do emissor; soma 0,294481871. Parcela janeiro/2025 continua corroboracao B3 secundaria.',
                 'Nenhuma ausencia global documentada.', 'Confrontar todos os avisos e revisoes por tesouraria, sobretudo janeiro/2025. RI direto HTTP 403.'),
    }
    ids={'ITSA3':['ITSA_RI'],'UNIP3':['UNIP_RI'],'SBSP3':['SBSP_JCP25_FINAL','SBSP_JCP26_FINAL'],
         'TGMA3':['TGMA_AGO25','TGMA_NOV25','TGMA_DEZ25','TGMA_CAPITAL25','TGMA_AUSENCIA26'],
         'CSAN3':['CSAN_AVISO23'],'SYNE3':['SYNE_RI'],'ALOS3':['ALOS_RI','ALOS_AVISO25']}
    matrix,stress=[] ,[]
    for old in prior:
        t,y=old['ticker'],int(old['year']);a,b=m.bridge.WINDOWS[y]
        in_window=[r for r in comparisons if r['ticker']==t and a<r['ex_date']<=b]
        cash=[e for e in events if e.asset==t and e.kind=='CASH' and a<e.date<=b]
        structural=[dict(event_id=e.event_id,kind=e.kind,date_ex=e.date,factor=e.factor,source=e.source,note=e.note)
                    for e in events if e.asset==t and e.kind!='CASH' and a<e.date<=b]
        rights_ids=[r['event_id'] for r in evidence if r['parent']==t and a<r['ex_date']<=b]
        unmatched=[e for e in cash if e.event_id not in matched]
        # A transparent stress of KNOWN but uncorroborated cash only. It is neither
        # a likely error nor an upper bound for undiscovered/structural events.
        omitted=[e for e in events if e not in unmatched]
        maxstress=0.0
        for rule in rights.RULES:
            w=rights.weights_for(sels[y],rule)
            if t not in w:continue
            for mode,end in [('annual',b),('maintain',m.END)]:
                _,r0,_=rights.simulate(book,events,coverage,a,end,{t:1.0},10000*w[t],evidence)
                _,r1,_=rights.simulate(book,omitted,coverage,a,end,{t:1.0},10000*w[t],evidence)
                delta=100*w[t]*(r1['return']-r0['return']);maxstress=max(maxstress,abs(delta))
                stress.append(dict(ticker=t,year=y,rule=rule,mechanism=mode,weight=w[t],scenario='REMOVER_SOMENTE_CAIXA_CONHECIDO_SEM_CORROBORACAO_NESTA_MATRIZ',
                                   removed_event_ids=';'.join(e.event_id for e in unmatched),portfolio_delta_pp=delta,applied=False,
                                   warning='NAO e limite do risco de eventos desconhecidos; manutencao propaga apenas caixa desta janela ate 2026'))
        sources_used=ids[t]
        factual_note,absence_note,gap_note=notes[t]
        status='PARCIAL_AVANCO_DOCUMENTAL' if t!='UNIP3' else 'PARCIAL_DOCUMENTO_ORIGINAL_PENDENTE'
        if t=='ALOS3' and y==2024:
            sources_used=['ALOS_RI']
            factual_note='Onze eventos preservados; janeiro/2025 contem duas parcelas. Aviso nominal original e demais revisoes ainda pendentes; coleta direta RI HTTP 403.'
            status='PARCIAL_DOCUMENTO_ORIGINAL_PENDENTE'
        matrix.append(dict(ticker=t,year=y,start=a,end=b,quotes_checked_local_cotahist=old['quotes_checked'],
                           original_quotes_independently_downloaded=False,known_cash_events=len(cash),cash_facts_checked=len(in_window),
                           facts_matching=sum(r['status']=='PRESENTE_NO_BASELINE' for r in in_window),
                           structural_events=json.dumps(structural,ensure_ascii=False,sort_keys=True),
                           structural_status='EVENTOS_HERDADOS_CORROBORADOS_V11; catalogo integral pendente' if structural else 'NENHUM_LANCAMENTO_LOCAL; nao comprova ausencia',
                           rights_already_documented_v11_2=';'.join(rights_ids),
                           unmatched_known_cash=len(unmatched),new_facts=factual_note,documented_absence_and_scope=absence_note,
                           source_gap=gap_note,source_ids=';'.join(sources_used),source_urls=';'.join(sources[i]['url'] for i in sources_used),
                           original_sha256s=';'.join(sources[i].get('sha256','SEM_ORIGINAL') for i in sources_used),
                           documented_correction_vs_v11_2_pp=0.0,
                           max_abs_known_cash_stress_pp=maxstress,max_impact_unknown_events='NAO_LIMITADO_DOCUMENTALMENTE',
                           status=status,fully_certified=False))
    assert len(matrix)==12
    dump(out,'matriz_12_ativo_ano_atualizada.csv',matrix)
    dump(out,'sensibilidade_12_caixa_nao_corroborado.csv',stress)
    (out/'resumo_matriz_12.json').write_text(json.dumps(dict(rows=12,fully_certified=0,
        facts_checked=len(comparisons),facts_matching=sum(r['status']=='PRESENTE_NO_BASELINE' for r in comparisons),
        rows_with_new_original_or_issuer_copy_evidence=9, # ITSA x4, SBSP, TGMA, CSAN, SYNE, ALOS2025
        unchanged_baseline=True,unknown_event_risk_bound=None),indent=2)+'\n')
    print('Matrix',len(matrix),'facts',len(comparisons),'review',sum(r['status']!='PRESENTE_NO_BASELINE' for r in comparisons))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);main(p.parse_args().out)
