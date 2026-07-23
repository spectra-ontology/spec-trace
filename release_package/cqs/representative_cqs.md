# Representative competency questions (RAN1 subset)

This file presents 14 of the 624 competency questions released in SpectraCQ v2.0, chosen to cover all five phases of the benchmark with full question text and executable reference Cypher. Each query below is quoted verbatim from its released file under `spectra_cq_v2.0/cypher/`; the copies under `../queries/cypher/` are byte-identical mirrors kept for standalone browsing. The complete per-CQ index (all five working groups) is in `cq_index.md`; question text, Cypher, and gold answer sets for every released CQ are under `spectra_cq_v2.0/`.

Gold row counts below are carried from `spectra_cq_v2.0/questions.json`, where each gold answer set was produced by executing the reference Cypher against the corresponding working-group knowledge graph (no human- or LLM-authored answers).

## Phase 1 — TDoc metadata

### `RAN1_P1_CQ1-1`

**Question**: List the TDocs at meeting RAN1#120 tied to Work Item NR_eMIMO-Core (MIMO meeting preparation).

**Category**: CQ1_Tdoc · **Gold**: 2 rows (primary column `t.tdocNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P1_CQ1-1.cypher` (mirror `../queries/cypher/P1_CQ1-1.cypher`)

```cypher
// SpectraCQ RAN1_P1_CQ1-1 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs at meeting RAN1#120 tied to Work Item NR_eMIMO-Core (MIMO meeting preparation).
// Gold: 2 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

### `RAN1_P1_CQ1-2`

**Question**: List the TDocs under Agenda Item 9.2 (AI/ML for NR) at meeting RAN1#121 (AI/ML session preparation).

**Category**: CQ1_Tdoc · **Gold**: 10 rows (primary column `t.tdocNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P1_CQ1-2.cypher` (mirror `../queries/cypher/P1_CQ1-2.cypher`)

```cypher
// SpectraCQ RAN1_P1_CQ1-2 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs under Agenda Item 9.2 (AI/ML for NR) at meeting RAN1#121 (AI/ML session preparation).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

### `RAN1_P1_CQ1-3`

**Question**: List the TDocs submitted by Huawei at meeting RAN1#120 (tracking a competitor's contributions).

**Category**: CQ1_Tdoc · **Gold**: 10 rows (primary column `t.tdocNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P1_CQ1-3.cypher` (mirror `../queries/cypher/P1_CQ1-3.cypher`)

```cypher
// SpectraCQ RAN1_P1_CQ1-3 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs submitted by Huawei at meeting RAN1#120 (tracking a competitor's contributions).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

## Phase 2 — Meeting resolutions

### `RAN1_P2_CQ1-1`

**Question**: List the agreements under Agenda Item 7.1 (NR MIMO) at meeting RAN1#115 (MIMO meeting outcomes).

**Category**: CQ1_Resolution · **Gold**: 11 rows (primary column `a.resolutionId`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P2_CQ1-1.cypher` (mirror `../queries/cypher/P2_CQ1-1.cypher`)

```cypher
// SpectraCQ RAN1_P2_CQ1-1 (RAN1, phase 2) -- CQ1_Resolution
// Question: List the agreements under Agenda Item 7.1 (NR MIMO) at meeting RAN1#115 (MIMO meeting outcomes).
// Gold: 11 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

### `RAN1_P2_CQ1-2`

**Question**: What was agreed on UL Tx switching (Agenda 5.1) at meeting RAN1#100? (UL switching decisions)

**Category**: CQ1_Resolution · **Gold**: 6 rows (primary column `a.resolutionId`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P2_CQ1-2.cypher` (mirror `../queries/cypher/P2_CQ1-2.cypher`)

```cypher
// SpectraCQ RAN1_P2_CQ1-2 (RAN1, phase 2) -- CQ1_Resolution
// Question: What was agreed on UL Tx switching (Agenda 5.1) at meeting RAN1#100? (UL switching decisions)
// Gold: 6 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
```

### `RAN1_P2_CQ1-3`

**Question**: List the conclusions reached at the latest meeting, RAN1#121 (status of open issues).

**Category**: CQ1_Resolution · **Gold**: 15 rows (primary column `c.resolutionId`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P2_CQ1-3.cypher` (mirror `../queries/cypher/P2_CQ1-3.cypher`)

```cypher
// SpectraCQ RAN1_P2_CQ1-3 (RAN1, phase 2) -- CQ1_Resolution
// Question: List the conclusions reached at the latest meeting, RAN1#121 (status of open issues).
// Gold: 15 rows, primary column "c.resolutionId"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence, c.resolutionId LIMIT 15
```

## Phase 3 — TS structure

### `RAN1_P3_CQ001`

**Question**: Return the top-level table of contents of TS 38.214 (locating DL-scheduling content).

**Category**: TS · **Gold**: 46 rows (primary column `sec.sectionNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P3_CQ001.cypher` (mirror `../queries/cypher/P3_CQ001.cypher`)

```cypher
// SpectraCQ RAN1_P3_CQ001 (RAN1, phase 3) -- TS
// Question: Return the top-level table of contents of TS 38.214 (locating DL-scheduling content).
// Gold: 46 rows, primary column "sec.sectionNumber"

MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
```

### `RAN1_P3_CQ002`

**Question**: Show the sub-structure under TS 38.214 Section 5.1 (implementing PDSCH procedures).

**Category**: TS · **Gold**: 7 rows (primary column `sub.sectionNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P3_CQ002.cypher` (mirror `../queries/cypher/P3_CQ002.cypher`)

```cypher
// SpectraCQ RAN1_P3_CQ002 (RAN1, phase 3) -- TS
// Question: Show the sub-structure under TS 38.214 Section 5.1 (implementing PDSCH procedures).
// Gold: 7 rows, primary column "sub.sectionNumber"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(root:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH root, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (root)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
```

### `RAN1_P3_CQ003`

**Question**: Show the breadcrumb path to TS 38.214 Section 5.1.3.2 (locating a section in the hierarchy).

**Category**: TS · **Gold**: 4 rows (primary column `n.sectionNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P3_CQ003.cypher` (mirror `../queries/cypher/P3_CQ003.cypher`)

```cypher
// SpectraCQ RAN1_P3_CQ003 (RAN1, phase 3) -- TS
// Question: Show the breadcrumb path to TS 38.214 Section 5.1.3.2 (locating a section in the hierarchy).
// Gold: 4 rows, primary column "n.sectionNumber"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(target:Section {sectionNumber:'5.1.3.2'}) WHERE rk.specRelease IS NOT NULL WITH target, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path = (target)-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
```

### `RAN1_P3_CQ004`

**Question**: Return the section count per level in TS 38.213 (gauging structural depth and complexity).

**Category**: TS · **Gold**: 5 rows (primary column `sec.level`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P3_CQ004.cypher` (mirror `../queries/cypher/P3_CQ004.cypher`)

```cypher
// SpectraCQ RAN1_P3_CQ004 (RAN1, phase 3) -- TS
// Question: Return the section count per level in TS 38.213 (gauging structural depth and complexity).
// Gold: 5 rows, primary column "sec.level"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
```

## Phase 4 — CR documents

### `RAN1_P4_CQ1-1`

**Question**: What is the specific reason-for-change of CR R1-2504971, which touches five specs to introduce LP-WUS/WUR? (rationale review)

**Category**: CQ1_CR · **Gold**: 1 rows (primary column `cr.tdocNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P4_CQ1-1.cypher` (mirror `../queries/cypher/P4_CQ1-1.cypher`)

```cypher
// SpectraCQ RAN1_P4_CQ1-1 (RAN1, phase 4) -- CQ1_CR
// Question: What is the specific reason-for-change of CR R1-2504971, which touches five specs to introduce LP-WUS/WUR? (rationale review)
// Gold: 1 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber: 'R1-2504971'}) WHERE cr.reasonForChange IS NOT NULL RETURN cr.tdocNumber, cr.reasonForChange
```

### `RAN1_P4_CQ1-2`

**Question**: What is the summary-of-change of CR R1-2506685, introducing the Rel-19 UL Tx switching 3Tx UE scenario?

**Category**: CQ1_CR · **Gold**: 1 rows (primary column `cr.tdocNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P4_CQ1-2.cypher` (mirror `../queries/cypher/P4_CQ1-2.cypher`)

```cypher
// SpectraCQ RAN1_P4_CQ1-2 (RAN1, phase 4) -- CQ1_CR
// Question: What is the summary-of-change of CR R1-2506685, introducing the Rel-19 UL Tx switching 3Tx UE scenario?
// Gold: 1 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber: 'R1-2506685'}) WHERE cr.summaryOfChange IS NOT NULL RETURN cr.tdocNumber, cr.summaryOfChange
```

## Phase 5 — Technical Reports

### `RAN1_P5_CQ1-1`

**Question**: Return the scope and conclusions of TR 38.769 on Ambient IoT (input for new IoT product planning).

**Category**: CQ1_TR · **Gold**: 1 rows (primary column `tr.trNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P5_CQ1-1.cypher` (mirror `../queries/cypher/P5_CQ1-1.cypher`)

```cypher
// SpectraCQ RAN1_P5_CQ1-1 (RAN1, phase 5) -- CQ1_TR
// Question: Return the scope and conclusions of TR 38.769 on Ambient IoT (input for new IoT product planning).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.769'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions
```

### `RAN1_P5_CQ1-2`

**Question**: Is the NR-U study TR 38.889 completed and ready to fold into the standard? Return its status and conclusions.

**Category**: CQ1_TR · **Gold**: 1 rows (primary column `tr.trNumber`) · **Files**: `spectra_cq_v2.0/cypher/RAN1_P5_CQ1-2.cypher` (mirror `../queries/cypher/P5_CQ1-2.cypher`)

```cypher
// SpectraCQ RAN1_P5_CQ1-2 (RAN1, phase 5) -- CQ1_TR
// Question: Is the NR-U study TR 38.889 completed and ready to fold into the standard? Return its status and conclusions.
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions
```

## Phase-agnostic example — multi-hop traceability

Beyond the per-phase CQs, the release ships one phase-agnostic example that chains two traceability layers (change requests modifying a section, and technical reports shaping the parent specification) in both query languages: `../queries/cypher/MULTI_HOP_traceability.cypher` and `../queries/sparql/MULTI_HOP_traceability.rq`. Both return the same 609 rows (87 CRs × 7 TRs) on the released RAN1 KG — the SPARQL form against `kg/per_wg/RAN1-body.ttl` directly, the Cypher form against the property graph restored by `pipeline/load_released_kg.py` (evidence: `../validation/example_queries_results.json`).

```cypher
// Multi-hop traceability: for TS 38.214 §5.1.5, which change requests
// modified it (and why), and which technical reports shaped the parent
// specification?
// Cypher twin of ../sparql/MULTI_HOP_traceability.rq — same two-layer chain,
// expressed against the property graph restored by pipeline/load_released_kg.py:
//   CR layer:  (Spec 38.214) <-[:BELONGS_TO_SPEC]- (Section 5.1.5)
//              <-[:MODIFIES_SECTION]- (CR) (.reasonForChange)
//   TR layer:  (Spec 38.214) <-[:IMPACTS_SPEC]- (TRImpact)
//              -[:IMPACT_OF_TR]-> (TechnicalReport)
//
// Modeling note: the released KG carries release-scoped Spec editions
// (e.g. 38.214 Rel-15..Rel-19), which own the Section nodes, plus a
// release-unscoped spec-level node, which receives TRImpact edges. The two
// layers are therefore joined on the natural key specNumber (the same
// property-keyed idiom the benchmark Cypher uses) rather than on one shared
// Spec node — hence the two independent MATCH anchors below.
//
// Coverage note: in the released RAN1 KG, meeting placement is carried by
// Tdoc and Resolution nodes rather than by CR nodes (see CQ1-1 and CQ2-1
// for those hops), so this example chains the CR and TR layers that are
// materialized end-to-end. All constants verified against the released
// RAN1-body.ttl.

MATCH (secSpec:Spec {specNumber: '38.214'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber: '5.1.5'})<-[:MODIFIES_SECTION]-(cr:CR)
MATCH (trSpec:Spec {specNumber: '38.214'})<-[:IMPACTS_SPEC]-(ti:TRImpact)-[:IMPACT_OF_TR]->(tr:TechnicalReport)
RETURN DISTINCT cr.tdocNumber AS crNumber, cr.reasonForChange AS reasonForChange, tr.trNumber AS trNumber
ORDER BY crNumber, trNumber
```
