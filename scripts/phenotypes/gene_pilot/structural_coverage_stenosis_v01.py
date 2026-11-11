#!/usr/bin/env python3
"""STENOSIS-001 structural HPO classification and frozen 662-gene discovery census.

Curated membership is independent of native HPO is_a ancestry. The underlying
records are disease-subject HPOA observations and disease-mediated projections,
not direct causal gene-phenotype assertions. No existing output is modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = "HP:0030680"
RELEASE = "v2026-09-01"
DECISION_URL = "https://app.notion.com/p/41429187800881c39a35f60c6dbaa45e"
APPROVED = {
    "HP:0001642": "Pulmonic stenosis",
    "HP:0001650": "Aortic valve stenosis",
    "HP:0001718": "Mitral stenosis",
    "HP:0004381": "Supravalvular aortic stenosis",
    "HP:0010446": "Tricuspid stenosis",
    "HP:0011570": "Congenital mitral stenosis",
    "HP:0034348": "Subpulmonary stenosis",
    "HP:0034349": "Supravalvar pulmonary stenosis",
    "HP:0034350": "Valvular pulmonary stenosis",
}
DEFERRED = {
    "HP:0001653": "Mitral regurgitation",
    "HP:0001659": "Aortic regurgitation",
    "HP:0005180": "Tricuspid regurgitation",
    "HP:0010444": "Pulmonic regurgitation",
    "HP:0034376": "Atrioventricular valve regurgitation",
    "HP:0034377": "Single atrioventricular valve regurgitation",
}
PINNED = {
    "registry": "523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c",
    "hp_obo": "93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22",
    "genes_to_phenotype": "507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c",
    "phenotype_hpoa": "e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72",
}
OBS_REQUIRED = {"projection_id", "source_claim_id", "original_subject",
                "original_object", "source_row_id", "source_resource",
                "source_release", "evidence_id", "claim_polarity",
                "evidence_outcome", "onset"}
PROJ_REQUIRED = {"projection_id", "gene_id", "gene_symbol", "disease_id",
                 "phenotype_id", "source_claim_id", "claim_polarity",
                 "projection_role", "hpoa_evidence_links"}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_tsv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = tuple(reader.fieldnames or ())
        if not set(required) <= set(cols):
            raise ValueError(f"{path}: missing {sorted(set(required) - set(cols))}")
        for row in reader:
            yield row


def write_tsv(path, rows, columns):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t",
                                extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_obo(path):
    terms, alt = {}, {}
    current = None

    def save():
        if current is None or "id" not in current:
            return
        term_id = current["id"]
        if term_id in terms:
            raise ValueError(f"Duplicated HPO term: {term_id}")
        terms[term_id] = dict(current)
        for other in current["alt_id"]:
            if other in alt and alt[other] != term_id:
                raise ValueError(f"Ambiguous HPO alternate ID: {other}")
            alt[other] = term_id

    with Path(path).open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line == "[Term]":
                save()
                current = {"parents": [], "alt_id": [], "obsolete": False}
            elif line.startswith("["):
                save()
                current = None
            elif current is not None and ": " in line:
                key, value = line.split(": ", 1)
                if key in ("id", "name"):
                    current[key] = value
                elif key == "is_a":
                    current["parents"].append(value.split(" ! ", 1)[0])
                elif key == "alt_id":
                    current["alt_id"].append(value)
                elif key == "is_obsolete":
                    current["obsolete"] = value == "true"
    save()
    return terms, alt


def ontology(terms, alt):
    if ROOT not in terms or terms[ROOT]["obsolete"]:
        raise ValueError(f"Missing current structural HPO root {ROOT}")
    visiting = set()

    @lru_cache(None)
    def ancestry(hpo_id):
        hpo_id = alt.get(hpo_id, hpo_id)
        if hpo_id not in terms or terms[hpo_id]["obsolete"]:
            return frozenset()
        if hpo_id in visiting:
            raise ValueError(f"Ontology is_a cycle: {hpo_id}")
        visiting.add(hpo_id)
        found = {hpo_id}
        for p in terms[hpo_id]["parents"]:
            found.update(ancestry(p))
        visiting.remove(hpo_id)
        return frozenset(found)

    return ancestry


def classification(terms, alt):
    anc = ontology(terms, alt)
    for hpo_id, expected_label in {**APPROVED, **DEFERRED}.items():
        t = terms.get(hpo_id)
        if t is None or t["obsolete"] or t.get("name") != expected_label:
            raise ValueError(
                f"Pinned HPO ID/label/obsolete mismatch: {hpo_id}, "
                f"expected {expected_label!r}, observed {t!r}"
            )
    members = {}
    for hpo_id, t in sorted(terms.items()):
        if t["obsolete"]:
            continue
        inherited = ROOT in anc(hpo_id)
        exception = hpo_id in APPROVED
        if not (inherited or exception):
            continue
        route = ("ontology_is_a+approved_exception" if inherited and exception
                 else "ontology_is_a" if inherited
                 else "approved_exception")
        members[hpo_id] = {
            "hpo_id": hpo_id, "hpo_label": t["name"], "hpo_release": RELEASE,
            "structural_member": "yes", "membership_route": route,
            "in_morphology_subtree": str(inherited).lower(),
            "approved_stenosis_exception": str(exception).lower(),
            "native_is_a_parents": ";".join(t["parents"]),
            "native_is_a_ancestors": ";".join(sorted(anc(hpo_id) - {hpo_id})),
            "anatomical_rationale": ("Approved structural stenosis involving a valve "
                                    "or cardiac outflow region" if exception else
                                    "Native HPO cardiovascular morphology ancestry"),
            "scientific_authority": ("Deanne M. Taylor" if exception else
                                     "Pinned HPO ontology"),
            "decision_date": "2026-11-10" if exception else "",
            "decision_provenance": DECISION_URL if exception else "",
            "scientific_status": ("user_approved" if exception else
                                  "ontology_derived"),
            "independent_review_status": "awaiting_Agent_2",
            "developmental_onset_inferred": "no",
        }
    if not set(APPROVED).issubset(members):
        raise ValueError("Approved stenosis term is missing")
    return members, anc


def verify_manifest(folder):
    folder = Path(folder)
    entries = {}
    for line in (folder / "SHA256SUMS.txt").read_text().splitlines():
        fields = line.split(None, 1)
        if len(fields) != 2:
            raise ValueError(f"Malformed checksum in {folder}")
        hash_, filename = fields
        if filename.startswith("*"):
            filename = filename[1:]
        if Path(filename).name != filename or filename in entries:
            raise ValueError(f"Unsafe checksum name {filename}")
        if digest(folder / filename) != hash_:
            raise ValueError(f"Upstream source digest mismatch: {filename}")
        entries[filename] = hash_
    required = {"manifest.json", "original_hpoa_observations.tsv",
                "gene_disease_hpo_discovery_projections.tsv"}
    if not required <= entries.keys():
        raise ValueError("Incomplete audited two-level export SHA256SUMS")
    m = json.loads((folder / "manifest.json").read_text())
    if (m.get("identity_profile") != "hpoa_disease_subject_two_level_v01"
        or m.get("original_evidence_link_count") != 63012
        or m.get("provisional_projection_count") != 62832):
        raise ValueError("Source manifest differs from audited two-level export")
    return entries


def distinct_keys(projections, observations, subset):
    picked = [p for p in projections.values()
              if p["projection_id"] in subset]
    ids = {p["projection_id"] for p in picked}
    evidence = [e for e in observations if e["projection_id"] in ids]
    positive_evidence = [e for e in evidence
                         if e["evidence_outcome"] in
                         {"categorical_positive", "observed_positive"}]
    return {
        "genes": {p["gene_id"] for p in picked},
        "diseases": {p["disease_id"] for p in picked},
        "hpo_terms": {p["resolved_hpo_id"] for p in picked},
        "original_source_rows": {
            (e["source_resource"], e["source_release"], e["source_row_id"])
            for e in evidence
        },
        "source_claims": {p["source_claim_id"] for p in picked},
        "original_evidence_links": {e["evidence_id"] for e in evidence},
        "positive_source_rows": {
            (e["source_resource"], e["source_release"], e["source_row_id"])
            for e in positive_evidence
        },
    }


def zip_review(output, included):
    path = output / "STENOSIS-001_review_v01.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for filename in included:
            info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (output / filename).read_bytes(),
                       compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    (output / "review_bundle.sha256").write_text(
        f"{digest(path)}  {path.name}\n", encoding="utf-8"
    )
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None or sorted(z.namelist()) != sorted(included):
            raise ValueError("Review archive integrity or inclusion failure")


def analyze(registry, obo, g2p, hpoa, source, out, *,
            strict=True, commit=None):
    paths = {"registry": Path(registry), "hp_obo": Path(obo),
             "genes_to_phenotype": Path(g2p), "phenotype_hpoa": Path(hpoa)}
    actual = {k: digest(v) for k, v in paths.items()}
    if strict and actual != PINNED:
        raise ValueError(f"Unexpected pinned source hash(es): "
                         f"{[k for k in PINNED if actual[k] != PINNED[k]]}")
    upstream = verify_manifest(source)
    reg = list(read_tsv(registry, {"hgnc_id", "approved_hgnc_symbol"}))
    genes = {r["hgnc_id"]: r["approved_hgnc_symbol"] for r in reg}
    if len(reg) != 662 or len(genes) != 662:
        raise ValueError("Frozen registry 662-gene identity check failed")
    terms, alt = parse_obo(obo)
    members, ancestors = classification(terms, alt)

    projections = {}
    for p in read_tsv(Path(source) / "gene_disease_hpo_discovery_projections.tsv",
                      PROJ_REQUIRED):
        if p["gene_id"] not in genes:
            raise ValueError("Source projection has gene outside frozen registry")
        if p["gene_symbol"] != genes[p["gene_id"]]:
            raise ValueError("Gene symbol differs from frozen registry")
        if p["projection_role"] != "disease_mediated_discovery_only":
            raise ValueError("Source projection role broadened")
        h = alt.get(p["phenotype_id"], p["phenotype_id"])
        if h not in members:
            continue
        if p["projection_id"] in projections:
            raise ValueError("Repeated source projection ID")
        projections[p["projection_id"]] = {
            **p, "resolved_hpo_id": h,
            "structural_membership_route": members[h]["membership_route"],
        }

    observations = []
    seen_evidence = set()
    for e in read_tsv(Path(source) / "original_hpoa_observations.tsv",
                      OBS_REQUIRED):
        p = projections.get(e["projection_id"])
        if p is None:
            continue
        if (e["source_claim_id"] != p["source_claim_id"]
            or e["original_subject"] != p["disease_id"]
            or e["original_object"] != p["phenotype_id"]
            or e["claim_polarity"] != p["claim_polarity"]):
            raise ValueError("Original disease-subject/source identity mismatch")
        if e["evidence_id"] in seen_evidence:
            raise ValueError("Duplicated original evidence ID")
        seen_evidence.add(e["evidence_id"])
        observations.append({
            **e, "resolved_hpo_id": p["resolved_hpo_id"],
            "structural_membership_route": p["structural_membership_route"],
            "developmental_onset_evidence": (
                "source_onset_reported" if e["onset"].strip()
                else "source_onset_unspecified"
            ),
            "developmental_onset_inferred": "no",
        })
    observations.sort(key=lambda e: (e["projection_id"], e["evidence_id"]))
    if len(observations) != sum(int(p["hpoa_evidence_links"]) for p in
                                projections.values()):
        raise ValueError("Source evidence link conservation failed")

    # A disease-mediated source annotation without curator negation is retained
    # as annotation coverage. 0/N and unreported frequencies remain distinct.
    eligible = {pid for pid, p in projections.items()
                if p["claim_polarity"] == "not_negated"}
    morphology = {pid for pid in eligible
                  if ROOT in ancestors(projections[pid]["resolved_hpo_id"])}
    exceptions = {pid for pid in eligible
                  if projections[pid]["resolved_hpo_id"] in APPROVED}
    extra = exceptions - morphology
    union = morphology | exceptions
    groups = {"morphology": morphology, "approved_exceptions": exceptions,
              "added_exceptions_only": extra, "union": union}
    metrics = {k: distinct_keys(projections, observations, v)
               for k, v in groups.items()}
    metrics["net_new_vs_morphology"] = {
        field: metrics["union"][field] - metrics["morphology"][field]
        for field in metrics["union"]
    }
    cols = ("scope", "genes", "diseases", "hpo_terms", "source_claims",
            "original_source_rows", "original_evidence_links",
            "positive_source_rows")
    coverage = [dict(scope=scope, **{key: len(value)
                                     for key, value in values.items()})
                for scope, values in metrics.items()]

    decisions = []
    for hpo_id, label in sorted({**APPROVED, **DEFERRED}.items()):
        t = terms[hpo_id]
        decisions.append({
            "hpo_id": hpo_id, "pinned_hpo_label": t["name"],
            "approved_label": label,
            "decision": ("approved_structural_exception" if hpo_id in APPROVED
                         else "deferred_for_explicit_exception"),
            "in_native_morphology_subtree":
                str(ROOT in ancestors(hpo_id)).lower(),
            "selected_by_native_ancestry":
                str(ROOT in ancestors(hpo_id)).lower(),
            "selected_by_curated_exception": str(hpo_id in APPROVED).lower(),
            "native_is_a_parents": ";".join(t["parents"]),
            "source_release": RELEASE, "decision_url": DECISION_URL,
            "independent_review_status": "awaiting_Agent_2",
        })

    # Select source-specific examples without creating clinical observations.
    examples = []
    for symbol in ("CIC", "LZTR1"):
        candidates = [
            e for e in observations
            if e["projection_id"] in union
            and projections[e["projection_id"]]["gene_symbol"] == symbol
        ]
        candidates.sort(key=lambda e: (
            e["resolved_hpo_id"] not in APPROVED,
            e["original_subject"], e["source_row_id"], e["evidence_id"]
        ))
        for e in candidates[:5]:
            examples.append({
                "gene_symbol": symbol,
                "gene_id": projections[e["projection_id"]]["gene_id"],
                "disease_id": e["original_subject"],
                "original_hpo_id": e["original_object"],
                "canonical_hpo_id": e["resolved_hpo_id"],
                "hpo_label": terms[e["resolved_hpo_id"]]["name"],
                "membership_route": e["structural_membership_route"],
                "original_source_row": e["source_row_id"],
                "original_reference": e.get("original_reference", ""),
                "source_frequency": e.get("frequency", ""),
                "source_qualifier": e.get("qualifier", ""),
                "source_onset": e["onset"],
                "onset_evidence": e["developmental_onset_evidence"],
                "source_claim_id": e["source_claim_id"],
                "source_scope": "HPOA_disease_phenotype_discovery",
            })
        if not candidates:
            examples.append({
                "gene_symbol": symbol, "gene_id": "", "disease_id": "",
                "original_hpo_id": "", "canonical_hpo_id": "",
                "hpo_label": "", "membership_route": "", "original_source_row": "",
                "original_reference": "", "source_frequency": "",
                "source_qualifier": "", "source_onset": "",
                "onset_evidence": "no_matching_source_annotation",
                "source_claim_id": "", "source_scope": "none_in_union",
            })
    extra_count = Counter(e["evidence_outcome"] for e in observations
                          if e["projection_id"] in union)
    onset_unspecified = {
        (e["source_resource"], e["source_release"], e["source_row_id"])
        for e in observations
        if e["projection_id"] in union and not e["onset"].strip()
    }
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"Refusing to replace versioned results: {out}")
    out.mkdir(parents=True)
    membership_rows = [members[i] for i in sorted(members)]
    selected_projections = [projections[i] for i in sorted(projections)]
    outputs = {
        "structural_membership.tsv": membership_rows,
        "selected_gene_disease_hpo_projections.tsv": selected_projections,
        "selected_original_hpoa_observations.tsv": observations,
        "coverage_summary.tsv": coverage,
        "exception_decisions.tsv": decisions,
        "source_examples.tsv": examples,
    }
    for filename, rows in outputs.items():
        if not rows:
            raise ValueError(f"Empty output: {filename}")
        write_tsv(out / filename, rows, tuple(rows[0].keys()))
    if commit is None:
        run = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=False)
        commit = run.stdout.strip() if run.returncode == 0 else "not_available"
    manifest = {
        "analysis": "STENOSIS-001_structural_coverage_v01",
        "status": "Agent_1_implementation_pending_independent_review",
        "decision_url": DECISION_URL,
        "hpo_release": RELEASE,
        "morphology_root": ROOT,
        "morphology_root_included": True,
        "approved_exception_ids": sorted(APPROVED),
        "deferred_exception_ids": sorted(DEFERRED),
        "native_ontology_edited": False,
        "patient_developmental_onset_inferred": False,
        "disease_mediated_gene_phenotype_promotions": 0,
        "frozen_registry_genes": len(genes),
        "input_sha256": actual,
        "upstream_sha256": upstream,
        "upstream_manifest_sha256": digest(Path(source) / "manifest.json"),
        "script_sha256": digest(Path(__file__)),
        "git_commit": commit,
        "output_counts": {r["scope"]: {k: r[k] for k in cols if k != "scope"}
                          for r in coverage},
        "structural_membership_count": len(members),
        "approved_exception_membership_count": len(APPROVED),
        "source_evidence_outcomes_in_union": dict(sorted(extra_count.items())),
        "union_source_rows_onset_unspecified": len(onset_unspecified),
        "source_scope": "pinned_HPOA_disease_phenotype_and_gene_discovery_only",
        "review_archive": "STENOSIS-001_review_v01.zip",
        "review_status": "Agent_2_not_yet_performed",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    full_files = sorted([*outputs, "manifest.json"])
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(out / f)}  {f}\n" for f in full_files),
        encoding="utf-8"
    )
    review = ["manifest.json", "coverage_summary.tsv",
              "exception_decisions.tsv", "source_examples.tsv"]
    (out / "review_SHA256SUMS.txt").write_text(
        "".join(f"{digest(out / f)}  {f}\n" for f in review),
        encoding="utf-8"
    )
    zip_review(out, review + ["review_SHA256SUMS.txt"])
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    base = Path("scripts/phenotypes/gene_pilot")
    p.add_argument("--registry", type=Path,
                   default=Path("data/releases/2026.09.08/genes.tsv"))
    p.add_argument("--obo", type=Path, default=base / "inputs/hp.obo")
    p.add_argument("--g2p", type=Path,
                   default=base / "inputs/genes_to_phenotype.txt")
    p.add_argument("--hpoa", type=Path,
                   default=base / "inputs/phenotype.hpoa")
    p.add_argument("--source", type=Path,
                   default=Path("results/phenotypes/hpo_two_level_projection_v01"))
    p.add_argument("--out", type=Path,
                   default=Path("results/phenotypes/structural_coverage_stenosis_v01"))
    a = p.parse_args()
    result = analyze(a.registry, a.obo, a.g2p, a.hpoa,
                     a.source, a.out)
    print(json.dumps({"output": str(a.out),
                      "coverage": result["output_counts"],
                      "review_zip_sha256":
                      (a.out / "review_bundle.sha256").read_text().strip()},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
