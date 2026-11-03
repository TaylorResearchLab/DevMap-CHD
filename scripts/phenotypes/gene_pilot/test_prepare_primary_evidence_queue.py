import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from prepare_primary_evidence_queue import produce

def write(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PrimaryEvidenceQueueTest(unittest.TestCase):
    def test_publication_lineage_and_missing_gene(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            candidates = [
                {"candidate_id": "c1", "gene_id": "HGNC:1", "gene_symbol": "GENE1",
                 "phenotype_id": "HP:1", "disease_id": "OMIM:1",
                 "assertion_state": "disease_mediated_candidate_asserted_present"},
                {"candidate_id": "c2", "gene_id": "HGNC:1", "gene_symbol": "GENE1",
                 "phenotype_id": "HP:2", "disease_id": "OMIM:1",
                 "assertion_state": "disease_mediated_candidate_asserted_absent"}]
            write(source / "par_candidates.tsv", candidates[0].keys(), candidates)
            evidence = [
                {"candidate_id": "c1", "primary_publication_id": "PMID:123",
                 "source_row_id": "phenotype.hpoa:1", "source_evidence_code": "PCS",
                 "original_subject": "OMIM:1", "original_object": "HP:1",
                 "evidence_role": "disease_phenotype_annotation", "original_reference": "PMID:123"},
                {"candidate_id": "c2", "primary_publication_id": "PMID:123",
                 "source_row_id": "phenotype.hpoa:2", "source_evidence_code": "PCS",
                 "original_subject": "OMIM:1", "original_object": "HP:2",
                 "evidence_role": "disease_phenotype_annotation", "original_reference": "PMID:123"}]
            write(source / "par_evidence.tsv", evidence[0].keys(), evidence)
            coverage = [{"gene_id": f"HGNC:{i}", "gene_symbol": f"GENE{i}",
                         "candidate_count": "2" if i == 1 else "0",
                         "source_g2p_rows": "1" if i == 1 else "0"} for i in range(1,663)]
            write(source / "gene_coverage.tsv", coverage[0].keys(), coverage)
            (source / "manifest.json").write_text(json.dumps({
                "reference_release": "HPO:v2026-09-01", "registry_gene_count": 662,
                "candidate_count": 2}))
            with open(source / "SHA256SUMS.txt", "w") as fh:
                for name in ("par_candidates.tsv", "par_evidence.tsv", "gene_coverage.tsv", "manifest.json"):
                    fh.write(f"{sha(source / name)}  {name}\n")
            summary = produce(source, root / "out")
            self.assertEqual(summary["publication_gene_review_pairs"], 1)
            self.assertEqual(summary["genes_without_hpo_candidates"], 661)
            with open(root / "out" / "publication_gene_queue.tsv") as fh:
                row = next(csv.DictReader(fh, delimiter="\t"))
                self.assertEqual(row["publication_id"], "PMID:123")
                self.assertEqual(row["direct_gene_disruption_evidence"], "NOT_ASSESSED")
                self.assertEqual(row["candidate_count"], "1")
            # Original source input is immutable to the queue generator.
            expected = {line.split(None, 1)[1].strip(): line.split(None, 1)[0]
                        for line in (source / "SHA256SUMS.txt").read_text().splitlines()}
            self.assertEqual(sha(source / "par_candidates.tsv"), expected["par_candidates.tsv"])

    def test_source_checksum_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.json").write_text(json.dumps({
                "reference_release": "HPO:v2026-09-01", "registry_gene_count": 662}))
            (root / "SHA256SUMS.txt").write_text("deadbeef  par_candidates.tsv\n")
            (root / "par_candidates.tsv").write_text("wrong")
            with self.assertRaises(ValueError):
                produce(root, root / "out")

if __name__ == "__main__":
    unittest.main()
