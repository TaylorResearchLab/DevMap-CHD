import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit_662_hpo_coverage import sha256, write_tsv
from audit_hpo_unmatched_gencc_mondo_v01 import census, classify, GENCC_FIELDS


def fixture(root):
    registry = root / "genes.tsv"
    gap = root / "gap"
    gencc = root / "gencc-submissions-new.tsv"
    gap.mkdir()
    genes = [{"hgnc_id": f"HGNC:{i}", "approved_hgnc_symbol": f"GENE{i}"}
             for i in range(1, 5)]
    write_tsv(registry, genes, list(genes[0]))
    missing = [
        {"hgnc_id": "HGNC:2", "approved_symbol": "GENE2",
         "identifier_diagnostic_state": "HGNC_Entrez_no_HPO_rows_or_symbol_leads"},
        {"hgnc_id": "HGNC:3", "approved_symbol": "GENE3",
         "identifier_diagnostic_state": "HGNC_Entrez_no_HPO_rows_or_symbol_leads"},
    ]
    write_tsv(gap / "unresolved_143_identifier_diagnostic.tsv", missing, list(missing[0]))
    write_tsv(gap / "gene_identifier_diagnostic_662.tsv", [
        {"hgnc_id": f"HGNC:{i}", "gene_symbol": f"GENE{i}"}
        for i in range(1,5)
    ], ["hgnc_id", "gene_symbol"])
    manifest = {
        "status": "read_only_gene_identifier_diagnostic_pending_independent_review",
        "frozen_gene_count": 4,
        "original_matched_gene_count": 2,
        "original_unmatched_gene_count": 2,
        "source_sha256": {"registry": sha256(registry)},
    }
    (gap / "manifest.json").write_text(json.dumps(manifest)+"\n", encoding="utf-8")
    with (gap / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for name in ("manifest.json", "gene_identifier_diagnostic_662.tsv",
                     "unresolved_143_identifier_diagnostic.tsv"):
            f.write(f"{sha256(gap / name)}  {name}\n")
    rows = []
    for sgc, gene, disease, cls, submitter in (
        ("SGC-1", "HGNC:1", "MONDO:1", "Definitive", "ClinGen"),
        ("SGC-2", "HGNC:2", "MONDO:2", "Strong", "ClinGen"),
        ("SGC-3", "HGNC:2", "MONDO:3", "Disputed Evidence", "Orphanet"),
    ):
        row = dict.fromkeys(GENCC_FIELDS, "")
        row.update(sgc_id=sgc, version_number="1", gene_curie=gene,
                   disease_curie=disease, disease_title="Example disease",
                   disease_original_curie="OMIM:10000",
                   disease_original_title="Submitted example",
                   classification_title=cls, submitter_title=submitter,
                   moi_title="Autosomal dominant")
        rows.append(row)
    write_tsv(gencc, rows, list(rows[0]))
    return registry, gap, gencc


class TestGenCCMondoUnmatched(unittest.TestCase):
    def test_distinct_mondo_and_evidence_directions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            registry, gap, gencc = fixture(root)
            m = census(registry, gap, gencc, root / "out", synthetic=True)
            self.assertEqual(m["hpo_unmatched_gene_count"], 2)
            self.assertEqual(m["hpo_unmatched_with_gencc_submissions"], 1)
            self.assertEqual(m["hpo_unmatched_without_gencc_submissions"], 1)
            self.assertEqual(m["gencc_submissions_for_hpo_unmatched"], 2)
            self.assertEqual(m["hpo_unmatched_with_clingen_submitter"], 1)
            self.assertEqual(m["hpo_unmatched_with_definitive_strong_moderate"], 1)
            self.assertEqual(m["direct_gene_phenotype_PARs_promoted"], 0)
            self.assertFalse(m["mondo_mappings_independently_validated"])
            with (root / "out" / "gencc_mondo_submissions_for_143.tsv").open(
                encoding="utf-8", newline=""
            ) as f:
                rows = list(csv.DictReader(f, delimiter="\t"))
            self.assertEqual({r["gencc_mondo_id"] for r in rows},
                             {"MONDO:2", "MONDO:3"})
            self.assertEqual({r["evidence_interpretation"] for r in rows},
                             {"supports_curated", "contested"})
            self.assertTrue(all(r["submitted_disease_id"] == "OMIM:10000"
                                for r in rows))

    def test_classification_semantics(self):
        self.assertEqual(classify("Refuted Evidence"), "refuted")
        self.assertEqual(classify("No Known Disease Relationship"),
                         "no_known_relationship")
        self.assertEqual(classify("Supportive"), "supportive_ungraded")
        self.assertEqual(classify("Limited"), "limited_evidence")
        self.assertEqual(classify("Unknown classification"),
                         "classification_unrecognized")

    def test_duplicate_source_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            registry, gap, gencc = fixture(root)
            with gencc.open("r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f, delimiter="\t"))
            rows.append(rows[-1].copy())
            write_tsv(gencc, rows, list(rows[0]))
            with self.assertRaisesRegex(ValueError, "Duplicate GenCC"):
                census(registry, gap, gencc, root / "out", synthetic=True)

    def test_corrupt_gap_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            registry, gap, gencc=fixture(root)
            with (gap/"unresolved_143_identifier_diagnostic.tsv").open("a") as f:
                f.write("tamper\n")
            with self.assertRaisesRegex(ValueError, "corrupted input"):
                census(registry, gap, gencc, root/"out", synthetic=True)

    def test_output_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            registry, gap, gencc=fixture(root)
            (root/"out").mkdir()
            with self.assertRaisesRegex(ValueError, "Output directory exists"):
                census(registry, gap, gencc, root/"out", synthetic=True)


if __name__ == "__main__":
    unittest.main()
