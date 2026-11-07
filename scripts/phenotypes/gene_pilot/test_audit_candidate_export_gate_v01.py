import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from export_gene_phenotype_par import export
from audit_candidate_export_gate_v01 import audit


def read_tsv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fixture(root, malformed=False):
    registry = root / "genes.tsv"
    registry.write_text(
        "hgnc_id\tapproved_hgnc_symbol\n" +
        "".join(f"HGNC:{i+100}\tGENE{i}\n" for i in range(662)),
        encoding="utf-8",
    )
    g2p = root / "genes_to_phenotype.txt"
    g2p.write_text(
        "#ncbi_gene_id\tgene_symbol\thpo_id\tdisease_id\n"
        "1\tGENE0\tHP:0000001\tOMIM:111111\n"
        "2\tGENE1\tHP:0000002\tOMIM:222222\n"
        "3\tLEGACY_SYMBOL\tHP:0000001\tOMIM:111111\n"
        + ("4\tGENE0\tINVALID\tOMIM:111111\n" if malformed else ""),
        encoding="utf-8",
    )
    hpoa = root / "phenotype.hpoa"
    hpoa.write_text(
        "#description: test fixture\n"
        "#database_id\thpo_id\taspect\tfrequency\tqualifier\treference\tevidence\tonset\tsex\tmodifier\n"
        "OMIM:111111\tHP:0000001\tP\t0/19\t\tPMID:1234\tPCS\t\t\t\n"
        "OMIM:111111\tHP:0000001\tP\t12/19\t\tPMID:1234\tPCS\tHP:0003581\t\t\n"
        "OMIM:111111\tHP:0003581\tC\t\t\tPMID:9999\tPCS\t\t\t\n"
        "OMIM:999999\tHP:0000001\tP\t12/19\t\tPMID:1111\tPCS\t\t\t\n",
        encoding="utf-8",
    )
    source_dir = root / "par_candidates_v02"
    export(registry, g2p, hpoa, source_dir, skip_sha=True)
    return registry, g2p, hpoa, source_dir


class TestReadOnlyCandidateIntegrity(unittest.TestCase):
    def test_conservation_polarity_and_explicit_missingness(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            reg, g2p, hpoa, existing = fixture(root)
            result = audit(reg, g2p, hpoa, existing, root / "audit",
                           skip_source_sha=True)
            self.assertTrue(result["gate_passed"])
            self.assertEqual(result["original_candidate_count"], 2)
            self.assertEqual(result["provisional_polarity_collisions_without_polarity"], 1)
            self.assertEqual(result["four_fate_conservation"]["g2p"]["emitted"], 1)
            self.assertEqual(result["four_fate_conservation"]["g2p"]["held"], 2)
            self.assertEqual(result["four_fate_conservation"]["g2p"]["failed"], 0)
            self.assertEqual(result["four_fate_conservation"]["hpoa"]["emitted"], 3)
            self.assertEqual(result["four_fate_conservation"]["hpoa"]["held"], 1)
            self.assertEqual(result["four_fate_conservation"]["hpoa"]["merged"], 0)
            self.assertEqual(result["direct_assertion_promotion"],
                             "blocked_pending_identity_review_and_human_disposition")
            coverage = read_tsv(root / "audit" / "gene_coverage_causal_states.tsv")
            self.assertEqual(coverage[0]["coverage_state_v2"], "candidate_available")
            self.assertEqual(coverage[1]["coverage_state_v2"],
                             "exact_g2p_without_matching_hpoa_P")
            self.assertEqual(coverage[2]["coverage_state_v2"],
                             "no_exact_symbol_g2p_row_alias_unresolved")
            diseases = read_tsv(root / "audit" / "disease_context_presence.tsv")
            self.assertEqual(diseases[0]["onset_source_state"], "at_least_one_P_onset_field")

    def test_silent_invalid_g2p_row_is_caught_without_mutating_export(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            reg, g2p, hpoa, existing = fixture(root, malformed=True)
            result = audit(reg, g2p, hpoa, existing, root / "audit",
                           skip_source_sha=True)
            self.assertFalse(result["gate_passed"])
            self.assertEqual(result["four_fate_conservation"]["g2p"]["failed"], 1)
            self.assertEqual(result["expected_candidate_count"], 2)

    def test_source_custody_hash_rejects_modification(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            reg, g2p, hpoa, existing = fixture(root)
            with (existing / "par_evidence.tsv").open("a", encoding="utf-8") as f:
                f.write("changed\n")
            with self.assertRaisesRegex(ValueError, "source custody"):
                audit(reg, g2p, hpoa, existing, root / "audit",
                      skip_source_sha=True)


if __name__ == "__main__":
    unittest.main()
