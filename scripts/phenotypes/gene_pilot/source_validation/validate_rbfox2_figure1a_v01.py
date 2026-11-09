#!/usr/bin/env python3
"""Check RBFOX2 Figure 1A transcription census and unresolved identity flags."""
import argparse
import json
from collections import Counter
from pathlib import Path

FILE = Path(__file__).with_name("RBFOX2_Sauvestre2025_Figure1A_33_source_records_v01.json")
SOURCE_PDF_SHA = "9e46dd253a90184a8aaaf864925cf2673d770fe490d7c4f943fa43583e0b417d"
DELETION = "chr22:33,519,384-36,552,435"
COUNTS = {
    "new_cases": 19, "historical_cases": 14,
    "HLHS": 10, "CoA": 10, "DORV": 4, "VSD": 8,
    "ASD": 6, "AorticValve": 6, "MitralValve": 7, "TOF": 1,
}

def verify(data):
    if data["source_pdf_sha256"] != SOURCE_PDF_SHA or data["reference_genome"] != "hg38":
        raise ValueError("Source identity or genome build mismatch")
    if data["acceptance_state"] != "no_new_biological_acceptance":
        raise ValueError("Unapproved case promotion")
    people = data["new_cohort"]
    history = data["previously_reported"]
    if set(x["id"] for x in people) != {f"P{i}" for i in range(1, 20)}:
        raise ValueError("New study case identifiers are incomplete")
    if set(x["id"] for x in history) != {f"R{i}" for i in range(20, 34)}:
        raise ValueError("Historical source identifiers are incomplete")
    if len(set(x["id"] for x in people + history)) != 33:
        raise ValueError("Repeated Figure 1A identifiers")
    def count(label):
        if label == "HLHS":
            return sum(p["hlhs"] for p in people)
        if label == "CoA":
            return sum(p["coarctation"] for p in people)
        if label == "DORV":
            return sum(p["dorv"] for p in people)
        if label in ("VSD", "ASD"):
            return sum(label in (p["septal"] or "") for p in people)
        if label == "AorticValve":
            return sum("aortic" in (p["left_valve"] or "") for p in people)
        if label == "MitralValve":
            return sum("mitral" in (p["left_valve"] or "") for p in people)
        if label == "TOF":
            return sum(p["other_cardiac"] == "TOF" for p in people)
        raise ValueError(label)
    computed = {"new_cases": len(people), "historical_cases": len(history)}
    for key in COUNTS:
        if key not in computed:
            computed[key] = count(key)
    if computed != COUNTS or data["cohort_counts"] != COUNTS:
        raise ValueError("Figure cohort phenotype counts differ from source")
    byp = {p["id"]: p for p in people}
    byr = {p["id"]: p for p in history}
    if (byp["P12"]["status"] != "no_recorded_cardiac_feature" or
        any([byp["P12"]["hlhs"], byp["P12"]["dorv"], byp["P12"]["coarctation"],
             byp["P12"]["septal"], byp["P12"]["left_valve"], byp["P12"]["other_cardiac"]])):
        raise ValueError("Unmarked carrier P12 incorrectly classified")
    if (byp["P18"]["status"] != "possible_duplicate_of_R24_hold" or
        byr["R24"]["status"] != "possible_duplicate_of_P18_hold" or
        DELETION not in byp["P18"]["source_variant_text"] or
        DELETION not in byr["R24"]["variant_source_text"]):
        raise ValueError("P18 and R24 shared-coordinate identity flag missing")
    if (byp["P17"]["status"] != "published_intragenic_label_questioned" or
        "intragenic del 3 Mb" not in byp["P17"]["source_variant_text"]):
        raise ValueError("P17 original deletion label lost")
    if any(byr[f"R{i}"]["cardiac_status"] != "cardiac NR" for i in range(30, 34)):
        raise ValueError("R30 to R33 not-reported cardiac classification altered")
    if (byp["P7"]["source_variant_text"] != "c.352C>T p.Gln118*" or
        data["reference_transcript"] != "NM_001349999.2"):
        raise ValueError("Gene/transcript-specific variant key unsafe")
    if Counter(p["inheritance"] for p in people) != Counter(
        {"De novo": 8, "Paternal": 3, "Maternal": 4, "NA": 4}
    ):
        raise ValueError("Inheritance count mismatch")
    return {"status": "passed", "new_records": len(people),
            "historical_records": len(history), "cardiac_feature_counts": computed,
            "biologically_accepted_new_cases": 0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=FILE)
    args = parser.parse_args()
    print(json.dumps(verify(json.loads(args.data.read_text(encoding="utf-8"))), sort_keys=True))

if __name__ == "__main__":
    main()
