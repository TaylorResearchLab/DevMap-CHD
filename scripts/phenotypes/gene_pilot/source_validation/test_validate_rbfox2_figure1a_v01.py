import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_rbfox2_figure1a_v01 import verify

class Figure1ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE/"RBFOX2_Sauvestre2025_Figure1A_33_source_records_v01.json").read_text())

    def test_census(self):
        r = verify(self.data)
        self.assertEqual((r["new_records"],r["historical_records"]),(19,14))
        self.assertEqual(r["biologically_accepted_new_cases"],0)

    def test_p12_has_no_reported_cardiac_phenotype(self):
        bad = copy.deepcopy(self.data)
        next(p for p in bad["new_cohort"] if p["id"]=="P12")["status"]="source_case_for_deduplicated_review"
        with self.assertRaisesRegex(ValueError,"Unmarked carrier"):
            verify(bad)

    def test_p18_r24_shared_intervals_hold(self):
        bad = copy.deepcopy(self.data)
        next(p for p in bad["previously_reported"] if p["id"]=="R24")["variant_source_text"]="gross del 3 Mb different"
        with self.assertRaisesRegex(ValueError,"shared-coordinate"):
            verify(bad)

    def test_r30_not_reported_is_not_unaffected(self):
        bad = copy.deepcopy(self.data)
        next(p for p in bad["previously_reported"] if p["id"]=="R30")["cardiac_status"]="unaffected"
        with self.assertRaisesRegex(ValueError,"not-reported"):
            verify(bad)

    def test_p17_original_variant_label_retained(self):
        bad = copy.deepcopy(self.data)
        next(p for p in bad["new_cohort"] if p["id"]=="P17")["source_variant_text"]="gross deletion"
        with self.assertRaisesRegex(ValueError,"P17 original"):
            verify(bad)

    def test_familial_variant_reference_includes_gene(self):
        bad = copy.deepcopy(self.data)
        child = next(p for p in bad["new_cohort"] if p["id"] == "P2")
        child["resolved_gene_variant_from_related_case"]["gene"] = "MESP1"
        with self.assertRaisesRegex(ValueError, "familial variant"):
            verify(bad)

    def test_familial_variant_reference_has_no_whitespace(self):
        bad = copy.deepcopy(self.data)
        child = next(p for p in bad["new_cohort"] if p["id"] == "P2")
        child["source_variant_reference"] = " P1"
        with self.assertRaisesRegex(ValueError, "familial variant"):
            verify(bad)

    def test_p7_gene_variant_collision_guard(self):
        bad = copy.deepcopy(self.data)
        next(p for p in bad["new_cohort"] if p["id"]=="P7")["source_variant_text"]="c.352C>T MESP1"
        with self.assertRaisesRegex(ValueError,"variant key"):
            verify(bad)

if __name__=="__main__":
    unittest.main()
