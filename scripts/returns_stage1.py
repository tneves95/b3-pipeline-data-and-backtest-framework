#!/usr/bin/env python3
"""Percentage-only checkpoint; never bridge a missing selection or return with zero."""
import csv
import hashlib
import json
import math
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "research/returns_2014_2026_inputs"
OUTPUT = ROOT / "research/returns_2014_2026_results"
LEGACY = ROOT / "research/graham_v6_comparison"
NAMES = ("R03 B2", "B00S B2", "B00S BH+entradas", "BH padrão", "IBOV")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def validate_return(value):
    if value is not None and (not math.isfinite(value) or value < -1):
        raise ValueError("Return must be finite and at least -100%, or explicitly missing")


def chain(returns):
    """Decimals in/out. Unknown intervals invalidate all later accumulation."""
    factor = 1.0
    result = []
    for r in returns:
        validate_return(r)
        factor = None if factor is None or r is None else factor * (1 + r)
        result.append(None if factor is None else factor - 1)
    return result


def june_close(payload, year):
    observations = []
    for row in payload["results"]:
        value = row.get("rateValue6")
        if value is None or value == "":
            continue
        day = date(year, 6, int(row["day"]))
        level = float(str(value).replace(".", "").replace(",", "."))
        if not math.isfinite(level) or level <= 0:
            raise ValueError("Invalid official IBOV level")
        observations.append((day.isoformat(), level))
    if not observations or len({d for d, _ in observations}) != len(observations):
        raise ValueError("Empty or duplicate June observations")
    return max(observations)


def summary(returns, benchmark, start, end, is_benchmark=False):
    if len(returns) != 12 or len(benchmark) != 12:
        raise ValueError("The study requires exactly 12 intervals")
    for r in returns + benchmark:
        validate_return(r)
    result = dict(observed_intervals=sum(r is not None for r in returns), required_intervals=12,
                  total_return_pct=None, cagr_pct=None, above_ibov_years=None,
                  positive_years=None, negative_years=None, flat_years=None,
                  mean_annual_pct=None, median_annual_pct=None, best_period=None,
                  best_return_pct=None, worst_period=None, worst_return_pct=None,
                  mean_rank=None, consistency_rank=None, final_rank=None)
    if any(r is None for r in returns) or any(r is None for r in benchmark):
        return result
    total = chain(returns)[-1]
    years = (date.fromisoformat(end) - date.fromisoformat(start)).days / 365.25
    best, worst = max(range(12), key=returns.__getitem__), min(range(12), key=returns.__getitem__)
    result.update(total_return_pct=100*total, cagr_pct=100*((1+total)**(1/years)-1),
                  above_ibov_years=None if is_benchmark else sum(r > b for r, b in zip(returns, benchmark)),
                  positive_years=sum(r > 0 for r in returns), negative_years=sum(r < 0 for r in returns),
                  flat_years=sum(r == 0 for r in returns), mean_annual_pct=100*statistics.mean(returns),
                  median_annual_pct=100*statistics.median(returns),
                  best_period=f"{2014+best}–{2015+best}", best_return_pct=100*returns[best],
                  worst_period=f"{2014+worst}–{2015+worst}", worst_return_pct=100*returns[worst])
    return result


def pct(value):
    return "ND" if value is None else f"{value:.4f}".replace(".", ",")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|"*len(headers)] +
                      ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sources = json.loads((INPUT / "b3/sources.json").read_text())
    closes = []
    for source in sources:
        path = INPUT / "b3" / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        day, level = june_close(json.loads(path.read_text()), source["year"])
        closes.append(dict(year=source["year"], date=day, ibov_points=level, source=source["url"], sha256=source["sha256"]))
    closes.sort(key=lambda r: r["year"])
    assert [r["year"] for r in closes] == list(range(2014, 2027))
    assert closes[-1]["date"] == "2026-06-30"
    write(OUTPUT / "ibov_june_closes.csv", closes)
    benchmark = [b["ibov_points"]/a["ibov_points"]-1 for a, b in zip(closes, closes[1:])]
    series = {name: [None]*12 for name in NAMES[:-1]} | {"IBOV": benchmark}
    cumulative = {name: chain(values) for name, values in series.items()}
    annual, accumulated, excess, statuses = [], [], [], []
    reasons = {
        "R03 B2": "Selecao PIT 2014–2019 nao estabelecida; elegibilidade anual posterior nao revalidada nesta missao",
        "B00S B2": "Universo BESST PIT e recorrencia de distribuicoes 2009–2019 nao reconstruidos; legado 2020–2025 parcial",
        "B00S BH+entradas": "Selecao inicial 2014 e uniao historica de elegiveis/sucessoras nao estabelecidas",
        "BH padrão": "Ranking completo de capitalizacao por companhia/classe e setor em 2014 nao estabelecido",
    }
    for i in range(12):
        base = dict(period=f"{2014+i}–{2015+i}", start=closes[i]["date"], end=closes[i+1]["date"])
        annual.append(base | {n: None if series[n][i] is None else 100*series[n][i] for n in NAMES})
        accumulated.append(base | {n: None if cumulative[n][i] is None else 100*cumulative[n][i] for n in NAMES})
        ex = base | {"IBOV_pct": benchmark[i]*100}
        for n in NAMES[:-1]:
            ex[n+"_minus_IBOV_pp"] = None if series[n][i] is None else 100*(series[n][i]-benchmark[i])
            statuses.append(base | dict(portfolio=n, status="NOT_COMPUTABLE_FROM_ESTABLISHED_SELECTION", reason=reasons[n]))
        excess.append(ex)
    write(OUTPUT / "annual_returns_pct.csv", annual)
    write(OUTPUT / "cumulative_returns_pct.csv", accumulated)
    write(OUTPUT / "annual_excess_pp.csv", excess)
    write(OUTPUT / "portfolio_status.csv", statuses)
    stats = [dict(portfolio=n) | summary(series[n], benchmark, closes[0]["date"], closes[-1]["date"], n=="IBOV") for n in NAMES]
    # Rankings require all five comparable trajectories; IBOV alone is not a winner.
    write(OUTPUT / "consolidated_pct.csv", stats)

    # Recompute percentage comparisons for inherited windows; not a new starting cohort.
    graham_path = LEGACY / "execution_v11_2_2026_10_07/direitos_itsa_v11_2/anuais_capital_10000.csv"
    barsi_path = LEGACY / "checkpoint_v13_2026_10_07/comparacao_anuais_manutencao_v13.csv"
    gr = {int(r["year"]): r for r in read(graham_path)}
    br = {int(r["year"]): r for r in read(barsi_path) if r["strategy"] == "B00S" and r["scenario"] == "central"
          and r["mechanism"] == "annual" and r["experiment"] == "v12_plus_v13"}
    assert set(gr) == set(br) == set(range(2020, 2026))
    segments = []
    for y in range(2020, 2026):
        i = y - 2014
        assert gr[y]["start"] == closes[i]["date"] and gr[y]["end"] == closes[i+1]["date"]
        g, b = float(gr[y]["R03"]), float(br[y]["central_return"])
        segments.append(dict(period=f"{y}–{y+1}", start=closes[i]["date"], end=closes[i+1]["date"],
            R03_inherited_pct=100*g, B00S_inherited_pct=100*b, IBOV_pct=100*benchmark[i],
            R03_minus_IBOV_pp=100*(g-benchmark[i]), B00S_minus_IBOV_pp=100*(b-benchmark[i]),
            status="CONDITIONAL_LEGACY_REFERENCE_NOT_VALIDATED_STAGE1",
            R03_source=str(graham_path.relative_to(ROOT)), B00S_source=str(barsi_path.relative_to(ROOT))))
    write(OUTPUT / "conditional_legacy_segments_pct.csv", segments)

    # Existing selections, with known years explicitly scoped and previous history unknown.
    weights = [r for r in read(LEGACY / "execution_v11_2_2026_10_07/carteiras_selecionadas_768_posicoes.csv")
               if (r["strategy"], r["scenario"]) in [("R03", "corrigido"), ("B00S", "central")]]
    write(OUTPUT / "conditional_legacy_weights.csv", weights)
    changes = []
    for strategy in ("R03", "B00S"):
        previous = None
        for y in range(2020,2026):
            current = {r["ticker"] for r in weights if r["strategy"] == strategy and int(r["year"]) == y}
            assert math.isclose(sum(float(r["weight"]) for r in weights if r["strategy"] == strategy and int(r["year"]) == y), 1, abs_tol=1e-12)
            changes.append(dict(year=y, strategy=strategy, members=";".join(sorted(current)),
                additions=None if previous is None else ";".join(sorted(current-previous)),
                removals=None if previous is None else ";".join(sorted(previous-current)),
                status="PREVIOUS_SELECTION_UNKNOWN" if previous is None else "LEGACY_TICKER_DIFF_REQUIRES_ISSUER_CONTINUITY"))
            previous = current
    write(OUTPUT / "conditional_legacy_membership_changes.csv", changes)

    coverage = json.loads((INPUT / "coverage/manifest.json").read_text())
    cover2014 = read(INPUT / "coverage/annual_coverage.csv")[0]
    total = stats[-1]
    report = ["# Checkpoint — etapa 1 percentual, 2014–2026 — 08/10/2026", "",
        "**Entrega parcial: a comparação completa das quatro carteiras ainda não foi calculada.** "
        "A série oficial do IBOV foi calculada nas 12 janelas; seleções históricas insuficientemente estabelecidas impedem "
        "atribuir retornos às quatro trajetórias desde 2014. ND significa não determinado, nunca retorno zero. "
        "Não há vencedor nem ranking de consistência das quatro carteiras neste checkpoint.", "",
        f"IBOV: **{pct(total['total_return_pct'])}% acumulados**, **{pct(total['cagr_pct'])}% a.a.**, "
        f"{total['positive_years']} anos positivos e {total['negative_years']} negativos. "
        f"Fechamentos: {closes[0]['date']} ({closes[0]['ibov_points']:.2f} pontos) e {closes[-1]['date']} ({closes[-1]['ibov_points']:.2f} pontos).", "",
        "Escopo: [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/2#issuecomment-6059288518). "
        "Esta entrega usa apenas percentuais/pontos de índice. Não executa simulação nominal, fiscal, de caixa, aportes ou liquidação. "
        "A autorização para registrar bloqueios e resultados parciais está na própria retificação.", "",
        "**Tabela 1 — retorno anual junho→junho (%)**", "",
        table(["Período", "Início", "Fim", *NAMES], [[r['period'],r['start'],r['end'], *[pct(r[n]) for n in NAMES]] for r in annual]), "",
        "Diferenças contra IBOV em p.p.: [matriz completa](../research/returns_2014_2026_results/annual_excess_pp.csv). "
        "As 48 diferenças das trajetórias pedidas são ND, pois os retornos das carteiras ainda não estão estabelecidos.", "",
        "**Tabela 2 — retorno acumulado desde junho/2014 (%)**", "",
        table(["Até", *NAMES], [[r['end'], *[pct(r[n]) for n in NAMES]] for r in accumulated]), "",
        "Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`. "
        "Índice inicial 1; qualquer intervalo ausente invalida o acumulado posterior. Não se reinicia a carteira em 2020.", "",
        "**Tabela 3 — consolidado 2014–2026**", "",
        table(["Série", "Acumulado %", "CAGR %", "Acima IBOV /12", "Pos./neg./zero", "Média anual %", "Mediana anual %", "Melhor ano (%)", "Pior ano (%)", "Posição média / consistência"],
            [[r['portfolio'],pct(r['total_return_pct']),pct(r['cagr_pct']),"N/A" if r['portfolio']=='IBOV' else "ND",
              f"{r['positive_years']}/{r['negative_years']}/{r['flat_years']}" if r['positive_years'] is not None else "ND",
              pct(r['mean_annual_pct']),pct(r['median_annual_pct']),
              f"{r['best_period']} ({pct(r['best_return_pct'])})" if r['best_period'] else "ND",
              f"{r['worst_period']} ({pct(r['worst_return_pct'])})" if r['worst_period'] else "ND", "ND / ND"] for r in stats]), "",
        "CAGR usa dias efetivos/365,25. Ranking anual, posição média e consistência exigem as cinco séries comparáveis; "
        "não se atribui primeiro lugar ao único índice disponível. Quando houver cobertura completa, posição anual usa média "
        "dos postos empatados; consistência ordena a menor posição anual média, com empate preservado. "
        "As 12 janelas pertencem à mesma trajetória e não constituem 12 experimentos independentes.", "",
        "**Segmentos herdados 2020–2026 — referências condicionais, fora das três tabelas primárias**", "",
        table(["Período", "R03 legado %", "B00S legado %", "IBOV %", "R03−IBOV p.p.", "B00S−IBOV p.p."],
            [[r['period'], *[pct(r[k]) for k in ['R03_inherited_pct','B00S_inherited_pct','IBOV_pct','R03_minus_IBOV_pp','B00S_minus_IBOV_pp']]] for r in segments]), "",
        "Esses percentuais reutilizam as seleções/retornos congelados v11.2 e v12+v13 e recalculam somente a comparação "
        "com IBOV oficial nas mesmas datas. Não são novas coortes, não reconstituem 2014 e não comprovam as seleções PIT da "
        "nova missão. A renovação anual com pesos fixados pode servir de referência ao B2 teórico, condicional à elegibilidade. "
        "B00S ainda combina eventos com aproximações de proventos; o legado contém exceções de continuidade e riscos de "
        "classe/normalização. Não promovemos esses números ao novo índice homogêneo. Nenhuma rotina fiscal ou de capital "
        "nominal foi executada; os arquivos de origem são apenas lidos.", "",
        "[Nomes e pesos herdados](../research/returns_2014_2026_results/conditional_legacy_weights.csv) e "
        "[mudanças entre listas](../research/returns_2014_2026_results/conditional_legacy_membership_changes.csv) estão "
        "marcados como condicionais. A lista anterior a 2020 é desconhecida; trocas de ticker precisam de continuidade "
        "por emissor e não são automaticamente entradas/saídas econômicas. Seleção inicial/2014 e movimentos "
        "2015–2019/BH+entradas/BH padrão permanecem não determinados.", "",
        "**Cobertura, recuperação seletiva e limites**", "",
        "O SQLite foi aberto em leitura somente; seu SHA-256 permaneceu idêntico antes/depois. Existem COTAHIST anuais "
        "1994–2026, DFP desde 2010, mapeamentos PIT e eventos históricos. A presença dos arquivos não demonstra "
        "universo completo nem integridade de cada sucessão societária. `IBOV11` no banco é um ticker e não foi tratado "
        "como o índice IBOV. Foram coletadas 13 respostas anuais diretamente da B3, com URL, data e hash.", "",
        f"Há {coverage['comparative_2009_records']} registros de lucro comparativo de 2009 nas DFP 2010, "
        f"dos quais {coverage['comparative_2009_available']} com recebimento até junho/2014; são registros por perímetro, "
        "não companhias únicas. Portanto, não se declarou 2009 inexistente. Na fotografia original do SQLite e "
        f"comparativos, {cover2014['earnings_complete']} de {cover2014['quoted_share_classes']} classes cotadas "
        f"examinadas em junho/2014 têm cobertura de lucro 2009–2013; {cover2014['earnings_indeterminate']} ficam "
        f"indeterminadas, incluindo {int(cover2014['quoted_share_classes'])-int(cover2014['mapped_unique'])} "
        "sem identidade única no mapeamento usado. Essa triagem cobre tickers "
        "com quatro letras e finais 3–6, não um censo de todas as classes/units. Ter série de lucro não é passar nos filtros.", "",
        f"Entre {coverage['dfp_known_versions']} versões DFP 2010–2013 com metadados conhecidos até o corte, "
        f"{coverage['dfp_known_versions_without_statement']} não têm linhas da DRE individual dessa versão no ZIP local. "
        "Essa contagem inclui versões substituídas e não equivale ao número de lacunas indispensáveis. "
        "O arquivo de cobertura identifica ticker/exercício e as datas posteriores para distinguir faltas materiais.", "",
        "A coleta seletiva recuperou os originais CVM 35587 (BB, DFP 2013), 24646 (Itaú, DFP 2012, com comparativos) "
        "e 39471 (WEG, FRE 2014); a CVM respondeu com arquivos ZIP. Os extratos/XML e hashes ficam na entrega. "
        "Foram extraídas 12 observações de lucro individual/consolidado nos XML originais, respeitando as contas "
        "específicas do plano bancário. Esses documentos permitem reparar parte das lacunas; a fotografia da cobertura original não inclui essa reparação "
        "e não deve ser lida como prova de indisponibilidade na CVM. A reconciliação integral desses originais com "
        "os filtros e demais emissores não foi concluída.", "",
        "Capital: 524 de 573 linhas de capital emitido no FRE rotulado 2014 não satisfazem recebimento/aprovação até "
        "junho/2014. Arquivos anteriores contêm evidência admissível para 500 emissores, inclusive vários líderes; "
        "portanto, o ranking das oito maiores não é considerado impossível. Ele permanece não estabelecido: falta "
        "reconciliar capital vigente de todas as classes, identidades históricas, preços e taxonomia do universo "
        "comparável. Não usamos capital posterior nem escolhemos os maiores de hoje.", "",
        "Pendências específicas: seleção R03 completa de 2014–2019 com filtros/triagem de perdas; universo BESST e "
        "recorrência de proventos conhecida em cada junho; predecessores/deslistados (por exemplo TBLE3, ALLL3 e BICB4 "
        "não resolvidos no mapeamento examinado); ranking por companhia de 2014; trajetórias de eventos homogêneas "
        "para as posições que essas seleções determinarem. Não são pendências de imposto, caixa ou financiamento.", "",
        "**Convenções fixadas para a primeira etapa**", "",
        "Índices de retorno total bruto, base 1 no último pregão de junho/2014, observados nos fechamentos oficiais "
        "de cada junho até 30/06/2026. Reinvestimento teórico integral dos proventos brutos no próprio ativo no fechamento "
        "da data-ex, incorporando conversões, desdobramentos e sucessoras uma única vez; preços nominais+eventos, ou série "
        "de retorno total validada, sem misturar dividendos adicionais com preços já ajustados. Nenhum saldo operacional "
        "é modelado. Os segmentos herdados acima não foram convertidos retroativamente a essa convenção uniforme.", "",
        "B2: conjunto elegível de cada junho; pesos iguais R03 e iguais por setor/depois por emissor B00S. "
        "Ausência de prova permanece INDETERMINATE, não FAIL. BH B00S: união dos nomes detidos com novos elegíveis; "
        "quando houver entradas, redistribuição interna aos pesos B00S no conjunto ampliado, preservando o nível "
        "do índice; sem entradas, pesos oscilam sem rebalanceamento discricionário. Essa regra de retenção+adições "
        "não é BH passivo estrito. BH padrão: dois maiores emissores de 2014 por grupo, 12,5% cada, sem novas líderes. "
        "Capitalização agrega classes sem contar units em duplicidade; classe de investimento escolhida pela liquidez "
        "conhecida na formação. Nenhuma dessas regras autoriza inventar a seleção faltante.", "",
        "Taxonomia: bens industriais (máquinas/equipamentos, material de transporte e serviços industriais); financeiro "
        "(bancos, seguros, intermediação e holdings de atividade financeira); utilidades públicas (energia, água/saneamento "
        "e gás canalizado); saúde (medicamentos, distribuição de medicamentos, serviços hospitalares, diagnósticos e "
        "operadoras de saúde). Holdings diversificadas exigem classificação econômica documentada. Bebidas, agricultura, "
        "joalheria e papel/celulose ficam fora desses quatro grupos.", "",
        "Histórico: `max(2009, ano−10)..ano−1`, com 5/6/7/8/9/10 exercícios em 2014/15/16/17/18/19 e dez móveis "
        "depois. Para o requisito proporcional 8/10: `ceil(0,8 × n)` anos positivos, preservando demais restrições "
        "da regra. Filtros próprios de três/cinco anos e demais limites não são afrouxados.", "",
        "**Reprodução e fontes**", "",
        "```bash\npython scripts/returns_stage1.py\npython -m pytest -q tests/test_returns_stage1.py\n"
        "# Apenas para repetir a auditoria no acervo local, sem o modificar:\n"
        "python scripts/audit_stage1_coverage.py --data-root /caminho/do/acervo\n```", "",
        "O cálculo percentual e seus testes são offline. `scripts/fetch_ibov_stage1.py` refaz somente a coleta B3 "
        "e deve ser usado explicitamente, pois atualiza o snapshot. Manifestos e CSVs estão em "
        "[insumos](../research/returns_2014_2026_inputs/) e [resultados](../research/returns_2014_2026_results/). "
        "O workflow independente verifica reprodução offline. A branch parte de `fc62733`, sem alterar arquivos "
        "das baselines v11.2/v12/v13 ou do PR #2.", "",
        "Validação local desta entrega: **18 testes da etapa percentual e 101 testes das baselines aprovados**. "
        "O replay percentual reproduziu os arquivos byte a byte. Esses testes verificam os cálculos e a preservação "
        "dos dados; não suprem as seleções históricas ainda não determinadas.", "",
        "Fontes oficiais: [evolução diária IBOV/B3](https://sistemaswebb3-listados.b3.com.br/indexStatisticsPage/daily-evolution/IBOVESPA?language=pt-br), "
        "[metodologia B3 — índice de retorno total](https://www.b3.com.br/data/files/9C/15/76/F6/3F6947102255C247AC094EA8/IBOV-Metodologia-pt-br__Novo_.pdf), "
        "[DFP/CVM](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp).", "",
        "**Estado final: checkpoint parcial publicado para revisão; pedido de quatro trajetórias completas ainda pendente. "
        "Não houve início da etapa fiscal/operacional, merge ou promoção de baseline.**", ""]
    (ROOT / "docs/checkpoint_returns_2014_2026_stage1.md").write_text("\n".join(report), encoding="utf-8")
    manifest = dict(status="PARTIAL_NOT_FULL_FOUR_PORTFOLIO_STUDY", dates=[r['date'] for r in closes],
        complete_requested_portfolios=0, complete_benchmark_intervals=12, conditional_legacy_portfolio_intervals=12,
        strict_annual_numeric_cells=12, strict_annual_missing_portfolio_cells=48,
        baseline_commit="fc62733", monetary_simulation=False, taxes=False, external_contributions=False,
        inputs=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in [graham_path,barsi_path]],
        outputs=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUTPUT.glob('*.csv'))])
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(total,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
