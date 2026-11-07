import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit_two_level_edge_cases_v01 import audit
from export_two_level_phenotype_v01 import export, sha256
from test_export_two_level_phenotype_v01 import fixture


def refresh_digest(directory, filename):
    checksum_file = directory / "SHA256SUMS.txt"
    lines = checksum_file.read_text(encoding="utf-8").splitlines()
    updated = []
    for line in lines:
        _, name = line.split(None, 1)
        name = name.strip()
        digest = sha256(directory / name) if name == filename else line.split()[0]
        updated.append(f"{digest}  {name}")
    checksum_file.write_text("\n".join(updated) + "\n", encoding="utf-8")


def prepared_fixture(root):
    old, integrity = fixture(root)
    path = integrity / "audit_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for source in ("g2p", "hpoa"):
        manifest["four_fate_conservation"][source].update(
            merged=0, held=0, failed=0
        )
    manifest["source_row_counts"] = {"g2p": 4, "hpoa": 4}
    path.write_text(json.dumps(manifest) + "\\n", encoding="utf-8")
    refresh_digest(integrity, "audit_manifest.json")
    return old, integrity


def change_original_frequency(folder, old_value, new_value):
    path = folder / "par_evidence.tsv"
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        rows = list(reader)
    matches = 0
    for row in rows:
        if row["frequency"] == old_value:
            row["frequency"] = new_value
            matches += 1
    if matches != 1:
        raise AssertionError(f"Expected one synthetic frequency {old_value}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    refresh_digest(folder, "par_evidence.tsv")


class TestTwoLevelEdgeGuard(unittest.TestCase):
    def test_verified_view_with_no_edge_cases(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, integrity = prepared_fixture(root)
            export(old, integrity, root / "view")
            r = audit(root / "view", old, integrity, root / "guard")
            self.assertEqual(r["original_evidence_links_verified"], 4)
            self.assertEqual(r["issue_count"], 0)
            self.assertTrue(r["input_conservation_ledger_verified"])
            self.assertTrue(r["source_fidelity_passed"])
            self.assertFalse(r["edge_cases_require_review"])
            self.assertEqual(r["direct_assertions_promoted"], 0)

    def test_NOT_with_reported_frequency_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, integrity = prepared_fixture(root)
            change_original_frequency(old, "", "3/5")
            # Only the final synthetic record is NOT and has blank frequency;
            # the original helper above changes it to a positive outcome.
            export(old, integrity, root / "view")
            r = audit(root / "view", old, integrity, root / "guard")
            self.assertEqual(r["not_with_frequency_rows"], 1)
            self.assertEqual(r["issue_count"], 1)
            self.assertTrue(r["edge_cases_require_review"])

    def test_zero_percent_and_excluded_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, integrity = prepared_fixture(root)
            change_original_frequency(old, "0/19", "0%")
            change_original_frequency(old, "12/19", "HP:0040285")
            export(old, integrity, root / "view")
            r = audit(root / "view", old, integrity, root / "guard")
            self.assertEqual(r["zero_percent_rows"], 1)
            self.assertEqual(r["excluded_frequency_rows"], 1)
            self.assertEqual(r["issue_count"], 2)
            self.assertTrue(r["edge_cases_require_review"])

    def test_missing_conservation_manifest_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, integrity = prepared_fixture(root)
            export(old, integrity, root / "view")
            path = root / "view" / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            del manifest["input_rows_conserved_from_prior_gate"]
            path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            refresh_digest(root / "view", "manifest.json")
            with self.assertRaisesRegex(ValueError, "Required input_rows_conserved"):
                audit(root / "view", old, integrity, root / "guard")

    def test_edited_source_evidence_fails_custody_check(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, integrity = prepared_fixture(root)
            export(old, integrity, root / "view")
            path = root / "view" / "original_hpoa_observations.tsv"
            with path.open("a", encoding="utf-8") as f:
                f.write("modified\n")
            with self.assertRaisesRegex(ValueError, "altered input"):
                audit(root / "view", old, integrity, root / "guard")


if __name__ == "__main__":
    unittest.main()
