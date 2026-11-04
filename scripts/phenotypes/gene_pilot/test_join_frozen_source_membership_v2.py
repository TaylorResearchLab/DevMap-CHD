import csv
import tempfile
import unittest
from pathlib import Path
from join_frozen_source_membership_v2 import locate_matrix, read_table, binary

class MembershipInputTests(unittest.TestCase):
    def test_matrix_file_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "CHD_Gene_Source_Membership_Matrix_v2_ids_canonical.tsv"
            path.write_text("HGNC ID\tApproved HGNC symbol\nHGNC:1\tGENE1\n")
            self.assertEqual(locate_matrix(root), path)
            self.assertEqual(next(read_table(path))["HGNC ID"], "HGNC:1")

    def test_one_hot_validation(self):
        self.assertEqual(binary("1", "membership", "HGNC:1"), 1)
        self.assertEqual(binary("0.0", "membership", "HGNC:1"), 0)
        with self.assertRaises(ValueError):
            binary("2", "membership", "HGNC:1")

    def test_matrix_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                locate_matrix(Path(tmp))

if __name__ == "__main__":
    unittest.main()
