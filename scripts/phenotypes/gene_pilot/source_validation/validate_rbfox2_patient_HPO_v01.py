#!/usr/bin/env python3
"""Validate RBFOX2 patient-specific source phenotype and candidate HPO projection."""
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "RBFOX2_Sauvestre2025_Figure1A_33_source_records_v01.json"
MAPS = HERE / "RBFOX2_Sauvestre2025_Figure1A_patient_HPO_candidates_v01.json"
SOURCE_COUNTS = {"HLHS": 10, "CoA": 10, "DORV": 4, "VSD": 8, "ASD": 6, "TOF": 1}
HPO_SOURCE_TERM_CANDIDATES = {
    "CoA": "HP:0001680", "DORV": "HP:0001719",
    "VSD": "HP:0001629", "ASD": "HP:0001631",
    "TOF": "HP:0001636", "Large PDA": "HP:0001643",
    "Mitral stenosis": "HP:0001718", "Mitral atresia": "HP:0011560",
    "LV non-compaction": "HP:0030682",
    "HLHS": "HP:0004383",
    "Pulmonary valve stenosis": "HP:0001642",
    "Abnormal tricuspid valve": "HP:0001702",
}

def expected_source_feature_tokens(p):
    terms = []
    if p["hlhs"]:
        terms.append(("HLHS", "HLHS"))
    if p["dorv"]:
        terms.append(("DORV", "DORV"))
    for term in ("VSD", "ASD"):
        if term in (p["septal"] or ""):
            terms.append(("Septal", term))
    if p["coarctation"]:
        terms.append(("CoA", "CoA"))
    if p["left_valve"]:
        valve = p["left_valve"].lower()
        if "mitral stenosis" in valve:
            terms.append(("Left valve", "Mitral stenosis"))
        elif "mitral atresia" in valve:
            terms.append(("Left valve", "Mitral atresia"))
        elif "mitral" in valve:
            terms.append(("Left valve", "mitral valve category"))
        if "aortic" in valve:
            terms.append(("Left valve", "aortic valve category"))
    if p["other_cardiac"]:
        text = p["other_cardiac"]
        terms.append(("Other cardiac", text))
    return terms

def verify(source, mapping):
    people = source["new_cohort"]
    if len(people) != 19 or source["reference_genome"] != "hg38":
        raise ValueError("RBFOX2 source cohort or genome identity changed")
    if mapping["primary_figure_source_pdf_sha256"] != source["source_pdf_sha256"]:
        raise ValueError("Source PDF identity changed")
    if (mapping["ontology_target"] != "HPO:v2026-09-01" or
        mapping["ontology_readiness"] != "pinned_ontology_mapping_checked_for_nonnull_candidates_some_source_categories_unresolved"):
        raise ValueError("Pinned HPO review status altered")
    records = mapping["source_feature_candidates"]
    by_id = {p["id"]:p for p in people}
    ids = set(by_id)
    source_count = Counter()
    map_count = Counter()
    for person in people:
        for column, term in expected_source_feature_tokens(person):
            source_count[(person["id"], column, term)] += 1
    for r in records:
        key = (r["figure_patient_id"],r["figure_feature_source_column"],r["original_feature_text"])
        map_count[key] += 1
        if r["gene_symbol"] != "RBFOX2" or r["figure_patient_id"] not in ids:
            raise ValueError("Source gene or patient identity mismatch")
        person = by_id[r["figure_patient_id"]]
        if (r["source_variant_text"] != person["source_variant_text"] or
            r["source_variant_reference"] != person["source_variant_reference"]):
            raise ValueError("Original patient variant source join mismatch")
        if r["approval_status"] != "source_lead_unaccepted":
            raise ValueError("Unapproved source feature promoted")
        expected_hpo_check = ("agent2_verified_pinned_hp_obo_v2026_09_01"
                              if r["hpo_candidate"] is not None
                              else "no_candidate_mapping_source_category_unresolved")
        if r["hpo_pinned_release_check"] != expected_hpo_check:
            raise ValueError("Pinned HPO source review status changed")
        term = r["original_feature_text"]
        if term in HPO_SOURCE_TERM_CANDIDATES:
            if r["hpo_candidate"] != HPO_SOURCE_TERM_CANDIDATES[term]:
                raise ValueError("Candidate HPO identifier changed: " + term)
        elif r["hpo_candidate"] is not None:
            raise ValueError("Unresolved HPO term silently mapped: " + term)
        if term == "HLHS":
            if (r["hpo_candidate"] != "HP:0004383" or
                r["mapping_scope"] != "ontology_directed_component_of_reported_HLHS" or
                r.get("component_representation_role") != "component_of_reported_HLHS_not_equivalent_diagnosis"):
                raise ValueError("HLHS HPO component incorrectly equated with original diagnosis")
        if term == "LV non-compaction":
            if (r["mapping_scope"] != "exact_source_morphology_term" or
                r["hpo_candidate"] != "HP:0030682"):
                raise ValueError("LV noncompaction morphology mapping altered")
        if r["figure_patient_id"] == "P18" and r["patient_disposition"] != "held_possible_duplicate_R24":
            raise ValueError("P18 possible duplicate hold removed")
    if map_count != source_count:
        raise ValueError("Source phenotype tokens not conserved")
    stats = mapping["stats"]
    expected = {
        "new_P_cases":19,"candidates":len(records),
        "subjects_with_marked_feature":len({x[0] for x in source_count}),
        "p12_entries":0,
        "hlhs":sum(k[2]=="HLHS" for k in map_count),
        "coa":sum(k[2]=="CoA" for k in map_count),
        "dorv":sum(k[2]=="DORV" for k in map_count),
        "vsd":sum(k[2]=="VSD" for k in map_count),
        "asd":sum(k[2]=="ASD" for k in map_count),
        "tof":sum(k[2]=="TOF" for k in map_count),
        "p18_hold":sum(k[0]=="P18" for k in map_count),
        "pinned_hpo_checked":sum(x["hpo_candidate"] is not None for x in records),
        "unmapped_source_features":sum(x["hpo_candidate"] is None for x in records),
        "ontology_component_HLHS":sum(x["original_feature_text"] == "HLHS" and x["hpo_candidate"] == "HP:0004383" for x in records),
        "exact_morphological_LVNC":sum(x["original_feature_text"] == "LV non-compaction" and x["hpo_candidate"] == "HP:0030682" for x in records),
        "independently_accepted":0
    }
    if (stats != expected or len(records) != 60 or
        stats["pinned_hpo_checked"] != 50 or stats["unmapped_source_features"] != 10 or
        stats["ontology_component_HLHS"] != 10 or stats["exact_morphological_LVNC"] != 2):
        raise ValueError("RBFOX2 mapping summary changed")
    for key, expected_num in SOURCE_COUNTS.items():
        observed = sum(k[2] == key for k in map_count)
        if observed != expected_num:
            raise ValueError("Published phenotype census differs: "+key)
    if sum(k[0]=="P12" for k in map_count) != 0:
        raise ValueError("Unmarked P12 carrier included")
    return {"status":"source_projection_conserved",
            "new_cohort":19,"individuals_with_recorded_features":18,
            "candidate_mappings":len(records),"approved_new_cases":0,
            "pinned_HPO_review":"reviewed_candidates_with_unresolved_source_categories"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--mappings",type=Path,default=MAPS)
    args=p.parse_args()
    source=json.loads(args.source.read_text(encoding="utf-8"))
    mapping=json.loads(args.mappings.read_text(encoding="utf-8"))
    print(json.dumps(verify(source,mapping),sort_keys=True))

if __name__=="__main__":
    main()
