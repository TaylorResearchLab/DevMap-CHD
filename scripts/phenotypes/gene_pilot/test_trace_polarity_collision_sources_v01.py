import csv
import tempfile
import unittest
from pathlib import Path

from audit_candidate_export_gate_v01 import audit
from test_audit_candidate_export_gate_v01 import fixture
from trace_polarity_collision_sources_v01 import trace


def table(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class TestCollisionSourceTrace(unittest.TestCase):
    def test_original_source_fields_and_candidate_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            registry, g2p, hpoa, candidate_dir = fixture(root)
            audit_dir = root / "audit"
            audit(registry, g2p, hpoa, candidate_dir, audit_dir, skip_source_sha=True)
            review_dir = root / "review"
            manifest = trace(candidate_dir, audit_dir, review_dir)
            self.assertEqual(manifest["group_count"], 1)
            self.assertEqual(manifest["candidate_count"], 2)
            self.assertEqual(manifest["evidence_row_count"], 2)
            self.assertEqual(manifest["groups_with_absent_and_present"], 1)
            self.assertEqual(manifest["direct_gene_phenotype_claims_accepted"], 0)
            review_rows = table(review_dir / "polarity_collision_source_rows.tsv")
            self.assertEqual({r["candidate_polarity"] for r in review_rows},
                             {"asserted_absent", "asserted_present"})
            self.assertEqual({r["original_subject"] for r in review_rows}, {"OMIM:111111"})
            self.assertEqual({r["original_object"] for r in review_rows}, {"HP:0000001"})
            self.assertEqual({r["source_evidence_code"] for r in review_rows}, {"PCS"})
            self.assertEqual({r["original_reference"] for r in review_rows}, {"PMID:1234"})
            absent = [r for r in review_rows if r["candidate_polarity"] == "asserted_absent"]
            self.assertEqual(len(absent), 1)
            self.assertEqual(absent[0]["frequency"], "0/19")
            self.assertEqual(absent[0]["polarity_basis"], "zero_numerator")
            self.assertEqual({r["evidence_role"] for r in review_rows},
                             {"disease_phenotype_annotation"})

    def test_tampered_collision_review_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            reg, g2p, hpoa, candidate_dir = fixture(root)
            audit_dir = root / "audit"
            audit(reg, g2p, hpoa, candidate_dir, audit_dir, skip_source_sha=True)
            with (audit_dir / "polarity_identity_collisions.tsv").open("a", encoding="utf-8") as out:
                out.write("tampered\n")
            with self.assertRaisesRegex(ValueError, "Unverified audit source"):
                trace(candidate_dir, audit_dir, root / "review")


if __name__ == "__main__":
    unittest.main()
