# RAN3 itemized contract changes

This page accounts for 112 original Core IDs: 88 proposed clarifications and 24 substantive variants.

Each entry retains the exact original and revised question and query. The change rationale is a proposal, not a completed author semantic judgment. Technical check counts concern scorer enforcement and captured reference consistency; all author semantic reviews remain pending.

[Review guide](../REVIEW_GUIDE.md) · [Full technical task ledger](../canonical_tasks.jsonl) · [Per-item scorer checks](../provenance/adversarial_validation.json)

| ID | Proposed change class | Required fields | Native rows | Scorer checks |
| --- | --- | --- | ---: | ---: |
| [RAN3_P1_CQ1-1](#ran3_p1_cq1-1) | Proposed clarification | tdocNumber (string) | 66 | 7/7 |
| [RAN3_P1_CQ1-2](#ran3_p1_cq1-2) | Proposed clarification | tdocNumber (string) | 30 | 7/7 |
| [RAN3_P1_CQ1-3](#ran3_p1_cq1-3) | Proposed clarification | tdocNumber (string) | 327 | 7/7 |
| [RAN3_P1_CQ1-4](#ran3_p1_cq1-4) | Substantive variant | tdocNumber (string) | 5,948 | 7/7 |
| [RAN3_P1_CQ1-5](#ran3_p1_cq1-5) | Proposed clarification | tdocNumber (string) | 137 | 7/7 |
| [RAN3_P1_CQ1-6](#ran3_p1_cq1-6) | Proposed clarification | status (string) | 1 | 7/7 |
| [RAN3_P1_CQ1-7](#ran3_p1_cq1-7) | Proposed clarification | purpose (string) | 1 | 7/7 |
| [RAN3_P1_CQ1-8](#ran3_p1_cq1-8) | Proposed clarification | contactName (string), contactId (string) | 1 | 10/10 |
| [RAN3_P1_CQ1-9](#ran3_p1_cq1-9) | Substantive variant | agendaNumber (string), description (string) | 42 | 10/10 |
| [RAN3_P1_CQ2-1](#ran3_p1_cq2-1) | Proposed clarification | predecessorTdoc (string) | 1 | 7/7 |
| [RAN3_P1_CQ2-3](#ran3_p1_cq2-3) | Proposed clarification | replyTargetTdoc (string) | 1 | 7/7 |
| [RAN3_P1_CQ2-4](#ran3_p1_cq2-4) | Proposed clarification | specNumber (string) | 1 | 7/7 |
| [RAN3_P1_CQ2-5](#ran3_p1_cq2-5) | Proposed clarification | category (string), clausesAffected (string) | 1 | 10/10 |
| [RAN3_P1_CQ2-6](#ran3_p1_cq2-6) | Proposed clarification | tdocNumber (string) | 3 | 7/7 |
| [RAN3_P1_CQ2-7](#ran3_p1_cq2-7) | Proposed clarification | lsTdoc (string) | 20 | 7/7 |
| [RAN3_P1_CQ3-1](#ran3_p1_cq3-1) | Proposed clarification | tdocNumber (string) | 2,010 | 7/7 |
| [RAN3_P1_CQ3-2](#ran3_p1_cq3-2) | Proposed clarification | companyName (string), tdocCount (integer) | 7 | 10/10 |
| [RAN3_P1_CQ3-3](#ran3_p1_cq3-3) | Proposed clarification | companyName (string), tdocCount (integer) | 85 | 10/10 |
| [RAN3_P1_CQ3-4](#ran3_p1_cq3-4) | Proposed clarification | agreedFraction (number) | 1 | 7/7 |
| [RAN3_P1_CQ3-5](#ran3_p1_cq3-5) | Proposed clarification | companyName (string), tdocNumber (string) | 354 | 10/10 |
| [RAN3_P1_CQ3-6](#ran3_p1_cq3-6) | Proposed clarification | workItemCode (string), tdocCount (integer) | 282 | 10/10 |
| [RAN3_P1_CQ4-1](#ran3_p1_cq4-1) | Substantive variant | canonicalMeetingNumber (string), tdocNumber (string) | 493 | 10/10 |
| [RAN3_P1_CQ4-2](#ran3_p1_cq4-2) | Proposed clarification | status (string), tdocCount (integer) | 7 | 10/10 |
| [RAN3_P1_CQ4-3](#ran3_p1_cq4-3) | Proposed clarification | tdocNumber (string) | 2 | 7/7 |
| [RAN3_P2_CQ1-1](#ran3_p2_cq1-1) | Proposed clarification | agreementId (string), content (string) | 84 | 10/10 |
| [RAN3_P2_CQ1-2](#ran3_p2_cq1-2) | Proposed clarification | conclusionId (string), content (string) | 214 | 10/10 |
| [RAN3_P2_CQ1-3](#ran3_p2_cq1-3) | Proposed clarification | workingAssumptionId (string), content (string) | 17 | 10/10 |
| [RAN3_P2_CQ1-4](#ran3_p2_cq1-4) | Proposed clarification | resolutionId (string), meeting (string) | 55 | 10/10 |
| [RAN3_P2_CQ1-5](#ran3_p2_cq1-5) | Proposed clarification | resolutionId (string), meeting (string) | 132 | 10/10 |
| [RAN3_P2_CQ1-6](#ran3_p2_cq1-6) | Substantive variant | resolutionId (string), meeting (string) | 104 | 10/10 |
| [RAN3_P2_CQ1-8](#ran3_p2_cq1-8) | Proposed clarification | agendaNumber (string), resolutionCount (integer) | 10 | 10/10 |
| [RAN3_P2_CQ2-1](#ran3_p2_cq2-1) | Proposed clarification | tdocNumber (string) | 41 | 7/7 |
| [RAN3_P2_CQ2-2](#ran3_p2_cq2-2) | Proposed clarification | resolutionId (string) | 358 | 7/7 |
| [RAN3_P2_CQ2-3](#ran3_p2_cq2-3) | Proposed clarification | resolutionId (string) | 941 | 7/7 |
| [RAN3_P2_CQ2-4](#ran3_p2_cq2-4) | Proposed clarification | specNumber (string), tdocCount (integer) | 57 | 10/10 |
| [RAN3_P2_CQ3-1](#ran3_p2_cq3-1) | Substantive variant | referencedTdocCount (integer) | 1 | 7/7 |
| [RAN3_P2_CQ3-2](#ran3_p2_cq3-2) | Proposed clarification | companyName (string), resolutionCount (integer) | 10 | 10/10 |
| [RAN3_P2_CQ3-3](#ran3_p2_cq3-3) | Substantive variant | companyName (string), tdocCount (integer) | 41 | 10/10 |
| [RAN3_P2_CQ4-1](#ran3_p2_cq4-1) | Substantive variant | companyName (string), meeting (string) | 17 | 10/10 |
| [RAN3_P2_CQ4-2](#ran3_p2_cq4-2) | Proposed clarification | agendaNumber (string), meeting (string) | 46 | 10/10 |
| [RAN3_P2_CQ4-3](#ran3_p2_cq4-3) | Proposed clarification | companyName (string), summaryCount (integer) | 10 | 10/10 |
| [RAN3_P2_CQ6-1](#ran3_p2_cq6-1) | Proposed clarification | meeting (string), meetingNumber (integer), resolutionCount (integer) | 16 | 13/13 |
| [RAN3_P2_CQ6-2](#ran3_p2_cq6-2) | Substantive variant | meeting (string), meetingNumber (integer), resolutionCount (integer) | 58 | 13/13 |
| [RAN3_P2_CQ6-3](#ran3_p2_cq6-3) | Proposed clarification | meeting (string), meetingNumber (integer), summaryCount (integer) | 14 | 13/13 |
| [RAN3_P3_CQ1-1](#ran3_p3_cq1-1) | Proposed clarification | sectionId (string), sectionNumber (string), title (string), level (integer) | 3,208 | 16/16 |
| [RAN3_P3_CQ1-10](#ran3_p3_cq1-10) | Substantive variant | specNumber (string), sectionId (string) | 5 | 10/10 |
| [RAN3_P3_CQ1-11](#ran3_p3_cq1-11) | Proposed clarification | specNumber (string), sectionCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ1-12](#ran3_p3_cq1-12) | Proposed clarification | level (integer), sectionCount (integer) | 4 | 10/10 |
| [RAN3_P3_CQ1-13](#ran3_p3_cq1-13) | Proposed clarification | sectionId (string) | 184 | 7/7 |
| [RAN3_P3_CQ1-14](#ran3_p3_cq1-14) | Proposed clarification | sectionCount (integer), tableCount (integer), figureCount (integer) | 1 | 13/13 |
| [RAN3_P3_CQ1-15](#ran3_p3_cq1-15) | Proposed clarification | sectionId (string), tableCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ1-16](#ran3_p3_cq1-16) | Proposed clarification | sectionId (string), figureCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ1-2](#ran3_p3_cq1-2) | Substantive variant | sectionId (string), sectionNumber (string), title (string) | 1,119 | 13/13 |
| [RAN3_P3_CQ1-4](#ran3_p3_cq1-4) | Proposed clarification | sectionId (string), sectionNumber (string), title (string) | 55 | 13/13 |
| [RAN3_P3_CQ1-5](#ran3_p3_cq1-5) | Substantive variant | tableId (string), tableNumber (string), caption (string) | 10 | 13/13 |
| [RAN3_P3_CQ1-6](#ran3_p3_cq1-6) | Substantive variant | figureId (string), figureNumber (string), caption (string) | 12 | 13/13 |
| [RAN3_P3_CQ1-7](#ran3_p3_cq1-7) | Substantive variant | sectionId (string) | 5 | 7/7 |
| [RAN3_P3_CQ1-8](#ran3_p3_cq1-8) | Proposed clarification | tableId (string), tableNumber (string), caption (string) | 10 | 13/13 |
| [RAN3_P3_CQ1-9](#ran3_p3_cq1-9) | Proposed clarification | sectionId (string) | 193 | 7/7 |
| [RAN3_P3_CQ2-1](#ran3_p3_cq2-1) | Substantive variant | sectionId (string) | 5 | 7/7 |
| [RAN3_P3_CQ2-2](#ran3_p3_cq2-2) | Substantive variant | sectionId (string) | 20 | 7/7 |
| [RAN3_P3_CQ2-3](#ran3_p3_cq2-3) | Proposed clarification | sectionId (string), referringSectionCount (integer) | 67 | 10/10 |
| [RAN3_P3_CQ2-4](#ran3_p3_cq2-4) | Proposed clarification | sectionId (string), referringSectionCount (integer) | 10 | 10/10 |
| [RAN3_P3_CQ2-5](#ran3_p3_cq2-5) | Proposed clarification | sectionId (string), specNumber (string) | 111 | 10/10 |
| [RAN3_P3_CQ2-6](#ran3_p3_cq2-6) | Proposed clarification | referenceEdgeCount (integer) | 1 | 7/7 |
| [RAN3_P3_CQ2-7](#ran3_p3_cq2-7) | Proposed clarification | specNumber (string), referenceEdgeCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ2-8](#ran3_p3_cq2-8) | Proposed clarification | sectionId (string), referringSectionCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ3-1](#ran3_p3_cq3-1) | Proposed clarification | specNumber (string), clausesAffected (string) | 1 | 10/10 |
| [RAN3_P3_CQ3-2](#ran3_p3_cq3-2) | Substantive variant | sectionId (string), sectionNumber (string), title (string) | 55 | 13/13 |
| [RAN3_P3_CQ3-3](#ran3_p3_cq3-3) | Proposed clarification | crTdoc (string) | 2,992 | 7/7 |
| [RAN3_P3_CQ3-4](#ran3_p3_cq3-4) | Proposed clarification | crTdoc (string) | 2,339 | 7/7 |
| [RAN3_P3_CQ3-5](#ran3_p3_cq3-5) | Proposed clarification | specNumber (string) | 44 | 7/7 |
| [RAN3_P3_CQ3-6](#ran3_p3_cq3-6) | Proposed clarification | specNumber (string) | 86 | 7/7 |
| [RAN3_P3_CQ3-7](#ran3_p3_cq3-7) | Substantive variant | crTdoc (string), clause (string), sectionId (string) | 2,438 | 13/13 |
| [RAN3_P3_CQ3-8](#ran3_p3_cq3-8) | Proposed clarification | specNumber (string), crCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ4-1](#ran3_p3_cq4-1) | Substantive variant | specNumber (string) | 57 | 7/7 |
| [RAN3_P3_CQ4-2](#ran3_p3_cq4-2) | Substantive variant | resolutionId (string), crTdoc (string) | 617 | 10/10 |
| [RAN3_P3_CQ4-3](#ran3_p3_cq4-3) | Substantive variant | resolutionId (string), crTdoc (string), clause (string), sectionId (string) | 1,156 | 16/16 |
| [RAN3_P3_CQ4-4](#ran3_p3_cq4-4) | Substantive variant | specNumber (string), crCount (integer), resolutionCount (integer) | 5 | 13/13 |
| [RAN3_P3_CQ5-1](#ran3_p3_cq5-1) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN3_P3_CQ5-2](#ran3_p3_cq5-2) | Proposed clarification | specNumber (string), crCount (integer) | 5 | 10/10 |
| [RAN3_P3_CQ5-3](#ran3_p3_cq5-3) | Substantive variant | editionId (string), specNumber (string), release (string), crCount (integer), sectionCount (integer), density (number) | 115 | 22/22 |
| [RAN3_P3_CQ5-4](#ran3_p3_cq5-4) | Proposed clarification | specNumber (string), tableCount (integer) | 23 | 10/10 |
| [RAN3_P3_CQ5-5](#ran3_p3_cq5-5) | Proposed clarification | specNumber (string), figureCount (integer) | 23 | 10/10 |
| [RAN3_P3_P3-S8-CQ02](#ran3_p3_p3-s8-cq02) | Proposed clarification | itemCount (integer), unlinkedCount (integer), allLinked (boolean) | 1 | 13/13 |
| [RAN3_P3_P3-S8-CQ05](#ran3_p3_p3-s8-cq05) | Proposed clarification | class (string), granularity (string), nodeCount (integer) | 2 | 13/13 |
| [RAN3_P4_CQ2-1](#ran3_p4_cq2-1) | Proposed clarification | specNumber (string) | 1 | 7/7 |
| [RAN3_P4_CQ2-2](#ran3_p4_cq2-2) | Proposed clarification | crTdoc (string) | 136 | 7/7 |
| [RAN3_P4_CQ2-3](#ran3_p4_cq2-3) | Proposed clarification | crTdoc (string) | 353 | 7/7 |
| [RAN3_P4_CQ2-4](#ran3_p4_cq2-4) | Proposed clarification | crTdoc (string), affectedSpecCount (integer) | 10 | 10/10 |
| [RAN3_P4_CQ3-1](#ran3_p4_cq3-1) | Proposed clarification | crTdoc (string), summary (string) | 37 | 10/10 |
| [RAN3_P4_CQ3-2](#ran3_p4_cq3-2) | Proposed clarification | crPackId (string) | 59 | 7/7 |
| [RAN3_P4_CQ3-3](#ran3_p4_cq3-3) | Proposed clarification | crPackId (string) | 18 | 7/7 |
| [RAN3_P4_CQ4-1](#ran3_p4_cq4-1) | Proposed clarification | crTdoc (string), reason (string) | 308 | 10/10 |
| [RAN3_P4_CQ4-2](#ran3_p4_cq4-2) | Substantive variant | crTdoc (string), reason (string), summary (string) | 2,685 | 13/13 |
| [RAN3_P4_CQ4-3](#ran3_p4_cq4-3) | Proposed clarification | sectionId (string) | 828 | 7/7 |
| [RAN3_P4_CQ4-4](#ran3_p4_cq4-4) | Proposed clarification | specNumber (string) | 30 | 7/7 |
| [RAN3_P4_CQ4-5](#ran3_p4_cq4-5) | Substantive variant | crTdoc (string), summary (string) | 415 | 10/10 |
| [RAN3_P5_TR-CQ-1-1](#ran3_p5_tr-cq-1-1) | Proposed clarification | trNumber (string) | 1 | 7/7 |
| [RAN3_P5_TR-CQ-1-4](#ran3_p5_tr-cq-1-4) | Proposed clarification | status (string), trCount (integer) | 2 | 10/10 |
| [RAN3_P5_TR-CQ-2-1](#ran3_p5_tr-cq-2-1) | Proposed clarification | specNumber (string) | 1 | 7/7 |
| [RAN3_P5_TR-CQ-2-2](#ran3_p5_tr-cq-2-2) | Proposed clarification | impactType (string) | 1 | 7/7 |
| [RAN3_P5_TR-CQ-2-3](#ran3_p5_tr-cq-2-3) | Proposed clarification | trNumber (string) | 1 | 7/7 |
| [RAN3_P5_TR-CQ-2-4](#ran3_p5_tr-cq-2-4) | Proposed clarification | trNumber (string) | 8 | 7/7 |
| [RAN3_P5_TR-CQ-2-5](#ran3_p5_tr-cq-2-5) | Proposed clarification | trNumber (string) | 6 | 7/7 |
| [RAN3_P5_TR-CQ-3-1](#ran3_p5_tr-cq-3-1) | Proposed clarification | specNumber (string), impactType (string), description (string) | 1 | 13/13 |
| [RAN3_P5_TR-CQ-3-2](#ran3_p5_tr-cq-3-2) | Proposed clarification | specNumber (string), impactType (string), description (string) | 2 | 13/13 |
| [RAN3_P5_TR-CQ-3-3](#ran3_p5_tr-cq-3-3) | Proposed clarification | impactType (string), description (string) | 1 | 10/10 |
| [RAN3_P5_TR-CQ-4-1](#ran3_p5_tr-cq-4-1) | Proposed clarification | trNumber (string), specNumber (string), impactType (string) | 2 | 13/13 |
| [RAN3_P5_TR-CQ-4-2](#ran3_p5_tr-cq-4-2) | Proposed clarification | status (string), scope (string) | 1 | 10/10 |
| [RAN3_P5_TR-CQ-4-3](#ran3_p5_tr-cq-4-3) | Proposed clarification | conclusions (string), specNumber (string), impactType (string) | 1 | 13/13 |
| [RAN3_P5_TR-CQ-5-3](#ran3_p5_tr-cq-5-3) | Proposed clarification | trNumber (string), impactCount (integer) | 5 | 10/10 |

## RAN3_P1_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs at meeting RAN3#130 linked to Work Item NR_newRAT-Core (interface work-item preparation).

**Revised question:** List all distinct TDoc identifiers presented at canonical meeting RAN3#130 and linked by RELATED_TO to NR_newRAT-Core. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original list is capped at ten and uses numeric meeting scope; remove cap, select exact canonical meeting, grade requested identifiers only.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-1/7e57bdb5f750d9a6a343b4f4351c2e0a0125e291a32a85b92c93265e79d09eee.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-1/7e57bdb5f750d9a6a343b4f4351c2e0a0125e291a32a85b92c93265e79d09eee.jsonl); 66 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ad099d9931956690962ce2afd4c3dbb70c8491d218ea71d0bf84e34d2a3a0697`.

## RAN3_P1_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs under agenda item 8.1 at meeting RAN3#130 (agenda-item document review).

**Revised question:** List all distinct TDoc identifiers presented at RAN3#130 and linked by BELONGS_TO to agenda number 8.1. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Preserve agenda and meeting filters, make full list explicit and remove unstated cap; title/status are unrequested.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-2/352156a4ce10e937fc4b222c180925cc9e657072c68ab460697587595ffa9771.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-2/352156a4ce10e937fc4b222c180925cc9e657072c68ab460697587595ffa9771.jsonl); 30 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `bca0f86f65956fe0d782675926be5699094d90e1f4307d0422bd509f525649cd`.

## RAN3_P1_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs Huawei submitted at meeting RAN3#130 (tracking a company's contributions).

**Revised question:** List all distinct TDoc identifiers presented at RAN3#130 and submitted by the Company named Huawei. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unstated cap and scope exact canonical meeting; no hidden title/type requirement.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-3/db50b2a600818d0cbd281e512a04900f5de792bb3960789df70270d296a62fba.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-3/db50b2a600818d0cbd281e512a04900f5de792bb3960789df70270d296a62fba.jsonl); 327 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ac8f90a050fea7f34d11cabd40a37b870a99cf9468147b9e4b041bbe17fc9d9f`.

## RAN3_P1_CQ1-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs discussed under Rel-19 (release-scoped document survey).

**Revised question:** List all distinct TDoc identifiers with a recorded TARGET_RELEASE edge to Rel-19. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** TARGET_RELEASE establishes target metadata, not that discussion occurred; explicitly redefine as release-target inventory and remove cap.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-4/dfde82271f58e88768d32e3b3b6370058f2a28121685cd285a8334a6e2a5eeae.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-4/dfde82271f58e88768d32e3b3b6370058f2a28121685cd285a8334a6e2a5eeae.jsonl); 5,948 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `95c5de08494aae7fc1a7bd592eed22880958d291a7e5361457717c11c57097a4`.

## RAN3_P1_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs agreed at meeting RAN3#130 (approved-outcome review).

**Revised question:** List all distinct TDoc identifiers presented at RAN3#130 whose recorded status equals agreed. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unstated ten cap, exact canonical meeting, recorded-status interpretation.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE t.status = 'agreed' RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) WHERE t.status = 'agreed' RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-5/cc76952d37daf80570d46691145e306cd45f3209ef5268ba6c5dd8e473df3f78.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-5/cc76952d37daf80570d46691145e306cd45f3209ef5268ba6c5dd8e473df3f78.jsonl); 137 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `392d7263071c356cd00180dfedb35a6b3d153d330d1314c73ac06b46dabf2993`.

## RAN3_P1_CQ1-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the decision status of TDoc R3-258530 (checking the outcome).

**Revised question:** Return the recorded status of TDoc R3-258530. Return named records with status. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Grade requested status, not current first TDoc identifier or extra type; status property is not independent decision history.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.status, t.type
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN DISTINCT t.status AS status
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "status",
      "nullable": false,
      "source_column_or_expression": "status",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-6/fb8a91389404f0cb839d5c22ed9a3240e4d394ca43cd0cdda2dc468fac96465d.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-6/fb8a91389404f0cb839d5c22ed9a3240e4d394ca43cd0cdda2dc468fac96465d.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0411d328252f2db8d949e4a67f3b3c4248543f62cbd93cb05e39ef3ccdcae7e8`.

## RAN3_P1_CQ1-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the 'For' purpose of TDoc R3-258530 (identifying document intent).

**Revised question:** Return the recorded For purpose value of TDoc R3-258530. Return named records with purpose. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Purpose is requested; TDoc ID is input context rather than graded answer.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.for
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN DISTINCT t.for AS purpose
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "purpose",
      "nullable": false,
      "source_column_or_expression": "purpose",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-7/c0260967fd48bd8787251397c371678116ae8f65f1c02ab8d9c0945d95db2d64.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-7/c0260967fd48bd8787251397c371678116ae8f65f1c02ab8d9c0945d95db2d64.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8646bd7da2a733b854a2efcb05ca98e736a5df28a803cebc825c4e07668ab8f5`.

## RAN3_P1_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the contact person for TDoc R3-258530 (finding the responsible author).

**Revised question:** List the distinct recorded contact names and contact identifiers linked by HAS_CONTACT from TDoc R3-258530. Return named records with contactName, contactId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Names/IDs disambiguate multiple possible contacts; linked contact is not proof of sole responsible author.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:HAS_CONTACT]->(c:Contact) RETURN DISTINCT c.contactName AS contactName, c.contactId AS contactId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "contactName",
      "nullable": false,
      "source_column_or_expression": "contactName",
      "type": "string"
    },
    {
      "name": "contactId",
      "nullable": false,
      "source_column_or_expression": "contactId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-8/afd5eeb0f960097d64ec7b4f50cbb51bc4e08bf40933b1c8647682304cc17ea0.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-8/afd5eeb0f960097d64ec7b4f50cbb51bc4e08bf40933b1c8647682304cc17ea0.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `51bdcf18a86f3ed8bdafab17d622d98c27e6b57370213822cbe0fe1b9b71bade`.

## RAN3_P1_CQ1-9

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all agenda items covered at meeting RAN3#130 (meeting-scope overview).

**Revised question:** List all distinct agenda-number and description pairs linked to TDocs presented at RAN3#130. Return named records with agendaNumber, description. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** TDoc-mediated population cannot certify every meeting agenda item; explicitly retain that graph-observable population and remove cap.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:BELONGS_TO]->(a:AgendaItem) RETURN DISTINCT a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:BELONGS_TO]->(a:AgendaItem) RETURN DISTINCT a.agendaNumber AS agendaNumber, a.agendaDescription AS description
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agendaNumber",
      "nullable": false,
      "source_column_or_expression": "agendaNumber",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": false,
      "source_column_or_expression": "description",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ1-9/4515cd857b2607e8a5e8d0f381815b0353595d8b5ac1859a3e5ee55ce908cb21.json), [complete native rows](../reference_outputs/RAN3_P1_CQ1-9/4515cd857b2607e8a5e8d0f381815b0353595d8b5ac1859a3e5ee55ce908cb21.jsonl); 42 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6641ceaf4baa590049781bcae26e8c24a656f983ecde6dc1b028b52c37f247c4`.

## RAN3_P1_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the predecessor revision of TDoc R3-241531 (revision-lineage tracing).

**Revised question:** List the identifiers of immediate predecessor TDocs linked by IS_REVISION_OF from R3-241531. Return named records with predecessorTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Immediate recorded predecessor is directly queryable; original source ID and title are unrequested.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241531'})-[:IS_REVISION_OF]->(prev:Tdoc) RETURN t.tdocNumber, prev.tdocNumber, prev.title
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241531'})-[:IS_REVISION_OF]->(prev:Tdoc) RETURN DISTINCT prev.tdocNumber AS predecessorTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "predecessorTdoc",
      "nullable": false,
      "source_column_or_expression": "predecessorTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-1/2bb0cce6e75ced6149e7c4ea4f1d658beed62a29c70ec2153860a2587bb12e14.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-1/2bb0cce6e75ced6149e7c4ea4f1d658beed62a29c70ec2153860a2587bb12e14.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7941da36d456771769eda9b4596e71ad5f3169407e6035004452b47378dcd8d3`.

## RAN3_P1_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the LS that TDoc R3-241518 replies to (liaison reply linkage).

**Revised question:** List all distinct LS TDoc identifiers reached by REPLY_TO from TDoc R3-241518. Return named records with replyTargetTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Preserve requested LS target type using both Tdoc and LS labels, rather than accepting arbitrary reply-target TDocs; explicit native identifier role.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241518'})-[:REPLY_TO]->(orig:Tdoc) RETURN t.tdocNumber, orig.tdocNumber, orig.title
```

**Revised query**

```cypher
MATCH (:Tdoc {tdocNumber:'R3-241518'})-[:REPLY_TO]->(orig:Tdoc:LS) RETURN DISTINCT orig.tdocNumber AS replyTargetTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "replyTargetTdoc",
      "nullable": false,
      "source_column_or_expression": "replyTargetTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-3/c1b47e1e16e07115dc5a824bea899b9ba938fc692638eff8872825fe94442fdc.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-3/c1b47e1e16e07115dc5a824bea899b9ba938fc692638eff8872825fe94442fdc.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `20c422c5eec1ce385417d2f9ef71d450519bc38708a550e32d569810ba975a44`.

## RAN3_P1_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the specs that CR R3-258530 modifies (change-impact scope).

**Revised question:** List all distinct specification numbers linked by MODIFIES from CR R3-258530. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Grade target spec numbers, not source CR ID; distinct spec-number population explicitly specified.

**Original query**

```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'})-[:MODIFIES]->(s:Spec) RETURN c.tdocNumber, s.specNumber
```

**Revised query**

```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'})-[:MODIFIES]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-4/af0392084ccb9f200d9f9572a24858fac3e0704b67b57f898bbd18d575081852.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-4/af0392084ccb9f200d9f9572a24858fac3e0704b67b57f898bbd18d575081852.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d4b1f3f3f0e010dacfc6c342f2ea4e8b7945b3a899466e090bf5565ae1b372f5`.

## RAN3_P1_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the category and affected clauses of CR R3-258530 (impact assessment).

**Revised question:** Return the recorded category and affected-clauses text of CR R3-258530. Return named records with category, clausesAffected. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Both requested attributes required as paired record; clausesAffected is source string, not independently parsed clause list.

**Original query**

```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'}) RETURN c.tdocNumber, c.crCategory, c.crNumber, c.clausesAffected
```

**Revised query**

```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'}) RETURN DISTINCT c.crCategory AS category, c.clausesAffected AS clausesAffected
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "category",
      "nullable": false,
      "source_column_or_expression": "category",
      "type": "string"
    },
    {
      "name": "clausesAffected",
      "nullable": false,
      "source_column_or_expression": "clausesAffected",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-5/1e5daf6ee67fad5f3a96d7db2f3ce3dd3b3d0268664865bf1d5f225bdcf6c826.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-5/1e5daf6ee67fad5f3a96d7db2f3ce3dd3b3d0268664865bf1d5f225bdcf6c826.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e62ce51ececcd8f825cc2c527d42ba322fd69099430a4c4302753012d29a6fe8`.

## RAN3_P1_CQ2-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs postponed at meeting RAN3#121bis (deferred-item tracking).

**Revised question:** List all distinct TDoc identifiers presented at canonical meeting RAN3#121bis whose recorded status is postponed. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Numeric meeting121 conflates base/bis. Use exact original requested bis meeting and remove cap; candidate needs source execution.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 121}) WHERE t.status = 'postponed' RETURN t.tdocNumber, t.title LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN3#121bis'}) WHERE t.status='postponed' RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-6/dd640384307fb29f0b81cd6c26a659c872600955228bccf1bc259aa906644c39.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-6/dd640384307fb29f0b81cd6c26a659c872600955228bccf1bc259aa906644c39.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e7410b72023c58919165cc1f572885451087c0bb0f17fc16a59659d7a8d18cbe`.

## RAN3_P1_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the incoming liaison statements at meeting RAN3#130 (incoming-LS triage).

**Revised question:** List all distinct incoming LS identifiers presented at canonical meeting RAN3#130, where direction equals in. Return named records with lsTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove cap, canonical meeting scope, incoming direction retained; title is not requested.

**Original query**

```cypher
MATCH (l:LS)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE l.direction = 'in' RETURN l.tdocNumber, l.title ORDER BY l.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (l:LS)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) WHERE l.direction = 'in' RETURN DISTINCT l.tdocNumber AS lsTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "lsTdoc",
      "nullable": false,
      "source_column_or_expression": "lsTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ2-7/b68acb92eefbfba012dafbb79e0f4753ffa6e5d0a809e1d8c1355b61958b2fb8.json), [complete native rows](../reference_outputs/RAN3_P1_CQ2-7/b68acb92eefbfba012dafbb79e0f4753ffa6e5d0a809e1d8c1355b61958b2fb8.jsonl); 20 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b60e19e644995b3d9011366c05e64db8b26b445438a634ee2b9996f42c3b84a8`.

## RAN3_P1_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Huawei's contributions to Work Item NR_newRAT-Core (competitor contribution review).

**Revised question:** List all distinct TDoc identifiers submitted by Huawei and linked to Work Item NR_newRAT-Core. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove ten cap; original company/workitem predicates retained.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-1/00bd959e8a589299e8dcad71460ad602d1e65c654a7a01652f147810950860f8.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-1/00bd959e8a589299e8dcad71460ad602d1e65c654a7a01652f147810950860f8.jsonl); 2,010 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `af6212ccd8e701d2d99b3690ecde4706692d23ac895280191bd4f0e7c7619bf7`.

## RAN3_P1_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Break down contributions by company under agenda item 8.1 at meeting RAN3#130 (competitive landscape).

**Revised question:** For each recorded submitting company under agenda 8.1 at RAN3#130, return its name and number of distinct matching TDocs. Return named records with companyName, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Company/count pairing required; count distinct documents rather than join rows; remove cap and exact meeting.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-2/ac6c91f4bb8e555dc521dd6062f89978cf2f57f4405b0cc767819246c9325e69.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-2/ac6c91f4bb8e555dc521dd6062f89978cf2f57f4405b0cc767819246c9325e69.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b71f6c5e387c91e06ddf26d7b9e2d09e8cf718b129d475a4dbed60a61e90394b`.

## RAN3_P1_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Count contributions per company on Work Item NR_newRAT-Core (participation ranking).

**Revised question:** For each recorded submitting company linked to NR_newRAT-Core, return its name and number of distinct matching TDocs. Return named records with companyName, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Correct requested company/count mapping, remove top10 not specified by question, distinct TDoc unit.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-3/daa3f2aed120a3d60d0d0e7450609cd7d78309906a5bd15aa7caa28c001151d6.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-3/daa3f2aed120a3d60d0d0e7450609cd7d78309906a5bd15aa7caa28c001151d6.jsonl); 85 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8d81f4b3b2d8b8ca803c91f57168a97a883d7273c42c06ada08ac7cf90d2972c`.

## RAN3_P1_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the share of Samsung's TDocs that were agreed (success-rate metric).

**Revised question:** Return the fraction of Samsung's distinct recorded TDocs with status agreed, using all of Samsung's distinct TDocs as denominator; return null if denominator is zero. Return named records with agreedFraction. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Grade requested share rather than total; use consistent distinct-document numerator/denominator and explicit zero denominator.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) WITH count(t) AS total MATCH (t2:Tdoc)-[:SUBMITTED_BY]->(c2:Company {companyName: 'Samsung'}) WHERE t2.status = 'agreed' RETURN total, count(t2) AS agreed, toFloat(count(t2)) / total AS ratio
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) WITH collect(DISTINCT t) AS docs WITH docs, [d IN docs WHERE d.status='agreed'] AS approved RETURN CASE WHEN size(docs)=0 THEN null ELSE toFloat(size(approved))/size(docs) END AS agreedFraction
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agreedFraction",
      "nullable": true,
      "source_column_or_expression": "agreedFraction",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-4/ed3ef92b545f2d4faac539d2cb6b2de8152f16e95ce97e174f429a6e80ef8fdd.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-4/ed3ef92b545f2d4faac539d2cb6b2de8152f16e95ce97e174f429a6e80ef8fdd.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d142d5541b077b9f00713be47aa86f12f49037aae1f5c82669f994e16bc8f7d5`.

## RAN3_P1_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List other companies' contributions in the same agenda and meeting as R3-258530 (peer-contribution comparison).

**Revised question:** List distinct submitting-company and TDoc-identifier pairs sharing a recorded agenda and meeting with R3-258530, excluding companies that submitted R3-258530. Return named records with companyName, tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original excludes only reference TDoc and does not implement other companies; exclude actual source submitters and remove cap.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:BELONGS_TO]->(a:AgendaItem), (t)-[:PRESENTED_AT]->(m:Meeting) MATCH (other:Tdoc)-[:BELONGS_TO]->(a), (other)-[:PRESENTED_AT]->(m), (other)-[:SUBMITTED_BY]->(c:Company) WHERE other.tdocNumber <> 'R3-258530' RETURN c.companyName, other.tdocNumber, other.title ORDER BY c.companyName LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber:'R3-258530'})-[:BELONGS_TO]->(a:AgendaItem), (t)-[:PRESENTED_AT]->(m:Meeting), (t)-[:SUBMITTED_BY]->(origin:Company) WITH t,a,m,collect(DISTINCT origin) AS origins MATCH (other:Tdoc)-[:BELONGS_TO]->(a), (other)-[:PRESENTED_AT]->(m), (other)-[:SUBMITTED_BY]->(c:Company) WHERE NOT c IN origins RETURN DISTINCT c.companyName AS companyName,other.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
      "source_column_or_expression": "companyName",
      "type": "string"
    },
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-5/1050e39d0e31e327050795c0e576aa006edd825ec7051215f4e45a46c54caa84.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-5/1050e39d0e31e327050795c0e576aa006edd825ec7051215f4e45a46c54caa84.jsonl); 354 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `86b03e017c7e20587911e88d79c6a17553979cb3806394532e82f3c5d226c268`.

## RAN3_P1_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show Huawei's contribution distribution across Work Items (identifying focus areas).

**Revised question:** For each Work Item with Huawei-submitted TDocs, return Work Item code and number of distinct Huawei TDocs linked to it. Return named records with workItemCode, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Distribution requires code/count pairs; remove truncated ranking and explicitly count distinct documents.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem) RETURN w.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem) RETURN DISTINCT w.workItemCode AS workItemCode, count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workItemCode",
      "nullable": false,
      "source_column_or_expression": "workItemCode",
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ3-6/b179335eccda66c41bbb62852ad2ce72f0e74e9a4886e3fe7034d52aad026b04.json), [complete native rows](../reference_outputs/RAN3_P1_CQ3-6/b179335eccda66c41bbb62852ad2ce72f0e74e9a4886e3fe7034d52aad026b04.jsonl); 282 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `33c1a297b193ece74a894d7edd4ce53943c760edfa4ee5adc84ea6fd8dd620c1`.

## RAN3_P1_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original question supplies neither a reference date nor a past-meeting cutoff. The revised explicit integer cutoff defines a separate executable variant and does not resolve the intended original reference time.

**Original question:** List Samsung's past-meeting contributions to Work Item NR_newRAT-Core (historical contribution review).

**Revised question:** List all distinct canonical-meeting and TDoc-identifier pairs for Samsung submissions related to Work Item NR_newRAT-Core, considering only meetings whose recorded integer meeting number is strictly less than the explicitly supplied cutoff 130. Exclude meetings without an integer meeting number. Return named records with canonicalMeetingNumber, tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original past-meeting reference time is absent. Supply cutoff130 as an explicit new benchmark input and label the narrower task substantive_variant, preserve canonical meeting/TDoc roles, exclude missing numeric sequence values, and remove unstated ten-result cap. No current-date or true chronological claim.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}), (t)-[:RELATED_TO]->(:WorkItem {workItemCode:'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) WHERE m.meetingNumberInt IS NOT NULL AND m.meetingNumberInt < 130 RETURN DISTINCT m.canonicalMeetingNumber AS canonicalMeetingNumber,t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "canonicalMeetingNumber",
      "nullable": false,
      "source_column_or_expression": "canonicalMeetingNumber",
      "type": "string"
    },
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ4-1/433fc23725ce7754006a02a58131f70f840993752c90a9e059009e472fb812a1.json), [complete native rows](../reference_outputs/RAN3_P1_CQ4-1/433fc23725ce7754006a02a58131f70f840993752c90a9e059009e472fb812a1.jsonl); 493 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `adbfe6d5742654c9bd6a2503b60d41f00b3054e11b1dddbc312147b396cccf3c`.

## RAN3_P1_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Summarize the outcomes of Samsung's contributions at meeting RAN3#130 (result rollup by status).

**Revised question:** For each recorded status among Samsung's TDocs presented at RAN3#130, return status and number of distinct matching TDocs. Return named records with status, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Outcome rollup requires paired status/count rather than status-only scoring; exact meeting and distinct unit.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.status, count(t) AS cnt ORDER BY cnt DESC
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) RETURN DISTINCT t.status AS status, count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "status",
      "nullable": false,
      "source_column_or_expression": "status",
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ4-2/c11fa6ce80a924d9a3276cf65fec4fa76a770236b6eb778f857ab46ff82ee54d.json), [complete native rows](../reference_outputs/RAN3_P1_CQ4-2/c11fa6ce80a924d9a3276cf65fec4fa76a770236b6eb778f857ab46ff82ee54d.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `02048aac2234d8dc79934454f75db41bce066ac3bf4757c4443a7a0c94396ef5`.

## RAN3_P1_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the not-treated TDocs under agenda item 13.2 at meeting RAN3#122 (pending-item tracking).

**Revised question:** List all distinct TDoc identifiers linked to agenda number 13.2 at RAN3#122 with recorded status not treated. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unstated cap and select canonical meeting; identifiers are requested.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '13.2'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 122}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '13.2'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#122'}) WHERE t.status = 'not treated' RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P1_CQ4-3/9c4ab5e96df4a16207c0069d1e177714ede269166d99cb0833dbeaf49a22964b.json), [complete native rows](../reference_outputs/RAN3_P1_CQ4-3/9c4ab5e96df4a16207c0069d1e177714ede269166d99cb0833dbeaf49a22964b.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `5ab993f5bb013d3d09e339c754c9c4f8a29eeb5b792dab5c327c19b3f3cfccd4`.

## RAN3_P2_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the agreements reached at meeting RAN3#121 (consensus-outcome review).

**Revised question:** List all distinct agreement identifiers and agreement-content strings recorded by MADE_AT at RAN3#121. Return named records with agreementId, content. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Agreements are identifiable content records; optional agenda is context only. Remove cap and keep exact canonical meeting.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#121'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#121'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId AS agreementId, a.content AS content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agreementId",
      "nullable": false,
      "source_column_or_expression": "agreementId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": false,
      "source_column_or_expression": "content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-1/d36f1fef513394cc973926562900231103d59dccbd6a0c08cfc4a19c01465f46.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-1/d36f1fef513394cc973926562900231103d59dccbd6a0c08cfc4a19c01465f46.jsonl); 84 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a4e9f572f253571f9d35c5697faf5f1861ab7210518055faa696429cde6fdb45`.

## RAN3_P2_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions drawn at meeting RAN3#94 (meeting-outcome review).

**Revised question:** List all distinct conclusion identifiers and content strings recorded at RAN3#94. Return named records with conclusionId, content. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove cap; optional agenda and consensus are unrequested context, conclusion content retained.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#94'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#94'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "conclusionId",
      "nullable": false,
      "source_column_or_expression": "conclusionId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": false,
      "source_column_or_expression": "content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-2/fe0582a5c111a1462190de7913161f779ae94c04179d824f5df2e45256e4322d.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-2/fe0582a5c111a1462190de7913161f779ae94c04179d824f5df2e45256e4322d.jsonl); 214 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `fdbf4ee2d0be75390d4460fa852ddce89efc8423da3312e59e4298e36d7ba79d`.

## RAN3_P2_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the working assumptions from meeting RAN3#112 (provisional-decision tracking).

**Revised question:** List all distinct working-assumption identifiers and content strings recorded at RAN3#112. Return named records with workingAssumptionId, content. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove cap and keep requested outcome content; optional agenda need not be required.

**Original query**

```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#112'}) OPTIONAL MATCH (w)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN w.resolutionId, w.content, ai.agendaNumber ORDER BY ai.agendaNumber, w.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#112'}) OPTIONAL MATCH (w)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT w.resolutionId AS workingAssumptionId, w.content AS content
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workingAssumptionId",
      "nullable": false,
      "source_column_or_expression": "workingAssumptionId",
      "type": "string"
    },
    {
      "name": "content",
      "nullable": false,
      "source_column_or_expression": "content",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-3/3084bcf94b739a3acf90d2fd95c630bd4eee16e15359aa0686dc4b3bebe19948.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-3/3084bcf94b739a3acf90d2fd95c630bd4eee16e15359aa0686dc4b3bebe19948.jsonl); 17 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `094af7deaf08c38b7e969627da282bd8972212902705e043ecf3c3c1696f9a24`.

## RAN3_P2_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions under agenda item 8.1 (agenda-item decision history).

**Revised question:** List all distinct resolution identifiers linked to agenda number8.1 and their recorded meeting identifiers. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove cap, specify agenda-number aggregation across recorded meetings; label list is not requested.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-4/30e2c410a31da04dfe914d34d803492d37446135c1a62420972f846617de0563.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-4/30e2c410a31da04dfe914d34d803492d37446135c1a62420972f846617de0563.jsonl); 55 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4620e370c6ed967803b3e4f8fccc2e5b8028a119a3524ae4aa98fac2529b016f`.

## RAN3_P2_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions tied to Rel-18 TDocs (release-scoped decision review).

**Revised question:** List all distinct resolution identifiers and meeting identifiers where resolutions reference TDocs targeting Rel-18. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Direct references and recorded target release retained; remove cap and duplicate paths.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.resolutionId, t.tdocNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-5/a0060a691df01ee7fcda8d379754fbced4d761cf6805a1be41ab9a41002a4fdb.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-5/a0060a691df01ee7fcda8d379754fbced4d761cf6805a1be41ab9a41002a4fdb.jsonl); 132 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4d30833e1b13287243bf09b333f588eb3b76cba9b4828de7f0a87c70d0b79a98`.

## RAN3_P2_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions that modify spec 38.423 (decision-to-spec tracing).

**Revised question:** List all distinct resolution identifiers and meetings where a resolution references a TDoc with MODIFIES link to spec38.423. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Resolution has no direct modifies edge in query; explicitly state indirect documentary path, not resolution causation; remove cap.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber, m.meetingNumberInt AS mNum ORDER BY mNum DESC, r.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-6/171d14216422888b706e58ea69b4c351f8302ab87cf07bb82bc4b2832125c5c0.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-6/171d14216422888b706e58ea69b4c351f8302ab87cf07bb82bc4b2832125c5c0.jsonl); 104 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e1863b9d898c92cf56f645ff3e550df623af7258c80f98e15079bdc3dd3202f6`.

## RAN3_P2_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 agenda items by resolution count (busiest agenda areas).

**Revised question:** Return top10 agenda-number groups by count of distinct Resolution nodes linked to that agenda number; break ties by ascending agenda number and return all groups if fewer than10 exist. Return named records with agendaNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Define grouping identity and distinct Resolution counting, paired fields, deterministic top10 policy.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS cnt ORDER BY cnt DESC, ai.agendaNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT ai.agendaNumber AS agendaNumber, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC, agendaNumber ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agendaNumber",
      "nullable": false,
      "source_column_or_expression": "agendaNumber",
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
        "field": "agendaNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ1-8/1a56a6d101029765d1ba52d9791665609bcc1083166a9a92120ee7423a9e94a4.json), [complete native rows](../reference_outputs/RAN3_P2_CQ1-8/1a56a6d101029765d1ba52d9791665609bcc1083166a9a92120ee7423a9e94a4.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4e70354425e2b0baefa8a0b5c24a23fcfb247c84dd35c661126324c15684fd7a`.

## RAN3_P2_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the TDocs referenced by three or more resolutions (high-impact contributions).

**Revised question:** List all distinct TDoc identifiers referenced by at least three distinct Resolution nodes. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Threshold must count resolutions rather than duplicated edges; remove cap and avoid unrequested reference-count field.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(r) AS refCnt WHERE refCnt >= 3 RETURN t.tdocNumber, refCnt ORDER BY refCnt DESC, t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(DISTINCT r) AS refCnt WHERE refCnt >= 3 RETURN DISTINCT t.tdocNumber AS tdocNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "tdocNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.json), [complete native rows](../reference_outputs/RAN3_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.jsonl); 41 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b676f379d02eeb05a4aad67cefee9f726f1c29da489daf645963c2c700dcd448`.

## RAN3_P2_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List resolutions that reference five or more TDocs (multi-document decisions).

**Revised question:** List all distinct Resolution identifiers that reference at least five distinct TDoc nodes. Return named records with resolutionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Count distinct referenced TDoc nodes for the requested five-or-more threshold. Remove unrequested meeting-membership restriction, sampling of references and ten-row cap.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r, collect(t.tdocNumber) AS refs, count(t) AS cnt WHERE cnt >= 5 MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, refs[..5] AS top5_refs, cnt ORDER BY m.meetingNumberInt DESC, cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r,count(DISTINCT t) AS referencedTdocCount WHERE referencedTdocCount>=5 RETURN DISTINCT r.resolutionId AS resolutionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.json), [complete native rows](../reference_outputs/RAN3_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.jsonl); 358 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d53eef93f35b4050e38b4d7312e178d0ddea0d3c0c9060a09af4e9f776afe160`.

## RAN3_P2_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find resolutions whose text cites R3- TDoc numbers (in-text reference check).

**Revised question:** List all distinct Resolution identifiers whose recorded content contains a token shaped as R3- followed by one or more digits, bounded on each side by the string boundary or a character other than a letter, digit, underscore or hyphen. Return named records with resolutionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Define exact token boundaries to exclude embedded XR3-123 and R3-123abc fragments. The textual token does not independently prove a graph REFERENCE edge or known real-world document; remove unrequested cap.

**Original query**

```cypher
MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '.*R3-.*' RETURN r.resolutionId, r.content ORDER BY r.resolutionId LIMIT 5
```

**Revised query**

```cypher
MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '(?s).*(?<![A-Za-z0-9_-])R3-[0-9]+(?![A-Za-z0-9_-]).*' RETURN DISTINCT r.resolutionId AS resolutionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ2-3/3143e2b9d7755d4cd55f274f5b14ac9f252a6939b1a9b52a2cd2285dabea377c.json), [complete native rows](../reference_outputs/RAN3_P2_CQ2-3/3143e2b9d7755d4cd55f274f5b14ac9f252a6939b1a9b52a2cd2285dabea377c.jsonl); 941 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9a1d7f89046973086721ed24007a8e97ebe2461870ab057d470c700d60c29c81`.

## RAN3_P2_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Count resolution-referenced TDocs per spec they modify (spec-change tracing).

**Revised question:** For each specification number reached through MODIFIES from a Resolution-referenced TDoc, count distinct such TDoc nodes. Return named records with specNumber, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unrequested meeting-membership restriction and global ten-row cap; preserve requested distinct TDoc count for every reached specification-number group.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) RETURN s.specNumber AS specNumber,count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ2-4/26d5430a3d9cc57cf70b80295a962327161c3aedffe2e88f103017ed18784eac.json), [complete native rows](../reference_outputs/RAN3_P2_CQ2-4/26d5430a3d9cc57cf70b80295a962327161c3aedffe2e88f103017ed18784eac.jsonl); 57 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `22d64ca8c4b5403d4a8c16d2a6ecf47b2551c7d81b0ae89c231219a1ba934046`.

## RAN3_P2_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return how many of ZTE's TDocs led to resolutions (contribution effectiveness).

**Revised question:** Count distinct ZTE-submitted TDoc nodes that are referenced by at least one recorded Resolution. Return named records with referencedTdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original count(DISTINCT r) counts resolutions, not linked TDocs; correct unit. Documentary reference does not establish led-to causation.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(t) RETURN count(DISTINCT t) AS totalTdocs, count(DISTINCT r) AS resolutionLinkedTdocs
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'ZTE'}) WHERE EXISTS { MATCH (:Resolution)-[:REFERENCES]->(t) } RETURN count(DISTINCT t) AS referencedTdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "referencedTdocCount",
      "nullable": false,
      "source_column_or_expression": "referencedTdocCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ3-1/df668d4ed5849a61912644c4f44aff6c139b7f39384fc1e7effe18329d50a388.json), [complete native rows](../reference_outputs/RAN3_P2_CQ3-1/df668d4ed5849a61912644c4f44aff6c139b7f39384fc1e7effe18329d50a388.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0528da71a27b2931cf09739e2dd58a4422e783cf1c9d4ef08b138a8579d83c42`.

## RAN3_P2_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 companies by resolution contribution (influence ranking).

**Revised question:** Return top10 companies by number of distinct recorded Resolutions referencing their TDocs; break ties by company name ascending and return all companies if fewer than10 exist. Return named records with companyName, resolutionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Operationalize contribution as count of referencing resolutions rather than causal influence; original count distinct r retained and deterministic ties.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC, companyName ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
      "source_column_or_expression": "companyName",
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
        "field": "companyName"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ3-2/32b4923de3bef2ae9f5fd77ad9d9c6a24e7077015f220f2a0cfaaa43205208f3.json), [complete native rows](../reference_outputs/RAN3_P2_CQ3-2/32b4923de3bef2ae9f5fd77ad9d9c6a24e7077015f220f2a0cfaaa43205208f3.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c691a59760b345745d4796478b30c10e97e8ef701d31188ae3376034232a56de`.

## RAN3_P2_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** Original main/leading contribution importance or specification ownership is not independently established by a TDoc count. The revised task defines only an explicit stored documentary association metric.

**Original question:** Rank the main contributors to spec 38.423 (spec-ownership analysis).

**Revised question:** Rank all qualifying company-name groups by the count of distinct submitted TDoc nodes referenced by at least one Resolution and modifying specification 38.423. A company-name group qualifies when at least one such TDoc is recorded. Rank count descending then company name ascending. Return named records with companyName, tdocCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** The original main/leading contributor and ownership notion has no independently validated contribution-quality metric. Define complete positive-match company-name groups ranked by distinct documentary TDoc count as a substantive variant, remove the unrequested ten-row cap and preserve deterministic keys.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT t) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, companyName ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
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
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ3-3/d1016954760828ea28c2317b1aaa6b10c8b9289cc9d5041a9a9d2a7abb38c65e.json), [complete native rows](../reference_outputs/RAN3_P2_CQ3-3/d1016954760828ea28c2317b1aaa6b10c8b9289cc9d5041a9a9d2a7abb38c65e.jsonl); 41 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5167f7d2320bda5b8c4ca88eb698c0dbee1864f53e20c162ca596c63af6834ab`.

## RAN3_P2_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return which company moderated agenda item 8.1 (rapporteur identification).

**Revised question:** List all distinct company-name and meeting pairs linked by MODERATED_BY from Summary nodes under agenda number8.1. Return named records with companyName, meeting. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Summary MODERATED_BY does not certify rapporteur role; preserve available record association and remove unrequested top10/count.

**Original query**

```cypher
MATCH (s:Summary)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (s)-[:MODERATED_BY]->(c:Company) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN c.companyName, m.canonicalMeetingNumber, count(s) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Summary)-[:RESOLUTION_BELONGS_TO]->(:AgendaItem {agendaNumber:'8.1'}), (s)-[:MODERATED_BY]->(c:Company), (s)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT c.companyName AS companyName,m.canonicalMeetingNumber AS meeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
      "source_column_or_expression": "companyName",
      "type": "string"
    },
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ4-1/bdd63b44bb2bf8fb0f14385a9afdff306a7d74c21156b94886be56b4030c95d3.json), [complete native rows](../reference_outputs/RAN3_P2_CQ4-1/bdd63b44bb2bf8fb0f14385a9afdff306a7d74c21156b94886be56b4030c95d3.jsonl); 17 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c71a605bd0676aa63c8c2c3bfacaafd60d48cbbdab4b62f5363fe81dd1f2cce0`.

## RAN3_P2_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the agenda items ZTE moderated (moderator-role tracking).

**Revised question:** List all distinct agenda-number and meeting pairs linked to Summary nodes moderated by ZTE. Return named records with agendaNumber, meeting. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Keep recorded moderator association and meeting disambiguation; remove cap and irrelevant s.summaryId ordering.

**Original query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN ai.agendaNumber, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, ai.agendaNumber, s.summaryId LIMIT 15
```

**Revised query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT ai.agendaNumber AS agendaNumber, m.canonicalMeetingNumber AS meeting
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agendaNumber",
      "nullable": false,
      "source_column_or_expression": "agendaNumber",
      "type": "string"
    },
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ4-2/fd7f8a8ac89b190174c0d66e99ef381e08e64d88ace1d707732fe6aff4136b84.json), [complete native rows](../reference_outputs/RAN3_P2_CQ4-2/fd7f8a8ac89b190174c0d66e99ef381e08e64d88ace1d707732fe6aff4136b84.jsonl); 46 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cd9b4f0c3f7a7552eb980f48576e41bfd6971f79d4ef734c232adb1287df1596`.

## RAN3_P2_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 companies by moderator assignments (leadership distribution).

**Revised question:** Return top10 company names and counts of distinct Summary nodes linked by MODERATED_BY; break ties by company name ascending and return all if fewer than10 exist. Return named records with companyName, summaryCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Distinct Summary-node count is explicit assignment proxy, not unverified leadership; deterministic top10.

**Original query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company) RETURN c.companyName, count(s) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT s) AS summaryCount ORDER BY summaryCount DESC, companyName ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "companyName",
      "nullable": false,
      "source_column_or_expression": "companyName",
      "type": "string"
    },
    {
      "name": "summaryCount",
      "nullable": false,
      "source_column_or_expression": "summaryCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "summaryCount"
      },
      {
        "direction": "asc",
        "field": "companyName"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ4-3/f441ee9beab9bf5c46b145b09269cd955ffa2209420eaf5ccd0b5704c2068b76.json), [complete native rows](../reference_outputs/RAN3_P2_CQ4-3/f441ee9beab9bf5c46b145b09269cd955ffa2209420eaf5ccd0b5704c2068b76.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `68cc4679b7f801f7cc7e45fd7d2de1d17dfcad872040e576483648ab5d923046`.

## RAN3_P2_CQ6-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the resolution-count trend for agenda item 8.1 over time (topic-activity trend).

**Revised question:** For each recorded meeting having resolutions under agenda number8.1, return meeting identifier, integer meeting number, and count of distinct matching Resolution nodes; order by integer meeting number then canonical meeting identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Trend requires meeting/count pairs, explicitly numeric recorded order with bis disambiguation; no invented zero-meeting observations.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(r) AS cnt ORDER BY mNum ASC
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '8.1'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    },
    {
      "name": "meetingNumber",
      "nullable": false,
      "source_column_or_expression": "meetingNumber",
      "type": "integer"
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
        "direction": "asc",
        "field": "meetingNumber"
      },
      {
        "direction": "asc",
        "field": "meeting"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ6-1/9e810be0e13d623143655064a9ee6db09f4dee690ace3c80312d83dde3bcb1ca.json), [complete native rows](../reference_outputs/RAN3_P2_CQ6-1/9e810be0e13d623143655064a9ee6db09f4dee690ace3c80312d83dde3bcb1ca.jsonl); 16 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `9a507ec20e9e398ed2af1966b1e26159e27674f2c26b2b517129b59535cd7266`.

## RAN3_P2_CQ6-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show ZTE's resolution-contribution trend over time (influence trajectory).

**Revised question:** For each recorded meeting, return meeting identifier, integer meeting number, and number of distinct Resolutions referencing ZTE-submitted TDocs; order by integer meeting number then canonical meeting identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Start from every stored Meeting and retain zero matching ZTE-reference Resolution counts via optional full path. Recorded association is a substantive variant of influence/contribution; integer meeting order plus canonical identifier tie is explicit.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(DISTINCT r) AS cnt ORDER BY mNum ASC
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (m)<-[:MADE_AT]-(r:Resolution)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'ZTE'}) RETURN m.canonicalMeetingNumber AS meeting,m.meetingNumberInt AS meetingNumber,count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC,meeting ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    },
    {
      "name": "meetingNumber",
      "nullable": false,
      "source_column_or_expression": "meetingNumber",
      "type": "integer"
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
        "direction": "asc",
        "field": "meetingNumber"
      },
      {
        "direction": "asc",
        "field": "meeting"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ6-2/3a0cf224e5313389e4ae037049441a74b1b49457c1794fb1d681cdea1f0e592f.json), [complete native rows](../reference_outputs/RAN3_P2_CQ6-2/3a0cf224e5313389e4ae037049441a74b1b49457c1794fb1d681cdea1f0e592f.jsonl); 58 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `7e55316e9ef441c521359dbd6b2a9262aab88c9522e9463616a7e487ad79dd3d`.

## RAN3_P2_CQ6-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show ZTE's moderator-role trend over time (leadership trajectory).

**Revised question:** For each recorded meeting with ZTE-moderated Summary nodes, return meeting identifier, integer meeting number and distinct Summary-node count; order by integer meeting number then canonical meeting identifier ascending. Return named records with meeting, meetingNumber, summaryCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Trend is observed Summary-node count, not inferred leadership; meeting/count mapping and order explicit.

**Original query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(s) AS cnt ORDER BY mNum ASC
```

**Revised query**

```cypher
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT s) AS summaryCount ORDER BY meetingNumber ASC, meeting ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meeting",
      "nullable": false,
      "source_column_or_expression": "meeting",
      "type": "string"
    },
    {
      "name": "meetingNumber",
      "nullable": false,
      "source_column_or_expression": "meetingNumber",
      "type": "integer"
    },
    {
      "name": "summaryCount",
      "nullable": false,
      "source_column_or_expression": "summaryCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "asc",
        "field": "meetingNumber"
      },
      {
        "direction": "asc",
        "field": "meeting"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P2_CQ6-3/393393bc166f940dc3bc101c912556c083f8dcfc331f0e60ac6e0cd5fa1ef4ed.json), [complete native rows](../reference_outputs/RAN3_P2_CQ6-3/393393bc166f940dc3bc101c912556c083f8dcfc331f0e60ac6e0cd5fa1ef4ed.jsonl); 14 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `63affc6d7e4b3b64e95625271012af0d40e2cc561f49c0980d04890858e871b4`.

## RAN3_P3_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all sections of spec 38.423 (full-structure overview).

**Revised question:** List all distinct section identifiers, section numbers, titles and levels linked to all recorded editions of specification38.423. Return named records with sectionId, sectionNumber, title, level. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original all conflicts with LIMIT25; remove cap and explicitly include recorded editions using section IDs.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "sectionNumber",
      "nullable": false,
      "source_column_or_expression": "sectionNumber",
      "type": "string"
    },
    {
      "name": "title",
      "nullable": false,
      "source_column_or_expression": "title",
      "type": "string"
    },
    {
      "name": "level",
      "nullable": false,
      "source_column_or_expression": "level",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-1/2fb5cc70df6699fa58c993640939e6ae51e291bd20532f8acd489e9075c30d28.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-1/2fb5cc70df6699fa58c993640939e6ae51e291bd20532f8acd489e9075c30d28.jsonl); 3,208 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `aa96a6fd927169f396a746fd30c55ed12377a69f1946664bc0dcb23699fc176c`.

## RAN3_P3_CQ1-10

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** Find the spec and section for Table 8.1-1 of spec 38.423 (table-provenance lookup).

**Revised question:** List distinct specification-number and section-identifier pairs that contain a recorded TSTable numbered8.1-1 in any recorded edition of specification38.423. Return named records with specNumber, sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original unstated latest-release LIMIT1 can hide editions/table matches; original asks spec+section, not caption. Preserve lookup across recorded editions. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.423'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(t:TSTable {tableNumber:'8.1-1'}) WHERE rk.specRelease IS NOT NULL WITH rk,sec,t ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN rk.specNumber, sec.sectionId, t.tableCaption
```

**Revised query**

```cypher
MATCH (rk:Spec {specNumber:'38.423'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(t:TSTable {tableNumber:'8.1-1'}) RETURN DISTINCT rk.specNumber AS specNumber,sec.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-10/f6dc4dec4cd1aaf16436ed1d950dbe2ab8c9a5d28d8123354cd0214d6f8438a1.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-10/f6dc4dec4cd1aaf16436ed1d950dbe2ab8c9a5d28d8123354cd0214d6f8438a1.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `72a55ba897b34b252f5db22ae242b8e180a667d683d1a2f7cb9108cfb48a3722`.

## RAN3_P3_CQ1-11

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by section count (largest specs by structure).

**Revised question:** Return top5 specification-number groups by number of distinct linked Section nodes across recorded editions; break ties by spec number ascending and return all groups if fewer than5 exist. Return named records with specNumber, sectionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Paired spec/count, explicit all-edition grouping and node unit, deterministic top5 boundary.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT s) AS sectionCount ORDER BY sectionCount DESC, specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
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
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-11/9d2a11cc7c4b434a3ccce19916d796b9afdd6603cab1b27c6fae20f9c6156fc7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-11/9d2a11cc7c4b434a3ccce19916d796b9afdd6603cab1b27c6fae20f9c6156fc7.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b3cbdefcc153beb333576d72a82fdc9bca4fe31eb974b06100406c8ef9bf481c`.

## RAN3_P3_CQ1-12

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the section-level distribution in spec 38.423 (structural-depth profile).

**Revised question:** For every recorded section-level value in all editions of specification38.423, return level and number of distinct matching Section nodes. Return named records with level, sectionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Full level/count distribution required; all-edition population and distinct section unit explicit.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT s.level AS level, count(DISTINCT s) AS sectionCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "level",
      "nullable": false,
      "source_column_or_expression": "level",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-12/cfc04bdeebd9c936cd9ba87ebc0ce193b9b2ca92215fc0c932f41d21a96e8ad4.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-12/cfc04bdeebd9c936cd9ba87ebc0ce193b9b2ca92215fc0c932f41d21a96e8ad4.jsonl); 4 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `27f089a4399c4e894e89300f3259c8acadbcf667cc93238d60e51a202fca0d50`.

## RAN3_P3_CQ1-13

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections marked Void (deprecated-section survey).

**Revised question:** List all distinct Section identifiers whose recorded title contains Void or void. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Source-title marker predicate explicit rather than claiming independently validated deprecation; remove cap.

**Original query**

```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 15
```

**Revised query**

```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN DISTINCT s.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-13/558ca9cc6c01e624e75ee44641985a11b12df81fb3605967fb805215903733f7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-13/558ca9cc6c01e624e75ee44641985a11b12df81fb3605967fb805215903733f7.jsonl); 184 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `29cd4abae1b41ee88ec5824a875b2713d61f64bb3d922ef041eeb74f68c7169b`.

## RAN3_P3_CQ1-14

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total counts of sections, tables, and figures (corpus-size overview).

**Revised question:** Return total numbers of recorded Section, TSTable and TSFigure nodes. Return named records with sectionCount, tableCount, figureCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** All three requested corpus counts paired in one named record; source labels and count units explicit.

**Original query**

```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```

**Revised query**

```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN DISTINCT secCnt AS sectionCount, tblCnt AS tableCount, figCnt AS figureCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionCount",
      "nullable": false,
      "source_column_or_expression": "sectionCount",
      "type": "integer"
    },
    {
      "name": "tableCount",
      "nullable": false,
      "source_column_or_expression": "tableCount",
      "type": "integer"
    },
    {
      "name": "figureCount",
      "nullable": false,
      "source_column_or_expression": "figureCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-14/3777a8ab0dcd9d592133503aa542223492d249632e33337fc810b5ce6269c521.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-14/3777a8ab0dcd9d592133503aa542223492d249632e33337fc810b5ce6269c521.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `200ac5dad629364efd07b85e1834cad64a83d6c5dcbd6ae5f6ada5b7bf94fbc5`.

## RAN3_P3_CQ1-15

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 sections by table count (table-dense sections).

**Revised question:** Return top5 Section identifiers by count of distinct contained TSTable nodes, ties by section identifier ascending; return all if fewer than5 have tables. Return named records with sectionId, tableCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Explicit positive-table population and distinct table-node unit, paired counts, deterministic ties.

**Original query**

```cypher
MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId, count(t) AS tableCount ORDER BY tableCount DESC, s.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT s.sectionId AS sectionId, count(DISTINCT t) AS tableCount ORDER BY tableCount DESC, sectionId ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
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
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-15/932f4680aa80332a3bbdd13b19041c12f311f4c5560b1a3af287686e47a73983.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-15/932f4680aa80332a3bbdd13b19041c12f311f4c5560b1a3af287686e47a73983.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4998ab79e6bf4a370bf3508e7dc797306e73cd533ca98625711b109050403546`.

## RAN3_P3_CQ1-16

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 sections by figure count (figure-dense sections).

**Revised question:** Return top5 Section identifiers by count of distinct contained TSFigure nodes, ties by section identifier ascending; return all if fewer than5 have figures. Return named records with sectionId, figureCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Explicit positive-figure population and distinct figure-node unit, paired counts, deterministic ties.

**Original query**

```cypher
MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId, count(f) AS figCount ORDER BY figCount DESC, s.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN DISTINCT s.sectionId AS sectionId, count(DISTINCT f) AS figureCount ORDER BY figureCount DESC, sectionId ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "figureCount",
      "nullable": false,
      "source_column_or_expression": "figureCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "figureCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-16/f23b567b6fe58370f446bb900814a0c9abc88e89c9972a742bf399fd55c229a2.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-16/f23b567b6fe58370f446bb900814a0c9abc88e89c9972a742bf399fd55c229a2.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e6780c3efccd759b3230f00efa83a9405e1aea1b048034bcf5e342ca19be305b`.

## RAN3_P3_CQ1-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the subsections of section 9.3.1 in spec 38.413 (navigating IE definitions).

**Revised question:** List all distinct immediate child Section identifiers, numbers and titles linked by HAS_SUB_SECTION from section9.3.1 in any recorded edition of specification38.413. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Subsections must state immediate relationship and editions; remove unstated latest-only and15 caps. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'9.3.1'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'9.3.1'})-[:HAS_SUB_SECTION]->(c:Section) RETURN DISTINCT c.sectionId AS sectionId,c.sectionNumber AS sectionNumber,c.sectionTitle AS title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "sectionNumber",
      "nullable": false,
      "source_column_or_expression": "sectionNumber",
      "type": "string"
    },
    {
      "name": "title",
      "nullable": false,
      "source_column_or_expression": "title",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-2/725424fefbe3766103b5b7d5074d22dfbad2195e813aa288df2080e2a5bb133b.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-2/725424fefbe3766103b5b7d5074d22dfbad2195e813aa288df2080e2a5bb133b.jsonl); 1,119 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `37b16a1daa7ebf2393c2f8f8b88d89e4007ec436233938c7893909baa76faa11`.

## RAN3_P3_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-1 sections of spec 38.413 (top-level table of contents).

**Revised question:** List all distinct Section identifiers, numbers and titles at level1 in every recorded edition of specification38.413. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Edition scope and section identity explicit; keep level predicate and grade full structure record.

**Original query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

**Revised query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "sectionNumber",
      "nullable": false,
      "source_column_or_expression": "sectionNumber",
      "type": "string"
    },
    {
      "name": "title",
      "nullable": false,
      "source_column_or_expression": "title",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-4/e1c39964bb71dd5c922c2649d667ce8a75b0e2214458821036bad71a8d72e98b.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-4/e1c39964bb71dd5c922c2649d667ce8a75b0e2214458821036bad71a8d72e98b.jsonl); 55 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `6b13e65179d764b9d25ad9a2d471d905dfbb850728232bacb8bbc6d6366784d6`.

## RAN3_P3_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the tables in section 8.1 of spec 38.413 (finding tabular content).

**Revised question:** List all distinct TSTable identifiers, table numbers and captions contained in section8.1 of every recorded edition of specification38.413. Return named records with tableId, tableNumber, caption. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original silent latest-release LIMIT1 is removed, table-ID distinguishes editions; three named inventory fields explicit. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.1'})-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId,t.tableNumber AS tableNumber,t.tableCaption AS caption
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tableId",
      "nullable": false,
      "source_column_or_expression": "tableId",
      "type": "string"
    },
    {
      "name": "tableNumber",
      "nullable": false,
      "source_column_or_expression": "tableNumber",
      "type": "string"
    },
    {
      "name": "caption",
      "nullable": false,
      "source_column_or_expression": "caption",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-5/72c3007f2f90e10172b37fbbc3cd1068c13876216edd05265ffedc891a21655b.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-5/72c3007f2f90e10172b37fbbc3cd1068c13876216edd05265ffedc891a21655b.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `199bef7e4d91f08f0d764d053d5e991bf836fa1f2b4c85ee58b08f70b758c2ee`.

## RAN3_P3_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the figures in section 8.7.5.2 of spec 38.413 (locating diagrams).

**Revised question:** List all distinct TSFigure identifiers, figure numbers and captions contained in section8.7.5.2 of every recorded edition of specification38.413. Return named records with figureId, figureNumber, caption. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unstated latest-release choice; distinguish figure editions by identifier and require named inventory fields. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.7.5.2'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.7.5.2'})-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN DISTINCT f.figureId AS figureId,f.figureNumber AS figureNumber,f.figureCaption AS caption
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "figureId",
      "nullable": false,
      "source_column_or_expression": "figureId",
      "type": "string"
    },
    {
      "name": "figureNumber",
      "nullable": false,
      "source_column_or_expression": "figureNumber",
      "type": "string"
    },
    {
      "name": "caption",
      "nullable": false,
      "source_column_or_expression": "caption",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-6/d20f33ed9bb94faffeb4bb2b8acd46ae5b0b21a97ae4d524cc15356345b35183.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-6/d20f33ed9bb94faffeb4bb2b8acd46ae5b0b21a97ae4d524cc15356345b35183.jsonl); 12 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `0082c1568f318ea55a8a520663a81b44c334162a4e01ff09e31fe13b8bdd7270`.

## RAN3_P3_CQ1-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** Return the section that contains Table 8.1-1 of spec 38.413 (table-to-section lookup).

**Revised question:** List all distinct Section identifiers containing TSTable number8.1-1 in any recorded edition of specification38.413. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original silent LIMIT1 can conceal multiple editions; grade requested containing section ID only. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(t:TSTable {tableNumber:'8.1-1'}) WHERE rk.specRelease IS NOT NULL WITH sec,t,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN sec.sectionId, sec.sectionTitle
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(:TSTable {tableNumber:'8.1-1'}) RETURN DISTINCT sec.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-7/d8056ac2750df5db029f7680c25600794151cb241ba01cce547bba9fd2d3550a.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-7/d8056ac2750df5db029f7680c25600794151cb241ba01cce547bba9fd2d3550a.jsonl); 5 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `31089718c3fd07a6b40d0ea480558380f11dac1a43c3c51e1c8ec12fc1cbe119`.

## RAN3_P3_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all tables in spec 38.423 (tabular-content inventory).

**Revised question:** List all distinct TSTable identifiers, table numbers and captions in any recorded edition of specification38.423. Return named records with tableId, tableNumber, caption. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** All inventory cannot be capped25; edition-aware table identity and explicit required inventory fields.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT t.tableId AS tableId, t.tableNumber AS tableNumber, t.tableCaption AS caption
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tableId",
      "nullable": false,
      "source_column_or_expression": "tableId",
      "type": "string"
    },
    {
      "name": "tableNumber",
      "nullable": false,
      "source_column_or_expression": "tableNumber",
      "type": "string"
    },
    {
      "name": "caption",
      "nullable": false,
      "source_column_or_expression": "caption",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-8/27ff145ed4cc4f3195bd241a543645a056b5408d46c7a2edd93d7769c95a834b.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-8/27ff145ed4cc4f3195bd241a543645a056b5408d46c7a2edd93d7769c95a834b.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `ea79c615986c706daf8c6be0856214763a2e3502973db3b554c03896f86b2e5c`.

## RAN3_P3_CQ1-9

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections whose title contains 'handover' (topic-based section search).

**Revised question:** List all distinct Section identifiers whose title contains handover ignoring letter case. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove unstated cap; retain exact original source-title case-insensitive predicate rather than infer topic.

**Original query**

```cypher
MATCH (sec:Section) WHERE toLower(sec.sectionTitle) CONTAINS 'handover' RETURN sec.sectionId, sec.sectionTitle ORDER BY sec.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section) WHERE toLower(sec.sectionTitle) CONTAINS 'handover' RETURN DISTINCT sec.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ1-9/6303544f8801b79ac8a47c6d3eb1bdf821b27df4220983aa25e2dda2fb956bd7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ1-9/6303544f8801b79ac8a47c6d3eb1bdf821b27df4220983aa25e2dda2fb956bd7.jsonl); 193 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `815708a1e60e414ce617915c008fdf02c0e4a4d9b93161af609e8a5dd82df9b1`.

## RAN3_P3_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sections that section 10.1 of spec 38.413 references (outgoing cross-references).

**Revised question:** List all distinct target Section identifiers referenced by REFERENCES_SECTION from section10.1 of every recorded edition of specification38.413. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** No question latest-release restriction; remove implicit edition choice and require target identifier. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:REFERENCES_SECTION]->(target:Section) RETURN target.sectionId, target.sectionTitle
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10.1'})-[:REFERENCES_SECTION]->(target:Section) RETURN DISTINCT target.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-1/e10a43527f2fdc8ccf8535248c66becc5810ebbc710f17993f7aa5fe98992f34.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-1/e10a43527f2fdc8ccf8535248c66becc5810ebbc710f17993f7aa5fe98992f34.jsonl); 5 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8c1cb27a4bde5d3412f51115ea5060ec216916e2e9f204da4919b9cdde3072c0`.

## RAN3_P3_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sections that reference section 10 of spec 38.413 (incoming cross-references).

**Revised question:** List all distinct source Section identifiers referencing section10 of any recorded edition of specification38.413. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** No question latest restriction; include recorded editions and grade source sections. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (src:Section)-[:REFERENCES_SECTION]->(sec) RETURN src.sectionId, src.sectionTitle
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10'})<-[:REFERENCES_SECTION]-(src:Section) RETURN DISTINCT src.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-2/4df6cee8d4bee573703c84d3ca60539016c89d22154137321854073e8175f60f.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-2/4df6cee8d4bee573703c84d3ca60539016c89d22154137321854073e8175f60f.jsonl); 20 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8a6f09c9e1a4895187e141bed6490a1655b5e17677443a2811c76d649ffdad21`.

## RAN3_P3_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the most-referenced sections within spec 38.413 (identifying key sections).

**Revised question:** Return one global ranking of all referenced edition-qualified Section identifiers belonging to recorded specification 38.413 editions. Count distinct referring Section nodes belonging to the same stored Spec edition node as the target; sort count descending then Section identifier ascending. Return named records with sectionId, referringSectionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Specify one global ranking across edition-qualified target IDs, rather than suggesting separate per-edition ranking. Restrict source and target to the same stored edition, count distinct referring Section nodes, and remove unrequested top-ten cap.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}), (s1)-[:REFERENCES_SECTION]->(s2:Section) RETURN s2.sectionId, count(*) AS refs ORDER BY refs DESC, s2.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.413'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId AS sectionId,count(DISTINCT s1) AS referringSectionCount ORDER BY referringSectionCount DESC,sectionId ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "referringSectionCount",
      "nullable": false,
      "source_column_or_expression": "referringSectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referringSectionCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-3/be7d2b446b760432db6637e395aeed4f913b6482775a9cce2e5329537c4623f4.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-3/be7d2b446b760432db6637e395aeed4f913b6482775a9cce2e5329537c4623f4.jsonl); 67 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6b2ac298417303e88b47e488516173a5d1990d36b9826d5637e1069d5cd2b84c`.

## RAN3_P3_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 most-referenced sections overall (globally cited sections).

**Revised question:** Return top10 Section identifiers by count of distinct referring Section nodes, descending count then ascending Section identifier; return all if fewer than10 are referenced. Return named records with sectionId, referringSectionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Top10 paired count and deterministic tie boundary; sectionTitle not required.

**Original query**

```cypher
MATCH (ref:Section)-[:REFERENCES_SECTION]->(s:Section) RETURN s.sectionId, s.sectionTitle, count(ref) AS refCount ORDER BY refCount DESC, s.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (ref:Section)-[:REFERENCES_SECTION]->(s:Section) RETURN DISTINCT s.sectionId AS sectionId, count(DISTINCT ref) AS referringSectionCount ORDER BY referringSectionCount DESC, sectionId ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "referringSectionCount",
      "nullable": false,
      "source_column_or_expression": "referringSectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referringSectionCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-4/99289e04a757e08e1fca1a2a5ee185a058fc641c1caad12f1bc72f2ca8afe04b.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-4/99289e04a757e08e1fca1a2a5ee185a058fc641c1caad12f1bc72f2ca8afe04b.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a127e8ea292bcd9c7243afb99779dd90d6b04feadc916a6bc99dbffa7fba41fa`.

## RAN3_P3_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List cross-spec references from spec 38.401 to other specs (inter-spec dependencies).

**Revised question:** List all distinct source-Section identifier and referenced-specification-number pairs from sections of specification38.401 to other specification numbers. Return named records with sectionId, specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Use explicit BELONGS_TO_SPEC membership rather than an unverified Section-ID prefix; preserve directed source/target roles and other-specification-number criterion, remove cap.

**Original query**

```cypher
MATCH (sec:Section)-[:REFERENCES_SPEC]->(sp:Spec) WHERE sec.sectionId STARTS WITH '38.401-' AND sp.specNumber <> '38.401' RETURN sec.sectionId, sp.specNumber ORDER BY sec.sectionId, sp.specNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.401'}), (sec)-[:REFERENCES_SPEC]->(sp:Spec) WHERE sp.specNumber<>'38.401' RETURN DISTINCT sec.sectionId AS sectionId,sp.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-5/efb2ca7da008137eb6a54d0d439bee7f820d5830fcfe2e3f1e71d4ee4c3333aa.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-5/efb2ca7da008137eb6a54d0d439bee7f820d5830fcfe2e3f1e71d4ee4c3333aa.jsonl); 111 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cfd96063d771f2f3f81403f365f8bbf4ccb57c78f576c0c2c8c8cc492056f7ea`.

## RAN3_P3_CQ2-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total number of section cross-references (reference-graph size).

**Revised question:** Count all recorded REFERENCES_SECTION relationship instances. Return named records with referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Specify edge rather than distinct node-pair unit; original count(*) over one edge directly supports it.

**Original query**

```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```

**Revised query**

```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN DISTINCT count(*) AS referenceEdgeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "referenceEdgeCount",
      "nullable": false,
      "source_column_or_expression": "referenceEdgeCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-6/95580790a18bcc0ac94d2bb98ca86a54c365e9207b53c4d8d16b02344f1f66c9.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-6/95580790a18bcc0ac94d2bb98ca86a54c365e9207b53c4d8d16b02344f1f66c9.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a5907559920a5cf8eb5cbf2674ae383eab18a9a0f0004a5bc4f6dc17bc2329e6`.

## RAN3_P3_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by intra-spec references (internal-cohesion metric).

**Revised question:** Return top5 specification-number groups by number of distinct REFERENCES_SECTION edges whose endpoints belong to the same recorded Spec edition, ties by specNumber ascending; return all if fewer than5 exist. Return named records with specNumber, referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Distinct edge unit avoids multiply matched BELONGS_TO joins; intra-edition identity and all-edition grouping explicit.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber, count(*) AS intraRefs ORDER BY intraRefs DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[reference:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC, specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "referenceEdgeCount",
      "nullable": false,
      "source_column_or_expression": "referenceEdgeCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referenceEdgeCount"
      },
      {
        "direction": "asc",
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-7/3ae2713eeeb72b83dd9331e4c86f21517fab2d5149c32e431a6ae1705b8939da.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-7/3ae2713eeeb72b83dd9331e4c86f21517fab2d5149c32e431a6ae1705b8939da.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `be16745b58bd8e6c202b19bd9d5fd49805fcab5cb10f474c871c9dce877a91f0`.

## RAN3_P3_CQ2-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 most-referenced sections within spec 38.423 (internal reference hubs).

**Revised question:** Return the top five edition-qualified Section identifiers belonging to recorded specification 38.423 editions by count of distinct referring Section nodes in the same stored Spec edition, including zero-count targets. Rank count descending then sectionId ascending; return every target if fewer than five targets exist. Return named records with sectionId, referringSectionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Preserve every recorded target Section including zero incoming same-edition references. Distinct source-node count and deterministic top-five cutoff ties are explicit; do not silently restrict to positively referenced targets.

**Original query**

```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId, s2.sectionTitle, count(*) AS refCount ORDER BY refCount DESC, s2.sectionId LIMIT 5
```

**Revised query**

```cypher
MATCH (s2:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.423'}) OPTIONAL MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp), (s1)-[:REFERENCES_SECTION]->(s2) RETURN s2.sectionId AS sectionId,count(DISTINCT s1) AS referringSectionCount ORDER BY referringSectionCount DESC,sectionId ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "referringSectionCount",
      "nullable": false,
      "source_column_or_expression": "referringSectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referringSectionCount"
      },
      {
        "direction": "asc",
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ2-8/fd01940afdbbdbe89f89955a7501b6781b1564bc3c888c00799625d28b08edc7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ2-8/fd01940afdbbdbe89f89955a7501b6781b1564bc3c888c00799625d28b08edc7.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5989a4abdeb8b82d7e810b744d435fffbfef169492154f551c770d5ea3d2f34f`.

## RAN3_P3_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the spec and affected clauses modified by CR R3-253336 (change-scope lookup).

**Revised question:** Return modified specification numbers paired with recorded affected-clauses text for CR R3-253336. Return named records with specNumber, clausesAffected. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Both requested fields must remain associated; clauses text does not certify actual resolved Section nodes.

**Original query**

```cypher
MATCH (cr:CR {tdocNumber: 'R3-253336'})-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, cr.clausesAffected
```

**Revised query**

```cypher
MATCH (cr:CR {tdocNumber: 'R3-253336'})-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, cr.clausesAffected AS clausesAffected
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "clausesAffected",
      "nullable": false,
      "source_column_or_expression": "clausesAffected",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-1/73ac830c270f6590f59733e5594e0fb06032cca60fe7eff7cc66cbc7a2a2b7a8.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-1/73ac830c270f6590f59733e5594e0fb06032cca60fe7eff7cc66cbc7a2a2b7a8.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `21cf40661bc005536143a06979ee2f8e9c53f0dbb545f5a1b614c4f135caa010`.

## RAN3_P3_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** Show the level-1 section structure of spec 38.423 targeted by CRs (change-context overview).

**Revised question:** List all distinct level1 Section identifiers, numbers and titles in recorded editions of specification38.423 whose hub is modified by a CR. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original silently latest edition and10 cap; level1 structure across recorded editions explicit without pretending CR-clause targeting. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.423'}) WHERE hub.specRelease IS NULL WITH DISTINCT hub MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (rk)<-[:BELONGS_TO_SPEC]-(s:Section {level:1}) RETURN s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.423'}) WHERE hub.specRelease IS NULL WITH DISTINCT hub MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub), (s:Section {level:1})-[:BELONGS_TO_SPEC]->(rk) RETURN DISTINCT s.sectionId AS sectionId,s.sectionNumber AS sectionNumber,s.sectionTitle AS title
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    },
    {
      "name": "sectionNumber",
      "nullable": false,
      "source_column_or_expression": "sectionNumber",
      "type": "string"
    },
    {
      "name": "title",
      "nullable": false,
      "source_column_or_expression": "title",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-2/1028a1b40847396e9218b1fbb3f40c1afedebbcebba55522090b9df36367afdc.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-2/1028a1b40847396e9218b1fbb3f40c1afedebbcebba55522090b9df36367afdc.jsonl); 55 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `beb229078fe95fb2654e7ce6927dfb4327642b524574e02f7fcf2ad1b8483476`.

## RAN3_P3_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that modify spec 38.423 (change history of a spec).

**Revised question:** List all distinct CR TDoc identifiers with MODIFIES edge to specification38.423. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Remove cap; requested CR IDs rather than implicit title/status payload.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT cr.tdocNumber AS crTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-3/8d7c39df41e87b672f5769ede27c19764e5ba9eb26e315a2da71a50d6c89e479.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-3/8d7c39df41e87b672f5769ede27c19764e5ba9eb26e315a2da71a50d6c89e479.jsonl); 2,992 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `033c362736e6c30ffce1734b6355c017de06860efc036564b573baf483ff706b`.

## RAN3_P3_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that record affected clauses (clause-level change survey).

**Revised question:** List all distinct CR TDoc identifiers with nonempty recorded clausesAffected text. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Predicate supports requested CR inventory; no hidden category/clauses requirement and no cap.

**Original query**

```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN DISTINCT cr.tdocNumber AS crTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-4/f4461bdd40d4132478ef5c23dae19e5a411fb387147c8c738d072e212287edc3.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-4/f4461bdd40d4132478ef5c23dae19e5a411fb387147c8c738d072e212287edc3.jsonl); 2,339 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `db07dd3b783fd9847b93b33c5794c2c3ccb87666cfae4fa03d6428b42b7477a9`.

## RAN3_P3_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the specs modified by CRs under Work Item NR_newRAT-Core (work-item change footprint).

**Revised question:** List all distinct specification numbers modified by CR-labeled TDocs linked to Work Item NR_newRAT-Core. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested spec inventory does not demand supporting CR counts; remove cap and keep workitem/CR restrictions.

**Original query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-5/f394a7574e3b81646cddf2831076f2ded786add512aa55c76de4addf4c36e02d.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-5/f394a7574e3b81646cddf2831076f2ded786add512aa55c76de4addf4c36e02d.jsonl); 44 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `48b20eafe00875a823005f51fd51c1c75e01ee80003d2645f44837d858525d72`.

## RAN3_P3_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the specs that Huawei's CRs modify (company change footprint).

**Revised question:** List all distinct specification numbers linked by MODIFIES from Huawei-submitted CRs. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested specs only, count incidental; remove cap.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-6/d9ca583463e772a18d77864dbea54c1ff0f918a49c74aba06fc64483a8b162c7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-6/d9ca583463e772a18d77864dbea54c1ff0f918a49c74aba06fc64483a8b162c7.jsonl); 86 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b8f61861eaff48a07b0e7bf8dce277988aa16bcc0c991c48c2cd108b34e21b48`.

## RAN3_P3_CQ3-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original actual affected-section and specification-edition semantics are not independently validated. The revised task uses exact trimmed comma-separated clause tokens and recorded TARGET_RELEASE/specRelease equality; this explicit formal variant does not certify actual normative clause effects or the original intended edition.

**Original question:** List CRs whose affected clauses match actual sections of spec 38.423 (clause-to-section validation).

**Revised question:** List distinct CR TDoc identifiers, exact comma-separated clause tokens, and matched Section identifiers in specification38.423 editions whose specRelease equals that CR's recorded TARGET_RELEASE name. Return named records with crTdoc, clause, sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original arbitrarily matches latest edition rather than CR target release; exact source tokens/recorded-release equality operationalized, no range parsing or historical causal validity claimed. Release-matched edition selection and literal comma-token matching define a substantive variant; original normative affected-section meaning remains unresolved.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.423'}) WHERE hub.specRelease IS NULL AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' WITH cr, hub, split(cr.clausesAffected, ',') AS clauses MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH cr, clauses, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH cr, clauses, collect(rk)[0] AS latestRk UNWIND clauses AS clause WITH cr, latestRk, trim(clause) AS clause MATCH (s:Section)-[:BELONGS_TO_SPEC]->(latestRk) WHERE s.sectionNumber = clause RETURN cr.tdocNumber, clause, s.sectionId ORDER BY cr.tdocNumber, clause, s.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.423'}), (cr)-[:TARGET_RELEASE]->(rel:Release) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected<>'' WITH DISTINCT cr,rel UNWIND split(cr.clausesAffected,',') AS rawClause WITH cr,rel,trim(rawClause) AS clause MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.423'}) WHERE sp.specRelease=rel.releaseName AND s.sectionNumber=clause RETURN DISTINCT cr.tdocNumber AS crTdoc,clause,s.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    },
    {
      "name": "clause",
      "nullable": false,
      "source_column_or_expression": "clause",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-7/9b33920c22548de0ba3c65522bcfac139cc3064fb5e1cf5ae2978e8fadc67df7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-7/9b33920c22548de0ba3c65522bcfac139cc3064fb5e1cf5ae2978e8fadc67df7.jsonl); 2,438 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `d52711124aeb23b32f2f77d4d68085a7f268021b729ab8c5f2c8236dcff19614`.

## RAN3_P3_CQ3-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by Rel-18 CR count (release-scoped change volume).

**Revised question:** Return top5 specification numbers by distinct CR-node count targeting Rel-18, ties by specNumber ascending; return all if fewer than5 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested pair and distinct CR unit; deterministic top5 ties.

**Original query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCnt ORDER BY crCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
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
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ3-8/4fced1ef5dbf1287f27ca189f70cb6244122e0c58e371f67c050ab4b6bacddf7.json), [complete native rows](../reference_outputs/RAN3_P3_CQ3-8/4fced1ef5dbf1287f27ca189f70cb6244122e0c58e371f67c050ab4b6bacddf7.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `92e0963f597aa5b511fb04932aba1f2cb4a0e0cfc25106fe5b88b0f9391b31d4`.

## RAN3_P3_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the specs modified by CRs that resolutions approved (decision-to-spec impact).

**Revised question:** List all distinct specification numbers modified by CRs referenced by recorded Resolutions. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** REFERENCES does not establish resolutions approved CRs; explicitly restrict to documentary reference task and remove cap.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(r) AS resolutions ORDER BY resolutions DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ4-1/eb96d70eeb40804a2d9c9f0f4d4959b246bf17af1df29b5fa9edd1d24c5f9940.json), [complete native rows](../reference_outputs/RAN3_P3_CQ4-1/eb96d70eeb40804a2d9c9f0f4d4959b246bf17af1df29b5fa9edd1d24c5f9940.jsonl); 57 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `73629fe27f50c80f1a429908f217b848d6403130c55059f6d3966d2c4f207172`.

## RAN3_P3_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the resolutions approving CRs that modify spec 38.423 (approval provenance).

**Revised question:** List all distinct Resolution-identifier and CR-TDoc pairs where a Resolution references a CR modifying specification38.423. Return named records with resolutionId, crTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original approving is unsupported by REFERENCES; retain exact documented relation as separate variant and remove cap.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT r.resolutionId AS resolutionId, cr.tdocNumber AS crTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ4-2/bb5d29c58e72c80ff807d701bd31c85019418c98f838bfd6f4e9153ba1a44bb9.json), [complete native rows](../reference_outputs/RAN3_P3_CQ4-2/bb5d29c58e72c80ff807d701bd31c85019418c98f838bfd6f4e9153ba1a44bb9.jsonl); 617 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8faa701d5fbbcddcc77d57ba011a82168000da3e6ad1bac220066f20a3f18fd4`.

## RAN3_P3_CQ4-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original actual affected-section and specification-edition semantics are not independently validated. The revised task uses exact trimmed comma-separated clause tokens and recorded TARGET_RELEASE/specRelease equality; this explicit formal variant does not certify actual normative clause effects or the original intended edition.

**Original question:** Trace affected sections through CRs referenced by resolutions (decision-to-section tracing).

**Revised question:** List distinct Resolution identifiers, referenced CR TDoc identifiers, exact comma-separated affected-clause tokens and matching Section identifiers in editions of modified specifications matching the CR's recorded TARGET_RELEASE. Return named records with resolutionId, crTdoc, clause, sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original returns clause string without actual Section match; candidate executes recorded release-aware exact-clause matching and retains path roles. Release-matched edition selection and literal comma-token matching define a substantive variant; original normative affected-section meaning remains unresolved.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN r.resolutionId, cr.tdocNumber, cr.clausesAffected, sp.specNumber ORDER BY r.resolutionId, cr.tdocNumber, sp.specNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(hub:Spec), (cr)-[:TARGET_RELEASE]->(rel:Release) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected<>'' WITH DISTINCT r,cr,hub.specNumber AS specNumber,rel UNWIND split(cr.clausesAffected,',') AS rawClause WITH r,cr,specNumber,rel,trim(rawClause) AS clause MATCH (s:Section)-[:BELONGS_TO_SPEC]->(edition:Spec) WHERE edition.specNumber=specNumber AND edition.specRelease=rel.releaseName AND s.sectionNumber=clause RETURN DISTINCT r.resolutionId AS resolutionId,cr.tdocNumber AS crTdoc,clause,s.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "resolutionId",
      "nullable": false,
      "source_column_or_expression": "resolutionId",
      "type": "string"
    },
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    },
    {
      "name": "clause",
      "nullable": false,
      "source_column_or_expression": "clause",
      "type": "string"
    },
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ4-3/70845dbc45e7c4a27ddc0012e6837dbf64513a740cbac20970eede123888bb5d.json), [complete native rows](../reference_outputs/RAN3_P3_CQ4-3/70845dbc45e7c4a27ddc0012e6837dbf64513a740cbac20970eede123888bb5d.jsonl); 1,156 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `576c91d74298e9da5221d79a6497123f49a33ac11ce20f06badc51b464a86e2a`.

## RAN3_P3_CQ4-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs most modified via the resolution-to-CR-to-spec path (decision-driven change ranking).

**Revised question:** Return top5 specification numbers by count of distinct CR nodes modifying the spec and referenced by at least one recorded Resolution, together with the count of distinct referencing Resolutions; ties by specNumber ascending. Return named records with specNumber, crCount, resolutionCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Most modified implies CR count, original ranked resolution count; correct ranking unit and make documentary path rather than decision-driven causation explicit.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS resolutions, count(DISTINCT cr) AS crs ORDER BY resolutions DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount, count(DISTINCT r) AS resolutionCount ORDER BY crCount DESC, specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
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
        "field": "crCount"
      },
      {
        "direction": "asc",
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ4-4/bc8064c5a1aa7548f38bd2ce01319a1385c7f5a2138e4df5d10101685ff4b6ea.json), [complete native rows](../reference_outputs/RAN3_P3_CQ4-4/bc8064c5a1aa7548f38bd2ce01319a1385c7f5a2138e4df5d10101685ff4b6ea.jsonl); 5 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `24eb21e03ded15c81f114f944803fa4c14476d212770197a7fbdb0b90ba60c83`.

## RAN3_P3_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the total number of CRs modifying spec 38.423 (change-volume metric).

**Revised question:** Count distinct CR nodes linked by MODIFIES to specification38.423. Return named records with crCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Distinct CR unit prevents duplicate edge/edition joins from inflating change volume.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN count(cr) AS totalCRs
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
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
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ5-1/fed51942115c59671128786578f07ce3a1a86cceedfbb8f07223dfff2f2adf2f.json), [complete native rows](../reference_outputs/RAN3_P3_CQ5-1/fed51942115c59671128786578f07ce3a1a86cceedfbb8f07223dfff2f2adf2f.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b92f76eb04f47359e52e8e72f3e87d6e02c86b3de97ddd80fb4b182a46786841`.

## RAN3_P3_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 specs by CR count (most-changed specs).

**Revised question:** Return top5 specification numbers by number of distinct modifying CR nodes, ties by specNumber ascending; return all if fewer than5 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Paired CR-node count with deterministic tie boundary; original joins can duplicate CRs.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
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
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ5-2/de2ad2702ef8f90b48d38bb16294d033497d24f74c54d2154165f6d1e61b4293.json), [complete native rows](../reference_outputs/RAN3_P3_CQ5-2/de2ad2702ef8f90b48d38bb16294d033497d24f74c54d2154165f6d1e61b4293.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e20cf600a696bf9d68b320e2ae2404da50c537bb5e8d3286bf37b106a8a7ed09`.

## RAN3_P3_CQ5-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return CR density (CRs per section) for each spec (change-intensity metric).

**Revised question:** For each recorded specification edition with sections, return edition identifier, specification number, release, count of distinct CR nodes targeting that release and modifying that specification number, distinct Section-node count and CRs-per-section ratio. Return named records with editionId, specNumber, release, crCount, sectionCount, density. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original all-release numerator/latest-release denominator and silent top5 are incomparable. New explicitly edition/release-aligned metric changes task and requires fresh predictions; no original-score reuse.

**Original query**

```cypher
MATCH (hub:Spec)<-[:MODIFIES]-(cr:CR) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCnt MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCnt, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCnt, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) WITH hub, crCnt, count(s) AS secCnt RETURN hub.specNumber AS specNumber, crCnt, secCnt, round(1.0 * crCnt / secCnt, 2) AS density ORDER BY density DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (edition:Spec)<-[:BELONGS_TO_SPEC]-(s:Section) WHERE edition.specRelease IS NOT NULL WITH edition,count(DISTINCT s) AS secCnt OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(hub:Spec), (cr)-[:TARGET_RELEASE]->(rel:Release) WHERE hub.specNumber=edition.specNumber AND rel.releaseName=edition.specRelease WITH edition,secCnt,count(DISTINCT cr) AS crCnt RETURN edition.id AS editionId,edition.specNumber AS specNumber,edition.specRelease AS release,crCnt AS crCount,secCnt AS sectionCount,toFloat(crCnt)/secCnt AS density
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "editionId",
      "nullable": false,
      "source_column_or_expression": "editionId",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "release",
      "nullable": false,
      "source_column_or_expression": "release",
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
    },
    {
      "name": "density",
      "nullable": false,
      "source_column_or_expression": "density",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ5-3/d4bf46893e9485b5d55ae8f9edee591ae5f579d33de2668ef6e63fa06904bb7c.json), [complete native rows](../reference_outputs/RAN3_P3_CQ5-3/d4bf46893e9485b5d55ae8f9edee591ae5f579d33de2668ef6e63fa06904bb7c.jsonl); 115 native rows retained. The retained per-item check record has 22 passing scorer checks for this definition.

**Definition SHA-256:** `6cb718dac0153ed5c57945f7967f334ab51316bb0fd7b00afd39b2496df4391e`.

## RAN3_P3_CQ5-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the distribution of table counts per spec (tabular-content profile).

**Revised question:** For every specification number with recorded editions, return number of distinct TSTable nodes linked through Section nodes to those editions, including zero when no such TSTable node is recorded. Return named records with specNumber, tableCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Distribution should not silently top5/exclude zero-table specs; graph-relative zero is query count, not proof source completeness.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(t) AS tblCnt ORDER BY tblCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specRelease IS NOT NULL OPTIONAL MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber AS specNumber,count(DISTINCT t) AS tableCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ5-4/8d4d9580ff46589f79046351b6dd2aa3c4dcb1b0abb2c36a591bd1811915a96e.json), [complete native rows](../reference_outputs/RAN3_P3_CQ5-4/8d4d9580ff46589f79046351b6dd2aa3c4dcb1b0abb2c36a591bd1811915a96e.jsonl); 23 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `75d017b35dd149b1cf57093a3adc9a76c145cfbd20dbd12670b5b82f1a2bb301`.

## RAN3_P3_CQ5-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the distribution of figure counts per spec (figure-content profile).

**Revised question:** For every specification number with recorded editions, return number of distinct TSFigure nodes linked through Section nodes to those editions, including zero when no such TSFigure node is recorded. Return named records with specNumber, figureCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Full spec/count mapping with explicit zero-record population and no silent top5; distinct-node unit.

**Original query**

```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(f) AS figCnt ORDER BY figCnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specRelease IS NOT NULL OPTIONAL MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber AS specNumber,count(DISTINCT f) AS figureCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "figureCount",
      "nullable": false,
      "source_column_or_expression": "figureCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_CQ5-5/ff1533ad075b7f25bc104a1622c898fc98cba219a5341e3202bc65db8a5361b9.json), [complete native rows](../reference_outputs/RAN3_P3_CQ5-5/ff1533ad075b7f25bc104a1622c898fc98cba219a5341e3202bc65db8a5361b9.jsonl); 23 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3ff1539e1aa4b210cd8a888aedf0a2bdc4bbddb383b62a15fe3f2746d0258d67`.

## RAN3_P3_P3-S8-CQ02

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Check whether every item-level entity node links to a Section via definedInSection (grounding-completeness check).

**Revised question:** For recorded item-granularity nodes with any of the five labels RRCParameter,CapabilityItem,Procedure,PerformanceRequirement,ConformanceTest, report population size, number lacking definedInSection to a Section, and whether every node has that link; allLinked is vacuously true for an empty population. Return named records with itemCount, unlinkedCount, allLinked. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original question requires Boolean all-node check, not class-only scoring. Count unique nodes once despite multiple labels; explicit empty-set interpretation.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

**Revised query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,EXISTS { MATCH (n)-[:definedInSection]->(:Section) } AS linked RETURN count(DISTINCT n) AS itemCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END) AS unlinkedCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END)=0 AS allLinked
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "itemCount",
      "nullable": false,
      "source_column_or_expression": "itemCount",
      "type": "integer"
    },
    {
      "name": "unlinkedCount",
      "nullable": false,
      "source_column_or_expression": "unlinkedCount",
      "type": "integer"
    },
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
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.json), [complete native rows](../reference_outputs/RAN3_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b464489747dc94435a2450816d32601237c010ed6ebf1b972bd1eda2aac60e5f`.

## RAN3_P3_P3-S8-CQ05

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the granularity distribution across the five entity classes (item-level vs section-level split).

**Revised question:** For each present class label among RRCParameter,CapabilityItem,Procedure,PerformanceRequirement,ConformanceTest and each recorded granularity value, return class, granularity and distinct-node count; a node belongs to every applicable class and missing granularity is &lt;unset&gt;. Return named records with class, granularity, nodeCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original arbitrarily chooses first matching label. Explicit class-membership distribution preserves roles/counts without inventing mutually exclusive classes.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

**Revised query**

```cypher
MATCH (n) WITH n,[l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']] AS classes UNWIND classes AS class RETURN class,coalesce(n.granularity,'<unset>') AS granularity,count(DISTINCT n) AS nodeCount
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
      "nullable": false,
      "source_column_or_expression": "granularity",
      "type": "string"
    },
    {
      "name": "nodeCount",
      "nullable": false,
      "source_column_or_expression": "nodeCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P3_P3-S8-CQ05/8b13f8809202000e821936d9a2a2c291e97b91dc8a6e72af90e2563a9144dddf.json), [complete native rows](../reference_outputs/RAN3_P3_P3-S8-CQ05/8b13f8809202000e821936d9a2a2c291e97b91dc8a6e72af90e2563a9144dddf.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `77220dcd40d19fc0125d3138d545f812c3fa87d84efe5acae22ae86f056318dd`.

## RAN3_P4_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by CR R3-244680 (cross-spec impact).

**Revised question:** List distinct specification numbers affected by CR R3-244680 through AFFECTS_CORE_SPEC,AFFECTS_TEST_SPEC,AFFECTS_OM_SPEC, excluding specification numbers the same CR directly MODIFIES. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Other specs requires excluding direct-modification targets; original relation type and source CR are context not graded answer.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R3-244680' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (c:CR {tdocNumber:'R3-244680'})-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(direct:Spec) WHERE direct.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ2-1/c2ecf15a365f4fed70844aef56342651807a63791c47a86092fdfd31c9e5db18.json), [complete native rows](../reference_outputs/RAN3_P4_CQ2-1/c2ecf15a365f4fed70844aef56342651807a63791c47a86092fdfd31c9e5db18.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ded9ddf0601359d24999bb1f4f0bd293129fed8ba83eea20747fcb903930ed1c`.

## RAN3_P4_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List CRs modifying spec 38.423 that also affect other specs (ripple-effect detection).

**Revised question:** List all distinct CR TDoc identifiers modifying specification38.423 and having an AFFECTS_CORE_SPEC,AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC edge to a different specification number. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original existence test does not check other-spec condition; add different-spec predicate and remove cap.

**Original query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.423'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.423' } RETURN DISTINCT c.tdocNumber AS crTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ2-2/ae812ce39a4527cdef38d227809e499232b6f97b83895acc106653772f8f7d71.json), [complete native rows](../reference_outputs/RAN3_P4_CQ2-2/ae812ce39a4527cdef38d227809e499232b6f97b83895acc106653772f8f7d71.jsonl); 136 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d8e9c3658b29d8a23f11ff235748a2ec42ad347425bcc85820119f728fda0e2b`.

## RAN3_P4_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List CRs that name spec 38.473 as an affected spec (incoming cross-spec impact).

**Revised question:** List all distinct CR TDoc identifiers with a recorded AFFECTS_CORE_SPEC,AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC edge to specification38.473. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested CR inventory rather than unrequested summary; remove cap and keep recorded impact types.

**Original query**

```cypher
MATCH (s:Spec {specNumber: '38.473'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Spec {specNumber: '38.473'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ2-3/7cc3efbd14961688b777d0be82e1fe8229bc29e94a16d46bd3ed45e4d5a9e3e3.json), [complete native rows](../reference_outputs/RAN3_P4_CQ2-3/7cc3efbd14961688b777d0be82e1fe8229bc29e94a16d46bd3ed45e4d5a9e3e3.jsonl); 353 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d7636f0d43504328b2a24db90ee850428698dcb5e4a7a2bc79258fb66c0abf12`.

## RAN3_P4_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 10 CRs by cross-spec impact count (widest-reaching changes).

**Revised question:** Return the top ten CR TDoc identifiers by the number of distinct specification numbers reached through recorded AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC links, excluding specification numbers directly MODIFIES-linked from the same CR. Include CRs with zero qualifying other-specification targets. Rank count descending then CR identifier ascending; return all CR identifiers if fewer than ten exist. Return named records with crTdoc, affectedSpecCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Count distinct other-specification numbers rather than relation instances; exclude directly modified primary specification numbers and preserve every CR, including zero qualifying targets, through optional impact matching. Explicit exact-top-ten deterministic ties.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
```

**Revised query**

```cypher
MATCH (c:CR) OPTIONAL MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN c.tdocNumber AS crTdoc,count(DISTINCT s.specNumber) AS affectedSpecCount ORDER BY affectedSpecCount DESC,crTdoc ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
      "type": "string"
    },
    {
      "name": "affectedSpecCount",
      "nullable": false,
      "source_column_or_expression": "affectedSpecCount",
      "type": "integer"
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
        "field": "crTdoc"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ2-4/97bcca5bffb80563555c01cb11d9ff3df5cde00ec783d126a23b00561f7f5f2b.json), [complete native rows](../reference_outputs/RAN3_P4_CQ2-4/97bcca5bffb80563555c01cb11d9ff3df5cde00ec783d126a23b00561f7f5f2b.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `062ac99e14e5db32cfdf6dc640e40c7f5993b28e1199b68c446db271c2fafce4`.

## RAN3_P4_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs in CR pack RP-241113 with their change summaries (pack-content review).

**Revised question:** List all distinct CR TDoc identifiers and recorded summaryOfChange values linked by HAS_CR from CRPack RP-241113. Return named records with crTdoc, summary. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested document/summary pair required, nullable source summaries retained and cap removed.

**Original query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-241113'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-241113'})-[:HAS_CR]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.summaryOfChange AS summary
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ3-1/7ae91dd0a82dad8daff91d7d235d2e99f233eefe9a50782900e5814e869902ff.json), [complete native rows](../reference_outputs/RAN3_P4_CQ3-1/7ae91dd0a82dad8daff91d7d235d2e99f233eefe9a50782900e5814e869902ff.jsonl); 37 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d6648d81710d4fb1c5b22af6eb1f79f3f9f2e6c7542038e806e0946a4f5912e0`.

## RAN3_P4_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CR packs holding CRs for Work Items matching NR_newRAT (work-item pack tracing).

**Revised question:** List all distinct CRPack identifiers containing a CR whose linked Work Item code contains NR_newRAT. Return named records with crPackId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Pack IDs requested; tsgMeeting can be null and is not required; remove cap.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC, pack.crPackId LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crPackId",
      "nullable": false,
      "source_column_or_expression": "crPackId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.json), [complete native rows](../reference_outputs/RAN3_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.jsonl); 59 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `4f5b3df4600408b1f26c70b67c2b263de44897c801042969b21f67144e0fc7bd`.

## RAN3_P4_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CR packs submitted to TSG meeting RAN#110 (plenary submission review).

**Revised question:** List all distinct CRPack identifiers with recorded tsgMeeting equal to RAN#110. Return named records with crPackId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original exact predicate retained, no ten cap.

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
      "nullable": false,
      "source_column_or_expression": "crPackId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.json), [complete native rows](../reference_outputs/RAN3_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.jsonl); 18 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `089cca04d73dacb4b65f326f54dc7172c65a575df95cdf1f3d1e6a52ad3ba510`.

## RAN3_P4_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the change reasons of CRs modifying section 9.4.5 of spec 38.473 (section-level change rationale).

**Revised question:** List all distinct CR TDoc identifiers and recorded change-reason values for CRs linked by MODIFIES_SECTION to section9.4.5 of any recorded edition of specification38.473. Return named records with crTdoc, reason. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Reasons must remain paired with CR identifiers; remove unstated cap, edition and recorded-edge interpretation explicit.

**Original query**

```cypher
MATCH (sec:Section {sectionNumber: '9.4.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.473'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber: '9.4.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.473'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.reasonForChange AS reason
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ4-1/6c959cacced0999e181cf60f2e8f2553d2e83cf86f142dde1abc962127ff3250.json), [complete native rows](../reference_outputs/RAN3_P4_CQ4-1/6c959cacced0999e181cf60f2e8f2553d2e83cf86f142dde1abc962127ff3250.jsonl); 308 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c64043c63695351f70ed87b5a59abece1a4148457a2ac26618a8eba2b932df95`.

## RAN3_P4_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the reasons and summaries of CRs approved by agreements (decision-linked change review).

**Revised question:** For every CR referenced by a recorded Agreement, return distinct CR TDoc identifier, recorded change reason and change summary. Return named records with crTdoc, reason, summary. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Agreement REFERENCES does not establish approval. Remove hidden5 cap and nonnull-reason exclusion; preserve nullable requested values.

**Original query**

```cypher
MATCH (a:Agreement)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
```

**Revised query**

```cypher
MATCH (:Agreement)-[:REFERENCES]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc,c.reasonForChange AS reason,c.summaryOfChange AS summary
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ4-2/243f05dac9640abd2647e0ab8dd5c5a1511b73779b7c1f621bf2b15d048c0801.json), [complete native rows](../reference_outputs/RAN3_P4_CQ4-2/243f05dac9640abd2647e0ab8dd5c5a1511b73779b7c1f621bf2b15d048c0801.jsonl); 2,685 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `9033fa83f33a14cdb8e53bd627c27a06e12782fc1c304ff40ed1aee7916616a8`.

## RAN3_P4_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections modified by CRs for Work Items matching NR_newRAT (work-item section footprint).

**Revised question:** List all distinct Section identifiers linked by MODIFIES_SECTION from CRs whose Work Item code contains NR_newRAT. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Recorded clause-target relation and substring filter explicit; remove cap.

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
      "nullable": false,
      "source_column_or_expression": "sectionId",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json), [complete native rows](../reference_outputs/RAN3_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl); 828 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e38a639c59d94c21cd9cf27da7b11cd2f58f51ad4a943581a05ca55bbc707456`.

## RAN3_P4_CQ4-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs affected by Samsung's CRs (company cross-spec footprint).

**Revised question:** List all distinct specification numbers affected through the three AFFECTS relations by CRs submitted by Company named Samsung. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Company exact identity rather than hidden name substring; full spec footprint without cap.

**Original query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName = 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ4-4/89624e477a373b49b7961a691bd4c2d9630cf8a04c4ef18273c4602dccd8d8ef.json), [complete native rows](../reference_outputs/RAN3_P4_CQ4-4/89624e477a373b49b7961a691bd4c2d9630cf8a04c4ef18273c4602dccd8d8ef.jsonl); 30 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `cf992b230da4df53aac901ab5c06f9c3388124e15f66049725a46a1f61a06c37`.

## RAN3_P4_CQ4-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the change summaries of CRs approved at meeting RAN3#123 (meeting-outcome review).

**Revised question:** List distinct CR TDoc identifiers and recorded summaryOfChange values for CRs referenced by Agreements at canonical meeting RAN3#123. Return named records with crTdoc, summary. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Approval unsupported by reference; exact canonical meeting excludes123bis, remove reason filter and cap. Candidate documentary association separate variant.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumberInt = 123 WITH a MATCH (a)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN3#123'}), (a)-[:REFERENCES]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc,c.summaryOfChange AS summary
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdoc",
      "nullable": false,
      "source_column_or_expression": "crTdoc",
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P4_CQ4-5/26c549692c66da3fee3eb6ff44d6af3f06c66942096bd811884fe3f0938dfaca.json), [complete native rows](../reference_outputs/RAN3_P4_CQ4-5/26c549692c66da3fee3eb6ff44d6af3f06c66942096bd811884fe3f0938dfaca.jsonl); 415 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d826f03c8bd7aad0edb68927544a3c1122b79e7199ad7f69ac742a64139ce1c0`.

## RAN3_P5_TR-CQ-1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the completed TRs targeting Rel-17 (release study inventory).

**Revised question:** List distinct TechnicalReport numbers targeting Rel-17 with recorded trStatus equal to Completed. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested TR inventory; title unrequested, release and status literal retained.

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
                  RETURN DISTINCT tr.trNumber AS trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-1-1/7eea9a5213a180906d29a55c316bd9027230da837751e359781ba8759e1786c2.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-1-1/7eea9a5213a180906d29a55c316bd9027230da837751e359781ba8759e1786c2.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `31b8aa42dee2adf32283675f1bce4f30770452e03c026e3850b3e12dc9e87745`.

## RAN3_P5_TR-CQ-1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the status distribution across all TRs (study-progress overview).

**Revised question:** For each recorded TechnicalReport status, return status and distinct TechnicalReport-node count. Return named records with status, trCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Direct reviewer example: status-only answer-column omits distribution counts; require paired fields.

**Original query**

```cypher
MATCH (tr:TechnicalReport) RETURN tr.trStatus, count(tr) AS cnt ORDER BY cnt DESC
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport) RETURN DISTINCT tr.trStatus AS status, count(DISTINCT tr) AS trCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "status",
      "nullable": false,
      "source_column_or_expression": "status",
      "type": "string"
    },
    {
      "name": "trCount",
      "nullable": false,
      "source_column_or_expression": "trCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-1-4/2e5b8bec396345d1d7a8618f28ab2bc8a647c99537e33fa9fad907ed8e95e3ee.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-1-4/2e5b8bec396345d1d7a8618f28ab2bc8a647c99537e33fa9fad907ed8e95e3ee.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f7cbc341d8ef7340f6c3c4fa9017fc2e63dca7d3f14ce1e8518746e1b69879df`.

## RAN3_P5_TR-CQ-2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs impacted by TR 38.823 (study-to-spec impact).

**Revised question:** List distinct specification numbers targeted by recorded TRImpact nodes linked from TechnicalReport38.823. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Spec inventory requested, impactType not required; define record-relative impact rather than independently established influence.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN DISTINCT s.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-2-1/d0e69f1cc487ecd0d94a1e8c2ba82777198095da179c2e3e29b9fc47a0ad1de6.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-2-1/d0e69f1cc487ecd0d94a1e8c2ba82777198095da179c2e3e29b9fc47a0ad1de6.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f62ceffc162e3e05da6c9b1b299109c97f1561a6d1af995eeda65491e17c73f5`.

## RAN3_P5_TR-CQ-2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the impact types recorded for TR 38.801 (impact-category profile).

**Revised question:** List all distinct recorded impactType values of TRImpact nodes linked from TechnicalReport38.801. Return named records with impactType. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Original asks types, not distribution counts; grade requested types only.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.801'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.801'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN DISTINCT imp.impactType AS impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "impactType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-2-2/32d2f693790b9ccecf23d951a88331acb2aa3483de891bb32b9a3d02b683bcbe.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-2-2/32d2f693790b9ccecf23d951a88331acb2aa3483de891bb32b9a3d02b683bcbe.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9cd37844b5610f040f599c7c8359257382404478120ee6a414a0ef37ee504eb8`.

## RAN3_P5_TR-CQ-2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs whose impact type is NewTS (new-spec-producing studies).

**Revised question:** List distinct TechnicalReport numbers with a linked TRImpact whose recorded impactType equals NewTS. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Recorded category filter is sufficient; title unrequested and producing causation not inferred.

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
                  RETURN DISTINCT tr.trNumber AS trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-2-3/0840c2c5205d7076696337d519bc60b4ee6a0e6094133406bcb40bb999489a8e.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-2-3/0840c2c5205d7076696337d519bc60b4ee6a0e6094133406bcb40bb999489a8e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `55aeb6aa1b14d26fa82374f4f625645c820fa6ecb6475b55edece7f7608b3ff3`.

## RAN3_P5_TR-CQ-2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs whose impact type is ExtendSection (section-extending studies).

**Revised question:** List distinct TechnicalReport numbers with a linked TRImpact whose recorded impactType equals ExtendSection. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Use recorded category membership rather than causal interpretation; titles not required.

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
                  RETURN DISTINCT tr.trNumber AS trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-2-4/3872d18e92203f9df04d1af568ab1cf9d8279f292be3f754c0b6b167ff6f5ccb.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-2-4/3872d18e92203f9df04d1af568ab1cf9d8279f292be3f754c0b6b167ff6f5ccb.jsonl); 8 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0bf6b334ea030773f267b3e089d3128492ced29c7ed1b73d97bb4543506b1e2a`.

## RAN3_P5_TR-CQ-2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs that impacted spec 38.401 (spec-provenance in studies).

**Revised question:** List all distinct TechnicalReport numbers whose linked TRImpact targets specification38.401. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Requested TR inventory only, no requirement for type/description; recorded association explicit.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.401'}) RETURN tr.trNumber, imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.401'}) RETURN DISTINCT tr.trNumber AS trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-2-5/8da2e6165fdbb0c2ddca22372ecc60bd99633088756e77a9e27c1e6c0df1d97f.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-2-5/8da2e6165fdbb0c2ddca22372ecc60bd99633088756e77a9e27c1e6c0df1d97f.jsonl); 6 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `69a594fb7d697380b1030be1e162951ba2437748ab31fc6bfb4df81e6e69288f`.

## RAN3_P5_TR-CQ-3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return which specs TR 38.823 impacts, with impact type and description (study-impact detail).

**Revised question:** List distinct specification-number, impact-type and impact-description records linked from TechnicalReport38.823 through TRImpact. Return named records with specNumber, impactType, description. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** All three requested fields paired; duplicate identical output rows collapse under explicit set semantics.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN DISTINCT s.specNumber AS specNumber, imp.impactType AS impactType, imp.impactDescription AS description
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": false,
      "source_column_or_expression": "description",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-3-1/23c416bcfd5a3dea5333bb534e56629cb33794442ba40870227eb0580dc8a9b2.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-3-1/23c416bcfd5a3dea5333bb534e56629cb33794442ba40870227eb0580dc8a9b2.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `8736eae03824fd4e88d71a4697361976295e89807a1edc52d91ae6707da79d2e`.

## RAN3_P5_TR-CQ-3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return TR 38.890's impact on specs 38.401 and 38.423 (targeted-impact review).

**Revised question:** List distinct specification-number, impact-type and impact-description records linked from TechnicalReport38.890 to specifications38.401 or38.423. Return named records with specNumber, impactType, description. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Targeted source/target scope and complete named impact detail explicit.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.890'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) WHERE s.specNumber IN ['38.401', '38.423'] RETURN s.specNumber, imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.890'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) WHERE s.specNumber IN ['38.401', '38.423'] RETURN DISTINCT s.specNumber AS specNumber, imp.impactType AS impactType, imp.impactDescription AS description
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": false,
      "source_column_or_expression": "description",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-3-2/bdce911c098516d910e85e2a637b82829fc6d643985b04e0f83baa54674825d5.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-3-2/bdce911c098516d910e85e2a637b82829fc6d643985b04e0f83baa54674825d5.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `5e5658c10a08fdeab3b442b1dd005bc94511ac0a1d9582e713fc075976f7f809`.

## RAN3_P5_TR-CQ-3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return TR 38.743's impact on spec 38.423 (targeted-impact review).

**Revised question:** List distinct impact-type and impact-description pairs linked from TechnicalReport38.743 to specification38.423. Return named records with impactType, description. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Both requested impact attributes, known source/target are input filters.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.423'}) RETURN imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.423'}) RETURN DISTINCT imp.impactType AS impactType, imp.impactDescription AS description
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": false,
      "source_column_or_expression": "description",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-3-3/86fae7f3d59476a770fccf5787f3bb9eeff7a6d9a3b869bfb5c4b84882336b7a.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-3-3/86fae7f3d59476a770fccf5787f3bb9eeff7a6d9a3b869bfb5c4b84882336b7a.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `9ba00892068df0bc74e78b5bd34515ef46db0cbefc7da48c33a5bc4b871ee8df`.

## RAN3_P5_TR-CQ-4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the Rel-17-targeted TRs with their spec-impact types (release study impact map).

**Revised question:** List all distinct Rel-17-targeted TR-number/specification-number/impact-type records; include one null-spec/null-type record for a TR with no complete linked impact-to-spec path. Return named records with trNumber, specNumber, impactType. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Flatten nested unordered/repeated impact maps into explicit set of named records; retain TR with no complete path via nullable fields; title unrequested.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber AS trNumber,s.specNumber AS specNumber,imp.impactType AS impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": true,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": true,
      "source_column_or_expression": "impactType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-4-1/7da8951deb214dd828819d6d8f4520cb6827fc63153bbd3179e0150400516aa1.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-4-1/7da8951deb214dd828819d6d8f4520cb6827fc63153bbd3179e0150400516aa1.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `d764a6cb706b535204dfb1e700f7a4eb8da8566ced1e60f7226f3a4ed9081cb4`.

## RAN3_P5_TR-CQ-4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the status and scope of TR 38.743 (study status and scope).

**Revised question:** Return recorded status and scope text of TechnicalReport38.743. Return named records with status, scope. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Required status/scope pair, source number is input not answer.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})
                  RETURN DISTINCT tr.trStatus AS status, tr.scope AS scope
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "status",
      "nullable": false,
      "source_column_or_expression": "status",
      "type": "string"
    },
    {
      "name": "scope",
      "nullable": false,
      "source_column_or_expression": "scope",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-4-2/03f32181d3ca899b460e69767229bea5da3637b6802d8206a56e0f1a1a1a14fd.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-4-2/03f32181d3ca899b460e69767229bea5da3637b6802d8206a56e0f1a1a1a14fd.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a89dbe9dc655d14ff103dcf52e056f043d821685cd7b82b445249a574c654f1f`.

## RAN3_P5_TR-CQ-4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return TR 38.879's conclusions and its spec impacts (study-to-spec outcome).

**Revised question:** Return distinct conclusion-text, specification-number and impact-type records for TechnicalReport38.879, including null target/type if it has no complete impact-to-spec path. Return named records with conclusions, specNumber, impactType. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Complete requested conclusions+impacts paired; optional-path null semantics explicitly retained.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.879'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.conclusions, s.specNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.879'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.conclusions AS conclusions, s.specNumber AS specNumber, imp.impactType AS impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "conclusions",
      "nullable": false,
      "source_column_or_expression": "conclusions",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": true,
      "source_column_or_expression": "specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": true,
      "source_column_or_expression": "impactType",
      "type": "string"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-4-3/14cb0c03546dc5575185955c8cfa23fc82ee149580b2a0a23cf2cb91826dbbdc.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-4-3/14cb0c03546dc5575185955c8cfa23fc82ee149580b2a0a23cf2cb91826dbbdc.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `823ce0e8e20976503b4c673e01324067f6df199384da25a5a2844f0ed7991b86`.

## RAN3_P5_TR-CQ-5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the top 5 TRs by number of spec impacts (highest-impact studies).

**Revised question:** Return top5 TechnicalReport numbers by number of distinct linked TRImpact nodes, ties by TR number ascending; return all if fewer than5 have impacts. Return named records with trNumber, impactCount. Interpret the population and relationships relative to the frozen RAN3 graph.

**Proposed rationale:** Explicit impact-node count rather than distinct target specs, requested counts/roles retained and ties deterministic.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, count(imp) AS cnt ORDER BY cnt DESC, tr.trNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN DISTINCT tr.trNumber AS trNumber, count(DISTINCT imp) AS impactCount ORDER BY impactCount DESC, trNumber ASC LIMIT 5
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "trNumber",
      "type": "string"
    },
    {
      "name": "impactCount",
      "nullable": false,
      "source_column_or_expression": "impactCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "impactCount"
      },
      {
        "direction": "asc",
        "field": "trNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN3_P5_TR-CQ-5-3/ad3765ccf2e88fe94ab363f5c33dff4ee64cfb7cef7cc7225ef6287493e7553a.json), [complete native rows](../reference_outputs/RAN3_P5_TR-CQ-5-3/ad3765ccf2e88fe94ab363f5c33dff4ee64cfb7cef7cc7225ef6287493e7553a.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ad37c4a9498cd54fcdd2760bef58610075667f83c316035195bda9a6faef5992`.
