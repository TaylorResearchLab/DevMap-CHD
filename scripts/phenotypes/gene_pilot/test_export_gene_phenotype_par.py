import csv
import tempfile
import unittest
from pathlib import Path
from export_gene_phenotype_par import export

class TestPhenotypeExporter(unittest.TestCase):
    def test_source_lineage_polarity_and_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "genes.tsv").write_text(
                "hgnc_id\tapproved_hgnc_symbol\n" +
                "".join(f"HGNC:{i+100}\tGENE{i}\n" for i in range(662)))
            (root / "g2p.tsv").write_text(
                "#ncbi_gene_id\tgene_symbol\thpo_id\tdisease_id\n" +
                "1\tGENE0\tHP:0000001\tOMIM:111111\n")
            (root / "hpoa.tsv").write_text(
                "#description: HPO disease-to-phenotype annotations v2026-09-01\n" +
                "#date: 2026-09-01\n" +
                "#database_id\thpo_id\taspect\tfrequency\tqualifier\treference\tevidence\tonset\tsex\tmodifier\n" +
                "OMIM:111111\tHP:0000001\tP\t0/19\t\tPMID:1234\tPCS\t\t\t\n" +
                "OMIM:111111\tHP:0000001\tP\t12/19\t\tPMID:1234\tPCS\t\t\t\n" +
                "OMIM:111111\tHP:0003581\tC\t\t\tPMID:9999\tPCS\t\t\t\n")
            manifest = export(root / "genes.tsv", root / "g2p.tsv",
                              root / "hpoa.tsv", root / "out", skip_sha=True)
            def read(name):
                with open(root / "out" / name, newline="") as handle:
                    return list(csv.DictReader(handle, delimiter="\t"))
            candidates = read("par_candidates.tsv")
            evidence = read("par_evidence.tsv")
            discovery = read("source_discovery_links.tsv")
            contexts = read("disease_context.tsv")
            coverage = read("gene_coverage.tsv")
            self.assertEqual(len(candidates), 2)
            self.assertEqual(len(evidence), 2)
            self.assertEqual(len(discovery), 2)
            self.assertEqual(len(contexts), 1)
            self.assertEqual(len(coverage), 662)
            self.assertEqual(len({r["candidate_id"] for r in candidates}), 2)
            self.assertEqual({r["primary_publication_id"] for r in evidence}, {"PMID:1234"})
            self.assertEqual(len({r["source_lineage_key"] for r in evidence}), 1)
            self.assertEqual({r["evidence_role"] for r in discovery}, {"disease_mediated_discovery_only"})
            self.assertEqual(contexts[0]["aspect"], "C")
            self.assertEqual(manifest["explicit_absence_candidates"], 1)
            self.assertEqual(manifest["registry_gene_count"], 662)

    def test_missing_header_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.hpoa"
            source.write_text("#description: no tabular header\n#date: 2026-09-01\\n")
            from export_gene_phenotype_par import source_rows
            with self.assertRaisesRegex(ValueError, "no matching tabular header"):
                list(source_rows(source, ("database_id", "hpo_id")))

if __name__ == "__main__":
    unittest.main()
