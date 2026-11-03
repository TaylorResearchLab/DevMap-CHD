# GenCC source evidence integration for DevMap phenotype candidates

GenCC provides versioned assertions about a gene–disease relationship and its mode of inheritance. This step adds an independent genetic source to the HPO phenotype candidate collection. It never interprets a GenCC gene–disease submission as direct gene disruption → phenotype observation.

Current GenCC downloads: https://thegencc.org/download

Use the recommended new-format TSV (`sgc_id`, `version_number`, `gene_curie`). Legacy UUID exports were deprecated in 2026. The downloaded GenCC source is retained on HPC with SHA256 in the generated manifest. The source is licensed CC0 with requested attribution to GenCC and submitting organizations. OMIM submissions are omitted from public GenCC downloads, so availability may differ from local licensed OMIM data.

## HPC commands

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_integrate_gencc_evidence.py' -v

mkdir -p scripts/phenotypes/gene_pilot/inputs

curl -fL --retry 3 \
  'https://thegencc.org/download/action/submissions-export-tsv?format=new' \
  -o scripts/phenotypes/gene_pilot/inputs/gencc-submissions-new.tsv

python3 scripts/phenotypes/gene_pilot/integrate_gencc_evidence.py \
  --hpo-dir results/phenotypes/par_candidates_v02 \
  --gencc scripts/phenotypes/gene_pilot/inputs/gencc-submissions-new.tsv \
  --out results/phenotypes/gencc_integration_v01

cat results/phenotypes/gencc_integration_v01/gencc_integration_manifest.json
```

This script requires stable SGC identifiers and explicit versions. It matches gene by exact HGNC CURIE and joins HPO candidates only when a GenCC source disease CURIE is identical to the disease CURIE in the HPOA source. Disease synonym matching and MONDO crosswalks are a separate, versioned mapping step. Zero exact matches indicate no exact native identifier overlap, not absence of genetic evidence.

## Outputs

* `gencc_gene_disease_evidence.tsv` preserves submission ID/version, classification, mode of inheritance, submitter and source references for all matched 662 registry genes.
* `gencc_hpo_exact_disease_matches.tsv` links existing HPO phenotype candidates with distinct GenCC gene–disease source assertions by identical disease CURIE. This is a two-source inference, not a directly observed phenotype effect of gene disruption.
* `gencc_missing_phenotype_genes.tsv` highlights registry genes with GenCC gene–disease classifications but no HPO candidate.
* `gencc_integration_manifest.json` and `SHA256SUMS.txt` record source checksum, counts and output integrity.

The source download is external to the public DevMap-CHD GitHub repository. Code and tests live on the feature branch. No new canonical PARs are created. The ClinGen submitter record is distinguished from the GenCC distribution layer so duplicated literature is traceable to the original publication.
