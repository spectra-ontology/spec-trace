# RAN2 itemized contract changes

This page accounts for 114 original Core IDs: 76 proposed clarifications and 38 substantive variants.

Each entry retains the exact original and revised question and query. The change rationale is a proposal, not a completed author semantic judgment. Technical check counts concern scorer enforcement and captured reference consistency; all author semantic reviews remain pending.

[Review guide](../REVIEW_GUIDE.md) · [Full technical task ledger](../canonical_tasks.jsonl) · [Per-item scorer checks](../provenance/adversarial_validation.json)

| ID | Proposed change class | Required fields | Native rows | Scorer checks |
| --- | --- | --- | ---: | ---: |
| [RAN2_P1_CQ1-1](#ran2_p1_cq1-1) | Proposed clarification | t.tdocNumber (string) | 24 | 7/7 |
| [RAN2_P1_CQ1-2](#ran2_p1_cq1-2) | Proposed clarification | t.tdocNumber (string) | 28 | 7/7 |
| [RAN2_P1_CQ1-3](#ran2_p1_cq1-3) | Proposed clarification | t.tdocNumber (string) | 148 | 7/7 |
| [RAN2_P1_CQ1-4](#ran2_p1_cq1-4) | Substantive variant | t.tdocNumber (string), m.canonicalMeetingNumber (string), m.meetingNumberInt (integer) | 10 | 13/13 |
| [RAN2_P1_CQ1-5](#ran2_p1_cq1-5) | Proposed clarification | t.tdocNumber (string) | 251 | 7/7 |
| [RAN2_P1_CQ1-6](#ran2_p1_cq1-6) | Substantive variant | t.status (string) | 1 | 7/7 |
| [RAN2_P1_CQ1-7](#ran2_p1_cq1-7) | Proposed clarification | t.`for` (string) | 1 | 7/7 |
| [RAN2_P1_CQ1-8](#ran2_p1_cq1-8) | Proposed clarification | c.contactName (string), c.contactId (string) | 1 | 10/10 |
| [RAN2_P1_CQ1-9](#ran2_p1_cq1-9) | Substantive variant | a.agendaNumber (string), a.agendaDescription (string) | 94 | 10/10 |
| [RAN2_P1_CQ2-1](#ran2_p1_cq2-1) | Proposed clarification | previousVersion (string), nextVersion (string) | 1 | 10/10 |
| [RAN2_P1_CQ2-3](#ran2_p1_cq2-3) | Substantive variant | t.tdocNumber (string), replyTarget (string) | 0 | 3/3 |
| [RAN2_P1_CQ2-4](#ran2_p1_cq2-4) | Proposed clarification | s.specNumber (string), s.specVersion (string) | 1 | 10/10 |
| [RAN2_P1_CQ2-5](#ran2_p1_cq2-5) | Proposed clarification | t.crCategory (string), t.clausesAffected (string), t.affectsUICC (boolean), t.affectsME (boolean), t.affectsRAN (boolean), t.affectsCN (boolean) | 1 | 18/18 |
| [RAN2_P1_CQ2-6](#ran2_p1_cq2-6) | Substantive variant | t.tdocNumber (string) | 9 | 7/7 |
| [RAN2_P1_CQ2-7](#ran2_p1_cq2-7) | Proposed clarification | t.tdocNumber (string), a.agendaNumber (string) | 37 | 10/10 |
| [RAN2_P1_CQ3-1](#ran2_p1_cq3-1) | Proposed clarification | t.tdocNumber (string) | 3,739 | 7/7 |
| [RAN2_P1_CQ3-2](#ran2_p1_cq3-2) | Proposed clarification | c.companyName (string), t.tdocNumber (string) | 65 | 10/10 |
| [RAN2_P1_CQ3-3](#ran2_p1_cq3-3) | Proposed clarification | c.companyName (string), contributions (integer) | 123 | 10/10 |
| [RAN2_P1_CQ3-5](#ran2_p1_cq3-5) | Proposed clarification | c.companyName (string), t.tdocNumber (string) | 5 | 10/10 |
| [RAN2_P1_CQ3-6](#ran2_p1_cq3-6) | Proposed clarification | wi.workItemCode (string), contributions (integer) | 306 | 10/10 |
| [RAN2_P1_CQ4-1](#ran2_p1_cq4-1) | Substantive variant | t.tdocNumber (string), m.canonicalMeetingNumber (string) | 64 | 10/10 |
| [RAN2_P1_CQ4-2](#ran2_p1_cq4-2) | Proposed clarification | t.status (string), count (integer) | 10 | 10/10 |
| [RAN2_P1_CQ4-3](#ran2_p1_cq4-3) | Proposed clarification | t.tdocNumber (string) | 100 | 7/7 |
| [RAN2_P2_CQ1-1](#ran2_p2_cq1-1) | Proposed clarification | a.resolutionId (string), a.content (string) | 96 | 10/10 |
| [RAN2_P2_CQ1-10](#ran2_p2_cq1-10) | Proposed clarification | type (string), cnt (integer) | 2 | 10/10 |
| [RAN2_P2_CQ1-2](#ran2_p2_cq1-2) | Proposed clarification | c.resolutionId (string), c.content (string) | 1 | 10/10 |
| [RAN2_P2_CQ1-3](#ran2_p2_cq1-3) | Proposed clarification | wa.resolutionId (string), wa.content (string) | 11 | 10/10 |
| [RAN2_P2_CQ1-4](#ran2_p2_cq1-4) | Proposed clarification | r.resolutionId (string), type (json), r.content (string) | 35 | 12/12 |
| [RAN2_P2_CQ1-5](#ran2_p2_cq1-5) | Substantive variant | r.resolutionId (string), r.content (string) | 306 | 10/10 |
| [RAN2_P2_CQ1-6](#ran2_p2_cq1-6) | Substantive variant | r.resolutionId (string), r.content (string) | 233 | 10/10 |
| [RAN2_P2_CQ1-7](#ran2_p2_cq1-7) | Substantive variant | workItemId (string), r.resolutionId (string) | 2,144 | 10/10 |
| [RAN2_P2_CQ1-8](#ran2_p2_cq1-8) | Proposed clarification | ai.agendaNumber (string), ai.meetingNumber (string), resolutionCount (integer) | 10 | 13/13 |
| [RAN2_P2_CQ2-1](#ran2_p2_cq2-1) | Substantive variant | r.resolutionId (string), r.content (string) | 2 | 10/10 |
| [RAN2_P2_CQ2-2](#ran2_p2_cq2-2) | Proposed clarification | t.tdocNumber (string) | 2 | 7/7 |
| [RAN2_P2_CQ2-3](#ran2_p2_cq2-3) | Substantive variant | a.resolutionId (string), a.content (string) | 25 | 10/10 |
| [RAN2_P2_CQ2-4](#ran2_p2_cq2-4) | Substantive variant | sp.specNumber (string) | 11 | 7/7 |
| [RAN2_P2_CQ2-5](#ran2_p2_cq2-5) | Substantive variant | r.resolutionId (string), r.content (string) | 1 | 10/10 |
| [RAN2_P2_CQ2-6](#ran2_p2_cq2-6) | Substantive variant | a.resolutionId (string), a.content (string) | 1,135 | 10/10 |
| [RAN2_P2_CQ3-1](#ran2_p2_cq3-1) | Substantive variant | totalTdocs (integer), resolvedTdocs (integer), ratio (number) | 1 | 13/13 |
| [RAN2_P2_CQ3-2](#ran2_p2_cq3-2) | Substantive variant | c.companyName (string), contributions (integer) | 62 | 10/10 |
| [RAN2_P2_CQ3-3](#ran2_p2_cq3-3) | Substantive variant | workItemCode (string), topCompanies (json) | 223 | 9/9 |
| [RAN2_P2_CQ3-5](#ran2_p2_cq3-5) | Proposed clarification | companyName (string), tdocCount (integer) | 10 | 10/10 |
| [RAN2_P2_CQ6-1](#ran2_p2_cq6-1) | Proposed clarification | meetingNumber (string), meetingNumberInt (integer), resCount (integer) | 58 | 13/13 |
| [RAN2_P2_CQ6-2](#ran2_p2_cq6-2) | Substantive variant | meetingNumber (string), meetingNumberInt (integer), huaweiCount (integer), total (integer), ratio (number) | 58 | 19/19 |
| [RAN2_P2_CQ6-3](#ran2_p2_cq6-3) | Proposed clarification | meetingNumber (string), meetingNumberInt (integer), agrCount (integer) | 58 | 13/13 |
| [RAN2_P2_CQ6-4](#ran2_p2_cq6-4) | Proposed clarification | meetingNumber (string), meetingNumberInt (integer), conCount (integer) | 58 | 13/13 |
| [RAN2_P3_CQ1-1](#ran2_p3_cq1-1) | Proposed clarification | s.sectionId (string), s.sectionNumber (string), s.sectionTitle (string) | 5,834 | 13/13 |
| [RAN2_P3_CQ1-10](#ran2_p3_cq1-10) | Proposed clarification | sp.specNumber (string), s.sectionId (string), t.tableId (string) | 5 | 13/13 |
| [RAN2_P3_CQ1-11](#ran2_p3_cq1-11) | Proposed clarification | sp.specNumber (string), sectionCount (integer) | 5 | 10/10 |
| [RAN2_P3_CQ1-12](#ran2_p3_cq1-12) | Proposed clarification | s.level (integer), cnt (integer) | 7 | 10/10 |
| [RAN2_P3_CQ1-13](#ran2_p3_cq1-13) | Proposed clarification | s.sectionId (string), s.sectionTitle (string) | 167 | 10/10 |
| [RAN2_P3_CQ1-14](#ran2_p3_cq1-14) | Proposed clarification | secCnt (integer), tblCnt (integer), figCnt (integer) | 1 | 13/13 |
| [RAN2_P3_CQ1-15](#ran2_p3_cq1-15) | Proposed clarification | s.sectionId (string), tableCount (integer) | 5 | 10/10 |
| [RAN2_P3_CQ1-16](#ran2_p3_cq1-16) | Proposed clarification | s.sectionId (string), figCount (integer) | 5 | 10/10 |
| [RAN2_P3_CQ1-2](#ran2_p3_cq1-2) | Substantive variant | parentSectionId (string), childSectionId (string), childSectionNumber (string), childSectionTitle (string) | 155 | 16/16 |
| [RAN2_P3_CQ1-4](#ran2_p3_cq1-4) | Proposed clarification | s.sectionId (string), s.sectionNumber (string), s.sectionTitle (string) | 40 | 13/13 |
| [RAN2_P3_CQ1-5](#ran2_p3_cq1-5) | Substantive variant | sectionId (string), tableId (string), tableNumber (string), tableCaption (string) | 31 | 16/16 |
| [RAN2_P3_CQ1-6](#ran2_p3_cq1-6) | Substantive variant | sectionId (string), figureId (string), figureNumber (string), figureCaption (string) | 18 | 16/16 |
| [RAN2_P3_CQ1-7](#ran2_p3_cq1-7) | Proposed clarification | t.tableId (string), s.sectionId (string) | 5 | 10/10 |
| [RAN2_P3_CQ1-8](#ran2_p3_cq1-8) | Proposed clarification | t.tableId (string), t.tableNumber (string), t.tableCaption (string) | 24 | 13/13 |
| [RAN2_P3_CQ1-9](#ran2_p3_cq1-9) | Proposed clarification | s.sectionId (string), s.sectionTitle (string) | 484 | 10/10 |
| [RAN2_P3_CQ2-1](#ran2_p3_cq2-1) | Substantive variant | sourceSectionId (string), targetSectionId (string) | 65 | 10/10 |
| [RAN2_P3_CQ2-2](#ran2_p3_cq2-2) | Substantive variant | sourceSectionId (string), targetSectionId (string) | 54 | 10/10 |
| [RAN2_P3_CQ2-3](#ran2_p3_cq2-3) | Proposed clarification | sectionId (string), refs (integer) | 1 | 10/10 |
| [RAN2_P3_CQ2-4](#ran2_p3_cq2-4) | Proposed clarification | s.sectionId (string), refCount (integer) | 10 | 10/10 |
| [RAN2_P3_CQ2-5](#ran2_p3_cq2-5) | Proposed clarification | from_section (string), to_section (string) | 2 | 10/10 |
| [RAN2_P3_CQ2-6](#ran2_p3_cq2-6) | Proposed clarification | totalRefs (integer) | 1 | 7/7 |
| [RAN2_P3_CQ2-7](#ran2_p3_cq2-7) | Proposed clarification | specNumber (string), intraRefs (integer) | 5 | 10/10 |
| [RAN2_P3_CQ2-8](#ran2_p3_cq2-8) | Proposed clarification | s2.sectionId (string), refCount (integer) | 5 | 10/10 |
| [RAN2_P3_CQ3-1](#ran2_p3_cq3-1) | Proposed clarification | sp.specNumber (string) | 1 | 7/7 |
| [RAN2_P3_CQ3-2](#ran2_p3_cq3-2) | Substantive variant | sectionId (string), sectionNumber (string), sectionTitle (string) | 133 | 13/13 |
| [RAN2_P3_CQ3-3](#ran2_p3_cq3-3) | Proposed clarification | cr.tdocNumber (string) | 10,599 | 7/7 |
| [RAN2_P3_CQ3-4](#ran2_p3_cq3-4) | Proposed clarification | cr.tdocNumber (string), cr.clausesAffected (string) | 3,855 | 10/10 |
| [RAN2_P3_CQ3-5](#ran2_p3_cq3-5) | Proposed clarification | sp.specNumber (string) | 23 | 7/7 |
| [RAN2_P3_CQ3-6](#ran2_p3_cq3-6) | Proposed clarification | sp.specNumber (string) | 53 | 7/7 |
| [RAN2_P3_CQ3-7](#ran2_p3_cq3-7) | Substantive variant | cr.tdocNumber (string), clause (string), s.sectionId (string) | 16,297 | 13/13 |
| [RAN2_P3_CQ3-8](#ran2_p3_cq3-8) | Proposed clarification | sp.specNumber (string), crCnt (integer) | 5 | 10/10 |
| [RAN2_P3_CQ4-1](#ran2_p3_cq4-1) | Substantive variant | sp.specNumber (string) | 34 | 7/7 |
| [RAN2_P3_CQ4-2](#ran2_p3_cq4-2) | Substantive variant | r.resolutionId (string), cr.tdocNumber (string) | 857 | 10/10 |
| [RAN2_P3_CQ4-3](#ran2_p3_cq4-3) | Substantive variant | resolutionId (string), tdocNumber (string), specNumber (string), clause (string), sectionId (string) | 1,833 | 19/19 |
| [RAN2_P3_CQ4-4](#ran2_p3_cq4-4) | Substantive variant | sp.specNumber (string), resolutions (integer), crs (integer) | 5 | 13/13 |
| [RAN2_P3_CQ5-1](#ran2_p3_cq5-1) | Proposed clarification | totalCRs (integer) | 1 | 7/7 |
| [RAN2_P3_CQ5-2](#ran2_p3_cq5-2) | Proposed clarification | sp.specNumber (string), crs (integer) | 5 | 10/10 |
| [RAN2_P3_CQ5-3](#ran2_p3_cq5-3) | Substantive variant | specNumber (string), crCnt (integer), secCnt (integer), density (number) | 123 | 16/16 |
| [RAN2_P3_CQ5-4](#ran2_p3_cq5-4) | Proposed clarification | sp.specNumber (string), tblCnt (integer) | 123 | 10/10 |
| [RAN2_P3_CQ5-5](#ran2_p3_cq5-5) | Proposed clarification | sp.specNumber (string), figCnt (integer) | 123 | 10/10 |
| [RAN2_P3_P3-S8-CQ02](#ran2_p3_p3-s8-cq02) | Proposed clarification | allLinked (boolean) | 1 | 7/7 |
| [RAN2_P3_P3-S8-CQ04](#ran2_p3_p3-s8-cq04) | Substantive variant | matches (boolean) | 1 | 7/7 |
| [RAN2_P3_P3-S8-CQ05](#ran2_p3_p3-s8-cq05) | Proposed clarification | class (string), granularity (string), c (integer) | 3 | 13/13 |
| [RAN2_P3_P3-S8-CQ07](#ran2_p3_p3-s8-cq07) | Substantive variant | has28Names (boolean) | 1 | 7/7 |
| [RAN2_P4_CQ2-1](#ran2_p4_cq2-1) | Proposed clarification | spec (string) | 4 | 7/7 |
| [RAN2_P4_CQ2-2](#ran2_p4_cq2-2) | Proposed clarification | tdocNumber (string) | 340 | 7/7 |
| [RAN2_P4_CQ2-3](#ran2_p4_cq2-3) | Proposed clarification | tdocNumber (string) | 8 | 7/7 |
| [RAN2_P4_CQ2-4](#ran2_p4_cq2-4) | Proposed clarification | tdocNumber (string), cnt (integer) | 10 | 10/10 |
| [RAN2_P4_CQ3-1](#ran2_p4_cq3-1) | Proposed clarification | tdocNumber (string), summary (string) | 5 | 10/10 |
| [RAN2_P4_CQ3-2](#ran2_p4_cq3-2) | Proposed clarification | crPackId (string) | 153 | 7/7 |
| [RAN2_P4_CQ3-3](#ran2_p4_cq3-3) | Substantive variant | crPackId (string) | 26 | 7/7 |
| [RAN2_P4_CQ4-1](#ran2_p4_cq4-1) | Proposed clarification | tdocNumber (string), reason (string) | 10 | 10/10 |
| [RAN2_P4_CQ4-2](#ran2_p4_cq4-2) | Substantive variant | tdocNumber (string), reason (string), summary (string) | 162 | 13/13 |
| [RAN2_P4_CQ4-3](#ran2_p4_cq4-3) | Proposed clarification | sectionId (string) | 859 | 7/7 |
| [RAN2_P4_CQ4-4](#ran2_p4_cq4-4) | Proposed clarification | spec (string) | 23 | 7/7 |
| [RAN2_P4_CQ4-5](#ran2_p4_cq4-5) | Substantive variant | tdocNumber (string), summary (string) | 3 | 10/10 |
| [RAN2_P5_TR-CQ-1-1](#ran2_p5_tr-cq-1-1) | Proposed clarification | tr.trNumber (string) | 2 | 7/7 |
| [RAN2_P5_TR-CQ-1-4](#ran2_p5_tr-cq-1-4) | Substantive variant | tr.trNumber (string) | 1 | 7/7 |
| [RAN2_P5_TR-CQ-2-1](#ran2_p5_tr-cq-2-1) | Proposed clarification | s.specNumber (string), imp.impactType (string) | 2 | 10/10 |
| [RAN2_P5_TR-CQ-2-2](#ran2_p5_tr-cq-2-2) | Proposed clarification | imp.impactType (string), cnt (integer) | 1 | 10/10 |
| [RAN2_P5_TR-CQ-2-3](#ran2_p5_tr-cq-2-3) | Substantive variant | tr.trNumber (string) | 1 | 7/7 |
| [RAN2_P5_TR-CQ-2-4](#ran2_p5_tr-cq-2-4) | Substantive variant | tr.trNumber (string) | 6 | 7/7 |
| [RAN2_P5_TR-CQ-2-5](#ran2_p5_tr-cq-2-5) | Proposed clarification | tr.trNumber (string) | 5 | 7/7 |
| [RAN2_P5_TR-CQ-3-1](#ran2_p5_tr-cq-3-1) | Proposed clarification | s.specNumber (string), imp.impactType (string), imp.impactDescription (string) | 2 | 13/13 |
| [RAN2_P5_TR-CQ-3-2](#ran2_p5_tr-cq-3-2) | Proposed clarification | s.specNumber (string), imp.impactType (string), imp.impactDescription (string) | 2 | 13/13 |
| [RAN2_P5_TR-CQ-3-3](#ran2_p5_tr-cq-3-3) | Proposed clarification | imp.impactType (string), imp.impactDescription (string) | 1 | 10/10 |
| [RAN2_P5_TR-CQ-4-1](#ran2_p5_tr-cq-4-1) | Proposed clarification | trNumber (string), impacts (json) | 2 | 9/9 |
| [RAN2_P5_TR-CQ-4-2](#ran2_p5_tr-cq-4-2) | Proposed clarification | tr.trStatus (string), tr.scope (string) | 1 | 10/10 |

## RAN2_P1_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs at meeting RAN2#130 linked to Work Item NR_Mob_enh2-Core (mobility-enhancement meeting prep).

**Revised question:** List all distinct TDoc numbers presented at RAN2#130 and linked by RELATED_TO to NR_Mob_enh2-Core.

**Proposed rationale:** Remove the undeclared ten-row cap and grade requested TDoc identifiers only.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-1/c4c93f9687efe94f4421637559038bec1da09edf2426e0620d3f96a12ee27eb4.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-1/c4c93f9687efe94f4421637559038bec1da09edf2426e0620d3f96a12ee27eb4.jsonl); 24 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `97945f61af38af8c72c2dfcbb2986a5f75cec2c74388a0de6a6e1e46e04ceec9`.

## RAN2_P1_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs under Agenda Item 6.1.3.1 (NR RRC) at meeting RAN2#132 (RRC agenda scan).

**Revised question:** List all distinct TDoc numbers presented at RAN2#132 and linked to agenda item 6.1.3.1.

**Proposed rationale:** Remove the undeclared row cap; preserve exact agenda membership rather than adding unrequested descendants.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '6.1.3.1'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '6.1.3.1'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-2/9d296466ad3857f79a42e8cfa034811d35aae57317b23b2b73fc295f654f9377.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-2/9d296466ad3857f79a42e8cfa034811d35aae57317b23b2b73fc295f654f9377.jsonl); 28 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b97cb02dcd3b62b6f304ec16f5c82ef6745d25ecd650a212a5990f0563e4c41b`.

## RAN2_P1_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs submitted by Huawei at meeting RAN2#132 (competitor contribution review).

**Revised question:** List all distinct TDoc numbers presented at RAN2#132 with a SUBMITTED_BY link to companyName Huawei.

**Proposed rationale:** Remove the undeclared row cap and limit scoring to requested contribution membership.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-3/7899a390108eba860101c4696d2c7155e72a5d58588b934d64e1dcf9ce565cca.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-3/7899a390108eba860101c4696d2c7155e72a5d58588b934d64e1dcf9ce565cca.jsonl); 148 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `c6f470d1ef4966b1550abc06686dcb6d39a2aab57a653bce5c186959a07f68ab`.

## RAN2_P1_CQ1-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Meeting numbering is a presentation-recency proxy, not submission time; define the actual ranking unit and deterministic cap.']

**Original question:** List the most recently submitted TDocs targeting Rel-19 (latest Rel-19 activity).

**Revised question:** Return ten distinct TDoc/meeting pairs targeting Rel-19, ordered by recorded meetingNumberInt descending and TDoc number ascending, with canonical meeting number as the final tie-breaker. Return TDoc number and canonical meeting number. Also return the numeric meetingNumberInt used for ordering.

**Proposed rationale:** Meeting numbering is a presentation-recency proxy, not submission time; define the actual ranking unit and deterministic cap.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.type, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-19'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber, m.canonicalMeetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC, m.canonicalMeetingNumber ASC LIMIT 10
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
      "name": "m.canonicalMeetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.canonicalMeetingNumber",
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
        "field": "m.canonicalMeetingNumber"
      }
    ],
    "tie_policy": "TDoc number, then canonical meeting number, ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "ten presentation pairs or all pairs if fewer exist",
    "tie_policy": "TDoc number, then canonical meeting number, ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-4/c8e181e5c2d86235ebb9b41d3a4e6394bc066abcac1178fd09e715b022b13ec6.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-4/c8e181e5c2d86235ebb9b41d3a4e6394bc066abcac1178fd09e715b022b13ec6.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `3af8540f0a718306bb8b55612eeb3c9bb28e0ed1dd4b8e2c93a48321650427e3`.

## RAN2_P1_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs approved or agreed at meeting RAN2#131 (meeting outcome review).

**Revised question:** List all distinct TDoc numbers presented at RAN2#131 whose recorded status is approved or agreed.

**Proposed rationale:** Grade requested identifiers; remove an undeclared output cap without inferring final adoption.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-5/3e479fdf17dd1f0ad7787a81a5443bcb2577930cc70df6d2fcdf2202b83817d7.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-5/3e479fdf17dd1f0ad7787a81a5443bcb2577930cc70df6d2fcdf2202b83817d7.jsonl); 251 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e906b19a3dafb07958dcb8f0a2fdb311767cb11c0e5c1149d3c0654ddff75925`.

## RAN2_P1_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The graph status field does not separately certify a decision or final state; remove arbitrary first-record selection.']

**Original question:** Return the decision status of TDoc R2-2509337 (outcome lookup).

**Revised question:** Return all distinct recorded status values for TDoc number R2-2509337.

**Proposed rationale:** The graph status field does not separately certify a decision or final state; remove arbitrary first-record selection.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.status, t.type LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN DISTINCT t.tdocNumber, t.title, t.status, t.type
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-6/f6bdad3e7d184db9eefffa9db40911bbec876c8e8f306c3512b8fb89ff20dbd0.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-6/f6bdad3e7d184db9eefffa9db40911bbec876c8e8f306c3512b8fb89ff20dbd0.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `92d7b79686e5d590ce678588e99d264439a9c0813cf589825a204dad7f30c4bc`.

## RAN2_P1_CQ1-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the intended purpose (the 'For' field) of TDoc R2-2509337 (contribution intent).

**Revised question:** Return all distinct recorded For-field values for TDoc number R2-2509337.

**Proposed rationale:** Grade the requested property and avoid arbitrary selection if multiple graph records exist.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.`for` LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN DISTINCT t.tdocNumber, t.title, t.`for`
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.`for`",
      "nullable": true,
      "source_column_or_expression": "t.`for`",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-7/d5ca095714b5b1c16ee862bf9340205f4f60fddf1cc42897b3cca25f18b2805e.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-7/d5ca095714b5b1c16ee862bf9340205f4f60fddf1cc42897b3cca25f18b2805e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1135c7bcc5bc2b033cffad3f21584c80e274b143a7d375758c31df5ce2f311ba`.

## RAN2_P1_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the contact person for TDoc R2-2509337 (author follow-up).

**Revised question:** Return every distinct contact name/contact identifier pair linked by HAS_CONTACT to TDoc number R2-2509337.

**Proposed rationale:** The singular question concealed possible multiple contacts; define all contacts and remove LIMIT 1.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:HAS_CONTACT]->(c:Contact) RETURN DISTINCT t.tdocNumber, c.contactName, c.contactId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "c.contactName",
      "nullable": true,
      "source_column_or_expression": "c.contactName",
      "type": "string"
    },
    {
      "name": "c.contactId",
      "nullable": true,
      "source_column_or_expression": "c.contactId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-8/ec3969274b625fb869a82f88dac3fea23deb420b1083da3f46299561cd62f6cf.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-8/ec3969274b625fb869a82f88dac3fea23deb420b1083da3f46299561cd62f6cf.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8fa31718e7e16637110a64509cc89e461b08704734fc1dccd5c2f9ee31f7e112`.

## RAN2_P1_CQ1-9

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The documentary join cannot establish a complete official agenda, including items with no TDoc; make that scope explicit and remove the cap.']

**Original question:** List all agenda items and their descriptions for meeting RAN2#132 (agenda overview).

**Revised question:** List all distinct agenda number/description pairs linked to at least one TDoc presented at RAN2#132.

**Proposed rationale:** The documentary join cannot establish a complete official agenda, including items with no TDoc; make that scope explicit and remove the cap.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 50
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN DISTINCT a.agendaNumber, a.agendaDescription
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ1-9/b353d4eb46ad40cbd3c70cfccb5dd5630a6c1c61402ab88e0a264dcb8d7dd4ee.json), [complete native rows](../reference_outputs/RAN2_P1_CQ1-9/b353d4eb46ad40cbd3c70cfccb5dd5630a6c1c61402ab88e0a264dcb8d7dd4ee.jsonl); 94 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4a8cbc86b408c66f955e4eef631b3e6b4c5c4d7ba649fda2c83e9888f154e2b9`.

## RAN2_P1_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the predecessor and successor revisions of TDoc R2-2509478 (revision-lineage tracing).

**Revised question:** For TDoc number R2-2509478, return all distinct predecessor/successor TDoc-number pairs from IS_REVISION_OF and REVISED_TO links. Use null for a missing side; if a side has multiple links, include every joined pair.

**Proposed rationale:** Define direction, optional-link nulls, and Cartesian pair semantics instead of assuming one predecessor/successor.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509478'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN t.tdocNumber, prev.tdocNumber AS previousVersion, next.tdocNumber AS nextVersion
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509478'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN DISTINCT t.tdocNumber, prev.tdocNumber AS previousVersion, next.tdocNumber AS nextVersion
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "previousVersion",
      "nullable": true,
      "source_column_or_expression": "previousVersion",
      "type": "string"
    },
    {
      "name": "nextVersion",
      "nullable": true,
      "source_column_or_expression": "nextVersion",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-1/a30a879cb60f5e774598bce32a214d8b0843fb6d45f4529bb1193f2f88538787.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-1/a30a879cb60f5e774598bce32a214d8b0843fb6d45f4529bb1193f2f88538787.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `921aec361c701d48c4aa130128059385d5200ff2b4eed4a1d16c67ada53a4765`.

## RAN2_P1_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original query supplies no focal TDoc and does not enforce incoming LS; use an explicitly global pair task and restrict the target type.']

**Original question:** Which incoming LS does a given TDoc reply to (reply-to linkage)?

**Revised question:** List every distinct replying-TDoc/incoming-liaison-TDoc number pair with a REPLY_TO link whose target has type LSin.

**Proposed rationale:** The original query supplies no focal TDoc and does not enforce incoming LS; use an explicitly global pair task and restrict the target type.

**Original query**

```cypher
MATCH (t:Tdoc)-[:REPLY_TO]->(target:Tdoc) RETURN t.tdocNumber, target.tdocNumber AS replyTarget ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:REPLY_TO]->(target:Tdoc) WHERE target.type = 'LSin' RETURN DISTINCT t.tdocNumber, target.tdocNumber AS replyTarget
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
      "name": "replyTarget",
      "nullable": true,
      "source_column_or_expression": "replyTarget",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-3/ae2dbe46ed85ca14478b63d8c3f61d6ae3335a859ab9f6572a643b7bcd6cb1b1.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-3/ae2dbe46ed85ca14478b63d8c3f61d6ae3335a859ab9f6572a643b7bcd6cb1b1.jsonl); 0 native rows retained. The retained per-item check record has 3 passing scorer checks for this definition.

**Definition SHA-256:** `73087e8006622f5a6ece106a312db271ef27b25cdd7a2038737a31bd4fce956f`.

## RAN2_P1_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which spec does CR R2-2509337 modify (change target)?

**Revised question:** Return all distinct specification-number/version pairs reached by MODIFIES from TDoc number R2-2509337; preserve null when a linked specification has no recorded version.

**Proposed rationale:** Grade modification targets, remove arbitrary one-target selection, and define optional version.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber, t.title, s.specNumber, s.specVersion LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:MODIFIES]->(s:Spec) RETURN DISTINCT t.tdocNumber, t.title, s.specNumber, s.specVersion
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.specNumber",
      "nullable": true,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "s.specVersion",
      "nullable": true,
      "source_column_or_expression": "s.specVersion",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-4/85578e63d6311caf118fe07a31c070204392ed9276a90dfea3941ff88550aca2.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-4/85578e63d6311caf118fe07a31c070204392ed9276a90dfea3941ff88550aca2.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a0862248fa4151155c6a5b95371b5ef12e023e877533bc7e027f25f57fd47552`.

## RAN2_P1_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the change category and affected scope of CR R2-2509337 (impact assessment).

**Revised question:** Return all distinct recorded combinations of CR category, literal clausesAffected text, and affectsUICC/ME/RAN/CN flags for TDoc number R2-2509337; preserve missing fields as null.

**Proposed rationale:** The flags are Boolean metadata and clausesAffected is raw text, not an independently verified clause-impact list; score all explicitly requested scope fields.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.crCategory, t.clausesAffected, t.affectsUICC, t.affectsME, t.affectsRAN, t.affectsCN LIMIT 1
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN DISTINCT t.tdocNumber, t.crCategory, t.clausesAffected, t.affectsUICC, t.affectsME, t.affectsRAN, t.affectsCN
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
    },
    {
      "name": "t.affectsUICC",
      "nullable": true,
      "source_column_or_expression": "t.affectsUICC",
      "type": "boolean"
    },
    {
      "name": "t.affectsME",
      "nullable": true,
      "source_column_or_expression": "t.affectsME",
      "type": "boolean"
    },
    {
      "name": "t.affectsRAN",
      "nullable": true,
      "source_column_or_expression": "t.affectsRAN",
      "type": "boolean"
    },
    {
      "name": "t.affectsCN",
      "nullable": true,
      "source_column_or_expression": "t.affectsCN",
      "type": "boolean"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-5/63c53d71bfd0a8b57ceab914fe0ff57f1118c27ece64f7e7e3affeadf36fa4d3.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-5/63c53d71bfd0a8b57ceab914fe0ff57f1118c27ece64f7e7e3affeadf36fa4d3.jsonl); 1 native rows retained. The retained per-item check record has 18 passing scorer checks for this definition.

**Definition SHA-256:** `dcbe0261059e87e5eaea6ac630546a57f8fb45c00dc4e8955ddfb978e7d2cbc9`.

## RAN2_P1_CQ2-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Recorded postponed status does not establish a later meeting; scope the task to observable metadata and remove the hidden cap.']

**Original question:** List the TDocs postponed to a later meeting at RAN2#131 (deferred-item tracking).

**Revised question:** List all distinct TDoc numbers presented at RAN2#131 whose recorded status is postponed.

**Proposed rationale:** Recorded postponed status does not establish a later meeting; scope the task to observable metadata and remove the hidden cap.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status = 'postponed' RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status = 'postponed' RETURN DISTINCT t.tdocNumber, t.title, t.type
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-6/30be991d1fdb28821493eb3309de5ea53ff931da78dc6ed5703a3651a7c97a8f.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-6/30be991d1fdb28821493eb3309de5ea53ff931da78dc6ed5703a3651a7c97a8f.jsonl); 9 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `824fe0dbdc1327733f485ac592ecbb088e926a8d149aa95195c9c2fd0c3ad3e4`.

## RAN2_P1_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the incoming liaison statements at meeting RAN2#132 with their agenda items (incoming-LS triage).

**Revised question:** List all distinct incoming LS TDoc-number/agenda-number pairs at RAN2#132, where incoming means LS.direction equals in.

**Proposed rationale:** Return both requested roles and remove the undeclared cap; no title or causal interpretation is required.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:LS)-[:BELONGS_TO]->(a:AgendaItem) WHERE t.direction = 'in' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY a.agendaNumber ASC, t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:LS)-[:BELONGS_TO]->(a:AgendaItem) WHERE t.direction = 'in' RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ2-7/76a8743ae02d5c62fe0d2c451d4ef53bf529ae964f1a9c8144c498f076adefa2.json), [complete native rows](../reference_outputs/RAN2_P1_CQ2-7/76a8743ae02d5c62fe0d2c451d4ef53bf529ae964f1a9c8144c498f076adefa2.jsonl); 37 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e8fe32a2de06a09cd58da84afabf9a23f51bd36e9890d8ea2b9ea0023c462a7f`.

## RAN2_P1_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Ericsson's contributions to Work Item NR_newRAT-Core (competitor positioning).

**Revised question:** List all distinct TDoc numbers submitted by companyName Ericsson and linked to NR_newRAT-Core, whether or not a meeting link is present.

**Proposed rationale:** A contribution-membership question should not silently require a meeting relationship or return only ten recent records.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Ericsson'}), (t)-[:RELATED_TO]->(:WorkItem {workItemCode:'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ3-1/654b7da2701e8e16761336e9625bc6efb65b70cb0c3d1e9d60ba1c54d30556eb.json), [complete native rows](../reference_outputs/RAN2_P1_CQ3-1/654b7da2701e8e16761336e9625bc6efb65b70cb0c3d1e9d60ba1c54d30556eb.jsonl); 3,739 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `605d59160ff6a938536065cf6837a6ca9bb78b4b8bd36d9a3a1854ac5757bc82`.

## RAN2_P1_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all companies' contributions under Agenda Item 8.2.2 (Ambient IoT) at RAN2#130 (A-IoT landscape).

**Revised question:** List all distinct company-name/TDoc-number pairs for TDocs presented at RAN2#130 under agenda item 8.2.2, using recorded SUBMITTED_BY links.

**Proposed rationale:** Grade both requested company and contribution roles; count no unstated sample as all contributions.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.2.2'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.2.2'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName, t.tdocNumber, t.title, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ3-2/97bb37b5547fa4e897ce7f055514d636de812c3cacb1340b24601ce026030fef.json), [complete native rows](../reference_outputs/RAN2_P1_CQ3-2/97bb37b5547fa4e897ce7f055514d636de812c3cacb1340b24601ce026030fef.jsonl); 65 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e7a807b92697a6c02fb267161947b681e71f767ce46f838730bb78034e9e870d`.

## RAN2_P1_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Count the contributions per company for Work Item NR_newRAT-Core (participation ranking).

**Revised question:** For each company with at least one TDoc linked to NR_newRAT-Core, return its company name and number of distinct submitted TDoc nodes linked to that work item.

**Proposed rationale:** Count distinct contribution nodes rather than join bindings and remove the unrequested top-ten restriction.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(DISTINCT t) AS contributions
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
      "name": "contributions",
      "nullable": true,
      "source_column_or_expression": "contributions",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ3-3/03e775241515f721378be7a0b48e702c929071846c7c5f11e95276bb733d5043.json), [complete native rows](../reference_outputs/RAN2_P1_CQ3-3/03e775241515f721378be7a0b48e702c929071846c7c5f11e95276bb733d5043.jsonl); 123 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `27b8b16830bf753fb60bbf263d2f6f6ef40b4e1f154844f8907347bd9f32f428`.

## RAN2_P1_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List other companies' TDocs under the same agenda item as R2-2509337 (competing-proposal scan).

**Revised question:** For each agenda item and meeting shared with R2-2509337, list all distinct company-name/other-TDoc-number pairs whose company is not a recorded submitter of R2-2509337. Exclude R2-2509337 itself.

**Proposed rationale:** Other companies requires excluding focal submitters, not merely excluding the focal document.

**Original query**

```cypher
MATCH (t0:Tdoc {tdocNumber: 'R2-2509337'})-[:BELONGS_TO]->(a:AgendaItem), (t0)-[:PRESENTED_AT]->(m:Meeting) MATCH (m)<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a), (t)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> 'R2-2509337' RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t0:Tdoc {tdocNumber: 'R2-2509337'})-[:BELONGS_TO]->(a:AgendaItem), (t0)-[:PRESENTED_AT]->(m:Meeting) MATCH (m)<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a), (t)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> 'R2-2509337' AND NOT EXISTS { MATCH (t0)-[:SUBMITTED_BY]->(c) } RETURN DISTINCT c.companyName, t.tdocNumber, t.title, t.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ3-5/27672a872847124245a9ed33fc54ffd4f4f6708c4a6bdbf3908cff85020e7f3d.json), [complete native rows](../reference_outputs/RAN2_P1_CQ3-5/27672a872847124245a9ed33fc54ffd4f4f6708c4a6bdbf3908cff85020e7f3d.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `961a4d215be4f2f37ffc41d735eec7712b217912db05d05496df2a983db9ed69`.

## RAN2_P1_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return Nokia's contribution distribution across work items (focus-area profiling).

**Revised question:** For each recorded work-item code linked to a TDoc submitted by companyName Nokia, return that code and the number of distinct Nokia TDoc nodes linked to it.

**Proposed rationale:** An unrequested top-ten cap omits part of the distribution; deduplicate contributions within each work item.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Nokia'}), (t)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Nokia'}), (t)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(DISTINCT t) AS contributions
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
      "name": "contributions",
      "nullable": true,
      "source_column_or_expression": "contributions",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ3-6/fdcb7dbfbccbb10270766e76bc51d874f6cf7edbdf99ee1433743ff18956cc6b.json), [complete native rows](../reference_outputs/RAN2_P1_CQ3-6/fdcb7dbfbccbb10270766e76bc51d874f6cf7edbdf99ee1433743ff18956cc6b.jsonl); 306 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `04034d4ba93aaf03fc122ce16f072020ad36a4df2aa7349444fb81f0375cc4d1`.

## RAN2_P1_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Earlier lacks a reference date or meeting; return the explicit recorded history scope rather than silently substituting ten recent items.']

**Original question:** List Samsung's contributions to Work Item NR_Mob_enh2-Core across earlier meetings (contribution history).

**Revised question:** List all distinct TDoc-number/meeting-number pairs for Samsung-submitted TDocs linked to NR_Mob_enh2-Core.

**Proposed rationale:** Earlier lacks a reference date or meeting; return the explicit recorded history scope rather than silently substituting ten recent items.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber
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
      "name": "m.canonicalMeetingNumber",
      "nullable": true,
      "source_column_or_expression": "m.canonicalMeetingNumber",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ4-1/8a87a2888c48543ab56cc56cc30a164d36e05bdaed5db1bf721634b762a11cd6.json), [complete native rows](../reference_outputs/RAN2_P1_CQ4-1/8a87a2888c48543ab56cc56cc30a164d36e05bdaed5db1bf721634b762a11cd6.jsonl); 64 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3c71e80ffd7c3320a547a4e74beb46bd2db4911d719054526c7514f88b3b9b6f`.

## RAN2_P1_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Summarize the outcomes of Samsung's contributions at RAN2#132 (meeting result summary).

**Revised question:** For Samsung-submitted TDoc nodes presented at RAN2#132, return the recorded status and number of distinct TDoc nodes in each status group, preserving null as a missing-status group.

**Proposed rationale:** The requested summary is a status/count mapping; deduplicate optional repeated company/meeting bindings.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.status, count(t) AS count ORDER BY count DESC
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.status, count(DISTINCT t) AS count
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ4-2/eaa0a39a9532a7ac2a21aebfd7999dfd7650a376d8ab96ebed18f6821ced5500.json), [complete native rows](../reference_outputs/RAN2_P1_CQ4-2/eaa0a39a9532a7ac2a21aebfd7999dfd7650a376d8ab96ebed18f6821ced5500.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3e3c4347949b417c91ca62b4a2e721ddc9d561ec0270facceb53ea6790bf1031`.

## RAN2_P1_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the not-treated TDocs under Agenda Item 11.4.2 at RAN2#107 (pending-item backlog).

**Revised question:** List all distinct TDoc numbers presented at RAN2#107 under agenda item 11.4.2 whose recorded status equals not treated.

**Proposed rationale:** Remove the undocumented ten-item sample and grade only the requested identifiers.

**Original query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#107'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '11.4.2'}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#107'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '11.4.2'}) WHERE t.status = 'not treated' RETURN DISTINCT t.tdocNumber, t.title, t.type
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P1_CQ4-3/95bdbd5fb920dd585d529da16b917abdf314850cac59cdaa42cd5602ed2959e0.json), [complete native rows](../reference_outputs/RAN2_P1_CQ4-3/95bdbd5fb920dd585d529da16b917abdf314850cac59cdaa42cd5602ed2959e0.jsonl); 100 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `522a564df5ae329ae2ac5c603897159088dab5762a214a489f47250114d09049`.

## RAN2_P2_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the agreements reached at meeting RAN2#117 (decision review).

**Revised question:** List all distinct Agreement identifier/content pairs linked by MADE_AT to RAN2#117.

**Proposed rationale:** A what-agreed response must score content as well as identifiers; agenda fields and a fifteen-row cap are unrequested.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#117'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#117'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId, a.content, ai.agendaNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-1/b16a1950642e3d9cab388488076ad488a286a85d33e90969537345de7c700894.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-1/b16a1950642e3d9cab388488076ad488a286a85d33e90969537345de7c700894.jsonl); 96 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `799d9ae8aebab365f2b37a0579959450c71a25b80b09e715d9ff6397ac7d2afd`.

## RAN2_P2_CQ1-10

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return resolution counts by type at meeting RAN2#132 (meeting decision mix).

**Revised question:** For Resolutions MADE_AT RAN2#132, return category/count pairs using this category priority: Agreement, otherwise Conclusion, otherwise WorkingAssumption, otherwise Other. Count each distinct Resolution node once.

**Proposed rationale:** Define multi-label categorization and the uncategorized fallback instead of silently returning a null type; grade both distribution fields.

**Original query**

```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' END AS type, count(r) AS cnt ORDER BY cnt DESC
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' ELSE 'Other' END AS type, count(DISTINCT r) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "type",
      "nullable": false,
      "source_column_or_expression": "type",
      "type": "string"
    },
    {
      "name": "cnt",
      "nullable": false,
      "source_column_or_expression": "cnt",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-10/ee9b1bae4a4ae8c230a9b42a1a95b27cf35afa043ac643b0c98cf995dee755e2.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-10/ee9b1bae4a4ae8c230a9b42a1a95b27cf35afa043ac643b0c98cf995dee755e2.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ad744ea18318d9f89810c61eb30b52bb05a28f1b104b6717957783df92742ac0`.

## RAN2_P2_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions drawn at meeting RAN2#121 (study-outcome review).

**Revised question:** List all distinct Conclusion identifier/content pairs linked by MADE_AT to RAN2#121.

**Proposed rationale:** Grade the requested conclusions rather than only identifiers or an unrequested consensus flag; remove the cap.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#121'}) RETURN c.resolutionId, c.content, c.hasConsensus ORDER BY c.sequence LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#121'}) RETURN DISTINCT c.resolutionId, c.content, c.hasConsensus
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-2/70935b69e943388b2a9fd1fd33df243afe47051b91e3b82dd4ede92fbe31b8e5.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-2/70935b69e943388b2a9fd1fd33df243afe47051b91e3b82dd4ede92fbe31b8e5.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e3df29c0b868a237df50137933476365a19e9dbe69968cf92ee2634da25e586c`.

## RAN2_P2_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the working assumptions from meeting RAN2#115 (provisional-decision review).

**Revised question:** List all distinct WorkingAssumption identifier/content pairs linked by MADE_AT to RAN2#115.

**Proposed rationale:** Score content and identity, and remove the unrequested fifteen-row sample.

**Original query**

```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#115'}) RETURN DISTINCT wa.resolutionId, wa.content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-3/060722eb232d6374db8daf779d5ac35a30dfc351b7b1cc921367b042333f5394.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-3/060722eb232d6374db8daf779d5ac35a30dfc351b7b1cc921367b042333f5394.jsonl); 11 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `9620eb87c2a9f193d995ba60849ab0df68dcbd76d1ec0165506c23286f5e9441`.

## RAN2_P2_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions under Agenda Item 8.11 at RAN2#117 (agenda decision trace).

**Revised question:** List all distinct resolution identifier/label-set/content triples linked by MADE_AT to RAN2#117 and belonging to agenda item 8.11 or an agenda number beginning 8.11..

**Proposed rationale:** The dotted prefix denotes descendants, and MADE_AT must enforce the requested meeting rather than joining any meeting; labels are an unordered set.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE (ai.agendaNumber = '8.11' OR ai.agendaNumber STARTS WITH '8.11.') AND ai.meetingNumber = '117' MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS type, r.content ORDER BY r.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE (ai.agendaNumber = '8.11' OR ai.agendaNumber STARTS WITH '8.11.') AND ai.meetingNumber = '117' MATCH (r)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber:'RAN2#117'}) RETURN DISTINCT r.resolutionId, labels(r) AS type, r.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": [
          "array",
          "null"
        ]
      },
      "name": "type",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "string",
        "kind": "set"
      },
      "nullable": true,
      "source_column_or_expression": "type",
      "type": "json"
    },
    {
      "name": "r.content",
      "nullable": true,
      "source_column_or_expression": "r.content",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-4/2db272fb1af4b107b1448421683f1e92e1cc96898e9a03e9306b71e37b637734.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-4/2db272fb1af4b107b1448421683f1e92e1cc96898e9a03e9306b71e37b637734.jsonl); 35 native rows retained. The retained per-item check record has 12 passing scorer checks for this definition.

**Definition SHA-256:** `8ab818ad837f127b63d3dc20a77fd325baf12591f6299f509b6cb5fc0722477a`.

## RAN2_P2_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The revised task restricts the population to records with a MADE_AT Meeting link. The original question did not explicitly require that restriction; this supplied scope is a substantive variant, not verified preservation of the original population.']

**Original question:** List the resolutions related to Rel-18 (release decision review).

**Revised question:** List all distinct resolution identifier/content pairs that REFERENCES a TDoc linked by TARGET_RELEASE to Rel-18. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** Define release relatedness by the explicit recorded relationship path and remove the hidden cap. The mandatory meeting-linked population is explicit. The revised task restricts the population to records with a MADE_AT Meeting link. The original question did not explicitly require that restriction; this supplied scope is a substantive variant, not verified preservation of the original population.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, r.content ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId, m.canonicalMeetingNumber, r.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
    {
      "name": "r.content",
      "nullable": true,
      "source_column_or_expression": "r.content",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-5/7bcef7f775eaf415c0fc1ce833cdd0090259b25f90ad65668264b9a1d5e1cbf8.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-5/7bcef7f775eaf415c0fc1ce833cdd0090259b25f90ad65668264b9a1d5e1cbf8.jsonl); 306 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `56af953e64123cd734e06512c33f94e876da994f792bc3068949344e72e8ebf5`.

## RAN2_P2_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The graph path is documentary evidence rather than proof that the resolution drove the change; remove the hidden cap.']

**Original question:** List the resolutions that drive changes to spec 38.331 (RRC decision impact).

**Revised question:** List all distinct resolution identifier/content pairs that REFERENCES a TDoc with a MODIFIES link to specification number 38.331. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** The graph path is documentary evidence rather than proof that the resolution drove the change; remove the hidden cap. The mandatory meeting-linked population is explicit.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, r.content ORDER BY m.meetingNumberInt DESC, r.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId, m.canonicalMeetingNumber, r.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
    {
      "name": "r.content",
      "nullable": true,
      "source_column_or_expression": "r.content",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-6/06ec4f85ce869e08daf93c81f862fba1b43a59b283500dc6822bb0aa42852674.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-6/06ec4f85ce869e08daf93c81f862fba1b43a59b283500dc6822bb0aa42852674.jsonl); 233 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `71167156225b119e8ecc7c0c37e7a8bd7c45610b64a6f55080396a05ca4e7ef1`.

## RAN2_P2_CQ1-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A given work item is not provided; define the global mapping rather than manufacture a focal input. Meeting and recency restrictions are unrequested.']

**Original question:** List the resolutions tied to a given work item via its TDocs (work-item decision trace).

**Revised question:** For all work items, list each distinct work-item-code/resolution-identifier pair connected by WorkItem &lt;-RELATED_TO- Tdoc &lt;-REFERENCES- Resolution. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** A given work item is not provided; define the global mapping rather than manufacture a focal input. Meeting and recency restrictions are unrequested. The mandatory meeting-linked population is explicit.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (r)-[:MADE_AT]->(m:Meeting) WITH wi, r, m RETURN wi.workItemCode AS workItemId, r.resolutionId, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, wi.workItemCode, r.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (r)-[:MADE_AT]->(m:Meeting) WITH wi, r, m RETURN DISTINCT wi.workItemCode AS workItemId, r.resolutionId, m.canonicalMeetingNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workItemId",
      "nullable": true,
      "source_column_or_expression": "workItemId",
      "type": "string"
    },
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-7/35a9fd8a8034fe8903a7a0c2bcec82c73b81ae845c00030b06bfc999efe5e866.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-7/35a9fd8a8034fe8903a7a0c2bcec82c73b81ae845c00030b06bfc999efe5e866.jsonl); 2,144 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `1485b794d1defe53d1d936f52f85fa2235df20a2ce0dd4cd9af4b1e9fa56eee0`.

## RAN2_P2_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 agenda items by resolution count (hot-topic ranking).

**Revised question:** Among all recorded agenda-number/meeting-number groups whose agenda number is non-null and differs from UNKNOWN, return the top ten by distinct Resolution-node count, including zero-count groups. Return both grouping keys and the count; rank count descending then agenda number and meeting number ascending, returning all available eligible groups if fewer than ten exist.

**Proposed rationale:** State the actual grouping unit, distinct counted entity, cap, and deterministic tie-breakers. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber <> 'UNKNOWN' RETURN ai.agendaNumber, ai.meetingNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC, ai.agendaNumber, ai.meetingNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) WHERE ai.agendaNumber <> 'UNKNOWN' OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) RETURN ai.agendaNumber,ai.meetingNumber,count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC,ai.agendaNumber ASC,ai.meetingNumber ASC LIMIT 10
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
      "name": "ai.meetingNumber",
      "nullable": true,
      "source_column_or_expression": "ai.meetingNumber",
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
      },
      {
        "direction": "asc",
        "field": "ai.meetingNumber"
      }
    ],
    "tie_policy": "agenda number, then meeting number, ascending"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ1-8/be00f6bdb7747e17fed5ab593da103620741e87f60cbf2118b1e7df54b7d82fc.json), [complete native rows](../reference_outputs/RAN2_P2_CQ1-8/be00f6bdb7747e17fed5ab593da103620741e87f60cbf2118b1e7df54b7d82fc.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `bdc675735a181c14ff28cc5ab4042d2d08dfaa0b267f7c99505806b7d03ea6af`.

## RAN2_P2_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['REFERENCES does not establish causal lead-to semantics; the TDoc field is scalar, so use equality instead of a string-in-string membership test.']

**Original question:** Which resolutions did TDoc R2-2508373 lead to (contribution-to-decision trace)?

**Revised question:** List all distinct resolution identifier/content pairs with a REFERENCES link to a TDoc whose tdocNumber equals R2-2508373. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** REFERENCES does not establish causal lead-to semantics; the TDoc field is scalar, so use equality instead of a string-in-string membership test. The mandatory meeting-linked population is explicit.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WHERE 'R2-2508373' IN t.tdocNumber MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, r.resolutionId, labels(r) AS type, m.canonicalMeetingNumber, r.content
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WHERE t.tdocNumber = 'R2-2508373' MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT t.tdocNumber, r.resolutionId, labels(r) AS type, m.canonicalMeetingNumber, r.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
    {
      "name": "r.content",
      "nullable": true,
      "source_column_or_expression": "r.content",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-1/cce83bc632928d667d4dbc2c53d1ba927d7031ea3bff61578b31ee66d74249ab.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-1/cce83bc632928d667d4dbc2c53d1ba927d7031ea3bff61578b31ee66d74249ab.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bf389cae85c73079a08760c47644839c7571cd09f6f7da01cb89cef23229f146`.

## RAN2_P2_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs referenced by Agreement AGR-132-8.13-005 (decision provenance).

**Revised question:** List all distinct TDoc numbers reached by REFERENCES from Agreement AGR-132-8.13-005.

**Proposed rationale:** Grade only the requested reference membership; agreement content and TDoc title are contextual rather than answer fields.

**Original query**

```cypher
MATCH (a:Agreement {resolutionId: 'AGR-132-8.13-005'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```

**Revised query**

```cypher
MATCH (a:Agreement {resolutionId: 'AGR-132-8.13-005'})-[:REFERENCES]->(t:Tdoc) RETURN DISTINCT a.resolutionId, a.content, t.tdocNumber, t.title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-2/ccd1fa245bf19525ce2859f299249ed8ff6d3bfbe4cd48eae0b8526acfc46f3b.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-2/ccd1fa245bf19525ce2859f299249ed8ff6d3bfbe4cd48eae0b8526acfc46f3b.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e7ddb09a3141ff05585f076989ca1dc00f7fffae51c5553484776409dc430ffd`.

## RAN2_P2_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A literal text filter does not certify a deferred decision; define the lexical task and remove the hidden cap.']

**Original question:** List the agreements flagging items for comeback (deferred-decision tracking).

**Revised question:** List all distinct Agreement identifier/content pairs whose recorded content contains comeback, ignoring case. Restrict this task to records with a MADE_AT link to a recorded Meeting.

**Proposed rationale:** A literal text filter does not certify a deferred decision; define the lexical task and remove the hidden cap. The mandatory meeting-linked population is explicit.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'comeback' RETURN a.resolutionId, m.canonicalMeetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE toLower(a.content) CONTAINS 'comeback' RETURN DISTINCT a.resolutionId, m.canonicalMeetingNumber, a.content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-3/f093094384e6e5e88dbd262167b6c573dc61b3da81d0dfed56a198587843a78c.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-3/f093094384e6e5e88dbd262167b6c573dc61b3da81d0dfed56a198587843a78c.jsonl); 25 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `2cd93c859724ddbd81385a2f36c4a36afb9368d32f084bdd347ddd52c5e64d6e`.

## RAN2_P2_CQ2-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['This documentary path identifies linked targets; it does not independently establish that agreed documents updated the specifications. Grade only requested specification membership.']

**Original question:** Which specs were updated by agreed TDocs at RAN2#132 (spec-change trace)?

**Revised question:** List all distinct specification numbers reached by Agreement MADE_AT RAN2#132 -&gt; REFERENCES Tdoc -&gt; MODIFIES Spec.

**Proposed rationale:** This documentary path identifies linked targets; it does not independently establish that agreed documents updated the specifications. Grade only requested specification membership.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec), (a)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN t.tdocNumber, sp.specNumber, a.resolutionId, a.content ORDER BY a.sequence, t.tdocNumber, sp.specNumber, a.resolutionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec), (a)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN DISTINCT t.tdocNumber, sp.specNumber, a.resolutionId, a.content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-4/1b396447c289af05e8127ab90037d86cf3ca2690dd5ec4314111b447cc3d2a7c.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-4/1b396447c289af05e8127ab90037d86cf3ca2690dd5ec4314111b447cc3d2a7c.jsonl); 11 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9981e339781ef55fba64451aa7cd5dbf249d2239fa03a6e9dc03abaf2b4d087f`.

## RAN2_P2_CQ2-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The evidence is documentary reference, not causal production of a decision; grade content and identifier without unrequested context.']

**Original question:** Which resolutions did TDoc R2-2500064 lead to (contribution-to-decision trace)?

**Revised question:** List all distinct Resolution identifier/content pairs with a REFERENCES link to TDoc number R2-2500064.

**Proposed rationale:** The evidence is documentary reference, not causal production of a decision; grade content and identifier without unrequested context.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R2-2500064'}), (r)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, r.resolutionId, labels(r) AS type, m.canonicalMeetingNumber, r.content
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc {tdocNumber:'R2-2500064'}) RETURN DISTINCT r.resolutionId,r.content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
    {
      "name": "r.content",
      "nullable": true,
      "source_column_or_expression": "r.content",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-5/eb1df557ba874509b32963e03f8914bfffe6e6e7b9d211c391e79621792c9a15.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-5/eb1df557ba874509b32963e03f8914bfffe6e6e7b9d211c391e79621792c9a15.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `856aebf2ff91a7381a2748d38119de44658b60810d301edd5d827eb8d85ebada`.

## RAN2_P2_CQ2-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The literal occurrence does not establish that an item is still open; define the lexical filter and remove the hidden cap.']

**Original question:** List the agreements containing open FFS items (further-study backlog).

**Revised question:** List all distinct Agreement identifier/content pairs whose recorded content contains FFS, ignoring case.

**Proposed rationale:** The literal occurrence does not establish that an item is still open; define the lexical filter and remove the hidden cap.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'FFS' RETURN a.resolutionId, m.canonicalMeetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement) WHERE toLower(a.content) CONTAINS 'ffs' RETURN DISTINCT a.resolutionId,a.content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ2-6/1a8253480583e345f2bf821fc3892ef006c0c6259d992c6bc074210d3b5a5fca.json), [complete native rows](../reference_outputs/RAN2_P2_CQ2-6/1a8253480583e345f2bf821fc3892ef006c0c6259d992c6bc074210d3b5a5fca.jsonl); 1,135 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4890872e2e6b74d9fdc952a8ca8121a1e0e4f4395eb3de18943a11523cdec059`.

## RAN2_P2_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Count a document once despite multiple links, preserve the zero-denominator case, and describe documentary references rather than causal effectiveness.']

**Original question:** Return the share of Huawei's TDocs that led to resolutions (effectiveness rate).

**Revised question:** For companyName Huawei, return the number of distinct submitted TDoc nodes, the number of those nodes referenced by any Resolution, and their percentage rounded to one decimal. Return null percentage when the submitted count is zero.

**Proposed rationale:** Count a document once despite multiple links, preserve the zero-denominator case, and describe documentary references rather than causal effectiveness.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS totalTdocs MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(t:Tdoc)<-[:REFERENCES]-(r:Resolution) WITH totalTdocs, count(DISTINCT t) AS resolvedTdocs RETURN totalTdocs, resolvedTdocs, round(100.0 * resolvedTdocs / totalTdocs, 1) AS ratio
```

**Revised query**

```cypher
MATCH (c:Company {companyName:'Huawei'}) OPTIONAL MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c) WITH c,count(DISTINCT t) AS totalTdocs OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(t2:Tdoc)-[:SUBMITTED_BY]->(c) WITH totalTdocs,count(DISTINCT t2) AS resolvedTdocs RETURN totalTdocs,resolvedTdocs,CASE WHEN totalTdocs=0 THEN null ELSE round(100.0*resolvedTdocs/totalTdocs,1) END AS ratio
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
      "name": "resolvedTdocs",
      "nullable": false,
      "source_column_or_expression": "resolvedTdocs",
      "type": "integer"
    },
    {
      "name": "ratio",
      "nullable": true,
      "source_column_or_expression": "ratio",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one summary row when the named Company exists",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ3-1/10260e17301c1e1d70ab6c5c5d4e4582185a89529ebec7d638228c4df3561e98.json), [complete native rows](../reference_outputs/RAN2_P2_CQ3-1/10260e17301c1e1d70ab6c5c5d4e4582185a89529ebec7d638228c4df3561e98.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `da854a4874c042629d562588303682ee4b27811e77a18365e31fb72cd8833c35`.

## RAN2_P2_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Retain resolution-contribution counting rather than interpret it as ownership; remove the undeclared top-ten cap and make the all-company ranking deterministic.']

**Original question:** Rank the main contributors to spec 38.331 (RRC ownership).

**Revised question:** For each recorded company whose submitted TDoc is referenced by a Resolution and modifies specification number 38.331, return its name and distinct Resolution-node count. Rank all companies by count descending and company name ascending.

**Proposed rationale:** Retain resolution-contribution counting rather than interpret it as ownership; remove the undeclared top-ten cap and make the all-company ranking deterministic.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS contributions ORDER BY contributions DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS contributions ORDER BY contributions DESC, c.companyName ASC
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
      "name": "contributions",
      "nullable": true,
      "source_column_or_expression": "contributions",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "contributions"
      },
      {
        "direction": "asc",
        "field": "c.companyName"
      }
    ],
    "tie_policy": "company name ascending"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all participating company-name groups"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ3-2/2dae403862608a6dc5b7a9f79e1efdd4ddd6f615c70ba887b655e811377037ae.json), [complete native rows](../reference_outputs/RAN2_P2_CQ3-2/2dae403862608a6dc5b7a9f79e1efdd4ddd6f615c70ba887b655e811377037ae.jsonl); 62 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a9a35a847b92e6154030a280bdab6d9f404974128cb5e7acba6e21a8a818ad2c`.

## RAN2_P2_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The query had undeclared limits on both work items and companies and unstable ties; group by documentary identifiers, not inferred technology leadership.']

**Original question:** Return the top companies by resolution contribution per work item (technology leadership).

**Revised question:** For each work-item code linked to at least one Resolution-referenced TDoc with a recorded submitter, return up to five companies with the largest distinct Resolution-node counts. Each ranked company entry contains company name and count; break count ties by company name ascending. Return every work-item code.

**Proposed rationale:** The query had undeclared limits on both work items and companies and unstable ties; group by documentary identifiers, not inferred technology leadership.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (t)-[:SUBMITTED_BY]->(c:Company) WITH wi, c, count(DISTINCT r) AS cnt ORDER BY cnt DESC WITH wi, collect({company: c.companyName, count: cnt})[0..5] AS topCompanies RETURN wi.workItemCode, topCompanies ORDER BY wi.workItemCode LIMIT 5
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (t)-[:SUBMITTED_BY]->(c:Company) WITH wi.workItemCode AS workItemCode,c.companyName AS company,count(DISTINCT r) AS count ORDER BY workItemCode ASC,count DESC,company ASC WITH workItemCode,collect({company:company,count:count})[0..5] AS topCompanies RETURN workItemCode,topCompanies
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workItemCode",
      "nullable": true,
      "source_column_or_expression": "workItemCode",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "additionalProperties": false,
          "properties": {
            "company": {
              "type": [
                "string",
                "null"
              ]
            },
            "count": {
              "type": "integer"
            }
          },
          "required": [
            "company",
            "count"
          ],
          "type": "object"
        },
        "type": [
          "array",
          "null"
        ]
      },
      "name": "topCompanies",
      "nested_array_semantics": {
        "$": "sequence"
      },
      "nested_collection_definition": {
        "cardinality": {
          "mode": "top_k",
          "tie_policy": "company name ascending",
          "value": 5
        },
        "element_type": "object",
        "fields": [
          {
            "name": "company",
            "nullable": true,
            "type": "string"
          },
          {
            "name": "count",
            "nullable": false,
            "type": "integer"
          }
        ],
        "kind": "sequence",
        "order_keys": [
          "count DESC",
          "company ASC"
        ],
        "tie_policy": "company name ascending"
      },
      "nullable": true,
      "source_column_or_expression": "topCompanies",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ3-3/45e25fd1b9784da6b764b93287e6f8408c05b760b8c4c5eac61778fbc4593867.json), [complete native rows](../reference_outputs/RAN2_P2_CQ3-3/45e25fd1b9784da6b764b93287e6f8408c05b760b8c4c5eac61778fbc4593867.jsonl); 223 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `0482d101eb1c76b4ddd948d0f170a18c8a8c639eaef639575a4132462a82bb0a`.

## RAN2_P2_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Rank the top 10 companies by resolution-referenced TDocs (overall influence).

**Revised question:** Among all recorded company-name groups, return the top ten by distinct submitted TDoc-node count where those TDocs are referenced by at least one Resolution, including zero-count groups. Return company name and TDoc count; rank count descending then company name ascending, returning all available groups if fewer than ten exist.

**Proposed rationale:** The original query counted Resolution nodes although the question requested referenced TDocs; fix the counted unit and deterministic ties, without interpreting it as influence. Start from the complete explicitly stated stored base population and optional counted links, preserving zero-count groups and distinct counting units.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (r)-[:MADE_AT]->(m:Meeting) RETURN c.companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company) OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS companyName,count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC,companyName ASC LIMIT 10
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
        "field": "companyName"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ3-5/86a419a18360ef9ca8bd7b6f352360e75a0c5c5c332efd34f383d0488d8bfb6e.json), [complete native rows](../reference_outputs/RAN2_P2_CQ3-5/86a419a18360ef9ca8bd7b6f352360e75a0c5c5c332efd34f383d0488d8bfb6e.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3d1a35f61cc274c3c1ae9d14f59a4de22bbaa6bc3a65570c15b312d9391e7be3`.

## RAN2_P2_CQ6-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the trend of Rel-18 resolution counts over meetings (chronological trend).

**Revised question:** For every recorded Meeting, return its canonical number, numeric meeting number, and number of distinct Resolution nodes MADE_AT that meeting and referencing at least one Rel-18-targeted TDoc. Include zero-count meetings and order numerically ascending, then by canonical number.

**Proposed rationale:** Deduplicate resolutions across referenced TDocs and include zero-count meetings so missing groups cannot distort the trend.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(r) AS resCount ORDER BY m.meetingNumberInt ASC
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m), (r)-[:REFERENCES]->(:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS resCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingNumber",
      "nullable": true,
      "source_column_or_expression": "meetingNumber",
      "type": "string"
    },
    {
      "name": "meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "meetingNumberInt",
      "type": "integer"
    },
    {
      "name": "resCount",
      "nullable": false,
      "source_column_or_expression": "resCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "meetingNumber"
      }
    ],
    "tie_policy": "canonical meeting number ascending for equal numeric meeting number"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ6-1/640513c5b8f045eb27fb2177d7802709c2c9e37eab7d881cae8dbd1013b2ee2a.json), [complete native rows](../reference_outputs/RAN2_P2_CQ6-1/640513c5b8f045eb27fb2177d7802709c2c9e37eab7d881cae8dbd1013b2ee2a.jsonl); 58 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `3aed8c289f3ce8c7efa56f6bccb318363e271ed12afc9e8e728fb3eb42d8cbfa`.

## RAN2_P2_CQ6-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original inner joins excluded zero-company meetings; use the same complete meeting population and denominator, and describe reference attribution rather than influence.']

**Original question:** Track how Huawei's resolution-contribution rate changed over meetings (influence trend).

**Revised question:** For every recorded Meeting, return canonical and numeric meeting numbers, total distinct Resolution count, count of those Resolutions referencing a Huawei-submitted TDoc, and percentage rounded to one decimal. Use null percentage when total is zero. Include zero Huawei counts and order meetings numerically ascending, then canonically.

**Proposed rationale:** The original inner joins excluded zero-company meetings; use the same complete meeting population and denominator, and describe reference attribution rather than influence.

**Original query**

```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting) WITH m, count(r) AS total MATCH (r2:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (r2)-[:MADE_AT]->(m) WITH m, total, count(DISTINCT r2) AS huaweiCount RETURN m.canonicalMeetingNumber, m.meetingNumberInt, huaweiCount, total, round(100.0 * huaweiCount / total, 1) AS ratio ORDER BY m.meetingNumberInt ASC
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m) WITH m,count(DISTINCT r) AS total OPTIONAL MATCH (r2:Resolution)-[:MADE_AT]->(m), (r2)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Huawei'}) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r2) AS huaweiCount,total,CASE WHEN total=0 THEN null ELSE round(100.0*count(DISTINCT r2)/total,1) END AS ratio ORDER BY meetingNumberInt ASC,meetingNumber ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingNumber",
      "nullable": true,
      "source_column_or_expression": "meetingNumber",
      "type": "string"
    },
    {
      "name": "meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "meetingNumberInt",
      "type": "integer"
    },
    {
      "name": "huaweiCount",
      "nullable": false,
      "source_column_or_expression": "huaweiCount",
      "type": "integer"
    },
    {
      "name": "total",
      "nullable": false,
      "source_column_or_expression": "total",
      "type": "integer"
    },
    {
      "name": "ratio",
      "nullable": true,
      "source_column_or_expression": "ratio",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "meetingNumber"
      }
    ],
    "tie_policy": "canonical meeting number ascending for equal numeric meeting number"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ6-2/960be3fc53b6063d4b4451e303238cd06932d16c8fa84d22836120600b7e9a5b.json), [complete native rows](../reference_outputs/RAN2_P2_CQ6-2/960be3fc53b6063d4b4451e303238cd06932d16c8fa84d22836120600b7e9a5b.jsonl); 58 native rows retained. The retained per-item check record has 19 passing scorer checks for this definition.

**Definition SHA-256:** `e3b45c455802ce29643e5647117627bcf64e5d7c60493694a7de90f1c35e1f05`.

## RAN2_P2_CQ6-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the trend of agreement counts per meeting (activity trend).

**Revised question:** For every recorded Meeting, return canonical and numeric meeting numbers and the number of distinct Agreement nodes linked by MADE_AT. Include zero-count meetings and order numerically ascending, then by canonical number.

**Proposed rationale:** A full meeting trend needs zero-count groups and distinct counted entities rather than nonempty join results.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(a) AS agrCount ORDER BY m.meetingNumberInt ASC
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Agreement)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS agrCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingNumber",
      "nullable": true,
      "source_column_or_expression": "meetingNumber",
      "type": "string"
    },
    {
      "name": "meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "meetingNumberInt",
      "type": "integer"
    },
    {
      "name": "agrCount",
      "nullable": false,
      "source_column_or_expression": "agrCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "meetingNumber"
      }
    ],
    "tie_policy": "canonical meeting number ascending for equal numeric meeting number"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ6-3/ebe1fd9067e1e81ae00fb4d8ce6608d7f23759d10f24cfc5eceadb2ac27509b8.json), [complete native rows](../reference_outputs/RAN2_P2_CQ6-3/ebe1fd9067e1e81ae00fb4d8ce6608d7f23759d10f24cfc5eceadb2ac27509b8.jsonl); 58 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b0c9361d442cb631799d7ffe6c50e46cec3e73b7ce9abc7e1c73c8d1c2a47e93`.

## RAN2_P2_CQ6-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the trend of conclusion counts per meeting (study-closure trend).

**Revised question:** For every recorded Meeting, return canonical and numeric meeting numbers and the number of distinct Conclusion nodes linked by MADE_AT. Include zero-count meetings and order numerically ascending, then by canonical number.

**Proposed rationale:** A full meeting trend needs zero-count groups and distinct counted entities rather than nonempty join results.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(c) AS conCount ORDER BY m.meetingNumberInt ASC
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Conclusion)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS conCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingNumber",
      "nullable": true,
      "source_column_or_expression": "meetingNumber",
      "type": "string"
    },
    {
      "name": "meetingNumberInt",
      "nullable": true,
      "source_column_or_expression": "meetingNumberInt",
      "type": "integer"
    },
    {
      "name": "conCount",
      "nullable": false,
      "source_column_or_expression": "conCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingNumberInt"
      },
      {
        "direction": "asc",
        "field": "meetingNumber"
      }
    ],
    "tie_policy": "canonical meeting number ascending for equal numeric meeting number"
  },
  "cardinality_policy": {
    "mode": "all",
    "notes": "all matching requested records; no undeclared final row cap"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P2_CQ6-4/3e3f0ff94505e31ff0724cbac72268da055a3b8c71df7e6be12379fac6a7d2d6.json), [complete native rows](../reference_outputs/RAN2_P2_CQ6-4/3e3f0ff94505e31ff0724cbac72268da055a3b8c71df7e6be12379fac6a7d2d6.jsonl); 58 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `c999fa59d8c1d2fb9a67b9875e9e33306d7f4fb7353d46cb57cf99e287ac0c25`.

## RAN2_P3_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all sections of spec 38.331 (RRC structure overview).

**Revised question:** List all distinct Section identifier/number/title triples belonging to any recorded version of specification number 38.331.

**Proposed rationale:** All sections conflicts with a twenty-five-row cap, and unspecified versions must not be collapsed; identifiers preserve version-specific entities.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT s.sectionId, s.sectionNumber, s.sectionTitle, s.level
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
    },
    {
      "name": "s.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "s.sectionNumber",
      "type": "string"
    },
    {
      "name": "s.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "s.sectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-1/641a4394bfedc94a6240aa57a8dd6059f46c82bcc437e485e4e9396f64afbf33.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-1/641a4394bfedc94a6240aa57a8dd6059f46c82bcc437e485e4e9396f64afbf33.jsonl); 5,834 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `131dc3ff943ec444038456bb6cd275cb81659dbe5fd29aa91a6a3c2b0b85670a`.

## RAN2_P3_CQ1-10

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find the spec and section that hold Table 6.3.3-1 (reverse table lookup).

**Revised question:** List all distinct specification-number/section-identifier/table-identifier triples locating tables numbered 6.3.3-1 through TABLE_IN_SECTION and BELONGS_TO_SPEC.

**Proposed rationale:** Specify all matching locations across graph versions instead of assuming a globally unique table number.

**Original query**

```cypher
MATCH (t:TSTable {tableNumber: '6.3.3-1'})-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, s.sectionId, t.tableId
```

**Revised query**

```cypher
MATCH (t:TSTable {tableNumber: '6.3.3-1'})-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN DISTINCT sp.specNumber, s.sectionId, t.tableId
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
      "name": "s.sectionId",
      "nullable": true,
      "source_column_or_expression": "s.sectionId",
      "type": "string"
    },
    {
      "name": "t.tableId",
      "nullable": true,
      "source_column_or_expression": "t.tableId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-10/3fc51625ba80f25b72bcad9b9acb4b3837591e627444541b9f47fd5558499c92.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-10/3fc51625ba80f25b72bcad9b9acb4b3837591e627444541b9f47fd5558499c92.jsonl); 5 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b8fb07770c3762846f4040db39ed804b43fa64f6a9c6bae4b0004cb463a1ac76`.

## RAN2_P3_CQ1-11

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by section count (largest specs).

**Revised question:** Return the top five recorded specification numbers by distinct Section-node count across all versions. Include zero-count specifications; return number and count, ranked by count descending and specification number ascending.

**Proposed rationale:** State version aggregation explicitly, deduplicate Section nodes, include zero-count groups, and define ranking ties.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber,count(DISTINCT s) AS sectionCount ORDER BY sectionCount DESC,sp.specNumber ASC LIMIT 5
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
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "sectionCount"
      },
      {
        "direction": "asc",
        "field": "sp.specNumber"
      }
    ],
    "tie_policy": "specification number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five specification-number groups or all when fewer exist",
    "tie_policy": "specification number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-11/9d24908f0804cae3dc3f55744286a8a33fc0ae0c18478940f3eb949bfe9de0d4.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-11/9d24908f0804cae3dc3f55744286a8a33fc0ae0c18478940f3eb949bfe9de0d4.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cb47fda7156a200047ab4d3ea0335bcc8c68db42f07d5bc08269c4c6e403250f`.

## RAN2_P3_CQ1-12

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the section-level distribution of spec 38.331 (structural depth profile).

**Revised question:** For Sections belonging to any recorded version of specification number 38.331, return every recorded level and its distinct Section-node count; retain null as a missing-level group.

**Proposed rationale:** A distribution needs both level and count; deduplicate Section nodes across matching specification links.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.level, count(DISTINCT s) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.level",
      "nullable": true,
      "source_column_or_expression": "s.level",
      "type": "integer"
    },
    {
      "name": "cnt",
      "nullable": true,
      "source_column_or_expression": "cnt",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-12/afa69bbf5fe2cbf611571838c064264f6c8e224c25385ea36deeeab64087d3eb.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-12/afa69bbf5fe2cbf611571838c064264f6c8e224c25385ea36deeeab64087d3eb.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0f4507931d8c671b333fbb6f11aba087bab2e0db9a9a1f42888b49563746a7a9`.

## RAN2_P3_CQ1-13

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections marked Void (placeholder scan).

**Revised question:** List all distinct Section identifier/title pairs whose title contains void, ignoring case.

**Proposed rationale:** Define the literal title filter without assuming placeholder meaning and remove the hidden fifteen-row cap.

**Original query**

```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 15
```

**Revised query**

```cypher
MATCH (s:Section) WHERE toLower(s.sectionTitle) CONTAINS 'void' RETURN DISTINCT s.sectionId, s.sectionTitle
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
    },
    {
      "name": "s.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "s.sectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-13/289ce9815d1b94e5d33adcdd16577732fed58ca405e1ac3cd4a1a7f73511beef.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-13/289ce9815d1b94e5d33adcdd16577732fed58ca405e1ac3cd4a1a7f73511beef.jsonl); 167 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e13d7ad0d1b5a6f687f2227cf3dcfa8df1d0fe005f4e879019595a39d9b46aee`.

## RAN2_P3_CQ1-14

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total counts of sections, tables, and figures (corpus size).

**Revised question:** Return the distinct node counts for Section, TSTable, and TSFigure in the frozen graph, in that named order.

**Proposed rationale:** Make all three counted graph labels explicit and grade their named count fields.

**Original query**

```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```

**Revised query**

```cypher
MATCH (s:Section) WITH count(DISTINCT s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(DISTINCT t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(DISTINCT f) AS figCnt RETURN secCnt, tblCnt, figCnt
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "mode": "exact",
    "notes": "one aggregate row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-14/592ee4344636cd6424b198818f6489098b47e40e604bb6c34b99845e05ef167f.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-14/592ee4344636cd6424b198818f6489098b47e40e604bb6c34b99845e05ef167f.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `2901f52e07b4a5f077aa8fa07f2fa1572b83004c0dac937eb659488868eac6f3`.

## RAN2_P3_CQ1-15

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 sections by table count (table-dense sections).

**Revised question:** Return the top five Section nodes by number of distinct CONTAINS_TABLE TSTable targets, including zero-target Sections. Return identifier and count; rank by count descending and Section identifier ascending.

**Proposed rationale:** Include the complete candidate population, deduplicate table targets, and define deterministic ties.

**Original query**

```cypher
MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId, count(t) AS tableCount ORDER BY tableCount DESC, s.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s:Section) OPTIONAL MATCH (s)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId,count(DISTINCT t) AS tableCount ORDER BY tableCount DESC,s.sectionId ASC LIMIT 5
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
    },
    {
      "name": "tableCount",
      "nullable": false,
      "source_column_or_expression": "tableCount",
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
        "direction": "asc",
        "field": "s.sectionId"
      }
    ],
    "tie_policy": "Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five Section-identifier groups or all when fewer exist",
    "tie_policy": "Section identifier ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-15/d1c4349d971691225099728b54c9c127c97fe821346b91aa431a7545664127eb.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-15/d1c4349d971691225099728b54c9c127c97fe821346b91aa431a7545664127eb.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5dd9e96a9730de3f2584453e7d33d6f6736a23190049d137ca1a5bbe63b3ce62`.

## RAN2_P3_CQ1-16

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 sections by figure count (figure-dense sections).

**Revised question:** Return the top five Section nodes by number of distinct CONTAINS_FIGURE TSFigure targets, including zero-target Sections. Return identifier and count; rank by count descending and Section identifier ascending.

**Proposed rationale:** Include the complete candidate population, deduplicate figure targets, and define deterministic ties.

**Original query**

```cypher
MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId, count(f) AS figCount ORDER BY figCount DESC, s.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s:Section) OPTIONAL MATCH (s)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId,count(DISTINCT f) AS figCount ORDER BY figCount DESC,s.sectionId ASC LIMIT 5
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
    },
    {
      "name": "figCount",
      "nullable": false,
      "source_column_or_expression": "figCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "figCount"
      },
      {
        "direction": "asc",
        "field": "s.sectionId"
      }
    ],
    "tie_policy": "Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five Section-identifier groups or all when fewer exist",
    "tie_policy": "Section identifier ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-16/80086a0f8f201384cbdc585ccd47aaf26e02181aaa1364ba9e6baee4c390708f.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-16/80086a0f8f201384cbdc585ccd47aaf26e02181aaa1364ba9e6baee4c390708f.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `904c02209e5541a8dae32e592a377a83d29bbc9267e7e2001a41c6184746d557`.

## RAN2_P3_CQ1-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Latest release was not requested and is not a unique version selection; preserve all recorded parent/child roles instead of choosing an arbitrary parent.']

**Original question:** List the subsections under section 5 of spec 38.321 (MAC structure drill-down).

**Revised question:** Across all recorded versions of specification number 38.321, list each direct HAS_SUB_SECTION child of every section numbered 5. Return parent identifier and child identifier, number, and title.

**Proposed rationale:** Latest release was not requested and is not a unique version selection; preserve all recorded parent/child roles instead of choosing an arbitrary parent.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(parent:Section {sectionNumber:'5'}) WHERE rk.specRelease IS NOT NULL WITH parent, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (parent)-[:HAS_SUB_SECTION]->(child:Section) RETURN child.sectionId, child.sectionNumber, child.sectionTitle ORDER BY child.sectionNumber
```

**Revised query**

```cypher
MATCH (parent:Section {sectionNumber:'5'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}), (parent)-[:HAS_SUB_SECTION]->(child:Section) RETURN DISTINCT parent.sectionId AS parentSectionId,child.sectionId AS childSectionId,child.sectionNumber AS childSectionNumber,child.sectionTitle AS childSectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "parentSectionId",
      "nullable": true,
      "source_column_or_expression": "parentSectionId",
      "type": "string"
    },
    {
      "name": "childSectionId",
      "nullable": true,
      "source_column_or_expression": "childSectionId",
      "type": "string"
    },
    {
      "name": "childSectionNumber",
      "nullable": true,
      "source_column_or_expression": "childSectionNumber",
      "type": "string"
    },
    {
      "name": "childSectionTitle",
      "nullable": true,
      "source_column_or_expression": "childSectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-2/f161444b7f06d849c82bb0fb947900525a8d2d4ecd5eeb12bc5ab0630f7c9473.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-2/f161444b7f06d849c82bb0fb947900525a8d2d4ecd5eeb12bc5ab0630f7c9473.jsonl); 155 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `b5fb8a66bee09050a36e48c6a92aa1e4a3a8d07d8881caa7af0105c3ce5f7cf7`.

## RAN2_P3_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-1 sections of spec 38.321 (top-level MAC outline).

**Revised question:** List every distinct Section identifier/number/title triple with level 1 belonging to any recorded version of specification number 38.321.

**Proposed rationale:** Explicit recorded-version scope preserves identity and makes level-1 semantics testable.

**Original query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

**Revised query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}) RETURN DISTINCT s.sectionId, s.sectionNumber, s.sectionTitle
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
    },
    {
      "name": "s.sectionNumber",
      "nullable": true,
      "source_column_or_expression": "s.sectionNumber",
      "type": "string"
    },
    {
      "name": "s.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "s.sectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-4/52be550ce339a5f8cbca1be4e0a271ecd1abf830d06d07f75be47ea1758cf595.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-4/52be550ce339a5f8cbca1be4e0a271ecd1abf830d06d07f75be47ea1758cf595.jsonl); 40 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `33710ed0d50f7fb300807e05d03ab4d1e96c1b8ebaed2bcdb49072b528acd875`.

## RAN2_P3_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['An unspecified section version cannot be selected by highest release and arbitrary LIMIT 1; expose version-specific identities and all recorded matches.']

**Original question:** List the tables in section 6.2.1 of spec 38.321 (table lookup).

**Revised question:** Across all recorded versions of specification number 38.321, list tables connected by CONTAINS_TABLE from sections numbered 6.2.1. Return section identifier and table identifier, number, and caption.

**Proposed rationale:** An unspecified section version cannot be selected by highest release and arbitrary LIMIT 1; expose version-specific identities and all recorded matches.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'6.2.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption
```

**Revised query**

```cypher
MATCH (s:Section {sectionNumber:'6.2.1'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}), (s)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT s.sectionId AS sectionId,t.tableId AS tableId,t.tableNumber AS tableNumber,t.tableCaption AS tableCaption
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
      "name": "tableId",
      "nullable": true,
      "source_column_or_expression": "tableId",
      "type": "string"
    },
    {
      "name": "tableNumber",
      "nullable": true,
      "source_column_or_expression": "tableNumber",
      "type": "string"
    },
    {
      "name": "tableCaption",
      "nullable": true,
      "source_column_or_expression": "tableCaption",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-5/4eb61728819ef72b6b6ec26ad249ca33131b87495445da6c8f5f5565f79a29bd.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-5/4eb61728819ef72b6b6ec26ad249ca33131b87495445da6c8f5f5565f79a29bd.jsonl); 31 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `88559e03f34d78f47604c6dbca17b9f75cac544372aa671a070bc594cf562fbb`.

## RAN2_P3_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Remove unrequested and nonunique latest-release selection; expose all recorded section/figure roles.']

**Original question:** List the figures in section 6.1.3.1 of spec 38.321 (figure lookup).

**Revised question:** Across all recorded versions of specification number 38.321, list figures connected by CONTAINS_FIGURE from sections numbered 6.1.3.1. Return section identifier and figure identifier, number, and caption.

**Proposed rationale:** Remove unrequested and nonunique latest-release selection; expose all recorded section/figure roles.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'6.1.3.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption
```

**Revised query**

```cypher
MATCH (s:Section {sectionNumber:'6.1.3.1'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}), (s)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN DISTINCT s.sectionId AS sectionId,f.figureId AS figureId,f.figureNumber AS figureNumber,f.figureCaption AS figureCaption
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
      "name": "figureId",
      "nullable": true,
      "source_column_or_expression": "figureId",
      "type": "string"
    },
    {
      "name": "figureNumber",
      "nullable": true,
      "source_column_or_expression": "figureNumber",
      "type": "string"
    },
    {
      "name": "figureCaption",
      "nullable": true,
      "source_column_or_expression": "figureCaption",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-6/e0d6f5b73935dfbdfa97bdb40a3449bd00795e0abc1f49f40f1084a57c6d9f13.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-6/e0d6f5b73935dfbdfa97bdb40a3449bd00795e0abc1f49f40f1084a57c6d9f13.jsonl); 18 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `023728faa06febcfeeeda0801863a4d066f4c93b66b1f0194d057723f55043d8`.

## RAN2_P3_CQ1-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which section contains Table 5.1-1 (table location)?

**Revised question:** List all distinct table-identifier/section-identifier pairs linked by TABLE_IN_SECTION where tableNumber is 5.1-1, across all recorded specifications and versions.

**Proposed rationale:** A table number is not globally unique; return all identified locations and specify the unbounded graph scope.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section) WHERE t.tableNumber = '5.1-1' RETURN t.tableId, s.sectionId, s.sectionTitle
```

**Revised query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section) WHERE t.tableNumber = '5.1-1' RETURN DISTINCT t.tableId, s.sectionId, s.sectionTitle
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tableId",
      "nullable": true,
      "source_column_or_expression": "t.tableId",
      "type": "string"
    },
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-7/61ea4eceee07a4af408e09c40de76f21d49f5f7d0cbf2010c3a8d5fa1069a320.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-7/61ea4eceee07a4af408e09c40de76f21d49f5f7d0cbf2010c3a8d5fa1069a320.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bb7897b51ef230ca90a539db918e6798e0e1bb005a45254f674213856de6d83d`.

## RAN2_P3_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all tables in spec 38.331 (table inventory).

**Revised question:** List every distinct table identifier/number/caption triple linked by TABLE_IN_SECTION to a Section belonging to any recorded version of specification number 38.331.

**Proposed rationale:** Remove a cap incompatible with all tables; version-specific table identifiers preserve repeated table numbers.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT t.tableId, t.tableNumber, t.tableCaption
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "t.tableId",
      "nullable": true,
      "source_column_or_expression": "t.tableId",
      "type": "string"
    },
    {
      "name": "t.tableNumber",
      "nullable": true,
      "source_column_or_expression": "t.tableNumber",
      "type": "string"
    },
    {
      "name": "t.tableCaption",
      "nullable": true,
      "source_column_or_expression": "t.tableCaption",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-8/a8652c87f6ec8ca9fb3a1591dfc13d18112b5f2deeeb0f3ccdc38caa540d55e7.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-8/a8652c87f6ec8ca9fb3a1591dfc13d18112b5f2deeeb0f3ccdc38caa540d55e7.jsonl); 24 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b52d03e710c304c988314801e70213c2830e92b1e3f3ab729ccde717720abd8f`.

## RAN2_P3_CQ1-9

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections whose title contains 'MAC' (topic search).

**Revised question:** List all distinct Section identifier/title pairs whose title contains the literal case-sensitive text MAC.

**Proposed rationale:** The original question explicitly defines a title substring, so retain that lexical criterion and remove only the hidden sample cap.

**Original query**

```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'MAC' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'MAC' RETURN DISTINCT s.sectionId, s.sectionTitle
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
    },
    {
      "name": "s.sectionTitle",
      "nullable": true,
      "source_column_or_expression": "s.sectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ1-9/4a7fdc5e7e8ff4edec601e8f19df8a418b0cbe3315b87af2990ac9d08459c1ce.json), [complete native rows](../reference_outputs/RAN2_P3_CQ1-9/4a7fdc5e7e8ff4edec601e8f19df8a418b0cbe3315b87af2990ac9d08459c1ce.jsonl); 484 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6ece384f5cf398dbe6ecc864e2b8a5a4bd52a45360c502ec798eeca44bc5e318`.

## RAN2_P3_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Unrequested latest-release selection loses source/version scope; preserve distinct source/target roles and all versions.']

**Original question:** List the sections referenced by section 5.4.4 of spec 38.321 (outgoing references).

**Revised question:** Across every recorded version of specification number 38.321, list each direct REFERENCES_SECTION target of sections numbered 5.4.4. Return source and target Section identifiers.

**Proposed rationale:** Unrequested latest-release selection loses source/version scope; preserve distinct source/target roles and all versions.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'5.4.4'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:REFERENCES_SECTION]->(ref:Section) RETURN ref.sectionId, ref.sectionTitle ORDER BY ref.sectionId
```

**Revised query**

```cypher
MATCH (s:Section {sectionNumber:'5.4.4'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}), (s)-[:REFERENCES_SECTION]->(ref:Section) RETURN DISTINCT s.sectionId AS sourceSectionId,ref.sectionId AS targetSectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "sourceSectionId",
      "type": "string"
    },
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "targetSectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-1/98f5d885a287b7c5db931a52ea7c9611f84f49a3e5939503794d045c7fb28d55.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-1/98f5d885a287b7c5db931a52ea7c9611f84f49a3e5939503794d045c7fb28d55.jsonl); 65 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c77eb785d5d8623979cdac0c93e115871e8005a0c4f60356141722b71efb86c3`.

## RAN2_P3_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Remove hidden latest-release selection and preserve version-specific reference roles.']

**Original question:** List the sections that reference section 5.4.3.1 of spec 38.321 (incoming references).

**Revised question:** Across every recorded version of specification number 38.321, list each direct REFERENCES_SECTION source pointing to sections numbered 5.4.3.1. Return referencing source and referenced target Section identifiers.

**Proposed rationale:** Remove hidden latest-release selection and preserve version-specific reference roles.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'5.4.3.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (ref:Section)-[:REFERENCES_SECTION]->(s) RETURN ref.sectionId, ref.sectionTitle ORDER BY ref.sectionId
```

**Revised query**

```cypher
MATCH (s:Section {sectionNumber:'5.4.3.1'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}), (ref:Section)-[:REFERENCES_SECTION]->(s) RETURN DISTINCT ref.sectionId AS sourceSectionId,s.sectionId AS targetSectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": true,
      "source_column_or_expression": "sourceSectionId",
      "type": "string"
    },
    {
      "name": "targetSectionId",
      "nullable": true,
      "source_column_or_expression": "targetSectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-2/dbecf80c01aca0a45fed27bb53f80a08f89c05960c542f9b40fe282f8ad14929.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-2/dbecf80c01aca0a45fed27bb53f80a08f89c05960c542f9b40fe282f8ad14929.jsonl); 54 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b104972358cc852edfe8de5aecda2cd1882ab777eec41012b9163bf1b05b15b4`.

## RAN2_P3_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which sections of spec 38.321 make the most references (reference hub)?

**Revised question:** Among Section nodes belonging to any recorded version of specification number 38.321, return every Section identifier whose number of distinct outgoing REFERENCES_SECTION target nodes is maximal, together with that count. Include zero-reference nodes in the candidate population.

**Proposed rationale:** The original query ranked referenced targets although the question asked sources making references; correct direction and include every maximum tie rather than an unrequested top ten.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}), (s1)-[:REFERENCES_SECTION]->(s2:Section) RETURN s2.sectionId, count(*) AS refs ORDER BY refs DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}) WITH DISTINCT s OPTIONAL MATCH (s)-[:REFERENCES_SECTION]->(target:Section) WITH s,count(DISTINCT target) AS refs WITH collect({id:s.sectionId,n:refs}) AS groups,max(refs) AS maximum UNWIND groups AS g WITH g,maximum WHERE g.n=maximum RETURN g.id AS sectionId,g.n AS refs
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
      "name": "refs",
      "nullable": false,
      "source_column_or_expression": "refs",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-3/6d10a6ae26655664c5f908eae751046d54dad3647a1e49a5f4012e7fdda48da6.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-3/6d10a6ae26655664c5f908eae751046d54dad3647a1e49a5f4012e7fdda48da6.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `78495bfb0273f674980a5cafaf6288f79b1b35d9bc03424d3d1372802b6d449f`.

## RAN2_P3_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 most-referenced sections (central sections).

**Revised question:** Return the top ten Section nodes by number of distinct incoming REFERENCES_SECTION source nodes, including zero-reference Sections. Return Section identifier and count; rank by count descending and Section identifier ascending.

**Proposed rationale:** Deduplicate reference sources, include the full Section population, and define ranking ties explicitly.

**Original query**

```cypher
MATCH (ref:Section)-[:REFERENCES_SECTION]->(s:Section) RETURN s.sectionId, s.sectionTitle, count(ref) AS refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Section) OPTIONAL MATCH (ref:Section)-[:REFERENCES_SECTION]->(s) RETURN s.sectionId,count(DISTINCT ref) AS refCount ORDER BY refCount DESC,s.sectionId ASC LIMIT 10
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
    },
    {
      "name": "refCount",
      "nullable": false,
      "source_column_or_expression": "refCount",
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
        "field": "s.sectionId"
      }
    ],
    "tie_policy": "Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top ten Section-identifier groups or all when fewer exist",
    "tie_policy": "Section identifier ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-4/397b3998052b5ad3a25f92e1095d8680249a4af1990ca426d275107be93d46d3.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-4/397b3998052b5ad3a25f92e1095d8680249a4af1990ca426d275107be93d46d3.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `53f2a546d9d0290ff3aee47352725f453c96e22db617bf3be2938e8de9e4bd37`.

## RAN2_P3_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the cross-spec references from spec 38.300 into spec 38.331 (inter-spec dependency).

**Revised question:** List all distinct source/target Section identifier pairs with a REFERENCES_SECTION link from a Section belonging to specification number 38.300 to one belonging to specification number 38.331, across recorded versions.

**Proposed rationale:** Grade both directed roles, remove hidden ten-row cap, and describe documentary references rather than unproved technical dependency.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec {specNumber: '38.300'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: '38.331'}) RETURN s1.sectionId AS from_section, s2.sectionId AS to_section LIMIT 10
```

**Revised query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec {specNumber: '38.300'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: '38.331'}) RETURN DISTINCT s1.sectionId AS from_section, s2.sectionId AS to_section
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "from_section",
      "nullable": true,
      "source_column_or_expression": "from_section",
      "type": "string"
    },
    {
      "name": "to_section",
      "nullable": true,
      "source_column_or_expression": "to_section",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-5/06dbd1a7380fa25ccb8e15f4233a57b31493b55796b7e799d4f691e70b24e16c.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-5/06dbd1a7380fa25ccb8e15f4233a57b31493b55796b7e799d4f691e70b24e16c.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bea05603e32f6206f8dfe66f0ebc022c08f5dbd010225c90249a367bda48618d`.

## RAN2_P3_CQ2-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total number of section-to-section references (cross-reference volume).

**Revised question:** Return the number of distinct directed REFERENCES_SECTION relationships whose source and target both have label Section. Count parallel relationship records separately.

**Proposed rationale:** The original query accepted any endpoint labels; make section-to-section and relationship-count units explicit.

**Original query**

```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```

**Revised query**

```cypher
MATCH (:Section)-[r:REFERENCES_SECTION]->(:Section) RETURN count(DISTINCT r) AS totalRefs
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "totalRefs",
      "nullable": false,
      "source_column_or_expression": "totalRefs",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one aggregate row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-6/ce40d7506dc733e360f8b3476401f0b0f838f377cee58ee1cd1575accacc31c4.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-6/ce40d7506dc733e360f8b3476401f0b0f838f377cee58ee1cd1575accacc31c4.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `04edcdfe3eedb37f9ecd9dbf23a3cdef436753693d12a6c084f33c2934fd50e2`.

## RAN2_P3_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by intra-spec reference count (internal cohesion).

**Revised question:** Return the top five recorded specification numbers by number of distinct directed Section-node pairs linked by REFERENCES_SECTION, with both Sections belonging to some recorded version of that specification number. Include zero-reference specifications; rank by count descending and number ascending.

**Proposed rationale:** Define number-level version aggregation, count each directed pair once, and do not interpret the count as validated internal cohesion.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber, count(*) AS intraRefs ORDER BY intraRefs DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:specNumber}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:specNumber}) RETURN specNumber,count(DISTINCT CASE WHEN s1 IS NOT NULL AND s2 IS NOT NULL THEN [s1,s2] ELSE null END) AS intraRefs ORDER BY intraRefs DESC,specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": true,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "intraRefs",
      "nullable": false,
      "source_column_or_expression": "intraRefs",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "intraRefs"
      },
      {
        "direction": "asc",
        "field": "specNumber"
      }
    ],
    "tie_policy": "specification number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five specification-number groups or all when fewer exist",
    "tie_policy": "specification number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-7/a8f6976eb334ec4f3a0bcdafd00744c07047b06fd4adf905ede69d529f596bc4.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-7/a8f6976eb334ec4f3a0bcdafd00744c07047b06fd4adf905ede69d529f596bc4.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b8e7cd77e1a328209ea78fd420811fa39771b30cf0a5607286ef77470c5c0982`.

## RAN2_P3_CQ2-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 most-referenced sections within spec 38.331 (internal hubs).

**Revised question:** Return the top five Sections belonging to any recorded version of specification number 38.331 by number of distinct incoming REFERENCES_SECTION source Sections that also belong to that specification number. Include zero-reference targets and rank by count descending, then target Section identifier ascending.

**Proposed rationale:** State the number-level version scope, deduplicate source nodes, include the full target population, and define ranking ties.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId, s2.sectionTitle, count(*) AS refCount ORDER BY refCount DESC, s2.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s2:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.331'}) WITH DISTINCT s2 OPTIONAL MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.331'}), (s1)-[:REFERENCES_SECTION]->(s2) RETURN s2.sectionId,count(DISTINCT s1) AS refCount ORDER BY refCount DESC,s2.sectionId ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s2.sectionId",
      "nullable": true,
      "source_column_or_expression": "s2.sectionId",
      "type": "string"
    },
    {
      "name": "refCount",
      "nullable": false,
      "source_column_or_expression": "refCount",
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
        "field": "s2.sectionId"
      }
    ],
    "tie_policy": "target Section identifier ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five target Section-identifier groups or all when fewer exist",
    "tie_policy": "target Section identifier ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ2-8/c64d627bc6ad52e878004834d4b2629b92d6bcf64c4bc350615e1d14666c1bf8.json), [complete native rows](../reference_outputs/RAN2_P3_CQ2-8/c64d627bc6ad52e878004834d4b2629b92d6bcf64c4bc350615e1d14666c1bf8.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `05a0ebe38726f2dc3311387a0f6aba5d6eab27ddcf3cbee3fc557dc2d0ed9052`.

## RAN2_P3_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which spec does CR R2-2509337 modify (change target)?

**Revised question:** List all distinct specification numbers reached by MODIFIES from CR nodes with TDoc number R2-2509337.

**Proposed rationale:** Define set-valued targets rather than assume one specification; no version or contextual fields are requested.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.tdocNumber = 'R2-2509337' RETURN sp.specNumber
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.tdocNumber = 'R2-2509337' RETURN DISTINCT sp.specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-1/efb54048ecf4e5d59c4ddddb1383fb81a81bd9ce0c8f383ef25d874628548539.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-1/efb54048ecf4e5d59c4ddddb1383fb81a81bd9ce0c8f383ef25d874628548539.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `94ae1d4c9530c5f3b13e2f2ac78d74aba9565d1a46a7fc636bdea24c5fabbf51`.

## RAN2_P3_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['This structural replacement does not evaluate the original unsupported CR-to-specific-section modification claim.']

**Original question:** Return the top-level sections of spec 38.331 that CRs modify (CR-target layout).

**Revised question:** If any recorded CR has a MODIFIES link to specification number 38.331, list all level-1 Section identifier/number/title triples belonging to any recorded version of that specification.

**Proposed rationale:** The graph supports whole-specification CR targeting and structural sections, not proof those particular sections were modified; remove arbitrary latest-release and ten-row selections.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.331'}) WHERE hub.specRelease IS NULL WITH hub LIMIT 1 MATCH (rk:Spec {specNumber:'38.331'})-[:IN_RELEASE_OF]->(hub) WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (rk)<-[:BELONGS_TO_SPEC]-(s:Section {level: 1}) RETURN s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Section {level:1})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.331'}) WHERE EXISTS { MATCH (:CR)-[:MODIFIES]->(:Spec {specNumber:'38.331'}) } RETURN DISTINCT s.sectionId AS sectionId,s.sectionNumber AS sectionNumber,s.sectionTitle AS sectionTitle
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
      "name": "sectionTitle",
      "nullable": true,
      "source_column_or_expression": "sectionTitle",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-2/6e4f55876c5adde43297be4f863886385497da3afdcc55292eb16b2c065e2899.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-2/6e4f55876c5adde43297be4f863886385497da3afdcc55292eb16b2c065e2899.jsonl); 133 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `62bc8a624d90936ffc63972b8204f9fa7ce880e2ca396d128453982210ab7ba8`.

## RAN2_P3_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that modify spec 38.331 (change history).

**Revised question:** List all distinct CR TDoc numbers with a MODIFIES link to specification number 38.331.

**Proposed rationale:** A complete CR membership task must not silently keep only ten recent identifiers.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT cr.tdocNumber, cr.title, cr.status
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-3/686f1507efd22ae20be473ddd719dc535470a38ed58335ba3072683c6b2d0ca5.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-3/686f1507efd22ae20be473ddd719dc535470a38ed58335ba3072683c6b2d0ca5.jsonl); 10,599 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ac8c37ffdeb0e05e58779d630c073f6f04fe6c19cc4edf3c10f69d5493ce311f`.

## RAN2_P3_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that specify affected clauses (clause-tagged CRs).

**Revised question:** List all distinct CR TDoc-number/clausesAffected-text pairs where clausesAffected is recorded and is not the empty string.

**Proposed rationale:** Return the recorded literal clause text with each tagged CR, remove the hidden cap, and avoid claiming independently verified clause impact.

**Original query**

```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN DISTINCT cr.tdocNumber, cr.clausesAffected, cr.crCategory
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-4/318fe07d10e7c1220993e0b8b849d1986e40337becbf3d82399040c4c0e23f6b.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-4/318fe07d10e7c1220993e0b8b849d1986e40337becbf3d82399040c4c0e23f6b.jsonl); 3,855 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5a0e76ce633081c45a318d9ec5839c53ba81b45b41d42179fb0f973d3799ffca`.

## RAN2_P3_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs do CRs for Work Item NR_newRAT-Core modify (work-item impact)?

**Revised question:** List all distinct specification numbers reached by MODIFIES from CR nodes linked by RELATED_TO to NR_newRAT-Core.

**Proposed rationale:** The question requests specification membership, while original count fields and top-ten restriction add unrequested scoring and omissions.

**Original query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:CR)-[:RELATED_TO]->(:WorkItem {workItemCode:'NR_newRAT-Core'}), (t)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-5/ea4d0119373b60952352587a9a7c5cb1b5f4f6a60f881f7c2b68aa6e14971298.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-5/ea4d0119373b60952352587a9a7c5cb1b5f4f6a60f881f7c2b68aa6e14971298.jsonl); 23 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b5394a9fa02a92c312ff62849df2a71abce6aabf4ef1d8e605242f89567d2f7e`.

## RAN2_P3_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs modified by Huawei's CRs (vendor footprint).

**Revised question:** List all distinct specification numbers reached by MODIFIES from CR nodes submitted by companyName Huawei.

**Proposed rationale:** Grade requested specification membership; counts and output caps are not part of the original answer intent.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(:Company {companyName:'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-6/44bd2f8ad0caba070bec893b25f9718dda452cdc8633a44da753e9d2b6f6adb5.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-6/44bd2f8ad0caba070bec893b25f9718dda452cdc8633a44da753e9d2b6f6adb5.jsonl); 53 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `17b82ddedc1c548c8cb33c3635750ccaa6976949e99822a39d983df6db69060c`.

## RAN2_P3_CQ3-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Literal equality does not certify intended clause ranges, edition alignment, or actual section modification.']

**Original question:** List the CRs whose affected clauses resolve to actual sections of spec 38.331 (clause-to-section matching).

**Revised question:** For CRs modifying specification number 38.331, split nonempty clausesAffected text on commas and trim each token. List every distinct CR-TDoc-number/token/Section-identifier triple where a nonempty token exactly equals sectionNumber of a Section belonging to any recorded version of 38.331. Do not expand ranges or infer modified sections.

**Proposed rationale:** The original query hides arbitrary latest-release and ten-row selection; make this an exact literal-field join, not certified clause resolution or CR-to-section modification.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.331'})-[:IN_RELEASE_OF]->(hub:Spec {specNumber:'38.331'}) WHERE hub.specRelease IS NULL WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (cr:CR)-[:MODIFIES]->(hub2:Spec {specNumber:'38.331'}) WHERE hub2.specRelease IS NULL AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' UNWIND split(cr.clausesAffected, ',') AS clause WITH cr, rk, trim(clause) AS clause MATCH (s:Section {sectionNumber: clause})-[:BELONGS_TO_SPEC]->(rk) RETURN cr.tdocNumber, clause, s.sectionId ORDER BY cr.tdocNumber, clause, s.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.331'}) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' WITH DISTINCT cr UNWIND split(cr.clausesAffected,',') AS raw WITH cr,trim(raw) AS clause WHERE clause <> '' MATCH (s:Section {sectionNumber:clause})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.331'}) RETURN DISTINCT cr.tdocNumber,clause,s.sectionId
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
      "name": "clause",
      "nullable": true,
      "source_column_or_expression": "clause",
      "type": "string"
    },
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-7/b0b8e45715e503446b91582037090d580e399e270eaa03cb5cc2b6d4487496d9.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-7/b0b8e45715e503446b91582037090d580e399e270eaa03cb5cc2b6d4487496d9.jsonl); 16,297 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `cc19bacc5121ae0d1238219e1c6e5012ebd7498dc41810dc5a9b200c8a337513`.

## RAN2_P3_CQ3-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by Rel-18 CR count (release change footprint).

**Revised question:** Return the top five recorded specification numbers by number of distinct CR nodes targeting Rel-18 and modifying that specification number. Include zero-count specifications; rank by count descending and number ascending.

**Proposed rationale:** Deduplicate CRs across release/version links, define zero groups, and make ranking ties deterministic.

**Original query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCnt ORDER BY crCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (cr:CR)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}), (cr)-[:MODIFIES]->(sp) RETURN sp.specNumber,count(DISTINCT cr) AS crCnt ORDER BY crCnt DESC,sp.specNumber ASC LIMIT 5
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
      "name": "crCnt",
      "nullable": false,
      "source_column_or_expression": "crCnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crCnt"
      },
      {
        "direction": "asc",
        "field": "sp.specNumber"
      }
    ],
    "tie_policy": "specification number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five specification-number groups or all when fewer exist",
    "tie_policy": "specification number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ3-8/c9029d8d234f6c7324c742b1c815543bf8420efb2bbfcf1e311764d29efd854c.json), [complete native rows](../reference_outputs/RAN2_P3_CQ3-8/c9029d8d234f6c7324c742b1c815543bf8420efb2bbfcf1e311764d29efd854c.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c04f8066792fb08ee07106c5b0e074c6ee3ae721bffcffeb0e1f709a6de9b0c9`.

## RAN2_P3_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A REFERENCES relationship does not establish CR approval; state the documentary path and remove unrequested count/cap fields.']

**Original question:** Which specs are modified by CRs approved via resolutions (decision-to-spec trace)?

**Revised question:** List all distinct specification numbers reached by Resolution -&gt; REFERENCES CR -&gt; MODIFIES Spec.

**Proposed rationale:** A REFERENCES relationship does not establish CR approval; state the documentary path and remove unrequested count/cap fields.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(r) AS resolutions ORDER BY resolutions DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (:Resolution)-[:REFERENCES]->(:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ4-1/947fb451020a9a8bee08fde420ead35a8c88051e829b0377686a13e709824eb4.json), [complete native rows](../reference_outputs/RAN2_P3_CQ4-1/947fb451020a9a8bee08fde420ead35a8c88051e829b0377686a13e709824eb4.jsonl); 34 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `fb4d8967bd5c3cedae0853b6aad87fb351efc3954a54d143e9f12960020e8a76`.

## RAN2_P3_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original approval claim exceeds the relationship meaning; keep explicit reference roles and return all pairs.']

**Original question:** Which resolutions approved the CRs that modify spec 38.331 (approval trace)?

**Revised question:** List all distinct Resolution-identifier/CR-TDoc-number pairs connected by REFERENCES where the CR has a MODIFIES link to specification number 38.331.

**Proposed rationale:** The original approval claim exceeds the relationship meaning; keep explicit reference roles and return all pairs.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT r.resolutionId, cr.tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "r.resolutionId",
      "nullable": true,
      "source_column_or_expression": "r.resolutionId",
      "type": "string"
    },
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ4-2/88e8e400175f9de4f4a94af21ff38305e36070622fb65b0f612af36851814c73.json), [complete native rows](../reference_outputs/RAN2_P3_CQ4-2/88e8e400175f9de4f4a94af21ff38305e36070622fb65b0f612af36851814c73.jsonl); 857 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e11d7555d746bc09737dbc7151b514737a202b01844e1e335baad9369c13dd0d`.

## RAN2_P3_CQ4-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Exact token joins do not independently certify affected-clause semantics, intended edition, range expansion, or causal decision-to-section modification.']

**Original question:** Trace sections from a resolution through its CR's affected clauses (decision-to-section trace).

**Revised question:** Trace Resolution REFERENCES CR MODIFIES Spec paths by exact comma-token matching: split the CR clausesAffected text on commas, trim nonempty tokens, and match each token to sectionNumber in any recorded version with the modified specification number. Return distinct Resolution identifier, CR TDoc number, specification number, token, and Section identifier tuples. This is a literal documentary join.

**Proposed rationale:** The original query returned no Section despite asking a section trace; add explicit exact token/Section matching while withholding claims of causal approval, range parsing, or edition-correct modification.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN r.resolutionId, cr.tdocNumber, cr.clausesAffected, sp.specNumber ORDER BY r.resolutionId, cr.tdocNumber, sp.specNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' WITH DISTINCT r,cr,sp.specNumber AS specNumber UNWIND split(cr.clausesAffected,',') AS raw WITH r,cr,specNumber,trim(raw) AS clause WHERE clause <> '' MATCH (s:Section {sectionNumber:clause})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:specNumber}) RETURN DISTINCT r.resolutionId AS resolutionId,cr.tdocNumber AS tdocNumber,specNumber,clause,s.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": true,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "tdocNumber",
      "nullable": true,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": true,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "clause",
      "nullable": true,
      "source_column_or_expression": "clause",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": true,
      "source_column_or_expression": "sectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ4-3/9d7cb79d3321eee1d6aaf195d70e1d9bd5d0e7520f069c94470326e90213ecc7.json), [complete native rows](../reference_outputs/RAN2_P3_CQ4-3/9d7cb79d3321eee1d6aaf195d70e1d9bd5d0e7520f069c94470326e90213ecc7.jsonl); 1,833 native rows retained. The retained per-item check record has 19 passing scorer checks for this definition.

**Definition SHA-256:** `092346cfc4fd3be89df1b970197c075c4f342d7176300c19bf96a7f75dfb2aa4`.

## RAN2_P3_CQ4-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Most modified is not established by resolution count; define the documentary ranking metric and both counted units, with deterministic ties.']

**Original question:** Return the top 5 specs most modified along the resolution to CR to spec path (decision-impact ranking).

**Revised question:** Return the top five specification numbers by distinct Resolution-node count along Resolution REFERENCES CR MODIFIES Spec paths. For each, also return the distinct referenced CR-node count. Rank by Resolution count descending and specification number ascending; include only specifications with a matching path.

**Proposed rationale:** Most modified is not established by resolution count; define the documentary ranking metric and both counted units, with deterministic ties.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS resolutions, count(DISTINCT cr) AS crs ORDER BY resolutions DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS resolutions, count(DISTINCT cr) AS crs ORDER BY resolutions DESC, sp.specNumber ASC LIMIT 5
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
      "name": "resolutions",
      "nullable": true,
      "source_column_or_expression": "resolutions",
      "type": "integer"
    },
    {
      "name": "crs",
      "nullable": true,
      "source_column_or_expression": "crs",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "resolutions"
      },
      {
        "direction": "asc",
        "field": "sp.specNumber"
      }
    ],
    "tie_policy": "specification number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five matching specification-number groups or all when fewer exist",
    "tie_policy": "specification number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ4-4/fd5304dae5f24fa4cb9910d370b275570b6d89db1e68003ed0b0be8c56cdf084.json), [complete native rows](../reference_outputs/RAN2_P3_CQ4-4/fd5304dae5f24fa4cb9910d370b275570b6d89db1e68003ed0b0be8c56cdf084.jsonl); 5 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `d169cfb6ed73147511217fff6ee06e3b896b4263879f73c4b4f31e020823c40f`.

## RAN2_P3_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total number of CRs modifying spec 38.331 (change volume).

**Revised question:** Return the number of distinct CR nodes with a MODIFIES link to any Spec node numbered 38.331.

**Proposed rationale:** Count CR nodes once even if several specification/version links match.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN count(cr) AS totalCRs
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN count(DISTINCT cr) AS totalCRs
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "totalCRs",
      "nullable": false,
      "source_column_or_expression": "totalCRs",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one aggregate count row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ5-1/1467e0b09d75cac166728471ffb3ea2d85c33c2351172eb745c78d2946d94c51.json), [complete native rows](../reference_outputs/RAN2_P3_CQ5-1/1467e0b09d75cac166728471ffb3ea2d85c33c2351172eb745c78d2946d94c51.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8a94b3219ba01d5c5d51efdf7711e5a937f0b4042fce12853f55662761da2b0d`.

## RAN2_P3_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by CR count (most-changed specs).

**Revised question:** Return the top five recorded specification numbers by number of distinct CR nodes modifying any Spec node with that number. Include zero-count specifications; return number and count, ranked by count descending and specification number ascending.

**Proposed rationale:** Deduplicate CRs across versions/links, define the ranking population and grouping unit, and resolve ties.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) RETURN sp.specNumber,count(DISTINCT cr) AS crs ORDER BY crs DESC,sp.specNumber ASC LIMIT 5
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
      "name": "crs",
      "nullable": false,
      "source_column_or_expression": "crs",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crs"
      },
      {
        "direction": "asc",
        "field": "sp.specNumber"
      }
    ],
    "tie_policy": "specification number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top five specification-number groups or all when fewer exist",
    "tie_policy": "specification number ascending",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ5-2/d0c1223a828fb06c0282d74e84e0adc5000205b0886192270fbfb25498d885dd.json), [complete native rows](../reference_outputs/RAN2_P3_CQ5-2/d0c1223a828fb06c0282d74e84e0adc5000205b0886192270fbfb25498d885dd.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `bf1de513a361980e05a9fae75626de1b350a9b238555f7321432e5d2cc4ceda9`.

## RAN2_P3_CQ5-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original query mixed all hub CRs with one arbitrarily selected latest-release Section population and hid a top-five cap; define consistent number-level all-version counts and zero-denominator behavior.']

**Original question:** Return CR density (CRs per section) by spec (change-hotspot metric).

**Revised question:** For every recorded specification number, return the number of distinct CR nodes modifying any version, number of distinct Section nodes belonging to any version, and CR/Section ratio rounded to two decimals. Use null ratio when the Section count is zero.

**Proposed rationale:** The original query mixed all hub CRs with one arbitrarily selected latest-release Section population and hid a top-five cap; define consistent number-level all-version counts and zero-denominator behavior.

**Original query**

```cypher
MATCH (hub:Spec)<-[:MODIFIES]-(cr:CR) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCnt MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCnt, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCnt, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) WITH hub, crCnt, count(s) AS secCnt RETURN hub.specNumber AS specNumber, crCnt, secCnt, round(1.0 * crCnt / secCnt, 2) AS density ORDER BY density DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) WITH sp.specNumber AS specNumber,count(DISTINCT cr) AS crCnt OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:specNumber}) WITH specNumber,crCnt,count(DISTINCT s) AS secCnt RETURN specNumber,crCnt,secCnt,CASE WHEN secCnt=0 THEN null ELSE round(1.0*crCnt/secCnt,2) END AS density
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": true,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "crCnt",
      "nullable": false,
      "source_column_or_expression": "crCnt",
      "type": "integer"
    },
    {
      "name": "secCnt",
      "nullable": false,
      "source_column_or_expression": "secCnt",
      "type": "integer"
    },
    {
      "name": "density",
      "nullable": true,
      "source_column_or_expression": "density",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ5-3/487908563607f348cc3f71a8ca3a770eec45d7fdd857eca0efefd9a1b3f8ecee.json), [complete native rows](../reference_outputs/RAN2_P3_CQ5-3/487908563607f348cc3f71a8ca3a770eec45d7fdd857eca0efefd9a1b3f8ecee.jsonl); 123 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `e3dae187d6594c8a109f15a2d909e5e0b7badb904eb374b7215d99ef9a4d1e90`.

## RAN2_P3_CQ5-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the distribution of table counts across specs (table density).

**Revised question:** For every recorded specification number, return the number of distinct TSTable nodes linked by TABLE_IN_SECTION to Sections belonging to any recorded version. Include zero-count specifications.

**Proposed rationale:** A distribution requires all groups rather than an undocumented top five; count distinct target objects across shared Section/version links.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(t) AS tblCnt ORDER BY tblCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (x:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber,count(DISTINCT x) AS tblCnt
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
      "name": "tblCnt",
      "nullable": false,
      "source_column_or_expression": "tblCnt",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ5-4/45fdc0633f8164712c356e9f735d184fee44f1251a200c7f4a00e37c4f3b98d7.json), [complete native rows](../reference_outputs/RAN2_P3_CQ5-4/45fdc0633f8164712c356e9f735d184fee44f1251a200c7f4a00e37c4f3b98d7.jsonl); 123 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `871cdc6ad33fa4d58620f17a8c81017dcf281a8e8f37105eeca5f6abb5428884`.

## RAN2_P3_CQ5-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the distribution of figure counts across specs (figure density).

**Revised question:** For every recorded specification number, return the number of distinct TSFigure nodes linked by FIGURE_IN_SECTION to Sections belonging to any recorded version. Include zero-count specifications.

**Proposed rationale:** A distribution requires all groups rather than an undocumented top five; count distinct target objects across shared Section/version links.

**Original query**

```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(f) AS figCnt ORDER BY figCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (x:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber,count(DISTINCT x) AS figCnt
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_CQ5-5/dcbb1f2c3c4be31713d50280fb34e4484a073b08d760dd2e4011d8f6bcd0fa78.json), [complete native rows](../reference_outputs/RAN2_P3_CQ5-5/dcbb1f2c3c4be31713d50280fb34e4484a073b08d760dd2e4011d8f6bcd0fa78.jsonl); 123 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `79204ee36cc94a44003ad7a4c1b7e11f1a770978b6d265f4843d9397a6bff622`.

## RAN2_P3_P3-S8-CQ02

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are all item-level entity nodes linked to a section via definedInSection (grounding completeness)?

**Revised question:** Are all nodes with granularity item and at least one of the labels RRCParameter, CapabilityItem, Procedure, PerformanceRequirement, or ConformanceTest linked by an outgoing definedInSection relationship to a Section? Return one Boolean; an empty qualifying population returns true.

**Proposed rationale:** Replace the class/count diagnostic with the Boolean the original question asks, define universal empty-set semantics, and count each multi-label node once.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

**Revised query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,EXISTS { MATCH (n)-[:definedInSection]->(:Section) } AS isLinked RETURN count(n)=sum(CASE WHEN isLinked THEN 1 ELSE 0 END) AS allLinked
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
    "notes": "one Boolean aggregate row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_P3-S8-CQ02/331269ffa59d1d15385194f8fe415f5f5ecfcb886ed25752312c5cf0795ba8e6.json), [complete native rows](../reference_outputs/RAN2_P3_P3-S8-CQ02/331269ffa59d1d15385194f8fe415f5f5ecfcb886ed25752312c5cf0795ba8e6.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a7ecb04608033c99dfc88c693bba657fac119f098847fdfe2c66144a8cdb1626`.

## RAN2_P3_P3-S8-CQ04

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

**Original question:** Do the disjointWith relations among features (LTM, CHO, CPC, CPAC, etc.) match feature_catalog.disjoint_feature_groups (consistency check)?

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
    "notes": "one Boolean aggregate row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_P3-S8-CQ04/259d126a11584ec37e08b6c7bdfda2ea4992dd0704cfe06b05bc002da001d3d2.json), [complete native rows](../reference_outputs/RAN2_P3_P3-S8-CQ04/259d126a11584ec37e08b6c7bdfda2ea4992dd0704cfe06b05bc002da001d3d2.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d569c1c37097d8d563271bd2f06a57990d0aec4001696f310ac9ca2feb17ae0b`.

## RAN2_P3_P3-S8-CQ05

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the granularity-property distribution across the five entity classes (item-level v3.0 vs section-level legacy).

**Revised question:** For each of the labels RRCParameter, CapabilityItem, Procedure, PerformanceRequirement, and ConformanceTest, return every recorded granularity value and distinct node count. A multi-label node contributes once to each applicable label; retain null for missing granularity.

**Proposed rationale:** The original query took only the first applicable label and used an ambiguous literal unset sentinel; define per-label counts and null semantics without inferring a dataset version.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

**Revised query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) UNWIND [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']] AS class RETURN class,n.granularity AS granularity,count(DISTINCT n) AS c
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_P3-S8-CQ05/61fa244b640eb3e3799a4b119c67ff31f7fb1fd08d0c8bb5c5be7d28c291f153.json), [complete native rows](../reference_outputs/RAN2_P3_P3-S8-CQ05/61fa244b640eb3e3799a4b119c67ff31f7fb1fd08d0c8bb5c5be7d28c291f153.jsonl); 3 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b6d1cf04fdb5f3faafee438edcdb79936ca9e8d4af6da5fe9a0a8b96390838c9`.

## RAN2_P3_P3-S8-CQ07

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['No independently supplied list of the intended 28 LTM capability names is provided; this variant checks cardinality, not identity completeness.']

**Original question:** Are the 28 LTM capability items loaded as CapabilityItem nodes (LTM baseline check)?

**Revised question:** Does the frozen graph contain exactly 28 distinct capabilityItemName values beginning ltm- among CapabilityItem nodes with granularity item? Return one Boolean.

**Proposed rationale:** The original count and ten-name sample cannot establish membership of an unspecified 28-item external list; define the measurable cardinality test while explicitly withholding identity certification.

**Original query**

```cypher
MATCH (cap:CapabilityItem) WHERE cap.capabilityItemName STARTS WITH 'ltm-' AND cap.granularity = 'item' RETURN count(cap) AS ltm_cap_count, collect(cap.capabilityItemName)[..10] AS sample
```

**Revised query**

```cypher
MATCH (cap:CapabilityItem) WHERE cap.capabilityItemName STARTS WITH 'ltm-' AND cap.granularity='item' RETURN count(DISTINCT cap.capabilityItemName)=28 AS has28Names
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "has28Names",
      "nullable": false,
      "source_column_or_expression": "has28Names",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "notes": "one Boolean aggregate row",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P3_P3-S8-CQ07/e59eefe6d8d74e9c2b4e66db9dfc1d10bcf04548735e371a3dab242858ede3dd.json), [complete native rows](../reference_outputs/RAN2_P3_P3-S8-CQ07/e59eefe6d8d74e9c2b4e66db9dfc1d10bcf04548735e371a3dab242858ede3dd.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `5ac81bc833fdba920e47f9fd2854b04a09879e699404295b2c5c97367be61437`.

## RAN2_P4_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by CR R2-2001766 (cross-spec impact).

**Revised question:** List all distinct specification numbers reached from CR TDoc number R2-2001766 through AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC, or AFFECTS_OM_SPEC, excluding any number that the same CR directly MODIFIES.

**Proposed rationale:** Other specifications must exclude primary modification targets; grade requested target numbers rather than an unrequested relation-role field.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R2-2001766' RETURN type(r) AS relType, s.specNumber AS spec
```

**Revised query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R2-2001766' AND NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN DISTINCT type(r) AS relType, s.specNumber AS spec
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ2-1/d7b9b650587960802ef71e709e50c1a89fd671b628115587d968de4e5be2115d.json), [complete native rows](../reference_outputs/RAN2_P4_CQ2-1/d7b9b650587960802ef71e709e50c1a89fd671b628115587d968de4e5be2115d.jsonl); 4 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8ff90ed0a704cc450c5dbf06064ebad85c9e6afb3d8b0460b264a8599e4f1b81`.

## RAN2_P4_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which CRs modifying spec 38.331 also affect other specs (ripple-effect CRs)?

**Revised question:** List all distinct CR TDoc numbers modifying specification number 38.331 and having an AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC, or AFFECTS_OM_SPEC target with a different specification number.

**Proposed rationale:** An arbitrary affected target, including another version of 38.331, does not establish other specifications; enforce number inequality and remove the cap.

**Original query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.331'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.331'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber <> '38.331' } RETURN DISTINCT c.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ2-2/faf2a0dd0eb857c20693aff7237d1ac8634d40faf0860d503aa3a6a7cb167513.json), [complete native rows](../reference_outputs/RAN2_P4_CQ2-2/faf2a0dd0eb857c20693aff7237d1ac8634d40faf0860d503aa3a6a7cb167513.jsonl); 340 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f3bdb5d0bd6c4a4efa8f5caf0051fd92b85c7f3cff3d5f1e4132ca6f0c26b29d`.

## RAN2_P4_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that name spec 38.212 as an affected spec (incoming impact).

**Revised question:** List all distinct CR TDoc numbers with an AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC, or AFFECTS_OM_SPEC link to a specification numbered 38.212.

**Proposed rationale:** Remove an unrequested ten-row limit and grade the documented incoming target membership.

**Original query**

```cypher
MATCH (s:Spec {specNumber: '38.212'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Spec {specNumber: '38.212'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ2-3/229591e0e1b956aeebf9443e146cfb9898381e8c82918d52b3e2760c73eebeb7.json), [complete native rows](../reference_outputs/RAN2_P4_CQ2-3/229591e0e1b956aeebf9443e146cfb9898381e8c82918d52b3e2760c73eebeb7.jsonl); 8 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1b1ab15b4af6ec08de0cd63e22b14a9288103df0e2e6532511557bf18b8fd7c3`.

## RAN2_P4_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 CRs by cross-spec impact count (widest-reaching CRs).

**Revised question:** Return the top ten CR TDoc-number groups by number of distinct affected specification numbers reached through AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC, or AFFECTS_OM_SPEC, excluding primary MODIFIES numbers. Include zero-count CR groups. Return TDoc number and count; rank by count descending and TDoc number ascending.

**Proposed rationale:** Count unique other specification numbers rather than relationship records or versions, include the full CR population, and define deterministic ties.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
```

**Revised query**

```cypher
MATCH (c:CR) OPTIONAL MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN c.tdocNumber AS tdocNumber,count(DISTINCT s.specNumber) AS cnt ORDER BY cnt DESC,tdocNumber ASC LIMIT 10
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
      "name": "cnt",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "cnt"
      },
      {
        "direction": "asc",
        "field": "tdocNumber"
      }
    ],
    "tie_policy": "CR TDoc number ascending"
  },
  "cardinality_policy": {
    "mode": "top_k",
    "notes": "top ten CR TDoc-number groups or all when fewer exist",
    "tie_policy": "CR TDoc number ascending",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ2-4/3d2df5e7c2b06025cb26af9f2ad34315e9482807352da3b333b3a0953206e070.json), [complete native rows](../reference_outputs/RAN2_P4_CQ2-4/3d2df5e7c2b06025cb26af9f2ad34315e9482807352da3b333b3a0953206e070.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0729a5c07c6fba77c1b8ee81423c6c1bb2914d7b19d7dc9e035fcb129503661d`.

## RAN2_P4_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs in CR pack RP-253714 with their change summaries (pack contents).

**Revised question:** List all distinct CR TDoc-number/change-summary pairs linked by HAS_CR from CR pack RP-253714, preserving null for a missing summary.

**Proposed rationale:** Pack contents is a complete membership/content task, not a ten-row sample.

**Original query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-253714'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-253714'})-[:HAS_CR]->(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary
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
      "name": "summary",
      "nullable": true,
      "source_column_or_expression": "summary",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ3-1/229c3f8ca0eecc54ab5d7e7b3e45f58d8fc9d8e3ac5d3c7e6eb755eb45f0e489.json), [complete native rows](../reference_outputs/RAN2_P4_CQ3-1/229c3f8ca0eecc54ab5d7e7b3e45f58d8fc9d8e3ac5d3c7e6eb755eb45f0e489.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `678352a51a261da59a92099b1465ef045957dd883bf2dd218e50c1333b17a62b`.

## RAN2_P4_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CR packs containing CRs for NR_newRAT work items (pack grouping).

**Revised question:** List all distinct CR pack identifiers reached by BELONGS_TO_CR_PACK from CRs whose recorded workItemCode contains the case-sensitive literal NR_newRAT.

**Proposed rationale:** Define the lexical work-item selector, remove the hidden cap, and score only requested pack identifiers.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crPackId",
      "nullable": true,
      "source_column_or_expression": "crPackId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ3-2/a5b2e2fb799004c8212955a6f4e408c0ee75cedabb713119533415dc1aaeb072.json), [complete native rows](../reference_outputs/RAN2_P4_CQ3-2/a5b2e2fb799004c8212955a6f4e408c0ee75cedabb713119533415dc1aaeb072.jsonl); 153 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7d03dd01f7f64d2111f0d5c368e1708c5c5a329d52e776721dc75fb2fadd3c57`.

## RAN2_P4_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The metadata value is observable; it does not independently establish actual plenary submission. Remove the hidden cap.']

**Original question:** List the CR packs submitted to TSG meeting RAN#110 (plenary submission list).

**Revised question:** List all distinct CR pack identifiers whose recorded tsgMeeting property equals RAN#110.

**Proposed rationale:** The metadata value is observable; it does not independently establish actual plenary submission. Remove the hidden cap.

**Original query**

```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#110'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#110'}) RETURN DISTINCT pack.crPackId AS crPackId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crPackId",
      "nullable": true,
      "source_column_or_expression": "crPackId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.json), [complete native rows](../reference_outputs/RAN2_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.jsonl); 26 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `eff134a99b85e12d87735d1fd7b58802c1008be8886f66c56c4faa54884d6446`.

## RAN2_P4_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the change reasons of CRs modifying section 5.3.5 of spec 38.331 (section change history).

**Revised question:** Across all recorded versions of specification number 38.331, list all distinct CR TDoc-number/reasonForChange pairs connected by MODIFIES_SECTION to sections numbered 5.3.5; retain missing reasons as null.

**Proposed rationale:** The graph has a named section-target relationship; scope the claim to those recorded links and remove version-order sampling.

**Original query**

```cypher
MATCH (sec:Section {sectionNumber: '5.3.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber: '5.3.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.reasonForChange AS reason
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
      "name": "reason",
      "nullable": true,
      "source_column_or_expression": "reason",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ4-1/98cf7a79c8ea3f7e8c82e93798378f49153add82a5d0ba2116b038d90305dce6.json), [complete native rows](../reference_outputs/RAN2_P4_CQ4-1/98cf7a79c8ea3f7e8c82e93798378f49153add82a5d0ba2116b038d90305dce6.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b576d7b98c9f80a3c7bfd550aab4e048f8ec324ba638421293573cbdb44e9940`.

## RAN2_P4_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['Agreement REFERENCES does not establish approval; remove the unrequested five-record WITH limit and grade all requested text fields.']

**Original question:** Return the change reasons and summaries of CRs approved by agreements (approved-change review).

**Revised question:** For every CR referenced by any Agreement and having a recorded reasonForChange, return each distinct TDoc-number/reason/summary tuple; retain missing summary as null.

**Proposed rationale:** Agreement REFERENCES does not establish approval; remove the unrequested five-record WITH limit and grade all requested text fields.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
```

**Revised query**

```cypher
MATCH (:Agreement)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL RETURN DISTINCT c.tdocNumber AS tdocNumber,c.reasonForChange AS reason,c.summaryOfChange AS summary
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
      "name": "reason",
      "nullable": true,
      "source_column_or_expression": "reason",
      "type": "string"
    },
    {
      "name": "summary",
      "nullable": true,
      "source_column_or_expression": "summary",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ4-2/5bdc60a5d2ebe1555fcf17269ba5966c61e5027260832e0c5eb33a8d1b79424f.json), [complete native rows](../reference_outputs/RAN2_P4_CQ4-2/5bdc60a5d2ebe1555fcf17269ba5966c61e5027260832e0c5eb33a8d1b79424f.jsonl); 162 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `90e1e8ecb29e65841513fa84a88da757a8d72dd331d0349b4b08d83c88080633`.

## RAN2_P4_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections modified by CRs for NR_newRAT work items (work-item section footprint).

**Revised question:** List all distinct Section identifiers reached by MODIFIES_SECTION from CRs whose recorded workItemCode contains the case-sensitive literal NR_newRAT.

**Proposed rationale:** Keep the explicit documentary section-target relationship and lexical work-item selection, removing the unrequested cap.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json), [complete native rows](../reference_outputs/RAN2_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl); 859 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `020ba2bdfaa93dc891eec06ee682121e95ed392848c03c72e00f7e7cf4c8c719`.

## RAN2_P4_CQ4-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by Samsung's CRs (vendor cross-spec impact).

**Revised question:** List all distinct specification numbers reached through AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC, or AFFECTS_OM_SPEC from CRs submitted by companyName Samsung, excluding any number directly MODIFIES-linked from the same CR.

**Proposed rationale:** Other must exclude primary targets, and a contains-company match must not silently mix names; specify exact recorded company identity and remove the cap.

**Original query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName = 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS spec
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ4-4/305839642e5fb3743209a413181a6e57ae914d5d970508ccf396ac330bd1084c.json), [complete native rows](../reference_outputs/RAN2_P4_CQ4-4/305839642e5fb3743209a413181a6e57ae914d5d970508ccf396ac330bd1084c.jsonl); 23 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a25ad9afc216f748da7df67b87ecca939e72eaf5438ba7a872b513df3891681f`.

## RAN2_P4_CQ4-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['REFERENCES does not certify approval; enforce the canonical meeting identity and remove the hidden sample cap.']

**Original question:** List the change summaries of CRs approved at meeting 132 (meeting change digest).

**Revised question:** List all distinct CR TDoc-number/change-summary pairs referenced by an Agreement MADE_AT RAN2#132, retaining only recorded nonnull summaries.

**Proposed rationale:** REFERENCES does not certify approval; enforce the canonical meeting identity and remove the hidden sample cap.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumberInt = 132 WITH a MATCH (a)-[:REFERENCES]->(c:CR) WHERE c.summaryOfChange IS NOT NULL RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.canonicalMeetingNumber = 'RAN2#132' WITH a MATCH (a)-[:REFERENCES]->(c:CR) WHERE c.summaryOfChange IS NOT NULL RETURN DISTINCT c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary
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
      "name": "summary",
      "nullable": true,
      "source_column_or_expression": "summary",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P4_CQ4-5/7ec0b69fbc01ab7124f1243826bc2bb4d45271779e3c4e99757655f98c4d382f.json), [complete native rows](../reference_outputs/RAN2_P4_CQ4-5/7ec0b69fbc01ab7124f1243826bc2bb4d45271779e3c4e99757655f98c4d382f.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a83c6bb47a175b93168113a836ed637e0e8dd48cf80bb2fc76a505fea1a94dc4`.

## RAN2_P5_TR-CQ-1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the completed TRs targeting Rel-17 (release study inventory).

**Revised question:** List all distinct TR numbers linked by TARGET_RELEASE to Rel-17 and having recorded trStatus Completed.

**Proposed rationale:** Grade requested TR membership without unrequested titles and make the recorded-status criterion explicit.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release)
                  WHERE r.releaseName = 'Rel-17' AND tr.trStatus = 'Completed'
                  RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release)
                  WHERE r.releaseName = 'Rel-17' AND tr.trStatus = 'Completed'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-1-1/1e9a86e3d8a7a4858a3ef1c5e4ed6831d7c0f06c307d124e64ab0fbcc39f9eff.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-1-1/1e9a86e3d8a7a4858a3ef1c5e4ed6831d7c0f06c307d124e64ab0fbcc39f9eff.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `03837bb87328fcf7dc45e4d335c4de5039bdabc632729ec426487d221e7a009e`.

## RAN2_P5_TR-CQ-1-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The frozen graph does not establish current real-world study status; scope the task to its recorded values.']

**Original question:** List the TRs currently Living (ongoing studies).

**Revised question:** List all distinct TR numbers with recorded trStatus Living in the frozen graph.

**Proposed rationale:** The frozen graph does not establish current real-world study status; scope the task to its recorded values.

**Original query**

```cypher
MATCH (tr:TechnicalReport)
                  WHERE tr.trStatus = 'Living'
                  RETURN tr.trNumber, tr.trTitle
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)
                  WHERE tr.trStatus = 'Living'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-1-4/2b0dad2795b84b6aae41b031a337b495c8ca4ae3c60019f3623706e2804d8d09.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-1-4/2b0dad2795b84b6aae41b031a337b495c8ca4ae3c60019f3623706e2804d8d09.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `51e3ab33de4926e390bb470c6dd4c1bfea4cfa18b6503406149bd7622408168a`.

## RAN2_P5_TR-CQ-2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs impacted by TR 38.825 with their impact type (study-to-spec impact).

**Revised question:** List all distinct specification-number/impact-type pairs connected from TR 38.825 through HAS_TR_IMPACT and IMPACTS_SPEC.

**Proposed rationale:** Grade both explicitly requested roles and describe recorded impact metadata, not independent technical causation.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN DISTINCT s.specNumber, imp.impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.specNumber",
      "nullable": true,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "imp.impactType",
      "nullable": true,
      "source_column_or_expression": "imp.impactType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-2-1/fb755f080a23883112f45a57776b453b6bb9d2aba52cab54094f9c2bac561015.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-2-1/fb755f080a23883112f45a57776b453b6bb9d2aba52cab54094f9c2bac561015.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3bed68998d0f2e65e0e427543702cd65385cf397e05f57721b4808d9fc18b55a`.

## RAN2_P5_TR-CQ-2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the impact-type breakdown of TR 38.804 (impact profile).

**Revised question:** For TR number 38.804, return each recorded impactType and the number of distinct HAS_TR_IMPACT target nodes with that type, preserving null as a missing-type group.

**Proposed rationale:** A breakdown requires both type and count; deduplicate shared impact nodes across graph TR versions.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.804'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.804'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(DISTINCT imp) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "imp.impactType",
      "nullable": true,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "cnt",
      "nullable": false,
      "source_column_or_expression": "cnt",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-2-2/521d99f10dad21f191d0f6a7c0ef7de58dd8a7d82e8772c9bd244b4918033481.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-2-2/521d99f10dad21f191d0f6a7c0ef7de58dd8a7d82e8772c9bd244b4918033481.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c69e584f78c664099dadddcf3620b6d54aeb2a009a0ee7406b63e871a8343a7a`.

## RAN2_P5_TR-CQ-2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The metadata does not independently prove a TR spawned a new TS; define the recorded category membership.']

**Original question:** List the TRs that spawned a new TS (new-spec studies).

**Revised question:** List all distinct TR numbers with a HAS_TR_IMPACT target whose recorded impactType is NewTS.

**Proposed rationale:** The metadata does not independently prove a TR spawned a new TS; define the recorded category membership.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-2-3/25c0252cee590a5c71bb274b1558ee9eb6858f62ea65c3490f6ef7fa4401f738.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-2-3/25c0252cee590a5c71bb274b1558ee9eb6858f62ea65c3490f6ef7fa4401f738.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `abae5dad12bb6ac613107594e448babb3dd4ef871d007a64cf92808ceafb1692`.

## RAN2_P5_TR-CQ-2-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['A recorded category can be measured without asserting independently verified actual section extension.']

**Original question:** List the TRs that extend existing sections (section-extension studies).

**Revised question:** List all distinct TR numbers with a HAS_TR_IMPACT target whose recorded impactType is ExtendSection.

**Proposed rationale:** A recorded category can be measured without asserting independently verified actual section extension.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-2-4/81bae9cdc68c73f5edc0e4936060beacc15a5ddd822faa903bd7bfca59609119.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-2-4/81bae9cdc68c73f5edc0e4936060beacc15a5ddd822faa903bd7bfca59609119.jsonl); 6 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f711f0928e894d8605e6f57da5d144c6d8ef1f49d5b8811bc1d966bbceb62005`.

## RAN2_P5_TR-CQ-2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs impacted spec 38.300 (reverse impact lookup)?

**Revised question:** List all distinct TR numbers connected to specification number 38.300 through HAS_TR_IMPACT and IMPACTS_SPEC.

**Proposed rationale:** Grade requested reverse TR membership; impact type is context rather than an answer field.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN tr.trNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN DISTINCT tr.trNumber, imp.impactType
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-2-5/1dd8713783e360522d2e34e86cb4b819c3f5d7084c5dc0adf16c6081ab6d403c.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-2-5/1dd8713783e360522d2e34e86cb4b819c3f5d7084c5dc0adf16c6081ab6d403c.jsonl); 5 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8f753b320dec0bea1f2cb50685614a395f1e70c644e00a06a40fb553862c59ce`.

## RAN2_P5_TR-CQ-3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs does TR 38.825 impact, and how (impact detail)?

**Revised question:** For TR 38.825, list all distinct target specification-number/recorded-impact-type/recorded-impact-description triples connected through HAS_TR_IMPACT and IMPACTS_SPEC.

**Proposed rationale:** How-impact is represented by the stored type and description; score all three requested fields without an independent causal claim.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN DISTINCT s.specNumber, imp.impactType, imp.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.specNumber",
      "nullable": true,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "imp.impactType",
      "nullable": true,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "imp.impactDescription",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-3-1/c200edc695127c1bd9940b40ce62972ac75e40a38b4fdaaa69134dee42ac8628.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-3-1/c200edc695127c1bd9940b40ce62972ac75e40a38b4fdaaa69134dee42ac8628.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `ce3767f40ec2e40b31aaab1b8e3ff9406a1bf93bbceb0c66a5e45a83c1be1dcf`.

## RAN2_P5_TR-CQ-3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return TR 38.836's impact on specs 38.300 and 38.321 (targeted impact).

**Revised question:** For TR 38.836, list all distinct target specification-number/recorded-impact-type/recorded-impact-description triples for target numbers 38.300 and 38.321.

**Proposed rationale:** Make target scope and each requested detail explicit, preserving separate recorded impacts.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.836'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  WHERE s.specNumber IN ['38.300', '38.321']
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.836'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  WHERE s.specNumber IN ['38.300', '38.321']
                  RETURN DISTINCT s.specNumber, imp.impactType, imp.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "s.specNumber",
      "nullable": true,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "imp.impactType",
      "nullable": true,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "imp.impactDescription",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-3-2/11a270b5ecbc02205607efcef0bb76fb9b6497b58ad4ab733a6d351b1d21d3d4.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-3-2/11a270b5ecbc02205607efcef0bb76fb9b6497b58ad4ab733a6d351b1d21d3d4.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `2673ce01921b0852dae21e0d39e9b666948f1886d1d0343e0a89e8cb732a778c`.

## RAN2_P5_TR-CQ-3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return TR 38.874's impact on spec 38.300 (targeted impact).

**Revised question:** For TR 38.874 and target specification number 38.300, list all distinct recorded impact-type/impact-description pairs connected through HAS_TR_IMPACT and IMPACTS_SPEC.

**Proposed rationale:** The requested impact content is the stored type and description; contextual TR/spec keys need not be graded.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.874'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.874'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN DISTINCT imp.impactType, imp.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "imp.impactType",
      "nullable": true,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "imp.impactDescription",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-3-3/845a00859210f3dba5d97b0554bf982b44b01e39f21ea87326a9233319ce6ec5.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-3-3/845a00859210f3dba5d97b0554bf982b44b01e39f21ea87326a9233319ce6ec5.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d5da5395a934cd19de3f6d3770a8468c63b610645ca5c28a08fcabc96d86c709`.

## RAN2_P5_TR-CQ-4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the Rel-17 TRs with their spec impacts and impact types (release impact map).

**Revised question:** For every distinct TR number linked by TARGET_RELEASE to Rel-17, return the set of recorded specification-number/impact-type pairs connected through HAS_TR_IMPACT and IMPACTS_SPEC. Return an empty set for a TR with no such complete path; preserve null type on a linked impact.

**Proposed rationale:** Define one TR-number group, deduplicate repeated release/impact links, and distinguish an empty impact collection from an artificial null/null map.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber AS trNumber,collect(DISTINCT CASE WHEN s IS NULL THEN null ELSE {spec:s.specNumber,type:imp.impactType} END) AS impacts
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
      "json_schema": {
        "items": {
          "additionalProperties": false,
          "properties": {
            "spec": {
              "type": [
                "string",
                "null"
              ]
            },
            "type": {
              "type": [
                "string",
                "null"
              ]
            }
          },
          "required": [
            "spec",
            "type"
          ],
          "type": "object"
        },
        "type": "array"
      },
      "name": "impacts",
      "nested_array_semantics": {
        "$": "set"
      },
      "nested_collection_definition": {
        "duplicates": "ignored",
        "element_type": "object",
        "empty_semantics": "no complete TRImpact/Spec path yields []",
        "fields": [
          {
            "name": "spec",
            "nullable": true,
            "type": "string"
          },
          {
            "name": "type",
            "nullable": true,
            "type": "string"
          }
        ],
        "kind": "set"
      },
      "nullable": false,
      "source_column_or_expression": "impacts",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-4-1/07fa3517a9e8ea81efd31b17d0a8d12c224306941335d4e9d2415279f854c5e0.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-4-1/07fa3517a9e8ea81efd31b17d0a8d12c224306941335d4e9d2415279f854c5e0.jsonl); 2 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `d1e1172b1a60b9b68186794f2641a08c8f5ad13e033d2cb6b069676527941328`.

## RAN2_P5_TR-CQ-4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the status and study scope of TR 38.744 (study snapshot).

**Revised question:** Return all distinct recorded status/scope pairs for TR number 38.744 in the frozen graph.

**Proposed rationale:** Grade only the requested fields and preserve multiple recorded states rather than imply a current snapshot beyond the graph.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.744'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.744'})
                  RETURN DISTINCT tr.trNumber, tr.trStatus, tr.scope
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN2_P5_TR-CQ-4-2/647e8bfadc9e96062dc19399dbb2d704bfa6cdbbed0702caa4112d7ce0cccbc3.json), [complete native rows](../reference_outputs/RAN2_P5_TR-CQ-4-2/647e8bfadc9e96062dc19399dbb2d704bfa6cdbbed0702caa4112d7ce0cccbc3.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b5f2328318180e0c24bea987b2bbdd49504286113ec128db5a248da9957194ee`.
