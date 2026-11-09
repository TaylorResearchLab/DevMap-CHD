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

    def test_hlhs_syndrome_unresolved(self):
        m=copy.deepcopy(self.mapping)
        next(x for x in m["source_feature_candidates"] if x["original_feature_text"]=="HLHS")["hpo_candidate"]="HP:0004383"
        with self.assertRaisesRegex(ValueError,"Unresolved HPO"):
            verify(self.source,m)

    def test_p12_no_hpo_inference(self):
        m=copy.deepcopy(self.mapping)
        row=copy.deepcopy(m["source_feature_candidates"][0])
        row["figure_patient_id"]="P12"
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
