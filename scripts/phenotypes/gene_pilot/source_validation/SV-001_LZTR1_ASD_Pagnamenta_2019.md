# DevMap source validation packet SV-001
## LZTR1 and atrial septal defect (HP:0001631)

**Status:** Agent 1 primary-source inspection completed 2026-11-07. Pending independent Agent 2 review and user scientific decision. No accepted PAR emitted.

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
