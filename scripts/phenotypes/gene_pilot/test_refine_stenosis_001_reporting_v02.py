"""Synthetic regression for the STENOSIS-001 v02 evidence and onset reporting."""
import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from structural_coverage_stenosis_v01 import analyze, digest
from test_structural_coverage_stenosis_v01 import fixture, tsv
from refine_stenosis_001_reporting_v02 import refine


def read_rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def prepare(root):
    reg, obo, g2p, hpoa, source = fixture(root)
    with obo.open("a", encoding="utf-8") as f:
        f.write("\n[Term]\nid: HP:0003577\nname: Congenital onset\n\n")
        f.write("[Term]\nid: HP:0003581\nname: Adult onset\n\n")
    obs = read_rows(source / "original_hpoa_observations.tsv")
    for record in obs:
        record["source_evidence_code"] = (
            "IEA" if record["projection_id"] == "p2" else "PCS"
        )
    tsv(source / "original_hpoa_observations.tsv", obs)
    names = ("gene_disease_hpo_discovery_projections.tsv",
             "original_hpoa_observations.tsv", "manifest.json")
    (source / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(source / n)}  {n}\n" for n in names)
    )
    old = root / "old"
    analyze(reg, obo, g2p, hpoa, source, old, strict=False, commit="TEST")
    candidate = root / "candidate"
    candidate.mkdir()
    context = [
        {"disease_id": "OMIM:1", "source_row_id": "phenotype.hpoa:99",
         "aspect": "C", "hpo_id": "HP:0003577", "reference": "PMID:1",
         "evidence": "PCS", "primary_publication_id": "PMID:1"},
        {"disease_id": "OMIM:2", "source_row_id": "phenotype.hpoa:100",
         "aspect": "C", "hpo_id": "HP:0003581", "reference": "OMIM:2",
         "evidence": "TAS", "primary_publication_id": ""},
        {"disease_id": "OMIM:2", "source_row_id": "phenotype.hpoa:101",
         "aspect": "P", "hpo_id": "HP:0001642", "reference": "PMID:3",
         "evidence": "PCS", "primary_publication_id": "PMID:3"},
        {"disease_id": "OMIM:absent", "source_row_id": "phenotype.hpoa:102",
         "aspect": "C", "hpo_id": "HP:0003577", "reference": "",
         "evidence": "TAS", "primary_publication_id": ""},
    ]
    tsv(candidate / "disease_context.tsv", context)
    (candidate / "manifest.json").write_text(
        json.dumps({"reference_release": "HPO:v2026-09-01"}) + "\n")
    (candidate / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(candidate / n)}  {n}\n"
                for n in ("manifest.json", "disease_context.tsv"))
    )
    return old, candidate, obo


class TestV02OnsetEvidence(unittest.TestCase):
    def test_scope_and_determinism(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old, candidate, obo = prepare(root)
            baseline = digest(old / "manifest.json")
            a = refine(old, candidate, obo, root / "new1",
                       strict=False, commit="TEST")
            b = refine(old, candidate, obo, root / "new2",
                       strict=False, commit="TEST")
            self.assertEqual(digest(old / "manifest.json"), baseline)
            self.assertEqual(a["disease_level_onset_count"], 2)
            self.assertEqual(a["congenital_disease_level_onset_count"], 1)
            self.assertTrue(a["disease_onset_is_not_patient_or_phenotype_onset"])
            self.assertEqual(a["original_union_count"], b["original_union_count"])
            ex = read_rows(root / "new1" / "source_examples_v02.tsv")
            self.assertTrue(any(
                x["gene_symbol"] == "LZTR1"
                and x["source_evidence_code"] == "IEA"
                and x["disease_onset_hpo_labels"] == "Adult onset"
                and x["phenotype_row_onset_column_status"] == "reported"
                for x in ex))
            self.assertTrue(any(
                x["gene_symbol"] == "CIC"
                and x["source_evidence_code"] == "PCS"
                and x["disease_onset_hpo_labels"] == "Congenital onset"
                and x["phenotype_row_onset_column_status"] == "blank"
                for x in ex))
            self.assertTrue(all(x["patient_specific_onset_asserted"] == "no"
                                for x in ex))
            self.assertEqual((old / "coverage_summary.tsv").read_bytes(),
                             (root / "new1" / "coverage_summary.tsv").read_bytes())
            with zipfile.ZipFile(root / "new1" /
                                 "STENOSIS-001_review_v02.zip") as z:
                self.assertIsNone(z.testzip())
                self.assertNotIn("disease_onset_context.tsv", z.namelist())
                self.assertIn("source_examples_v02.tsv", z.namelist())
            for name in ("SHA256SUMS.txt", "review_bundle.sha256"):
                self.assertEqual(digest(root / "new1" / name),
                                 digest(root / "new2" / name))

    def test_rejects_source_mutation_and_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old, candidate, obo = prepare(root)
            refine(old, candidate, obo, root / "new", strict=False, commit="TEST")
            with self.assertRaises(FileExistsError):
                refine(old, candidate, obo, root / "new", strict=False,
                       commit="TEST")
            with (candidate / "disease_context.tsv").open("a") as f:
                f.write("altered\n")
            with self.assertRaises(ValueError):
                refine(old, candidate, obo, root / "mutated",
                       strict=False, commit="TEST")


if __name__ == "__main__":
    unittest.main()
