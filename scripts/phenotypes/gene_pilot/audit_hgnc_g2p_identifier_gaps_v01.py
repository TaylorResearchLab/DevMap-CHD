#!/usr/bin/env python3
"""Audit independent HGNC/NCBI/symbol coverage and unresolved HPO alias leads.

Read-only; does not add gene-HPO associations or modify the 662-gene registry.
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from audit_662_hpo_coverage import (
    EXPECTED_G2P_SHA, EXPECTED_HPOA_SHA, sha256, tsv_rows, write_tsv,
)

REGISTRY_SHA = "523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c"
HGNC_SHA = "6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20"
OUT_FIELDS = (
    "hgnc_id", "approved_symbol", "ensembl_gene_id", "hgnc_snapshot_symbol",
    "hgnc_status", "hgnc_entrez_id", "coverage_original_method",
    "exact_symbol_rows", "ncbi_id_rows", "both_symbol_and_ncbi",
    "ncbi_rows_with_other_symbol", "exact_symbol_rows_with_other_ncbi",
    "historical_alias_source_rows", "historical_alias_symbols_in_hpo",
    "historical_alias_ncbi_ids", "historical_alias_other_hgnc_ids",
    "identifier_diagnostic_state", "source_gene_phenotype_scope",
)
ALIAS_FIELDS = (
    "hgnc_id", "approved_symbol", "candidate_symbol", "candidate_kind",
    "hpo_g2p_rows", "hpo_source_ncbi_ids", "hgnc_entrez_id",
    "source_id_matches_hgnc", "other_hgnc_owners", "review_state",
)


def checked_manifest(folder, names):
    values = {}
    for text in (folder / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        parts = text.split(None, 1)
        if len(parts) != 2:
            raise ValueError("Malformed SHA256SUMS line")
        name = parts[1].strip()
        if Path(name).name != name or name in values:
            raise ValueError(f"Unsafe or duplicate checksum key: {name}")
        values[name] = parts[0]
    for name in names:
        if name not in values or sha256(folder / name) != values[name]:
            raise ValueError(f"Missing or changed verified input: {folder / name}")


def source_aliases(value):
    if not value:
        return set()
    # HGNC complete set multi-value columns use pipe separators.
    # Tolerate bracketed CSV-like encodings without treating whole cell as alias.
    clean = value.strip().strip("[]")
    return {v.strip().strip("'\" ")
            for v in re.split(r"[|,]", clean) if v.strip().strip("'\" ")}


def audit(registry, g2p, hpoa, hgnc, coverage_dir, out, check_hashes=True):
    registry, g2p, hpoa = Path(registry), Path(g2p), Path(hpoa)
    hgnc, coverage_dir, out = Path(hgnc), Path(coverage_dir), Path(out)
    if out.exists():
        raise ValueError("Output directory exists; use a new version")
    hashes = {"registry": sha256(registry), "g2p": sha256(g2p),
              "hpoa": sha256(hpoa), "hgnc": sha256(hgnc)}
    if check_hashes and hashes != {
        "registry": REGISTRY_SHA, "g2p": EXPECTED_G2P_SHA,
        "hpoa": EXPECTED_HPOA_SHA, "hgnc": HGNC_SHA,
    }:
        raise ValueError("Frozen input SHA256 mismatch")
    checked_manifest(coverage_dir, (
        "gene_hpo_coverage_662.tsv", "genes_without_hpo_gene_summary.tsv",
        "hpo_coverage_662_manifest.json",
    ))
    old = json.loads((coverage_dir / "hpo_coverage_662_manifest.json").read_text())
    if (old.get("frozen_gene_registry_count") != 662 or
        old.get("hpo_ncbi_crosswalk_provided") is not True or
        old.get("sha256", {}).get("hgnc_crosswalk") != hashes["hgnc"] or
        old.get("sha256", {}).get("genes_to_phenotype") != hashes["g2p"] or
        old.get("sha256", {}).get("phenotype_hpoa") != hashes["hpoa"] or
        old.get("sha256", {}).get("registry") != hashes["registry"]):
        raise ValueError("Coverage output is not linked to pinned input files")

    with registry.open(encoding="utf-8-sig", newline="") as f:
        registry_rows = list(csv.DictReader(f, delimiter="\t"))
    frozen = {r["hgnc_id"]: r for r in registry_rows}
    if len(registry_rows) != 662 or len(frozen) != 662:
        raise ValueError("Frozen registry must contain 662 distinct HGNC IDs")
    frozen_symbols = {r["approved_hgnc_symbol"] for r in registry_rows}
    if len(frozen_symbols) != 662:
        raise ValueError("Frozen registry must contain 662 distinct approved symbols")

    hgnc_by_id = {}
    hgnc_symbol_owner = defaultdict(set)
    hgnc_alias_owners = defaultdict(set)
    for row in tsv_rows(hgnc, {"hgnc_id", "symbol", "entrez_id"}):
        hid = row["hgnc_id"].strip()
        if hid in hgnc_by_id:
            raise ValueError(f"Duplicate HGNC snapshot ID: {hid}")
        hgnc_by_id[hid] = row
        hgnc_symbol_owner[row["symbol"].strip()].add(hid)
        for value in ("prev_symbol", "alias_symbol"):
            for a in source_aliases(row.get(value, "")):
                hgnc_alias_owners[a].add(hid)

    by_symbol, by_ncbi = Counter(), Counter()
    ncbi_by_symbol, symbol_by_ncbi = defaultdict(set), defaultdict(set)
    source_count = 0
    for row in tsv_rows(g2p, {"ncbi_gene_id", "gene_symbol", "hpo_id", "disease_id"}):
        source_count += 1
        symbol = row["gene_symbol"].strip()
        ncbi = row["ncbi_gene_id"].strip()
        by_symbol[symbol] += 1
        if ncbi:
            by_ncbi[ncbi] += 1
        ncbi_by_symbol[symbol].add(ncbi)
        if ncbi:
            symbol_by_ncbi[ncbi].add(symbol)
    if source_count != old["hpo_total_gene_summary_rows"]:
        raise ValueError("HPO G2P original row count changed")

    old_rows = {}
    with (coverage_dir / "gene_hpo_coverage_662.tsv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            gid = row["hgnc_id"]
            if gid in old_rows:
                raise ValueError("Duplicate gene in original coverage output")
            old_rows[gid] = row
    if set(old_rows) != set(frozen):
        raise ValueError("Original coverage gene set changed")

    diagnostics, missing, leads = [], [], []
    for gid, r in sorted(frozen.items()):
        symbol = r["approved_hgnc_symbol"]
        hg = hgnc_by_id.get(gid)
        ncbi = (hg or {}).get("entrez_id", "").strip()
        ncbi = ncbi if ncbi.isdigit() else ""
        exact = by_symbol[symbol]
        stable = by_ncbi[ncbi] if ncbi else 0
        old_row = old_rows[gid]
        previously_found = old_row["hpo_gene_summary_status"] == "PRESENT"
        if (bool(exact or stable) != previously_found or
            old_row["match_method"] not in ("NCBI_GENE_ID", "SYMBOL_EXACT", "NO_MATCH")):
            raise ValueError(f"Original matching result changed for {gid}")

        aliases = {}
        for kind, column in (("previous", "prev_symbol"), ("alias", "alias_symbol")):
            for alt in source_aliases((hg or {}).get(column, "")):
                if alt != symbol and by_symbol[alt]:
                    aliases.setdefault(alt, set()).add(kind)
        alias_ncbi_ids, other_owners = set(), set()
        for alt in sorted(aliases):
            matching_ids = ncbi_by_symbol[alt]
            alias_ncbi_ids |= matching_ids
            owners = ((hgnc_symbol_owner.get(alt, set()) |
                       hgnc_alias_owners.get(alt, set())) - {gid})
            other_owners |= owners
            leads.append({
                "hgnc_id": gid, "approved_symbol": symbol,
                "candidate_symbol": alt,
                "candidate_kind": ";".join(sorted(aliases[alt])),
                "hpo_g2p_rows": by_symbol[alt],
                "hpo_source_ncbi_ids": ";".join(sorted(matching_ids)),
                "hgnc_entrez_id": ncbi,
                "source_id_matches_hgnc": "yes" if ncbi and ncbi in matching_ids else "no",
                "other_hgnc_owners": ";".join(sorted(owners)),
                "review_state": "alias_proposal_requires_identifier_adjudication",
            })
        if previously_found:
            state = "matched_source"
        elif not hg:
            state = "no_HGNC_snapshot_record"
        elif not ncbi and aliases:
            state = "no_HGNC_Entrez_with_alias_source_leads"
        elif not ncbi:
            state = "no_HGNC_Entrez_no_source_symbol_lead"
        elif aliases:
            state = "HGNC_Entrez_no_HPO_rows_alias_source_leads"
        else:
            state = "HGNC_Entrez_no_HPO_rows_or_symbol_leads"
        row = {
            "hgnc_id": gid, "approved_symbol": symbol,
            "ensembl_gene_id": r.get("ensembl_gene_id", ""),
            "hgnc_snapshot_symbol": (hg or {}).get("symbol", ""),
            "hgnc_status": (hg or {}).get("status", ""),
            "hgnc_entrez_id": ncbi,
            "coverage_original_method": old_row["match_method"],
            "exact_symbol_rows": exact, "ncbi_id_rows": stable,
            "both_symbol_and_ncbi": "yes" if exact and stable else "no",
            "ncbi_rows_with_other_symbol": ";".join(
                sorted(symbol_by_ncbi.get(ncbi, set()) - {symbol})),
            "exact_symbol_rows_with_other_ncbi": ";".join(
                sorted(ncbi_by_symbol.get(symbol, set()) - {ncbi, ""})),
            "historical_alias_source_rows": sum(by_symbol[a] for a in aliases),
            "historical_alias_symbols_in_hpo": ";".join(sorted(aliases)),
            "historical_alias_ncbi_ids": ";".join(sorted(alias_ncbi_ids)),
            "historical_alias_other_hgnc_ids": ";".join(sorted(other_owners)),
            "identifier_diagnostic_state": state,
            "source_gene_phenotype_scope": "HPO_G2P_disease_mediated_discovery_only",
        }
        diagnostics.append(row)
        if not previously_found:
            missing.append(row)

    if (len(missing) != old["hpo_gene_summary_unannotated_gene_count"] or
        sum(x["identifier_diagnostic_state"] == "matched_source"
            for x in diagnostics) != old["hpo_gene_summary_annotated_gene_count"]):
        raise ValueError("Original 519/143 partition not conserved")
    summary = Counter(r["identifier_diagnostic_state"] for r in diagnostics)
    result = {
        "status": "read_only_gene_identifier_diagnostic_pending_independent_review",
        "frozen_gene_count": len(frozen),
        "original_matched_gene_count": len(diagnostics) - len(missing),
        "original_unmatched_gene_count": len(missing),
        "exact_symbol_matched_genes": sum(int(x["exact_symbol_rows"]) > 0 for x in diagnostics),
        "ncbi_id_matched_genes": sum(int(x["ncbi_id_rows"]) > 0 for x in diagnostics),
        "both_exact_symbol_and_ncbi_matched_genes": sum(x["both_symbol_and_ncbi"] == "yes" for x in diagnostics),
        "unmatched_without_HGNC_entrez": sum(not x["hgnc_entrez_id"] for x in missing),
        "unmatched_with_alias_hpo_source_leads": sum(bool(x["historical_alias_symbols_in_hpo"]) for x in missing),
        "unmatched_without_alias_hpo_source_leads": sum(not x["historical_alias_symbols_in_hpo"] for x in missing),
        "alias_source_leads_total": len(leads),
        "alias_leads_with_other_HGNC_owners": sum(bool(x["other_hgnc_owners"]) for x in leads),
        "identifier_states": dict(sorted(summary.items())),
        "source_g2p_rows_scanned": source_count,
        "hgnc_rows_scanned": len(hgnc_by_id),
        "source_sha256": hashes,
        "prior_coverage_manifest_sha256": sha256(coverage_dir / "hpo_coverage_662_manifest.json"),
        "gene_reassignment_performed": False,
        "direct_gene_phenotype_PARs_promoted": 0,
        "interpretation": ("Source matching and possible historical alias leads only. "
                           "An alias match is not proof of equivalent HGNC/NCBI identity; "
                           "no observed phenotype is inferred for unmatched genes."),
    }
    out.mkdir(parents=True)
    files = {
        "gene_identifier_diagnostic_662.tsv": (diagnostics, OUT_FIELDS),
        "unresolved_143_identifier_diagnostic.tsv": (missing, OUT_FIELDS),
        "historical_alias_source_leads.tsv": (leads, ALIAS_FIELDS),
    }
    for name, (items, fields) in files.items():
        write_tsv(out / name, items, fields)
    (out / "manifest.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for name in (*files, "manifest.json"):
            f.write(f"{sha256(out / name)}  {name}\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--g2p", required=True, type=Path)
    parser.add_argument("--hpoa", required=True, type=Path)
    parser.add_argument("--hgnc", required=True, type=Path)
    parser.add_argument("--coverage-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.registry, args.g2p, args.hpoa,
                           args.hgnc, args.coverage_dir, args.out), indent=2))


if __name__ == "__main__":
    main()
