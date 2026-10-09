"""Read-only audit checks. This never runs or writes a portfolio backtest."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
INPUT = REPO / "research/b00s_four_variants_2014_2026/inputs"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run():
    baseline = json.loads((HERE / "baseline_all_tracked.json").read_text())
    changed = [name for name, expected in baseline["files"].items()
               if not (REPO / name).is_file()
               or sha((REPO / name).read_bytes()) != expected]
    assert not changed, ("Existing baseline changed", changed)
    packet = json.loads((HERE / "blind_packet_manifest.json").read_text())
    assert packet["baseline_commit"] == baseline["commit"]
    protocol = "docs/experimento_b00s_quatro_variantes_2014_2026.md"
    assert sha((REPO / protocol).read_bytes()) == packet["protocol_original_sha256"]
    original_v2 = subprocess.check_output(["git", "show", "7fea064:" + protocol], cwd=REPO)
    assert original_v2 == (REPO / protocol).read_bytes()
    sections = 0
    unique = set()
    for case in packet["cases"]:
        for source in case["source_sections"]:
            assert source["received"][:10] <= case["cutoff"], (case["ticker"], source["docid"])
            blob = (INPUT / source["original"]).read_bytes()
            raw = gzip.decompress(blob) if source["original"].endswith(".gz") else blob
            assert sha(raw) == source["original_sha256"]
            if source.get("submission", {}).get("reference"):
                assert source["submission"]["reference"][:10] <= case["cutoff"]
            sections += 1
            unique.add((source["docid"], source["group"]))
        for name, expected in case["files"].items():
            assert sha((INPUT / name).read_bytes()) == expected, name
        for name, supplement in case.get("supplements", {}).items():
            path = HERE / supplement["path"]
            assert sha(path.read_bytes()) == supplement["sha256"]
            if name == "ipca_known.json":
                ipca = json.loads(path.read_text())
                assert ipca["known_may_availability"]["release_date"] <= case["cutoff"]
                for observation in ipca["sgs433_known_monthly_values"]:
                    day, month, year = observation["data"].split("/")
                    assert f"{year}-{month}" <= f"{case['year']}-05"
            if name == "selection_quotes.json":
                for quote in json.loads(path.read_text())["quotes"]:
                    raw = quote["raw_record"].encode("latin-1")
                    assert sha(raw) == quote["record_sha256"]
                    assert quote["date"] == case["cutoff"]
                    assert raw[2:10].decode() == case["cutoff"].replace("-", "")
                    assert raw[12:24].decode().strip() == quote["ticker"]
                    assert int(raw[108:121]) / 100 == quote["close"]
            if name == "selection_quote.json":
                quote = json.loads(path.read_text())
                raw = path.with_name(quote["raw_record_file"]).read_bytes()
                assert sha(raw) == quote["raw_record_sha256"] == quote["quote"]["record_sha256"]
                assert quote["quote"]["date"] == case["cutoff"]
    # Verify every PR #3 blob against Git's original content hash.
    pr3 = "8d394e9ab563daebe43603a3e85f35f43c1402bc"
    entries = subprocess.check_output(["git", "ls-tree", "-r", "-z", pr3], cwd=REPO).split(b"\0")
    protected = 0
    for entry in entries:
        if not entry:
            continue
        meta, name = entry.split(b"\t", 1)
        _, kind, expected = meta.split()
        assert kind == b"blob"
        data = (REPO / name.decode()).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert actual == expected.decode(), name
        protected += 1
    prior = "docs/reviews/adversarial_2019.json"
    prior_original = subprocess.check_output(["git", "show", "b13546c:" + prior], cwd=REPO)
    assert prior_original == (REPO / prior).read_bytes()
    # New reports are immutable after the independent reviewers seal them.
    sealed = json.loads((HERE / "sealed_reports.json").read_text())
    for report in sealed["files"]:
        blob = (HERE / report["path"]).read_bytes()
        assert sha(blob) == report["sha256"], report["path"]
        if "uncompressed_sha256" in report:
            assert sha(gzip.decompress(blob)) == report["uncompressed_sha256"]
    return dict(baseline_commit=baseline["commit"], baseline_files_unchanged=len(baseline["files"]),
                pr3_files_unchanged=protected, sample_cases=len(packet["cases"]),
                supplied_source_sections=sections, unique_source_sections=len(unique),
                source_hash_mismatches=0, post_cutoff_sources=0,
                original_v2_unchanged=True, prior_independent_2019_unchanged=True,
                sealed_report_files_unchanged=len(sealed["files"]),
                portfolio_recalculations=0, portfolio_reclassifications=0)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
