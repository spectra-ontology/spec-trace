# Anonymized index of the 137 SPECTRA Competency Questions

This file enumerates all 137 competency questions used to design and validate SPECTRA across five development phases. The full text of each question and its executable Cypher/SPARQL are retained as internal validation evidence (see `PUBLISHING.md` and the paper's Availability section); for each CQ we publish the **identifier**, **phase**, **target category**, **target persona**, and **schema area exercised** so that third parties can verify (i) the breadth of the elicited CQs across personas and categories, and (ii) which ontology classes / object properties each CQ traverses.

**Total**: 137 CQs across 5 phases (P1=25, P2=34, P3=45, P4=15, P5=18).

A representative subset of CQs (with full question text and executable Cypher/SPARQL) is in `representative_cqs.md`.

| ID | Phase | Category | Persona | Schema area exercised |
|----|------:|----------|---------|------------------------|
| `P1_CQ1-1` | 1 | Tdoc metadata lookup |  | classes={Meeting, WorkItem}; rels={PRESENTED_AT, RELATED_TO} |
| `P1_CQ1-2` | 1 | Tdoc metadata lookup |  | classes={Meeting}; rels={BELONGS_TO, PRESENTED_AT} |
| `P1_CQ1-3` | 1 | Tdoc metadata lookup |  | classes={Company, Meeting}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ1-4` | 1 | Tdoc metadata lookup |  | classes={Release}; rels={PRESENTED_AT, TARGET_RELEASE} |
| `P1_CQ1-5` | 1 | Tdoc metadata lookup |  | classes={Meeting}; rels={PRESENTED_AT} |
| `P1_CQ1-6` | 1 | Tdoc metadata lookup |  | classes={Tdoc} |
| `P1_CQ1-7` | 1 | Tdoc metadata lookup |  | classes={Tdoc} |
| `P1_CQ1-8` | 1 | Tdoc metadata lookup |  | classes={Tdoc}; rels={HAS_CONTACT} |
| `P1_CQ1-9` | 1 | Tdoc metadata lookup |  | classes={Meeting}; rels={BELONGS_TO, PRESENTED_AT} |
| `P1_CQ2-1` | 1 | CQ2_Tdoc관계추적 |  | classes={Tdoc}; rels={IS_REVISION_OF, REVISED_TO} |
| `P1_CQ2-2` | 1 | CQ2_Tdoc관계추적 |  | classes={Tdoc}; rels={CC_TO, ORIGINATED_FROM, SENT_TO} |
| `P1_CQ2-3` | 1 | CQ2_Tdoc관계추적 |  | classes={Tdoc}; rels={REPLY_TO} |
| `P1_CQ2-4` | 1 | CQ2_Tdoc관계추적 |  | classes={Spec}; rels={MODIFIES} |
| `P1_CQ2-5` | 1 | CQ2_Tdoc관계추적 |  | classes={Tdoc} |
| `P1_CQ2-6` | 1 | CQ2_Tdoc관계추적 |  | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `P1_CQ2-7` | 1 | CQ2_Tdoc관계추적 |  | classes={Meeting, Tdoc}; rels={BELONGS_TO, ORIGINATED_FROM, PRESENTED_AT} |
| `P1_CQ3-1` | 1 | CQ3_회사분석 |  | classes={Company, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ3-2` | 1 | CQ3_회사분석 |  | classes={Meeting}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ3-3` | 1 | CQ3_회사분석 |  | classes={WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ3-4` | 1 | CQ3_회사분석 |  | classes={Company}; rels={SUBMITTED_BY} |
| `P1_CQ3-5` | 1 | CQ3_회사분석 |  | classes={Tdoc}; rels={BELONGS_TO, SUBMITTED_BY} |
| `P1_CQ3-6` | 1 | CQ3_회사분석 |  | classes={Company}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ4-1` | 1 | CQ4_회의히스토리 |  | classes={Company, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `P1_CQ4-2` | 1 | CQ4_회의히스토리 |  | classes={Company, Meeting}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ4-3` | 1 | CQ4_회의히스토리 |  | classes={Meeting}; rels={BELONGS_TO, PRESENTED_AT} |
| `P2_CQ1-1` | 2 | Resolution lookup |  | classes={Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `P2_CQ1-2` | 2 | Resolution lookup |  | classes={AgendaItem, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `P2_CQ1-3` | 2 | Resolution lookup |  | classes={Meeting}; rels={MADE_AT} |
| `P2_CQ1-4` | 2 | Resolution lookup |  | classes={Meeting}; rels={MADE_AT} |
| `P2_CQ1-5` | 2 | Resolution lookup |  | rels={MADE_AT} |
| `P2_CQ1-6` | 2 | Resolution lookup |  | rels={MADE_AT} |
| `P2_CQ1-7` | 2 | Resolution lookup |  | rels={MADE_AT} |
| `P2_CQ2-1` | 2 | CQ2_Tdoc-Resolution추적 |  | classes={Agreement}; rels={REFERENCES} |
| `P2_CQ2-2` | 2 | CQ2_Tdoc-Resolution추적 |  | classes={Tdoc}; rels={MADE_AT, REFERENCES} |
| `P2_CQ2-3` | 2 | CQ2_Tdoc-Resolution추적 |  | classes={Meeting}; rels={MADE_AT} |
| `P2_CQ2-4` | 2 | CQ2_Tdoc-Resolution추적 |  | rels={RESOLUTION_BELONGS_TO} |
| `P2_CQ2-5` | 2 | CQ2_Tdoc-Resolution추적 |  | rels={MADE_AT} |
| `P2_CQ3-1` | 2 | CQ3_회사기여도 |  | classes={Company}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-2` | 2 | CQ3_회사기여도 |  | classes={Company}; rels={REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-3` | 2 | CQ3_회사기여도 |  | rels={REFERENCES, RESOLUTION_BELONGS_TO, SUBMITTED_BY} |
| `P2_CQ3-4` | 2 | CQ3_회사기여도 |  | classes={Company}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-5` | 2 | CQ3_회사기여도 |  | rels={REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-6` | 2 | CQ3_회사기여도 |  | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `P2_CQ4-1` | 2 | CQ4_기술주도권분석 |  | rels={BELONGS_TO, MODERATED_BY} |
| `P2_CQ4-2` | 2 | CQ4_기술주도권분석 |  | classes={Company}; rels={BELONGS_TO, MODERATED_BY} |
| `P2_CQ4-3` | 2 | CQ4_기술주도권분석 |  | rels={MODERATED_BY} |
| `P2_CQ5-1` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-2` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-3` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-4` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-5` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-6` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-7` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-8` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-9` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-10` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-11` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-12` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P2_CQ5-13` | 2 | CQ5_기술트렌드 |  | rels={MADE_AT} |
| `P3_CQ001` | 3 | TS structure exploration | HW/SW engineer | classes={Spec}; rels={HAS_SECTION} |
| `P3_CQ002` | 3 | TS structure exploration | HW/SW engineer | classes={Section}; rels={HAS_SUB_SECTION} |
| `P3_CQ003` | 3 | TS structure exploration | HW/SW engineer | classes={Section}; rels={PARENT_SECTION} |
| `P3_CQ004` | 3 | TS structure exploration | standardization engineer | classes={Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ005` | 3 | TS structure exploration | HW/SW engineer | classes={Spec}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ006` | 3 | TS structure exploration | HW/SW engineer | classes={Spec}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `P3_CQ007` | 3 | TS structure exploration | HW/SW engineer | rels={BELONGS_TO_SPEC} |
| `P3_CQ008` | 3 | TS structure exploration | standardization engineer | rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION, TABLE_IN_SECTION} |
| `P3_CQ009` | 3 | TS cross-reference analysis | HW/SW engineer | classes={Section}; rels={REFERENCES_SECTION} |
| `P3_CQ010` | 3 | TS cross-reference analysis | HW/SW engineer | classes={Section}; rels={REFERENCES_SECTION} |
| `P3_CQ011` | 3 | TS cross-reference analysis | standardization engineer | rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ012` | 3 | TS cross-reference analysis | HW/SW engineer | rels={REFERENCES_SECTION} |
| `P3_CQ013` | 3 | TS cross-reference analysis | standardization engineer | rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ014` | 3 | TS cross-reference analysis | standardization engineer | rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ015` | 3 | TS cross-reference analysis | standardization engineer | classes={Section}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ016` | 3 | CR_TS_변경추적 | standardization engineer | classes={Spec}; rels={MODIFIES} |
| `P3_CQ017` | 3 | CR_TS_변경추적 | standardization engineer | classes={Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ018` | 3 | CR_TS_변경추적 | HW/SW engineer | classes={Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ019` | 3 | CR_TS_변경추적 | 전략기획 | rels={MODIFIES} |
| `P3_CQ020` | 3 | CR_TS_변경추적 | HW/SW engineer | classes={Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ021` | 3 | CR_TS_변경추적 | standardization engineer | classes={Spec}; rels={MODIFIES} |
| `P3_CQ022` | 3 | CR_TS_변경추적 | 전략기획 | classes={Spec}; rels={MODIFIES, PRESENTED_AT} |
| `P3_CQ023` | 3 | Resolution_TS_의사결정 | standardization engineer | classes={Spec}; rels={MODIFIES, REFERENCES} |
| `P3_CQ024` | 3 | Resolution_TS_의사결정 | standardization engineer | classes={Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ025` | 3 | Resolution_TS_의사결정 | standardization engineer | rels={MODIFIES, REFERENCES} |
| `P3_CQ026` | 3 | Resolution_TS_의사결정 | IP특허 | classes={Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ027` | 3 | Resolution_TS_의사결정 | standardization engineer | rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ028` | 3 | Resolution_TS_의사결정 | standardization engineer | classes={Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ029` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC} |
| `P3_CQ030` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `P3_CQ031` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC} |
| `P3_CQ032` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ033` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ034` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ035` | 3 | 기술_키워드검색 | HW/SW engineer | rels={BELONGS_TO_SPEC} |
| `P3_CQ036` | 3 | 통합분석 | 전략기획 | classes={Spec}; rels={BELONGS_TO_SPEC, MODIFIES} |
| `P3_CQ037` | 3 | 통합분석 | 전략기획 | rels={MODIFIES, SUBMITTED_BY} |
| `P3_CQ038` | 3 | 통합분석 | standardization engineer | rels={BELONGS_TO_SPEC, MODIFIES, REFERENCES_SECTION} |
| `P3_CQ039` | 3 | 통합분석 | IP특허 | classes={Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `P3_CQ040` | 3 | 통합분석 | 전략기획 | rels={MODIFIES, REFERENCES} |
| `P3_CQ041` | 3 | 통합분석 | standardization engineer | rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ042` | 3 | 통합분석 | HW/SW engineer | rels={BELONGS_TO_SPEC, CONTAINS_TABLE, HAS_SUB_SECTION} |
| `P3_CQ043` | 3 | 통합분석 | standardization engineer | — |
| `P3_CQ044` | 3 | CR_TS_변경추적 | 전략기획 | classes={WorkItem}; rels={MODIFIES, RELATED_TO} |
| `P3_CQ045` | 3 | Resolution_TS_의사결정 | standardization engineer | classes={WorkItem}; rels={MODIFIES, REFERENCES, RELATED_TO} |
| `P4_CQ1-1` | 4 | CR change rationale |  | classes={CR} |
| `P4_CQ1-2` | 4 | CR change rationale |  | classes={CR} |
| `P4_CQ1-3` | 4 | CR change rationale |  | classes={WorkItem}; rels={RELATED_TO} |
| `P4_CQ2-1` | 4 | CQ2_CrossSpec영향 |  | classes={CR} |
| `P4_CQ2-2` | 4 | CQ2_CrossSpec영향 |  | classes={Spec}; rels={MODIFIES} |
| `P4_CQ2-3` | 4 | CQ2_CrossSpec영향 |  | classes={Spec} |
| `P4_CQ2-4` | 4 | CQ2_CrossSpec영향 |  | — |
| `P4_CQ3-1` | 4 | CQ3_CRPack분석 |  | classes={CRPack}; rels={HAS_CR} |
| `P4_CQ3-2` | 4 | CQ3_CRPack분석 |  | classes={WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `P4_CQ3-3` | 4 | CQ3_CRPack분석 |  | rels={HAS_CR} |
| `P4_CQ4-1` | 4 | CQ4_연계분석 |  | classes={Spec}; rels={MODIFIES} |
| `P4_CQ4-2` | 4 | CQ4_연계분석 |  | classes={Resolution}; rels={REFERENCES} |
| `P4_CQ4-3` | 4 | CQ4_연계분석 |  | classes={WorkItem}; rels={MODIFIES, RELATED_TO} |
| `P4_CQ4-4` | 4 | CQ4_연계분석 |  | classes={Company}; rels={SUBMITTED_BY} |
| `P4_CQ4-5` | 4 | CQ4_연계분석 |  | classes={Meeting}; rels={MADE_AT, REFERENCES} |
| `P5_CQ1-1` | 5 | TR study status |  | classes={TechnicalReport} |
| `P5_CQ1-2` | 5 | TR study status |  | classes={TechnicalReport} |
| `P5_CQ1-3` | 5 | TR study status |  | classes={TechnicalReport} |
| `P5_CQ1-4` | 5 | TR study status |  | classes={TechnicalReport} |
| `P5_CQ2-1` | 5 | CQ2_TS반영영향추적 |  | classes={TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ2-2` | 5 | CQ2_TS반영영향추적 |  | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ2-3` | 5 | CQ2_TS반영영향추적 |  | classes={Spec}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ2-4` | 5 | CQ2_TS반영영향추적 |  | classes={Section}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ2-5` | 5 | CQ2_TS반영영향추적 |  | classes={TRImpact}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ3-1` | 5 | CQ3_기술별영향범위 |  | classes={TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ3-2` | 5 | CQ3_기술별영향범위 |  | classes={TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ3-3` | 5 | CQ3_기술별영향범위 |  | classes={TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ4-1` | 5 | CQ4_릴리스별연구영향 |  | classes={Release}; rels={HAS_TR_IMPACT, IMPACTS_SPEC, TARGET_RELEASE} |
| `P5_CQ4-2` | 5 | CQ4_릴리스별연구영향 |  | classes={TechnicalReport} |
| `P5_CQ4-3` | 5 | CQ4_릴리스별연구영향 |  | classes={TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ5-1` | 5 | CQ5_TR간참조관계 |  | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `P5_CQ5-2` | 5 | CQ5_TR간참조관계 |  | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `P5_CQ5-3` | 5 | CQ5_TR간참조관계 |  | rels={REFERENCES_TR} |