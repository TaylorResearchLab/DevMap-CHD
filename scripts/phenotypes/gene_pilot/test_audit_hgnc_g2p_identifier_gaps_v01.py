import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit_hgnc_g2p_identifier_gaps_v01 import audit
from audit_662_hpo_coverage import sha256


def write(path, headers, data):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def fixture(root):
    registry = root / "registry.tsv"
    g2p = root / "g2p.tsv"
    hpoa = root / "hpoa.tsv"
    hgnc = root / "hgnc.tsv"
    coverage = root / "coverage"
    coverage.mkdir()

    genes = [
        {"hgnc_id": f"HGNC:{1000+i}",
         "approved_hgnc_symbol": f"GENE{i}", "ensembl_gene_id": f"ENSG{i:011d}"}
        for i in range(662)
    ]
    write(registry, tuple(genes[0]), genes)
    hgnc_rows = []
    for i in range(662):
        hgnc_rows.append({
            "hgnc_id": f"HGNC:{1000+i}",
            "symbol": f"GENE{i}",
            "entrez_id": "" if i == 520 else str(1000+i),
            "status": "Approved",
            "prev_symbol": "OLDGENE1" if i == 1 else
                           "GENE519OLD" if i == 519 else "",
            "alias_symbol": "GENE0" if i == 521 else "",
        })
    write(hgnc, tuple(hgnc_rows[0]), hgnc_rows)
    g2p_rows = [
        {"ncbi_gene_id": str(1000+i),
         "gene_symbol": "OLDGENE1" if i == 1 else f"GENE{i}",
         "hpo_id": "HP:0000001", "disease_id": "OMIM:111111"}
        for i in range(519)
    ]
    g2p_rows.append({"ncbi_gene_id": "999999", "gene_symbol": "GENE519OLD",
                     "hpo_id": "HP:0000002", "disease_id": "OMIM:222222"})
    write(g2p, tuple(g2p_rows[0]), g2p_rows)
    hpoa.write_text("synthetic", encoding="utf-8")

    coverage_rows = [
        {"hgnc_id": f"HGNC:{1000+i}",
         "match_method": "NCBI_GENE_ID" if i < 519 else "NO_MATCH",
         "hpo_gene_summary_status": ("PRESENT" if i < 519 else
                                     "NO_ROWS_IN_PINNED_HPO_DISCOVERY_INDEX")}
        for i in range(662)
    ]
    write(coverage / "gene_hpo_coverage_662.tsv",
          tuple(coverage_rows[0]), coverage_rows)
    write(coverage / "genes_without_hpo_gene_summary.tsv",
          tuple(coverage_rows[0]), coverage_rows[519:])
    hashes = {
        "registry": sha256(registry), "genes_to_phenotype": sha256(g2p),
        "phenotype_hpoa": sha256(hpoa), "hgnc_crosswalk": sha256(hgnc),
    }
    manifest = {
        "frozen_gene_registry_count": 662, "hpo_ncbi_crosswalk_provided": True,
        "hpo_total_gene_summary_rows": 520,
        "hpo_gene_summary_annotated_gene_count": 519,
        "hpo_gene_summary_unannotated_gene_count": 143,
        "sha256": hashes
    }
    (coverage / "hpo_coverage_662_manifest.json").write_text(
        json.dumps(manifest)+"\n", encoding="utf-8"
    )
    names = ["gene_hpo_coverage_662.tsv", "genes_without_hpo_gene_summary.tsv",
             "hpo_coverage_662_manifest.json"]
    (coverage / "SHA256SUMS.txt").write_text("".join(
        f"{sha256(coverage / name)}  {name}\n" for name in names
    ), encoding="utf-8")
    return registry, g2p, hpoa, hgnc, coverage


def tab(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class TestHGNCIndependentMatching(unittest.TestCase):
    def test_independent_match_axes_and_unverified_alias_leads(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            args = fixture(root)
            result = audit(*args, root/"audit", check_hashes=False)
            self.assertEqual(result["frozen_gene_count"], 662)
            self.assertEqual(result["original_matched_gene_count"], 519)
            self.assertEqual(result["original_unmatched_gene_count"], 143)
            self.assertEqual(result["exact_symbol_matched_genes"], 518)
            self.assertEqual(result["ncbi_id_matched_genes"], 519)
            self.assertEqual(result["both_exact_symbol_and_ncbi_matched_genes"], 518)
            self.assertEqual(result["unmatched_with_alias_hpo_source_leads"], 2)
            self.assertEqual(result["unmatched_without_HGNC_entrez"], 1)
            self.assertEqual(result["alias_source_leads_total"], 3)
            self.assertEqual(result["alias_leads_with_other_HGNC_owners"], 1)
            self.assertFalse(result["gene_reassignment_performed"])
            self.assertEqual(result["direct_gene_phenotype_PARs_promoted"], 0)
            leads = tab(root/"audit"/"historical_alias_source_leads.tsv")
            x = [r for r in leads if r["approved_symbol"] == "GENE519"]
            self.assertEqual(len(x), 1)
            self.assertEqual(x[0]["hpo_source_ncbi_ids"], "999999")
            self.assertEqual(x[0]["source_id_matches_hgnc"], "no")
            y = [r for r in leads if r["approved_symbol"] == "GENE521"]
            self.assertEqual(y[0]["other_hgnc_owners"], "HGNC:1000")
            self.assertEqual(len(tab(root/"audit"/"unresolved_143_identifier_diagnostic.tsv")), 143)

    def test_corrupt_prior_coverage_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            args = fixture(root)
            prior = root/"coverage"/"gene_hpo_coverage_662.tsv"
            prior.write_text(prior.read_text()+"corrupt\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed verified input"):
                audit(*args, root/"audit", check_hashes=False)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            args=fixture(root)
            (root/"audit").mkdir()
            with self.assertRaisesRegex(ValueError, "Output directory exists"):
                audit(*args, root/"audit", check_hashes=False)


if __name__ == "__main__":
    unittest.main()
