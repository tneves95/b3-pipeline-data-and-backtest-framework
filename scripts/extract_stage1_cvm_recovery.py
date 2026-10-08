#!/usr/bin/env python3
"""Extract the three recovered CVM originals without changing the SQLite."""
import csv
import hashlib
import json
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "research/returns_2014_2026_inputs/cvm_recovery"


def main():
    rows, extracts = [], []
    for source in json.loads((FOLDER / "attempts.json").read_text()):
        raw = (FOLDER / source["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
        with ZipFile(BytesIO(raw)) as archive:
            ext = ".dfp" if source["document_type"] == "dfp" else ".fre"
            name = next(n for n in archive.namelist() if n.endswith(ext))
            with ZipFile(BytesIO(archive.read(name))) as form:
                wanted = ["InfoFinaDFin.xml", "PeriodoDemonstracaoFinanceira.xml", "Documento.xml"] if ext == ".dfp" else ["CapitalSocial.xml", "Documento.xml"]
                dest = FOLDER / (str(source["document_id"]) + "_financial_extract.zip")
                with ZipFile(dest, "w", compression=ZIP_DEFLATED) as output:
                    for member in wanted:
                        value = form.read(member)
                        # A fixed ZIP date makes repeated extraction reproducible.
                        from zipfile import ZipInfo
                        info = ZipInfo(member, date_time=(1980,1,1,0,0,0))
                        info.compress_type = ZIP_DEFLATED
                        output.writestr(info, value)
                        extracts.append(dict(document_id=source["document_id"], original_member=name,
                            member=member, sha256=hashlib.sha256(value).hexdigest(), extract=dest.name))
                if ext != ".dfp":
                    continue
                periods = {r.findtext("NumeroIdentificacaoPeriodo"): r.findtext("DataFimPeriodo")[:10]
                           for r in ET.fromstring(form.read("PeriodoDemonstracaoFinanceira.xml"))}
                for row in ET.fromstring(form.read("InfoFinaDFin.xml")):
                    code = row.findtext("PlanoConta/NumeroConta", "")
                    desc = row.findtext("DescricaoConta1", "")
                    if not (re.fullmatch(r"3\.\d{2}", code) and desc.startswith("Lucro") and "Período" in desc):
                        continue
                    for period, end in sorted(periods.items()):
                        rows.append(dict(document_id=source["document_id"], cnpj=source["cnpj"],
                            received=source["receipt"], period_end=end, account=code, description=desc,
                            information_type_code=row.findtext("PlanoConta/VersaoPlanoConta/CodigoTipoInformacaoFinanceira"),
                            statement_value=row.findtext("ValorConta"+period),
                            status="RECOVERED_ORIGINAL_NOT_FULL_FILTER_VALIDATION", source=source["url"]))
    with (FOLDER / "recovered_income.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (FOLDER / "extracts_manifest.json").write_text(json.dumps(extracts, indent=2)+"\n")
    print(f"Recovered {len(rows)} income observations from original forms")


if __name__ == "__main__":
    main()
