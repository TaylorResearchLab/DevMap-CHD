import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from inspect_pubmind_raw_tables import inspect

class InventoryTest(unittest.TestCase):
    def test_tsv_and_gz_and_frozen_gene_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=root/"pubmind";data.mkdir()
            with (data/"pubmind_nodes.tsv").open("w") as f:
                f.write("id\tname\tPVID\tHPO_ID\nvariant:1\tTEST\tPVID:1\tHP:0001\n")
            with gzip.open(data/"pubmind_edges.tsv.gz","wt") as f:
                f.write("subject\tpredicate\tobject\tpublication_id\nvariant:1\tassociated_with\tHP:0001\tPMID:123\n")
            registry=root/"genes.tsv"
            with registry.open("w",newline="") as f:
                w=csv.writer(f,delimiter="\t")
                w.writerow(["hgnc_id","approved_hgnc_symbol"])
                w.writerows((f"HGNC:{i}",f"GENE{i}") for i in range(662))
            out=root/"out"
            result=inspect(data,registry,out)
            self.assertEqual(result["registry_genes"],662)
            self.assertEqual(result["file_count"],2)
            self.assertEqual(result["files_with_hpo_columns"],["pubmind_nodes.tsv"])
            self.assertEqual(result["files_with_publication_columns"],["pubmind_edges.tsv.gz"])
            all_rows=json.loads((out/"pubmind_source_inventory.json").read_text())["files"]
            self.assertTrue(any(r["probable_edge_table"] for r in all_rows))
            self.assertTrue((out/"SHA256SUMS.txt").exists())

    def test_invalid_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/"input";src.mkdir()
            genes=root/"genes.tsv";genes.write_text("hgnc_id\nHGNC:1\n")
            with self.assertRaisesRegex(ValueError,"662"):
                inspect(src,genes,root/"out")

if __name__=="__main__":
    unittest.main()
