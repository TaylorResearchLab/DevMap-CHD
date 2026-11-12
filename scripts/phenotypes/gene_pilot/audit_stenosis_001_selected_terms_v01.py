#!/usr/bin/env python3
"""Read-only STENOSIS-001 nine-term audit from existing full Isilon output."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def audit(output, registry):
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest.get("analysis") != "STENOSIS-001_structural_coverage_v01":
        raise ValueError("Wrong analysis output")
    approved = manifest["approved_exception_ids"]
    if len(approved) != 9 or len(set(approved)) != 9:
        raise ValueError("Unexpected approved exception set")
    genes = {r["approved_hgnc_symbol"] for r in rows(registry)}
    if len(genes) != 662:
        raise ValueError("Frozen gene registry denominator mismatch")
    projections = defaultdict(list)
    eligible_ids = set()
    selected_by_pid = {}
    for p in rows(output / "selected_gene_disease_hpo_projections.tsv"):
        if p["resolved_hpo_id"] in approved:
            projections[p["resolved_hpo_id"]].append(p)
            selected_by_pid[p["projection_id"]] = p
            if p["claim_polarity"] == "not_negated":
                eligible_ids.add(p["projection_id"])
    evidence = defaultdict(lambda: {"all": set(), "eligible": set(),
                                    "positive": set()})
    for e in rows(output / "selected_original_hpoa_observations.tsv"):
        p = selected_by_pid.get(e["projection_id"])
        if p is None:
            continue
        h = p["resolved_hpo_id"]
        key = (e["source_resource"], e["source_release"], e["source_row_id"])
        evidence[h]["all"].add(key)
        if e["projection_id"] in eligible_ids:
            evidence[h]["eligible"].add(key)
            if e["evidence_outcome"] in ("categorical_positive", "observed_positive"):
                evidence[h]["positive"].add(key)
    print("HPO_ID\tLABEL\tALL_PROJECTIONS\tELIGIBLE_PROJECTIONS\tGENES\tDISEASES\tSOURCE_ROWS\tPOSITIVE_SOURCE_ROWS")
    decisions = {x["hpo_id"]: x for x in rows(output / "exception_decisions.tsv")}
    missing = []
    for h in approved:
        ps = projections[h]
        eligible = [p for p in ps if p["projection_id"] in eligible_ids]
        if not eligible:
            missing.append(h)
        print("\t".join(map(str, [
            h, decisions[h]["pinned_hpo_label"], len(ps), len(eligible),
            len({p["gene_id"] for p in eligible}),
            len({p["disease_id"] for p in eligible}),
            len(evidence[h]["eligible"]), len(evidence[h]["positive"]),
        ])))
    print("MISSING_QUALIFYING_EXCEPTION_IDS\t" + ";".join(missing))
    print("CIC_IN_FROZEN_662_REGISTRY\t" + str("CIC" in genes).lower())
    print("LZTR1_IN_FROZEN_662_REGISTRY\t" + str("LZTR1" in genes).lower())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results", type=Path, default=Path(
            "results/phenotypes/structural_coverage_stenosis_v01"))
    parser.add_argument(
        "--registry", type=Path, default=Path(
            "data/releases/2026.09.08/genes.tsv"))
    args = parser.parse_args()
    audit(args.results, args.registry)


if __name__ == "__main__":
    main()
