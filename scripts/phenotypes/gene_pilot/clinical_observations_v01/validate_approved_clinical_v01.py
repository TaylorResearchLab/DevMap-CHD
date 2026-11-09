#!/usr/bin/env python3
"""Read-only integrity checks for DevMap approved clinical observations v01."""
import argparse
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
FILES = {
    "observations": "approved_clinical_observations_v01.json",
    "mappings": "hpo_mapping_candidates_v01.json",
    "functional": "functional_evidence_v01.json",
}
SOURCE_DX = {
    "SV-003a": ("MESP1", "p.E104K", "TOF"),
    "SV-003b": ("MESP1", "p.L120P", "TOF"),
    "SV-003c": ("MESP1", "p.L147Pfs*9", "cVSD"),
    "SV-004a": ("ROCK2", "p.S39F", "AORTIC STENOSIS | BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE | TETRALOGY OF FALLOT "),
    "SV-004b": ("ROCK2", "p.D255G", "PATENT DUCTUS ARTERIOSUS "),
}
EXPECTED_TERMS = {
    "SV-003a": [("TOF", "HP:0001636")],
    "SV-003b": [("TOF", "HP:0001636")],
    "SV-003c": [("cVSD", "HP:0001629")],
    "SV-004a": [
        ("AORTIC STENOSIS", "HP:0001650"),
        ("BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE", "HP:0001647"),
        ("TETRALOGY OF FALLOT", "HP:0001636"),
    ],
    "SV-004b": [("PATENT DUCTUS ARTERIOSUS", "HP:0001643")],
}
EXPECTED_ASSAYS = {
    ("SV-003a", "luciferase_reporter"): (0.08, 0.04),
    ("SV-003a", "two_hybrid"): (0.56, 0.08),
    ("SV-003b", "luciferase_reporter"): (0.06, 0.03),
    ("SV-003b", "two_hybrid"): (0.32, 0.06),
    ("SV-003c", "luciferase_reporter"): (0.03, 0.02),
    ("SV-003c", "two_hybrid"): (0.05, 0.01),
}

def load_data(base=BASE):
    return {k: json.loads((Path(base) / filename).read_text(encoding="utf-8"))
            for k, filename in FILES.items()}

def verify(data):
    observations, mappings, functional = (data[k] for k in FILES)
    if not all(isinstance(x, list) for x in (observations, mappings, functional)):
        raise ValueError("All inputs must be JSON arrays")
    ids = [r["observation_id"] for r in observations]
    if len(ids) != len(set(ids)) or set(ids) != set(SOURCE_DX):
        raise ValueError("Observation census/identity mismatch")
    by_id = {r["observation_id"]: r for r in observations}
    for ident, (gene, variant, diagnosis) in SOURCE_DX.items():
        row = by_id[ident]
        if (row["gene_symbol"], row["protein_variant_original"], row["original_diagnosis_field"]) != (gene, variant, diagnosis):
            raise ValueError("Original clinical diagnosis or variant changed: " + ident)
        if (row["record_class"] != "accepted_patient_variant_clinical_coobservation"
            or row["causality_status"] != "not_adjudicated"):
            raise ValueError("Claim scope changed: " + ident)
        if (row["decision_id"] != ident[:6] or row["decision_date"] != "2026-11-08"
            or row["disposition"] != "accepted_at_original_clinical_observation_scope"):
            raise ValueError("Decision changed: " + ident)
        if gene == "ROCK2":
            patient = {"SV-004a": "1-11926", "SV-004b": "1-13760"}[ident]
            if (row["source_patient_id"] != patient
                or row["source_patient_key_kind"] != "published_blinded_id"
                or row["genome_build"] is not None
                or row["clinical_primary_source"]["pmid"] != "28991257"
                or row["variant_source"]["pmid"] != "31941532"
                or row["variant_source"]["refers_to_same_patient"] is not True):
                raise ValueError("PCGC lineage or genomic build changed: " + ident)
        else:
            if (row["source_patient_id"] is not None
                or row["source_patient_key_kind"] != "internal_variant_scoped_case_reference"
                or row["clinical_primary_source"]["pmid"] != "26694203"):
                raise ValueError("Werner source identity changed: " + ident)
    actual = Counter((m["observation_id"], m["original_phenotype_text"], m["hpo_id"]) for m in mappings)
    expected = Counter((i, t, h) for i, terms in EXPECTED_TERMS.items() for t, h in terms)
    if actual != expected:
        raise ValueError("HPO mapping census or original phenotype text changed")
    for row in mappings:
        if (row["hpo_source_release"] != "v2026-09-01" or
            row["mapping_record_status"] != "independent_reviewer_checked_not_a_replacement_for_source_text"):
            raise ValueError("HPO mapping provenance or status changed")
        if row["observation_id"] == "SV-004a" and row["original_phenotype_text"] == "AORTIC STENOSIS":
            if row["mapping_kind"] != "flagged_candidate_adds_valvar_level":
                raise ValueError("Unspecified aortic stenosis incorrectly promoted to valvar")
        elif row["observation_id"] == "SV-003c":
            if row["mapping_kind"] != "broader_than_source_subtype":
                raise ValueError("Conoventricular subtype flag missing")
    keys = [(f["observation_id"], f["assay"]) for f in functional]
    if len(keys) != len(set(keys)) or set(keys) != set(EXPECTED_ASSAYS):
        raise ValueError("Functional assay census altered")
    for row in functional:
        key = (row["observation_id"], row["assay"])
        if ((row["reported_value"], row["reported_plus_minus"]) != EXPECTED_ASSAYS[key]
            or row["source_pmid"] != "26694203"
            or row["evidence_type"] != "experimental_functional_observation"):
            raise ValueError("Experimental evidence altered: " + str(key))
    return {
        "status": "passed", "approved_clinical_cases": len(observations),
        "hpo_mapping_records": len(mappings),
        "functional_measurement_records": len(functional),
        "direct_causal_pars_issued": 0,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, default=BASE)
    args = p.parse_args()
    print(json.dumps(verify(load_data(args.input_dir)), sort_keys=True))

if __name__ == "__main__":
    main()
