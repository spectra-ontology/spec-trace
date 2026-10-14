# RAN1 itemized contract changes

This page accounts for 124 original Core IDs: 55 proposed clarifications and 69 substantive variants.

Each entry retains the exact original and revised question and query. The change rationale is a proposal, not a completed author semantic judgment. Technical check counts concern scorer enforcement and captured reference consistency; all author semantic reviews remain pending.

[Review guide](../REVIEW_GUIDE.md) · [Full technical task ledger](../canonical_tasks.jsonl) · [Per-item scorer checks](../provenance/adversarial_validation.json)

| ID | Proposed change class | Required fields | Native rows | Scorer checks |
| --- | --- | --- | ---: | ---: |
| [RAN1_P1_CQ1-1](#ran1_p1_cq1-1) | Proposed clarification | t.tdocNumber (string) | 2 | 7/7 |
| [RAN1_P1_CQ1-2](#ran1_p1_cq1-2) | Proposed clarification | t.tdocNumber (string) | 129 | 7/7 |
| [RAN1_P1_CQ1-3](#ran1_p1_cq1-3) | Proposed clarification | t.tdocNumber (string) | 110 | 7/7 |
| [RAN1_P1_CQ1-4](#ran1_p1_cq1-4) | Substantive variant | t.tdocNumber (string), m.meetingNumber (string), m.meetingNumberInt (integer) | 10 | 13/13 |
| [RAN1_P1_CQ1-5](#ran1_p1_cq1-5) | Proposed clarification | t.tdocNumber (string) | 102 | 7/7 |
| [RAN1_P1_CQ1-6](#ran1_p1_cq1-6) | Substantive variant | t.status (string) | 1 | 7/7 |
| [RAN1_P1_CQ1-7](#ran1_p1_cq1-7) | Proposed clarification | t.for (string) | 1 | 7/7 |
| [RAN1_P1_CQ1-8](#ran1_p1_cq1-8) | Proposed clarification | ct.contactName (string) | 1 | 7/7 |
| [RAN1_P1_CQ1-9](#ran1_p1_cq1-9) | Substantive variant | a.agendaNumber (string), a.agendaDescription (string) | 64 | 10/10 |
| [RAN1_P1_CQ2-3](#ran1_p1_cq2-3) | Proposed clarification | original_tdoc (string) | 1 | 7/7 |
| [RAN1_P1_CQ2-4](#ran1_p1_cq2-4) | Proposed clarification | t.tdocNumber (string), t.status (string) | 2,423 | 10/10 |
| [RAN1_P1_CQ2-5](#ran1_p1_cq2-5) | Proposed clarification | t.crCategory (string), t.clausesAffected (string) | 1 | 10/10 |
| [RAN1_P1_CQ2-6](#ran1_p1_cq2-6) | Substantive variant | t.tdocNumber (string) | 3 | 7/7 |
| [RAN1_P1_CQ2-7](#ran1_p1_cq2-7) | Proposed clarification | t.tdocNumber (string), a.agendaNumber (string) | 32 | 10/10 |
| [RAN1_P1_CQ3-1](#ran1_p1_cq3-1) | Proposed clarification | t.tdocNumber (string) | 299 | 7/7 |
| [RAN1_P1_CQ3-2](#ran1_p1_cq3-2) | Substantive variant | companyName (string), tdocNumber (string) | 148 | 10/10 |
| [RAN1_P1_CQ3-3](#ran1_p1_cq3-3) | Proposed clarification | c.companyName (string), tdocCount (integer) | 10 | 10/10 |
| [RAN1_P1_CQ3-4](#ran1_p1_cq3-4) | Proposed clarification | total (integer), approved (integer), approvalRate (number) | 1 | 13/13 |
| [RAN1_P1_CQ3-5](#ran1_p1_cq3-5) | Proposed clarification | t.tdocNumber (string), c.companyName (string), a.agendaNumber (string) | 162 | 13/13 |
| [RAN1_P1_CQ3-6](#ran1_p1_cq3-6) | Proposed clarification | wi.workItemCode (string), tdocCount (integer) | 10 | 10/10 |
| [RAN1_P1_CQ4-1](#ran1_p1_cq4-1) | Proposed clarification | m.meetingNumber (string), t.tdocNumber (string) | 123 | 10/10 |
| [RAN1_P1_CQ4-2](#ran1_p1_cq4-2) | Proposed clarification | t.status (string), count (integer) | 7 | 10/10 |
| [RAN1_P1_CQ4-3](#ran1_p1_cq4-3) | Proposed clarification | t.tdocNumber (string) | 101 | 7/7 |
| [RAN1_P2_CQ1-1](#ran1_p2_cq1-1) | Proposed clarification | a.resolutionId (string), a.content (string) | 11 | 10/10 |
| [RAN1_P2_CQ1-2](#ran1_p2_cq1-2) | Substantive variant | a.resolutionId (string), a.content (string) | 6 | 10/10 |
| [RAN1_P2_CQ1-3](#ran1_p2_cq1-3) | Proposed clarification | c.resolutionId (string), c.content (string) | 64 | 10/10 |
| [RAN1_P2_CQ1-4](#ran1_p2_cq1-4) | Proposed clarification | wa.resolutionId (string), wa.content (string) | 5 | 10/10 |
| [RAN1_P2_CQ1-5](#ran1_p2_cq1-5) | Substantive variant | a.resolutionId (string), a.content (string), m.meetingNumber (string), m.meetingNumberInt (integer) | 15 | 16/16 |
| [RAN1_P2_CQ1-6](#ran1_p2_cq1-6) | Substantive variant | a.resolutionId (string), a.content (string) | 47 | 10/10 |
| [RAN1_P2_CQ1-7](#ran1_p2_cq1-7) | Substantive variant | a.resolutionId (string), a.content (string) | 420 | 10/10 |
| [RAN1_P2_CQ2-1](#ran1_p2_cq2-1) | Proposed clarification | t.tdocNumber (string) | 4 | 7/7 |
| [RAN1_P2_CQ2-2](#ran1_p2_cq2-2) | Substantive variant | a.resolutionId (string), a.content (string) | 2 | 10/10 |
| [RAN1_P2_CQ2-3](#ran1_p2_cq2-3) | Substantive variant | a.resolutionId (string), a.content (string) | 44 | 10/10 |
| [RAN1_P2_CQ2-4](#ran1_p2_cq2-4) | Substantive variant | ai.agendaNumber (string), resolutionCount (integer) | 10 | 10/10 |
| [RAN1_P2_CQ2-5](#ran1_p2_cq2-5) | Substantive variant | a.resolutionId (string), a.content (string) | 488 | 10/10 |
| [RAN1_P2_CQ3-1](#ran1_p2_cq3-1) | Substantive variant | t.tdocNumber (string), a.resolutionId (string) | 2,483 | 10/10 |
| [RAN1_P2_CQ3-2](#ran1_p2_cq3-2) | Substantive variant | totalTdocs (integer), referencedTdocCount (integer), contributionRate (number) | 1 | 13/13 |
| [RAN1_P2_CQ3-3](#ran1_p2_cq3-3) | Substantive variant | c.companyName (string), contributionCount (integer) | 10 | 10/10 |
| [RAN1_P2_CQ3-4](#ran1_p2_cq3-4) | Proposed clarification | a.resolutionId (string), a.content (string), latestMeetingNumberInt (integer) | 10 | 13/13 |
| [RAN1_P2_CQ3-6](#ran1_p2_cq3-6) | Proposed clarification | t.tdocNumber (string) | 70 | 7/7 |
| [RAN1_P2_CQ4-1](#ran1_p2_cq4-1) | Substantive variant | c.companyName (string), flCount (integer) | 5 | 10/10 |
| [RAN1_P2_CQ4-2](#ran1_p2_cq4-2) | Substantive variant | ai.agendaNumber (string) | 37 | 7/7 |
| [RAN1_P2_CQ4-3](#ran1_p2_cq4-3) | Proposed clarification | c.companyName (string), flCount (integer) | 10 | 10/10 |
| [RAN1_P2_CQ5-1](#ran1_p2_cq5-1) | Substantive variant | m.meetingNumber (string), a.resolutionId (string), a.content (string), m.meetingNumberInt (integer) | 1,423 | 16/16 |
| [RAN1_P2_CQ5-10](#ran1_p2_cq5-10) | Substantive variant | a.resolutionId (string), a.content (string) | 182 | 10/10 |
| [RAN1_P2_CQ5-11](#ran1_p2_cq5-11) | Substantive variant | a.resolutionId (string), a.content (string) | 110 | 10/10 |
| [RAN1_P2_CQ5-12](#ran1_p2_cq5-12) | Substantive variant | a.resolutionId (string), a.content (string) | 55 | 10/10 |
| [RAN1_P2_CQ5-13](#ran1_p2_cq5-13) | Substantive variant | a.resolutionId (string), a.content (string) | 570 | 10/10 |
| [RAN1_P2_CQ5-2](#ran1_p2_cq5-2) | Substantive variant | a.resolutionId (string), a.content (string) | 461 | 10/10 |
| [RAN1_P2_CQ5-3](#ran1_p2_cq5-3) | Substantive variant | a.resolutionId (string), a.content (string) | 339 | 10/10 |
| [RAN1_P2_CQ5-4](#ran1_p2_cq5-4) | Substantive variant | a.resolutionId (string), a.content (string) | 1,530 | 10/10 |
| [RAN1_P2_CQ5-5](#ran1_p2_cq5-5) | Substantive variant | a.resolutionId (string), a.content (string) | 532 | 10/10 |
| [RAN1_P2_CQ5-6](#ran1_p2_cq5-6) | Proposed clarification | m.meetingNumber (string), agreementCount (integer), m.meetingNumberInt (integer) | 33 | 13/13 |
| [RAN1_P2_CQ5-7](#ran1_p2_cq5-7) | Substantive variant | a.resolutionId (string), a.content (string) | 75 | 10/10 |
| [RAN1_P2_CQ5-8](#ran1_p2_cq5-8) | Substantive variant | a.resolutionId (string), a.content (string) | 170 | 10/10 |
| [RAN1_P2_CQ5-9](#ran1_p2_cq5-9) | Substantive variant | a.resolutionId (string), a.content (string) | 80 | 10/10 |
| [RAN1_P3_CQ001](#ran1_p3_cq001) | Substantive variant | sec.sectionNumber (string), sec.sectionTitle (string), specRelease (string), specVersion (string) | 46 | 16/16 |
| [RAN1_P3_CQ002](#ran1_p3_cq002) | Substantive variant | sourceSectionId (string), subSectionId (string), sub.sectionNumber (string), sub.sectionTitle (string) | 35 | 16/16 |
| [RAN1_P3_CQ003](#ran1_p3_cq003) | Substantive variant | targetSectionId (string), breadcrumb (json) | 5 | 9/9 |
| [RAN1_P3_CQ004](#ran1_p3_cq004) | Substantive variant | sec.level (integer), sectionCount (integer) | 5 | 10/10 |
| [RAN1_P3_CQ005](#ran1_p3_cq005) | Substantive variant | sectionId (string), sectionNumber (string), tableCount (integer) | 2 | 13/13 |
| [RAN1_P3_CQ006](#ran1_p3_cq006) | Proposed clarification | tableId (string), tbl.tableNumber (string), tbl.tableCaption (string), sectionId (string) | 548 | 16/16 |
| [RAN1_P3_CQ007](#ran1_p3_cq007) | Proposed clarification | sp.specNumber (string), sectionId (string), sec.sectionNumber (string), sec.sectionTitle (string) | 57 | 16/16 |
| [RAN1_P3_CQ008](#ran1_p3_cq008) | Substantive variant | ts (string), secCnt (integer), tblCnt (integer), figCnt (integer) | 8 | 16/16 |
| [RAN1_P3_CQ009](#ran1_p3_cq009) | Substantive variant | sourceSectionId (string), targetSectionId (string), tgt.sectionNumber (string), tgt.sectionTitle (string) | 20 | 16/16 |
| [RAN1_P3_CQ010](#ran1_p3_cq010) | Substantive variant | targetSectionId (string), sourceSectionId (string), src.sectionNumber (string), src.sectionTitle (string) | 115 | 16/16 |
| [RAN1_P3_CQ011](#ran1_p3_cq011) | Proposed clarification | sectionId (string), refByCnt (integer) | 15 | 10/10 |
| [RAN1_P3_CQ012](#ran1_p3_cq012) | Proposed clarification | hasMutualReferences (boolean) | 1 | 7/7 |
| [RAN1_P3_CQ013](#ran1_p3_cq013) | Proposed clarification | ts (string), secCnt (integer), refCnt (integer), refDensity (number) | 8 | 16/16 |
| [RAN1_P3_CQ014](#ran1_p3_cq014) | Proposed clarification | sectionA (string), sectionB (string) | 188 | 10/10 |
| [RAN1_P3_CQ015](#ran1_p3_cq015) | Substantive variant | sourceSectionId (string), viaSectionId (string), targetSectionId (string), targetTitle (string) | 23 | 16/16 |
| [RAN1_P3_CQ016](#ran1_p3_cq016) | Proposed clarification | totalCR (integer) | 1 | 7/7 |
| [RAN1_P3_CQ017](#ran1_p3_cq017) | Proposed clarification | cr.tdocNumber (string), latestMeetingNumberInt (integer) | 20 | 10/10 |
| [RAN1_P3_CQ018](#ran1_p3_cq018) | Substantive variant | cr.tdocNumber (string), cr.clausesAffected (string) | 83 | 10/10 |
| [RAN1_P3_CQ019](#ran1_p3_cq019) | Proposed clarification | sp.specNumber (string), crCount (integer) | 8 | 10/10 |
| [RAN1_P3_CQ020](#ran1_p3_cq020) | Proposed clarification | cr.tdocNumber (string) | 123 | 7/7 |
| [RAN1_P3_CQ021](#ran1_p3_cq021) | Substantive variant | tdocNumber (string), tokenCount (integer), clauseTokens (json) | 34 | 12/12 |
| [RAN1_P3_CQ022](#ran1_p3_cq022) | Proposed clarification | meeting (string), crCount (integer), meetingInt (integer) | 60 | 13/13 |
| [RAN1_P3_CQ023](#ran1_p3_cq023) | Substantive variant | agrCount (integer) | 1 | 7/7 |
| [RAN1_P3_CQ024](#ran1_p3_cq024) | Substantive variant | agr.resolutionId (string), content (string), m.meetingNumber (string), m.meetingNumberInt (integer) | 10 | 16/16 |
| [RAN1_P3_CQ025](#ran1_p3_cq025) | Substantive variant | sp.specNumber (string), agrCount (integer) | 8 | 10/10 |
| [RAN1_P3_CQ026](#ran1_p3_cq026) | Substantive variant | agr.resolutionId (string), content (string) | 1 | 10/10 |
| [RAN1_P3_CQ027](#ran1_p3_cq027) | Proposed clarification | hasCrossSpecAgreement (boolean) | 1 | 7/7 |
| [RAN1_P3_CQ028](#ran1_p3_cq028) | Substantive variant | res.resolutionId (string), content (string) | 3 | 10/10 |
| [RAN1_P3_CQ029](#ran1_p3_cq029) | Proposed clarification | sp.specNumber (string) | 5 | 7/7 |
| [RAN1_P3_CQ030](#ran1_p3_cq030) | Substantive variant | tableId (string), tbl.tableNumber (string), tbl.tableCaption (string) | 332 | 13/13 |
| [RAN1_P3_CQ031](#ran1_p3_cq031) | Substantive variant | sp.specNumber (string), sectionCount (integer) | 2 | 10/10 |
| [RAN1_P3_CQ032](#ran1_p3_cq032) | Substantive variant | sp.specNumber (string), sectionId (string), sec.sectionTitle (string), tables (json) | 53 | 15/15 |
| [RAN1_P3_CQ033](#ran1_p3_cq033) | Substantive variant | sp.specNumber (string), sectionId (string), sec.sectionTitle (string), tables (json) | 107 | 15/15 |
| [RAN1_P3_CQ034](#ran1_p3_cq034) | Substantive variant | sp.specNumber (string), sectionId (string), sec.sectionTitle (string), tables (json) | 73 | 15/15 |
| [RAN1_P3_CQ035](#ran1_p3_cq035) | Proposed clarification | sp.specNumber (string), sectionId (string), sec.sectionTitle (string) | 182 | 13/13 |
| [RAN1_P3_CQ036](#ran1_p3_cq036) | Proposed clarification | ts (string), crCount (integer), sectionCount (integer) | 5 | 13/13 |
| [RAN1_P3_CQ037](#ran1_p3_cq037) | Proposed clarification | co.companyName (string), crCount (integer) | 71 | 10/10 |
| [RAN1_P3_CQ038](#ran1_p3_cq038) | Substantive variant | sectionId (string), refCount (integer), literalClauseCRCount (integer) | 10 | 13/13 |
| [RAN1_P3_CQ039](#ran1_p3_cq039) | Proposed clarification | co.companyName (string), crCount (integer) | 10 | 10/10 |
| [RAN1_P3_CQ040](#ran1_p3_cq040) | Substantive variant | ts (string), crCnt (integer), agrCnt (integer) | 5 | 13/13 |
| [RAN1_P3_CQ041](#ran1_p3_cq041) | Proposed clarification | sectionId (string), tableCount (integer) | 98 | 10/10 |
| [RAN1_P3_CQ042](#ran1_p3_cq042) | Substantive variant | sectionId (string), tableCount (integer), subSectionCount (integer) | 10 | 13/13 |
| [RAN1_P3_CQ044](#ran1_p3_cq044) | Proposed clarification | spec (string) | 16 | 7/7 |
| [RAN1_P3_CQ045](#ran1_p3_cq045) | Substantive variant | spec (string) | 3 | 7/7 |
| [RAN1_P3_P3-S8-CQ02](#ran1_p3_p3-s8-cq02) | Proposed clarification | allLinked (boolean) | 1 | 7/7 |
| [RAN1_P3_P3-S8-CQ04](#ran1_p3_p3-s8-cq04) | Substantive variant | matches (boolean) | 1 | 7/7 |
| [RAN1_P3_P3-S8-CQ05](#ran1_p3_p3-s8-cq05) | Proposed clarification | class (string), granularity (string), c (integer) | 1 | 13/13 |
| [RAN1_P4_CQ1-3](#ran1_p4_cq1-3) | Proposed clarification | cr.tdocNumber (string), cr.consequencesIfNotApproved (string) | 14 | 10/10 |
| [RAN1_P4_CQ2-1](#ran1_p4_cq2-1) | Proposed clarification | sp.specNumber (string), relationType (string) | 5 | 10/10 |
| [RAN1_P4_CQ2-2](#ran1_p4_cq2-2) | Substantive variant | affectedSpec (string), crCount (integer) | 10 | 10/10 |
| [RAN1_P4_CQ2-3](#ran1_p4_cq2-3) | Substantive variant | crCount (integer), sampleCRs (json) | 1 | 9/9 |
| [RAN1_P4_CQ2-4](#ran1_p4_cq2-4) | Proposed clarification | cr.tdocNumber (string), affectedSpecCount (integer), affectedSpecs (json) | 10 | 12/12 |
| [RAN1_P4_CQ3-2](#ran1_p4_cq3-2) | Substantive variant | pack.crPackId (string), crCount (integer) | 66 | 10/10 |
| [RAN1_P4_CQ3-3](#ran1_p4_cq3-3) | Proposed clarification | pack.crPackId (string), crCount (integer) | 10 | 10/10 |
| [RAN1_P5_CQ1-3](#ran1_p5_cq1-3) | Proposed clarification | tr.trNumber (string), tr.trTitle (string), tr.scope (string) | 1 | 13/13 |
| [RAN1_P5_CQ2-1](#ran1_p5_cq2-1) | Substantive variant | sp.specNumber (string), ti.impactType (string) | 1 | 10/10 |
| [RAN1_P5_CQ2-2](#ran1_p5_cq2-2) | Substantive variant | s.sectionId (string) | 1 | 7/7 |
| [RAN1_P5_CQ2-3](#ran1_p5_cq2-3) | Substantive variant | tr.trNumber (string), ti.impactType (string) | 11 | 10/10 |
| [RAN1_P5_CQ2-4](#ran1_p5_cq2-4) | Substantive variant | tr.trNumber (string) | 1 | 7/7 |
| [RAN1_P5_CQ2-5](#ran1_p5_cq2-5) | Substantive variant | tr.trNumber (string), sp.specNumber (string) | 1 | 10/10 |
| [RAN1_P5_CQ3-1](#ran1_p5_cq3-1) | Substantive variant | s.sectionId (string) | 2 | 7/7 |
| [RAN1_P5_CQ3-2](#ran1_p5_cq3-2) | Substantive variant | s.sectionId (string) | 1 | 7/7 |
| [RAN1_P5_CQ3-3](#ran1_p5_cq3-3) | Substantive variant | sp.specNumber (string), ti.impactType (string), ti.affectedSection (string), ti.impactDescription (string) | 2 | 16/16 |
| [RAN1_P5_CQ4-1](#ran1_p5_cq4-1) | Substantive variant | tr.trNumber (string), ti.impactType (string), sp.specNumber (string) | 7 | 13/13 |
| [RAN1_P5_CQ4-2](#ran1_p5_cq4-2) | Substantive variant | tr.trStatus (string), tr.scope (string) | 1 | 10/10 |
| [RAN1_P5_CQ5-1](#ran1_p5_cq5-1) | Proposed clarification | ref.trNumber (string) | 6 | 7/7 |
| [RAN1_P5_CQ5-2](#ran1_p5_cq5-2) | Proposed clarification | src.trNumber (string) | 4 | 7/7 |
| [RAN1_P5_CQ5-3](#ran1_p5_cq5-3) | Proposed clarification | trNumber (string), referenceCount (integer) | 5 | 10/10 |

## RAN1_P1_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs at meeting RAN1#120 tied to Work Item NR_eMIMO-Core (MIMO meeting preparation).

**Revised question:** List all distinct TDoc identifiers presented at RAN1#120 and related to Work Item NR_eMIMO-Core in the released graph.

**Proposed rationale:** The original entity/filter meaning is retained. Remove the unstated ten-row cap; extra title/type/status fields are not required.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-1/c8d4b67d4baff33ab4a154ce88442871a986dbe4de7e6cccc8ba1ac1b6539654.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-1/c8d4b67d4baff33ab4a154ce88442871a986dbe4de7e6cccc8ba1ac1b6539654.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f4be5f19275d0894b21bf1572b827f8f544e9f68a933836e4e325e9b588921da`.

## RAN1_P1_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs under Agenda Item 9.2 (AI/ML for NR) at meeting RAN1#121 (AI/ML session preparation).

**Revised question:** List all distinct TDoc identifiers presented at RAN1#121 whose recorded agenda number is 9.2 or begins with 9.2. in the released graph.

**Proposed rationale:** Remove the unasked cap and give hierarchical agenda membership an explicit boundary.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE (a.agendaNumber = '9.2' OR a.agendaNumber STARTS WITH '9.2.') RETURN DISTINCT t.tdocNumber, t.title, t.type, a.agendaNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-2/3a7fdc79903d986b4899409246f83ebca45b1a03dc74eb346a68a39ac21204e2.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-2/3a7fdc79903d986b4899409246f83ebca45b1a03dc74eb346a68a39ac21204e2.jsonl); 129 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ef320d70ccfdf78069677c473222a15bde98279dcf25a3309672c6a96c2c3715`.

## RAN1_P1_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs submitted by Huawei at meeting RAN1#120 (tracking a competitor's contributions).

**Revised question:** List all distinct TDoc identifiers presented at RAN1#120 and submitted by the graph Company named Huawei.

**Proposed rationale:** Retain company/meeting scope and entity membership; remove hidden cap.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-3/9a6bc0f4c06527926c87bfd3b081dfe57919ef1fd42e991cd996c83bd768a190.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-3/9a6bc0f4c06527926c87bfd3b081dfe57919ef1fd42e991cd996c83bd768a190.jsonl); 110 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `34b8e60fa303452d7a6a794614820873d21f0e9130b2c263701ee68a79a000d5`.

## RAN1_P1_CQ1-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The graph has meeting-based ordering rather than actual submission time; explicit ten-row scope is a revised operational definition.']

**Original question:** List the most recently submitted TDocs targeting Rel-18 (contribution status by release).

**Revised question:** Return the ten distinct TDoc/meeting pairs targeting Rel-18 with greatest recorded meetingNumberInt. Return TDoc identifier, meeting-number string and meetingNumberInt; rank the integer descending, then TDoc identifier and meeting-number string ascending. Recency refers to meeting numbers, not submission timestamps; return all pairs if fewer than ten exist.

**Proposed rationale:** The graph has meeting-based ordering rather than actual submission time; explicit ten-row scope is a revised operational definition. Final returned meeting-string key disambiguates meetings sharing the same integer; DISTINCT operates only on asked fields.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.type, t.status, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber,m.meetingNumber,m.meetingNumberInt ORDER BY m.meetingNumberInt DESC,t.tdocNumber ASC,m.meetingNumber ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "m.meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "m.meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "t.tdocNumber"
      },
      {
        "direction": "asc",
        "field": "m.meetingNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most ten records under the declared total-order keys",
    "tie_policy": "deterministic_all_keys",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-4/cd63721c7e5d9e7d46f22db5098e80c21ae90f15bfb13bea3d5beab2b6f7ab75.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-4/cd63721c7e5d9e7d46f22db5098e80c21ae90f15bfb13bea3d5beab2b6f7ab75.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `7930fb065a715fae9893eef32c3aa6f5773e35f98bf4e166ecfcbd67e46ad61e`.

## RAN1_P1_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs approved or agreed at meeting RAN1#121.

**Revised question:** List all distinct TDoc identifiers at RAN1#121 with recorded status approved or agreed.

**Proposed rationale:** Use recorded status, not independent approval validation; remove hidden cap.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-5/d775c9f78a085c7febe3989770912c028b17923d6fde03cd525dcf2edda99455.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-5/d775c9f78a085c7febe3989770912c028b17923d6fde03cd525dcf2edda99455.jsonl); 102 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d5c910dce82e36703a233fd7bcb0e7365052aa2baf9d863261142b23e5253520`.

## RAN1_P1_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A snapshot property does not prove historically final status. All matching nodes are retained rather than choosing an arbitrary one.']

**Original question:** What is the final status of TDoc R1-2501234? (single-document status lookup)

**Revised question:** Return every distinct status value recorded for TDoc identifier R1-2501234 in the released graph.

**Proposed rationale:** A snapshot property does not prove historically final status. All matching nodes are retained rather than choosing an arbitrary one.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.status LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN DISTINCT t.tdocNumber, t.title, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.status",
      "nullable": true,
      "source_column_or_expression": "t.status",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-6/ff13d9d9ebddd420e00224eccde3f9a26cf87419115208a3831481162805c7e9.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-6/ff13d9d9ebddd420e00224eccde3f9a26cf87419115208a3831481162805c7e9.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ce603f9754327e11148f6f5d7c03f2a35dbec2b5f0ae056703b20f19ffc51660`.

## RAN1_P1_CQ1-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What is the intended purpose (For) of TDoc R1-2501234 — Discussion, Approval, or Agreement?

**Revised question:** Return the distinct For property values recorded for TDoc identifier R1-2501234.

**Proposed rationale:** The existing query retrieves recorded purpose values; remove arbitrary single-node cap.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.for LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN DISTINCT t.tdocNumber, t.title, t.for
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.for",
      "nullable": true,
      "source_column_or_expression": "t.for",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-7/eef5473b0b05bb27ac767e2ad36357625a10ba6cacc72c8f212ba760bd92b312.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-7/eef5473b0b05bb27ac767e2ad36357625a10ba6cacc72c8f212ba760bd92b312.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f90eb479bdb43ba3b65cceb12f35d565281cd9f050835f384bd31caf256a4c64`.

## RAN1_P1_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Who is the contact person for TDoc R1-2501234? (contact lookup)

**Revised question:** List all distinct recorded contact names linked by HAS_CONTACT to TDoc R1-2501234.

**Proposed rationale:** Single-contact uniqueness is not guaranteed by a LIMIT1; remove it.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'})-[:HAS_CONTACT]->(ct:Contact) RETURN t.tdocNumber, ct.contactName LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'})-[:HAS_CONTACT]->(ct:Contact) RETURN DISTINCT t.tdocNumber, ct.contactName
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ct.contactName",
      "nullable": true,
      "source_column_or_expression": "ct.contactName",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-8/eb8d7dcb70344df0eea62b712527d3c0ce6edd8b58668ca97be2df3348b09616.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-8/eb8d7dcb70344df0eea62b712527d3c0ce6edd8b58668ca97be2df3348b09616.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e031fe4453f351000790614411d6b929dc8afeb92468d4feab7eefb023be365f`.

## RAN1_P1_CQ1-9

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The query reconstructs agenda entries from contributions, not an independent complete meeting agenda. Explicit documentary scope avoids an unverified completeness claim.']

**Original question:** List the full agenda of meeting RAN1#120 with descriptions (meeting preparation).

**Revised question:** List all distinct agenda-number/description pairs linked to TDocs presented at RAN1#120.

**Proposed rationale:** The query reconstructs agenda entries from contributions, not an independent complete meeting agenda. Explicit documentary scope avoids an unverified completeness claim.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN DISTINCT a.agendaNumber, a.agendaDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.agendaNumber",
      "nullable": true,
      "source_column_or_expression": "a.agendaNumber",
      "type": "string"
    },
    {
      "name": "a.agendaDescription",
      "nullable": true,
      "source_column_or_expression": "a.agendaDescription",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ1-9/fb3379fb8d9de97acc5213afcc5c75fafc57ee13e8ad8bef4a9582600dbcdaa7.json), [complete native rows](../reference_outputs/RAN1_P1_CQ1-9/fb3379fb8d9de97acc5213afcc5c75fafc57ee13e8ad8bef4a9582600dbcdaa7.jsonl); 64 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `047fe5846d16bd3eec13ec4e8387dec18b0b56cae8bc5d6b7232347f8769fa33`.

## RAN1_P1_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which LS does TDoc R1-2000004 reply to? (reply-chain tracing)

**Revised question:** List all distinct original TDoc identifiers linked from R1-2000004 by REPLY_TO and recorded with type LS in or LS out.

**Proposed rationale:** The original question asks an LS target; the original query did not constrain target type. Add the explicit LS restriction and remove hidden cap.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2000004'})-[:REPLY_TO]->(original:Tdoc) RETURN t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2000004'})-[:REPLY_TO]->(original:Tdoc) WHERE original.type IN ['LS in', 'LS out'] RETURN DISTINCT t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "original_tdoc",
      "nullable": true,
      "source_column_or_expression": "original_tdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ2-3/73761b710b0f9f7d99dc5e4429db045ce4aca96846ec8072918537e326f2524c.json), [complete native rows](../reference_outputs/RAN1_P1_CQ2-3/73761b710b0f9f7d99dc5e4429db045ce4aca96846ec8072918537e326f2524c.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b4d546d0bba495871e7094c14007338a3f76778e6e57e39a62a11a12ed2cebe9`.

## RAN1_P1_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs modifying TS 38.214 with their status (revision status of 38.214).

**Revised question:** List all distinct TDoc-identifier/status pairs with type CR or draftCR linked by MODIFIES to TS 38.214.

**Proposed rationale:** The original query arbitrarily returns one CR; remove cap and grade both identifier and requested status.

**Original query**

```cypher
MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN t.tdocNumber, t.title, t.status, t.type ORDER BY t.tdocNumber ASC LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN DISTINCT t.tdocNumber, t.title, t.status, t.type
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "t.status",
      "nullable": true,
      "source_column_or_expression": "t.status",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ2-4/6dcbcb3ecd2315ab79605fc002304e8edeed8b165bc37d210f857d896a9e6c19.json), [complete native rows](../reference_outputs/RAN1_P1_CQ2-4/6dcbcb3ecd2315ab79605fc002304e8edeed8b165bc37d210f857d896a9e6c19.jsonl); 2,423 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3a882cd5aa8cf288edc8ae1dcff73e02f1c926439ab6691da88efa7e7ddde162`.

## RAN1_P1_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What are the change category (F/A/B/C/D) and affected clauses of CR R1-2504971?

**Revised question:** Return every distinct recorded change-category/affected-clauses string pair for TDoc R1-2504971. Preserve clausesAffected as a literal string rather than inferring a parsed clause set.

**Proposed rationale:** Both requested fields are graded; preserve string representation and remove arbitrary one-node selection.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2504971'}) RETURN t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2504971'}) RETURN DISTINCT t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.crCategory",
      "nullable": true,
      "source_column_or_expression": "t.crCategory",
      "type": "string"
    },
    {
      "name": "t.clausesAffected",
      "nullable": true,
      "source_column_or_expression": "t.clausesAffected",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ2-5/2e135fa99122fa719a61282d06b4d23454294f18400cf108306cf226643906f5.json), [complete native rows](../reference_outputs/RAN1_P1_CQ2-5/2e135fa99122fa719a61282d06b4d23454294f18400cf108306cf226643906f5.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `289cb099c96dd274ad5a8002377495e7dff0bb62f67d0daf41461b5cdc3b1fee`.

## RAN1_P1_CQ2-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A postponed status does not independently identify the eventual next meeting; task is explicitly snapshot-based.']

**Original question:** List the TDocs postponed to the next meeting at RAN1#120 (tracking open items).

**Revised question:** List all distinct TDoc identifiers presented at RAN1#120 with recorded status postponed.

**Proposed rationale:** A postponed status does not independently identify the eventual next meeting; task is explicitly snapshot-based.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {status: 'postponed'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {status: 'postponed'}) RETURN DISTINCT t.tdocNumber, t.title, t.type
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ2-6/d04c50b11578c0f0c88794812875c2c1a13aad7d747e75bb7a4fd91f010f6634.json), [complete native rows](../reference_outputs/RAN1_P1_CQ2-6/d04c50b11578c0f0c88794812875c2c1a13aad7d747e75bb7a4fd91f010f6634.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7de4f524b8d979066f63ec4757e95971401dbbe19004a16742199f7fda6b7097`.

## RAN1_P1_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the incoming LSs (LS in) at meeting RAN1#120 and their agenda items (reviewing other WGs' requests).

**Revised question:** List all distinct incoming-LS TDoc identifiers and agenda-number pairs at RAN1#120, using recorded type LS in.

**Proposed rationale:** Grade both requested document and agenda roles; origin/title are incidental.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "a.agendaNumber",
      "nullable": true,
      "source_column_or_expression": "a.agendaNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ2-7/b75ed76895cdaf0f453dcce1ed6d46b3f51ee128d3a824f221b49d75cc2a354b.json), [complete native rows](../reference_outputs/RAN1_P1_CQ2-7/b75ed76895cdaf0f453dcce1ed6d46b3f51ee128d3a824f221b49d75cc2a354b.jsonl); 32 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4107c1f64cb32baaff7fc37035625281fe0cfa8fd187d975305a669eb7ce1f08`.

## RAN1_P1_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs Samsung submitted under Work Item NR_MIMO_evo_DL_UL-Core (NR MIMO Evolution).

**Revised question:** List all distinct Samsung-submitted TDoc identifiers related to Work Item NR_MIMO_evo_DL_UL-Core.

**Proposed rationale:** Membership requested without a cap; remove cap.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-1/7599aa68ac76ec892ae2869db40c43842a5d1898b2acc3364c62f7f7144207ba.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-1/7599aa68ac76ec892ae2869db40c43842a5d1898b2acc3364c62f7f7144207ba.jsonl); 299 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `20cce430bebe22b9a767dcf3ed5f743e97c4d6ad85d50c6ae241165628d0450b`.

## RAN1_P1_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original other-companies reference remains unspecified; this candidate is a new named-input variant.']

**Explicit additional inputs (retained provenance)**

```json
[
  {
    "name": "focal_companyName",
    "origin": "new explicitly named benchmark input; not recovered original author intent",
    "value": "Samsung"
  }
]
```

**Original question:** List other companies' TDocs under Agenda Item 8.1 (NR Coverage Enhancement) at meeting RAN1#120 (surveying competitors).

**Revised question:** Using Samsung as the explicitly supplied focal company, list all distinct company-name/TDoc-number pairs under agenda item 8.1 or its dotted descendants at RAN1#120, excluding companyName Samsung.

**Proposed rationale:** The original question never supplies the reference company. This new named-input variant supplies Samsung openly rather than pretending to certify the ambiguous original; remove hidden output caps and avoid prefix 8.10 matching 8.1.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '8.1' MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (:Meeting {meetingNumber:'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem), (t)-[:SUBMITTED_BY]->(c:Company) WHERE (a.agendaNumber='8.1' OR a.agendaNumber STARTS WITH '8.1.') AND c.companyName <> 'Samsung' RETURN DISTINCT c.companyName AS companyName,t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": true,
      "source_column_or_expression": "companyName",
      "type": "string"
    },
    {
      "name": "tdocNumber",
      "nullable": true,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-2/a8b9f41489f21e1ca83fef2665706e1e7a69a926957c49292a7bb2dc00bebd12.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-2/a8b9f41489f21e1ca83fef2665706e1e7a69a926957c49292a7bb2dc00bebd12.jsonl); 148 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `fe72bcab26847fe479bc64c4db344d52a23bc54cd097c237776f5d60643e7a64`.

## RAN1_P1_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which companies contributed most to Work Item NR_unlic-Core (NR-U)? Top 10 by TDoc count (competitive landscape).

**Revised question:** Return at most ten companies related to NR_unlic-Core, with counts of distinct matching TDocs, ordered by count descending then company name ascending.

**Proposed rationale:** Define document counting unit and deterministic tie policy; counts of duplicate join bindings are not document counts.

**Original query**

```cypher
MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.companyName",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
      "type": "string"
    },
    {
      "name": "tdocCount",
      "nullable": false,
      "source_column_or_expression": "tdocCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tdocCount"
      },
      {
        "direction": "asc",
        "field": "c.companyName"
      }
    ],
    "tie_policy": "company name ascending; exactly ten at most, excluding extra boundary ties"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most ten companies; no extra boundary ties",
    "tie_policy": "company name ascending; exactly ten at most, excluding extra boundary ties",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-3/3c5029b637a266ede1ca75a5849606f7e8960679b954a41c9e7e6b74d5535003.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-3/3c5029b637a266ede1ca75a5849606f7e8960679b954a41c9e7e6b74d5535003.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bcf67a72463863a9190de62118b8b6a30ea7cbb9c2b43f8c14e31424709d83d0`.

## RAN1_P1_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What share and count of Qualcomm's TDocs were approved or agreed? (contribution success rate)

**Revised question:** For distinct Qualcomm-submitted TDocs, return total document count, approved-or-agreed document count, and that count as a percentage of the total rounded to one decimal place; return null percentage when total is zero.

**Proposed rationale:** Requested count/share need every numeric field. Count distinct TDocs before aggregating and define zero-denominator behavior.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Qualcomm'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, round(100.0 * approved / total, 1) AS approvalRate LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company {companyName:'Qualcomm'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH DISTINCT t WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved','agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, CASE WHEN total=0 THEN null ELSE round(100.0*approved/total,1) END AS approvalRate
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "total",
      "nullable": false,
      "source_column_or_expression": "total",
      "type": "integer"
    },
    {
      "name": "approved",
      "nullable": false,
      "source_column_or_expression": "approved",
      "type": "integer"
    },
    {
      "name": "approvalRate",
      "nullable": true,
      "source_column_or_expression": "approvalRate",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one aggregate record, including zero-total case",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-4/722d55826c940cbe993092417ce8003f402c29aa8e76272ccf4c3c0f3e0bfc47.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-4/722d55826c940cbe993092417ce8003f402c29aa8e76272ccf4c3c0f3e0bfc47.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `2e81c325e7bee51ca37369ce11f20b6e1b6597a0bb16b55ac579e0c147fed4a7`.

## RAN1_P1_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List other companies' TDocs under the same agenda item as TDoc R1-2501234 (checking competing contributions).

**Revised question:** List all distinct TDoc/company/agenda-number triples sharing a recorded agenda node with R1-2501234, excluding that TDoc and companies that submitted R1-2501234.

**Proposed rationale:** The original query excludes only the source TDoc, not its companies; enforce the requested other-company role.

**Original query**

```cypher
MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber AND NOT EXISTS { MATCH (t0)-[:SUBMITTED_BY]->(c) } RETURN DISTINCT t.tdocNumber, t.title, c.companyName, a.agendaNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "c.companyName",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
      "type": "string"
    },
    {
      "name": "a.agendaNumber",
      "nullable": true,
      "source_column_or_expression": "a.agendaNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-5/47b281e5bcf7cffcc0fdbb3c4247edcc33060e7fa270fd15bedaf88720882db6.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-5/47b281e5bcf7cffcc0fdbb3c4247edcc33060e7fa270fd15bedaf88720882db6.jsonl); 162 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `5bfec8d268b90c321f8228291ad3747dc8bc807ae1ca13193b8b245672862e35`.

## RAN1_P1_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What are Nokia's main technical areas? Top 10 Work Items by contribution count.

**Revised question:** Among all recorded Work Item-code groups, return the ten with the largest numbers of distinct Nokia-submitted TDoc nodes, including zero-count groups. Return code and count; sort count descending then code ascending, returning all available groups if fewer than ten exist.

**Proposed rationale:** Operationalizes main areas as the explicitly requested Work Item/TDoc ranking; count distinct documents. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Nokia'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS tdocCount ORDER BY tdocCount DESC, wi.workItemCode ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (wi:WorkItem) OPTIONAL MATCH (:Company {companyName:'Nokia'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi) RETURN wi.workItemCode,count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC,wi.workItemCode ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "wi.workItemCode",
      "nullable": true,
      "source_column_or_expression": "wi.workItemCode",
      "type": "string"
    },
    {
      "name": "tdocCount",
      "nullable": false,
      "source_column_or_expression": "tdocCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tdocCount"
      },
      {
        "direction": "asc",
        "field": "wi.workItemCode"
      }
    ],
    "tie_policy": "Work Item code ascending; at most ten entries"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.",
    "short_population": "all_available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ3-6/68a6fcfd753540496354bc333d5786bce7efb788b52dafb08c4151292922c52c.json), [complete native rows](../reference_outputs/RAN1_P1_CQ3-6/68a6fcfd753540496354bc333d5786bce7efb788b52dafb08c4151292922c52c.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a9e3cc02113f3796fa357376ac6cd6695f498304b983cffa680d75714abf02df`.

## RAN1_P1_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Samsung's contributions to Work Item NR_eMIMO-Core across past meetings (tracing a technical history).

**Revised question:** List all distinct meeting-number/TDoc-identifier pairs for Samsung-submitted TDocs related to NR_eMIMO-Core.

**Proposed rationale:** Meeting and document jointly identify the requested history; no cap was asked.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.meetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT m.meetingNumber, t.tdocNumber, t.title, t.status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ4-1/94089c3e91cc31bd90e45b199ee05fed1bce3dab81a4a44c39d3f89a349df32e.json), [complete native rows](../reference_outputs/RAN1_P1_CQ4-1/94089c3e91cc31bd90e45b199ee05fed1bce3dab81a4a44c39d3f89a349df32e.jsonl); 123 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `382a7ed8e92e6c7a48a9451f12159492aacfe690b1b80d3ac058dfc5ac51ae7f`.

## RAN1_P1_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Summarize the outcome of Ericsson's contributions at meeting RAN1#120 by status (count per status).

**Revised question:** Return every recorded status and the number of distinct Ericsson-submitted TDocs with that status at RAN1#120.

**Proposed rationale:** A status distribution requires both status and count; counting unit is distinct documents.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(t) AS count ORDER BY count DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(DISTINCT t) AS count
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.status",
      "nullable": true,
      "source_column_or_expression": "t.status",
      "type": "string"
    },
    {
      "name": "count",
      "nullable": false,
      "source_column_or_expression": "count",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ4-2/07970c75d3496079a8a580de635e2a589c80da35c42a99d1888203324e72aaf5.json), [complete native rows](../reference_outputs/RAN1_P1_CQ4-2/07970c75d3496079a8a580de635e2a589c80da35c42a99d1888203324e72aaf5.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3c97348d0c3247b534e211981260df7ce9162baa6b420c2927e558be6d717f7d`.

## RAN1_P1_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs still not treated under Agenda Item 9.3 (NR duplex evolution) at meeting RAN1#120.

**Revised question:** List all distinct TDoc identifiers at RAN1#120 with status not treated and agenda number 9.3 or a 9.3. descendant.

**Proposed rationale:** Use exact hierarchical prefix boundary and remove hidden cap.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.3' AND t.status = 'not treated' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE (a.agendaNumber = '9.3' OR a.agendaNumber STARTS WITH '9.3.') AND t.status = 'not treated' RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P1_CQ4-3/8d3f16739420010921945be90a36d252b3d2ad027dcdded54725717e897dec52.json), [complete native rows](../reference_outputs/RAN1_P1_CQ4-3/8d3f16739420010921945be90a36d252b3d2ad027dcdded54725717e897dec52.jsonl); 101 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d846b4cae96a0d072690891c24b12391ea27dc2e0392e1b690c08ce0d63d3cf5`.

## RAN1_P2_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the agreements under Agenda Item 7.1 (NR MIMO) at meeting RAN1#115 (MIMO meeting outcomes).

**Revised question:** List all distinct agreement-identifier/content pairs at RAN1#115 whose linked agenda number is 7.1 or begins with 7.1.

**Proposed rationale:** Original agreements imply identifiers and text; both must be graded. No cap is specified.

**Original query**

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE (ai.agendaNumber = '7.1' OR ai.agendaNumber STARTS WITH '7.1.') RETURN DISTINCT a.resolutionId, a.content, ai.agendaNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-1/57698c835e530fdd1d4dbadbbfca982ac8add8b75c47532d3e428f20638b5e47.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-1/57698c835e530fdd1d4dbadbbfca982ac8add8b75c47532d3e428f20638b5e47.jsonl); 11 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c0abe074ea35703e41ec2a63d4cf981e4b2befd7a0337397bdfe4077ea30766d`.

## RAN1_P2_CQ1-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The explicit agenda defines retrieval scope; domain judgment that every entry is about UL switching is not certified.']

**Original question:** What was agreed on UL Tx switching (Agenda 5.1) at meeting RAN1#100? (UL switching decisions)

**Revised question:** Return all distinct agreement-identifier/content pairs at RAN1#100 under recorded agenda number 5.1.

**Proposed rationale:** The explicit agenda defines retrieval scope; domain judgment that every entry is about UL switching is not certified.

**Original query**

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '5.1'}), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#100'}) RETURN DISTINCT a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-2/46b82421c0d9bafcbe27fba4a012b2291cf2cc2d7a3154085645f67150d1c5d9.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-2/46b82421c0d9bafcbe27fba4a012b2291cf2cc2d7a3154085645f67150d1c5d9.jsonl); 6 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `25454dc3423505b4a65b32c4c4a3fd7fcb365cb49368f18ab776ee6f51f092f5`.

## RAN1_P2_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions reached at the latest meeting, RAN1#121 (status of open issues).

**Revised question:** List all distinct conclusion-identifier/content pairs recorded at RAN1#121.

**Proposed rationale:** Fixed meeting scope is preserved without claiming it is globally latest; remove cap.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence, c.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN DISTINCT c.resolutionId, c.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.resolutionId",
      "nullable": true,
      "source_column_or_expression": "c.resolutionId",
      "type": "string"
    },
    {
      "name": "c.content",
      "nullable": true,
      "source_column_or_expression": "c.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-3/0cb02d340f81c369c98e081a754847c42cfbee667f5f579fd076192dc086522b.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-3/0cb02d340f81c369c98e081a754847c42cfbee667f5f579fd076192dc086522b.jsonl); 64 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `95aeae61ae929ff47a478fc20b82e499b637c22f29d7d758c288e71bd156efbc`.

## RAN1_P2_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the working assumptions from meeting RAN1#115 (items that may be revisited).

**Revised question:** List all distinct working-assumption identifier/content pairs recorded at RAN1#115.

**Proposed rationale:** Grade requested records with content; remove unasked cap.

**Original query**

```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN DISTINCT wa.resolutionId, wa.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "wa.resolutionId",
      "nullable": true,
      "source_column_or_expression": "wa.resolutionId",
      "type": "string"
    },
    {
      "name": "wa.content",
      "nullable": true,
      "source_column_or_expression": "wa.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-4/37befb0bb91b53a52b164e1ebaaadab3fd3c111dc6f718bd9ebad9caaa371099.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-4/37befb0bb91b53a52b164e1ebaaadab3fd3c111dc6f718bd9ebad9caaa371099.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f86b85578aaf46ed4d487e633acc74a2919813442b07000ba249c070e126883a`.

## RAN1_P2_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Recent is made explicit as a bounded meeting-order task rather than claiming a complete semantic FFS interpretation.']

**Original question:** List recent agreements carrying an FFS (Further For Study) marker (items needing further study).

**Revised question:** Return the top fifteen distinct Agreement/content/meeting records with hasFFS=true. Return Agreement identifier, content, meeting-number string and meetingNumberInt; rank the integer descending, then Agreement identifier, meeting-number string and content ascending, returning all records if fewer than fifteen exist.

**Proposed rationale:** Recent is made explicit as a bounded meeting-order task rather than claiming a complete semantic FFS interpretation. Every returned record discriminator has an observable deterministic tie key.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.hasFFS = true RETURN a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.hasFFS=true RETURN DISTINCT a.resolutionId,a.content,m.meetingNumber,m.meetingNumberInt ORDER BY m.meetingNumberInt DESC,a.resolutionId ASC,m.meetingNumber ASC,a.content ASC LIMIT 15
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    },
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "m.meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "m.meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "a.resolutionId"
      },
      {
        "direction": "asc",
        "field": "m.meetingNumber"
      },
      {
        "direction": "asc",
        "field": "a.content"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most fifteen records",
    "tie_policy": "deterministic_all_keys",
    "value": 15
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-5/ac6f01d21d082daccbfc267db0c84bf32588981e7228e3346d04b0bf7f215aa9.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-5/ac6f01d21d082daccbfc267db0c84bf32588981e7228e3346d04b0bf7f215aa9.jsonl); 15 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `69b59361ec2e79db49c93aca090129fdb451285f0031a6ecea478e687957926f`.

## RAN1_P2_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The existing keyword screen does not certify complete topic relevance. The candidate states its literal documentary scope. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on PDCCH blind decoding? (PDCCH decisions)

**Revised question:** Return all distinct Agreement identifier/content pairs whose content contains both case-sensitive literals PDCCH and blind. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** The existing keyword screen does not certify complete topic relevance. The candidate states its literal documentary scope. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PDCCH' AND a.content CONTAINS 'blind' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PDCCH' AND a.content CONTAINS 'blind' RETURN DISTINCT a.resolutionId, m.meetingNumber, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-6/2393c97fd0fc262c7fc7526f03c5352aa530de23c417adb9a80302667b2fa0c6.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-6/2393c97fd0fc262c7fc7526f03c5352aa530de23c417adb9a80302667b2fa0c6.jsonl); 47 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3c01c0b998d6e6f6a176c80650e611db7fd23f655969f59391e40e11965c18a2`.

## RAN1_P2_CQ1-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Replace unverified semantic topic coverage with explicit literal-match scope. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on beam management? (beam-management decisions)

**Revised question:** Return all distinct Agreement identifier/content pairs whose content contains the case-sensitive literal beam and at least one of management or indication. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Replace unverified semantic topic coverage with explicit literal-match scope. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'beam' AND (a.content CONTAINS 'management' OR a.content CONTAINS 'indication') RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'beam' AND (a.content CONTAINS 'management' OR a.content CONTAINS 'indication') RETURN DISTINCT a.resolutionId, m.meetingNumber, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ1-7/97e9bf98eaff5a20cc209983242d439de9b65a169bf58164fa4ce4007e83c1a0.json), [complete native rows](../reference_outputs/RAN1_P2_CQ1-7/97e9bf98eaff5a20cc209983242d439de9b65a169bf58164fa4ce4007e83c1a0.jsonl); 420 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e82b5b27bae2b7ef60178f92f3c0b04cc8090bf19227741a43c0121eb6b6a08f`.

## RAN1_P2_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs referenced by Agreement AGR-100-6.1-001 (tracing the source documents behind a decision).

**Revised question:** List every distinct TDoc identifier referenced through REFERENCES by Agreement AGR-100-6.1-001.

**Proposed rationale:** Documentary REFERENCES supplies the requested link; no causality claim is added.

**Original query**

```cypher
MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```

**Revised query**

```cypher
MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ2-1/d27a861a5f6466910ab60ba912585e280632a5e4dd28849809d3b5e639042039.json), [complete native rows](../reference_outputs/RAN1_P2_CQ2-1/d27a861a5f6466910ab60ba912585e280632a5e4dd28849809d3b5e639042039.jsonl); 4 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `07db0adb57bdd14828020b998673b553e875df97d003c98679d03d551887b956`.

## RAN1_P2_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A recorded reference does not establish that a contribution caused a decision. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** Which agreement did TDoc R1-2001110 lead to? (tracing a contribution into the standard)

**Revised question:** List all distinct Agreement identifier/content pairs that reference TDoc R1-2001110 through REFERENCES. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** A recorded reference does not establish that a contribution caused a decision. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R1-2001110'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R1-2001110'}), (a)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber, a.resolutionId, a.content, m.meetingNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ2-2/756b5d8812a3e969a5c38847d2653305fdd2c16d9a049d2b2605e7a882ec6b96.json), [complete native rows](../reference_outputs/RAN1_P2_CQ2-2/756b5d8812a3e969a5c38847d2653305fdd2c16d9a049d2b2605e7a882ec6b96.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d260557996bfd49747b0f91229057bf8363bffd8eead11a14b36c25d91dd4402`.

## RAN1_P2_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Keyword containment is not independent CR approval verification.']

**Original question:** List the agreements at meeting RAN1#115 that approved a CR (tracing spec-change decisions).

**Revised question:** List all distinct Agreement identifier/content pairs at RAN1#115 whose content contains CR and at least one of agreed or approved, using case-sensitive literal matching.

**Proposed rationale:** Keyword containment is not independent CR approval verification.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved') RETURN a.resolutionId, a.content ORDER BY a.sequence, a.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved') RETURN DISTINCT a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ2-3/885b853e92358e6bfdb920213a27be44a5ff27010631c319f8c1cef7090e3275.json), [complete native rows](../reference_outputs/RAN1_P2_CQ2-3/885b853e92358e6bfdb920213a27be44a5ff27010631c319f8c1cef7090e3275.jsonl); 44 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0a1592d5875f0c8a15542830902fd8c5b933ad5afa3f8a3f949ab15c0b5e4bbf`.

## RAN1_P2_CQ2-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Grouping agenda strings across meetings is explicit; use distinct resolution nodes and deterministic tie break.']

**Original question:** Which agenda items carry the most resolutions? Top 10 (identifying hot topics).

**Revised question:** Among all recorded agenda-number-string groups across meetings, return the ten with the greatest distinct Resolution-node counts, including zero-count groups. Return agenda number and count; rank count descending then agenda-number string ascending, returning all available groups if fewer than ten exist.

**Proposed rationale:** Grouping agenda strings across meetings is explicit; use distinct resolution nodes and deterministic tie break. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) RETURN ai.agendaNumber,count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC,ai.agendaNumber ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ai.agendaNumber",
      "nullable": true,
      "source_column_or_expression": "ai.agendaNumber",
      "type": "string"
    },
    {
      "name": "resolutionCount",
      "nullable": false,
      "source_column_or_expression": "resolutionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "resolutionCount"
      },
      {
        "direction": "asc",
        "field": "ai.agendaNumber"
      }
    ],
    "tie_policy": "agenda number lexicographically ascending; no extra boundary ties"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.",
    "short_population": "all_available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ2-4/dde5b73d1060b0ddd2df101af3003df1851d7c28117876f0ad30fa68cb3c8cae.json), [complete native rows](../reference_outputs/RAN1_P2_CQ2-4/dde5b73d1060b0ddd2df101af3003df1851d7c28117876f0ad30fa68cb3c8cae.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `027f76946d3275392ae971beba0cc60f4e9c64caf4a20912807849acd48f0d33`.

## RAN1_P2_CQ2-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original query includes Agreement records only and literal spec-number mentions; it does not demonstrate all resolutions or actual modifications. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the resolutions related to changes to TS 38.211 (revision history of 38.211).

**Revised question:** List all distinct Agreement identifier/content pairs whose content contains the case-sensitive literal 38.211. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Original query includes Agreement records only and literal spec-number mentions; it does not demonstrate all resolutions or actual modifications. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS '38.211' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS '38.211' RETURN DISTINCT a.resolutionId, m.meetingNumber, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ2-5/728a40e248fe5098df177ad4fcfd08d26c7ccf76634f967cccd9f8668198bbb0.json), [complete native rows](../reference_outputs/RAN1_P2_CQ2-5/728a40e248fe5098df177ad4fcfd08d26c7ccf76634f967cccd9f8668198bbb0.jsonl); 488 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d4de4a09e7f8701dffebacbf43ab96b9f500234cb57587984a90d62ca69c58d0`.

## RAN1_P2_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Documentary references replace the causal led-to claim; no hidden cap. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List Huawei's TDocs that led to an agreement (tracing a company's contributions to the standard).

**Revised question:** List all distinct Huawei-submitted TDoc/Agreement identifier pairs linked by REFERENCES. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Documentary references replace the causal led-to claim; no hidden cap. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, a.resolutionId, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber, a.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (a)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber, t.title, a.resolutionId, m.meetingNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ3-1/36d32369895592f96d0ac459be2bbd1e1e291a36214d0e471dbcc6abb3ec24a2.json), [complete native rows](../reference_outputs/RAN1_P2_CQ3-1/36d32369895592f96d0ac459be2bbd1e1e291a36214d0e471dbcc6abb3ec24a2.jsonl); 2,483 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `beaef199c8401ff234d5462ae621e5fde782924dfd17d6a99238ed8cce7a7808`.

## RAN1_P2_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Correct the original Agreement-node numerator to distinct TDocs and define zero-total behavior. REFERENCES is documentary, not proof of fed-into causality.']

**Original question:** How many of Samsung's TDocs fed into agreements, and what share? (contribution performance)

**Revised question:** For Samsung-submitted TDocs, return the total distinct document count, the distinct document count referenced by at least one Agreement, and the latter count as a percentage of total rounded to one decimal place; return null percentage when total is zero.

**Proposed rationale:** Correct the original Agreement-node numerator to distinct TDocs and define zero-total behavior. REFERENCES is documentary, not proof of fed-into causality.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH c, count(t) AS totalTdocs OPTIONAL MATCH (a:Agreement)-[:REFERENCES]->(t2:Tdoc)-[:SUBMITTED_BY]->(c) WITH c, totalTdocs, count(DISTINCT a) AS agreementCount RETURN c.companyName, totalTdocs, agreementCount, round(100.0 * agreementCount / totalTdocs, 1) AS contributionRate
```

**Revised query**

```cypher
MATCH (c:Company {companyName:'Samsung'}) OPTIONAL MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c) WITH c,count(DISTINCT t) AS totalTdocs OPTIONAL MATCH (a:Agreement)-[:REFERENCES]->(t2:Tdoc)-[:SUBMITTED_BY]->(c) WITH totalTdocs,count(DISTINCT t2) AS referencedTdocCount RETURN totalTdocs,referencedTdocCount,CASE WHEN totalTdocs=0 THEN null ELSE round(100.0*referencedTdocCount/totalTdocs,1) END AS contributionRate
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "totalTdocs",
      "nullable": false,
      "source_column_or_expression": "totalTdocs",
      "type": "integer"
    },
    {
      "name": "referencedTdocCount",
      "nullable": false,
      "source_column_or_expression": "referencedTdocCount",
      "type": "integer"
    },
    {
      "name": "contributionRate",
      "nullable": true,
      "source_column_or_expression": "contributionRate",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one aggregate record if the named Company exists",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ3-2/8335f61d13ac479bdad12f1f4dca348c413f4fcb182423f7502662b49be95840.json), [complete native rows](../reference_outputs/RAN1_P2_CQ3-2/8335f61d13ac479bdad12f1f4dca348c413f4fcb182423f7502662b49be95840.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `3bbf3c442470a9cc1eba88e7ef76a0e5d45394a0534a0b7058a57e267c03ef00`.

## RAN1_P2_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Define documentary contribution count unit as agreements, not influence or causality; enforce prefix and deterministic tie.']

**Original question:** Which companies contributed most to resolutions under NR MIMO (Agenda 7.1)? Top 10.

**Revised question:** Among all recorded company-name groups, return the ten with the greatest numbers of distinct Agreement nodes under agenda number 7.1 or its 7.1. descendants that reference a company-submitted TDoc, including zero-count groups. Return company/count pairs; rank count descending then company name ascending, returning all available groups if fewer than ten exist. This counts recorded documentary associations.

**Proposed rationale:** Define documentary contribution count unit as agreements, not influence or causality; enforce prefix and deterministic tie. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN c.companyName, count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company) OPTIONAL MATCH (a:Agreement)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(c), (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber='7.1' OR ai.agendaNumber STARTS WITH '7.1.' RETURN c.companyName,count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC,c.companyName ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.companyName",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
      "type": "string"
    },
    {
      "name": "contributionCount",
      "nullable": false,
      "source_column_or_expression": "contributionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "contributionCount"
      },
      {
        "direction": "asc",
        "field": "c.companyName"
      }
    ],
    "tie_policy": "company-name ascending; at most ten entries"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.",
    "short_population": "all_available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ3-3/f10ccd817f3f61a6ee7f47f783ea1e521adbf170f06ec6c8b21b3e1a3a4ae6fa.json), [complete native rows](../reference_outputs/RAN1_P2_CQ3-3/f10ccd817f3f61a6ee7f47f783ea1e521adbf170f06ec6c8b21b3e1a3a4ae6fa.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f5475ab4eba6720dba8e4eb9023289b1ccc00a06919f38cc1ec78d2824b24ec0`.

## RAN1_P2_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Qualcomm's 10 most recent agreements.

**Revised question:** Return at most ten distinct Agreement nodes that reference Qualcomm-submitted TDocs, with identifier, content and greatest linked meetingNumberInt. Order by that meeting number descending then agreement identifier ascending. Break any remaining tie by returned content ascending.

**Proposed rationale:** The original query limits TDoc-agreement join rows rather than ten agreements; aggregate by Agreement before limiting and expose the actual meeting-based recency definition. Include the already requested content as a final observable tie key.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Qualcomm'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Qualcomm'}), (a)-[:MADE_AT]->(m:Meeting) WITH a,max(m.meetingNumberInt) AS latestMeetingNumberInt RETURN a.resolutionId,a.content,latestMeetingNumberInt ORDER BY latestMeetingNumberInt DESC,a.resolutionId ASC,a.content ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    },
    {
      "name": "latestMeetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "latestMeetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "latestMeetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "a.resolutionId"
      },
      {
        "direction": "asc",
        "field": "a.content"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most ten distinct Agreement nodes",
    "tie_policy": "deterministic_all_keys",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ3-4/eb0dbbc713bd4ad17f0e0506aebeb8ad53ce9f81fa7ea4625434abdb5b72cfdd.json), [complete native rows](../reference_outputs/RAN1_P2_CQ3-4/eb0dbbc713bd4ad17f0e0506aebeb8ad53ce9f81fa7ea4625434abdb5b72cfdd.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `f1e95b6bdd742084067d109fc7c20e02e98aa0acd4a9de1741421b3cc0b602bc`.

## RAN1_P2_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which of ZTE's TDocs were approved? (approval track record)

**Revised question:** List all distinct ZTE-submitted TDoc identifiers with recorded status approved.

**Proposed rationale:** Preserve explicit recorded status and company; remove unasked cap.

**Original query**

```cypher
MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN DISTINCT t.tdocNumber, t.title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ3-6/0d126a6f371d1d4046b3d0feaf8e73d3ea487a32c1129490a8e0e5a06d79c390.json), [complete native rows](../reference_outputs/RAN1_P2_CQ3-6/0d126a6f371d1d4046b3d0feaf8e73d3ea487a32c1129490a8e0e5a06d79c390.jsonl); 70 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f17b33cffebad1ba04a505e6933a4d55d46d10a59dc1fdc1ff208c0b209260c9`.

## RAN1_P2_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Recorded moderation/FL metadata is not independent technical leadership validation. Count documents and state deterministic tie policy.']

**Original question:** Which companies led the most FL summaries under Agenda Item 7.1 (NR MIMO)? Top 5 (technical leadership).

**Revised question:** Return the five companies linked by MODERATED_BY to the most distinct TDocs with summaryType FL under agenda number 7.1 or its 7.1. descendants; return company/count pairs, sorted count descending then company name ascending.

**Proposed rationale:** Recorded moderation/FL metadata is not independent technical leadership validation. Count documents and state deterministic tie policy.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company)
WHERE ai.agendaNumber STARTS WITH '7.1' AND t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 5
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company)
WHERE (ai.agendaNumber='7.1' OR ai.agendaNumber STARTS WITH '7.1.') AND t.summaryType = 'FL'
RETURN c.companyName, count(DISTINCT t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.companyName",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
      "type": "string"
    },
    {
      "name": "flCount",
      "nullable": false,
      "source_column_or_expression": "flCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "flCount"
      },
      {
        "direction": "asc",
        "field": "c.companyName"
      }
    ],
    "tie_policy": "company name ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most five companies",
    "tie_policy": "company name ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ4-1/fdb2614b59c12ebb1641a1981fd7510f32375c9e4c679e796e630078e774bd42.json), [complete native rows](../reference_outputs/RAN1_P2_CQ4-1/fdb2614b59c12ebb1641a1981fd7510f32375c9e4c679e796e630078e774bd42.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `088c0e608ea00c1630919bf2c946a38a5ee023d9345c035f11a212b0d9bb5d3c`.

## RAN1_P2_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Literal FL/moderation scope supplies recorded evidence only; remove unasked top15 cap.']

**Original question:** List the agenda items where Huawei served as Feature Lead on the FL summary (areas it leads).

**Revised question:** List all distinct agenda-number strings attached to FL-summary TDocs that are linked by MODERATED_BY to Huawei.

**Proposed rationale:** Literal FL/moderation scope supplies recorded evidence only; remove unasked top15 cap.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company {companyName: 'Huawei'})
WHERE t.summaryType = 'FL'
RETURN DISTINCT ai.agendaNumber, count(t) AS flCount ORDER BY flCount DESC, ai.agendaNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company {companyName: 'Huawei'})
WHERE t.summaryType = 'FL'
RETURN DISTINCT ai.agendaNumber, count(DISTINCT t) AS flCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ai.agendaNumber",
      "nullable": true,
      "source_column_or_expression": "ai.agendaNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ4-2/398fc8b4dcc3e1f3a852656de118207e89ba25dd346c660dc095d90c5d1dc976.json), [complete native rows](../reference_outputs/RAN1_P2_CQ4-2/398fc8b4dcc3e1f3a852656de118207e89ba25dd346c660dc095d90c5d1dc976.jsonl); 37 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `838c574770c81d24b78d709ba9fa046043696b55ff74e7ad0a91e391f53000d8`.

## RAN1_P2_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which companies handled the most FL summaries? Top 10 (technical-leadership ranking).

**Revised question:** Return the ten companies linked by MODERATED_BY to the most distinct FL-summary TDocs, with counts, sorted count descending then company name ascending.

**Proposed rationale:** Count distinct document nodes and define recorded metadata as task scope.

**Original query**

```cypher
MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(DISTINCT t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.companyName",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
      "type": "string"
    },
    {
      "name": "flCount",
      "nullable": false,
      "source_column_or_expression": "flCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "flCount"
      },
      {
        "direction": "asc",
        "field": "c.companyName"
      }
    ],
    "tie_policy": "company name ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most ten companies",
    "tie_policy": "company name ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ4-3/56b59cde7638c0a20c09981827c132c18242c1198efa7da9910377ba2c435454.json), [complete native rows](../reference_outputs/RAN1_P2_CQ4-3/56b59cde7638c0a20c09981827c132c18242c1198efa7da9910377ba2c435454.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4db276d19cf83b1821bd76f305482584b33a07f01eb9f3b338baaf18e06d5c7a`.

## RAN1_P2_CQ5-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Text mentions supply an ordered documentary history; they do not establish technical evolution by themselves. Remove unasked cap and break meeting ties.']

**Original question:** Trace how agreements on CSI-RS evolved over time (CSI-RS technical evolution).

**Revised question:** List all distinct meeting/Agreement/content triples containing the case-sensitive literal CSI-RS, ordered by meetingNumberInt ascending and agreement identifier ascending. Also return the numeric meetingNumberInt used for ordering.

**Proposed rationale:** Text mentions supply an ordered documentary history; they do not establish technical evolution by themselves. Remove unasked cap and break meeting ties.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'CSI-RS' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt ASC LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'CSI-RS' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content, m.meetingNumberInt ORDER BY m.meetingNumberInt ASC, a.resolutionId ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    },
    {
      "name": "m.meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "m.meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "a.resolutionId"
      }
    ],
    "tie_policy": "resolution identifier ascending"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching documentary records"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-1/0b84d75462e6aa462e303f8de477a4f600745d79ab3b8a1cb3415801242b8d69.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-1/0b84d75462e6aa462e303f8de477a4f600745d79ab3b8a1cb3415801242b8d69.jsonl); 1,423 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `26f1ca40039c588af3bc2e9a5e0954ae67a3c14b421707724e38946c60f8adc5`.

## RAN1_P2_CQ5-10

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on UCI multiplexing?

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals UCI and multiplex. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'UCI' AND a.content CONTAINS 'multiplex' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'UCI' AND a.content CONTAINS 'multiplex' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-10/46826133293c3216ad492d0abb93548b159103b96884ff96a100528ce471d97a.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-10/46826133293c3216ad492d0abb93548b159103b96884ff96a100528ce471d97a.jsonl); 182 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3c2aaabdfc5991d493dafa000e99ae99e310fd0cde1fa6c82be1b3b8c85d62e9`.

## RAN1_P2_CQ5-11

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on DMRS patterns (DMRS pattern decisions).

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals DMRS and pattern. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DMRS' AND a.content CONTAINS 'pattern' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DMRS' AND a.content CONTAINS 'pattern' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-11/8062c1b5836facadc7ad49bee5d88a56dd246bdf36bfd08369a38be4c5592d51.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-11/8062c1b5836facadc7ad49bee5d88a56dd246bdf36bfd08369a38be4c5592d51.jsonl); 110 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `20895481f77a297c29ae87fb8848978d43d8dbcb1aeccb853b916be0491c840c`.

## RAN1_P2_CQ5-12

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on the SSB burst set?

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals SSB and burst. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'burst' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'burst' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-12/1bea88a0f4468e99795e1d4bf0cb373ebb8974a738ee522fd2dd830ade37f8c2.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-12/1bea88a0f4468e99795e1d4bf0cb373ebb8974a738ee522fd2dd830ade37f8c2.jsonl); 55 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `2698e4cf5f10018939963326f002f5733780e41e0b37b06c8a81d17c15c76ad4`.

## RAN1_P2_CQ5-13

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on PUCCH resources.

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals PUCCH and resource. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUCCH' AND a.content CONTAINS 'resource' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUCCH' AND a.content CONTAINS 'resource' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-13/c94e1f8471d180a8d3f40cd7d504b03e00e7feda5f4b0fdb3f492d9ece26a382.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-13/c94e1f8471d180a8d3f40cd7d504b03e00e7feda5f4b0fdb3f492d9ece26a382.jsonl); 570 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3702e5087982f88bd5ce038f6fa98964e06f505f0ded3bc4666150ee3af5af2d`.

## RAN1_P2_CQ5-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on HARQ feedback (HARQ decisions).

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals HARQ and feedback. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'HARQ' AND a.content CONTAINS 'feedback' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'HARQ' AND a.content CONTAINS 'feedback' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-2/4048cf78557758dee4a3e7b684e38d7198e0a7974c97baae03ef5b51679d1324.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-2/4048cf78557758dee4a3e7b684e38d7198e0a7974c97baae03ef5b51679d1324.jsonl); 461 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `38ade04460fb9e75470af8c5500258c389701686247bafa1d746673a7101777e`.

## RAN1_P2_CQ5-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on SRS configuration (SRS configuration decisions).

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals SRS and configuration. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SRS' AND a.content CONTAINS 'configuration' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SRS' AND a.content CONTAINS 'configuration' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-3/38bc9436e3e6425f99252206ca8e6b46845e301d70607baac7a598259166b459.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-3/38bc9436e3e6425f99252206ca8e6b46845e301d70607baac7a598259166b459.jsonl); 339 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `624288733df381842c876304ef4872250e413bdfbe5569d47713505f0da28e73`.

## RAN1_P2_CQ5-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on DCI formats? (DCI format decisions)

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals DCI and format. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DCI' AND a.content CONTAINS 'format' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DCI' AND a.content CONTAINS 'format' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-4/107cf1a034941fa74cbf309429c73856e729223c49f483777aebab47eedd8ff3.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-4/107cf1a034941fa74cbf309429c73856e729223c49f483777aebab47eedd8ff3.jsonl); 1,530 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0c4ca779e33f50ce424203d271be004e4ebfe6a7b317e756ee19ea5154a477b4`.

## RAN1_P2_CQ5-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on PUSCH repetition? (PUSCH repetition decisions)

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals PUSCH and repetition. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'repetition' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'repetition' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-5/b20709fd4b0d3a8deeaddb6114294e71b8e5e68e4a2c44d8d99452f68e5238eb.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-5/b20709fd4b0d3a8deeaddb6114294e71b8e5e68e4a2c44d8d99452f68e5238eb.jsonl); 532 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b37a2628d51b4dadc969a390ee997dd617466bf1bb878d9770567949b5e7959b`.

## RAN1_P2_CQ5-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How did the number of agreements per meeting trend from RAN1#100 to RAN1#121?

**Revised question:** For every recorded Meeting with meetingNumberInt from 100 through 121, return its meeting number and count of distinct linked Agreements, including zero-agreement meetings; order by integer meeting number ascending. Also return the numeric meetingNumberInt used for ordering.

**Proposed rationale:** The original inner match omits zero counts and string sorting does not define temporal order. Use Meeting as population and an optional Agreement link.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumber IN ['RAN1#100', 'RAN1#101', 'RAN1#102', 'RAN1#103', 'RAN1#104', 'RAN1#105', 'RAN1#106', 'RAN1#107', 'RAN1#108', 'RAN1#109', 'RAN1#110', 'RAN1#111', 'RAN1#112', 'RAN1#113', 'RAN1#114', 'RAN1#115', 'RAN1#116', 'RAN1#117', 'RAN1#118', 'RAN1#119', 'RAN1#120', 'RAN1#121'] RETURN m.meetingNumber, count(a) AS agreementCount ORDER BY m.meetingNumber
```

**Revised query**

```cypher
MATCH (m:Meeting) WHERE m.meetingNumberInt >= 100 AND m.meetingNumberInt <= 121 OPTIONAL MATCH (a:Agreement)-[:MADE_AT]->(m) RETURN m.meetingNumber,m.meetingNumberInt,count(DISTINCT a) AS agreementCount ORDER BY m.meetingNumberInt ASC,m.meetingNumber ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "agreementCount",
      "nullable": false,
      "source_column_or_expression": "agreementCount",
      "type": "integer"
    },
    {
      "name": "m.meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "m.meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "m.meetingNumber"
      }
    ],
    "tie_policy": "meeting-number string ascending"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "exactly one record per qualifying recorded meeting; all such meetings are returned"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-6/3f95b1deb8e004eddd9109ab33731f98f9a7bf9b03d4dc12365323f7c005466e.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-6/3f95b1deb8e004eddd9109ab33731f98f9a7bf9b03d4dc12365323f7c005466e.jsonl); 33 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `c9d78ca04a8be15c98557064956f0d897842cbbd157e0256113ee4370816dd3b`.

## RAN1_P2_CQ5-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on MIMO codebooks.

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals MIMO and codebook. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'MIMO' AND a.content CONTAINS 'codebook' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'MIMO' AND a.content CONTAINS 'codebook' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-7/27e7b5fc31a8e45e8495ff1fc5e2bf1f8b5a7b4ef97e20c452c2bcc5585756d2.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-7/27e7b5fc31a8e45e8495ff1fc5e2bf1f8b5a7b4ef97e20c452c2bcc5585756d2.jsonl); 75 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `9fc7e55f095f334c8bb38b8409afb0faecac5b2fcf88e5b87627e05ef0aa97d8`.

## RAN1_P2_CQ5-8

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** What was agreed on BWP switching?

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals BWP and switch. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'BWP' AND a.content CONTAINS 'switch' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'BWP' AND a.content CONTAINS 'switch' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-8/9884718d2f1fd342f630982cd0ca460a0f4a8f1796d0f574213e53b08742d021.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-8/9884718d2f1fd342f630982cd0ca460a0f4a8f1796d0f574213e53b08742d021.jsonl); 170 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ded4beb06df2d29178d6af3fba8312f27a2c1de40d3b6db44e7982ac12471348`.

## RAN1_P2_CQ5-9

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** List the agreements on slot aggregation.

**Revised question:** Return all distinct Agreement identifier/content pairs containing both case-sensitive literals slot and aggregation. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** An explicit lexical retrieval task is proposed; source keywords alone do not prove complete semantic topic coverage. This is marked as a substantive task variant. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'slot' AND a.content CONTAINS 'aggregation' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'slot' AND a.content CONTAINS 'aggregation' RETURN DISTINCT m.meetingNumber, a.resolutionId, a.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "a.resolutionId",
      "nullable": true,
      "source_column_or_expression": "a.resolutionId",
      "type": "string"
    },
    {
      "name": "a.content",
      "nullable": true,
      "source_column_or_expression": "a.content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P2_CQ5-9/eaa0edcbbc732f4fbee62bc6d53c65336a86607a2e31cbdd5ac2532516b6212c.json), [complete native rows](../reference_outputs/RAN1_P2_CQ5-9/eaa0edcbbc732f4fbee62bc6d53c65336a86607a2e31cbdd5ac2532516b6212c.jsonl); 80 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `2df48cc43e4e3ea58135053075b02ccce43ca36002bedc39a01027eda929c6f8`.

## RAN1_P3_CQ001

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Expose all recorded version identities rather than silently conflating structural snapshots; direct HAS_SECTION defines top-level scope.']

**Original question:** Return the top-level table of contents of TS 38.214 (locating DL-scheduling content).

**Revised question:** For each recorded Spec version numbered 38.214, return release, version, and section-number/title pairs of its directly linked HAS_SECTION nodes.

**Proposed rationale:** Expose all recorded version identities rather than silently conflating structural snapshots; direct HAS_SECTION defines top-level scope.

**Original query**

```cypher
MATCH (sp:Spec {specNumber: '38.214'})-[:HAS_SECTION]->(sec:Section) RETURN sec.sectionNumber, sec.sectionTitle ORDER BY sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sp:Spec {specNumber:'38.214'})-[:HAS_SECTION]->(sec:Section) RETURN DISTINCT sp.specRelease,sp.specVersion,sec.sectionNumber,sec.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sec.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "sec.sectionNumber",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    },
    {
      "name": "specRelease",
      "nullable": true,
      "source_column_or_expression": "sp.specRelease",
      "type": "string"
    },
    {
      "name": "specVersion",
      "nullable": true,
      "source_column_or_expression": "sp.specVersion",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ001/a35063cffc73959da02bfc4042987ff18d1c08cf118f36d6fddcbba41818a52e.json), [complete native rows](../reference_outputs/RAN1_P3_CQ001/a35063cffc73959da02bfc4042987ff18d1c08cf118f36d6fddcbba41818a52e.jsonl); 46 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `8d2f6cb4f7bd5a4e9780215d1028dc01316894daa4de6a6f15cc9dba19441379`.

## RAN1_P3_CQ002

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Remove arbitrary highest-release LIMIT1 and preserve graph node identity across versions. Explicit all-version scope requires author review.']

**Original question:** Show the sub-structure under TS 38.214 Section 5.1 (implementing PDSCH procedures).

**Revised question:** Across all recorded versions of TS 38.214 Section 5.1, list every distinct source-section/direct-subsection identifier pair, with subsection number and title.

**Proposed rationale:** Remove arbitrary highest-release LIMIT1 and preserve graph node identity across versions. Explicit all-version scope requires author review.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(root:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH root, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (root)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sub.sectionNumber, sub.sectionTitle ORDER BY sub.sectionNumber
```

**Revised query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(root:Section {sectionNumber:'5.1'}) MATCH (root)-[:HAS_SUB_SECTION]->(sub:Section) RETURN DISTINCT root.sectionId,sub.sectionId,sub.sectionNumber,sub.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "root.sectionId",
      "type": "string"
    },
    {
      "name": "subSectionId",
      "nullable": true,
      "source_column_or_expression": "sub.sectionId",
      "type": "string"
    },
    {
      "name": "sub.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "sub.sectionNumber",
      "type": "string"
    },
    {
      "name": "sub.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sub.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ002/28d239a7c05a01ab226e47b6e77d45eed9a56f37991d41d3ecaef6d47c99b019.json), [complete native rows](../reference_outputs/RAN1_P3_CQ002/28d239a7c05a01ab226e47b6e77d45eed9a56f37991d41d3ecaef6d47c99b019.jsonl); 35 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `2fe0c6177a14ad4bee1a9d4da142753a4cdd51306487f3c79497a1d640f7b15d`.

## RAN1_P3_CQ003

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original single edition/branch remains unspecified; paths requiring more than ten edges are outside this explicit variant.']

**Explicit additional inputs (retained provenance)**

```json
[
  {
    "name": "maximum_parent_edges",
    "origin": "visible new benchmark path bound",
    "value": 10
  },
  {
    "name": "edition_scope",
    "origin": "visible replacement for unspecified original edition",
    "value": "all recorded versions"
  }
]
```

**Original question:** Show the breadcrumb path to TS 38.214 Section 5.1.3.2 (locating a section in the hierarchy).

**Revised question:** Across all recorded versions of specification number 38.214, return every root-to-target breadcrumb path for sections numbered 5.1.3.2 that reaches a root within at most ten PARENT_SECTION edges. A root has no outgoing PARENT_SECTION link. Return target Section identifier and an ordered root-to-target array of identifier/number/title records for each path.

**Proposed rationale:** The original singular breadcrumb has no edition, branch, or depth definition. This explicit all-version, all-root-path variant retains the existing ten-edge bound as a named limit and grades the whole ordered path; it does not certify deeper or unspecified edition paths.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(target:Section {sectionNumber:'5.1.3.2'}) WHERE rk.specRelease IS NOT NULL WITH target, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH path = (target)-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT (root)-[:PARENT_SECTION]->(:Section) UNWIND nodes(path) AS n RETURN n.sectionNumber, n.sectionTitle ORDER BY n.level
```

**Revised query**

```cypher
MATCH (target:Section {sectionNumber:'5.1.3.2'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.214'}) WITH DISTINCT target MATCH p=(target)-[:PARENT_SECTION*0..10]->(root:Section) WHERE NOT EXISTS { MATCH (root)-[:PARENT_SECTION]->(:Section) } RETURN DISTINCT target.sectionId AS targetSectionId,[n IN reverse(nodes(p)) | {id:n.sectionId,number:n.sectionNumber,title:n.sectionTitle}] AS breadcrumb
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "targetSectionId",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "additionalProperties": false,
          "properties": {
            "id": {
              "type": [
                "string",
                "null"
              ]
            },
            "number": {
              "type": [
                "string",
                "null"
              ]
            },
            "title": {
              "type": [
                "string",
                "null"
              ]
            }
          },
          "required": [
            "id",
            "number",
            "title"
          ],
          "type": "object"
        },
        "type": "array"
      },
      "name": "breadcrumb",
      "nested_array_semantics": {
        "$": "sequence"
      },
      "nested_collection_definition": {
        "element_type": "object",
        "fields": [
          {
            "name": "id",
            "nullable": true,
            "type": "string"
          },
          {
            "name": "number",
            "nullable": true,
            "type": "string"
          },
          {
            "name": "title",
            "nullable": true,
            "type": "string"
          }
        ],
        "kind": "sequence",
        "order": "root-to-target traversal order"
      },
      "nullable": false,
      "source_column_or_expression": "breadcrumb",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ003/6427895dd8420df0276169a74f3f73fc8322e194a77de8acfd747857615fdb6f.json), [complete native rows](../reference_outputs/RAN1_P3_CQ003/6427895dd8420df0276169a74f3f73fc8322e194a77de8acfd747857615fdb6f.jsonl); 5 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `23e6c31fd4819a41845789d6094087b133841bba5dd0d9f2c88a65464752ad58`.

## RAN1_P3_CQ004

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Define version scope and count node identities rather than duplicate join bindings.']

**Original question:** Return the section count per level in TS 38.213 (gauging structural depth and complexity).

**Revised question:** For TS 38.213 across all recorded Spec versions, return each recorded section level and the count of distinct Section nodes at that level.

**Proposed rationale:** Define version scope and count node identities rather than duplicate join bindings.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(DISTINCT sec) AS sectionCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sec.level",
      "nullable": true,
      "source_column_or_expression": "sec.level",
      "type": "integer"
    },
    {
      "name": "sectionCount",
      "nullable": false,
      "source_column_or_expression": "sectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ004/0a160c982e84156260375fdf37cf700064c5dc32467690adfdc4ca4afb27a56d.json), [complete native rows](../reference_outputs/RAN1_P3_CQ004/0a160c982e84156260375fdf37cf700064c5dc32467690adfdc4ca4afb27a56d.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `2a0cadcddcfa2480542c94d6469ae46a3f5a86419a33a92bbadfab676ac4186a`.

## RAN1_P3_CQ005

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Most requires a maximum, not an arbitrary top15 cap; explicit all-version Section identity and all-ties policy avoid cross-version ambiguity.']

**Original question:** Which sections of TS 38.213 contain the most tables? (finding parameter-dense implementation points)

**Revised question:** Return every Section node belonging to TS 38.213 that has the maximum number of distinct CONTAINS_TABLE-linked TSTable nodes, with section identifier, number and count. Include every tie; zero-table sections participate with count zero.

**Proposed rationale:** Most requires a maximum, not an arbitrary top15 cap; explicit all-version Section identity and all-ties policy avoid cross-version ambiguity.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sec.sectionNumber, sec.sectionTitle, count(tbl) AS tableCount ORDER BY tableCount DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.213'}) WITH DISTINCT sec OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec,count(DISTINCT tbl) AS tableCount WITH collect({sec:sec,n:tableCount}) AS grouped,max(tableCount) AS maxCount UNWIND grouped AS g WITH g,maxCount WHERE g.n=maxCount RETURN g.sec.sectionId AS sectionId,g.sec.sectionNumber AS sectionNumber,g.n AS tableCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "sectionNumber",
      "nullable": true,
      "source_column_or_expression": "sectionNumber",
      "type": "string"
    },
    {
      "name": "tableCount",
      "nullable": false,
      "source_column_or_expression": "tableCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all sections tied for maximum distinct table count"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ005/44bb90db8583507f882a015bd8a5a3820f7f0b398777758850ddfef5f589799e.json), [complete native rows](../reference_outputs/RAN1_P3_CQ005/44bb90db8583507f882a015bd8a5a3820f7f0b398777758850ddfef5f589799e.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `efdeaa961952aa08518a0f8946e34c712f2acca18168f95497ea50a45b4901fc`.

## RAN1_P3_CQ006

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all tables defined in TS 38.214 (parameter tables to reference during implementation).

**Revised question:** List all distinct table-node/section-node identifier pairs linked by TABLE_IN_SECTION and BELONGS_TO_SPEC to TS 38.214, with table number and caption.

**Proposed rationale:** Table numbers repeat across versions; preserve graph node identities for a complete unambiguous table inventory.

**Original query**

```cypher
MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.214'}) RETURN tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY tbl.tableNumber
```

**Revised query**

```cypher
MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.214'}) RETURN DISTINCT tbl.tableId,tbl.tableNumber,tbl.tableCaption,sec.sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tableId",
      "nullable": true,
      "source_column_or_expression": "tbl.tableId",
      "type": "string"
    },
    {
      "name": "tbl.tableNumber",
      "nullable": true,
      "source_column_or_expression": "tbl.tableNumber",
      "type": "string"
    },
    {
      "name": "tbl.tableCaption",
      "nullable": true,
      "source_column_or_expression": "tbl.tableCaption",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ006/598a3b73230b3ef68716968cf087d2f2d0528dccd9e3a194b57b971e2e79f90c.json), [complete native rows](../reference_outputs/RAN1_P3_CQ006/598a3b73230b3ef68716968cf087d2f2d0528dccd9e3a194b57b971e2e79f90c.jsonl); 548 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `49ffced21b4c2b26b568bdcfd4ca1b95f5e09f749e502ca89f62c2728a87c7d4`.

## RAN1_P3_CQ007

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find sections whose title contains 'PDSCH' across all TSs (locating PDSCH content).

**Revised question:** List all distinct Spec-number/Section-identifier/number/title records whose section title contains PDSCH case-insensitively.

**Proposed rationale:** Section node identity distinguishes recorded versions; case-insensitive literal title matching is explicit.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN DISTINCT sp.specNumber,sec.sectionId,sec.sectionNumber,sec.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "sec.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "sec.sectionNumber",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ007/b80adfc4248baed71fa19df41e4369bcf4f575ec851ed50c2ad38af3a708d945.json), [complete native rows](../reference_outputs/RAN1_P3_CQ007/b80adfc4248baed71fa19df41e4369bcf4f575ec851ed50c2ad38af3a708d945.jsonl); 57 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `1453052a2fd093b76625d44dc2613439e09f783c34907b8db21f54e1285bbb62`.

## RAN1_P3_CQ008

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original refers to eight TSs without naming the eight-number input; this revised task covers recorded TS numbers with Sections and does not certify that original selection or conceptual complexity.']

**Original question:** Compare the eight TSs by section, table, and figure counts (which spec is most complex).

**Revised question:** For each recorded TS number with Section nodes, return counts of distinct Section, TSTable and TSFigure nodes linked to that number across all recorded versions.

**Proposed rationale:** Grade each requested count; node counts do not independently measure conceptual complexity. Explicit version grouping and distinct node counts avoid join inflation.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp2.specNumber = ts WITH ts, secCnt, count(DISTINCT tbl) AS tblCnt OPTIONAL MATCH (fig:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp3:Spec) WHERE sp3.specNumber = ts RETURN ts, secCnt, tblCnt, count(DISTINCT fig) AS figCnt ORDER BY secCnt DESC
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(DISTINCT sec) AS secCnt OPTIONAL MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp2.specNumber = ts WITH ts, secCnt, count(DISTINCT tbl) AS tblCnt OPTIONAL MATCH (fig:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp3:Spec) WHERE sp3.specNumber = ts RETURN ts, secCnt, tblCnt, count(DISTINCT fig) AS figCnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ts",
      "nullable": true,
      "source_column_or_expression": "ts",
      "type": "string"
    },
    {
      "name": "secCnt",
      "nullable": false,
      "source_column_or_expression": "secCnt",
      "type": "integer"
    },
    {
      "name": "tblCnt",
      "nullable": false,
      "source_column_or_expression": "tblCnt",
      "type": "integer"
    },
    {
      "name": "figCnt",
      "nullable": false,
      "source_column_or_expression": "figCnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ008/1d957bc62bd95b17af866f7fda2fac5ede58e8f44789cc1930f02d83491598d7.json), [complete native rows](../reference_outputs/RAN1_P3_CQ008/1d957bc62bd95b17af866f7fda2fac5ede58e8f44789cc1930f02d83491598d7.jsonl); 8 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `43513a42777053a9adbb394570d905d29603933232f8dc8113151437be79ad5e`.

## RAN1_P3_CQ009

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Remove arbitrary release selection; target identity must include the recorded node rather than bare section number.']

**Original question:** Which sections does TS 38.214 Section 5.1 reference? (companion reading for implementation)

**Revised question:** Across all recorded versions of TS 38.214 Section 5.1, list all distinct source/target Section identifier pairs linked by REFERENCES_SECTION, with target number and title.

**Proposed rationale:** Remove arbitrary release selection; target identity must include the recorded node rather than bare section number.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(src:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH src, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (src)-[:REFERENCES_SECTION]->(tgt:Section) RETURN tgt.sectionNumber, tgt.sectionTitle ORDER BY tgt.sectionNumber
```

**Revised query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(src:Section {sectionNumber:'5.1'}) MATCH (src)-[:REFERENCES_SECTION]->(tgt:Section) RETURN DISTINCT src.sectionId,tgt.sectionId,tgt.sectionNumber,tgt.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "src.sectionId",
      "type": "string"
    },
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "tgt.sectionId",
      "type": "string"
    },
    {
      "name": "tgt.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "tgt.sectionNumber",
      "type": "string"
    },
    {
      "name": "tgt.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "tgt.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ009/204b92d3cd112be791389c982a9cce5a2e8673e55cef75a83a7934b2472c73ad.json), [complete native rows](../reference_outputs/RAN1_P3_CQ009/204b92d3cd112be791389c982a9cce5a2e8673e55cef75a83a7934b2472c73ad.jsonl); 20 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `3f21d1f64d147262034aa63e042136dc4b96b4dd42d976360dfd015728b47b59`.

## RAN1_P3_CQ010

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Remove hidden latest-release choice and final30-row cap; preserve version identities.']

**Original question:** Which sections reference TS 38.211 Section 5.2.1 (Pseudo-random sequence)? (finding users of this base algorithm)

**Revised question:** Across all recorded versions of TS 38.211 Section 5.2.1, list every distinct target/source Section identifier pair connected by an incoming REFERENCES_SECTION edge, with source number and title.

**Proposed rationale:** Remove hidden latest-release choice and final30-row cap; preserve version identities.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.211'})<-[:BELONGS_TO_SPEC]-(tgt:Section {sectionNumber:'5.2.1'}) WHERE rk.specRelease IS NOT NULL WITH tgt, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (tgt)<-[:REFERENCES_SECTION]-(src:Section) RETURN src.sectionNumber, src.sectionTitle ORDER BY src.sectionNumber LIMIT 30
```

**Revised query**

```cypher
MATCH (rk:Spec {specNumber:'38.211'})<-[:BELONGS_TO_SPEC]-(tgt:Section {sectionNumber:'5.2.1'}) MATCH (tgt)<-[:REFERENCES_SECTION]-(src:Section) RETURN DISTINCT tgt.sectionId,src.sectionId,src.sectionNumber,src.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "tgt.sectionId",
      "type": "string"
    },
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "src.sectionId",
      "type": "string"
    },
    {
      "name": "src.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "src.sectionNumber",
      "type": "string"
    },
    {
      "name": "src.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "src.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ010/2ef8bbd6555d87494816d20050b64bfb63f1e86833abd763eb0bbca00eef7303.json), [complete native rows](../reference_outputs/RAN1_P3_CQ010/2ef8bbd6555d87494816d20050b64bfb63f1e86833abd763eb0bbca00eef7303.jsonl); 115 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `abe4ac0f0293811f9e99ea592dc54e26e3cf85090b4fc661e65c2954656e0d30`.

## RAN1_P3_CQ011

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Rank the top 15 most-referenced sections across all eight TSs (identifying core sections).

**Revised question:** Rank the top fifteen Section nodes by the count of distinct incoming REFERENCES_SECTION source nodes, across every recorded Section node; return Section identifier and count, sorting count descending then Section identifier ascending.

**Proposed rationale:** Count node-level references, not repeated join bindings, and define deterministic ties. Source identity separates Spec versions.

**Original query**

```cypher
MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refByCnt MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refByCnt ORDER BY refByCnt DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (tgt:Section) OPTIONAL MATCH (tgt)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt,count(DISTINCT src) AS refByCnt RETURN tgt.sectionId,refByCnt ORDER BY refByCnt DESC,tgt.sectionId ASC LIMIT 15
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "tgt.sectionId",
      "type": "string"
    },
    {
      "name": "refByCnt",
      "nullable": false,
      "source_column_or_expression": "refByCnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "refByCnt"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most fifteen Section nodes",
    "tie_policy": "Section identifier ascending",
    "value": 15
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ011/5799a5810e0e7474200f95374536193074e70e03400bda6ffce6d396ddce4450.json), [complete native rows](../reference_outputs/RAN1_P3_CQ011/5799a5810e0e7474200f95374536193074e70e03400bda6ffce6d396ddce4450.jsonl); 15 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a041bcda79f6aba7eace66582452b660e80b35db17412df9830fce1a6b3a69d1`.

## RAN1_P3_CQ012

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are there mutually referencing section pairs within TS 38.213? (tightly coupled procedures)

**Revised question:** Does the released graph contain two different Section nodes linked to TS 38.213 whose REFERENCES_SECTION edges run in both directions?

**Proposed rationale:** Preserve the original yes/no intent; compute a Boolean rather than grading one member of a pair list.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId STARTS WITH '38.213' AND b.sectionId STARTS WITH '38.213' AND a.sectionId < b.sectionId RETURN a.sectionNumber AS sectionA, a.sectionTitle AS titleA, b.sectionNumber AS sectionB, b.sectionTitle AS titleB ORDER BY a.sectionId, b.sectionId LIMIT 20
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.213'}),(b:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.213'}),(a)-[:REFERENCES_SECTION]->(b)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId RETURN count(DISTINCT a)>0 AS hasMutualReferences
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "hasMutualReferences",
      "nullable": false,
      "source_column_or_expression": "hasMutualReferences",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one Boolean record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ012/737e533ef0c2ab11aa79bdd31b0fa7bbfd5efc6314777a9c0f70737d8d8e017d.json), [complete native rows](../reference_outputs/RAN1_P3_CQ012/737e533ef0c2ab11aa79bdd31b0fa7bbfd5efc6314777a9c0f70737d8d8e017d.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `c7053d549c432b40e75acb3c3d7a41109f2a688d614545f4b737159be0cb8c40`.

## RAN1_P3_CQ013

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Compare cross-section reference density across the TSs (how tightly each is internally linked).

**Revised question:** For each recorded Spec-number group, return its distinct Section-node count, number of distinct directed REFERENCES_SECTION source/target node pairs internal to that Spec number, and pair-count divided by section-count rounded to two decimals; use null when the denominator is zero.

**Proposed rationale:** The original prefix filter does not restrict target to the same Spec and count(*) counts a null optional-match row. Use explicit internal pair identity and denominator.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (src:Section)-[:REFERENCES_SECTION]->(tgt:Section) WHERE src.sectionId STARTS WITH ts WITH ts, secCnt, count(*) AS refCnt RETURN ts, secCnt, refCnt, round(toFloat(refCnt) / secCnt * 100) / 100 AS refDensity ORDER BY refDensity DESC
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts,count(DISTINCT sec) AS secCnt OPTIONAL MATCH (src:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec),(src)-[:REFERENCES_SECTION]->(tgt:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp1.specNumber=ts AND sp2.specNumber=ts WITH ts,secCnt,count(DISTINCT CASE WHEN src IS NOT NULL AND tgt IS NOT NULL THEN [src,tgt] ELSE null END) AS refCnt RETURN ts,secCnt,refCnt,CASE WHEN secCnt=0 THEN null ELSE round(100.0*refCnt/secCnt)/100.0 END AS refDensity
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ts",
      "nullable": true,
      "source_column_or_expression": "ts",
      "type": "string"
    },
    {
      "name": "secCnt",
      "nullable": false,
      "source_column_or_expression": "secCnt",
      "type": "integer"
    },
    {
      "name": "refCnt",
      "nullable": false,
      "source_column_or_expression": "refCnt",
      "type": "integer"
    },
    {
      "name": "refDensity",
      "nullable": true,
      "source_column_or_expression": "refDensity",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ013/a67b945634ed767611f985989c060be5077a91ac81c72025485ab0c9379e9d39.json), [complete native rows](../reference_outputs/RAN1_P3_CQ013/a67b945634ed767611f985989c060be5077a91ac81c72025485ab0c9379e9d39.jsonl); 8 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `c206191c6ea4405aa96d69b46009d86c6847b27f47f05f2cc5ac2a4938e7630c`.

## RAN1_P3_CQ014

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find section pairs that reference each other (checking for circular dependencies).

**Revised question:** List every unordered pair of distinct Section identifiers whose REFERENCES_SECTION edges run in both directions, placing the lexicographically smaller identifier in sectionA.

**Proposed rationale:** A two-way direct reference is the supported documentary relation; it does not prove arbitrary dependency cycles. Remove cap and preserve full Section identifiers.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId MATCH (a)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (b)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + a.sectionNumber AS sectionA, sp2.specNumber + '-' + b.sectionNumber AS sectionB ORDER BY a.sectionId, b.sectionId LIMIT 20
```

**Revised query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId RETURN DISTINCT a.sectionId AS sectionA,b.sectionId AS sectionB
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionA",
      "nullable": true,
      "source_column_or_expression": "sectionA",
      "type": "string"
    },
    {
      "name": "sectionB",
      "nullable": true,
      "source_column_or_expression": "sectionB",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ014/5852f1235d9d2cf60faf1045302cd8a831011467011be8b346b3a5998af9ad6e.json), [complete native rows](../reference_outputs/RAN1_P3_CQ014/5852f1235d9d2cf60faf1045302cd8a831011467011be8b346b3a5998af9ad6e.jsonl); 188 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `488e96acf7b8e22334acaa8cc7da86983240c7e3a1f0a6e0e8c781bf59243325`.

## RAN1_P3_CQ015

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Rename the guard-rejected start variable, remove arbitrary release and row selections, and grade the target/intermediate roles rather than the original via-only key.']

**Original question:** What does TS 38.214 Section 5.1 reach two hops out via references? (2-hop dependencies)

**Revised question:** Across all recorded versions of TS 38.214 Section 5.1, return every distinct source/intermediate/target Section identifier triple reached by exactly two successive REFERENCES_SECTION edges, with target title.

**Proposed rationale:** Rename the guard-rejected start variable, remove arbitrary release and row selections, and grade the target/intermediate roles rather than the original via-only key.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(start:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH start, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (start)-[:REFERENCES_SECTION]->(mid:Section)-[:REFERENCES_SECTION]->(end:Section) MATCH (mid)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (end)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + mid.sectionNumber AS via, sp2.specNumber + '-' + end.sectionNumber AS target, end.sectionTitle LIMIT 20
```

**Revised query**

```cypher
MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(source:Section {sectionNumber:'5.1'}) MATCH (source)-[:REFERENCES_SECTION]->(mid:Section)-[:REFERENCES_SECTION]->(target:Section) RETURN DISTINCT source.sectionId,mid.sectionId,target.sectionId,target.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "source.sectionId",
      "type": "string"
    },
    {
      "name": "viaSectionId",
      "nullable": true,
      "source_column_or_expression": "mid.sectionId",
      "type": "string"
    },
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "target.sectionId",
      "type": "string"
    },
    {
      "name": "targetTitle",
      "nullable": true,
      "source_column_or_expression": "target.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ015/153a142ade760084e30907a0f698ff05cbabf1d90fc7483568964460a531edb1.json), [complete native rows](../reference_outputs/RAN1_P3_CQ015/153a142ade760084e30907a0f698ff05cbabf1d90fc7483568964460a531edb1.jsonl); 23 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `d53a80ea4e227b7f2dc287aa1955edaad39a428821f287eef8bf2895f1d837fb`.

## RAN1_P3_CQ016

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many CRs have been raised against TS 38.214? (how actively it is revised)

**Revised question:** How many distinct CR nodes are linked by MODIFIES to Spec number 38.214?

**Proposed rationale:** Explicit documentary CR-node counting unit, rather than claims about external filing completeness.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(cr) AS totalCR
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(DISTINCT cr) AS totalCR
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "totalCR",
      "nullable": false,
      "source_column_or_expression": "totalCR",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one integer aggregate record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ016/2e578c6044063209dac5fa54a1229a51f1d0b1da0e7c1c99ef4c1bc2a4652424.json), [complete native rows](../reference_outputs/RAN1_P3_CQ016/2e578c6044063209dac5fa54a1229a51f1d0b1da0e7c1c99ef4c1bc2a4652424.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `6cf1cef8ce4821a552b8671bd7cf539c6401716b2665505449e8d67277c49122`.

## RAN1_P3_CQ017

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the 20 most recent CRs modifying TS 38.213 (recent changes).

**Revised question:** Return the twenty distinct CR nodes linked by MODIFIES to TS 38.213 with greatest linked meetingNumberInt, reporting TDoc identifier and that meeting number; break ties by ascending TDoc identifier.

**Proposed rationale:** Deduplicate CR nodes before ranking; company joins previously consumed the row limit. Meeting-based recency is explicit.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN cr.tdocNumber, cr.title, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.213'}),(cr)-[:PRESENTED_AT]->(m:Meeting) WITH cr,max(m.meetingNumberInt) AS latestMeetingNumberInt RETURN cr.tdocNumber,latestMeetingNumberInt ORDER BY latestMeetingNumberInt DESC,cr.tdocNumber ASC LIMIT 20
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "cr.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "cr.tdocNumber",
      "type": "string"
    },
    {
      "name": "latestMeetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "latestMeetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "latestMeetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "cr.tdocNumber"
      }
    ],
    "tie_policy": "TDoc identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most twenty distinct CR nodes",
    "tie_policy": "TDoc identifier ascending",
    "value": 20
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ017/d599455acb096190ba54c80d3f35c09a9f8643f3b1c80db84a0d177a7fade627.json), [complete native rows](../reference_outputs/RAN1_P3_CQ017/d599455acb096190ba54c80d3f35c09a9f8643f3b1c80db84a0d177a7fade627.jsonl); 20 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e3b2f60fa0b7e045d56355c76c56d4bb0567c940c80fa9985638b0f92202e5b3`.

## RAN1_P3_CQ018

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['exact_5_1_clause_membership_requires_author_approved_clausesAffected_parser']

**Original question:** Which CRs affect TS 38.214 Section 5.1? List CRs whose affected clauses include 5.1 (impact on my implementation).

**Revised question:** List all distinct CR-identifier/clausesAffected-string pairs linked by MODIFIES to TS 38.214 whose clausesAffected literal contains 5.1.

**Proposed rationale:** Substring 5.1 can also match 15.1 or 5.10 and does not establish exact clause impact. The literal-filter variant is marked as substantive; no parsed clause membership is invented.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS '5.1' MATCH (cr)-[:SUBMITTED_BY]->(co:Company) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, cr.clausesAffected, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.214'}) WHERE cr.clausesAffected CONTAINS '5.1' RETURN DISTINCT cr.tdocNumber,cr.clausesAffected
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "cr.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "cr.tdocNumber",
      "type": "string"
    },
    {
      "name": "cr.clausesAffected",
      "nullable": true,
      "source_column_or_expression": "cr.clausesAffected",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ018/4881bc24d93719d5d539b513180fb2a6e87d0efe48f83fa465d554319ca1a3e0.json), [complete native rows](../reference_outputs/RAN1_P3_CQ018/4881bc24d93719d5d539b513180fb2a6e87d0efe48f83fa465d554319ca1a3e0.jsonl); 83 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d3bf0054235e9a84a11dfd32c48d8e5368c19b660a1318ef1aba73f40d258eac`.

## RAN1_P3_CQ019

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Compare CR counts across the eight TSs (where standardization activity concentrates).

**Revised question:** For each of TS 38.201, 38.202, 38.211, 38.212, 38.213, 38.214, 38.215 and 38.291 present in the graph, return its number and count of distinct MODIFIES-linked CR nodes, including zero counts.

**Proposed rationale:** Retain the explicitly enumerated eight-spec scope, include zero-count groups and avoid counting repeated links.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp2:Spec {specNumber:specNumber}) RETURN specNumber AS `sp.specNumber`,count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ019/db4fe61efc5f9d782ab6d87747b52d9785e4b2a6bc451dbcc952fb5796a423e4.json), [complete native rows](../reference_outputs/RAN1_P3_CQ019/db4fe61efc5f9d782ab6d87747b52d9785e4b2a6bc451dbcc952fb5796a423e4.jsonl); 8 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8d4473919fbef5244d41a3b0cd097b693ad6452f8fe69c5f712a56b6da8550d4`.

## RAN1_P3_CQ020

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs Qualcomm submitted against TS 38.214 (its areas of contribution).

**Revised question:** List all distinct CR identifiers linked by MODIFIES to TS 38.214 and SUBMITTED_BY to the Company named Qualcomm.

**Proposed rationale:** An exact named company is preferable to substring-matching Qualcomm variants without a declared alias policy; remove unasked cap and incidental meeting restriction.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) WHERE co.companyName CONTAINS 'Qualcomm' MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.214'}),(cr)-[:SUBMITTED_BY]->(:Company {companyName:'Qualcomm'}) RETURN DISTINCT cr.tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "cr.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "cr.tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ020/dbe3b276539e9bb75c3b00c0fceaa7e4ebba63e07e20f2085a7653d2ba3c5abe.json), [complete native rows](../reference_outputs/RAN1_P3_CQ020/dbe3b276539e9bb75c3b00c0fceaa7e4ebba63e07e20f2085a7653d2ba3c5abe.jsonl); 123 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9a97c64a0830e07e23953b544628ad02730010a68b154df0a4219d276435f552`.

## RAN1_P3_CQ021

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original distinct affected-section interpretation remains unverified; token strings are not certified section references.']

**Original question:** Which are the large CRs touching many clauses? List CRs affecting five or more sections of TS 38.214.

**Revised question:** For CRs modifying specification number 38.214, split clausesAffected text on commas, trim whitespace, discard empty tokens, and deduplicate exact token strings. Return every CR TDoc number with at least five such tokens, its token count, and the unordered token set. Do not interpret or expand ranges.

**Proposed rationale:** Comma-separated raw metadata does not certify five affected sections. This explicit literal-token variant provides a deterministic unit, distinctness rule, and threshold without claiming section-level impact or verified parsing.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND size(split(cr.clausesAffected, ',')) >= 5 RETURN cr.tdocNumber, cr.title, cr.clausesAffected, size(split(cr.clausesAffected, ',')) AS affectedCount ORDER BY affectedCount DESC, cr.tdocNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.214'}) WHERE cr.clausesAffected IS NOT NULL WITH DISTINCT cr UNWIND [token IN split(cr.clausesAffected,',') WHERE trim(token) <> ''] AS raw WITH cr,collect(DISTINCT trim(raw)) AS clauseTokens WHERE size(clauseTokens)>=5 RETURN cr.tdocNumber AS tdocNumber,size(clauseTokens) AS tokenCount,clauseTokens
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": true,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    },
    {
      "name": "tokenCount",
      "nullable": false,
      "source_column_or_expression": "tokenCount",
      "type": "integer"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "clauseTokens",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "kind": "set",
        "tokenization": "comma split; trim; discard empty; no range expansion"
      },
      "nullable": false,
      "source_column_or_expression": "clauseTokens",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ021/330c4fd29447c48f21d6375fac363e31a122a91f10443c440a66460295effb20.json), [complete native rows](../reference_outputs/RAN1_P3_CQ021/330c4fd29447c48f21d6375fac363e31a122a91f10443c440a66460295effb20.jsonl); 34 native rows retained. The retained per-item check record has 12 passing scorer checks for this definition.

**Definition SHA-256:** `f8a65470f61ff49f2b1b86fc4f5247343aa2723544057e12acff125440bbd4c3`.

## RAN1_P3_CQ022

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the trend of TS 38.213 CR submissions per meeting (standardization-activity trend).

**Revised question:** For each recorded Meeting, return its meeting number, meetingNumberInt, and count of distinct CR nodes linked to both that meeting and TS 38.213; include zero counts and order by meetingNumberInt ascending, then meeting number ascending.

**Proposed rationale:** Retain the complete meeting denominator rather than omitting zero-CR meetings; use distinct CR nodes and explicit time order.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) WITH m.meetingNumber AS meeting, m.meetingNumberInt AS meetingInt, count(cr) AS crCount RETURN meeting, crCount ORDER BY meetingInt
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (cr:CR)-[:PRESENTED_AT]->(m),(cr)-[:MODIFIES]->(:Spec {specNumber:'38.213'}) RETURN m.meetingNumber AS meeting,m.meetingNumberInt AS meetingInt,count(DISTINCT cr) AS crCount ORDER BY meetingInt ASC,meeting ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meeting",
      "nullable": true,
      "source_column_or_expression": "meeting",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    },
    {
      "name": "meetingInt",
      "nullable": true,
      "source_column_or_expression": "meetingInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingInt"
      },
      {
        "direction": "asc",
        "field": "meeting"
      }
    ],
    "tie_policy": "meeting identifier string ascending"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "exactly one record per qualifying recorded meeting; all such meetings are returned"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ022/855328dc20c56b10c6e4f5e4a898785b615ccc3815ab2990b7f45a9f4c9c6a4a.json), [complete native rows](../reference_outputs/RAN1_P3_CQ022/855328dc20c56b10c6e4f5e4a898785b615ccc3815ab2990b7f45a9f4c9c6a4a.jsonl); 60 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b4a5671182ee8b0d02d9e64aca215cb3a4d229ce32a4b5c585bd42da3f63e2c0`.

## RAN1_P3_CQ023

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['REFERENCES does not prove CR approval; mark the documentary-count variant explicitly.']

**Original question:** How many agreements approved CRs modifying TS 38.214? (how active decision-making is here)

**Revised question:** How many distinct Agreement nodes reference CR nodes linked by MODIFIES to TS 38.214?

**Proposed rationale:** REFERENCES does not prove CR approval; mark the documentary-count variant explicitly.

**Original query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(DISTINCT agr) AS agrCount
```

**Revised query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(DISTINCT agr) AS agrCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agrCount",
      "nullable": false,
      "source_column_or_expression": "agrCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one integer aggregate record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ023/ac742d823a77faa67ff6131e6ba462e4b1871ff9e78d847d3e6a00facfa11ce1.json), [complete native rows](../reference_outputs/RAN1_P3_CQ023/ac742d823a77faa67ff6131e6ba462e4b1871ff9e78d847d3e6a00facfa11ce1.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `610308649c442b02286914456191ac1b68da8aee45e28570e56b8c67fac320c7`.

## RAN1_P3_CQ024

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The query supports documentary links rather than independent causal impact. Both content and record identifiers are part of the explicit output.']

**Original question:** List the 10 most recent agreements affecting TS 38.213 (recent decisions).

**Revised question:** Return the top ten distinct Agreement/content/meeting records linked through REFERENCES to a CR that MODIFIES specification number 38.213. Return Agreement identifier, contentWithEquations if present otherwise content, meeting-number string and meetingNumberInt. Rank the integer descending, then Agreement identifier, meeting-number string and returned content ascending; return all records if fewer than ten exist.

**Proposed rationale:** The query supports documentary links rather than independent causal impact. Both content and record identifiers are part of the explicit output. Final returned meeting/content keys make distinct-record cutoff deterministic.

**Original query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC, agr.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(:CR)-[:MODIFIES]->(:Spec {specNumber:'38.213'}), (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId,coalesce(agr.contentWithEquations,agr.content) AS content,m.meetingNumber,m.meetingNumberInt ORDER BY m.meetingNumberInt DESC,agr.resolutionId ASC,m.meetingNumber ASC,content ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agr.resolutionId",
      "nullable": true,
      "source_column_or_expression": "agr.resolutionId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": true,
      "source_column_or_expression": "content",
      "type": "string"
    },
    {
      "name": "m.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumber",
      "type": "string"
    },
    {
      "name": "m.meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "m.meetingNumberInt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "m.meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "agr.resolutionId"
      },
      {
        "direction": "asc",
        "field": "m.meetingNumber"
      },
      {
        "direction": "asc",
        "field": "content"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "at most ten Agreement/meeting records",
    "tie_policy": "deterministic_all_keys",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ024/26d3dec2105cd341c214d012b8b239d3c74106c81ba9e118dc96288d0c2745c0.json), [complete native rows](../reference_outputs/RAN1_P3_CQ024/26d3dec2105cd341c214d012b8b239d3c74106c81ba9e118dc96288d0c2745c0.jsonl); 10 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `56b091b767d994230863ee1660f2217687a624af3d1b7ae6c12e588d06097755`.

## RAN1_P3_CQ025

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Use the complete explicitly named Spec-number denominator; agreement links do not independently quantify consensus.']

**Original question:** Summarize the number of agreements per TS (which spec sees the most consensus).

**Revised question:** For each of TS 38.201, 38.202, 38.211, 38.212, 38.213, 38.214, 38.215 and 38.291 present in the graph, return the number and count of distinct Agreements referencing a CR that MODIFIES it; include zero counts.

**Proposed rationale:** Use the complete explicitly named Spec-number denominator; agreement links do not independently quantify consensus.

**Original query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(DISTINCT agr) AS agrCount ORDER BY agrCount DESC
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(:CR)-[:MODIFIES]->(:Spec {specNumber:specNumber}) RETURN specNumber AS `sp.specNumber`,count(DISTINCT agr) AS agrCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "agrCount",
      "nullable": false,
      "source_column_or_expression": "agrCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ025/88eb6f41a8b3c6b33331c982e496c2fa96991c5e2e6306d2b0df7f5edfcaf610.json), [complete native rows](../reference_outputs/RAN1_P3_CQ025/88eb6f41a8b3c6b33331c982e496c2fa96991c5e2e6306d2b0df7f5edfcaf610.jsonl); 8 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `52d594178c18e842b52dfae6c8435b3a00af00b66c9597eaba8c734b6846e0d1`.

## RAN1_P3_CQ026

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Use the recorded marker without claiming an independent issue-state judgment; no unasked cap. Meeting-linked population is now explicit rather than a hidden mandatory join.']

**Original question:** Which TS 38.213 agreements still carry a TBD? (technical issues not yet settled)

**Revised question:** List all distinct Agreement identifier/content pairs with hasTBD=true linked by REFERENCES to a CR that MODIFIES TS 38.213. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Use the recorded marker without claiming an independent issue-state judgment; no unasked cap. Meeting-linked population is now explicit rather than a hidden mandatory join.

**Original query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE agr.hasTBD = true MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE agr.hasTBD = true MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agr.resolutionId",
      "nullable": true,
      "source_column_or_expression": "agr.resolutionId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": true,
      "source_column_or_expression": "content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ026/30d198930263f0d4072e2925c4bc3671a8ef594e926da88ca59dba00e9618fcc.json), [complete native rows](../reference_outputs/RAN1_P3_CQ026/30d198930263f0d4072e2925c4bc3671a8ef594e926da88ca59dba00e9618fcc.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0842caaaffcd2b67ac769e549a8ae21968b2f5ce02f058157887574176f7baff`.

## RAN1_P3_CQ027

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are there agreements that reference CRs across multiple TSs at once? (cross-TS decisions)

**Revised question:** Does any Agreement node reference CR nodes that MODIFIES-link to at least two distinct Spec-number values anywhere in the graph?

**Proposed rationale:** Preserve yes/no intent and remove the query-only five-spec restriction. Count Spec numbers rather than version nodes.

**Original query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH agr, collect(DISTINCT sp.specNumber) AS specs WHERE size(specs) > 1 MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN agr.resolutionId, specs, m.meetingNumber ORDER BY m.meetingNumberInt DESC, agr.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(:CR)-[:MODIFIES]->(sp:Spec) WITH agr,count(DISTINCT sp.specNumber) AS specCount WHERE specCount>1 RETURN count(DISTINCT agr)>0 AS hasCrossSpecAgreement
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "hasCrossSpecAgreement",
      "nullable": false,
      "source_column_or_expression": "hasCrossSpecAgreement",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one Boolean record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ027/1cff3c4cf69da88c4a932fa096102ac16c55a0d5dcda506e64ab2a42350c5e91.json), [complete native rows](../reference_outputs/RAN1_P3_CQ027/1cff3c4cf69da88c4a932fa096102ac16c55a0d5dcda506e64ab2a42350c5e91.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `822f329638be3aa5ac771bd8717f64f3906b370db1221f7141681974fc6c13be`.

## RAN1_P3_CQ028

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The revised task restricts the population to records with a MADE_AT Meeting link. The original question did not explicitly require that restriction; this supplied scope is a substantive variant, not verified preservation of the original population.']

**Original question:** Which TS 38.213 resolutions mention HARQ? (tracing HARQ-related decisions)

**Revised question:** List all distinct Resolution identifier/content pairs whose contentWithEquations, or content fallback, contains HARQ case-insensitively and which reference a CR that MODIFIES TS 38.213. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Both requested resolution identity and text are graded; exact documentary and literal-match scope is explicit. Meeting-linked population is now explicit rather than a hidden mandatory join. The revised task restricts the population to records with a MADE_AT Meeting link. The original question did not explicitly require that restriction; this supplied scope is a substantive variant, not verified preservation of the original population.

**Original query**

```cypher
MATCH (res:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE COALESCE(res.contentWithEquations, res.content, '') =~ '(?i).*HARQ.*' MATCH (res)-[:MADE_AT]->(m:Meeting) RETURN [lbl IN ['Resolution','Agreement','Conclusion','WorkingAssumption'] WHERE lbl IN labels(res)] AS type, res.resolutionId, COALESCE(res.contentWithEquations, res.content) AS content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, res.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (res:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE COALESCE(res.contentWithEquations, res.content, '') =~ '(?i).*HARQ.*' MATCH (res)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT [lbl IN ['Resolution','Agreement','Conclusion','WorkingAssumption'] WHERE lbl IN labels(res)] AS type, res.resolutionId, COALESCE(res.contentWithEquations, res.content) AS content, m.meetingNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "res.resolutionId",
      "nullable": true,
      "source_column_or_expression": "res.resolutionId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": true,
      "source_column_or_expression": "content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ028/f548de0fab4fdd04744093cd4405a593ae61c2391fa7ee46967ed0422a1d68fa.json), [complete native rows](../reference_outputs/RAN1_P3_CQ028/f548de0fab4fdd04744093cd4405a593ae61c2391fa7ee46967ed0422a1d68fa.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e3318291a6983e072abbc517c54b03e02290ebc6d082f6ff94996fe61cc5ea06`.

## RAN1_P3_CQ029

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TSs define antenna-related sections? (locating specs for antenna-port implementation)

**Revised question:** List all distinct Spec-number strings having a linked Section title containing antenna case-insensitively.

**Proposed rationale:** The question asks TS identities rather than every unrequested title/count; title matching is explicit.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*antenna.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*antenna.*' RETURN DISTINCT sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ029/9307ecb641d1eca0f80d56a975e6b3ef7a2e7878c1820db18efabcd71f4c931b.json), [complete native rows](../reference_outputs/RAN1_P3_CQ029/9307ecb641d1eca0f80d56a975e6b3ef7a2e7878c1820db18efabcd71f4c931b.jsonl); 5 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a5129b6b05a930a06747fcb787cb474ebb58666a537d99313ff746dab3fc5503`.

## RAN1_P3_CQ030

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Table identifier distinguishes versions; the candidate is an explicit caption match rather than a full semantic CSI inventory.']

**Original question:** List the CSI-related tables (parameter tables for CSI-reporting implementation).

**Revised question:** List all distinct linked TSTable identifiers, numbers and captions whose caption contains CSI case-insensitively.

**Proposed rationale:** Table identifier distinguishes versions; the candidate is an explicit caption match rather than a full semantic CSI inventory.

**Original query**

```cypher
MATCH (tbl:TSTable) WHERE tbl.tableCaption =~ '(?i).*CSI.*' MATCH (tbl)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY sp.specNumber, tbl.tableNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(:Spec) WHERE tbl.tableCaption =~ '(?i).*CSI.*' RETURN DISTINCT tbl.tableId,tbl.tableNumber,tbl.tableCaption
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tableId",
      "nullable": true,
      "source_column_or_expression": "tbl.tableId",
      "type": "string"
    },
    {
      "name": "tbl.tableNumber",
      "nullable": true,
      "source_column_or_expression": "tbl.tableNumber",
      "type": "string"
    },
    {
      "name": "tbl.tableCaption",
      "nullable": true,
      "source_column_or_expression": "tbl.tableCaption",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ030/4b4789849fd2e79793e6055044e02d4608d1ce0011ce95d89ff8ae802a2e89db.json), [complete native rows](../reference_outputs/RAN1_P3_CQ030/4b4789849fd2e79793e6055044e02d4608d1ce0011ce95d89ff8ae802a2e89db.jsonl); 332 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `930af735c7054472152452635236c76346634a4b2685b593a1c7e110715e3b7b`.

## RAN1_P3_CQ031

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Distribution means spec/count pairs, not merely spec names. Define the recorded title-match criterion.']

**Original question:** How are HARQ-related sections distributed across the TSs? (scope of HARQ implementation)

**Revised question:** For each Spec-number group having a Section title containing HARQ case-insensitively, return its Spec number and count of distinct matching Section nodes across recorded versions.

**Proposed rationale:** Distribution means spec/count pairs, not merely spec names. Define the recorded title-match criterion.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*HARQ.*' RETURN sp.specNumber, count(sec) AS sectionCount, collect(sec.sectionNumber) AS sections ORDER BY sectionCount DESC
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*HARQ.*' RETURN sp.specNumber, count(DISTINCT sec) AS sectionCount, collect(sec.sectionNumber) AS sections
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionCount",
      "nullable": false,
      "source_column_or_expression": "sectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ031/5c417f37583c2db051b2aec7f72d1f2cd29dbebd38c611b3ca4d14daf7101870.json), [complete native rows](../reference_outputs/RAN1_P3_CQ031/5c417f37583c2db051b2aec7f72d1f2cd29dbebd38c611b3ca4d14daf7101870.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a871736fc3c2aefa1f236818dacc0d0f44620d9f727f43f5f91455b164a01c8e`.

## RAN1_P3_CQ032

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.']

**Original question:** Show the PDCCH-related sections and tables (full scope for control-channel implementation).

**Revised question:** For every Section title containing PDCCH case-insensitively, return Spec number, Section identifier and title, and the set of distinct CONTAINS_TABLE-linked TSTable identifiers, with an empty set when none are linked.

**Proposed rationale:** Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDCCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDCCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber,sec.sectionId,sec.sectionTitle,collect(DISTINCT tbl.tableId) AS tables
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "tables",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "empty": "empty array",
        "kind": "set"
      },
      "nullable": false,
      "source_column_or_expression": "tables",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ032/1af2444ae7f44bd2358a559cd0ca5faf2b2ce532c9290540f5cf36f5ffc36134.json), [complete native rows](../reference_outputs/RAN1_P3_CQ032/1af2444ae7f44bd2358a559cd0ca5faf2b2ce532c9290540f5cf36f5ffc36134.jsonl); 53 native rows retained. The retained per-item check record has 15 passing scorer checks for this definition.

**Definition SHA-256:** `06990be9713549f77db2ec0e24628112eaac8fa4a248a53c47550d4f34ffc8ad`.

## RAN1_P3_CQ033

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.']

**Original question:** Show the PUSCH-related sections and tables (scope for uplink data-channel implementation).

**Revised question:** For every Section title containing PUSCH case-insensitively, return Spec number, Section identifier and title, and the set of distinct CONTAINS_TABLE-linked TSTable identifiers, with an empty set when none are linked.

**Proposed rationale:** Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PUSCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PUSCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber,sec.sectionId,sec.sectionTitle,collect(DISTINCT tbl.tableId) AS tables
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "tables",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "empty": "empty array",
        "kind": "set"
      },
      "nullable": false,
      "source_column_or_expression": "tables",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ033/fde66920f6f3b846f85f4fcc04a3453c5abfbeadd632655d67fca5451a23d80a.json), [complete native rows](../reference_outputs/RAN1_P3_CQ033/fde66920f6f3b846f85f4fcc04a3453c5abfbeadd632655d67fca5451a23d80a.jsonl); 107 native rows retained. The retained per-item check record has 15 passing scorer checks for this definition.

**Definition SHA-256:** `6c3b54f5012739f84bea07f043c36b55ed39754aee36b5ff38b414ee44d551be`.

## RAN1_P3_CQ034

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.']

**Original question:** Show the SRS (Sounding Reference Signal) sections and tables (specs for SRS implementation).

**Revised question:** For every Section title containing SRS or sounding case-insensitively, return Spec number, Section identifier and title, and the set of distinct CONTAINS_TABLE-linked TSTable identifiers, with an empty set when none are linked.

**Proposed rationale:** Version-bearing Section and table identities prevent accidental merging of repeated numbers. Topic completeness is not certified by title matching.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*SRS.*' OR sec.sectionTitle =~ '(?i).*sounding.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*SRS.*' OR sec.sectionTitle =~ '(?i).*sounding.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber,sec.sectionId,sec.sectionTitle,collect(DISTINCT tbl.tableId) AS tables
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "tables",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "empty": "empty array",
        "kind": "set"
      },
      "nullable": false,
      "source_column_or_expression": "tables",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ034/a4a2a6c684efc32fb8472a0f3db2c692fceac8794968a40e6f8edbaa477eab40.json), [complete native rows](../reference_outputs/RAN1_P3_CQ034/a4a2a6c684efc32fb8472a0f3db2c692fceac8794968a40e6f8edbaa477eab40.jsonl); 73 native rows retained. The retained per-item check record has 15 passing scorer checks for this definition.

**Definition SHA-256:** `e5200c6d91e752f85a69ad81b9828cb34c8803caa1101b83bb5daa85bd6681fb`.

## RAN1_P3_CQ035

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which sections mention measurement or reporting? (scope for measurement-reporting implementation)

**Revised question:** List all distinct Spec-number/Section-identifier/title records whose title contains measurement or reporting case-insensitively.

**Proposed rationale:** Only titles are searched; remove hidden cap and retain Section identity.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*(measurement|reporting).*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle ORDER BY sp.specNumber, sec.sectionNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*(measurement|reporting).*' RETURN DISTINCT sp.specNumber,sec.sectionId,sec.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "sec.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sec.sectionTitle",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ035/591a73d36557e05b00b8f117ede887df89a4b0fc77335af1e94526a9a19dc2ea.json), [complete native rows](../reference_outputs/RAN1_P3_CQ035/591a73d36557e05b00b8f117ede887df89a4b0fc77335af1e94526a9a19dc2ea.jsonl); 182 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `e07f8f7709bc18558be8b8525eb9e661a15f07ba8dca766976ff51d513ee8e5a`.

## RAN1_P3_CQ036

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Compare the top 5 TSs by CR count against their section counts (complexity vs. change frequency).

**Revised question:** Among the eight explicitly listed RAN1 TS numbers, return the five greatest distinct-CR counts together with distinct Section-node counts across all recorded versions. Sort by CR count descending and TS number ascending; include zero counts for recorded Spec numbers.

**Proposed rationale:** Avoid count inflation, hidden top-k ties and inner-match removal of zero-section groups. Counts do not independently measure implementation complexity.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH sp.specNumber AS ts, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5 MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: ts}) RETURN ts, crCount, count(sec) AS sectionCount ORDER BY crCount DESC
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH DISTINCT sp.specNumber AS ts OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:ts}) WITH ts,count(DISTINCT cr) AS crCount ORDER BY crCount DESC,ts ASC LIMIT 5 OPTIONAL MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:ts}) RETURN ts,crCount,count(DISTINCT sec) AS sectionCount ORDER BY crCount DESC,ts ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ts",
      "nullable": true,
      "source_column_or_expression": "ts",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    },
    {
      "name": "sectionCount",
      "nullable": false,
      "source_column_or_expression": "sectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crCount"
      },
      {
        "direction": "asc",
        "field": "ts"
      }
    ],
    "tie_policy": "TS number lexicographically ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "return min(5, qualifying population size); no extra boundary ties; cutoff is selected before downstream joins",
    "tie_policy": "TS number lexicographically ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ036/90c1c75447210fe67a083d97f3029b09b4cb87ecb6fa4ad7413730ac31fb056a.json), [complete native rows](../reference_outputs/RAN1_P3_CQ036/90c1c75447210fe67a083d97f3029b09b4cb87ecb6fa4ad7413730ac31fb056a.jsonl); 5 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `2461fb49ccc41f60f93cb59db0cf34d529cdbf27d1442c9423d510c9fceb6b45`.

## RAN1_P3_CQ037

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Rank companies by total CRs submitted across the eight TSs (who the major players are).

**Revised question:** Rank every company-name group having at least one matching submitted CR by the count of distinct submitted CR nodes that MODIFIES-link to at least one of TS 38.201, 38.202, 38.211, 38.212, 38.213, 38.214, 38.215 or 38.291; order count descending and company name ascending.

**Proposed rationale:** The original rank-all question has no top15 request. Count each CR once per company even when it modifies several listed Specs.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, co.companyName ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "co.companyName",
      "nullable": true,
      "source_column_or_expression": "co.companyName",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crCount"
      },
      {
        "direction": "asc",
        "field": "co.companyName"
      }
    ],
    "tie_policy": "company name ascending"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching Company groups"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ037/50d8124665e2b07f7de906d05cdd659d4cd77037e1e0b3083b1fe60ae6f62bfc.json), [complete native rows](../reference_outputs/RAN1_P3_CQ037/50d8124665e2b07f7de906d05cdd659d4cd77037e1e0b3083b1fe60ae6f62bfc.jsonl); 71 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `1b47eb0e09059cecb5e104ef5fe6cd8ef113299ccdc314197b67a0d6c0910afb`.

## RAN1_P3_CQ038

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original CR modification claims remain unverified: exact literal token matching neither expands ranges nor establishes intended edition or actual modification.']

**Original question:** Return the top 10 most-referenced sections and how many CRs modified each (stability of core sections).

**Revised question:** Return the top ten Section nodes by distinct incoming REFERENCES_SECTION source count, including zero-reference Sections; break ties by Section identifier ascending. For each return Section identifier, incoming count, and number of distinct CR nodes modifying the same specification number whose comma-split, trimmed clausesAffected tokens exactly equal that Section number. Treat this last count as literal metadata matches, not verified section modifications.

**Proposed rationale:** The original substring heuristic cannot certify CR-modified sections. This variant preserves the requested top-reference analysis while replacing the unsupported modification count with a precisely stated literal join and visibly withholding edition/impact certification.

**Original query**

```cypher
MATCH (tgt:Section)<-[:REFERENCES_SECTION]-(src:Section) WITH tgt, count(src) AS refCount ORDER BY refCount DESC LIMIT 10 MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS tgt.sectionNumber RETURN sp.specNumber, tgt.sectionNumber, tgt.sectionTitle, refCount, count(cr) AS crCount ORDER BY refCount DESC
```

**Revised query**

```cypher
MATCH (tgt:Section) OPTIONAL MATCH (src:Section)-[:REFERENCES_SECTION]->(tgt) WITH tgt,count(DISTINCT src) AS refCount ORDER BY refCount DESC,tgt.sectionId ASC LIMIT 10 OPTIONAL MATCH (tgt)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(crSpec:Spec) WHERE crSpec.specNumber=sp.specNumber AND cr.clausesAffected IS NOT NULL AND tgt.sectionNumber IN [token IN split(cr.clausesAffected,',') | trim(token)] RETURN tgt.sectionId AS sectionId,refCount,count(DISTINCT cr) AS literalClauseCRCount ORDER BY refCount DESC,sectionId ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "refCount",
      "nullable": false,
      "source_column_or_expression": "refCount",
      "type": "integer"
    },
    {
      "name": "literalClauseCRCount",
      "nullable": false,
      "source_column_or_expression": "literalClauseCRCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "refCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "return min(10, qualifying population size); no extra boundary ties; cutoff is selected before downstream joins",
    "tie_policy": "Section identifier ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ038/26390ee03e76a0383f90812fc1aeb151ca3680ac1875e16672f26eec7822d3c7.json), [complete native rows](../reference_outputs/RAN1_P3_CQ038/26390ee03e76a0383f90812fc1aeb151ca3680ac1875e16672f26eec7822d3c7.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `5854c6199c6721863a8a730b9b1e11fe84c29c803b7b8192ab5292257f2f4f1a`.

## RAN1_P3_CQ039

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which companies submitted the most CRs modifying TS 38.214? Top 10 (technical leadership in this spec).

**Revised question:** Among all recorded company-name groups, return the ten with the greatest counts of distinct submitted CR nodes MODIFIES-linked to specification number 38.214, including zero-count groups. Return company/count pairs; rank count descending then company name ascending, returning all available groups if fewer than ten exist.

**Proposed rationale:** Correct document counting unit and deterministic top-k ties; no independent technical-leadership label is asserted. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (co:Company) OPTIONAL MATCH (cr:CR)-[:SUBMITTED_BY]->(co), (cr)-[:MODIFIES]->(:Spec {specNumber:'38.214'}) RETURN co.companyName,count(DISTINCT cr) AS crCount ORDER BY crCount DESC,co.companyName ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "co.companyName",
      "nullable": true,
      "source_column_or_expression": "co.companyName",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crCount"
      },
      {
        "direction": "asc",
        "field": "co.companyName"
      }
    ],
    "tie_policy": "company name ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.",
    "short_population": "all_available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ039/6710e9ea55247d89a77e73fc6f5b0e3becd887d3251baa616cf51b03956a8fe4.json), [complete native rows](../reference_outputs/RAN1_P3_CQ039/6710e9ea55247d89a77e73fc6f5b0e3becd887d3251baa616cf51b03956a8fe4.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e5bd74615c2c75fd71b9f4158b63c520679576621a177319fcfc4584bc82dfb9`.

## RAN1_P3_CQ040

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Use all requested numeric roles and a complete named denominator; recorded Agreement links do not independently measure consensus. The five-TS subset is an explicitly declared variant; the unspecified all-TS original is not certified.']

**Original question:** Compare CR counts against agreement counts per TS (which spec changes most relative to consensus).

**Revised question:** For TS 38.211, 38.212, 38.213, 38.214 and 38.215 present in the graph, return each number, count of distinct CR nodes that MODIFIES it, and count of distinct Agreements that REFERENCES one of those CRs; include zero counts.

**Proposed rationale:** Use all requested numeric roles and a complete named denominator; recorded Agreement links do not independently measure consensus. The five-TS subset is an explicitly declared variant; the unspecified all-TS original is not certified.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH sp.specNumber AS ts, count(cr) AS crCnt OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(cr2:CR)-[:MODIFIES]->(sp2:Spec) WHERE sp2.specNumber = ts RETURN ts, crCnt, count(DISTINCT agr) AS agrCnt ORDER BY crCnt DESC
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH DISTINCT sp.specNumber AS ts OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:ts}) WITH ts,count(DISTINCT cr) AS crCnt OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(:CR)-[:MODIFIES]->(:Spec {specNumber:ts}) RETURN ts,crCnt,count(DISTINCT agr) AS agrCnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ts",
      "nullable": true,
      "source_column_or_expression": "ts",
      "type": "string"
    },
    {
      "name": "crCnt",
      "nullable": false,
      "source_column_or_expression": "crCnt",
      "type": "integer"
    },
    {
      "name": "agrCnt",
      "nullable": false,
      "source_column_or_expression": "agrCnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ040/d5b2c56a6cc379e5d542986262114b87c2d185e0be37f4ae63e33182feb9101e.json), [complete native rows](../reference_outputs/RAN1_P3_CQ040/d5b2c56a6cc379e5d542986262114b87c2d185e0be37f4ae63e33182feb9101e.jsonl); 5 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `4027c4dbb1f061ae73f93f478413ec1a094b6e7e1a5c4e0116fe838ace7624ad`.

## RAN1_P3_CQ041

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which sections contain five or more tables? (parameter-dense implementation points)

**Revised question:** List every distinct Section identifier with at least five distinct CONTAINS_TABLE-linked TSTable nodes, and its table-node count.

**Proposed rationale:** Remove the unasked top15 cap and grade the identity/count pair.

**Original query**

```cypher
MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 5 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount ORDER BY tableCount DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec,count(DISTINCT tbl) AS tableCount WHERE tableCount>=5 RETURN sec.sectionId,tableCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sec.sectionId",
      "type": "string"
    },
    {
      "name": "tableCount",
      "nullable": false,
      "source_column_or_expression": "tableCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ041/29c75e4856a2d581172ee368fb25dda8a8054bd2820d597f60945d2c80969590.json), [complete native rows](../reference_outputs/RAN1_P3_CQ041/29c75e4856a2d581172ee368fb25dda8a8054bd2820d597f60945d2c80969590.jsonl); 98 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `fd0da582add7d3504113292c9ce07c1cb1f4e5194b1484ad3c9fbf4ea3c4956c`.

## RAN1_P3_CQ042

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original implementation difficulty was not measured; the joint ordering is a newly declared structural variant, not recovery of unspecified original intent.']

**Explicit additional inputs (retained provenance)**

```json
[
  {
    "name": "minimum_table_count",
    "origin": "visible retained original query threshold",
    "value": 3
  },
  {
    "name": "minimum_direct_subsection_count",
    "origin": "new explicit both-dimensions criterion",
    "value": 1
  }
]
```

**Original question:** Which are the top 10 areas rich in both sections and tables? (high implementation difficulty)

**Revised question:** Using a minimum of three tables as an explicit input, return the top ten Section nodes by distinct CONTAINS_TABLE target count descending, then distinct direct HAS_SUB_SECTION child count descending, then Section identifier ascending. Include only nodes with at least three tables and at least one direct child. Return identifier and both counts. This measures recorded structural density.

**Proposed rationale:** The original joint-richness ranking and implementation difficulty were undefined. This explicit threshold/ranking variant makes both structural dimensions operative, removes join multiplication, and does not assert measured implementation difficulty.

**Original query**

```cypher
MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 3 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) OPTIONAL MATCH (sec)-[:HAS_SUB_SECTION]->(sub:Section) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount, count(sub) AS subSectionCount ORDER BY tableCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section) OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec,count(DISTINCT tbl) AS tableCount WHERE tableCount>=3 OPTIONAL MATCH (sec)-[:HAS_SUB_SECTION]->(sub:Section) WITH sec,tableCount,count(DISTINCT sub) AS subSectionCount WHERE subSectionCount>=1 RETURN sec.sectionId AS sectionId,tableCount,subSectionCount ORDER BY tableCount DESC,subSectionCount DESC,sectionId ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "tableCount",
      "nullable": false,
      "source_column_or_expression": "tableCount",
      "type": "integer"
    },
    {
      "name": "subSectionCount",
      "nullable": false,
      "source_column_or_expression": "subSectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tableCount"
      },
      {
        "direction": "desc",
        "field": "subSectionCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "direct-child count descending, then Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top ten structurally qualifying Section nodes or all when fewer exist",
    "tie_policy": "direct-child count descending, then Section identifier ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ042/7d9f18069808f48e7635a27d140ea2c29ce3a5cc46d0ddc01ccfc313d9f17df8.json), [complete native rows](../reference_outputs/RAN1_P3_CQ042/7d9f18069808f48e7635a27d140ea2c29ce3a5cc46d0ddc01ccfc313d9f17df8.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `c3608c8775f7abbab80f38850f39eb7be6989c77c677085f0b9e3d1bbd3a5003`.

## RAN1_P3_CQ044

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TSs modified by CRs under Work Item NR_newRAT-Core (portfolio impact of this work item).

**Revised question:** List all distinct Spec-number strings linked by MODIFIES from CRs RELATED_TO Work Item NR_newRAT-Core.

**Proposed rationale:** Question asks impacted TS identities; counts are incidental, and the graph link is documentary.

**Original query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(cr) AS crCount ORDER BY crCount DESC
```

**Revised query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "spec",
      "nullable": true,
      "source_column_or_expression": "spec",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ044/44d757001432fdcd18ab932e750ac6392efc20e81eac3bd1e5693c864eb907e4.json), [complete native rows](../reference_outputs/RAN1_P3_CQ044/44d757001432fdcd18ab932e750ac6392efc20e81eac3bd1e5693c864eb907e4.jsonl); 16 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a5564ea444818fcacdf000ae01d2ac24c94cb4f9ccfa5fd2d266cb214abe2d20`.

## RAN1_P3_CQ045

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Recorded connectivity does not demonstrate that resolutions entered the normative standard.']

**Original question:** Which TSs did resolutions on NR_FeMIMO-Core CRs land in? (how this work item's decisions entered the standard)

**Revised question:** List every distinct Spec-number string reachable from NR_FeMIMO-Core through RELATED_TO CRs that are also referenced by a Resolution.

**Proposed rationale:** Recorded connectivity does not demonstrate that resolutions entered the normative standard.

**Original query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_FeMIMO-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) MATCH (res:Resolution)-[:REFERENCES]->(cr) RETURN sp.specNumber AS spec, count(DISTINCT res) AS resolutionCount, count(DISTINCT cr) AS crCount ORDER BY resolutionCount DESC
```

**Revised query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_FeMIMO-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) MATCH (res:Resolution)-[:REFERENCES]->(cr) RETURN sp.specNumber AS spec, count(DISTINCT res) AS resolutionCount, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "spec",
      "nullable": true,
      "source_column_or_expression": "spec",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_CQ045/82a6f025f52fb53ac5ae6b8da2529a4fe64cc06c6e9f1e4729dea30b5daca2d1.json), [complete native rows](../reference_outputs/RAN1_P3_CQ045/82a6f025f52fb53ac5ae6b8da2529a4fe64cc06c6e9f1e4729dea30b5daca2d1.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `479e25ad37ed7e8318afd65c950b9eb133a36589499b5e32699d1bf50f000862`.

## RAN1_P3_P3-S8-CQ02

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are all item-level entity nodes linked to a Section via :definedInSection? (grounding-coverage check)

**Revised question:** Is every node labeled RRCParameter, CapabilityItem, Procedure, PerformanceRequirement or ConformanceTest and having granularity=item linked to a Section by definedInSection? Return true for an empty qualifying population.

**Proposed rationale:** Preserve the original universal Boolean intent. Explicit node-label population and vacuous-empty convention replace incorrect class-name-only scoring.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

**Revised query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,exists((n)-[:definedInSection]->(:Section)) AS linked RETURN count(n)=sum(CASE WHEN linked THEN 1 ELSE 0 END) AS allLinked
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "allLinked",
      "nullable": false,
      "source_column_or_expression": "allLinked",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one Boolean record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_P3-S8-CQ02/355597e5fd81eeb9b3ef5d5ede7b2503a1053ed717ae1b01e72d8b004003c78f.json), [complete native rows](../reference_outputs/RAN1_P3_P3-S8-CQ02/355597e5fd81eeb9b3ef5d5ede7b2503a1053ed717ae1b01e72d8b004003c78f.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `59649c5f4eab4ed5bb8dd41546c7ab0a28296592ee8256095daa66e7910c0773`.

## RAN1_P3_P3-S8-CQ04

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The actual shared catalog and loader supply a recoverable benchmark input. Normalize pairs lexicographically and compare complete pair sets rather than grading the first Feature name.']

**Explicit additional inputs (retained provenance)**

```json
{
  "curation_status": "uncurated",
  "expected_undirected_pairs": 6,
  "path": "ontology/config/feature_catalog.yaml",
  "sha256": "53eadcce776589eb6e3df230da31e53638eea84a3c636419e79fd74973b28468"
}
```

The supplied catalog input is [catalog_input.json](../catalog_input.json); the recorded original path above is provenance, not an offline dependency.

**Original question:** Do the disjointWith relations between Features (LTM, CHO, CPC, CPAC, etc.) match the feature catalog's disjoint groups? (consistency check)

**Revised question:** Does the complete set of unordered Feature-name pairs joined by disjointWith equal the pair set generated from every disjoint_feature_groups member combination in the supplied checksum-pinned SPECTRA Feature catalog? Return one Boolean; this tests consistency with an uncurated SPECTRA-authored input, not independent 3GPP truth. Include self-links, equal-name links, and links with missing names in the actual normalized pair set; these must also match the supplied catalog.

**Proposed rationale:** The actual shared catalog and loader supply a recoverable benchmark input. Normalize pairs lexicographically and compare complete pair sets rather than grading the first Feature name. Explicitly require all actual pair members to have non-null names, making missing-name edges a Boolean false rather than nullable comparison.

**Original query**

```cypher
MATCH (a:Feature)-[:disjointWith]->(b:Feature) WHERE a.name < b.name RETURN a.name AS a, b.name AS b ORDER BY a, b
```

**Revised query**

```cypher
WITH [["Conditional Handover (CHO, Rel-16)", "Conditional PSCell Addition/Change (CPAC, Rel-18)"], ["Conditional Handover (CHO, Rel-16)", "Conditional PSCell Change (CPC, Rel-16)"], ["Conditional Handover (CHO, Rel-16)", "LTM (L1/L2 Triggered Mobility, Rel-18)"], ["Conditional PSCell Addition/Change (CPAC, Rel-18)", "Conditional PSCell Change (CPC, Rel-16)"], ["Conditional PSCell Addition/Change (CPAC, Rel-18)", "LTM (L1/L2 Triggered Mobility, Rel-18)"], ["Conditional PSCell Change (CPC, Rel-16)", "LTM (L1/L2 Triggered Mobility, Rel-18)"]] AS expected OPTIONAL MATCH (a:Feature)-[:disjointWith]-(b:Feature) WITH expected,collect(DISTINCT CASE WHEN a IS NULL THEN null WHEN a.name <= b.name THEN [a.name,b.name] ELSE [b.name,a.name] END) AS actual RETURN size(actual)=size(expected) AND all(pair IN actual WHERE all(member IN pair WHERE member IS NOT NULL)) AND all(pair IN expected WHERE pair IN actual) AS matches
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "matches",
      "nullable": false,
      "source_column_or_expression": "matches",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one Boolean record",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_P3-S8-CQ04/259d126a11584ec37e08b6c7bdfda2ea4992dd0704cfe06b05bc002da001d3d2.json), [complete native rows](../reference_outputs/RAN1_P3_P3-S8-CQ04/259d126a11584ec37e08b6c7bdfda2ea4992dd0704cfe06b05bc002da001d3d2.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ef83b70e7fe6791303c8a72c7e9f188dba3bb29f0d454c3565f50f49e3162b6e`.

## RAN1_P3_P3-S8-CQ05

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What is the granularity-property distribution across the five entity classes? (item-level vs. section-level)

**Revised question:** For each of the five named entity labels present on a node, return that class label, its literal granularity value or null when missing, and count of distinct nodes in the label/value group. A multi-label node may contribute to multiple class groups.

**Proposed rationale:** Avoid silently choosing the first label and sentinel collision for a real &lt;unset&gt; string; preserve null as a typed value.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

**Revised query**

```cypher
MATCH (n) UNWIND [l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'] WHERE l IN labels(n)] AS class RETURN class,n.granularity AS granularity,count(DISTINCT n) AS c
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "class",
      "nullable": false,
      "source_column_or_expression": "class",
      "type": "string"
    },
    {
      "name": "granularity",
      "nullable": true,
      "source_column_or_expression": "granularity",
      "type": "string"
    },
    {
      "name": "c",
      "nullable": false,
      "source_column_or_expression": "c",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P3_P3-S8-CQ05/833993bba0052cf15fc9bce0b5402b6895872eb764d5ff0cc5564f719e2db3ad.json), [complete native rows](../reference_outputs/RAN1_P3_P3-S8-CQ05/833993bba0052cf15fc9bce0b5402b6895872eb764d5ff0cc5564f719e2db3ad.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `50723a7858da391dbd6a84a99c6df0fd46adf91d1a7521411e5ffba8f0ca3111`.

## RAN1_P4_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What happens if the CRs under Work Item NR_LPWUS-Core (Rel-19 LP-WUS/WUR) are not approved? (consequences-if-not-approved)

**Revised question:** For every CR RELATED_TO NR_LPWUS-Core having a nonnull consequencesIfNotApproved property, return its identifier and that recorded statement.

**Proposed rationale:** The field stores documentary authorship rather than an independently measured counterfactual. Grade both identity and text.

**Original query**

```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved ORDER BY cr.tdocNumber DESC
```

**Revised query**

```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "cr.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "cr.tdocNumber",
      "type": "string"
    },
    {
      "name": "cr.consequencesIfNotApproved",
      "nullable": false,
      "source_column_or_expression": "cr.consequencesIfNotApproved",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ1-3/d432744dda0d2632d82a3b0c3d3c2bf687a474c049552d99d5c1905a9ad08f7e.json), [complete native rows](../reference_outputs/RAN1_P4_CQ1-3/d432744dda0d2632d82a3b0c3d3c2bf687a474c049552d99d5c1905a9ad08f7e.jsonl); 14 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bff97261cfe4f82cc1c761f650731045b9cc2d3a9c97645f48aee2734ceb26b4`.

## RAN1_P4_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the five specs CR R1-2504971 affects and the impact type (Core/Test/OM) for each.

**Revised question:** List all distinct Spec-number/relation-type pairs linked from CR R1-2504971 by AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC.

**Proposed rationale:** Grade the requested target and impact role; five is a historical observed count rather than a silently enforced cap.

**Original query**

```cypher
MATCH (cr:CR {tdocNumber: 'R1-2504971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, sp.specNumber, type(r) AS relationType ORDER BY sp.specNumber ASC
```

**Revised query**

```cypher
MATCH (cr:CR {tdocNumber: 'R1-2504971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN DISTINCT cr.tdocNumber, sp.specNumber, type(r) AS relationType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "relationType",
      "nullable": true,
      "source_column_or_expression": "relationType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ2-1/2e98d288fad78836034d81b031718e48f9372c292880c267e8cc76a4afea9150.json), [complete native rows](../reference_outputs/RAN1_P4_CQ2-1/2e98d288fad78836034d81b031718e48f9372c292880c267e8cc76a4afea9150.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b7e8e08252a2282847e6bc7b2c518cc75a960d3d2dd35cf367b67867a61d0b19`.

## RAN1_P4_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Other means a different Spec number, not merely a different version node. Ripple-into causality is not implied.']

**Original question:** Which other specs do CRs modifying TS 38.214 most often ripple into, and how many CRs each?

**Revised question:** For CRs that MODIFIES-link to TS 38.214, return every other Spec-number string linked by one of the three AFFECTS relations and the number of distinct such CR nodes.

**Proposed rationale:** Other means a different Spec number, not merely a different version node. Ripple-into causality is not implied.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(mainSpec:Spec {specNumber: '38.214'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(otherSpec:Spec) WHERE mainSpec <> otherSpec RETURN mainSpec.specNumber AS modifiedSpec, otherSpec.specNumber AS affectedSpec, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(mainSpec:Spec {specNumber: '38.214'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(otherSpec:Spec) WHERE mainSpec.specNumber <> otherSpec.specNumber RETURN mainSpec.specNumber AS modifiedSpec, otherSpec.specNumber AS affectedSpec, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "affectedSpec",
      "nullable": true,
      "source_column_or_expression": "affectedSpec",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ2-2/9b8d2e57160e96bb31be575b5dfddb032559ca1d97e11738085c000bfb5f9d75.json), [complete native rows](../reference_outputs/RAN1_P4_CQ2-2/9b8d2e57160e96bb31be575b5dfddb032559ca1d97e11738085c000bfb5f9d75.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `087d7c1468849098e87600a49adf58a6ff58082e396e743d27d1d8bd320fafbc`.

## RAN1_P4_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Representativeness is not measured; replace unordered collect slicing with an explicitly deterministic sample and count documents once across versions/roles.']

**Original question:** How many CRs list TS 38.214 as a cross-spec impact target, and which are representative?

**Revised question:** Return the count of distinct CR identifiers linked by any AFFECTS relation to Spec number 38.214, and the lexicographically smallest at most ten distinct CR identifiers as a deterministic illustrative sample.

**Proposed rationale:** Representativeness is not measured; replace unordered collect slicing with an explicitly deterministic sample and count documents once across versions/roles.

**Original query**

```cypher
MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec {specNumber: '38.214'}) WITH sp, collect(cr.tdocNumber) AS crList, count(cr) AS crCount RETURN sp.specNumber, crCount, crList[..10] AS sampleCRs
```

**Revised query**

```cypher
MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(:Spec {specNumber:'38.214'}) WITH DISTINCT cr.tdocNumber AS doc ORDER BY doc ASC WITH collect(doc) AS docs RETURN size(docs) AS crCount,docs[..10] AS sampleCRs
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "sampleCRs",
      "nested_array_semantics": {
        "$": "sequence"
      },
      "nested_collection_definition": {
        "duplicates": "disallowed",
        "element_type": "string",
        "kind": "sequence",
        "order": "ascending lexicographic identifier"
      },
      "nullable": false,
      "source_column_or_expression": "sampleCRs",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one aggregate record; sample array length at most ten",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ2-3/7858a55d0b9e3a0344c75c9882b935076b2d01ce43a8c7f0a55ece8a1bc6c29f.json), [complete native rows](../reference_outputs/RAN1_P4_CQ2-3/7858a55d0b9e3a0344c75c9882b935076b2d01ce43a8c7f0a55ece8a1bc6c29f.jsonl); 1 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `8c9b9a24c11a07c0c4223adbe2dfac835af98332751e4c962948aa6fc9f7d4d3`.

## RAN1_P4_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which 10 CRs have the widest cross-spec reach, and which specs does each affect?

**Revised question:** Among all recorded CR-identifier groups, return the ten with the greatest number of distinct specification-number strings reached through AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC, including zero-count groups. Return CR identifier, count and the set of these specification-number strings; do not exclude directly MODIFIES-linked specification numbers. Rank count descending then CR identifier ascending, returning all available groups if fewer than ten exist.

**Proposed rationale:** Count Spec numbers rather than version nodes so the count equals the cardinality of the reported target set. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, count(DISTINCT sp) AS affectedSpecCount, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC, cr.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR) OPTIONAL MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber,count(DISTINCT sp.specNumber) AS affectedSpecCount,collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC,cr.tdocNumber ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "cr.tdocNumber",
      "nullable": true,
      "source_column_or_expression": "cr.tdocNumber",
      "type": "string"
    },
    {
      "name": "affectedSpecCount",
      "nullable": false,
      "source_column_or_expression": "affectedSpecCount",
      "type": "integer"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "affectedSpecs",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "kind": "set"
      },
      "nullable": false,
      "source_column_or_expression": "affectedSpecs",
      "type": "json"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "affectedSpecCount"
      },
      {
        "direction": "asc",
        "field": "cr.tdocNumber"
      }
    ],
    "tie_policy": "CR identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.",
    "short_population": "all_available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ2-4/5f6236e91e76317f5b97c778366fc70e453d1f88949bdf06aa61a99a41140093.json), [complete native rows](../reference_outputs/RAN1_P4_CQ2-4/5f6236e91e76317f5b97c778366fc70e453d1f88949bdf06aa61a99a41140093.jsonl); 10 native rows retained. The retained per-item check record has 12 passing scorer checks for this definition.

**Definition SHA-256:** `fc47f33dcaee7799497433ca26dc06c6f3a7b42aa62c331ab5ef8b58a1b457fc`.

## RAN1_P4_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The observed tsgMeeting values are null; do not claim plenary submission timing. Pack identity and distinct membership are graph-supported.']

**Original question:** Into which CR packs were the CRs of Work Item NR_newRAT-Core (initial NR spec) bundled for TSG submission?

**Revised question:** For every CRPack linked by BELONGS_TO_CR_PACK from a CR RELATED_TO NR_newRAT-Core, return the pack identifier and count of distinct such CR nodes.

**Proposed rationale:** The observed tsgMeeting values are null; do not claim plenary submission timing. Pack identity and distinct membership are graph-supported.

**Original query**

```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(cr) AS crCount ORDER BY pack.tsgMeeting DESC, crCount DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "pack.crPackId",
      "nullable": true,
      "source_column_or_expression": "pack.crPackId",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ3-2/09d0488d6b697007fa44fc69ffece02cba7a2a4c80a5c94eb2b556bcb4f448b4.json), [complete native rows](../reference_outputs/RAN1_P4_CQ3-2/09d0488d6b697007fa44fc69ffece02cba7a2a4c80a5c94eb2b556bcb4f448b4.jsonl); 66 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `edb8562a7dbb869e229c8b01df8aa34ebf757b7120108e8774af9f0587531a13`.

## RAN1_P4_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CR packs submitted to plenary RAN#109 and the CR count in each.

**Revised question:** List all CRPack identifiers with recorded tsgMeeting=RAN#109 and their numbers of distinct HAS_CR-linked CR nodes.

**Proposed rationale:** Recorded pack/meeting metadata is the scope; count distinct documents.

**Original query**

```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(cr) AS crCount ORDER BY crCount DESC
```

**Revised query**

```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "pack.crPackId",
      "nullable": true,
      "source_column_or_expression": "pack.crPackId",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P4_CQ3-3/c2d9331ee287d9cd74aa9d16c9f60201bf2ec1f8b8d638ad79d4e533991f9ef3.json), [complete native rows](../reference_outputs/RAN1_P4_CQ3-3/c2d9331ee287d9cd74aa9d16c9f60201bf2ec1f8b8d638ad79d4e533991f9ef3.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f9305c1e65e26d04662c421479ac3fdfc5cc9bca2ac42f278b2277985d8100c7`.

## RAN1_P5_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs still in Draft and the technologies they study (anticipating future standard impact).

**Revised question:** List all TechnicalReport number/title/scope records having recorded trStatus=Draft.

**Proposed rationale:** Preserve documentary study description and recorded status; no independently predicted future impact.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trNumber",
      "nullable": true,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "tr.trTitle",
      "nullable": true,
      "source_column_or_expression": "tr.trTitle",
      "type": "string"
    },
    {
      "name": "tr.scope",
      "nullable": true,
      "source_column_or_expression": "tr.scope",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ1-3/53c8dea554d35ce69d73598457f5e5b52f1b8044f3e15bca88a0fa6b56521038.json), [complete native rows](../reference_outputs/RAN1_P5_CQ1-3/53c8dea554d35ce69d73598457f5e5b52f1b8044f3e15bca88a0fa6b56521038.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `25f5bcd33eea65879dda196fd267b1764a9c6468b67b82c07b1e97924ebc4c79`.

## RAN1_P5_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Restrict to NewTS rather than treating every impact as creation, and distinguish missing recorded links from proof of no historical new TS.']

**Original question:** Did the Ambient IoT study (TR 38.769) create any new TS? If so, which TS and what impact type?

**Revised question:** List the Spec-number/impact-type pairs linked from TR 38.769 through HAS_TR_IMPACT and IMPACTS_SPEC when impactType=NewTS; an empty set means no such recorded link.

**Proposed rationale:** Restrict to NewTS rather than treating every impact as creation, and distinguish missing recorded links from proof of no historical new TS.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.769'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, tr.trTitle, ti.impactType, sp.specNumber, ti.impactDescription
```

**Revised query**

```cypher
MATCH (:TechnicalReport {trNumber:'38.769'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType:'NewTS'})-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT sp.specNumber,ti.impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "ti.impactType",
      "nullable": true,
      "source_column_or_expression": "ti.impactType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ2-1/b3cbdd29ecd65612e4a93aba631559531163f146da43187ff009df7d5be60f0a.json), [complete native rows](../reference_outputs/RAN1_P5_CQ2-1/b3cbdd29ecd65612e4a93aba631559531163f146da43187ff009df7d5be60f0a.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `030ddd7e63112f9178f7bb24a9906d8e36db061f6d9bd2aadefed6895c262c11`.

## RAN1_P5_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original query omits the question-specified target-TS restriction. Add it; reported NewSection is documentary metadata.']

**Original question:** Which new sections did the NR-U study (TR 38.889) add to TS 38.211-38.214? (PHY-layer reference)

**Revised question:** List all distinct Section identifiers linked from TR 38.889 through a NewSection impact to a Section BELONGS_TO_SPEC one of TS 38.211, 38.212, 38.213 or 38.214.

**Proposed rationale:** The original query omits the question-specified target-TS restriction. Add it; reported NewSection is documentary metadata.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.889'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
```

**Revised query**

```cypher
MATCH (:TechnicalReport {trNumber:'38.889'})-[:HAS_TR_IMPACT]->(:TRImpact {impactType:'NewSection'})-[:IMPACTS_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214'] RETURN DISTINCT s.sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.sectionId",
      "nullable": true,
      "source_column_or_expression": "s.sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ2-2/a992cd3e78af748a303ba868185367b116ab9a86fa1f6393723e3ba4388c2028.json), [complete native rows](../reference_outputs/RAN1_P5_CQ2-2/a992cd3e78af748a303ba868185367b116ab9a86fa1f6393723e3ba4388c2028.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ae89275cf0a318b887975e0dd5c99c7b5f0e706b8c3c33b8d1870a3db8ddbf49`.

## RAN1_P5_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Grade report identity and impact role together; recorded linkage is not an independent causal conclusion.']

**Original question:** List every TR that affected TS 38.211 and its impact type (revision history of 38.211).

**Revised question:** List every distinct TR-number/impact-type pair connected to TS 38.211 by HAS_TR_IMPACT and IMPACTS_SPEC.

**Proposed rationale:** Grade report identity and impact role together; recorded linkage is not an independent causal conclusion.

**Original query**

```cypher
MATCH (sp:Spec {specNumber: '38.211'})<-[:IMPACTS_SPEC]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (sp:Spec {specNumber: '38.211'})<-[:IMPACTS_SPEC]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN DISTINCT tr.trNumber, tr.trTitle, ti.impactType, ti.affectedSection, ti.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trNumber",
      "nullable": true,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "ti.impactType",
      "nullable": true,
      "source_column_or_expression": "ti.impactType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ2-3/8617983d90a5267c225e2c0dc9719f0f29c6a86bb05a0e9d53e3c2ec76a1d99c.json), [complete native rows](../reference_outputs/RAN1_P5_CQ2-3/8617983d90a5267c225e2c0dc9719f0f29c6a86bb05a0e9d53e3c2ec76a1d99c.jsonl); 11 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `28042380fa54330a4dc8bdd19110c53ceb36aa9051fd44f9b406dd2b7eb2a5b6`.

## RAN1_P5_CQ2-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Original query selects Rel-19 while question omits release and asks causal origin. State precise documentary target/version.']

**Original question:** Which TR study did TS 38.211 Section 8 (Sidelink) originate from?

**Revised question:** List all distinct TR numbers linked through recorded TRImpact nodes to Section identifier 38.211-Rel-19-8.

**Proposed rationale:** Original query selects Rel-19 while question omits release and asks causal origin. State precise documentary target/version.

**Original query**

```cypher
MATCH (s:Section {sectionId: '38.211-Rel-19-8'})<-[:IMPACTS_SECTION]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ti.impactType, ti.impactDescription
```

**Revised query**

```cypher
MATCH (s:Section {sectionId: '38.211-Rel-19-8'})<-[:IMPACTS_SECTION]-(ti:TRImpact)<-[:HAS_TR_IMPACT]-(tr:TechnicalReport) RETURN DISTINCT tr.trNumber, tr.trTitle, ti.impactType, ti.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trNumber",
      "nullable": true,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ2-4/d208107655a5a83da5e543a2904c810903be5191f90c45d91956bf19de32549a.json), [complete native rows](../reference_outputs/RAN1_P5_CQ2-4/d208107655a5a83da5e543a2904c810903be5191f90c45d91956bf19de32549a.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `552ae69202d27e90e2865777ff14eb58e9fa6c911d5151c430cbe898750c71fb`.

## RAN1_P5_CQ2-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Recorded NewTS link replaces independently established historical creation.']

**Original question:** List the TR studies that spawned an entirely new TS, with the resulting TS number (origins of new specs).

**Revised question:** List all distinct TR-number/Spec-number pairs linked by HAS_TR_IMPACT through an impact with type NewTS to IMPACTS_SPEC.

**Proposed rationale:** Recorded NewTS link replaces independently established historical creation.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, sp.specNumber, ti.impactDescription ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, sp.specNumber, ti.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trNumber",
      "nullable": true,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ2-5/bfc462709fa33605e796d32b22b7ae086ebe6c7aa293273af01ffe76e5767a2c.json), [complete native rows](../reference_outputs/RAN1_P5_CQ2-5/bfc462709fa33605e796d32b22b7ae086ebe6c7aa293273af01ffe76e5767a2c.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `9dc603f88ec935b49a4773805cd919551f27f06d7d253680a4ec1200ecec7c34`.

## RAN1_P5_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Use the actual traceability relation without independent causal impact certification.']

**Original question:** Which TS sections did the RedCap (Reduced Capability) study TR 38.875 affect? (low-power IoT reference)

**Revised question:** List every distinct Section identifier linked from TR 38.875 through HAS_TR_IMPACT and IMPACTS_SECTION.

**Proposed rationale:** Use the actual traceability relation without independent causal impact certification.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.875'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, tr.trTitle, ti.impactType, s.sectionId, ti.impactDescription ORDER BY s.sectionId
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.875'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SECTION]->(s:Section) RETURN DISTINCT tr.trNumber, tr.trTitle, ti.impactType, s.sectionId, ti.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.sectionId",
      "nullable": true,
      "source_column_or_expression": "s.sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ3-1/ba60c719133b279bfa7c8d6e9ea4c3ddd3df1a9cf7ddc98aa77b3ddfbc5e5296.json), [complete native rows](../reference_outputs/RAN1_P5_CQ3-1/ba60c719133b279bfa7c8d6e9ea4c3ddd3df1a9cf7ddc98aa77b3ddfbc5e5296.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e87af306036536a6041b1ffcb951339838cb538054bed706ff17d28fb371987c`.

## RAN1_P5_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Enforce the target-TS restriction stated by the question but omitted in the query; new-section status remains recorded metadata.']

**Original question:** Which new sections did the LP-WUS (Low-Power Wake-Up Signal) study TR 38.869 add to TS 38.211 and 38.213? (UE power-saving implementation)

**Revised question:** List all distinct Section identifiers connected from TR 38.869 through a NewSection impact and BELONGS_TO_SPEC TS 38.211 or 38.213.

**Proposed rationale:** Enforce the target-TS restriction stated by the question but omitted in the query; new-section status remains recorded metadata.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.869'})-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewSection'})-[:IMPACTS_SECTION]->(s:Section) RETURN tr.trNumber, ti.affectedSection, s.sectionId, ti.impactDescription ORDER BY s.sectionId
```

**Revised query**

```cypher
MATCH (:TechnicalReport {trNumber:'38.869'})-[:HAS_TR_IMPACT]->(:TRImpact {impactType:'NewSection'})-[:IMPACTS_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.213'] RETURN DISTINCT s.sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.sectionId",
      "nullable": true,
      "source_column_or_expression": "s.sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ3-2/fcc14f6839246479c8eeb4a5aa5ff3105626ba700e3a2c78fda6889364d9522c.json), [complete native rows](../reference_outputs/RAN1_P5_CQ3-2/fcc14f6839246479c8eeb4a5aa5ff3105626ba700e3a2c78fda6889364d9522c.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9f5f42cf48cfae41b94e99af692e4cf74cc293978ea5e2aa104cc35805466411`.

## RAN1_P5_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Enforce the explicitly requested target Specs; do not infer independent causal truth from impact descriptions.']

**Original question:** What impact did the URLLC study TR 38.824 have on TS 38.211 and 38.214, in detail? (low-latency industrial comms)

**Revised question:** Return distinct Spec-number/impact-type/affected-section-literal/description records connected from TR 38.824 to TS 38.211 or TS 38.214 through recorded TRImpact nodes.

**Proposed rationale:** Enforce the explicitly requested target Specs; do not infer independent causal truth from impact descriptions.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.824'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, sp.specNumber, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY sp.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.824'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.214'] RETURN DISTINCT tr.trNumber, sp.specNumber, ti.impactType, ti.affectedSection, ti.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    },
    {
      "name": "ti.impactType",
      "nullable": true,
      "source_column_or_expression": "ti.impactType",
      "type": "string"
    },
    {
      "name": "ti.affectedSection",
      "nullable": true,
      "source_column_or_expression": "ti.affectedSection",
      "type": "string"
    },
    {
      "name": "ti.impactDescription",
      "nullable": true,
      "source_column_or_expression": "ti.impactDescription",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ3-3/cdcb130438c12034c5c18a62f4055ff00ccaf7d95238e6f5b661faefeed806a8.json), [complete native rows](../reference_outputs/RAN1_P5_CQ3-3/cdcb130438c12034c5c18a62f4055ff00ccaf7d95238e6f5b661faefeed806a8.jsonl); 2 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `0998b20d56dacf282b0cd666e1907cc1b99cf365d55839478e10b5a0065707d6`.

## RAN1_P5_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Optional missing impacts remain explicit nulls, not proof of no real-world impact.']

**Original question:** List the TR studies targeting Rel-18 and the type of impact each had on the TSs.

**Revised question:** For every TechnicalReport TARGET_RELEASE-linked to Rel-18, return TR number and each recorded IMPACTS_SPEC target/impact-type pair, with null target/type when no such impact is linked.

**Proposed rationale:** Optional missing impacts remain explicit nulls, not proof of no real-world impact.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, tr.trStatus, ti.impactType, sp.specNumber ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, tr.trStatus, ti.impactType, sp.specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trNumber",
      "nullable": true,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "ti.impactType",
      "nullable": true,
      "source_column_or_expression": "ti.impactType",
      "type": "string"
    },
    {
      "name": "sp.specNumber",
      "nullable": true,
      "source_column_or_expression": "sp.specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ4-1/75f0206a0f2960bd1bbb0bc98ce1329ec6142975f151a73a032b3e975cf09e55.json), [complete native rows](../reference_outputs/RAN1_P5_CQ4-1/75f0206a0f2960bd1bbb0bc98ce1329ec6142975f151a73a032b3e975cf09e55.jsonl); 7 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `d90a536f1c4e4ba40bd238d72ded31afd5b0d0e74916f890c1e76b94ce46a2e0`.

## RAN1_P5_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Current status is not established by an unfiltered version query; define the frozen graph record scope and grade only requested fields.']

**Original question:** Return the current status and scope of the 6G Radio study TR 38.760-1 (next-generation roadmap review).

**Revised question:** For all recorded versions of TR 38.760-1, return each distinct pair of recorded status and scope.

**Proposed rationale:** Current status is not established by an unfiltered version query; define the frozen graph record scope and grade only requested fields.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN DISTINCT tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tr.trStatus",
      "nullable": true,
      "source_column_or_expression": "tr.trStatus",
      "type": "string"
    },
    {
      "name": "tr.scope",
      "nullable": true,
      "source_column_or_expression": "tr.scope",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ4-2/018f0a6ae03867588db9b9749095f31befb3ea0b4a103f3db2ca69a17c4da900.json), [complete native rows](../reference_outputs/RAN1_P5_CQ4-2/018f0a6ae03867588db9b9749095f31befb3ea0b4a103f3db2ca69a17c4da900.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `7243f925ea4e8e305dee9acb0585a50690526d309b74e442629a978bcbfe1d0d`.

## RAN1_P5_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other TRs referenced by TR 38.859 (Ambient IoT for NR) (surveying related studies).

**Revised question:** List the distinct TR numbers reached by outgoing REFERENCES_TR links from TR 38.859, excluding 38.859 itself.

**Proposed rationale:** Grade target TR membership without unrequested source/title fields; require other TR numbers explicitly.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.859'})-[:REFERENCES_TR]->(ref:TechnicalReport) RETURN tr.trNumber, tr.trTitle, ref.trNumber, ref.trTitle ORDER BY ref.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.859'})-[:REFERENCES_TR]->(ref:TechnicalReport) WHERE ref.trNumber <> tr.trNumber RETURN DISTINCT tr.trNumber, tr.trTitle, ref.trNumber, ref.trTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "ref.trNumber",
      "nullable": true,
      "source_column_or_expression": "ref.trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ5-1/f31962daad4f02505a87c3591e310d2c49e6276693734df98afafe83fff499ec.json), [complete native rows](../reference_outputs/RAN1_P5_CQ5-1/f31962daad4f02505a87c3591e310d2c49e6276693734df98afafe83fff499ec.jsonl); 6 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0c5ac8dd24a26abe9fee706021da5955d87fac8a5a11c1db6c46cf8821c648e9`.

## RAN1_P5_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs that reference TR 38.802 (RedCap) (reverse lookup, tracing follow-on studies).

**Revised question:** List the distinct TR numbers with an outgoing REFERENCES_TR link to TR 38.802.

**Proposed rationale:** Grade reverse documentary reference membership without interpreting a link as a follow-on historical relationship.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.802'})<-[:REFERENCES_TR]-(src:TechnicalReport) RETURN tr.trNumber, tr.trTitle, src.trNumber, src.trTitle ORDER BY src.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.802'})<-[:REFERENCES_TR]-(src:TechnicalReport) RETURN DISTINCT tr.trNumber, tr.trTitle, src.trNumber, src.trTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "src.trNumber",
      "nullable": true,
      "source_column_or_expression": "src.trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ5-2/682638af05ecc8dd3fca5baed622ad814d52c625be193d694bffa8426e6b940b.json), [complete native rows](../reference_outputs/RAN1_P5_CQ5-2/682638af05ecc8dd3fca5baed622ad814d52c625be193d694bffa8426e6b940b.jsonl); 4 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0a365f4766c875de1c31a28413f37f19bb3785d000777d5111fbd835de68dcae`.

## RAN1_P5_CQ5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which are the top 5 most-referenced TRs? (identifying foundational studies)

**Revised question:** Return the top five recorded TR numbers by number of distinct referencing TR numbers, including zero-reference TRs. Rank by count descending and TR number ascending; return each number and its count.

**Proposed rationale:** Specify TR-number rather than graph-version node counting, include the full population, and resolve ties deterministically; reference counts do not establish foundational significance.

**Original query**

```cypher
MATCH (ref:TechnicalReport)<-[:REFERENCES_TR]-(src:TechnicalReport) WITH ref, count(src) AS refCount ORDER BY refCount DESC, ref.trNumber LIMIT 5 RETURN ref.trNumber, ref.trTitle, refCount
```

**Revised query**

```cypher
MATCH (ref:TechnicalReport) OPTIONAL MATCH (src:TechnicalReport)-[:REFERENCES_TR]->(ref) WITH ref.trNumber AS trNumber, count(DISTINCT src.trNumber) AS referenceCount RETURN trNumber, referenceCount ORDER BY referenceCount DESC, trNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": true,
      "source_column_or_expression": "trNumber",
      "type": "string"
    },
    {
      "name": "referenceCount",
      "nullable": false,
      "source_column_or_expression": "referenceCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referenceCount"
      },
      {
        "direction": "asc",
        "field": "trNumber"
      }
    ],
    "tie_policy": "TR number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five TR-number groups, or all groups when fewer than five exist",
    "tie_policy": "TR number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN1_P5_CQ5-3/ed5798c88eb8b9e0f84dd396437c3e5b97130ba57b037ddc7fc6784156d63e9e.json), [complete native rows](../reference_outputs/RAN1_P5_CQ5-3/ed5798c88eb8b9e0f84dd396437c3e5b97130ba57b037ddc7fc6784156d63e9e.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8eaaef7941c30b91887dd80044c2e2b5bda410635cc53c94bd31f0d4d27b6252`.
