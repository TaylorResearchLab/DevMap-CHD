#!/usr/bin/env bash
set -euo pipefail
mkdir -p inputs results
RELEASE=v2026-09-01
ROOT=https://github.com/obophenotype/human-phenotype-ontology/releases/download/${RELEASE}
curl -fL --retry 3 --output inputs/genes_to_phenotype.txt "$ROOT/genes_to_phenotype.txt"
curl -fL --retry 3 --output inputs/phenotype.hpoa "$ROOT/phenotype.hpoa"
printf '%s  %s\n' \
  '507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c' inputs/genes_to_phenotype.txt \
  'e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72' inputs/phenotype.hpoa | sha256sum -c
python run_gene_phenotype_pilot.py \
  --genes pilot_genes.tsv \
  --gene-phenotype inputs/genes_to_phenotype.txt \
  --phenotype-hpoa inputs/phenotype.hpoa \
  --expected-gene-sha256 507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c \
  --expected-hpoa-sha256 e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72 \
  --source-release "$RELEASE" --out results
python -m unittest discover -s ../../../tests/phenotypes -v
