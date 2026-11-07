# DevMap phenotype assertion primary-source evidence contract (draft v01)

Status: **proposed for SCUTER Agent 2 review and scientific acceptance**. Applies to HPOA-derived discoveries, PubMind variant associations, and other future phenotype sources for the frozen DevMap-CHD 662-gene registry. It does not change accepted biological content.

## Principle

For each proposed gene disruption → phenotype assertion, maintain a machine-readable reference to the *specific original evidence supporting that phenotype*. The gene's general literature or disease associations are not substitutes for phenotype-specific publication evidence. Evidence is independently auditable on demand.

## Separate records

**Assertion candidate**: `candidate_id`, `hgnc_id`, `hpo_id_original`, `hpo_id_resolved`, `phenotype_polarity`, `disease_id`, `disruption_type`, `assertion_status`, `source_release`.

**Source observation**: `observation_id`, `candidate_id`, `source_resource`, `source_dataset`, `source_release`, `source_record_id`, `source_row_id`, `PVID`, `variant_annotation_original`, `hgvs_g_normalized`, `disease_id_original`, `source_phenotype_id`, `source_phenotype_polarity`. Preserve each observed variant and its original mapping. Blank variant information is explicitly recorded as unknown or not applicable, rather than inferred.

**Phenotype-specific publication link**: `evidence_id`, `observation_id`, `candidate_id`, `Publication_ID`, `identifier_type` (PMID/PMCID/DOI/other), `publication_specific_pathogenicity_score`, `source_publication_position`, `source_mapping_method`, `publication_link_role`, `evidence_location`, `phenotype_observation_summary`, `evidence_type`, `review_status`, `reviewer`, `review_date`, `review_note`.

Each link must trace one observed gene/variant–phenotype relationship to its source publication. Retain all source rows, including repeated PVIDs with separate publications and repeated publications with distinct phenotypes. Preserve a source-specific observation key rather than assuming PVID alone is unique across SNV/CNV/SV/GF.

## Evidence link roles

- `phenotype_specific_source_link`: original source identifies this publication as supporting this particular HPO observation, including PubMind SNV positional correspondence.
- `gene_level_publication_lead`: publication linked to gene or PVID but not independently attributed to this HPO observation. This is a discovery lead, **not** assertion-supporting publication evidence.
- `disease_phenotype_secondary_annotation`: HPOA disease–phenotype record with its own reference; retains disease-mediated context and source subject.
- `primary_publication_verified`: reviewer inspected the original publication and located the specific phenotype observation (evidence location and observation summary required).

The `evidence_type` field identifies patient observation, functional experiment, model organism, secondary curation, review, or uncertain, where supported by original source.

## Validation status

1. `source_identified`: source-specific PVID/HPO/publication relationship recovered and source record identified.
2. `primary_source_checked`: the original publication was read and location documented.
3. `phenotype_verified`: the reported phenotype, subject, polarity, variant and disease context were checked against the original source.
4. `biologically_accepted`: human scientific authority accepted the assertion after independent SCUTER review.

A downstream phenotype PAR should link to exact evidence IDs and retain the original source and ontology releases. The same original publication should not be treated as multiple independent supporting studies simply because it appears in HPOA, PubMind or another source.

## Input acceptance checks for Aditya's complete PubMind export

1. All input gene symbols reconcile to frozen HGNC IDs; absent rows and missing phenotypes retain their source dataset identity.
2. SNV/CNV/SV/GF source type and version are recorded. Original variant descriptions remain unchanged. Normalized SNV HGVSg is additional, when available.
3. For all 1,522 source PubMind Gene–HPO pairs, compare linked primary publication counts with the v2 table, respecting Aditya's positional HPO-to-publication mapping. Report discrepancies, missing publication identifiers and unsupported cross-products.
4. Record all variant/HPO/publication associations with stable source row IDs, without fabricating evidence for missing HPO in CNV/SV/GF records.
5. Preserve paper-specific pathogenicity scores and missingness. They are source assessments, not automatic proof of causality.
6. The HPO 2026-09-01 audit maps 842 active and 2 obsolete terms. Retain original identifiers and ontology replacement suggestions separately.
7. Export an inspection queue for missing or indirect publication links and a verification ledger for reviewed assertions.

## Initial review set

The 62 PubMind Gene–HPO pairs new to HPO discovery under HPO heart morphology provide a useful review cohort. Start with direct structural examples HAND1–HP:0001961, GJC1–HP:0001631, HAND2–HP:0011653, ISL1–HP:0001710, and the remaining congenital structural lesions. Myocardial hypertrophy, cardiomyopathy, and remodeling are retained as separate phenotype categories. All pairs remain provisional until source verification.

## Release and access

Original PubMind files and the future variant-level evidence table remain private on CHOP HPC pending PubMind reuse agreement. Code and this contract are versioned in GitHub. A public PAR release must apply the permitted source redistribution rules to original records and excerpts.

Source records support on-demand review through saved identifiers, location within the publication, original row reference and version checksums. Preserve review decisions as versioned records without overwriting the underlying source evidence.

## Scientific authority decision, 2026-11-07: review allocation policy

User-approved policy supersedes any blanket requirement to independently revalidate every imported primary reference. An expert-curated source assertion with a traceable PubMed identifier is accepted as expert-curated evidence **at its original claim scope**. Record the source, original claim subject/predicate/object, PMID, curator or institution, classification/evidence code and source version. Validate technical integrity of the import, identifiers and source attribution. A separate full-text primary source re-review is ordinarily unnecessary for that unchanged expert-curated claim.

The following still receive targeted assessment:
- HPO or ClinGen assertions with missing or unclear direct publication provenance, weaker evidence, disputed/refuted interpretations or conflicting annotations.
- Other GenCC submitter classifications with varying curation standards; retain submitter and source classification rather than extending ClinGen's authority to all GenCC records.
- New gene disruption–phenotype assertions that DevMap constructs by inference, including gene→disease→phenotype traversals. Expert curations of the two input edges do not independently validate the inferred direct relationship.
- Novel molecular mechanisms, phenotype specificity, polarity conflicts, ambiguous subject identities, and contradictory observations.

PubMind associations originate from automated/AI extraction and **require independent secondary scientific review**. Recover the original phenotype-specific PVID/HPO/publication mapping; Agent 1 constructs and verifies evidence from the source, Agent 2 independently checks the source attribution and interpretation, and the User accepts/narrows/defers/rejects each proposed biological claim. PubMind publication counts and gene-level literature leads are provisional source evidence until reviewed.

Two separate statuses must be maintained:
1. `source_curation_status`: `expert_curated_with_pmid`, `expert_curated_provenance_incomplete`, `automated_extraction`, `unresolved_source_type`. This classifies the *source assertion*.
2. `devmap_disposition`: `imported_source_assertion`, `pending_secondary_review`, `reviewed_with_qualification`, `accepted_by_user`, `narrowed_by_user`, `deferred_by_user`, `rejected_by_user`. This identifies the *DevMap treatment*; source import is not equivalent to user acceptance of a new gene disruption claim.

Preserve the original curated claims even when DevMap's newly inferred assertions require further review. For accepted expert source imports, retain the actual PMID rather than substituting a publication count. Identical publications represented in HPO, ClinGen or PubMind are one primary source and should not be counted as independent studies.

The previously stated review stages in this draft contract govern PubMind and newly constructed assertions. The user-approved expert-curation exception above takes precedence for unchanged, provenance-complete source imports. SCUTER independent review remains required for new DevMap biological interpretations and disputable associations.
