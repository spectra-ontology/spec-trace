# Anonymized index of the 137 SPECTRA Competency Questions

This file enumerates all 137 competency questions used to design and validate SPECTRA across five development phases. The full text of each question and its executable Cypher/SPARQL are retained as internal validation evidence (see `PUBLISHING.md` and the paper's Availability section). For each CQ we publish the **identifier**, **phase**, **target category** (translated to English), and **schema area exercised** so third parties can verify (i) the breadth of the elicited CQ set across categories and (ii) which ontology classes / object properties each CQ traverses.

**Total**: 137 CQs across 5 phases (P1=25, P2=34, P3=45, P4=15, P5=18).

A representative subset of CQs (with full question text and executable Cypher/SPARQL) is in `representative_cqs.md`. A category-by-phase distribution is rendered as `../diagrams/cq_distribution.png`.

| ID | Phase | Category | Schema area exercised |
|----|------:|----------|------------------------|
| `P1_CQ1-1` | 1 | Tdoc lookup | classes={Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO} |
| `P1_CQ1-2` | 1 | Tdoc lookup | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `P1_CQ1-3` | 1 | Tdoc lookup | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ1-4` | 1 | Tdoc lookup | classes={Meeting, Release, Tdoc}; rels={PRESENTED_AT, TARGET_RELEASE} |
| `P1_CQ1-5` | 1 | Tdoc lookup | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `P1_CQ1-6` | 1 | Tdoc lookup | classes={Tdoc} |
| `P1_CQ1-7` | 1 | Tdoc lookup | classes={Tdoc} |
| `P1_CQ1-8` | 1 | Tdoc lookup | classes={Contact, Tdoc}; rels={HAS_CONTACT} |
| `P1_CQ1-9` | 1 | Tdoc lookup | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `P1_CQ2-1` | 1 | Tdoc relation tracing | classes={Tdoc}; rels={IS_REVISION_OF, REVISED_TO} |
| `P1_CQ2-2` | 1 | Tdoc relation tracing | classes={Tdoc, WorkingGroup}; rels={CC_TO, ORIGINATED_FROM, SENT_TO} |
| `P1_CQ2-3` | 1 | Tdoc relation tracing | classes={Tdoc}; rels={REPLY_TO} |
| `P1_CQ2-4` | 1 | Tdoc relation tracing | classes={Spec, Tdoc}; rels={MODIFIES} |
| `P1_CQ2-5` | 1 | Tdoc relation tracing | classes={Tdoc} |
| `P1_CQ2-6` | 1 | Tdoc relation tracing | classes={Meeting, Tdoc}; rels={PRESENTED_AT} |
| `P1_CQ2-7` | 1 | Tdoc relation tracing | classes={AgendaItem, Meeting, Tdoc, WorkingGroup}; rels={BELONGS_TO, ORIGINATED_FROM, PRESENTED_AT} |
| `P1_CQ3-1` | 1 | Company contribution analysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ3-2` | 1 | Company contribution analysis | classes={AgendaItem, Company, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ3-3` | 1 | Company contribution analysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ3-4` | 1 | Company contribution analysis | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `P1_CQ3-5` | 1 | Company contribution analysis | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, SUBMITTED_BY} |
| `P1_CQ3-6` | 1 | Company contribution analysis | classes={Company, Tdoc, WorkItem}; rels={RELATED_TO, SUBMITTED_BY} |
| `P1_CQ4-1` | 1 | Meeting history analysis | classes={Company, Meeting, Tdoc, WorkItem}; rels={PRESENTED_AT, RELATED_TO, SUBMITTED_BY} |
| `P1_CQ4-2` | 1 | Meeting history analysis | classes={Company, Meeting, Tdoc}; rels={PRESENTED_AT, SUBMITTED_BY} |
| `P1_CQ4-3` | 1 | Meeting history analysis | classes={AgendaItem, Meeting, Tdoc}; rels={BELONGS_TO, PRESENTED_AT} |
| `P2_CQ1-1` | 2 | Resolution lookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `P2_CQ1-2` | 2 | Resolution lookup | classes={AgendaItem, Agreement, Meeting}; rels={MADE_AT, RESOLUTION_BELONGS_TO} |
| `P2_CQ1-3` | 2 | Resolution lookup | classes={Conclusion, Meeting}; rels={MADE_AT} |
| `P2_CQ1-4` | 2 | Resolution lookup | classes={Meeting, WorkingAssumption}; rels={MADE_AT} |
| `P2_CQ1-5` | 2 | Resolution lookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ1-6` | 2 | Resolution lookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ1-7` | 2 | Resolution lookup | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ2-1` | 2 | Tdoc-to-Resolution tracing | classes={Agreement, Tdoc}; rels={REFERENCES} |
| `P2_CQ2-2` | 2 | Tdoc-to-Resolution tracing | classes={Agreement, Meeting, Tdoc}; rels={MADE_AT, REFERENCES} |
| `P2_CQ2-3` | 2 | Tdoc-to-Resolution tracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ2-4` | 2 | Tdoc-to-Resolution tracing | classes={AgendaItem, Resolution}; rels={RESOLUTION_BELONGS_TO} |
| `P2_CQ2-5` | 2 | Tdoc-to-Resolution tracing | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ3-1` | 2 | Company-level contribution scoring | classes={Agreement, Company, Meeting, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-2` | 2 | Company-level contribution scoring | classes={Agreement, Company, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-3` | 2 | Company-level contribution scoring | classes={AgendaItem, Agreement, Company, Tdoc}; rels={REFERENCES, RESOLUTION_BELONGS_TO, SUBMITTED_BY} |
| `P2_CQ3-4` | 2 | Company-level contribution scoring | classes={Agreement, Company, Meeting, Tdoc}; rels={MADE_AT, REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-5` | 2 | Company-level contribution scoring | classes={Agreement, Company, Tdoc}; rels={REFERENCES, SUBMITTED_BY} |
| `P2_CQ3-6` | 2 | Company-level contribution scoring | classes={Company, Tdoc}; rels={SUBMITTED_BY} |
| `P2_CQ4-1` | 2 | Technical leadership analysis | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, MODERATED_BY} |
| `P2_CQ4-2` | 2 | Technical leadership analysis | classes={AgendaItem, Company, Tdoc}; rels={BELONGS_TO, MODERATED_BY} |
| `P2_CQ4-3` | 2 | Technical leadership analysis | classes={Company, Tdoc}; rels={MODERATED_BY} |
| `P2_CQ5-1` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-2` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-3` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-4` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-5` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-6` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-7` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-8` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-9` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-10` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-11` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-12` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P2_CQ5-13` | 2 | Tech trends | classes={Agreement, Meeting}; rels={MADE_AT} |
| `P3_CQ001` | 3 | TS structure exploration | classes={Section, Spec}; rels={HAS_SECTION} |
| `P3_CQ002` | 3 | TS structure exploration | classes={Section}; rels={HAS_SUB_SECTION} |
| `P3_CQ003` | 3 | TS structure exploration | classes={Section}; rels={PARENT_SECTION} |
| `P3_CQ004` | 3 | TS structure exploration | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ005` | 3 | TS structure exploration | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ006` | 3 | TS structure exploration | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `P3_CQ007` | 3 | TS structure exploration | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ008` | 3 | TS structure exploration | classes={Section, Spec, TSFigure, TSTable}; rels={BELONGS_TO_SPEC, FIGURE_IN_SECTION, TABLE_IN_SECTION} |
| `P3_CQ009` | 3 | TS cross-reference analysis | classes={Section}; rels={REFERENCES_SECTION} |
| `P3_CQ010` | 3 | TS cross-reference analysis | classes={Section}; rels={REFERENCES_SECTION} |
| `P3_CQ011` | 3 | TS cross-reference analysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ012` | 3 | TS cross-reference analysis | classes={Section}; rels={REFERENCES_SECTION} |
| `P3_CQ013` | 3 | TS cross-reference analysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ014` | 3 | TS cross-reference analysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ015` | 3 | TS cross-reference analysis | classes={Section, Spec}; rels={BELONGS_TO_SPEC, REFERENCES_SECTION} |
| `P3_CQ016` | 3 | CR-TS change tracking | classes={CR, Spec}; rels={MODIFIES} |
| `P3_CQ017` | 3 | CR-TS change tracking | classes={CR, Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ018` | 3 | CR-TS change tracking | classes={CR, Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ019` | 3 | CR-TS change tracking | classes={CR, Spec}; rels={MODIFIES} |
| `P3_CQ020` | 3 | CR-TS change tracking | classes={CR, Company, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT, SUBMITTED_BY} |
| `P3_CQ021` | 3 | CR-TS change tracking | classes={CR, Spec}; rels={MODIFIES} |
| `P3_CQ022` | 3 | CR-TS change tracking | classes={CR, Meeting, Spec}; rels={MODIFIES, PRESENTED_AT} |
| `P3_CQ023` | 3 | Resolution-to-TS decision tracking | classes={Agreement, CR, Spec}; rels={MODIFIES, REFERENCES} |
| `P3_CQ024` | 3 | Resolution-to-TS decision tracking | classes={Agreement, CR, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ025` | 3 | Resolution-to-TS decision tracking | classes={Agreement, CR, Spec}; rels={MODIFIES, REFERENCES} |
| `P3_CQ026` | 3 | Resolution-to-TS decision tracking | classes={Agreement, CR, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ027` | 3 | Resolution-to-TS decision tracking | classes={Agreement, CR, Meeting, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ028` | 3 | Resolution-to-TS decision tracking | classes={CR, Meeting, Resolution, Spec}; rels={MADE_AT, MODIFIES, REFERENCES} |
| `P3_CQ029` | 3 | Technical keyword search | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ030` | 3 | Technical keyword search | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, TABLE_IN_SECTION} |
| `P3_CQ031` | 3 | Technical keyword search | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ032` | 3 | Technical keyword search | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ033` | 3 | Technical keyword search | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ034` | 3 | Technical keyword search | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ035` | 3 | Technical keyword search | classes={Section, Spec}; rels={BELONGS_TO_SPEC} |
| `P3_CQ036` | 3 | Integrated cross-class analysis | classes={CR, Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES} |
| `P3_CQ037` | 3 | Integrated cross-class analysis | classes={CR, Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `P3_CQ038` | 3 | Integrated cross-class analysis | classes={CR, Section, Spec}; rels={BELONGS_TO_SPEC, MODIFIES, REFERENCES_SECTION} |
| `P3_CQ039` | 3 | Integrated cross-class analysis | classes={CR, Company, Spec}; rels={MODIFIES, SUBMITTED_BY} |
| `P3_CQ040` | 3 | Integrated cross-class analysis | classes={Agreement, CR, Spec}; rels={MODIFIES, REFERENCES} |
| `P3_CQ041` | 3 | Integrated cross-class analysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE} |
| `P3_CQ042` | 3 | Integrated cross-class analysis | classes={Section, Spec, TSTable}; rels={BELONGS_TO_SPEC, CONTAINS_TABLE, HAS_SUB_SECTION} |
| `P3_CQ043` | 3 | Integrated cross-class analysis | classes={CR, Company, Meeting, Resolution, Section, Spec, TSFigure, TSTable} |
| `P3_CQ044` | 3 | CR-TS change tracking | classes={CR, Spec, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `P3_CQ045` | 3 | Resolution-to-TS decision tracking | classes={CR, Resolution, Spec, WorkItem}; rels={MODIFIES, REFERENCES, RELATED_TO} |
| `P4_CQ1-1` | 4 | CR rationale lookup | classes={CR} |
| `P4_CQ1-2` | 4 | CR rationale lookup | classes={CR} |
| `P4_CQ1-3` | 4 | CR rationale lookup | classes={CR, WorkItem}; rels={RELATED_TO} |
| `P4_CQ2-1` | 4 | Cross-spec impact analysis | classes={CR, Spec} |
| `P4_CQ2-2` | 4 | Cross-spec impact analysis | classes={CR, Spec}; rels={MODIFIES} |
| `P4_CQ2-3` | 4 | Cross-spec impact analysis | classes={CR, Spec} |
| `P4_CQ2-4` | 4 | Cross-spec impact analysis | classes={CR, Spec} |
| `P4_CQ3-1` | 4 | CRPack-level analysis | classes={CR, CRPack}; rels={HAS_CR} |
| `P4_CQ3-2` | 4 | CRPack-level analysis | classes={CR, CRPack, WorkItem}; rels={BELONGS_TO_CR_PACK, RELATED_TO} |
| `P4_CQ3-3` | 4 | CRPack-level analysis | classes={CR, CRPack}; rels={HAS_CR} |
| `P4_CQ4-1` | 4 | Cross-link analysis | classes={CR, Spec}; rels={MODIFIES} |
| `P4_CQ4-2` | 4 | Cross-link analysis | classes={CR, Resolution}; rels={REFERENCES} |
| `P4_CQ4-3` | 4 | Cross-link analysis | classes={CR, Spec, WorkItem}; rels={MODIFIES, RELATED_TO} |
| `P4_CQ4-4` | 4 | Cross-link analysis | classes={CR, Company, Spec}; rels={SUBMITTED_BY} |
| `P4_CQ4-5` | 4 | Cross-link analysis | classes={CR, Meeting, Resolution}; rels={MADE_AT, REFERENCES} |
| `P5_CQ1-1` | 5 | TR study status analysis | classes={TechnicalReport} |
| `P5_CQ1-2` | 5 | TR study status analysis | classes={TechnicalReport} |
| `P5_CQ1-3` | 5 | TR study status analysis | classes={TechnicalReport} |
| `P5_CQ1-4` | 5 | TR study status analysis | classes={TechnicalReport} |
| `P5_CQ2-1` | 5 | TS-impact tracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ2-2` | 5 | TS-impact tracing | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ2-3` | 5 | TS-impact tracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ2-4` | 5 | TS-impact tracing | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ2-5` | 5 | TS-impact tracing | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ3-1` | 5 | Per-feature impact scope | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ3-2` | 5 | Per-feature impact scope | classes={Section, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SECTION} |
| `P5_CQ3-3` | 5 | Per-feature impact scope | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ4-1` | 5 | Per-Release research impact | classes={Release, Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC, TARGET_RELEASE} |
| `P5_CQ4-2` | 5 | Per-Release research impact | classes={TechnicalReport} |
| `P5_CQ4-3` | 5 | Per-Release research impact | classes={Spec, TRImpact, TechnicalReport}; rels={HAS_TR_IMPACT, IMPACTS_SPEC} |
| `P5_CQ5-1` | 5 | Inter-TR reference analysis | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `P5_CQ5-2` | 5 | Inter-TR reference analysis | classes={TechnicalReport}; rels={REFERENCES_TR} |
| `P5_CQ5-3` | 5 | Inter-TR reference analysis | classes={TechnicalReport}; rels={REFERENCES_TR} |