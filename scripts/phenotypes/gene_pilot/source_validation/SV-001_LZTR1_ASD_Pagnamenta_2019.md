# DevMap source validation packet SV-001
## LZTR1 and atrial septal defect (HP:0001631)

**Status:** Agent 2 primary-text review completed; user scientific disposition on 2026-11-07 is NARROW TO REPORTED DECIPHER OBSERVATION. Original table provenance and the HP:0001631 normalization qualification retained. No direct gene–phenotype PAR emitted.

**Proposed observation:** In Pagnamenta et al. 2019, one individual carrying a reported de novo LZTR1 c.290G>T (p.Arg97Leu) variant was annotated with atrial septal defect in the source Table 1.

**Gene:** LZTR1, HGNC:6742.
**Phenotype:** HP:0001631, atrial septal defect, structural CHD.
**Disease context:** Noonan syndrome, clinically suspected at recruitment.
**Original subject:** DDD individual 303983, NOT an abstract gene subject.
**Variant:** NM_006767.3:c.290G>T (p.Arg97Leu), heterozygous de novo, in LZTR1 KT1 domain.
**Evidence location:** Pagnamenta et al., *Clinical Genetics* 95(6):693–703, 2019, Table 1, individual **303983**, de novo LZTR1 case. Table 1 phenotype cell includes atrial septal defect, hypertrophic cardiomyopathy and ventricular septal defect. Narrative paragraph following Figure 1 and Table 1 identifies individual 303983 and the same de novo variant but explicitly names only HCM and VSD, not ASD. This table/narrative difference should be checked by Agent 2.
**Primary source identifiers:** PMID:30859559, PMCID:PMC6563422, DOI:10.1111/cge.13533.
**Primary full text:** https://onlinelibrary.wiley.com/doi/full/10.1111/cge.13533
**Direct table evidence:** https://onlinelibrary.wiley.com/doi/full/10.1111/cge.13533 (Table 1, individual 303983)
**Independent secondary source:** ClinGen LZTR1–Noonan syndrome gene validity evaluation https://search.clinicalgenome.org/kb/gene-validity/CGGV:assertion_6f21db9c-87ea-4095-96ca-4277eaa21232-2020-04-23T17:00:00.000Z (patient 303983, LZTR1 c.290G>T, ASD HP:0001631). ClinGen's curation confirms transcription of table phenotype but is not a second independent patient observation.
**Related first lead:** Umeki et al., *Human Genetics* 138:21–35, 2019, PMID:30368668, DOI:10.1007/s00439-018-1951-7, reports ASD at cohort abstract level. This is a separate study, not the source of the variant/patient mapping above. Do not conflate its cases with 303983.

### Agent 1 evidence assessment
- Original paper full text HTML read, with source-specific patient/variant/phenotype in Table 1.
- One primary clinical observation is source identified and checked; Table 1 is the controlling clinical record for ASD.
- The paper's narrative omits ASD while listing HCM/VSD for the same patient; this represents a within-paper reporting discrepancy, not necessarily a contradiction or explicit absence.
- Data support an observed association of one person's LZTR1 variant with ASD in suspected Noonan syndrome. Molecular causation of ASD specifically remains to be evaluated with the full gene–disease context and other independent probands.
- No original PubMind PVID link has yet been established; this packet is independent primary-literature evidence, not a claim of recovered PubMind provenance.
- Publication and phenotype observations are source-specific; no gene→disease→phenotype graph traversal used to fabricate the clinical observation.

### Independent review requested from Agent 2
1. Open primary full text, inspect Table 1 (patient 303983), variant call, phenotype cell and adjacent narrative, independently.
2. Verify whether the original table prints ASD (possibly with typo 'Atria septal defect'), check document/author correction or any genotype ambiguity, and confirm source term maps to HP:0001631.
3. Separate the original patient observation from ClinGen secondary curation and Umeki independent cohort. Check if ASD is supported elsewhere in Pagnamenta original materials.
4. Report precise locator, contrary evidence if any, proper assertion subject/variant/disruption class, and one of `supported`, `supported_with_narrowing`, `unresolved`, `contradicted`.
5. Do not infer source PVID or PubMind-specific PMID mapping; await Aditya full variant-level export.

### User decision
Pending (accept / narrow / defer / reject) after Agent 2 primary-source validation. The existing PAR Core claim identity and exporter policy issues remain separate and gate formal accepted PAR emission.


## Agent 2 source review addendum, 2026-11-07 (pending user disposition)

[Claude's source review](https://app.notion.com/41129187800881fca046e55f2ff85766) examined the complete Pagnamenta 2019 primary text after reading Agent 1's source locators. This is a **second source check following prior exposure**, not a blinded review. Agent 2 assigned **supported with narrowing**.

The original Table 1 lists DECIPHER/DDD individual 303983, female, with de novo LZTR1 NM_006767.3:c.290G>T p.(Arg97Leu) (proband/mother/father 1/0/0). Its phenotype cell spells the original term **"Atria septal defect"** alongside HCM and VSD. The article provides no HPO identifier for this cell. Mapping that text to HP:0001631 is a curator-level normalization proposal. The narrative identifies VSD and HCM but does not report ASD, and no original ascertainment modality or age for ASD is stated. The table reproduces a DECIPHER-submitted phenotype observation. It is **one source observation**, not a separately described echocardiographic finding. VSD has concordant table and narrative documentation, whereas ASD is table-only.

**Agent 2 proposed narrowed observation for user decision:** DECIPHER individual 303983, female, reported de novo LZTR1 p.(Arg97Leu), has the DECIPHER-submitted ASD phenotype term published in Pagnamenta Table 1 (PMID 30859559), mapped provisionally to HP:0001631; ASD is absent from the article narrative and its ascertainment details are unspecified. Preserve HCM and VSD as additional co-recorded phenotypes rather than evidence that the ASD mapping was independently confirmed.

Status remains **pending user accept/narrow/defer/reject**. PubMind PVID-to-publication attribution and PAR Core identity are separate. No direct phenotype PAR accepted or minted.


## User scientific disposition, 2026-11-07 (authoritative; supersedes historical pending labels above)

**Decision 2: NARROW TO REPORTED OBSERVATION.** [Approved disposition in the DevMap Communications Log](https://app.notion.com/p/41129187800881eeab02f31b9a936cc5).

**Accepted source observation:** DECIPHER/DDD individual **303983**, female, with a reported de novo LZTR1 `NM_006767.3:c.290G>T`, p.(Arg97Leu), has the original DECIPHER-submitted phenotype term **"Atria septal defect"** in Pagnamenta et al. 2019, *Clinical Genetics*, Table 1, PMID **30859559**, PMCID **PMC6563422**. The original paper does not give HP:0001631 for that table cell. Translating "Atria septal defect" to HP:0001631 is a documented **curator normalization**, retaining the exact original text.

The Results narrative for this individual reports VSD and hypertrophic cardiomyopathy without an ASD description. ASD ascertainment modality and age are unspecified in the publication. ClinGen's secondary use of the same patient and observation does not constitute a second independent patient. The Umeki PMID 30368668 study remains separate from the 303983 record.

**Disposition fields for source validation:** `devmap_disposition=narrowed_by_user`; `accepted_scope=single_DECIPHER_reported_phenotype_observation`; `source_primary_pmid=30859559`; `normalization_status=curator_mapped_to_HP:0001631`; `direct_gene_phenotype_PAR_accepted=false`. These are review annotations, not modifications to the original HPOA, DECIPHER or PubMind source records.

The user did not accept a generalized causal LZTR1 disruption → ASD claim. Original primary evidence, clinical subject, reported variant, phenotype text and separate mapping remain traceable. The original registry and all historical candidate IDs are unchanged.
