# Schema-area index of the 624 released SpectraCQ v2.0 competency questions

This file enumerates all 624 scored competency questions released in SpectraCQ v2.0, generated directly from `cqs/spectra_cq_v2.0/questions.json` (the benchmark's single source of truth; regenerate with `python3 pipeline/generate_cq_index.py`). The full question text, executable reference Cypher (one file per CQ), and per-CQ gold answer sets are shipped under `cqs/spectra_cq_v2.0/` (see `cqs/spectra_cq_v2.0/README.md`). For each CQ this index publishes the **identifier**, **phase**, **category** (carried verbatim from the benchmark metadata; an empty label is shown as *(uncategorized)*), and **schema area exercised**, so third parties can verify at a glance (i) the breadth of the released CQ set and (ii) which ontology classes / relationships each CQ traverses.

**Total**: 624 released CQs across 5 working groups (RAN1=142, RAN2=128, RAN3=123, RAN4=117, RAN5=114) and 5 phases (P1=123, P2=112, P3=233, P4=75, P5=81). 654 CQs were authored in total; 30 are withheld as a held-out set (see `cqs/spectra_cq_v2.0/README.md` for the hold-out policy).

A representative subset of CQs (with full question text and executable Cypher/SPARQL) is in `representative_cqs.md`. A category-by-phase distribution is rendered as `../diagrams/cq_distribution.png`. The design-phase validation evidence that preceded this benchmark is indexed in `../validation/validation_manifest.md`.

## RAN1 (142 CQs)

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `RAN1_P1_CQ1-1` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO} |
| `RAN1_P1_CQ1-2` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN1_P1_CQ1-3` | 1 | CQ1_TdocBasicSearch | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P1_CQ1-4` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Release, Tdoc}; rels={PRESENTED_AT, TARGET_RELEASE} |
| `RAN1_P1_CQ1-5` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN1_P1_CQ1-6` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN1_P1_CQ1-7` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN1_P1_CQ1-8` | 1 | CQ1_TdocBasicSearch | classes={Contact, Tdoc}; rels={HAS_CONTACT} |
| `RAN1_P1_CQ1-9` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN1_P1_CQ2-2` | 1 | CQ2_TdocRelationTracing | classes={Tdoc, WorkingGroup}; rels={CC_TO, ORIGINATED_FROM, SENT_TO} |
| `RAN1_P1_CQ2-3` | 1 | CQ2_TdocRelationTracing | classes={Tdoc}; rels={REPLY_TO} |
| `RAN1_P1_CQ2-4` | 1 | CQ2_TdocRelationTracing | classes={Spec, Tdoc}; rels={MODIFIES} |
| `RAN1_P1_CQ2-5` | 1 | CQ2_TdocRelationTracing | classes={Tdoc} |
| `RAN1_P1_CQ2-6` | 1 | CQ2_TdocRelationTracing | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN1_P1_CQ2-7` | 1 | CQ2_TdocRelationTracing | classes={AgendaItem, Meeting, Tdoc, WorkingGroup}; rels={BELONGS_TO, ORIGINATED_FROM, PRESENTED_AT} |
| `RAN1_P1_CQ3-1` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN1_P1_CQ3-2` | 1 | CQ3_CompanyAnalysis | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P1_CQ3-3` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN1_P1_CQ3-4` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN1_P1_CQ3-5` | 1 | CQ3_CompanyAnalysis | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, SUBMITTED_BY} |
| `RAN1_P1_CQ3-6` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN1_P1_CQ4-1` | 1 | CQ4_MeetingHistory | classes={Company, Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `RAN1_P1_CQ4-2` | 1 | CQ4_MeetingHistory | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P1_CQ4-3` | 1 | CQ4_MeetingHistory | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN1_P2_CQ1-1` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN1_P2_CQ1-2` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN1_P2_CQ1-3` | 2 | CQ1_ResolutionLookup | classes={Conclusion, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ1-4` | 2 | CQ1_ResolutionLookup | classes={Meeting, WorkingAssumption}; rels={MADE_AT} |
| `RAN1_P2_CQ1-5` | 2 | CQ1_ResolutionLookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ1-6` | 2 | CQ1_ResolutionLookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ1-7` | 2 | CQ1_ResolutionLookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ2-1` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Tdoc}; rels={REFERENCES} |
| `RAN1_P2_CQ2-2` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN1_P2_CQ2-3` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ2-4` | 2 | CQ2_TdocResolutionTracing | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN1_P2_CQ2-5` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ3-1` | 2 | CQ3_CompanyContribution | classes={Agreement, Company, Meeting, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN1_P2_CQ3-2` | 2 | CQ3_CompanyContribution | classes={Agreement, Company, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN1_P2_CQ3-3` | 2 | CQ3_CompanyContribution | classes={AgendaItem, Agreement, Company, Tdoc}; rels={REFERENCES, RESOLUTION_BELONGS_TO, SUBMITTED_BY} |
| `RAN1_P2_CQ3-4` | 2 | CQ3_CompanyContribution | classes={Agreement, Company, Meeting, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN1_P2_CQ3-5` | 2 | CQ3_CompanyContribution | classes={Agreement, Company, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN1_P2_CQ3-6` | 2 | CQ3_CompanyContribution | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN1_P2_CQ4-1` | 2 | CQ4_TechLeadership | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, MODERATED_BY} |
| `RAN1_P2_CQ4-2` | 2 | CQ4_TechLeadership | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, MODERATED_BY} |
| `RAN1_P2_CQ4-3` | 2 | CQ4_TechLeadership | classes={Company, Tdoc}; rels={MODERATED_BY} |
| `RAN1_P2_CQ5-1` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-2` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-3` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-4` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-5` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-6` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-7` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-8` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-9` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-10` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-11` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-12` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P2_CQ5-13` | 2 | CQ5_TechTrend | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN1_P3_CQ001` | 3 | TS_Structure | classes={Section, Spec}; rels={HAS_SECTION} |
| `RAN1_P3_CQ002` | 3 | TS_Structure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN1_P3_CQ003` | 3 | TS_Structure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, PARENT_SECTION} |
| `RAN1_P3_CQ004` | 3 | TS_Structure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN1_P3_CQ005` | 3 | TS_Structure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN1_P3_CQ006` | 3 | TS_Structure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN1_P3_CQ007` | 3 | TS_Structure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN1_P3_CQ008` | 3 | TS_Structure | classes={Section, Spec, TSFigure, TSTable}; rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION, TABLE_IN_SECTION} |
| `RAN1_P3_CQ009` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ010` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ011` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ012` | 3 | TS_ReferenceAnalysis | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN1_P3_CQ013` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ014` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ015` | 3 | TS_ReferenceAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN1_P3_CQ016` | 3 | CR_TS_ChangeTracing | classes={Spec}; rels={MODIFIES} |
| `RAN1_P3_CQ017` | 3 | CR_TS_ChangeTracing | classes={Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P3_CQ018` | 3 | CR_TS_ChangeTracing | classes={Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P3_CQ019` | 3 | CR_TS_ChangeTracing | classes={Spec}; rels={MODIFIES} |
| `RAN1_P3_CQ020` | 3 | CR_TS_ChangeTracing | classes={Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `RAN1_P3_CQ021` | 3 | CR_TS_ChangeTracing | classes={Spec}; rels={MODIFIES} |
| `RAN1_P3_CQ022` | 3 | CR_TS_ChangeTracing | classes={Meeting, Spec}; rels={MODIFIES, PRESENTED_AT} |
| `RAN1_P3_CQ023` | 3 | Resolution_TS_DecisionMaking | classes={Agreement, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN1_P3_CQ024` | 3 | Resolution_TS_DecisionMaking | classes={Agreement, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN1_P3_CQ025` | 3 | Resolution_TS_DecisionMaking | classes={Agreement, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN1_P3_CQ026` | 3 | Resolution_TS_DecisionMaking | classes={Agreement, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN1_P3_CQ027` | 3 | Resolution_TS_DecisionMaking | classes={Agreement, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN1_P3_CQ028` | 3 | Resolution_TS_DecisionMaking | classes={Meeting, Resolution, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN1_P3_CQ029` | 3 | Tech_KeywordSearch | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN1_P3_CQ030` | 3 | Tech_KeywordSearch | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN1_P3_CQ031` | 3 | Tech_KeywordSearch | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN1_P3_CQ032` | 3 | Tech_KeywordSearch | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN1_P3_CQ033` | 3 | Tech_KeywordSearch | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN1_P3_CQ034` | 3 | Tech_KeywordSearch | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN1_P3_CQ035` | 3 | Tech_KeywordSearch | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN1_P3_CQ036` | 3 | IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES} |
| `RAN1_P3_CQ037` | 3 | IntegratedAnalysis | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN1_P3_CQ038` | 3 | IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES, REFERENCES_SECTION} |
| `RAN1_P3_CQ039` | 3 | IntegratedAnalysis | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN1_P3_CQ040` | 3 | IntegratedAnalysis | classes={Agreement, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN1_P3_CQ041` | 3 | IntegratedAnalysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN1_P3_CQ042` | 3 | IntegratedAnalysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE, HAS_SUB_SECTION} |
| `RAN1_P3_CQ043` | 3 | IntegratedAnalysis | classes={Company, Meeting, Resolution, Section, Spec, TSFigure, TSTable} |
| `RAN1_P3_CQ044` | 3 | CR_TS_ChangeTracing | classes={Spec, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `RAN1_P3_CQ045` | 3 | Resolution_TS_DecisionMaking | classes={Resolution, Spec, WorkItem}; rels={MODIFIES, REFERENCES, RELATED_TO} |
| `RAN1_P3_P3-S8-CQ01` | 3 | CQ_Step8_EntityCount | — |
| `RAN1_P3_P3-S8-CQ02` | 3 | CQ_Step8_DefinedInSection | classes={Section} |
| `RAN1_P3_P3-S8-CQ04` | 3 | CQ_Step8_FeatureDisjoint | classes={Feature} |
| `RAN1_P3_P3-S8-CQ05` | 3 | CQ_Step8_GranularityDump | — |
| `RAN1_P3_P3-S8-CQ06` | 3 | CQ_Step8_CoreIE_Baseline | classes={RRCParameter} |
| `RAN1_P3_P3-S8-CQ08` | 3 | CQ_Step8_FeatureCatalogParity | classes={Feature} |
| `RAN1_P4_CQ1-1` | 4 | CQ1_CRChangeRationale | — |
| `RAN1_P4_CQ1-2` | 4 | CQ1_CRChangeRationale | — |
| `RAN1_P4_CQ1-3` | 4 | CQ1_CRChangeRationale | classes={WorkItem}; rels={RELATED_TO} |
| `RAN1_P4_CQ2-1` | 4 | CQ2_CrossSpecImpact | classes={Spec} |
| `RAN1_P4_CQ2-2` | 4 | CQ2_CrossSpecImpact | classes={Spec}; rels={AFFECTS_CORE_SPEC, MODIFIES} |
| `RAN1_P4_CQ2-3` | 4 | CQ2_CrossSpecImpact | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN1_P4_CQ2-4` | 4 | CQ2_CrossSpecImpact | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN1_P4_CQ3-1` | 4 | CQ3_CRPackAnalysis | classes={CRPack}; rels={HAS_CR} |
| `RAN1_P4_CQ3-2` | 4 | CQ3_CRPackAnalysis | classes={CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `RAN1_P4_CQ3-3` | 4 | CQ3_CRPackAnalysis | classes={CRPack}; rels={HAS_CR} |
| `RAN1_P4_CQ4-1` | 4 | CQ4_LinkedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN1_P4_CQ4-2` | 4 | CQ4_LinkedAnalysis | classes={Resolution}; rels={REFERENCES} |
| `RAN1_P4_CQ4-3` | 4 | CQ4_LinkedAnalysis | classes={Spec, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `RAN1_P4_CQ4-4` | 4 | CQ4_LinkedAnalysis | classes={Company, Spec}; rels={AFFECTS_CORE_SPEC, SUBMITTED_BY} |
| `RAN1_P4_CQ4-5` | 4 | CQ4_LinkedAnalysis | classes={Meeting, Resolution}; rels={MADE_AT, REFERENCES} |
| `RAN1_P5_CQ1-1` | 5 | CQ1_TRStudyStatus | classes={TechnicalReport} |
| `RAN1_P5_CQ1-2` | 5 | CQ1_TRStudyStatus | classes={TechnicalReport} |
| `RAN1_P5_CQ1-3` | 5 | CQ1_TRStudyStatus | classes={TechnicalReport} |
| `RAN1_P5_CQ1-4` | 5 | CQ1_TRStudyStatus | classes={TechnicalReport} |
| `RAN1_P5_CQ2-1` | 5 | CQ2_TSImpactTracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN1_P5_CQ2-2` | 5 | CQ2_TSImpactTracing | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `RAN1_P5_CQ2-3` | 5 | CQ2_TSImpactTracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN1_P5_CQ2-4` | 5 | CQ2_TSImpactTracing | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `RAN1_P5_CQ2-5` | 5 | CQ2_TSImpactTracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN1_P5_CQ3-1` | 5 | CQ3_TechImpactScope | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `RAN1_P5_CQ3-2` | 5 | CQ3_TechImpactScope | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `RAN1_P5_CQ3-3` | 5 | CQ3_TechImpactScope | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN1_P5_CQ4-1` | 5 | CQ4_PerReleaseStudyImpact | classes={Release, Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC, TARGET_RELEASE} |
| `RAN1_P5_CQ4-2` | 5 | CQ4_PerReleaseStudyImpact | classes={TechnicalReport} |
| `RAN1_P5_CQ4-3` | 5 | CQ4_PerReleaseStudyImpact | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN1_P5_CQ5-1` | 5 | CQ5_TRCrossReference | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `RAN1_P5_CQ5-2` | 5 | CQ5_TRCrossReference | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `RAN1_P5_CQ5-3` | 5 | CQ5_TRCrossReference | classes={TechnicalReport}; rels={REFERENCES_TR} |

## RAN2 (128 CQs)

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `RAN2_P1_CQ1-1` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO} |
| `RAN2_P1_CQ1-2` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN2_P1_CQ1-3` | 1 | CQ1_TdocBasicSearch | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN2_P1_CQ1-4` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Release, Tdoc}; rels={PRESENTED_AT, TARGET_RELEASE} |
| `RAN2_P1_CQ1-5` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN2_P1_CQ1-6` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN2_P1_CQ1-7` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN2_P1_CQ1-8` | 1 | CQ1_TdocBasicSearch | classes={Contact, Tdoc}; rels={HAS_CONTACT} |
| `RAN2_P1_CQ1-9` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN2_P1_CQ2-1` | 1 | CQ2_TdocRelationTracing | classes={Tdoc}; rels={IS_REVISION_OF, REVISED_TO} |
| `RAN2_P1_CQ2-2` | 1 | CQ2_TdocRelationTracing | classes={Tdoc, WorkingGroup}; rels={CC_TO, ORIGINATED_FROM, SENT_TO} |
| `RAN2_P1_CQ2-3` | 1 | CQ2_TdocRelationTracing | classes={Tdoc}; rels={REPLY_TO} |
| `RAN2_P1_CQ2-4` | 1 | CQ2_TdocRelationTracing | classes={Spec, Tdoc}; rels={MODIFIES} |
| `RAN2_P1_CQ2-5` | 1 | CQ2_TdocRelationTracing | classes={Tdoc} |
| `RAN2_P1_CQ2-6` | 1 | CQ2_TdocRelationTracing | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN2_P1_CQ2-7` | 1 | CQ2_TdocRelationTracing | classes={AgendaItem, Meeting}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN2_P1_CQ3-1` | 1 | CQ3_CompanyAnalysis | classes={Company, Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `RAN2_P1_CQ3-2` | 1 | CQ3_CompanyAnalysis | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `RAN2_P1_CQ3-3` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN2_P1_CQ3-4` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN2_P1_CQ3-5` | 1 | CQ3_CompanyAnalysis | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `RAN2_P1_CQ3-6` | 1 | CQ3_CompanyAnalysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN2_P1_CQ4-1` | 1 | CQ4_MeetingHistory | classes={Company, Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `RAN2_P1_CQ4-2` | 1 | CQ4_MeetingHistory | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN2_P1_CQ4-3` | 1 | CQ4_MeetingHistory | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN2_P2_CQ1-1` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN2_P2_CQ1-2` | 2 | CQ1_ResolutionLookup | classes={Conclusion, Meeting}; rels={MADE_AT} |
| `RAN2_P2_CQ1-3` | 2 | CQ1_ResolutionLookup | classes={Meeting, WorkingAssumption}; rels={MADE_AT} |
| `RAN2_P2_CQ1-4` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Meeting, Resolution}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN2_P2_CQ1-5` | 2 | CQ1_ResolutionLookup | classes={Meeting, Release, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, TARGET_RELEASE} |
| `RAN2_P2_CQ1-6` | 2 | CQ1_ResolutionLookup | classes={Meeting, Resolution, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN2_P2_CQ1-7` | 2 | CQ1_ResolutionLookup | classes={Meeting, Resolution, Tdoc, WorkItem}; rels={MADE_AT, REFERENCES, RELATED_TO} |
| `RAN2_P2_CQ1-8` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN2_P2_CQ2-1` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN2_P2_CQ2-2` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Tdoc}; rels={REFERENCES} |
| `RAN2_P2_CQ2-3` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN2_P2_CQ2-4` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN2_P2_CQ3-1` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN2_P2_CQ3-2` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES, SUBMITTED_BY} |
| `RAN2_P2_CQ3-3` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc, WorkItem}; rels={REFERENCES, RELATED_TO, SUBMITTED_BY} |
| `RAN2_P2_CQ3-4` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN2_P2_CQ6-1` | 2 | CQ6_TrendComparison | classes={Meeting, Release, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, TARGET_RELEASE} |
| `RAN2_P2_CQ6-2` | 2 | CQ6_TrendComparison | classes={Company, Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN2_P2_CQ1-9` | 2 | CQ1_ResolutionLookup | classes={Agreement, Conclusion, Resolution, WorkingAssumption} |
| `RAN2_P2_CQ1-10` | 2 | CQ1_ResolutionLookup | classes={Agreement, Conclusion, Meeting, Resolution, WorkingAssumption}; rels={MADE_AT} |
| `RAN2_P2_CQ2-5` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN2_P2_CQ2-6` | 2 | CQ2_TdocResolutionTracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN2_P2_CQ3-5` | 2 | CQ3_CompanyContribution | classes={Company, Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN2_P2_CQ6-3` | 2 | CQ6_TrendComparison | classes={Agreement, Meeting}; rels={MADE_AT} |
| `RAN2_P2_CQ6-4` | 2 | CQ6_TrendComparison | classes={Conclusion, Meeting}; rels={MADE_AT} |
| `RAN2_P3_CQ1-1` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN2_P3_CQ1-2` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN2_P3_CQ1-3` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, PARENT_SECTION} |
| `RAN2_P3_CQ1-4` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN2_P3_CQ1-5` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN2_P3_CQ1-6` | 3 | CQ1_TSStructure | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, CONTAINS_FIGURE} |
| `RAN2_P3_CQ1-7` | 3 | CQ1_TSStructure | classes={Section, TSTable}; rels={TABLE_IN_SECTION} |
| `RAN2_P3_CQ1-8` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN2_P3_CQ1-9` | 3 | CQ1_TSStructure | classes={Section} |
| `RAN2_P3_CQ1-10` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN2_P3_CQ2-1` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ2-2` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ2-3` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ2-4` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN2_P3_CQ2-5` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ3-1` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN2_P3_CQ3-2` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN2_P3_CQ3-3` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN2_P3_CQ3-4` | 3 | CQ3_CRLinkage | — |
| `RAN2_P3_CQ3-5` | 3 | CQ3_CRLinkage | classes={Spec, Tdoc, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `RAN2_P3_CQ3-6` | 3 | CQ3_CRLinkage | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN2_P3_CQ4-1` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN2_P3_CQ4-2` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN2_P3_CQ5-1` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN2_P3_CQ5-2` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN2_P3_CQ1-11` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN2_P3_CQ1-12` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN2_P3_CQ1-13` | 3 | CQ1_TSStructure | classes={Section} |
| `RAN2_P3_CQ1-14` | 3 | CQ1_TSStructure | classes={Section, TSFigure, TSTable} |
| `RAN2_P3_CQ1-15` | 3 | CQ1_TSStructure | classes={Section, TSTable}; rels={CONTAINS_TABLE} |
| `RAN2_P3_CQ1-16` | 3 | CQ1_TSStructure | classes={Section, TSFigure}; rels={CONTAINS_FIGURE} |
| `RAN2_P3_CQ2-6` | 3 | CQ2_TSCrossReference | rels={REFERENCES_SECTION} |
| `RAN2_P3_CQ2-7` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ2-8` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN2_P3_CQ3-7` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN2_P3_CQ3-8` | 3 | CQ3_CRLinkage | classes={Release, Spec}; rels={MODIFIES, TARGET_RELEASE} |
| `RAN2_P3_CQ4-3` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN2_P3_CQ4-4` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN2_P3_CQ5-3` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN2_P3_CQ5-4` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN2_P3_CQ5-5` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION} |
| `RAN2_P3_P3-S8-CQ01` | 3 | CQ_Step8_EntityCount | — |
| `RAN2_P3_P3-S8-CQ02` | 3 | CQ_Step8_DefinedInSection | classes={Section} |
| `RAN2_P3_P3-S8-CQ04` | 3 | CQ_Step8_FeatureDisjoint | classes={Feature} |
| `RAN2_P3_P3-S8-CQ05` | 3 | CQ_Step8_GranularityDump | — |
| `RAN2_P3_P3-S8-CQ06` | 3 | CQ_Step8_CoreIE_Baseline | classes={RRCParameter} |
| `RAN2_P3_P3-S8-CQ07` | 3 | CQ_Step8_LTM_Capabilities | classes={CapabilityItem} |
| `RAN2_P3_P3-S8-CQ08` | 3 | CQ_Step8_FeatureCatalogParity | classes={Feature} |
| `RAN2_P4_CQ1-1` | 4 | CQ1_ChangeRationale | — |
| `RAN2_P4_CQ1-2` | 4 | CQ1_ChangeRationale | — |
| `RAN2_P4_CQ1-3` | 4 | CQ1_ChangeRationale | — |
| `RAN2_P4_CQ2-1` | 4 | CQ2_CrossSpec | classes={Spec} |
| `RAN2_P4_CQ2-2` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC, MODIFIES} |
| `RAN2_P4_CQ2-3` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN2_P4_CQ2-4` | 4 | CQ2_CrossSpec | — |
| `RAN2_P4_CQ3-1` | 4 | CQ3_CRPack | classes={CRPack}; rels={HAS_CR} |
| `RAN2_P4_CQ3-2` | 4 | CQ3_CRPack | classes={CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `RAN2_P4_CQ3-3` | 4 | CQ3_CRPack | classes={CRPack} |
| `RAN2_P4_CQ4-1` | 4 | CQ4_LinkedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES_SECTION} |
| `RAN2_P4_CQ4-2` | 4 | CQ4_LinkedAnalysis | classes={Agreement}; rels={REFERENCES} |
| `RAN2_P4_CQ4-3` | 4 | CQ4_LinkedAnalysis | classes={Section, WorkItem}; rels={MODIFIES_SECTION, RELATED_TO} |
| `RAN2_P4_CQ4-4` | 4 | CQ4_LinkedAnalysis | classes={Company, Spec}; rels={AFFECTS_CORE_SPEC, SUBMITTED_BY} |
| `RAN2_P4_CQ4-5` | 4 | CQ4_LinkedAnalysis | classes={Agreement, Meeting}; rels={MADE_AT, REFERENCES} |
| `RAN2_P5_TR-CQ-1-1` | 5 | *(uncategorized)* | classes={Release, TechnicalReport}; rels={TARGET_RELEASE} |
| `RAN2_P5_TR-CQ-1-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN2_P5_TR-CQ-1-3` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN2_P5_TR-CQ-1-4` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN2_P5_TR-CQ-2-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN2_P5_TR-CQ-2-2` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN2_P5_TR-CQ-2-3` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN2_P5_TR-CQ-2-4` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN2_P5_TR-CQ-2-5` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN2_P5_TR-CQ-3-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN2_P5_TR-CQ-3-2` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN2_P5_TR-CQ-3-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN2_P5_TR-CQ-4-1` | 5 | *(uncategorized)* | classes={Release, Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC, TARGET_RELEASE} |
| `RAN2_P5_TR-CQ-4-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN2_P5_TR-CQ-4-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |

## RAN3 (123 CQs)

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `RAN3_P1_CQ1-1` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO} |
| `RAN3_P1_CQ1-2` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN3_P1_CQ1-3` | 1 | CQ1_TdocBasicSearch | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN3_P1_CQ1-4` | 1 | CQ1_TdocBasicSearch | classes={Release, Tdoc}; rels={TARGET_RELEASE} |
| `RAN3_P1_CQ1-5` | 1 | CQ1_TdocBasicSearch | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN3_P1_CQ1-6` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN3_P1_CQ1-7` | 1 | CQ1_TdocBasicSearch | classes={Tdoc} |
| `RAN3_P1_CQ1-8` | 1 | CQ1_TdocBasicSearch | classes={Contact, Tdoc}; rels={HAS_CONTACT} |
| `RAN3_P1_CQ1-9` | 1 | CQ1_TdocBasicSearch | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN3_P1_CQ2-1` | 1 | CQ2_TdocRelationTracing | classes={Tdoc}; rels={IS_REVISION_OF} |
| `RAN3_P1_CQ2-2` | 1 | CQ2_TdocRelationTracing | classes={Tdoc, WorkingGroup}; rels={CC_TO, ORIGINATED_FROM, SENT_TO} |
| `RAN3_P1_CQ2-3` | 1 | CQ2_TdocRelationTracing | classes={Tdoc}; rels={REPLY_TO} |
| `RAN3_P1_CQ2-4` | 1 | CQ2_TdocRelationTracing | classes={Spec}; rels={MODIFIES} |
| `RAN3_P1_CQ2-5` | 1 | CQ2_TdocRelationTracing | — |
| `RAN3_P1_CQ2-6` | 1 | CQ2_TdocRelationTracing | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN3_P1_CQ2-7` | 1 | CQ2_TdocRelationTracing | classes={Meeting}; rels={PRESENTED_AT} |
| `RAN3_P1_CQ3-1` | 1 | CQ3_CompanyCompetitors | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN3_P1_CQ3-2` | 1 | CQ3_CompanyCompetitors | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `RAN3_P1_CQ3-3` | 1 | CQ3_CompanyCompetitors | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN3_P1_CQ3-4` | 1 | CQ3_CompanyCompetitors | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN3_P1_CQ3-5` | 1 | CQ3_CompanyCompetitors | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `RAN3_P1_CQ3-6` | 1 | CQ3_CompanyCompetitors | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `RAN3_P1_CQ4-1` | 1 | CQ4_HistorySummary | classes={Company, Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `RAN3_P1_CQ4-2` | 1 | CQ4_HistorySummary | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `RAN3_P1_CQ4-3` | 1 | CQ4_HistorySummary | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `RAN3_P2_CQ1-1` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ1-2` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Conclusion, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ1-3` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Meeting, WorkingAssumption}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ1-4` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Meeting, Resolution}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ1-5` | 2 | CQ1_ResolutionLookup | classes={Meeting, Release, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, TARGET_RELEASE} |
| `RAN3_P2_CQ1-6` | 2 | CQ1_ResolutionLookup | classes={Meeting, Resolution, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN3_P2_CQ1-8` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ2-1` | 2 | CQ2_TdocResolutionTracing | classes={Resolution, Tdoc}; rels={REFERENCES} |
| `RAN3_P2_CQ2-2` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN3_P2_CQ2-3` | 2 | CQ2_TdocResolutionTracing | classes={Resolution} |
| `RAN3_P2_CQ2-4` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN3_P2_CQ3-1` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN3_P2_CQ3-2` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN3_P2_CQ3-3` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES, SUBMITTED_BY} |
| `RAN3_P2_CQ3-4` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN3_P2_CQ4-1` | 2 | CQ4_ModeratorRole | classes={AgendaItem, Company, Meeting, Summary}; rels={MADE_AT, MODERATED_BY, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ4-2` | 2 | CQ4_ModeratorRole | classes={AgendaItem, Company, Meeting, Summary}; rels={MADE_AT, MODERATED_BY, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ4-3` | 2 | CQ4_ModeratorRole | classes={Company, Summary}; rels={MODERATED_BY} |
| `RAN3_P2_CQ6-1` | 2 | CQ6_TrendComparison | classes={AgendaItem, Meeting, Resolution}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN3_P2_CQ6-2` | 2 | CQ6_TrendComparison | classes={Company, Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN3_P2_CQ6-3` | 2 | CQ6_TrendComparison | classes={Company, Meeting, Summary}; rels={MADE_AT, MODERATED_BY} |
| `RAN3_P3_CQ1-1` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN3_P3_CQ1-2` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN3_P3_CQ1-3` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, PARENT_SECTION} |
| `RAN3_P3_CQ1-4` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN3_P3_CQ1-5` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN3_P3_CQ1-6` | 3 | CQ1_TSStructure | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, CONTAINS_FIGURE} |
| `RAN3_P3_CQ1-7` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN3_P3_CQ1-8` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN3_P3_CQ1-9` | 3 | CQ1_TSStructure | classes={Section} |
| `RAN3_P3_CQ1-10` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN3_P3_CQ2-1` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN3_P3_CQ2-2` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN3_P3_CQ2-3` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN3_P3_CQ2-4` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN3_P3_CQ2-5` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={REFERENCES_SPEC} |
| `RAN3_P3_CQ3-1` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN3_P3_CQ3-2` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN3_P3_CQ3-3` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN3_P3_CQ3-4` | 3 | CQ3_CRLinkage | — |
| `RAN3_P3_CQ3-5` | 3 | CQ3_CRLinkage | classes={Spec, Tdoc, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `RAN3_P3_CQ3-6` | 3 | CQ3_CRLinkage | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN3_P3_CQ4-1` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN3_P3_CQ4-2` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN3_P3_CQ5-1` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN3_P3_CQ5-2` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN3_P3_CQ1-11` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN3_P3_CQ1-12` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN3_P3_CQ1-13` | 3 | CQ1_TSStructure | classes={Section} |
| `RAN3_P3_CQ1-14` | 3 | CQ1_TSStructure | classes={Section, TSFigure, TSTable} |
| `RAN3_P3_CQ1-15` | 3 | CQ1_TSStructure | classes={Section, TSTable}; rels={CONTAINS_TABLE} |
| `RAN3_P3_CQ1-16` | 3 | CQ1_TSStructure | classes={Section, TSFigure}; rels={CONTAINS_FIGURE} |
| `RAN3_P3_CQ2-6` | 3 | CQ2_TSCrossReference | rels={REFERENCES_SECTION} |
| `RAN3_P3_CQ2-7` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN3_P3_CQ2-8` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN3_P3_CQ3-7` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN3_P3_CQ3-8` | 3 | CQ3_CRLinkage | classes={Release, Spec}; rels={MODIFIES, TARGET_RELEASE} |
| `RAN3_P3_CQ4-3` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN3_P3_CQ4-4` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN3_P3_CQ5-3` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN3_P3_CQ5-4` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN3_P3_CQ5-5` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION} |
| `RAN3_P3_P3-S8-CQ01` | 3 | CQ_Step8_EntityCount | — |
| `RAN3_P3_P3-S8-CQ02` | 3 | CQ_Step8_DefinedInSection | classes={Section} |
| `RAN3_P3_P3-S8-CQ05` | 3 | CQ_Step8_GranularityDump | — |
| `RAN3_P3_P3-S8-CQ06` | 3 | CQ_Step8_CoreIE_Baseline | classes={RRCParameter} |
| `RAN3_P3_P3-S8-CQ08` | 3 | CQ_Step8_FeatureCatalogParity | classes={Feature} |
| `RAN3_P4_CQ1-1` | 4 | CQ1_ChangeRationale | — |
| `RAN3_P4_CQ1-2` | 4 | CQ1_ChangeRationale | — |
| `RAN3_P4_CQ1-3` | 4 | CQ1_ChangeRationale | — |
| `RAN3_P4_CQ2-1` | 4 | CQ2_CrossSpec | classes={Spec} |
| `RAN3_P4_CQ2-2` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC, MODIFIES} |
| `RAN3_P4_CQ2-3` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN3_P4_CQ2-4` | 4 | CQ2_CrossSpec | — |
| `RAN3_P4_CQ3-1` | 4 | CQ3_CRPack | classes={CRPack}; rels={HAS_CR} |
| `RAN3_P4_CQ3-2` | 4 | CQ3_CRPack | classes={CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `RAN3_P4_CQ3-3` | 4 | CQ3_CRPack | classes={CRPack} |
| `RAN3_P4_CQ4-1` | 4 | CQ4_LinkedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES_SECTION} |
| `RAN3_P4_CQ4-2` | 4 | CQ4_LinkedAnalysis | classes={Agreement}; rels={REFERENCES} |
| `RAN3_P4_CQ4-3` | 4 | CQ4_LinkedAnalysis | classes={Section, WorkItem}; rels={MODIFIES_SECTION, RELATED_TO} |
| `RAN3_P4_CQ4-4` | 4 | CQ4_LinkedAnalysis | classes={Company, Spec}; rels={AFFECTS_CORE_SPEC, SUBMITTED_BY} |
| `RAN3_P4_CQ4-5` | 4 | CQ4_LinkedAnalysis | classes={Agreement, Meeting}; rels={MADE_AT, REFERENCES} |
| `RAN3_P5_TR-CQ-1-1` | 5 | *(uncategorized)* | classes={Release, TechnicalReport}; rels={TARGET_RELEASE} |
| `RAN3_P5_TR-CQ-1-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN3_P5_TR-CQ-1-3` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN3_P5_TR-CQ-1-4` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN3_P5_TR-CQ-2-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-2-2` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN3_P5_TR-CQ-2-3` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN3_P5_TR-CQ-2-4` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN3_P5_TR-CQ-2-5` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-3-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-3-2` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-3-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-4-1` | 5 | *(uncategorized)* | classes={Release, Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC, TARGET_RELEASE} |
| `RAN3_P5_TR-CQ-4-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN3_P5_TR-CQ-4-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN3_P5_TR-CQ-5-3` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |

## RAN4 (117 CQs)

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `RAN4_P1_CQ1-1` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN4_P1_CQ1-2` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN4_P1_CQ1-3` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN4_P1_CQ1-4` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN4_P1_CQ1-5` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN4_P1_CQ2-1` | 1 | *(uncategorized)* | classes={Release, Tdoc}; rels={TARGET_RELEASE} |
| `RAN4_P1_CQ2-2` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN4_P1_CQ2-3` | 1 | *(uncategorized)* | classes={Tdoc, WorkItem}; rels={RELATED_TO} |
| `RAN4_P1_CQ3-1` | 1 | *(uncategorized)* | classes={AgendaItem, Tdoc}; rels={BELONGS_TO} |
| `RAN4_P1_CQ3-2` | 1 | *(uncategorized)* | classes={Tdoc} |
| `RAN4_P1_CQ3-3` | 1 | *(uncategorized)* | classes={Company}; rels={SUBMITTED_BY} |
| `RAN4_P1_CQ4-2` | 1 | *(uncategorized)* | classes={WorkingGroup}; rels={SENT_TO} |
| `RAN4_P1_CQ5-1` | 1 | *(uncategorized)* | — |
| `RAN4_P1_CQ5-2` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN4_P1_CQ5-3` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN4_P1_CQ5-4` | 1 | *(uncategorized)* | classes={Release, Tdoc}; rels={TARGET_RELEASE} |
| `RAN4_P1_CQ5-5` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN4_P1_CQ6-1` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN4_P1_CQ6-2` | 1 | *(uncategorized)* | classes={Meeting} |
| `RAN4_P1_CQ6-3` | 1 | *(uncategorized)* | classes={Tdoc} |
| `RAN4_P1_CQ6-4` | 1 | *(uncategorized)* | — |
| `RAN4_P1_CQ6-5` | 1 | *(uncategorized)* | classes={Contact} |
| `RAN4_P1_CQ7-1` | 1 | *(uncategorized)* | classes={AgendaItem} |
| `RAN4_P1_CQ7-2` | 1 | *(uncategorized)* | classes={WorkItem} |
| `RAN4_P2_CQ1-1` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN4_P2_CQ1-2` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Conclusion, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN4_P2_CQ1-3` | 2 | CQ1_ResolutionLookup | classes={Meeting, WorkingAssumption}; rels={MADE_AT} |
| `RAN4_P2_CQ1-4` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Meeting, Resolution}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `RAN4_P2_CQ1-5` | 2 | CQ1_ResolutionLookup | classes={Meeting, Release, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, TARGET_RELEASE} |
| `RAN4_P2_CQ1-6` | 2 | CQ1_ResolutionLookup | classes={Meeting, Resolution, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN4_P2_CQ1-8` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN4_P2_CQ2-1` | 2 | CQ2_TdocResolutionTracing | classes={Resolution, Tdoc}; rels={REFERENCES} |
| `RAN4_P2_CQ2-2` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN4_P2_CQ2-3` | 2 | CQ2_TdocResolutionTracing | classes={Resolution} |
| `RAN4_P2_CQ2-4` | 2 | CQ2_TdocResolutionTracing | classes={Meeting, Resolution, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN4_P2_CQ3-1` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN4_P2_CQ3-2` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN4_P2_CQ3-3` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES, SUBMITTED_BY} |
| `RAN4_P2_CQ3-4` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN4_P2_CQ6-1` | 2 | CQ6_TrendComparison | classes={AgendaItem, Meeting, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN4_P2_CQ6-2` | 2 | CQ6_TrendComparison | classes={Company, Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN4_P3_CQ1-1` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-2` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN4_P3_CQ1-3` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, PARENT_SECTION} |
| `RAN4_P3_CQ1-4` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-5` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN4_P3_CQ1-6` | 3 | CQ1_TSStructure | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, CONTAINS_FIGURE} |
| `RAN4_P3_CQ1-7` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN4_P3_CQ1-8` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN4_P3_CQ1-9` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-10` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN4_P3_CQ1-11` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-12` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN4_P3_CQ1-13` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-15` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ1-16` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN4_P3_CQ2-1` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN4_P3_CQ2-2` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN4_P3_CQ2-3` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN4_P3_CQ2-4` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN4_P3_CQ2-5` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN4_P3_CQ2-6` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SPEC} |
| `RAN4_P3_CQ2-7` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SPEC} |
| `RAN4_P3_CQ2-8` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN4_P3_CQ3-1` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN4_P3_CQ3-2` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN4_P3_CQ3-3` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN4_P3_CQ3-4` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN4_P3_CQ3-5` | 3 | CQ3_CRLinkage | classes={Spec, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `RAN4_P3_CQ3-6` | 3 | CQ3_CRLinkage | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN4_P3_CQ3-7` | 3 | CQ3_CRLinkage | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN4_P3_CQ3-8` | 3 | CQ3_CRLinkage | classes={Release, Spec}; rels={MODIFIES, TARGET_RELEASE} |
| `RAN4_P3_CQ4-1` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN4_P3_CQ4-2` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec}; rels={MODIFIES, REFERENCES} |
| `RAN4_P3_CQ4-3` | 3 | CQ4_ResolutionLinkage | classes={Meeting, Spec}; rels={MODIFIES, PRESENTED_AT} |
| `RAN4_P3_CQ4-4` | 3 | CQ4_ResolutionLinkage | classes={Resolution, Spec, WorkItem}; rels={MODIFIES, REFERENCES, RELATED_TO} |
| `RAN4_P3_CQ5-1` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN4_P3_CQ5-2` | 3 | CQ5_IntegratedAnalysis | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN4_P3_CQ5-3` | 3 | CQ5_IntegratedAnalysis | classes={Release, Spec}; rels={MODIFIES, TARGET_RELEASE} |
| `RAN4_P3_CQ5-4` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN4_P3_P3-S8-CQ01` | 3 | CQ_Step8_EntityCount | — |
| `RAN4_P3_P3-S8-CQ02` | 3 | CQ_Step8_DefinedInSection | classes={Section} |
| `RAN4_P3_P3-S8-CQ05` | 3 | CQ_Step8_GranularityDump | — |
| `RAN4_P3_P3-S8-CQ06` | 3 | CQ_Step8_CoreIE_Baseline | classes={RRCParameter} |
| `RAN4_P3_P3-S8-CQ08` | 3 | CQ_Step8_FeatureCatalogParity | classes={Feature} |
| `RAN4_P4_CQ1-1` | 4 | CQ1_ChangeRationale | — |
| `RAN4_P4_CQ1-2` | 4 | CQ1_ChangeRationale | — |
| `RAN4_P4_CQ1-3` | 4 | CQ1_ChangeRationale | — |
| `RAN4_P4_CQ2-1` | 4 | CQ2_CrossSpec | classes={Spec} |
| `RAN4_P4_CQ2-2` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC, MODIFIES} |
| `RAN4_P4_CQ2-3` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN4_P4_CQ2-4` | 4 | CQ2_CrossSpec | — |
| `RAN4_P4_CQ3-1` | 4 | CQ3_CRPack | classes={CRPack}; rels={HAS_CR} |
| `RAN4_P4_CQ3-2` | 4 | CQ3_CRPack | classes={CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `RAN4_P4_CQ3-3` | 4 | CQ3_CRPack | classes={CRPack} |
| `RAN4_P4_CQ4-1` | 4 | CQ4_LinkedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES_SECTION} |
| `RAN4_P4_CQ4-2` | 4 | CQ4_LinkedAnalysis | classes={Agreement}; rels={REFERENCES} |
| `RAN4_P4_CQ4-3` | 4 | CQ4_LinkedAnalysis | classes={Section, WorkItem}; rels={MODIFIES_SECTION, RELATED_TO} |
| `RAN4_P4_CQ4-4` | 4 | CQ4_LinkedAnalysis | classes={Company, Spec}; rels={AFFECTS_CORE_SPEC, SUBMITTED_BY} |
| `RAN4_P4_CQ4-5` | 4 | CQ4_LinkedAnalysis | classes={Agreement, Meeting, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN4_P5_CQ1-1` | 5 | *(uncategorized)* | classes={Release, TechnicalReport}; rels={TARGET_RELEASE} |
| `RAN4_P5_CQ1-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN4_P5_CQ1-3` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN4_P5_CQ1-4` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN4_P5_CQ2-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ2-2` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN4_P5_CQ2-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ2-4` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ2-5` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ3-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ3-2` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ3-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ4-1` | 5 | *(uncategorized)* | classes={Release, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, TARGET_RELEASE} |
| `RAN4_P5_CQ4-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN4_P5_CQ4-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN4_P5_CQ5-2` | 5 | *(uncategorized)* | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `RAN4_P5_CQ5-3` | 5 | *(uncategorized)* | classes={TechnicalReport}; rels={REFERENCES_TR} |

## RAN5 (114 CQs)

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `RAN5_P1_CQ1-1` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN5_P1_CQ1-2` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN5_P1_CQ1-3` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN5_P1_CQ1-4` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN5_P1_CQ1-5` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN5_P1_CQ2-1` | 1 | *(uncategorized)* | classes={Release, Tdoc}; rels={TARGET_RELEASE} |
| `RAN5_P1_CQ2-2` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN5_P1_CQ2-3` | 1 | *(uncategorized)* | classes={Tdoc, WorkItem}; rels={RELATED_TO} |
| `RAN5_P1_CQ3-1` | 1 | *(uncategorized)* | classes={AgendaItem, Tdoc}; rels={BELONGS_TO} |
| `RAN5_P1_CQ3-2` | 1 | *(uncategorized)* | classes={Tdoc} |
| `RAN5_P1_CQ3-3` | 1 | *(uncategorized)* | classes={Company}; rels={SUBMITTED_BY} |
| `RAN5_P1_CQ4-1` | 1 | *(uncategorized)* | classes={Tdoc}; rels={IS_REVISION_OF} |
| `RAN5_P1_CQ4-2` | 1 | *(uncategorized)* | classes={WorkingGroup}; rels={SENT_TO} |
| `RAN5_P1_CQ5-1` | 1 | *(uncategorized)* | — |
| `RAN5_P1_CQ5-2` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN5_P1_CQ5-3` | 1 | *(uncategorized)* | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `RAN5_P1_CQ5-4` | 1 | *(uncategorized)* | classes={Release, Tdoc}; rels={TARGET_RELEASE} |
| `RAN5_P1_CQ5-5` | 1 | *(uncategorized)* | classes={Spec}; rels={MODIFIES} |
| `RAN5_P1_CQ6-1` | 1 | *(uncategorized)* | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `RAN5_P1_CQ6-2` | 1 | *(uncategorized)* | classes={Meeting} |
| `RAN5_P1_CQ6-3` | 1 | *(uncategorized)* | classes={Tdoc} |
| `RAN5_P1_CQ6-4` | 1 | *(uncategorized)* | — |
| `RAN5_P1_CQ6-5` | 1 | *(uncategorized)* | classes={Contact} |
| `RAN5_P1_CQ7-1` | 1 | *(uncategorized)* | classes={AgendaItem} |
| `RAN5_P1_CQ7-2` | 1 | *(uncategorized)* | classes={WorkItem} |
| `RAN5_P2_CQ1-1` | 2 | CQ1_ResolutionLookup | classes={Conclusion, Meeting}; rels={MADE_AT} |
| `RAN5_P2_CQ1-2` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN5_P2_CQ1-3` | 2 | CQ1_ResolutionLookup | classes={Release, Resolution, Tdoc}; rels={REFERENCES, TARGET_RELEASE} |
| `RAN5_P2_CQ1-4` | 2 | CQ1_ResolutionLookup | classes={Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES} |
| `RAN5_P2_CQ1-5` | 2 | CQ1_ResolutionLookup | classes={Resolution, Tdoc, WorkItem}; rels={REFERENCES, RELATED_TO} |
| `RAN5_P2_CQ1-6` | 2 | CQ1_ResolutionLookup | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `RAN5_P2_CQ2-1` | 2 | CQ2_TdocResolutionTracing | classes={Resolution, Tdoc}; rels={REFERENCES} |
| `RAN5_P2_CQ2-2` | 2 | CQ2_TdocResolutionTracing | classes={Resolution, Tdoc}; rels={REFERENCES} |
| `RAN5_P2_CQ2-4` | 2 | CQ2_TdocResolutionTracing | classes={Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES} |
| `RAN5_P2_CQ3-1` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN5_P2_CQ3-2` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc, WorkItem}; rels={REFERENCES, RELATED_TO, SUBMITTED_BY} |
| `RAN5_P2_CQ3-3` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Spec, Tdoc}; rels={MODIFIES, REFERENCES, SUBMITTED_BY} |
| `RAN5_P2_CQ3-4` | 2 | CQ3_CompanyContribution | classes={Company, Resolution, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `RAN5_P2_CQ6-1` | 2 | CQ6_TrendComparison | classes={Meeting, Resolution}; rels={MADE_AT} |
| `RAN5_P2_CQ6-2` | 2 | CQ6_TrendComparison | classes={Company, Meeting, Resolution, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `RAN5_P3_CQ1-1` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-2` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN5_P3_CQ1-3` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, PARENT_SECTION} |
| `RAN5_P3_CQ1-4` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-5` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN5_P3_CQ1-6` | 3 | CQ1_TSStructure | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, CONTAINS_FIGURE} |
| `RAN5_P3_CQ1-7` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN5_P3_CQ1-8` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN5_P3_CQ1-9` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-10` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN5_P3_CQ1-11` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-12` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC, HAS_SUB_SECTION} |
| `RAN5_P3_CQ1-13` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-14` | 3 | CQ1_TSStructure | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `RAN5_P3_CQ1-15` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ1-16` | 3 | CQ1_TSStructure | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ2-1` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN5_P3_CQ2-2` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN5_P3_CQ2-3` | 3 | CQ2_TSCrossReference | classes={Section}; rels={REFERENCES_SECTION} |
| `RAN5_P3_CQ2-4` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN5_P3_CQ2-5` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SPEC} |
| `RAN5_P3_CQ2-6` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SPEC} |
| `RAN5_P3_CQ2-7` | 3 | CQ2_TSCrossReference | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `RAN5_P3_CQ3-1` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN5_P3_CQ3-2` | 3 | CQ3_CRLinkage | classes={Section, Spec}; rels={BELONGS_TO_SPEC, IN_RELEASE_OF, MODIFIES} |
| `RAN5_P3_CQ3-3` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN5_P3_CQ3-4` | 3 | CQ3_CRLinkage | classes={Spec}; rels={MODIFIES} |
| `RAN5_P3_CQ3-6` | 3 | CQ3_CRLinkage | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN5_P3_CQ4-1` | 3 | CQ4_ResolutionLinkage | classes={Conclusion, Spec, Tdoc}; rels={MODIFIES, REFERENCES} |
| `RAN5_P3_CQ4-2` | 3 | CQ4_ResolutionLinkage | classes={Conclusion, Spec, Tdoc}; rels={MODIFIES, REFERENCES} |
| `RAN5_P3_CQ4-3` | 3 | CQ4_ResolutionLinkage | classes={Conclusion, Meeting, Spec, Tdoc}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `RAN5_P3_CQ4-4` | 3 | CQ4_ResolutionLinkage | classes={Conclusion, Tdoc}; rels={REFERENCES} |
| `RAN5_P3_CQ5-1` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN5_P3_CQ5-2` | 3 | CQ5_IntegratedAnalysis | classes={Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `RAN5_P3_CQ5-3` | 3 | CQ5_IntegratedAnalysis | classes={Release, Spec}; rels={MODIFIES, TARGET_RELEASE} |
| `RAN5_P3_CQ5-4` | 3 | CQ5_IntegratedAnalysis | classes={Spec}; rels={MODIFIES} |
| `RAN5_P3_CQ5-5` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `RAN5_P3_CQ5-6` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `RAN5_P3_CQ5-7` | 3 | CQ5_IntegratedAnalysis | classes={Section, Spec, TSFigure}; rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION} |
| `RAN5_P3_P3-S8-CQ01` | 3 | CQ_Step8_EntityCount | — |
| `RAN5_P3_P3-S8-CQ02` | 3 | CQ_Step8_DefinedInSection | classes={Section} |
| `RAN5_P3_P3-S8-CQ05` | 3 | CQ_Step8_GranularityDump | — |
| `RAN5_P3_P3-S8-CQ06` | 3 | CQ_Step8_CoreIE_Baseline | classes={RRCParameter} |
| `RAN5_P3_P3-S8-CQ08` | 3 | CQ_Step8_FeatureCatalogParity | classes={Feature} |
| `RAN5_P4_CQ1-1` | 4 | CQ1_ChangeRationale | — |
| `RAN5_P4_CQ1-2` | 4 | CQ1_ChangeRationale | — |
| `RAN5_P4_CQ1-3` | 4 | CQ1_ChangeRationale | — |
| `RAN5_P4_CQ2-1` | 4 | CQ2_CrossSpec | classes={Spec} |
| `RAN5_P4_CQ2-2` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC, MODIFIES} |
| `RAN5_P4_CQ2-3` | 4 | CQ2_CrossSpec | classes={Spec}; rels={AFFECTS_CORE_SPEC} |
| `RAN5_P4_CQ2-4` | 4 | CQ2_CrossSpec | — |
| `RAN5_P4_CQ3-1` | 4 | CQ3_CRPack | classes={CRPack}; rels={HAS_CR} |
| `RAN5_P4_CQ3-2` | 4 | CQ3_CRPack | classes={CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `RAN5_P4_CQ3-3` | 4 | CQ3_CRPack | classes={CRPack}; rels={HAS_CR} |
| `RAN5_P4_CQ4-1` | 4 | CQ4_LinkedAnalysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES_SECTION} |
| `RAN5_P4_CQ4-2` | 4 | CQ4_LinkedAnalysis | classes={Conclusion}; rels={REFERENCES} |
| `RAN5_P4_CQ4-3` | 4 | CQ4_LinkedAnalysis | classes={Section, WorkItem}; rels={MODIFIES_SECTION, RELATED_TO} |
| `RAN5_P4_CQ4-4` | 4 | CQ4_LinkedAnalysis | classes={Company, Spec}; rels={AFFECTS_CORE_SPEC, SUBMITTED_BY} |
| `RAN5_P4_CQ4-5` | 4 | CQ4_LinkedAnalysis | classes={Conclusion, Meeting, Tdoc}; rels={MADE_AT, REFERENCES} |
| `RAN5_P5_CQ1-1` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN5_P5_CQ1-2` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN5_P5_CQ1-3` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN5_P5_CQ1-4` | 5 | *(uncategorized)* | classes={TechnicalReport} |
| `RAN5_P5_CQ2-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN5_P5_CQ2-2` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN5_P5_CQ2-3` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN5_P5_CQ2-4` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN5_P5_CQ2-5` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN5_P5_CQ3-1` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN5_P5_CQ3-2` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN5_P5_CQ3-3` | 5 | *(uncategorized)* | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT} |
| `RAN5_P5_CQ4-1` | 5 | *(uncategorized)* | classes={Release, TechnicalReport}; rels={TARGET_RELEASE} |
| `RAN5_P5_CQ4-2` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `RAN5_P5_CQ4-3` | 5 | *(uncategorized)* | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
