#!/usr/bin/env python3
"""Verify ROCK2 ledger fields directly against pinned original published source files.

This is an independent read-only source comparison, complementary to the
approved-observation ledger's own fixed-value mutation guards.
"""
import argparse
import csv
import hashlib
import json
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

JIN_S1_SHA256 = "8089f313183d025f0ad9d5e58d554c5740a15dfb53172492cd03a8c6d3fe03ee"
SEVIM_S2_XLSX_SHA256 = "1ee89cc19b7e88182e5c039e5a5621f6e488a3efaf9342d5cba63381362d9ab9"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def require_hash(path, expected):
    if sha256(path) != expected:
        raise ValueError("Source checksum mismatch: " + str(path))

def read_jin_s1(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        title = next(f).strip()
        if "Phenotypes for each CHD proband" not in title:
            raise ValueError("Unexpected Jin S1 title")
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 2871:
        raise ValueError("Jin S1 census differs from the pinned 2,871 probands")
    ids = [r["Blinded ID"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Jin S1 duplicate blinded ID")
    return {r["Blinded ID"]: r for r in rows}

def xlsx_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.findall(".//x:t", NS))
            for si in root.findall("x:si", NS)]

def cell_col(cell_ref):
    match = re.match(r"^([A-Z]+)[0-9]+$", cell_ref)
    if match is None:
        raise ValueError("Unexpected XLSX cell reference " + cell_ref)
    idx = 0
    for ch in match.group(1):
        idx = idx * 26 + ord(ch) - 64
    return idx - 1

def xlsx_rows(xml_bytes, shared):
    root = ET.fromstring(xml_bytes)
    out = {}
    for row in root.findall(".//x:sheetData/x:row", NS):
        fields = {}
        for cell in row.findall("x:c", NS):
            value = cell.findtext("x:v", namespaces=NS)
            if cell.attrib.get("t") == "s":
                value = shared[int(value)]
            elif cell.attrib.get("t") == "inlineStr":
                value = "".join(x.text or "" for x in cell.findall(".//x:t", NS))
            fields[cell_col(cell.attrib["r"])] = value or ""
        out[int(row.attrib["r"])] = fields
    return out

def read_sevim_s2_xlsx(path):
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = workbook.findall(".//x:sheet", NS)
        target = next((x for x in sheets if x.attrib.get("name") == "S2"), None)
        if target is None:
            raise ValueError("No original S2 sheet")
        rid = target.attrib["{" + NS["r"] + "}id"]
        relroot = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel = next((x for x in relroot if x.attrib.get("Id") == rid), None)
        if rel is None:
            raise ValueError("S2 worksheet relationship missing")
        sheet_path = rel.attrib["Target"]
        if sheet_path.startswith("/"):
            sheet_path = sheet_path.lstrip("/")
        elif not sheet_path.startswith("xl/"):
            sheet_path = posixpath.normpath(posixpath.join("xl", sheet_path))
        rows = xlsx_rows(z.read(sheet_path), xlsx_strings(z))
    header = rows.get(2)
    if not header:
        raise ValueError("S2 source header is missing")
    names = {i: value for i, value in header.items() if value}
    needed = {"CHROM", "POS", "REF", "ALT", "Gene", "AA change",
              "Blinded ID", "Cardiac Category", "EM", "NDD",
              "Family history of CHD", "CADD_Score"}
    if not needed.issubset(set(names.values())):
        raise ValueError("Missing original S2 source columns")
    return [
        {names[i]: value for i, value in row.items() if i in names}
        for key, row in rows.items() if key > 2
    ]

def verify_source_files(observations, s1_path, s2_path,
                        expected_s1_sha=JIN_S1_SHA256,
                        expected_s2_sha=SEVIM_S2_XLSX_SHA256):
    require_hash(s1_path, expected_s1_sha)
    require_hash(s2_path, expected_s2_sha)
    s1 = read_jin_s1(s1_path)
    s2_rows = read_sevim_s2_xlsx(s2_path)
    candidates = [r for r in s2_rows if r.get("Gene") == "ROCK2"]
    if len(candidates) != 2:
        raise ValueError("ROCK2 source row count mismatch")
    s2 = {r["Blinded ID"]: r for r in candidates}
    if set(s2) != {"1-11926", "1-13760"}:
        raise ValueError("ROCK2 source patient IDs mismatch")
    for record in observations:
        if record["gene_symbol"] != "ROCK2":
            continue
        pid = record["source_patient_id"]
        clinical = s1[pid]
        variant = s2[pid]
        meta = record["source_metadata"]
        if clinical["Cardiac Diagnoses"] != record["original_diagnosis_field"]:
            raise ValueError("Original Jin S1 diagnosis field changed: " + pid)
        if (clinical["Cohort"], clinical["Sample Type"],
            clinical["Cardiac Category"], clinical["EM"], clinical["NDD"]) != (
            meta["cohort"], meta["sample_type"], meta["cardiac_category"],
            meta["extracardiac_manifestations"].split(",")[0],
            meta["neurodevelopmental_disorder"].split(",")[0]):
            raise ValueError("Original Jin S1 subject clinical context changed: " + pid)
        if (variant["CHROM"], variant["POS"], variant["REF"], variant["ALT"],
            variant["Gene"], variant["AA change"], variant["Cardiac Category"],
            variant["EM"], variant["NDD"], variant["Family history of CHD"]) != (
            record["original_chromosome"], str(record["original_position"]),
            record["original_ref"], record["original_alt"], "ROCK2",
            record["protein_variant_original"], meta["cardiac_category"],
            "Yes", "No", meta["family_history_chd"]):
            raise ValueError("Original Sevim S2 variant fields changed: " + pid)
        if float(variant["CADD_Score"]) != meta["source_cadd_score"]:
            raise ValueError("Original S2 CADD mismatch: " + pid)
        if record["genome_build"] is not None:
            raise ValueError("Source S2 does not name genomic build: " + pid)
    return {"status": "source_files_verified", "jin_s1_sha256": expected_s1_sha,
            "sevim_s2_xlsx_sha256": expected_s2_sha,
            "jin_unique_patients": len(s1), "rock2_case_rows_reconciled": 2}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--s1-tsv", type=Path, required=True)
    ap.add_argument("--s2-xlsx", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, default=Path(__file__).with_name("approved_clinical_observations_v01.json"))
    args = ap.parse_args()
    print(json.dumps(verify_source_files(json.loads(args.ledger.read_text(encoding="utf-8")),
                                         args.s1_tsv, args.s2_xlsx), sort_keys=True))

if __name__ == "__main__":
    main()
