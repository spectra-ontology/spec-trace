# Representative Competency Questions

This file lists a curated subset of the 137 competency questions used to design and validate SPECTRA. Each entry shows the question, the schema area exercised, and the Cypher query used to answer it against a SPECTRA-conformant knowledge graph. SPARQL translations for a subset of these CQs are in `../queries/sparql/`.

The **complete 137-CQ suite** and the full executable query set are retained as internal validation material; see the paper's Availability section.

Each CQ identifier below is namespaced by the development phase in which the CQ was first introduced (P1 = Phase 1 TDoc metadata, P2 = Phase 2 Resolutions, P3 = Phase 3 TS structure, P4 = Phase 4 CR documents, P5 = Phase 5 TRs).

---

## P1_CQ1-1

- **Phase**: 1
- **Category**: Tdoc metadata
- **Question**: List the Tdocs presented at meeting RAN1#120 that are linked to Work Item NR_eMIMO-Core.
- **Cypher** (see `../queries/cypher/P1_CQ1-1.cypher`):

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

## P1_CQ1-2

- **Phase**: 1
- **Category**: Tdoc metadata
- **Question**: List the Tdocs presented at meeting RAN1#121 under agenda items beginning with 9.2.
- **Cypher** (see `../queries/cypher/P1_CQ1-2.cypher`):

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

## P1_CQ1-3

- **Phase**: 1
- **Category**: Tdoc metadata
- **Question**: List the Tdocs presented at meeting RAN1#120 submitted by a given Company (replace 'CompanyX' with an actual vendor name from your knowledge graph).
- **Cypher** (see `../queries/cypher/P1_CQ1-3.cypher`):

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'CompanyX'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

## P2_CQ1-1

- **Phase**: 2
- **Category**: Resolution lookup
- **Question**: List the Agreements made at meeting RAN1#115 under agenda items beginning with 7.1.
- **Cypher** (see `../queries/cypher/P2_CQ1-1.cypher`):

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

## P2_CQ1-2

- **Phase**: 2
- **Category**: Resolution lookup
- **Question**: List the Agreements made at meeting RAN1#100 under agenda item 5.1.
- **Cypher** (see `../queries/cypher/P2_CQ1-2.cypher`):

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
```

## P2_CQ1-3

- **Phase**: 2
- **Category**: Resolution lookup
- **Question**: List the Conclusions recorded at meeting RAN1#121.
- **Cypher** (see `../queries/cypher/P2_CQ1-3.cypher`):

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence LIMIT 15
```

## P3_CQ001

- **Phase**: 3
- **Category**: TS structure
- **Question**: Return the top-level section table of contents of TS 38.214.
- **Cypher** (see `../queries/cypher/P3_CQ001.cypher`):

```cypher
MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
```

## P3_CQ002

- **Phase**: 3
- **Category**: TS structure
- **Question**: Return the immediate sub-sections of TS 38.214 section 5.1.
- **Cypher** (see `../queries/cypher/P3_CQ002.cypher`):

```cypher
MATCH (root:Section {sectionId: '38.214-5.1'})-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
```

## P3_CQ003

- **Phase**: 3
- **Category**: TS structure
- **Question**: Return the section breadcrumb (path to root) for TS 38.214 section 5.1.3.2.
- **Cypher** (see `../queries/cypher/P3_CQ003.cypher`):

```cypher
MATCH path = (target:Section {sectionId: '38.214-5.1.3.2'})-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
```

## P3_CQ004

- **Phase**: 3
- **Category**: TS structure
- **Question**: Return the per-level section count for TS 38.213 (structural complexity profile).
- **Cypher** (see `../queries/cypher/P3_CQ004.cypher`):

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
```

## P4_CQ1-1

- **Phase**: 4
- **Category**: CR rationale
- **Question**: Return the reason-for-change of CR R1-2504971.
- **Cypher** (see `../queries/cypher/P4_CQ1-1.cypher`):

```cypher
MATCH (cr:CR {tdocNumber: 'R1-2504971'}) WHERE cr.reasonForChange IS NOT NULL RETURN cr.tdocNumber, cr.reasonForChange
```

## P4_CQ1-2

- **Phase**: 4
- **Category**: CR rationale
- **Question**: Return the summary-of-change of CR R1-2506685.
- **Cypher** (see `../queries/cypher/P4_CQ1-2.cypher`):

```cypher
MATCH (cr:CR {tdocNumber: 'R1-2506685'}) WHERE cr.summaryOfChange IS NOT NULL RETURN cr.tdocNumber, cr.summaryOfChange
```

## P5_CQ1-1

- **Phase**: 5
- **Category**: TR study status
- **Question**: Return the trStatus, scope, and conclusions of TR 38.769.
- **Cypher** (see `../queries/cypher/P5_CQ1-1.cypher`):

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.769'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions
```

## P5_CQ1-2

- **Phase**: 5
- **Category**: TR study status
- **Question**: Return the trStatus and conclusions of TR 38.889.
- **Cypher** (see `../queries/cypher/P5_CQ1-2.cypher`):

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions
```
