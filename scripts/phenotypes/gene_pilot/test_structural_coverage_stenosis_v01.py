"""Synthetic tests for the STENOSIS-001 source-conserving structural view."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from structural_coverage_stenosis_v01 import (
    APPROVED, DEFERRED, ROOT, analyze, classification, digest,
    ontology, parse_obo, read_tsv,
)


def tsv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tuple(rows[0]), delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def fixture(root):
    base = root / "source"
    base.mkdir()
    reg = root / "genes.tsv"
    tsv(reg, [
        {"hgnc_id": f"HGNC:{i}", "approved_hgnc_symbol":
         {1: "CIC", 2: "LZTR1", 3: "GENE3"}.get(i, f"GENE{i}")}
        for i in range(1, 663)
    ])
    obo = root / "hp.obo"
    lines = ["format-version: 1.2", "",
             "[Term]", f"id: {ROOT}",
             "name: Abnormal cardiovascular system morphology", ""]
    for hp, label in sorted({**APPROVED, **DEFERRED}.items()):
        lines.extend(["[Term]", f"id: {hp}", f"name: {label}"])
        # HP:0001650 tests a term reachable by both approved and native routes.
        # HP:0001653 tests a deferred exception still reached by true ancestry.
        if hp in {"HP:0001650", "HP:0001653"}:
            lines.append(f"is_a: {ROOT} ! test parent")
        lines.append("")
    lines.extend(["[Term]", "id: HP:0999000",
                  "name: Test morphology descendant",
                  f"is_a: {ROOT} ! test parent", "",
                  "[Term]", "id: HP:0999001",
                  "name: Test nonstructural term", ""])
    obo.write_text("\n".join(lines), encoding="utf-8")
    g2p = root / "genes_to_phenotype.txt"
    hpoa = root / "phenotype.hpoa"
    g2p.write_text("synthetic\n")
    hpoa.write_text("synthetic\n")

    records = [
        ("p1", "HGNC:1", "CIC", "OMIM:1", "HP:0001642", "not_negated",
         "observed_positive", "phenotype.hpoa:10", "", "ev1"),
        ("p2", "HGNC:2", "LZTR1", "OMIM:2", "HP:0001650", "not_negated",
         "observed_positive", "phenotype.hpoa:11", "HP:0003581", "ev2"),
        ("p3", "HGNC:3", "GENE3", "OMIM:1", "HP:0001642", "not_negated",
         "frequency_unreported", "phenotype.hpoa:10", "", "ev3"),
        ("p4", "HGNC:3", "GENE3", "ORPHA:1", "HP:0999000", "not_negated",
         "observed_zero", "phenotype.hpoa:12", "", "ev4"),
        ("p5", "HGNC:3", "GENE3", "ORPHA:2", "HP:0001653", "negated",
         "observed_zero", "phenotype.hpoa:13", "", "ev5"),
        ("p6", "HGNC:3", "GENE3", "ORPHA:3", "HP:0034377", "not_negated",
         "observed_positive", "phenotype.hpoa:14", "", "ev6"),
    ]
    projections = []
    observations = []
    for (pid, gene, symbol, disease, hp, polarity, outcome,
         source_row, onset, eid) in records:
        projections.append({
            "projection_id": pid, "gene_id": gene, "gene_symbol": symbol,
            "disease_id": disease, "phenotype_id": hp,
            "source_claim_id": f"src:{disease}:{hp}:{polarity}",
            "claim_polarity": polarity,
            "projection_role": "disease_mediated_discovery_only",
            "hpoa_evidence_links": "1",
        })
        observations.append({
            "projection_id": pid,
            "source_claim_id": f"src:{disease}:{hp}:{polarity}",
            "original_subject": disease, "original_object": hp,
            "source_row_id": source_row, "source_resource": "HPOA",
            "source_release": "v2026-09-01", "evidence_id": eid,
            "claim_polarity": polarity, "evidence_outcome": outcome,
            "onset": onset, "original_reference": "PMID:123",
            "frequency": "0/1" if outcome == "observed_zero" else "1/1",
            "qualifier": "NOT" if polarity == "negated" else "",
        })
    tsv(base / "gene_disease_hpo_discovery_projections.tsv", projections)
    tsv(base / "original_hpoa_observations.tsv", observations)
    (base / "manifest.json").write_text(json.dumps({
        "identity_profile": "hpoa_disease_subject_two_level_v01",
        "original_evidence_link_count": 63012,
        "provisional_projection_count": 62832,
    }))
    names = ["gene_disease_hpo_discovery_projections.tsv",
             "original_hpoa_observations.tsv", "manifest.json"]
    (base / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(base / n)}  {n}\n" for n in names)
    )
    return reg, obo, g2p, hpoa, base


class StructuralMembershipTests(unittest.TestCase):
    def test_nine_in_six_deferred_not_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            f = fixture(Path(d))
            terms, alt = parse_obo(f[1])
            before = {x: list(t["parents"]) for x, t in terms.items()}
            members, ancestors = classification(terms, alt)
            self.assertEqual(set(APPROVED), {
                "HP:0001642", "HP:0001650", "HP:0001718",
                "HP:0004381", "HP:0010446", "HP:0011570",
                "HP:0034348", "HP:0034349", "HP:0034350",
            })
            self.assertEqual(set(DEFERRED), {
                "HP:0001653", "HP:0001659", "HP:0005180",
                "HP:0010444", "HP:0034376", "HP:0034377",
            })
            self.assertEqual(len(APPROVED), 9)
            self.assertEqual(len(DEFERRED), 6)
            self.assertTrue(set(APPROVED) <= set(members))
            for term in DEFERRED:
                self.assertNotIn(term, APPROVED)
            self.assertNotIn("HP:0034377", members)
            self.assertIn("HP:0001653", members)
            self.assertEqual(
                members["HP:0001653"]["membership_route"],
                "ontology_is_a")
            self.assertEqual(
                members["HP:0001650"]["membership_route"],
                "ontology_is_a+approved_exception")
            self.assertEqual(
                before, {x: list(t["parents"]) for x, t in terms.items()})
            self.assertIn(ROOT, ancestors("HP:0999000"))
            self.assertNotIn(ROOT, ancestors("HP:0001642"))

    def test_source_scope_coverage_and_reproducible_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = fixture(root)
            a = analyze(*f, root / "out_1", strict=False, commit="TEST")
            b = analyze(*f, root / "out_2", strict=False, commit="TEST")
            self.assertEqual(a["output_counts"], b["output_counts"])
            self.assertEqual(a["output_counts"]["morphology"]["genes"], 2)
            self.assertEqual(
                a["output_counts"]["added_exceptions_only"]["genes"], 2)
            self.assertEqual(a["output_counts"]["union"]["genes"], 3)
            self.assertEqual(
                a["output_counts"]["net_new_vs_morphology"]["genes"], 1)
            # The same original HPOA source row appears under two gene
            # projections and counts as one original source observation.
            self.assertEqual(a["output_counts"]["union"]["original_source_rows"], 3)
            self.assertEqual(a["output_counts"]["union"]["original_evidence_links"], 4)
            self.assertEqual(a["disease_mediated_gene_phenotype_promotions"], 0)
            self.assertEqual(a["patient_developmental_onset_inferred"], False)
            self.assertEqual(a["union_source_rows_onset_unspecified"], 2)
            obs = list(read_tsv(root / "out_1" /
                                "selected_original_hpoa_observations.tsv",
                                {"original_subject", "onset", "claim_polarity"}))
            self.assertEqual(len(obs), 5)  # includes native descendant negated
            self.assertTrue(any(x["claim_polarity"] == "negated" for x in obs))
            self.assertTrue(any(x["onset"] == "HP:0003581" for x in obs))
            self.assertTrue(all(x["developmental_onset_inferred"] == "no"
                                for x in obs))
            for n in ("SHA256SUMS.txt", "review_SHA256SUMS.txt",
                      "STENOSIS-001_review_v01.zip", "review_bundle.sha256"):
                self.assertEqual(
                    digest(root / "out_1" / n),
                    digest(root / "out_2" / n), n)
            import zipfile
            with zipfile.ZipFile(root / "out_1" /
                                 "STENOSIS-001_review_v01.zip") as z:
                self.assertIsNone(z.testzip())
                self.assertNotIn("selected_original_hpoa_observations.tsv",
                                 z.namelist())
                self.assertIn("review_SHA256SUMS.txt", z.namelist())

    def test_hard_fail_on_mutated_or_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = fixture(root)
            with self.assertRaises(ValueError):
                analyze(*f, root / "strict_out", strict=True, commit="TEST")
            source_file = f[4] / "original_hpoa_observations.tsv"
            source_file.write_text(source_file.read_text() + "mutated\n")
            with self.assertRaises(ValueError):
                analyze(*f, root / "invalid_out", strict=False, commit="TEST")

    def test_output_refuses_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = fixture(root)
            analyze(*f, root / "existing", strict=False, commit="TEST")
            with self.assertRaises(FileExistsError):
                analyze(*f, root / "existing", strict=False, commit="TEST")


if __name__ == "__main__":
    unittest.main()
