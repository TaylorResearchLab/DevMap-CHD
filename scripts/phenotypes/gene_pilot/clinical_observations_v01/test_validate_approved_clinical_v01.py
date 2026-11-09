"""Synthetic mutation guards for accepted clinical observations v01."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_approved_clinical_v01 import load_data, verify

class TestClinicalObservations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_approved_ledger_counts(self):
        self.assertEqual(verify(self.data), {
            "status": "passed", "approved_clinical_cases": 5,
            "hpo_mapping_records": 7, "functional_measurement_records": 6,
            "direct_causal_pars_issued": 0, "secondary_curator_assignments": 2})

    def test_verbatim_source_trailing_space(self):
        bad = copy.deepcopy(self.data)
        bad["observations"][3]["original_diagnosis_field"] = bad["observations"][3]["original_diagnosis_field"].rstrip()
        with self.assertRaisesRegex(ValueError, "Original clinical diagnosis"):
            verify(bad)

    def test_duplicate_patient_record(self):
        bad = copy.deepcopy(self.data)
        bad["observations"].append(copy.deepcopy(bad["observations"][4]))
        with self.assertRaisesRegex(ValueError, "census/identity"):
            verify(bad)

    def test_causal_promotion_disallowed(self):
        bad = copy.deepcopy(self.data)
        bad["observations"][0]["causality_status"] = "causal"
        with self.assertRaisesRegex(ValueError, "Claim scope"):
            verify(bad)

    def test_aortic_stenosis_valvar_flag_preserved(self):
        bad = copy.deepcopy(self.data)
        for row in bad["mappings"]:
            if row["observation_id"] == "SV-004a" and row["original_phenotype_text"] == "AORTIC STENOSIS":
                row["mapping_kind"] = "source_term_normalization"
        with self.assertRaisesRegex(ValueError, "aortic stenosis"):
            verify(bad)

    def test_conoventricular_subtype_preserved(self):
        bad = copy.deepcopy(self.data)
        for row in bad["mappings"]:
            if row["observation_id"] == "SV-003c":
                row["mapping_kind"] = "source_term_normalization"
        with self.assertRaisesRegex(ValueError, "Conoventricular"):
            verify(bad)


    def test_mesp1_genomic_build_and_cDNA_preserved(self):
        bad = copy.deepcopy(self.data)
        bad["observations"][0]["genome_build"] = None
        with self.assertRaisesRegex(ValueError, "Werner Table 2"):
            verify(bad)

    def test_mesp1_parental_source_genotypes_preserved(self):
        bad = copy.deepcopy(self.data)
        bad["observations"][1]["source_metadata"]["parental_genotypes"]["mother"] = "Carrier"
        with self.assertRaisesRegex(ValueError, "Werner Table 2"):
            verify(bad)

    def test_secondary_curator_is_same_original_patient(self):
        bad = copy.deepcopy(self.data)
        bad["secondary"][0]["original_primary_patient_id"] = "new_patient"
        with self.assertRaisesRegex(ValueError, "Secondary curator"):
            verify(bad)

    def test_functional_measurement_change_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["functional"][0]["reported_value"] = 1.0
        with self.assertRaisesRegex(ValueError, "Experimental evidence"):
            verify(bad)

if __name__ == "__main__":
    unittest.main()
