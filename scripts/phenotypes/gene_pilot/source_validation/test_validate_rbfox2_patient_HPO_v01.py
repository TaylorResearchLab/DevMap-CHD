"""Mutation tests for RBFOX2 per-patient phenotype/source projection."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from validate_rbfox2_patient_HPO_v01 import verify

class TestRBFOX2HPOProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((HERE/"RBFOX2_Sauvestre2025_Figure1A_33_source_records_v01.json").read_text(encoding="utf-8"))
        cls.mapping=json.loads((HERE/"RBFOX2_Sauvestre2025_Figure1A_patient_HPO_candidates_v01.json").read_text(encoding="utf-8"))

    def test_source_token_conservation(self):
        r=verify(self.source,self.mapping)
        self.assertEqual((r["candidate_mappings"],r["individuals_with_recorded_features"]),(60,18))
        self.assertEqual(r["pinned_HPO_review"],"reviewed_candidates_with_unresolved_source_categories")

    def test_hlhs_component_annotation_preserves_original_syndrome(self):
        m=copy.deepcopy(self.mapping)
        row=next(x for x in m["source_feature_candidates"] if x["original_feature_text"]=="HLHS")
        self.assertEqual(row["hpo_candidate"],"HP:0004383")
        self.assertEqual(row["original_feature_text"],"HLHS")
        row["mapping_scope"]="exact_source_term_equivalence"
        with self.assertRaisesRegex(ValueError,"HLHS HPO component"):
            verify(self.source,m)

    def test_hlhs_candidate_cannot_revert_to_unverified(self):
        m=copy.deepcopy(self.mapping)
        row=next(x for x in m["source_feature_candidates"] if x["original_feature_text"]=="HLHS")
        row["hpo_candidate"]=None
        with self.assertRaisesRegex(ValueError,"Pinned HPO|Candidate HPO"):
            verify(self.source,m)

    def test_lv_noncompaction_morphology_not_cardiomyopathy(self):
        m=copy.deepcopy(self.mapping)
        row=next(x for x in m["source_feature_candidates"] if x["original_feature_text"]=="LV non-compaction")
        self.assertEqual(row["hpo_candidate"],"HP:0030682")
        row["hpo_candidate"]="HP:0012817"
        with self.assertRaisesRegex(ValueError,"Candidate HPO"):
            verify(self.source,m)

    def test_p12_no_hpo_inference(self):
        m=copy.deepcopy(self.mapping)
        row=copy.deepcopy(m["source_feature_candidates"][0])
        row["figure_patient_id"]="P12"
        source_p12 = next(x for x in self.source["new_cohort"] if x["id"] == "P12")
        row["source_variant_text"] = source_p12["source_variant_text"]
        row["source_variant_reference"] = source_p12["source_variant_reference"]
        m["source_feature_candidates"].append(row)
        with self.assertRaisesRegex(ValueError,"Source phenotype"):
            verify(self.source,m)

    def test_original_variant_source_conservation(self):
        m=copy.deepcopy(self.mapping)
        m["source_feature_candidates"][0]["source_variant_text"]="c.352C>T p.Q118X MESP1"
        with self.assertRaisesRegex(ValueError,"variant source"):
            verify(self.source,m)

    def test_duplicate_hold_retained(self):
        m=copy.deepcopy(self.mapping)
        next(x for x in m["source_feature_candidates"] if x["figure_patient_id"]=="P18")["patient_disposition"]="accepted"
        with self.assertRaisesRegex(ValueError,"duplicate hold"):
            verify(self.source,m)

    def test_candidate_remains_unaccepted(self):
        m=copy.deepcopy(self.mapping)
        m["source_feature_candidates"][0]["approval_status"]="biologically_accepted"
        with self.assertRaisesRegex(ValueError,"Unapproved"):
            verify(self.source,m)

if __name__=="__main__":
    unittest.main()
