"""Synthetic direct original-source reconciliation test for the ROCK2 ledger."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_original_sources_v01 import verify_source_files

BASE = Path(__file__).resolve().parent
WB = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture(root, observations):
    s1 = root / "original_jin_s1.tsv"
    s2 = root / "original_sevim_s2.xlsx"
    fields = ["Blinded ID", "Cohort", "Sample Type", "Cardiac Category",
              "Cardiac Diagnoses", "EM", "NDD"]
    by_pid = {row["source_patient_id"]: row for row in observations
              if row["gene_symbol"] == "ROCK2"}
    with s1.open("w", encoding="utf-8", newline="") as f:
        f.write("Supplementary Data Set 1: Phenotypes for each CHD proband\r\n")
        wr = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\r\n")
        wr.writeheader()
        for i in range(2871):
            pid = {2684:"1-11926",2737:"1-13760"}.get(i, f"faux-{i:04d}")
            if pid in by_pid:
                r = by_pid[pid]
                wr.writerow({"Blinded ID":pid,"Cohort":"PCGC","Sample Type":"Trio",
                             "Cardiac Category":r["source_metadata"]["cardiac_category"],
                             "Cardiac Diagnoses":r["original_diagnosis_field"],
                             "EM":"Yes","NDD":"No"})
            else:
                wr.writerow({"Blinded ID":pid,"Cohort":"PCGC","Sample Type":"Trio",
                             "Cardiac Category":"other","Cardiac Diagnoses":"faux",
                             "EM":"No","NDD":"No"})
    cols = ["CHROM","POS","REF","ALT","Gene","AA change","Blinded ID",
            "Cardiac Category","EM","NDD","Family history of CHD","CADD_Score"]
    def col(index):
        return chr(65 + index)
    def xmlrow(number, vals):
        cells=[]
        for i, val in enumerate(vals):
            ref=f"{col(i)}{number}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>')
        return f'<row r="{number}">{"".join(cells)}</row>'
    source_rows = [xmlrow(2, cols)]
    for pos, pid in ((245,"1-11926"),(246,"1-13760")):
        o=by_pid[pid];m=o["source_metadata"]
        source_rows.append(xmlrow(pos, [
            o["original_chromosome"],o["original_position"],o["original_ref"],
            o["original_alt"],"ROCK2",o["protein_variant_original"],pid,
            m["cardiac_category"],"Yes","No",m["family_history_chd"],m["source_cadd_score"],
        ]))
    body = f'<worksheet xmlns="{WB}"><sheetData>{"".join(source_rows)}</sheetData></worksheet>'
    workbook = (f'<workbook xmlns="{WB}" xmlns:r="{REL}">'
                '<sheets><sheet name="S2" sheetId="2" r:id="rId2"/></sheets></workbook>')
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
            ' Target="worksheets/sheet2.xml"/></Relationships>')
    with zipfile.ZipFile(s2,"w") as z:
        z.writestr("xl/workbook.xml",workbook)
        z.writestr("xl/_rels/workbook.xml.rels",rels)
        z.writestr("xl/worksheets/sheet2.xml",body)
    return s1,s2

class SourceComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = json.loads((BASE/"approved_clinical_observations_v01.json").read_text())

    def test_exact_source_rows_reconcile(self):
        with tempfile.TemporaryDirectory() as temp:
            s1,s2 = fixture(Path(temp),self.observations)
            result = verify_source_files(self.observations,s1,s2,
                                         expected_s1_sha=digest(s1),
                                         expected_s2_sha=digest(s2))
            self.assertEqual(result["rock2_case_rows_reconciled"],2)
            self.assertEqual(result["jin_unique_patients"],2871)

    def test_pin_failure_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            s1,s2 = fixture(Path(temp),self.observations)
            with self.assertRaisesRegex(ValueError,"Source checksum mismatch"):
                verify_source_files(self.observations,s1,s2,
                                    expected_s1_sha="0"*64,
                                    expected_s2_sha=digest(s2))

    def test_original_diagnosis_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            s1,s2 = fixture(Path(temp),self.observations)
            mutated = json.loads(json.dumps(self.observations))
            for row in mutated:
                if row["observation_id"] == "SV-004a":
                    row["original_diagnosis_field"] = row["original_diagnosis_field"].rstrip()
            with self.assertRaisesRegex(ValueError,"Jin S1 diagnosis field"):
                verify_source_files(mutated,s1,s2,
                                    expected_s1_sha=digest(s1),
                                    expected_s2_sha=digest(s2))

if __name__ == "__main__":
    unittest.main()
