# RAN5 itemized contract changes

This page accounts for 103 original Core IDs: 81 proposed clarifications and 22 substantive variants.

Each entry retains the exact original and revised question and query. The change rationale is a proposal, not a completed author semantic judgment. Technical check counts concern scorer enforcement and captured reference consistency; all author semantic reviews remain pending.

[Review guide](../REVIEW_GUIDE.md) · [Full technical task ledger](../canonical_tasks.jsonl) · [Per-item scorer checks](../provenance/adversarial_validation.json)

| ID | Proposed change class | Required fields | Native rows | Scorer checks |
| --- | --- | --- | ---: | ---: |
| [RAN5_P1_CQ1-1](#ran5_p1_cq1-1) | Proposed clarification | tdocNumber (string) | 1,427 | 7/7 |
| [RAN5_P1_CQ1-2](#ran5_p1_cq1-2) | Proposed clarification | tdocNumber (string), title (string), documentType (string), company (string) | 1 | 16/16 |
| [RAN5_P1_CQ1-3](#ran5_p1_cq1-3) | Substantive variant | tdocNumber (string), title (string), specNumber (string) | 725 | 13/13 |
| [RAN5_P1_CQ1-4](#ran5_p1_cq1-4) | Proposed clarification | meeting (string), tdocCount (integer) | 5 | 10/10 |
| [RAN5_P1_CQ1-5](#ran5_p1_cq1-5) | Substantive variant | tdocNumber (string) | 1,336 | 7/7 |
| [RAN5_P1_CQ2-1](#ran5_p1_cq2-1) | Proposed clarification | tdocCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ2-2](#ran5_p1_cq2-2) | Proposed clarification | tdocNumber (string) | 6,123 | 7/7 |
| [RAN5_P1_CQ2-3](#ran5_p1_cq2-3) | Proposed clarification | workItemCode (string), tdocCount (integer) | 5 | 10/10 |
| [RAN5_P1_CQ3-1](#ran5_p1_cq3-1) | Proposed clarification | meeting (string), agendaNumber (string), tdocCount (integer) | 10 | 13/13 |
| [RAN5_P1_CQ3-2](#ran5_p1_cq3-2) | Proposed clarification | documentType (string), tdocCount (integer) | 20 | 10/10 |
| [RAN5_P1_CQ3-3](#ran5_p1_cq3-3) | Proposed clarification | company (string), crCount (integer) | 10 | 10/10 |
| [RAN5_P1_CQ4-1](#ran5_p1_cq4-1) | Substantive variant | tdocNumber (string), revisionPath (json) | 335 | 9/9 |
| [RAN5_P1_CQ4-2](#ran5_p1_cq4-2) | Proposed clarification | tdocNumber (string), direction (string), recipients (json) | 529 | 12/12 |
| [RAN5_P1_CQ5-1](#ran5_p1_cq5-1) | Proposed clarification | label (string), nodeCount (integer) | 22 | 10/10 |
| [RAN5_P1_CQ5-2](#ran5_p1_cq5-2) | Proposed clarification | meeting (string), meetingNumber (integer), tdocCount (integer) | 35 | 13/13 |
| [RAN5_P1_CQ5-3](#ran5_p1_cq5-3) | Proposed clarification | withCompany (integer) | 1 | 7/7 |
| [RAN5_P1_CQ5-4](#ran5_p1_cq5-4) | Proposed clarification | release (string), tdocCount (integer) | 11 | 10/10 |
| [RAN5_P1_CQ5-5](#ran5_p1_cq5-5) | Proposed clarification | specNumber (string), crCount (integer) | 10 | 10/10 |
| [RAN5_P1_CQ6-1](#ran5_p1_cq6-1) | Proposed clarification | tdocCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ6-2](#ran5_p1_cq6-2) | Proposed clarification | meetingCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ6-3](#ran5_p1_cq6-3) | Proposed clarification | tdocCount (integer), crCount (integer), crFraction (number) | 1 | 13/13 |
| [RAN5_P1_CQ6-4](#ran5_p1_cq6-4) | Proposed clarification | lsCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ6-5](#ran5_p1_cq6-5) | Proposed clarification | contactCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ7-1](#ran5_p1_cq7-1) | Proposed clarification | agendaCount (integer) | 1 | 7/7 |
| [RAN5_P1_CQ7-2](#ran5_p1_cq7-2) | Proposed clarification | workItemCount (integer) | 1 | 7/7 |
| [RAN5_P2_CQ1-1](#ran5_p2_cq1-1) | Proposed clarification | conclusionId (string), content (string), consensus (boolean) | 9 | 13/13 |
| [RAN5_P2_CQ1-2](#ran5_p2_cq1-2) | Proposed clarification | meeting (string), agendaNumber (string), resolutionCount (integer) | 8,632 | 13/13 |
| [RAN5_P2_CQ1-3](#ran5_p2_cq1-3) | Proposed clarification | release (string), resolutionCount (integer) | 11 | 10/10 |
| [RAN5_P2_CQ1-4](#ran5_p2_cq1-4) | Proposed clarification | specNumber (string), resolutionCount (integer) | 19 | 10/10 |
| [RAN5_P2_CQ1-5](#ran5_p2_cq1-5) | Proposed clarification | workItemCode (string), resolutionCount (integer) | 398 | 10/10 |
| [RAN5_P2_CQ1-6](#ran5_p2_cq1-6) | Proposed clarification | agendaNumber (string), meeting (string), resolutionCount (integer) | 10 | 13/13 |
| [RAN5_P2_CQ2-1](#ran5_p2_cq2-1) | Proposed clarification | tdocNumber (string), resolutionCount (integer) | 7 | 10/10 |
| [RAN5_P2_CQ2-2](#ran5_p2_cq2-2) | Proposed clarification | resolutionId (string), tdocNumbers (json) | 83 | 9/9 |
| [RAN5_P2_CQ2-4](#ran5_p2_cq2-4) | Proposed clarification | tdocNumber (string), specNumbers (json) | 336 | 9/9 |
| [RAN5_P2_CQ3-1](#ran5_p2_cq3-1) | Proposed clarification | company (string), tdocCount (integer) | 10 | 10/10 |
| [RAN5_P2_CQ3-2](#ran5_p2_cq3-2) | Proposed clarification | workItemCode (string), company (string), resolutionCount (integer) | 85 | 13/13 |
| [RAN5_P2_CQ3-3](#ran5_p2_cq3-3) | Substantive variant | specNumber (string), company (string), tdocCount (integer) | 67 | 13/13 |
| [RAN5_P2_CQ6-1](#ran5_p2_cq6-1) | Proposed clarification | meeting (string), meetingNumber (integer), resolutionCount (integer) | 35 | 13/13 |
| [RAN5_P2_CQ6-2](#ran5_p2_cq6-2) | Proposed clarification | meeting (string), meetingNumber (integer), resolutionCount (integer) | 35 | 13/13 |
| [RAN5_P3_CQ1-1](#ran5_p3_cq1-1) | Proposed clarification | sectionId (string), sectionNumber (string), title (string), level (integer) | 24,890 | 16/16 |
| [RAN5_P3_CQ1-10](#ran5_p3_cq1-10) | Proposed clarification | specNumber (string), sectionId (string), tableNumber (string) | 1,863 | 13/13 |
| [RAN5_P3_CQ1-11](#ran5_p3_cq1-11) | Proposed clarification | sectionId (string) | 352 | 7/7 |
| [RAN5_P3_CQ1-12](#ran5_p3_cq1-12) | Substantive variant | parentSectionId (string), sectionId (string) | 3 | 10/10 |
| [RAN5_P3_CQ1-13](#ran5_p3_cq1-13) | Proposed clarification | sectionId (string) | 174 | 7/7 |
| [RAN5_P3_CQ1-14](#ran5_p3_cq1-14) | Proposed clarification | tableCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ1-15](#ran5_p3_cq1-15) | Proposed clarification | sectionId (string) | 931 | 7/7 |
| [RAN5_P3_CQ1-16](#ran5_p3_cq1-16) | Substantive variant | specNumber (string), sectionCount (integer) | 5 | 10/10 |
| [RAN5_P3_CQ1-2](#ran5_p3_cq1-2) | Substantive variant | parentSectionId (string), sectionId (string) | 16 | 10/10 |
| [RAN5_P3_CQ1-4](#ran5_p3_cq1-4) | Proposed clarification | sectionId (string) | 231 | 7/7 |
| [RAN5_P3_CQ1-5](#ran5_p3_cq1-5) | Substantive variant | sectionId (string), tableId (string) | 2 | 10/10 |
| [RAN5_P3_CQ1-6](#ran5_p3_cq1-6) | Substantive variant | sectionId (string), figureId (string) | 20 | 10/10 |
| [RAN5_P3_CQ1-7](#ran5_p3_cq1-7) | Proposed clarification | tableId (string), sectionId (string) | 5,457 | 10/10 |
| [RAN5_P3_CQ1-8](#ran5_p3_cq1-8) | Proposed clarification | tableId (string) | 22,352 | 7/7 |
| [RAN5_P3_CQ1-9](#ran5_p3_cq1-9) | Proposed clarification | sectionId (string), title (string) | 1,945 | 10/10 |
| [RAN5_P3_CQ2-1](#ran5_p3_cq2-1) | Substantive variant | sourceSectionId (string), targetSectionId (string) | 32 | 10/10 |
| [RAN5_P3_CQ2-2](#ran5_p3_cq2-2) | Proposed clarification | sectionId (string), referenceCount (integer) | 10 | 10/10 |
| [RAN5_P3_CQ2-3](#ran5_p3_cq2-3) | Proposed clarification | sectionId (string), referenceCount (integer) | 10 | 10/10 |
| [RAN5_P3_CQ2-4](#ran5_p3_cq2-4) | Proposed clarification | fromSpec (string), toSpec (string), referenceCount (integer) | 4 | 13/13 |
| [RAN5_P3_CQ2-5](#ran5_p3_cq2-5) | Proposed clarification | specNumber (string), referenceCount (integer) | 5 | 10/10 |
| [RAN5_P3_CQ2-6](#ran5_p3_cq2-6) | Proposed clarification | fromSpec (string), toSpec (string), referenceCount (integer) | 10 | 13/13 |
| [RAN5_P3_CQ2-7](#ran5_p3_cq2-7) | Proposed clarification | internalReferenceCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ3-1](#ran5_p3_cq3-1) | Substantive variant | tdocNumber (string), specNumber (string) | 5 | 10/10 |
| [RAN5_P3_CQ3-2](#ran5_p3_cq3-2) | Substantive variant | crCount (integer), sectionCount (integer) | 1 | 10/10 |
| [RAN5_P3_CQ3-3](#ran5_p3_cq3-3) | Proposed clarification | tdocNumber (string) | 4,934 | 7/7 |
| [RAN5_P3_CQ3-4](#ran5_p3_cq3-4) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ3-6](#ran5_p3_cq3-6) | Substantive variant | company (string), specNumber (string), crCount (integer) | 820 | 13/13 |
| [RAN5_P3_CQ4-1](#ran5_p3_cq4-1) | Substantive variant | specNumber (string) | 9 | 7/7 |
| [RAN5_P3_CQ4-2](#ran5_p3_cq4-2) | Proposed clarification | conclusionId (string) | 3 | 7/7 |
| [RAN5_P3_CQ4-3](#ran5_p3_cq4-3) | Substantive variant | meeting (string), specNumber (string) | 1 | 10/10 |
| [RAN5_P3_CQ4-4](#ran5_p3_cq4-4) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ5-1](#ran5_p3_cq5-1) | Proposed clarification | tdocNumber (string) | 4,934 | 7/7 |
| [RAN5_P3_CQ5-2](#ran5_p3_cq5-2) | Substantive variant | company (string), specNumber (string), crCount (integer) | 820 | 13/13 |
| [RAN5_P3_CQ5-3](#ran5_p3_cq5-3) | Substantive variant | release (string), specNumber (string) | 69 | 10/10 |
| [RAN5_P3_CQ5-4](#ran5_p3_cq5-4) | Substantive variant | specNumber (string), crCount (integer) | 5 | 10/10 |
| [RAN5_P3_CQ5-5](#ran5_p3_cq5-5) | Substantive variant | sectionCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ5-6](#ran5_p3_cq5-6) | Substantive variant | tableCount (integer) | 1 | 7/7 |
| [RAN5_P3_CQ5-7](#ran5_p3_cq5-7) | Substantive variant | figureCount (integer) | 1 | 7/7 |
| [RAN5_P3_P3-S8-CQ02](#ran5_p3_p3-s8-cq02) | Proposed clarification | allLinked (boolean) | 1 | 7/7 |
| [RAN5_P3_P3-S8-CQ05](#ran5_p3_p3-s8-cq05) | Proposed clarification | entityClass (string), granularity (string), nodeCount (integer) | 6 | 13/13 |
| [RAN5_P4_CQ2-1](#ran5_p4_cq2-1) | Proposed clarification | specNumber (string) | 1 | 7/7 |
| [RAN5_P4_CQ2-2](#ran5_p4_cq2-2) | Proposed clarification | tdocNumber (string) | 399 | 7/7 |
| [RAN5_P4_CQ2-3](#ran5_p4_cq2-3) | Proposed clarification | tdocNumber (string) | 768 | 7/7 |
| [RAN5_P4_CQ2-4](#ran5_p4_cq2-4) | Proposed clarification | tdocNumber (string), specCount (integer) | 10 | 10/10 |
| [RAN5_P4_CQ3-1](#ran5_p4_cq3-1) | Substantive variant | crPackId (string), tdocNumber (string), summary (string) | 23,262 | 13/13 |
| [RAN5_P4_CQ3-2](#ran5_p4_cq3-2) | Proposed clarification | crPackId (string) | 194 | 7/7 |
| [RAN5_P4_CQ3-3](#ran5_p4_cq3-3) | Proposed clarification | crPackId (string), crCount (integer) | 10 | 10/10 |
| [RAN5_P4_CQ4-1](#ran5_p4_cq4-1) | Proposed clarification | tdocNumber (string), reason (string) | 7 | 10/10 |
| [RAN5_P4_CQ4-2](#ran5_p4_cq4-2) | Proposed clarification | tdocNumber (string), reason (string), summary (string) | 135 | 13/13 |
| [RAN5_P4_CQ4-3](#ran5_p4_cq4-3) | Proposed clarification | sectionId (string) | 6,065 | 7/7 |
| [RAN5_P4_CQ4-4](#ran5_p4_cq4-4) | Proposed clarification | specNumber (string) | 12 | 7/7 |
| [RAN5_P4_CQ4-5](#ran5_p4_cq4-5) | Proposed clarification | tdocNumber (string), summary (string) | 23 | 10/10 |
| [RAN5_P5_CQ1-1](#ran5_p5_cq1-1) | Proposed clarification | trNumber (string), status (string) | 3 | 10/10 |
| [RAN5_P5_CQ1-4](#ran5_p5_cq1-4) | Proposed clarification | trNumber (string) | 3 | 7/7 |
| [RAN5_P5_CQ2-1](#ran5_p5_cq2-1) | Proposed clarification | specNumber (string), impactType (string) | 5 | 10/10 |
| [RAN5_P5_CQ2-2](#ran5_p5_cq2-2) | Proposed clarification | impactType (string), description (string) | 3 | 10/10 |
| [RAN5_P5_CQ2-3](#ran5_p5_cq2-3) | Proposed clarification | trNumber (string) | 2 | 7/7 |
| [RAN5_P5_CQ2-4](#ran5_p5_cq2-4) | Proposed clarification | trNumber (string) | 1 | 7/7 |
| [RAN5_P5_CQ2-5](#ran5_p5_cq2-5) | Proposed clarification | trNumber (string), impactType (string) | 2 | 10/10 |
| [RAN5_P5_CQ3-1](#ran5_p5_cq3-1) | Proposed clarification | trNumber (string), specNumber (string), impactType (string), description (string) | 5 | 16/16 |
| [RAN5_P5_CQ3-2](#ran5_p5_cq3-2) | Proposed clarification | trNumber (string), specNumber (string), impactType (string), description (string) | 3 | 16/16 |
| [RAN5_P5_CQ4-1](#ran5_p5_cq4-1) | Proposed clarification | trNumber (string) | 2 | 7/7 |
| [RAN5_P5_CQ4-2](#ran5_p5_cq4-2) | Proposed clarification | trNumber (string), impactType (string) | 2 | 10/10 |
| [RAN5_P5_CQ4-3](#ran5_p5_cq4-3) | Proposed clarification | trNumber (string), impactType (string) | 1 | 10/10 |

## RAN5_P1_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs presented at meeting RAN5#109 (meeting document survey).

**Revised question:** List every distinct TDoc identifier presented at RAN5#109. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the unrequested ten-document cap; title is not an answer requirement.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ1-1/acb6f72fc87bb0ea46c3dba056b6b6b17a3e68e019a7bf78a4391cd87e6a66a2.json), [complete native rows](../reference_outputs/RAN5_P1_CQ1-1/acb6f72fc87bb0ea46c3dba056b6b6b17a3e68e019a7bf78a4391cd87e6a66a2.jsonl); 1,427 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b279b7533f5d6a2f73b8ff264b78b2f8adfe4ffac36efa999965be50b5a154bb`.

## RAN5_P1_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the details of TDoc R5-255500, including its submitting company (document lookup).

**Revised question:** Give the identifier, title, document type and submitting-company name for R5-255500; use null when an optional property or company is not recorded. Return named records with tdocNumber, title, documentType, company. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Native company is JSON null, not the historical string None; grade all requested roles.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber:'R5-255500'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, t.type, c.companyName
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber:'R5-255500'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, t.type, c.companyName
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocNumber",
      "nullable": false,
      "source_column_or_expression": "t.tdocNumber",
      "type": "string"
    },
    {
      "name": "title",
      "nullable": true,
      "source_column_or_expression": "t.title",
      "type": "string"
    },
    {
      "name": "documentType",
      "nullable": true,
      "source_column_or_expression": "t.type",
      "type": "string"
    },
    {
      "name": "company",
      "nullable": true,
      "source_column_or_expression": "c.companyName",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ1-2/38523ed6a0f26fe057deb62317a28b7eef03c6d92ecc32de4e8d8c6c07214544.json), [complete native rows](../reference_outputs/RAN5_P1_CQ1-2/38523ed6a0f26fe057deb62317a28b7eef03c6d92ecc32de4e8d8c6c07214544.jsonl); 1 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `da34b9929a8feb1c3557ca9defeff075622afbb371c84f6a55036ad48851566f`.

## RAN5_P1_CQ1-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the details of a CR (R5-255xxx) and the spec it modifies (change-request lookup).

**Revised question:** For every CR identifier starting with R5-255, give its title and each recorded modified specification number; use null when no MODIFIES target is recorded. Return named records with tdocNumber, title, specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** R5-255xxx does not identify a single CR. Explicitly adopt the stored prefix population instead of inventing a selected document; remove the five-row cap.

**Original query**

```cypher
MATCH (cr:CR) WHERE cr.tdocNumber STARTS WITH 'R5-255' OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN cr.tdocNumber, cr.title, sp.specNumber ORDER BY cr.tdocNumber, sp.specNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (cr:CR) WHERE cr.tdocNumber STARTS WITH 'R5-255' OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT cr.tdocNumber AS tdocNumber, cr.title AS title, sp.specNumber AS specNumber
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
    },
    {
      "name": "title",
      "nullable": true,
      "source_column_or_expression": "title",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": true,
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ1-3/e6fd03a6908f46b6aedb57f9e1983dfbc452e7d5ac16d931f17af5d0e74cb027.json), [complete native rows](../reference_outputs/RAN5_P1_CQ1-3/e6fd03a6908f46b6aedb57f9e1983dfbc452e7d5ac16d931f17af5d0e74cb027.jsonl); 725 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `ba4e400ad2d71f00a97317f2b4acbba38c42a1185fb76e97081a4ab010266e8c`.

## RAN5_P1_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which five meetings hosted the most TDocs? (activity ranking)

**Revised question:** Return the five recorded meeting-identifier groups with the most distinct presented TDoc nodes and their counts, including zero-count groups. Rank by tdocCount descending, meeting ascending; return fewer only if fewer stored eligible groups exist. Return named records with meeting, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count TDoc nodes rather than joined occurrences; make cutoff ties deterministic. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, meeting ASC LIMIT 5
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
        "field": "meeting"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ1-4/9350c5a6b407f3a30bb9ddd51d705678508c96452a484c49d584b5561e84b102.json), [complete native rows](../reference_outputs/RAN5_P1_CQ1-4/9350c5a6b407f3a30bb9ddd51d705678508c96452a484c49d584b5561e84b102.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `7b419451ffb211ad73b91c93822d4c12cfe69cfc9650385ddd4eaca879c5c74f`.

## RAN5_P1_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Samsung's TDocs, newest first (contributor tracking).

**Revised question:** List all distinct TDoc identifiers submitted to the recorded companyName Samsung, in descending lexicographic tdocNumber order. This ordering is an identifier order, not a verified submission timestamp. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original newest-first query orders identifier strings and caps ten. No chronological timestamp interpretation is certified; expose this as an identifier-order variant.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Samsung'}) RETURN t.tdocNumber ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) RETURN DISTINCT t.tdocNumber AS tdocNumber ORDER BY tdocNumber DESC
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
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tdocNumber"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ1-5/81c8db90ec90bb2ade8ba208fa584fdccfb67674e5771a0b8147942509cb1175.json), [complete native rows](../reference_outputs/RAN5_P1_CQ1-5/81c8db90ec90bb2ade8ba208fa584fdccfb67674e5771a0b8147942509cb1175.jsonl); 1,336 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d5e9fc95058d0c78f778d64cbcdcad6bcee54a7382fdd31681be1e26f657a183`.

## RAN5_P1_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs target Rel-18? (release volume check)

**Revised question:** Count distinct TDoc nodes linked by TARGET_RELEASE to Rel-18. Return named records with tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Make the TDoc count unit explicit and prevent join multiplicity.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}) RETURN count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ2-1/a7a5008320f200c21568abd5611e98fe2c9adbab7ec315fe45057535d439dd1f.json), [complete native rows](../reference_outputs/RAN5_P1_CQ2-1/a7a5008320f200c21568abd5611e98fe2c9adbab7ec315fe45057535d439dd1f.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `643dd9a7a0404cb8394280e7ecbb16e300abcea1099b3611004ed41125cb28a0`.

## RAN5_P1_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that modify TS 38.533 (spec-change tracking).

**Revised question:** List all distinct CR TDoc identifiers linked by MODIFIES to TS 38.533. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the unrequested ten-CR cap; deduplicate stored edition associations.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.533'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ2-2/4d663ad5794d6d2fc5b9ed078dfafe5bb05d2e67bc403d9918c423738c0b01bf.json), [complete native rows](../reference_outputs/RAN5_P1_CQ2-2/4d663ad5794d6d2fc5b9ed078dfafe5bb05d2e67bc403d9918c423738c0b01bf.jsonl); 6,123 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a968cbb34d3a18fa070e0e79bfaa0656cbbea473de70d221572297e0254e948a`.

## RAN5_P1_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which five Work Items have the most TDocs? (work-item activity)

**Revised question:** Return the five recorded Work Item code groups linked to the most distinct TDoc nodes, with counts, including zero-count groups. Rank by tdocCount descending, workItemCode ascending; return fewer only if fewer stored eligible groups exist. Return named records with workItemCode, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Pair each code with its distinct-document count; fix unspecified cutoff ties. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (wi:WorkItem) OPTIONAL MATCH (t:Tdoc)-[:RELATED_TO]->(wi) RETURN wi.workItemCode AS workItemCode, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, workItemCode ASC LIMIT 5
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
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tdocCount"
      },
      {
        "direction": "asc",
        "field": "workItemCode"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ2-3/8d2a8064ccb13469977a2cfb8889bfce6e3b1e92f008c0ec628e5d48ca57ad6f.json), [complete native rows](../reference_outputs/RAN5_P1_CQ2-3/8d2a8064ccb13469977a2cfb8889bfce6e3b1e92f008c0ec628e5d48ca57ad6f.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6c9c4a6e3cebc9ac64418e71259aae5d0b1f194a65a9012ddd1f2914de39fcd5`.

## RAN5_P1_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten agenda items drew the most TDocs? (agenda workload)

**Revised question:** Return the ten recorded meeting-and-agenda-number groups linked to the most distinct TDoc nodes, with counts, including zero-count groups. Rank by tdocCount descending, meeting ascending, agendaNumber ascending; return fewer only if fewer stored eligible groups exist. Return named records with meeting, agendaNumber, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Repeated agenda numbers across meetings were merged. Identify an agenda instance by meeting and agenda number; count distinct TDocs. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) OPTIONAL MATCH (t:Tdoc)-[:BELONGS_TO]->(ai) RETURN ai.meetingNumber AS meeting, ai.agendaNumber AS agendaNumber, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, meeting ASC, agendaNumber ASC LIMIT 10
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
      "name": "agendaNumber",
      "nullable": false,
      "source_column_or_expression": "agendaNumber",
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
        "field": "meeting"
      },
      {
        "direction": "asc",
        "field": "agendaNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ3-1/4e37daf9375ccb5c354d03c73976cc307ec4d77d46ca79e6c4ee20aeff95e270.json), [complete native rows](../reference_outputs/RAN5_P1_CQ3-1/4e37daf9375ccb5c354d03c73976cc307ec4d77d46ca79e6c4ee20aeff95e270.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `0cd63e43a210c1ffc23743b39069a9f1a4e406c9988a199a029fd738aabda473`.

## RAN5_P1_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Break down TDocs by type (document-type distribution).

**Revised question:** Report the complete recorded document-type distribution: each type value and its TDoc-node count. A missing type is null. Return named records with documentType, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Distribution requires the type/count pair and all groups; remove the unrequested cap.

**Original query**

```cypher
MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc) RETURN t.type AS documentType, count(t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "documentType",
      "nullable": true,
      "source_column_or_expression": "documentType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ3-2/4da041f8b4741365c0c39b9d43507de25582c805440cf6b06f7b43986839adef.json), [complete native rows](../reference_outputs/RAN5_P1_CQ3-2/4da041f8b4741365c0c39b9d43507de25582c805440cf6b06f7b43986839adef.jsonl); 20 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b828d1dea19d8b80ebca711ed025fcc6c05fd9187a8d35fe846c90d9c063b17c`.

## RAN5_P1_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten companies submitted the most CRs? (contribution ranking)

**Revised question:** Return the ten recorded company-name groups submitting the most distinct CR nodes, with counts, including zero-count groups. Rank by crCount descending, company ascending; return fewer only if fewer stored eligible groups exist. Return named records with company, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Define unique CR counting and deterministic ties; company attribution is a stored link, not independent organizational validation. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Company) OPTIONAL MATCH (cr:CR)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS company, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, company ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
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
        "field": "company"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ3-3/c96027f5f148a4a46fe71fd0b5942fdf669322d0b10ec182e7725be34907fb8e.json), [complete native rows](../reference_outputs/RAN5_P1_CQ3-3/c96027f5f148a4a46fe71fd0b5942fdf669322d0b10ec182e7725be34907fb8e.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `fdcf0692c79543d998255b6de78987f40ea16ab1b4c18531ca951d71a4f6cc0d`.

## RAN5_P1_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Trace the revision chain of a TDoc (R5-255xxx) (revision-lineage tracing).

**Revised question:** For every TDoc identifier starting with R5-255, return every stored IS_REVISION_OF path ending at a TDoc with no recorded TDoc predecessor. Each revisionPath is an ordered list from the starting document to its terminal predecessor. This reports stored terminal paths, not a certified complete historical revision chain. Return named records with tdocNumber, revisionPath. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original collects an unordered ancestor bag, uses an arbitrary three-hop bound and selects five prefix rows. An explicit terminal-path variant preserves lineage evidence without claiming one complete real-world chain. Source replay must stop on resource limits rather than silently truncate.

**Original query**

```cypher
MATCH (t:Tdoc)-[:IS_REVISION_OF*1..3]->(prev:Tdoc) WHERE t.tdocNumber STARTS WITH 'R5-255' RETURN t.tdocNumber, collect(prev.tdocNumber) AS chain ORDER BY t.tdocNumber LIMIT 5
```

**Revised query**

```cypher
MATCH p=(t:Tdoc)-[:IS_REVISION_OF*1..]->(prev:Tdoc) WHERE t.tdocNumber STARTS WITH 'R5-255' AND NOT EXISTS { MATCH (prev)-[:IS_REVISION_OF]->(:Tdoc) } RETURN DISTINCT t.tdocNumber AS tdocNumber, [n IN nodes(p) | n.tdocNumber] AS revisionPath
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
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "revisionPath",
      "nested_array_semantics": {
        "$": "sequence"
      },
      "nullable": false,
      "source_column_or_expression": "revisionPath",
      "type": "json"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ4-1/9f2ff132442d34fc8ab2eb2c1c0de4d6c4c2ff885116dcbdeceb7e93805a3b00.json), [complete native rows](../reference_outputs/RAN5_P1_CQ4-1/9f2ff132442d34fc8ab2eb2c1c0de4d6c4c2ff885116dcbdeceb7e93805a3b00.jsonl); 335 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `e3b925eb7285a652ff0a012c5ba8d2621f8a6308e38753eca30f74b5a683cf88`.

## RAN5_P1_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** For each liaison statement (LS), show its direction and recipient working groups (LS routing analysis).

**Revised question:** For every stored LS identifier and direction, list the distinct SENT_TO working-group names. Use an empty recipient array when none is recorded and null for a missing direction. Return named records with tdocNumber, direction, recipients. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the five-LS cap, preserve direction and recipient roles, and define recipient set semantics. Empty recorded recipients do not imply real-world routing absence.

**Original query**

```cypher
MATCH (ls:LS) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo ORDER BY ls.tdocNumber, ls.direction LIMIT 5
```

**Revised query**

```cypher
MATCH (ls:LS) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber AS tdocNumber, ls.direction AS direction, collect(DISTINCT wg.wgName) AS recipients
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
    },
    {
      "name": "direction",
      "nullable": true,
      "source_column_or_expression": "direction",
      "type": "string"
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "recipients",
      "nested_array_semantics": {
        "$": "set"
      },
      "nullable": false,
      "source_column_or_expression": "recipients",
      "type": "json"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ4-2/c54237db117030a7a9f7e522e68bf86fe86453ad2a1562cc03dcf678805e2911.json), [complete native rows](../reference_outputs/RAN5_P1_CQ4-2/c54237db117030a7a9f7e522e68bf86fe86453ad2a1562cc03dcf678805e2911.jsonl); 529 native rows retained. The retained per-item check record has 12 passing scorer checks for this definition.

**Definition SHA-256:** `0c862a60b226d9fb357ae25211ac9daee238f63fc1fe7f46c0dd9087817d0b5b`.

## RAN5_P1_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Report node counts by label across the graph (dataset overview).

**Revised question:** Report each observed node label and the number of nodes carrying it; a node carrying multiple labels contributes once to each applicable label. Return named records with label, nodeCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Native count is integer; label memberships are not a partition of unique nodes.

**Original query**

```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```

**Revised query**

```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "label",
      "nullable": false,
      "source_column_or_expression": "label",
      "type": "string"
    },
    {
      "name": "nodeCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.json), [complete native rows](../reference_outputs/RAN5_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.jsonl); 22 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `55a652060c325adf2d796e3ff73c1efaf5fc926278a5080252052a398da7044c`.

## RAN5_P1_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show TDoc counts per meeting, most recent first (coverage check).

**Revised question:** For every stored meeting, show its number of distinct presented TDoc nodes, including zero. Order by meetingNumberInt descending, then canonical meeting identifier ascending; this is stored meeting-number order. Return named records with meeting, meetingNumber, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the five-meeting cap, retain zero meetings, define chronological proxy and total ordering.

**Original query**

```cypher
MATCH (m:Meeting) WITH m OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m, count(t) AS tdocs RETURN m.canonicalMeetingNumber, tdocs ORDER BY m.meetingNumberInt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT t) AS tdocCount ORDER BY meetingNumber DESC, meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ5-2/2517476d85167840e33d697c641f890924a166bddaa6c41ccb4b8b1132757c87.json), [complete native rows](../reference_outputs/RAN5_P1_CQ5-2/2517476d85167840e33d697c641f890924a166bddaa6c41ccb4b8b1132757c87.jsonl); 35 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `2278ff6bf32de24e0bbf3fc18db79ecf3adaa89e7457c49b7e013f41596d9470`.

## RAN5_P1_CQ5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs have a submitting company recorded? (attribution coverage)

**Revised question:** Count distinct TDoc nodes with at least one recorded SUBMITTED_BY link to a Company node. Return named records with withCompany. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original count(c) counts company-link occurrences and count(t) is inflated by the optional join. Count each TDoc once; do not relabel the old count as corrected gold.

**Original query**

```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
```

**Revised query**

```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(DISTINCT CASE WHEN c IS NOT NULL THEN t END) AS withCompany
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "withCompany",
      "nullable": false,
      "source_column_or_expression": "withCompany",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ5-3/58d3bd9b2b693f3791fe66e4260a21167528b274c019dc198881e0e3bdec511f.json), [complete native rows](../reference_outputs/RAN5_P1_CQ5-3/58d3bd9b2b693f3791fe66e4260a21167528b274c019dc198881e0e3bdec511f.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d5752c7b80ac3e0f9dfbab918e98a2a6f0ee569ab02460af7882a3feb2bf7fc2`.

## RAN5_P1_CQ5-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Break down TDocs by target release (release distribution).

**Revised question:** For every target release reached by a TDoc, show the count of distinct linked TDoc nodes; a document targeting multiple releases contributes once to each linked release. Return named records with release, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Return all release/count pairs; remove cap and explicit join-count inflation.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName AS release, count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "release",
      "nullable": false,
      "source_column_or_expression": "release",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ5-4/0c68849b5e55ff9e15c1d62cd3090dd0b0492fecc1dc7ee9a0975b18ee668175.json), [complete native rows](../reference_outputs/RAN5_P1_CQ5-4/0c68849b5e55ff9e15c1d62cd3090dd0b0492fecc1dc7ee9a0975b18ee668175.jsonl); 11 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `a2e3ab8cfbe3df7f3f6964824f250ee28766e2c7a3423559426f266a025954f9`.

## RAN5_P1_CQ5-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten specs receive the most CRs? (spec churn ranking)

**Revised question:** Return the ten recorded specification-number groups receiving the most distinct CR nodes via MODIFIES, with counts, including zero-count groups. Rank by crCount descending, specNumber ascending; return fewer only if fewer stored eligible groups exist. Return named records with specNumber, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count a CR once per specification number across stored editions and fix cutoff ties. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) RETURN sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 10
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
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ5-5/e99de94fbd0c50a0b8375827bee591b271b2439cf401f3ba5b8d81a460265a96.json), [complete native rows](../reference_outputs/RAN5_P1_CQ5-5/e99de94fbd0c50a0b8375827bee591b271b2439cf401f3ba5b8d81a460265a96.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `184854df2139f1d54ec0f35b2e8983d71bb8f475e1cce8adbae1ec8ea68f0d32`.

## RAN5_P1_CQ6-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs were presented at meeting RAN5#109? (meeting volume)

**Revised question:** Count distinct TDoc nodes presented at canonical meeting RAN5#109. Return named records with tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Use distinct document nodes, not joined presentation occurrences.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN count(t) AS cnt
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN count(DISTINCT t) AS tdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ6-1/3dbbf441cd0076cedd8eec71c3090265dd24c0e8f9c6a377c70af257fc6418ef.json), [complete native rows](../reference_outputs/RAN5_P1_CQ6-1/3dbbf441cd0076cedd8eec71c3090265dd24c0e8f9c6a377c70af257fc6418ef.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `21c6287fff0a23cef81c3546c0bf1c84dacc2475186842c4b6458c15cea39079`.

## RAN5_P1_CQ6-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many meetings are in the dataset? (corpus size)

**Revised question:** Count Meeting nodes in the stored graph. Return named records with meetingCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve exact count query; map native integer cnt to a named count field.

**Original query**

```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```

**Revised query**

```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.json), [complete native rows](../reference_outputs/RAN5_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `80cf1b2f9917b76e822c7b74ca640c74ba478d0cc23f86c5eb07449ccac1ac5c`.

## RAN5_P1_CQ6-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Compare the total TDoc count against the CR count (CR proportion).

**Revised question:** Report total TDoc-node count, total CR-node count, and CR fraction crCount/tdocCount. Use null for the fraction if there are no TDoc nodes. Return named records with tdocCount, crCount, crFraction. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** The original comparison returns two counts but no proportion. Explicitly require both counts and the defined ratio, including zero-denominator policy.

**Original query**

```cypher
MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
```

**Revised query**

```cypher
MATCH (t:Tdoc) WITH count(t) AS tdocCount MATCH (cr:CR) WITH tdocCount, count(cr) AS crCount RETURN tdocCount, crCount, CASE WHEN tdocCount=0 THEN null ELSE 1.0*crCount/tdocCount END AS crFraction
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "tdocCount",
      "nullable": false,
      "source_column_or_expression": "tdocCount",
      "type": "integer"
    },
    {
      "name": "crCount",
      "nullable": false,
      "source_column_or_expression": "crCount",
      "type": "integer"
    },
    {
      "name": "crFraction",
      "nullable": true,
      "source_column_or_expression": "crFraction",
      "type": "number"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ6-3/12dace2f88adc9c9c91d579725c52339066af631a85f3b8ab1e8b391a96e2b3d.json), [complete native rows](../reference_outputs/RAN5_P1_CQ6-3/12dace2f88adc9c9c91d579725c52339066af631a85f3b8ab1e8b391a96e2b3d.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `dde71d2d822412d729a46c102361547409cd9aff0c226d1e0c5dbb6669e1f990`.

## RAN5_P1_CQ6-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many liaison statements (LS) are recorded? (LS count)

**Revised question:** Count LS nodes in the stored graph. Return named records with lsCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original single-label aggregate; map its native integer to the requested node-count role.

**Original query**

```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```

**Revised query**

```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "lsCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.json), [complete native rows](../reference_outputs/RAN5_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0aded54db72e43da18e617ecde43f19fd787ff2ce2de768a83a1cbf36a4a64e8`.

## RAN5_P1_CQ6-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many Contact nodes exist? (contact count)

**Revised question:** Count Contact nodes in the stored graph. Return named records with contactCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original single-label aggregate; map its native integer to the requested node-count role.

**Original query**

```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```

**Revised query**

```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "contactCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.json), [complete native rows](../reference_outputs/RAN5_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7b020a3f47e32de9d686e2eb6f1e2ad5bfb689700b4a1ccddf3b4d46bb3fa50f`.

## RAN5_P1_CQ7-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many agenda items are recorded? (agenda count)

**Revised question:** Count AgendaItem nodes in the stored graph. Return named records with agendaCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original single-label aggregate; map its native integer to the requested node-count role.

**Original query**

```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agendaCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.json), [complete native rows](../reference_outputs/RAN5_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8ee66b0126e8fc6bef9cca13e7b34c9f25e91a5363c914cf3ac709dbb424b042`.

## RAN5_P1_CQ7-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many Work Items are recorded? (work-item count)

**Revised question:** Count WorkItem nodes in the stored graph. Return named records with workItemCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original single-label aggregate; map its native integer to the requested node-count role.

**Original query**

```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```

**Revised query**

```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workItemCount",
      "nullable": false,
      "source_column_or_expression": "cnt",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.json), [complete native rows](../reference_outputs/RAN5_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `aa149c25ccb0698ea9daae8ee50c2bb79179a841773c86fa3acf43f1d562af36`.

## RAN5_P2_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions reached at meeting RAN5#81 (meeting-outcome review).

**Revised question:** List all Conclusion identifiers, their recorded content and consensus flags at RAN5#81; null denotes an unrecorded property. Return named records with conclusionId, content, consensus. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the unrequested cap and preserve the native Boolean instead of serialized text.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN5#81'}) RETURN c.resolutionId AS id, c.content AS content, c.hasConsensus AS consensus ORDER BY c.sequence LIMIT 10
```

**Revised query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#81'}) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content, c.hasConsensus AS consensus
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
      "nullable": true,
      "source_column_or_expression": "content",
      "type": "string"
    },
    {
      "name": "consensus",
      "nullable": true,
      "source_column_or_expression": "consensus",
      "type": "boolean"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-1/3a62dde859d732480ab17ce7162958d5d85e5a6528672ae9a1a4706cda2e7479.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-1/3a62dde859d732480ab17ce7162958d5d85e5a6528672ae9a1a4706cda2e7479.jsonl); 9 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b6549327b93c3937b65cccf4b7199147069e8eefcd0b9f467e10929af7779924`.

## RAN5_P2_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the number of resolutions per agenda item (agenda-outcome breakdown).

**Revised question:** For every stored meeting-and-agenda-number instance, count distinct Resolution nodes linked by RESOLUTION_BELONGS_TO, including zero. Return named records with meeting, agendaNumber, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original merges repeated agenda numbers across meetings and caps groups. Count per meeting/agenda instance and retain zero outcomes.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, count(r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN agenda, cnt
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) RETURN ai.meetingNumber AS meeting, ai.agendaNumber AS agendaNumber, count(DISTINCT r) AS resolutionCount
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-2/b745f12fd11591022d995e706fadf1a7d95eea0b132280e18a82ae463107b7b4.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-2/b745f12fd11591022d995e706fadf1a7d95eea0b132280e18a82ae463107b7b4.jsonl); 8,632 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `f3cbe67aff4d44415b7ae773694e1428aef1581cf53a937224573ebb60e383e6`.

## RAN5_P2_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many resolutions relate to each release? (release-outcome breakdown)

**Revised question:** For each recorded releaseName starting with Rel-, count distinct Resolution nodes reaching it through REFERENCES/TARGET_RELEASE; include zero. Return named records with release, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove group cap and define every release, zero coverage, and distinct Resolution counting.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release) WHERE rel.releaseName STARTS WITH 'Rel-' WITH rel.releaseName AS release, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN release, cnt
```

**Revised query**

```cypher
MATCH (rel:Release) WHERE rel.releaseName STARTS WITH 'Rel-' OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:TARGET_RELEASE]->(rel) RETURN rel.releaseName AS release, count(DISTINCT r) AS resolutionCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "release",
      "nullable": false,
      "source_column_or_expression": "release",
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-3/1937ac1daac300c409a7117d98c76a9487faf6b62d494cb7682f4e499a6848ac.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-3/1937ac1daac300c409a7117d98c76a9487faf6b62d494cb7682f4e499a6848ac.jsonl); 11 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5bf0a1b13446db33778555e17d6d824afdf384b0c01250175bc9eb0f655ee2b9`.

## RAN5_P2_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many resolutions touch each modified spec? (spec-outcome breakdown)

**Revised question:** For each specification number reached by a Resolution through REFERENCES/MODIFIES, count distinct reaching Resolution nodes. Return named records with specNumber, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Return all reached specification/count pairs. Reachability is an association and does not prove causal decision impact.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH s.specNumber AS spec, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN spec, cnt
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:MODIFIES]->(s:Spec) RETURN s.specNumber AS specNumber, count(DISTINCT r) AS resolutionCount
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
      "name": "resolutionCount",
      "nullable": false,
      "source_column_or_expression": "resolutionCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-4/d09690556af96a17acf6535741fe716974c52291ab31bb433d5f36c125966de1.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-4/d09690556af96a17acf6535741fe716974c52291ab31bb433d5f36c125966de1.jsonl); 19 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f07c5bae9849e9d9736015f42be375aefa42e80ac8bdce9bea317dc994385826`.

## RAN5_P2_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many resolutions relate to each Work Item? (work-item outcome breakdown)

**Revised question:** For every Work Item code in the graph, count distinct Resolution nodes reaching it through REFERENCES/RELATED_TO; include zero. Return named records with workItemCode, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove group cap, preserve complete Work Item population and count each Resolution once.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) WITH wi.workItemCode AS wi_id, count(DISTINCT r) AS cnt ORDER BY cnt DESC, wi_id LIMIT 10 RETURN wi_id, cnt
```

**Revised query**

```cypher
MATCH (wi:WorkItem) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:RELATED_TO]->(wi) RETURN wi.workItemCode AS workItemCode, count(DISTINCT r) AS resolutionCount
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
      "name": "resolutionCount",
      "nullable": false,
      "source_column_or_expression": "resolutionCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-5/09000588b765b5f2e76a3bb1d7d0b2db6287eb1c4deb6c04aa785e09734f1fcf.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-5/09000588b765b5f2e76a3bb1d7d0b2db6287eb1c4deb6c04aa785e09734f1fcf.jsonl); 398 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e55ff791fad555b261fbfbe9bc6a8dd12a5d9e4b7e78e8be2d3855772e0481d5`.

## RAN5_P2_CQ1-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten agenda items yielded the most resolutions? (busiest-agenda ranking)

**Revised question:** Return the ten recorded meeting-and-agenda-number groups linked to the most distinct Resolution nodes, with counts, including zero-count groups. Rank by resolutionCount descending, agendaNumber ascending, meeting ascending; return fewer only if fewer stored eligible groups exist. Return named records with agendaNumber, meeting, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original agenda/meeting identity and tie ordering; fix distinct count units and pair all roles. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, ai.meetingNumber AS meeting, count(r) AS cnt ORDER BY cnt DESC, agenda, meeting LIMIT 10 RETURN agenda, meeting, cnt
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) RETURN ai.agendaNumber AS agendaNumber, ai.meetingNumber AS meeting, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC, agendaNumber ASC, meeting ASC LIMIT 10
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
      },
      {
        "direction": "asc",
        "field": "meeting"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ1-6/798cfdcc224ed2360f867578f7ef76eb071aa420020284141e748aa1857d023a.json), [complete native rows](../reference_outputs/RAN5_P2_CQ1-6/798cfdcc224ed2360f867578f7ef76eb071aa420020284141e748aa1857d023a.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `6edaf0288adb9c6c26f28e664d257ecca01e00e8881c385ba391394583082ed9`.

## RAN5_P2_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TDocs are referenced by two or more resolutions? (frequently-cited documents)

**Revised question:** List all TDoc identifiers referenced by at least two distinct Resolution nodes, together with their distinct Resolution counts. Return named records with tdocNumber, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove unrequested cap and require identifier/count pairing; repeated joins do not qualify as independent resolutions.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t.tdocNumber AS tdoc, count(r) AS ref_count WHERE ref_count >= 2 RETURN tdoc, ref_count ORDER BY ref_count DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t.tdocNumber AS tdocNumber, count(DISTINCT r) AS resolutionCount WHERE resolutionCount>=2 RETURN tdocNumber, resolutionCount
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
    },
    {
      "name": "resolutionCount",
      "nullable": false,
      "source_column_or_expression": "resolutionCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ2-1/6bf6cbae13975c91ab6bc36c27eea3ae6a4299b22ba6a7dfe5e33bb6a8c8c32e.json), [complete native rows](../reference_outputs/RAN5_P2_CQ2-1/6bf6cbae13975c91ab6bc36c27eea3ae6a4299b22ba6a7dfe5e33bb6a8c8c32e.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5f74481c50044bae7eabc69b770b8e86f3cfe278c6aa81bfd50bf1437e7db074`.

## RAN5_P2_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** For each resolution, list the TDocs it references (resolution-to-document mapping).

**Revised question:** For every Resolution identifier, list the complete set of distinct referenced TDoc identifiers; return an empty array if none is recorded. Return named records with resolutionId, tdocNumbers. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original top-ten and first-five samples do not implement each/list. Preserve all resolutions and all referenced document identifiers.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r.resolutionId AS rid, collect(t.tdocNumber) AS tdocs, count(t) AS cnt ORDER BY cnt DESC, rid LIMIT 10 RETURN rid, cnt, tdocs[..5] AS sample_tdocs
```

**Revised query**

```cypher
MATCH (r:Resolution) OPTIONAL MATCH (r)-[:REFERENCES]->(t:Tdoc) RETURN r.resolutionId AS resolutionId, collect(DISTINCT t.tdocNumber) AS tdocNumbers
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
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "tdocNumbers",
      "nested_array_semantics": {
        "$": "set"
      },
      "nullable": false,
      "source_column_or_expression": "tdocNumbers",
      "type": "json"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ2-2/81bf83a73268c12f2da15f1956af6770541c45867ad8f3282bb7f39cea321e7b.json), [complete native rows](../reference_outputs/RAN5_P2_CQ2-2/81bf83a73268c12f2da15f1956af6770541c45867ad8f3282bb7f39cea321e7b.jsonl); 83 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `2ecc79af044b6696de22b452e69d7dad3644bea50c8fe1922e0004961fc7c30d`.

## RAN5_P2_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs does each referenced TDoc end up modifying? (document-to-spec impact)

**Revised question:** For every TDoc referenced by a Resolution, list the complete set of distinct specification numbers it reaches through MODIFIES; return an empty array when none is recorded. Return named records with tdocNumber, specNumbers. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove top-ten and five-spec samples; include referenced TDocs lacking a recorded MODIFIES target. Do not equate node count with distinct specification-number count.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH t.tdocNumber AS tdoc, collect(DISTINCT s.specNumber) AS specs, count(DISTINCT s) AS spec_count ORDER BY spec_count DESC, tdoc LIMIT 10 RETURN tdoc, spec_count, specs[..5] AS sample_specs
```

**Revised query**

```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc) WITH DISTINCT t OPTIONAL MATCH (t)-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber AS tdocNumber, collect(DISTINCT s.specNumber) AS specNumbers
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
    },
    {
      "json_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      },
      "name": "specNumbers",
      "nested_array_semantics": {
        "$": "set"
      },
      "nullable": false,
      "source_column_or_expression": "specNumbers",
      "type": "json"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ2-4/d1c6567717f206d762872c7dd82dfd9c9d3dac7a26e87e78af7011299546ca96.json), [complete native rows](../reference_outputs/RAN5_P2_CQ2-4/d1c6567717f206d762872c7dd82dfd9c9d3dac7a26e87e78af7011299546ca96.jsonl); 336 native rows retained. The retained per-item check record has 9 passing scorer checks for this definition.

**Definition SHA-256:** `fad3267759f0bf3444c4fb2d6efc6cf00fdd787b1dbf73b434f9057cd3e84cba`.

## RAN5_P2_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten companies submitted the most resolution-referenced TDocs? (influence ranking)

**Revised question:** Return the ten recorded company-name groups submitting the most distinct Resolution-referenced TDoc nodes, with TDoc counts, including zero-count groups. Rank by tdocCount descending, company ascending; return fewer only if fewer stored eligible groups exist. Return named records with company, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original query counts Resolution nodes although the question asks for TDocs; change the counted entity, not just the column label. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WITH c.companyName AS company, count(DISTINCT r) AS resolution_count ORDER BY resolution_count DESC, company LIMIT 10 RETURN company, resolution_count
```

**Revised query**

```cypher
MATCH (c:Company) OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS company, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, company ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
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
        "field": "company"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ3-1/0946622bda42d999411576761c467bf679d14590ef97037e69d0d3c690ec0716.json), [complete native rows](../reference_outputs/RAN5_P2_CQ3-1/0946622bda42d999411576761c467bf679d14590ef97037e69d0d3c690ec0716.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `74b87ae6f202505a0e459ea84649dd6e272b8f6e8cd287fe9a5e6bf414768418`.

## RAN5_P2_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show each company's resolution contributions per Work Item (technology contribution breakdown).

**Revised question:** For each reached company/Work Item pair, count distinct Resolution nodes referencing a TDoc submitted by that company and linked to that Work Item. Return named records with workItemCode, company, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Complete matrix requires all reached pairs and their distinct resolution counts, not ten global rows. Stored paths define association, not independent authorship of outcomes.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) MATCH (t)-[:SUBMITTED_BY]->(c:Company) WITH wi.workItemCode AS wi_id, c.companyName AS company, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN wi_id, company, cnt
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (t)-[:SUBMITTED_BY]->(c:Company) RETURN wi.workItemCode AS workItemCode, c.companyName AS company, count(DISTINCT r) AS resolutionCount
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
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ3-2/cc6a556f0e685e3030ed91c98f83d6e8d80f86e0a68560b351e5d1627151b9b3.json), [complete native rows](../reference_outputs/RAN5_P2_CQ3-2/cc6a556f0e685e3030ed91c98f83d6e8d80f86e0a68560b351e5d1627151b9b3.jsonl); 85 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `02c8c48c41718a7d58e60071b02f57fdbdc1de997683bb5b1d67a619b299d137`.

## RAN5_P2_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Rank the main contributors to each spec's resolutions (spec contributor ranking).

**Revised question:** For each reached specification number, rank company-name groups having at least one matching Resolution-referenced submitted TDoc for that specification by the number of distinct Resolution-referenced TDoc nodes they submitted that modify that specification. Within a specification order by TDoc count descending and company name ascending; order specification groups by specNumber ascending. Return named records with specNumber, company, tdocCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Main contributor has no validated single metric. Define the stored TDoc-count metric and full within-spec ranking as a variant instead of presenting ten global rows as per-spec leaders. The candidate explicitly ranks matching company-name groups rather than promising zero-contribution companies for every specification.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (t)-[:SUBMITTED_BY]->(c:Company) WITH s.specNumber AS spec, c.companyName AS company, count(DISTINCT t) AS tdoc_count ORDER BY tdoc_count DESC LIMIT 10 RETURN spec, company, tdoc_count
```

**Revised query**

```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec), (t)-[:SUBMITTED_BY]->(c:Company) RETURN s.specNumber AS specNumber, c.companyName AS company, count(DISTINCT t) AS tdocCount ORDER BY specNumber ASC, tdocCount DESC, company ASC
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
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
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
        "direction": "asc",
        "field": "specNumber"
      },
      {
        "direction": "desc",
        "field": "tdocCount"
      },
      {
        "direction": "asc",
        "field": "company"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ3-3/4d0a87d8b832983020a48d43601a5ee67ebf80a4171794c83dc89ee7ced64f7c.json), [complete native rows](../reference_outputs/RAN5_P2_CQ3-3/4d0a87d8b832983020a48d43601a5ee67ebf80a4171794c83dc89ee7ced64f7c.jsonl); 67 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `924bbb24fcacf34f20024c6f7f90fbf88b688a2dcb36f0791931e0b68bfb507d`.

## RAN5_P2_CQ6-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Track resolution counts across meetings over time (resolution trend).

**Revised question:** For every stored meeting, report its distinct Resolution count, including zero. Order by meetingNumberInt ascending and canonical identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original omits zero-resolution meetings; define complete series and deterministic meeting-number order.

**Original query**

```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(r) AS cnt ORDER BY num ASC RETURN meeting, cnt
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ6-1/4986278ff854149f6c194337b8c87df4bedb12b3a9c6575e01394d357820986f.json), [complete native rows](../reference_outputs/RAN5_P2_CQ6-1/4986278ff854149f6c194337b8c87df4bedb12b3a9c6575e01394d357820986f.jsonl); 35 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `e704394c1f783d10835002edb0896d124c4ad23769838f352dc6901a78148c0c`.

## RAN5_P2_CQ6-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Track Samsung's resolution contributions across meetings over time (contribution trend).

**Revised question:** For every stored meeting, count distinct Resolution nodes referencing at least one TDoc submitted by the recorded companyName Samsung; include zero and order by meetingNumberInt ascending, then canonical identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original sparse series omits other meetings; use an optional full path so zero meetings remain and each resolution contributes once.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(DISTINCT r) AS cnt ORDER BY num ASC RETURN meeting, cnt
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (m)<-[:MADE_AT]-(r:Resolution)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P2_CQ6-2/76e29fd5b7e773d2678eaf7f79eea070c4ee455a763837ea4f22f0dda7dc1014.json), [complete native rows](../reference_outputs/RAN5_P2_CQ6-2/76e29fd5b7e773d2678eaf7f79eea070c4ee455a763837ea4f22f0dda7dc1014.jsonl); 35 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `4e45246ab3df1b61a9a2be73f1b673e44ab54d37e472746ba7af15789c40991c`.

## RAN5_P3_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections of TS 38.533 (structure browsing).

**Revised question:** List all Section identifiers, stored numbers, titles and stored level values belonging to every recorded edition of TS 38.533. Return named records with sectionId, sectionNumber, title, level. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the unrequested 25-section cap; identifiers distinguish releases, and stored level is not certified against normative outline text.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
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
      "nullable": true,
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-1/a60e2d232dd3da583a38de994a1ed8632ef4180471090432541f9da0a0ffecb5.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-1/a60e2d232dd3da583a38de994a1ed8632ef4180471090432541f9da0a0ffecb5.jsonl); 24,890 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `e7f9b4efa3594b820bcb3b1815081c737ebb50022cc049ca85d687f0636f8335`.

## RAN5_P3_CQ1-10

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Locate the spec and section for tables numbered 6.2.x (table-number lookup).

**Revised question:** For every stored TSTable whose tableNumber starts with 6.2., locate its containing Section and specification number through CONTAINS_TABLE/BELONGS_TO_SPEC. Return table number, edition-qualified section identifier and specification number. Return named records with specNumber, sectionId, tableNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve the full original specification population and table-number predicate. Use the dot boundary for 6.2.x, remove the ten-row cap and require all requested location roles.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable) WHERE t.tableNumber STARTS WITH '6.2' RETURN sp.specNumber, sec.sectionId, t.tableNumber, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable) WHERE t.tableNumber STARTS WITH '6.2.' RETURN DISTINCT sp.specNumber AS specNumber, sec.sectionId AS sectionId, t.tableNumber AS tableNumber
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
    },
    {
      "name": "tableNumber",
      "nullable": false,
      "source_column_or_expression": "tableNumber",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-10/60f4a1a456ee66a0506f9c094d81091c14599a7058f82366290cbf6fbee7965f.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-10/60f4a1a456ee66a0506f9c094d81091c14599a7058f82366290cbf6fbee7965f.jsonl); 1,863 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `b80c9ca5aa1102cc2e354582935efa94093c8aa3787c346d7e02d910a2ad3412`.

## RAN5_P3_CQ1-11

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-2 sections of TS 38.521-2 (second-level outline).

**Revised question:** List all Section identifiers with stored level=2 belonging to recorded TS 38.521-2 editions. Return named records with sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the 25-row cap and grade requested section identities; stored level is the explicit predicate.

**Original query**

```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-2'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {level:2})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-2'}) RETURN DISTINCT s.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-11/f8bc0381950fe03f69ab78190f3b8b3c498bbe664c16281a46406f0ad38f1840.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-11/f8bc0381950fe03f69ab78190f3b8b3c498bbe664c16281a46406f0ad38f1840.jsonl); 352 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8417e5e263c3060031753fd479a36f93ecc6e4860e4b1e657bcb4dc5aab1a1a7`.

## RAN5_P3_CQ1-12

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the subsections under section 7 of TS 38.523-1 (drilling into a clause).

**Revised question:** List every direct HAS_SUB_SECTION target of sectionNumber 7 in each recorded TS 38.523-1 edition; pair parent and child section identifiers. Return named records with parentSectionId, sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original silently chooses one latest-release parent and caps children. Preserve every edition and define direct versus recursive subsections. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.523-1'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'7'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber:'7'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.523-1'}), (sec)-[:HAS_SUB_SECTION]->(sub:Section) RETURN DISTINCT sec.sectionId AS parentSectionId, sub.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "parentSectionId",
      "nullable": false,
      "source_column_or_expression": "parentSectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-12/ce1cb4c11e0795e91bf8d8e8908d78bd001c5ed987353a0b7bc245c9b3ba9289.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-12/ce1cb4c11e0795e91bf8d8e8908d78bd001c5ed987353a0b7bc245c9b3ba9289.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0a64d356d09d3aa6369066c670a5e1c953f5da1d7592f6e4894bc4fd6a811517`.

## RAN5_P3_CQ1-13

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the void sections of TS 38.521-1 (identifying removed clauses).

**Revised question:** List all Section identifiers marked isVoid=true in recorded TS 38.521-1 editions. Return named records with sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Void flag is a stored marker, not a demonstrated historical removal event; remove cap.

**Original query**

```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {isVoid:true})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT s.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-13/1b19199e4c0b4452c1f31ba06fdfca855a6b351e75df099b1e1b3a94f83fd117.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-13/1b19199e4c0b4452c1f31ba06fdfca855a6b351e75df099b1e1b3a94f83fd117.jsonl); 174 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `083d7892c5aeb0c5b124d0616f69a8d4ec9280f403a912d2c2a15d5f2d30bcb7`.

## RAN5_P3_CQ1-14

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many tables does TS 38.533 contain? (table count)

**Revised question:** Count distinct TSTable nodes directly CONTAINS_TABLE-linked from sections of recorded TS 38.533 editions. Return named records with tableCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count distinct directly contained table nodes across recorded editions; do not count repeated joined associations.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN count(t) AS tableCount
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN count(DISTINCT t) AS tableCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-14/1acee4a9ee7fc3d3833a1a836c6c293410042a386f4fb4b703fd1b99019933e0.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-14/1acee4a9ee7fc3d3833a1a836c6c293410042a386f4fb4b703fd1b99019933e0.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `940c25e201535e769f47066527df30281ee9dd432a2b06aa98349d76bd68cad5`.

## RAN5_P3_CQ1-15

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-3 sections of TS 38.533 (deep-outline browsing).

**Revised question:** List all Section identifiers with stored level=3 belonging to recorded TS 38.533 editions. Return named records with sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the 25-row cap; explicit stored-level condition avoids assuming independently verified hierarchy.

**Original query**

```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {level:3})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT s.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-15/55b3bddf20bf7bd74ddeddc9daa92274ea950983448f480bd0ca4d09bbfbb6c4.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-15/55b3bddf20bf7bd74ddeddc9daa92274ea950983448f480bd0ca4d09bbfbb6c4.jsonl); 931 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `82e4d555ec761de23ed1550307ee710d52d0c24b4f48513596b3f3ba39693dd7`.

## RAN5_P3_CQ1-16

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which five RAN5 specs have the most sections? (largest specs)

**Revised question:** Among all recorded specification-number groups starting with 38.5, return the five with the most distinct Section nodes and their counts, including zero-count groups. Rank by sectionCount descending, specNumber ascending; return fewer only if fewer stored eligible groups exist. Return named records with specNumber, sectionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original RAN5 spec ownership is not established by a numeric prefix. Retain the explicit prefix as a limited formal variant; count distinct section nodes and fix ties. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber AS specNumber, count(DISTINCT s) AS sectionCount ORDER BY sectionCount DESC, specNumber ASC LIMIT 5
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
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-16/c00c3e271ad8967d60d9f743a69e84bf34c933c6175d27f1b651a20cd7e796de.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-16/c00c3e271ad8967d60d9f743a69e84bf34c933c6175d27f1b651a20cd7e796de.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `414b705e18581f11e12b5ded887c36be17a6d99e29eb227d550384a5b11e791e`.

## RAN5_P3_CQ1-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the subsections under section 5 of TS 38.533 (drilling into a clause).

**Revised question:** List every direct HAS_SUB_SECTION target of sectionNumber 5 in each recorded TS 38.533 edition; pair parent and child section identifiers. Return named records with parentSectionId, sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove hidden latest-release selection and child cap; do not mix editions or infer transitive descendants. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.533'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'5'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber:'5'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}), (sec)-[:HAS_SUB_SECTION]->(sub:Section) RETURN DISTINCT sec.sectionId AS parentSectionId, sub.sectionId AS sectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "parentSectionId",
      "nullable": false,
      "source_column_or_expression": "parentSectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-2/19401e20877cd5a70b9d7f1f025f942ad03a7b0818b1036b285fe8e1a1660d87.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-2/19401e20877cd5a70b9d7f1f025f942ad03a7b0818b1036b285fe8e1a1660d87.jsonl); 16 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cad834db3e70b8f27b1fe44a1374a31484b43fd4212f00ecdf4438b45e5df3d2`.

## RAN5_P3_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-1 sections of TS 38.533 (top-level outline).

**Revised question:** List Section identifiers with stored level=1 in all recorded TS 38.533 editions. Return named records with sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Exact native replay retains all 231 rows. Grade requested identities; stored level does not certify normative top-level hierarchy.

**Original query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

**Revised query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "s.sectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-4/350c3a1642232688a7777aaeba71653dfe1347f1e337bb79b97b6e079e7f7b3d.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-4/350c3a1642232688a7777aaeba71653dfe1347f1e337bb79b97b6e079e7f7b3d.jsonl); 231 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `f5f5c5e7b3c7eca40fdc3178cf38a874abd0abd2efec49df2b7ee3cd141d3f07`.

## RAN5_P3_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the tables in section 6.2.3 of TS 38.521-1 (table lookup).

**Revised question:** List every TSTable directly contained in sectionNumber 6.2.3 of every recorded TS 38.521-1 edition, with table and containing-section identifiers. Return named records with sectionId, tableId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove latest-release and inventory caps, distinguish edition-qualified identifiers, and restrict to stored direct containment. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.521-1'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'6.2.3'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber:'6.2.3'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT sec.sectionId AS sectionId, t.tableId AS tableId
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
      "name": "tableId",
      "nullable": false,
      "source_column_or_expression": "tableId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-5/dc6e27279d68ca5891d964390579b4f763fb80167a04596145693fdd2298653b.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-5/dc6e27279d68ca5891d964390579b4f763fb80167a04596145693fdd2298653b.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cf7f449eccda215184028f627b3ec67b41bfde21dd19a5db0cc5bcc0c3f10560`.

## RAN5_P3_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the figures in section 5.3.4.1 of TS 38.509 (figure lookup).

**Revised question:** List every TSFigure directly contained in sectionNumber 5.3.4.1 of every recorded TS 38.509 edition, with figure and containing-section identifiers. Return named records with sectionId, figureId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove hidden latest-edition choice and figure cap; preserve direct figure/section mapping. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.509'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'5.3.4.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption ORDER BY f.figureNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber:'5.3.4.1'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.509'}), (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN DISTINCT sec.sectionId AS sectionId, f.figureId AS figureId
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
      "name": "figureId",
      "nullable": false,
      "source_column_or_expression": "figureId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-6/4f016047955728f877cf8d3bf37a701168ecb386972c8dba87b8db17af611b3e.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-6/4f016047955728f877cf8d3bf37a701168ecb386972c8dba87b8db17af611b3e.jsonl); 20 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0d857d6a88fc396e5d1e52fde7085a438f5d28054ed7adfa9b195c0d495f0b7c`.

## RAN5_P3_CQ1-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find which sections contain tables in TS 38.521-1 (table-to-section mapping).

**Revised question:** Report every stored TABLE_IN_SECTION mapping from a TSTable to a Section belonging to a recorded TS 38.521-1 edition. Return named records with tableId, sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove five-row cap and score the requested paired mapping, not an incidental title column.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN t.tableId, sec.sectionId, sec.sectionTitle ORDER BY t.tableNumber, t.tableId LIMIT 5
```

**Revised query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT t.tableId AS tableId, sec.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-7/1ec3e03b1228df97a00a6d812535447b1a2aed820c0c66fcf7e539389cd937e0.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-7/1ec3e03b1228df97a00a6d812535447b1a2aed820c0c66fcf7e539389cd937e0.jsonl); 5,457 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `fe3b247aac7cbd426117e11b595c5281d03c839c42f7fbf36bf598d6b721cd68`.

## RAN5_P3_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all tables in TS 38.523-1 (table inventory).

**Revised question:** List every distinct TSTable identifier contained in sections belonging to recorded TS 38.523-1 editions. Return named records with tableId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** All tables cannot be implemented by a 25-row sample; edition-qualified table identifiers are the inventory answer unit.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.523-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber, t.tableId LIMIT 25
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.523-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-8/e8b7b7b27ddfe5b9bd4f1b94fd17c8e2f3f13eb459bf12a9a4b52fd214cd8e86.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-8/e8b7b7b27ddfe5b9bd4f1b94fd17c8e2f3f13eb459bf12a9a4b52fd214cd8e86.jsonl); 22,352 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `4efb0ed5322f03b8d6d59d51e14cb1ab3b20399c941f538d083134ea18f011fc`.

## RAN5_P3_CQ1-9

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find sections of TS 38.533 whose title contains 'measurement' (topic search).

**Revised question:** List all Section identifiers and titles in recorded TS 38.533 editions whose stored title contains measurement case-insensitively. Return named records with sectionId, title. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove unrequested topic-search cap and make title matching explicit; missing titles do not match.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN DISTINCT s.sectionId AS sectionId, s.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ1-9/ac3736d234b0ca26ff4f4736cceff9742b8b7b20f0881482aa45fe034a0c0b9f.json), [complete native rows](../reference_outputs/RAN5_P3_CQ1-9/ac3736d234b0ca26ff4f4736cceff9742b8b7b20f0881482aa45fe034a0c0b9f.jsonl); 1,945 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `366d368f46575cb33add5c7e73b73e6e0ffe46790ca377222b19336d287bca97`.

## RAN5_P3_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** Which sections does section 6.5D.3.3.5 of TS 38.521-1 reference? (outgoing cross-references)

**Revised question:** For each recorded TS 38.521-1 edition, report every REFERENCES_SECTION target of its sectionNumber 6.5D.3.3.5; pair source and target section identifiers. Return named records with sourceSectionId, targetSectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove hidden latest-edition and 25-row selection; keep direction and edition-qualified source/target roles. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.521-1'})<-[:BELONGS_TO_SPEC]-(a:Section {sectionNumber:'6.5D.3.3.5'}) WHERE rk.specRelease IS NOT NULL WITH a,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a)-[:REFERENCES_SECTION]->(b:Section) RETURN b.sectionId, b.sectionTitle ORDER BY b.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (a:Section {sectionNumber:'6.5D.3.3.5'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}), (a)-[:REFERENCES_SECTION]->(b:Section) RETURN DISTINCT a.sectionId AS sourceSectionId, b.sectionId AS targetSectionId
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sourceSectionId",
      "nullable": false,
      "source_column_or_expression": "sourceSectionId",
      "type": "string"
    },
    {
      "name": "targetSectionId",
      "nullable": false,
      "source_column_or_expression": "targetSectionId",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-1/9b7eb362bab770c7f9332f9dba21796947d53f52f5f155e69676a7c2bb353609.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-1/9b7eb362bab770c7f9332f9dba21796947d53f52f5f155e69676a7c2bb353609.jsonl); 32 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `62116825888056fa64657d48d32e5c05d648ac145a94c2eb79dd2bb14f9957aa`.

## RAN5_P3_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten sections are referenced most often? (most-cited clauses)

**Revised question:** Among all recorded Section-identifier groups, return the ten with the most distinct incoming REFERENCES_SECTION relationship instances, with counts, including zero-count groups. Rank by referenceCount descending, sectionId ascending; return fewer only if fewer stored eligible groups exist. Return named records with sectionId, referenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Specify stored relationship count and deterministic cutoff ties instead of grading section titles. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (b:Section) OPTIONAL MATCH (:Section)-[r:REFERENCES_SECTION]->(b) RETURN b.sectionId AS sectionId, count(DISTINCT r) AS referenceCount ORDER BY referenceCount DESC, sectionId ASC LIMIT 10
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
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-2/1ad9863f5457efd84381f06d08876ce7935896140028621af10e9b212459f6be.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-2/1ad9863f5457efd84381f06d08876ce7935896140028621af10e9b212459f6be.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d25fe2432b3523217c9b4191ab57570796658e5b766ce8fd668a293198c724ac`.

## RAN5_P3_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten sections make the most outgoing references? (heaviest referrers)

**Revised question:** Among all recorded Section-identifier groups, return the ten with the most distinct outgoing REFERENCES_SECTION relationship instances, with counts, including zero-count groups. Rank by referenceCount descending, sectionId ascending; return fewer only if fewer stored eligible groups exist. Return named records with sectionId, referenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original query has explicit count-descending, identifier-ascending ties. Preserve exact query and native projection. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section) OPTIONAL MATCH (a)-[r:REFERENCES_SECTION]->(:Section) RETURN a.sectionId, count(DISTINCT r) AS outCount ORDER BY outCount DESC, a.sectionId ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "sectionId",
      "nullable": false,
      "source_column_or_expression": "a.sectionId",
      "type": "string"
    },
    {
      "name": "referenceCount",
      "nullable": false,
      "source_column_or_expression": "outCount",
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
        "field": "sectionId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-3/c76832825736e9768e1328af5c8f59a9898dbeef92ee800c004f23a760dd8b83.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-3/c76832825736e9768e1328af5c8f59a9898dbeef92ee800c004f23a760dd8b83.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `268c8c00fa92ee0d4963af32e9a2b37767244f5b807efad6b97a6999b094e7a3`.

## RAN5_P3_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which spec-to-spec section-reference pairs are most frequent? (cross-spec coupling)

**Revised question:** Rank every cross-specification-number pair reached by a Section-to-Section REFERENCES_SECTION link, counting distinct directed relationship instances per fromSpec/toSpec pair. Order count descending, then fromSpec and toSpec ascending. Return named records with fromSpec, toSpec, referenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Question supplies no top-k. Remove cap, preserve directed roles and count unique references instead of association-join rows.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[r:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber<>sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT r) AS referenceCount ORDER BY referenceCount DESC, fromSpec ASC, toSpec ASC
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "fromSpec",
      "nullable": false,
      "source_column_or_expression": "fromSpec",
      "type": "string"
    },
    {
      "name": "toSpec",
      "nullable": false,
      "source_column_or_expression": "toSpec",
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
        "field": "fromSpec"
      },
      {
        "direction": "asc",
        "field": "toSpec"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-4/a9afc9b34c806499446a49031efa414a5fb872c8a468bfc2004c03d2eca6fcf9.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-4/a9afc9b34c806499446a49031efa414a5fb872c8a468bfc2004c03d2eca6fcf9.jsonl); 4 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `5b0289fdcf1dc7a74b7ed1965fd73e21ebcad7031b5869fc02fcf570610292c8`.

## RAN5_P3_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which five specs does TS 38.521-1 reference most? (dependency ranking)

**Revised question:** Return the five specification-number groups most referenced by sections of recorded TS 38.521-1 editions via REFERENCES_SPEC, with distinct directed-link counts. Rank by referenceCount descending, specNumber ascending; return fewer only if fewer matching groups exist. Return named records with specNumber, referenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Define count as stored reference edges across all recorded editions and preserve deterministic ties.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC, target.specNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}), (a)-[r:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber AS specNumber, count(DISTINCT r) AS referenceCount ORDER BY referenceCount DESC, specNumber ASC LIMIT 5
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
        "field": "specNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-5/4c6d83a653e26c92b528d093b8c78df724b495a5fa521a504a2f0dad388050ab.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-5/4c6d83a653e26c92b528d093b8c78df724b495a5fa521a504a2f0dad388050ab.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `da193dbc745d98c5e43947d7d81a22b46ba23b52bd743309cab49be8c45504fa`.

## RAN5_P3_CQ2-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten spec-to-spec reference pairs are most frequent? (cross-spec dependencies)

**Revised question:** Return the ten cross-specification-number pairs with the most distinct directed REFERENCES_SPEC links from sections, with counts. Rank by referenceCount descending, fromSpec ascending, toSpec ascending; return fewer only if fewer matching groups exist. Return named records with fromSpec, toSpec, referenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Keep directed pair/count roles and make unspecified cutoff ties deterministic.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[r:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber<>sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT r) AS referenceCount ORDER BY referenceCount DESC, fromSpec ASC, toSpec ASC LIMIT 10
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "fromSpec",
      "nullable": false,
      "source_column_or_expression": "fromSpec",
      "type": "string"
    },
    {
      "name": "toSpec",
      "nullable": false,
      "source_column_or_expression": "toSpec",
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
        "field": "fromSpec"
      },
      {
        "direction": "asc",
        "field": "toSpec"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-6/de690dc933df56b56fad11593d702a0c3a50dd0cd6143e2bc6549cc9ef8b0118.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-6/de690dc933df56b56fad11593d702a0c3a50dd0cd6143e2bc6549cc9ef8b0118.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `980240b581617daa7b4b3f8ab89d3040af891d9d7ec56800e8f4fb405f3b6703`.

## RAN5_P3_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many internal cross-references does TS 38.533 contain? (self-reference density)

**Revised question:** Count distinct directed REFERENCES_SECTION relationships whose source and target belong to the same stored Spec node with specNumber 38.533, across all recorded editions. Return named records with internalReferenceCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Define internal as the same stored edition node and count each relationship once; do not imply a normalized density.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.533'}), (a)-[r:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(DISTINCT r) AS internalReferenceCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "internalReferenceCount",
      "nullable": false,
      "source_column_or_expression": "internalReferenceCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ2-7/d003417ae92a10637d4cc3036155d2ad2b3709a46845fd55bab4d0777511a355.json), [complete native rows](../reference_outputs/RAN5_P3_CQ2-7/d003417ae92a10637d4cc3036155d2ad2b3709a46845fd55bab4d0777511a355.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d129a6dfdffc51b89a759e31146bb0e67f8c1e4f921bb3b4b194f0a27014d3df`.

## RAN5_P3_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which RAN5 specs do recent CRs modify? (change-to-spec mapping)

**Revised question:** Select the five distinct CR identifiers with the lexicographically greatest tdocNumber values among CRs modifying a specification number starting with 38.5. Report every recorded modified specification number with that prefix for each selected CR. Identifier order is not a verified temporal definition of recent. Return named records with tdocNumber, specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Recent and RAN5 ownership are not defined by the original query. Explicitly label lexical-prefix selection as a variant; apply the five-CR bound before expanding every CR/spec pair.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN cr.tdocNumber, sp.specNumber ORDER BY cr.tdocNumber DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' WITH DISTINCT cr ORDER BY cr.tdocNumber DESC LIMIT 5 MATCH (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN DISTINCT cr.tdocNumber AS tdocNumber, sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ3-1/5ce6bb08ba87a44a18b3d77a6caf982d7ee3613db80acab00ea4e34f977cf0c4.json), [complete native rows](../reference_outputs/RAN5_P3_CQ3-1/5ce6bb08ba87a44a18b3d77a6caf982d7ee3613db80acab00ea4e34f977cf0c4.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e827d57338d10e38ae4683bc8f09d8b0f90752dc220cc9311ee1fcce0bd91a00`.

## RAN5_P3_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** For TS 38.521-1, report its CR count alongside its section total (change-and-structure summary).

**Revised question:** For all recorded TS 38.521-1 editions, report the number of distinct CR nodes linked by MODIFIES and distinct Section nodes linked by BELONGS_TO_SPEC. Return named records with crCount, sectionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original combines hub CR count with only one latest-release section count. State common all-recorded-editions scope and avoid multiplying counts. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.521-1'}) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber AS specNumber, crCount, count(s) AS sectionCount
```

**Revised query**

```cypher
OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) WITH count(DISTINCT cr) AS crCount OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}) RETURN crCount, count(DISTINCT s) AS sectionCount
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ3-2/5f9ce770d64d72716161f41ed726a32360be3442b2e76a0848dc340e102dc2b7.json), [complete native rows](../reference_outputs/RAN5_P3_CQ3-2/5f9ce770d64d72716161f41ed726a32360be3442b2e76a0848dc340e102dc2b7.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `45adad3fca054c117da4e7f00509e8562995999902fa47da1c86bed8b3309c5a`.

## RAN5_P3_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that modify TS 38.521-1 (change-request survey).

**Revised question:** List all distinct CR TDoc identifiers linked by MODIFIES to any recorded TS 38.521-1 edition. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the ten-row survey cap and score requested CR identities; duplicate question remains a distinct original ID, not independent task diversity.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ3-3/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.json), [complete native rows](../reference_outputs/RAN5_P3_CQ3-3/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.jsonl); 4,934 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `adb3480ea618bac0c256b563e1c7aa03ff7e0a0e113dad86f8ca6c6298d74687`.

## RAN5_P3_CQ3-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many RAN5 CRs record the clauses they affect? (metadata completeness)

**Revised question:** Count CR nodes in the RAN5 graph whose recorded clausesAffected string is nonempty after trimming whitespace. Return named records with crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Metadata completeness is a CR-property question. Remove the unrequested 38.5 MODIFIES filter and association-count inflation; nonblank metadata does not certify affected-clause parsing.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN count(cr) AS crCount
```

**Revised query**

```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND trim(cr.clausesAffected)<>'' RETURN count(cr) AS crCount
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ3-4/ff6c698b88259c492051e0109730f3a66f5e69d4d7877e8958fed967b98eb837.json), [complete native rows](../reference_outputs/RAN5_P3_CQ3-4/ff6c698b88259c492051e0109730f3a66f5e69d4d7877e8958fed967b98eb837.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e31f3d7a5c42a58846b2c880a900a87cefc75311982cd9b228c7c41caee3909a`.

## RAN5_P3_CQ3-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which RAN5 specs does each company modify via CRs? (company spec impact)

**Revised question:** For every recorded company/specification-number pair with specNumber starting with 38.5, report the number of distinct CR nodes linking that company by SUBMITTED_BY and that specification by MODIFIES. Return named records with company, specNumber, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove global top-ten cap and define complete paired counts. A numeric prefix is an explicit variant population, not certified WG ownership.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN c.companyName, sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN c.companyName AS company, sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
      "type": "string"
    },
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ3-6/865e343cd27d2de09c908f0baba30ced35270e5f1b8b876d8ee49ff7cfc4072c.json), [complete native rows](../reference_outputs/RAN5_P3_CQ3-6/865e343cd27d2de09c908f0baba30ced35270e5f1b8b876d8ee49ff7cfc4072c.jsonl); 820 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `e96eed0c0119c109f132d73e72aa09137f0ae21a2f75269eecb4aa5f10939e96`.

## RAN5_P3_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which RAN5 specs are modified by CRs that conclusions reference? (outcome-to-spec trace)

**Revised question:** List distinct specification numbers reached from a Conclusion through REFERENCES to a CR and MODIFIES to a Spec, restricted to specNumber starting with 38.5. Return named records with specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original path permits non-CR TDocs and caps ten traces. Require the CR label and score requested spec identities; numeric-prefix ownership remains a variant.

**Original query**

```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN res.resolutionId, t.tdocNumber, sp.specNumber ORDER BY res.resolutionId DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (:Conclusion)-[:REFERENCES]->(t:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN DISTINCT sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ4-1/f7a4fca6a808db4c5f32a1be0271636156599a9caeabff83f20170c0b7ad35bc.json), [complete native rows](../reference_outputs/RAN5_P3_CQ4-1/f7a4fca6a808db4c5f32a1be0271636156599a9caeabff83f20170c0b7ad35bc.jsonl); 9 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e095c57f840240719a35548c7dc734278ac0617a873cfbab51ca10879481548c`.

## RAN5_P3_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions that reference CRs modifying TS 38.521-1 (decision provenance).

**Revised question:** List all distinct Conclusion identifiers referencing a CR linked by MODIFIES to recorded TS 38.521-1. Return named records with conclusionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Require CR type instead of arbitrary Tdoc, remove cap and grade requested conclusion identifiers.

**Original query**

```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN res.resolutionId, t.tdocNumber ORDER BY res.resolutionId DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT res.resolutionId AS conclusionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ4-2/c94bff345f653addfeb78305ba40ba7a240d0c055e31ac75203d2021b00a051c.json), [complete native rows](../reference_outputs/RAN5_P3_CQ4-2/c94bff345f653addfeb78305ba40ba7a240d0c055e31ac75203d2021b00a051c.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `99e41b40a9d1477f912cb7b1a054a252f548638a990000d25232c3466275943d`.

## RAN5_P3_CQ4-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Per meeting, which RAN5 specs do approved CRs modify? (meeting-level spec impact)

**Revised question:** Per canonical meeting, list specification numbers starting with 38.5 reached from a Conclusion made at that meeting through REFERENCES to a CR whose stored status is exactly the case-sensitive string approved, then MODIFIES. This status criterion reports a stored field and does not independently establish a 3GPP approval decision. Return named records with meeting, specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original query has no approval-status filter and no CR label. Define an explicit stored-status/prefix variant instead of fabricating approval semantics or claiming conclusion-reference proves approval. Status vocabulary and intended approval meaning still need author semantic review.

**Original query**

```cypher
MATCH (res:Conclusion)-[:MADE_AT]->(m:Meeting), (res)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' WITH m.canonicalMeetingNumber AS meeting, sp.specNumber AS spec, count(DISTINCT t) AS crCount RETURN meeting, spec, crCount ORDER BY crCount DESC, meeting, spec LIMIT 10
```

**Revised query**

```cypher
MATCH (res:Conclusion)-[:MADE_AT]->(m:Meeting), (res)-[:REFERENCES]->(t:CR)-[:MODIFIES]->(sp:Spec) WHERE t.status='approved' AND sp.specNumber STARTS WITH '38.5' RETURN DISTINCT m.canonicalMeetingNumber AS meeting, sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ4-3/4027a079ab23fcb3d2e5bcecc8b74be311bf72391cdaf654e05a1c72fca46694.json), [complete native rows](../reference_outputs/RAN5_P3_CQ4-3/4027a079ab23fcb3d2e5bcecc8b74be311bf72391cdaf654e05a1c72fca46694.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d234346e9cfa2f35abb88685d66b4d61fe2f9c89796619c015cd14bd5bf12dac`.

## RAN5_P3_CQ4-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** How many CRs do conclusions reference? (resolution-to-CR coverage)

**Revised question:** Count distinct CR nodes referenced by at least one Conclusion. Return named records with crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original returns conclusion and CR counts; question requires crCount=135 rather than first resCount=25. Preserve exact query and choose the correct named native column.

**Original query**

```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc:CR) RETURN count(DISTINCT res) AS resCount, count(DISTINCT t) AS crCount
```

**Revised query**

```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc:CR) RETURN count(DISTINCT res) AS resCount, count(DISTINCT t) AS crCount
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ4-4/01a81f812fc24fbf698f2599e622443f0d393f3c99c5b23de2ecca5eae2ff85b.json), [complete native rows](../reference_outputs/RAN5_P3_CQ4-4/01a81f812fc24fbf698f2599e622443f0d393f3c99c5b23de2ecca5eae2ff85b.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `db0acde43925d943208bd5290872da657db3e4dac0ad8e2444777c4a299ff5f3`.

## RAN5_P3_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all CRs changing TS 38.521-1 (comprehensive change survey).

**Revised question:** List all distinct CR TDoc identifiers linked by MODIFIES to any recorded TS 38.521-1 edition. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove the ten-row survey cap and score requested CR identities; duplicate question remains a distinct original ID, not independent task diversity.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-1/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-1/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.jsonl); 4,934 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `d899fce40f60d0c26c1600e6594e9caddaf825194a34e2b49074c20bed5f0f14`.

## RAN5_P3_CQ5-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show each company's CR contributions per RAN5 spec (contribution matrix).

**Revised question:** For every recorded company/specification-number pair with specNumber starting with 38.5, report the number of distinct submitted CR nodes that modify that specification number. Return named records with company, specNumber, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove incomplete ten-row matrix and count distinct CRs. Prefix-only scope is a variant until WG ownership is semantically confirmed.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' WITH c.companyName AS company, sp.specNumber AS spec, count(cr) AS cnt ORDER BY cnt DESC RETURN company, spec, cnt LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN c.companyName AS company, sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "company",
      "nullable": false,
      "source_column_or_expression": "company",
      "type": "string"
    },
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
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-2/865e343cd27d2de09c908f0baba30ced35270e5f1b8b876d8ee49ff7cfc4072c.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-2/865e343cd27d2de09c908f0baba30ced35270e5f1b8b876d8ee49ff7cfc4072c.jsonl); 820 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `df20f2d1de22ec82f8234951ef76ab9f70531b37742a36e4b31cdb6b62ffcbd1`.

## RAN5_P3_CQ5-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which RAN5 specs were changed in each release? (release-level change map)

**Revised question:** List all distinct recorded target-release/specification-number pairs reached from a CR through TARGET_RELEASE and MODIFIES, restricted to specNumber starting with 38.5. Return named records with release, specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove global ten-row sample; preserve requested mapping. A CR target release is a recorded association, not a independently established actual change date or approval.

**Original query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN rel.releaseName, sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN DISTINCT rel.releaseName AS release, sp.specNumber AS specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "release",
      "nullable": false,
      "source_column_or_expression": "release",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-3/f953543ba863947fc967a0a494442ca8d52d90d40c552f68e3c2eec7c2f08d60.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-3/f953543ba863947fc967a0a494442ca8d52d90d40c552f68e3c2eec7c2f08d60.jsonl); 69 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `7f1d4d47a36f114797383cfc99fbad11a124addd3a4fe357e05195d646bfe1c5`.

## RAN5_P3_CQ5-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which five RAN5 specs received the most CRs? (highest-churn specs)

**Revised question:** Among all recorded specification-number groups starting with 38.5, return the five modified by the most distinct CR nodes, with counts, including zero-count groups. Rank by crCount descending, specNumber ascending; return fewer only if fewer stored eligible groups exist. Return named records with specNumber, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Define unique CR unit and cutoff ties; prefix membership does not certify RAN5 specification ownership. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) RETURN sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 5
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
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-4/fe44eb0fffe74760c15665cad0bcee43d37336d174ae5ead5a48c861be76220e.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-4/fe44eb0fffe74760c15665cad0bcee43d37336d174ae5ead5a48c861be76220e.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `3ffb357af6a53296b9dfec47b44e8db49245957f373597ef50f88ffe1db83d10`.

## RAN5_P3_CQ5-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many sections do RAN5 specs contain in total? (corpus size)

**Revised question:** Count distinct Section nodes belonging to recorded Spec nodes whose specNumber starts with 38.5. Return named records with sectionCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Explicit prefix population and stored edition nodes; do not imply certified WG ownership or count joined memberships twice.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(s) AS totalSections
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(DISTINCT s) AS sectionCount
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
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-5/2da4cb16f4ad200a4831139f22aa406da588730ab0ddc3ce71a59c9be3f40ac3.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-5/2da4cb16f4ad200a4831139f22aa406da588730ab0ddc3ce71a59c9be3f40ac3.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `5ec862c8baa70cf94c2a7aa7a52ca602f06261b76682fc5355abed92d1bf9d6a`.

## RAN5_P3_CQ5-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many tables do RAN5 specs contain in total? (table corpus size)

**Revised question:** Count distinct TSTable nodes linked by TABLE_IN_SECTION to sections belonging to recorded Spec nodes whose specNumber starts with 38.5. Return named records with tableCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count table nodes rather than joined containment associations. Prefix-only population is an explicit variant.

**Original query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(t) AS totalTables
```

**Revised query**

```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(DISTINCT t) AS tableCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-6/6a0bfb81e50b98c9c99bfabda92a8f6a64a31c6180f56b48c4cd201d91c3e62e.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-6/6a0bfb81e50b98c9c99bfabda92a8f6a64a31c6180f56b48c4cd201d91c3e62e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `a6ea6029ce51328a3b7b43c7f6f4fb4962d3fa46790e0958a19c5f00824f755a`.

## RAN5_P3_CQ5-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many figures do RAN5 specs contain in total? (figure corpus size)

**Revised question:** Count distinct TSFigure nodes linked by FIGURE_IN_SECTION to sections belonging to recorded Spec nodes whose specNumber starts with 38.5. Return named records with figureCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count figure nodes once across joined memberships; numeric prefix is an explicit variant population.

**Original query**

```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(f) AS totalFigures
```

**Revised query**

```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(DISTINCT f) AS figureCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_CQ5-7/4f2437966271770364f5d1dc877666774be3f3cfadeef50d6ee22917f1e7598b.json), [complete native rows](../reference_outputs/RAN5_P3_CQ5-7/4f2437966271770364f5d1dc877666774be3f3cfadeef50d6ee22917f1e7598b.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0e6ef6935615d258b6e8acfb642f1220b3a6e80e5d3f358f8358ba5e8a6b962a`.

## RAN5_P3_P3-S8-CQ02

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are all item-level entity nodes linked to a section via definedInSection? (link-coverage check)

**Revised question:** Among nodes carrying any of RRCParameter, CapabilityItem, Procedure, PerformanceRequirement or ConformanceTest and having granularity=item, return whether every node has at least one direct definedInSection link to a Section. Return null if this item-node population is empty. Return named records with allLinked. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Question is Boolean, not the class label returned first by the original query. Preserve the five-class population, direct-link predicate and explicit empty-population policy.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

**Revised query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH count(n) AS total, sum(CASE WHEN exists((n)-[:definedInSection]->(:Section)) THEN 1 ELSE 0 END) AS linked RETURN CASE WHEN total=0 THEN null ELSE total=linked END AS allLinked
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "allLinked",
      "nullable": true,
      "source_column_or_expression": "allLinked",
      "type": "boolean"
    }
  ],
  "collection": {
    "kind": "set"
  },
  "cardinality_policy": {
    "extent": "one aggregate record, including zero count for an empty matching population",
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_P3-S8-CQ02/c2f52383112b27941cd02b91433d69f675600ef3d86a36676f3766f646c46ad5.json), [complete native rows](../reference_outputs/RAN5_P3_P3-S8-CQ02/c2f52383112b27941cd02b91433d69f675600ef3d86a36676f3766f646c46ad5.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b2e044c8fb1f5ecc559421fc47de2a1c4f1617236b42516b79326ea14816989b`.

## RAN5_P3_P3-S8-CQ05

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the granularity distribution across the five entity classes (item-level vs legacy section-level).

**Revised question:** For each of RRCParameter, CapabilityItem, Procedure, PerformanceRequirement and ConformanceTest, report all recorded granularity values with node counts. Use null for missing granularity. If a class has no nodes, emit one record with granularity=null and nodeCount=0. Multi-label nodes contribute to each listed class they carry. Return named records with entityClass, granularity, nodeCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original first-label grouping omits absent classes and uses a collision-prone unset string. Define full five-class distribution, null and zero-class semantics.

**Original query**

```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

**Revised query**

```cypher
UNWIND ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'] AS entityClass OPTIONAL MATCH (n) WHERE entityClass IN labels(n) RETURN entityClass, n.granularity AS granularity, count(n) AS nodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "entityClass",
      "nullable": false,
      "source_column_or_expression": "entityClass",
      "type": "string"
    },
    {
      "name": "granularity",
      "nullable": true,
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P3_P3-S8-CQ05/53707b4e885ba0f3953e90e46a3760d9ed831a48cf5e47254f9a28553e767302.json), [complete native rows](../reference_outputs/RAN5_P3_P3-S8-CQ05/53707b4e885ba0f3953e90e46a3760d9ed831a48cf5e47254f9a28553e767302.jsonl); 6 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `803d228b8833ffbeda724e358ab6ba42554a35a9121cee7731fba854c06bb98d`.

## RAN5_P4_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by CR R5-255419 (cross-spec impact).

**Revised question:** List distinct specification numbers reached from CR R5-255419 by recorded AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC links, excluding any specification number that the same CR directly MODIFIES. Return named records with specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Other specification requires excluding directly modified specification numbers; do not treat typed impact flags as proven downstream causal changes.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R5-255419' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (c:CR {tdocNumber:'R5-255419'})-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ2-1/0a532ca9b7deb4a54ac4264938ec55c85aa042d4588e0f13d8f6d95d7061224d.json), [complete native rows](../reference_outputs/RAN5_P4_CQ2-1/0a532ca9b7deb4a54ac4264938ec55c85aa042d4588e0f13d8f6d95d7061224d.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8fb27849d4d477580dd480fd05ccdd934d099ad6b8c2193d5013a8cd312a5a46`.

## RAN5_P4_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which CRs modifying TS 38.521-1 also affect other specs? (ripple-effect screening)

**Revised question:** List all distinct CR TDoc identifiers modifying TS 38.521-1 and linked by one of the three recorded AFFECTS_*_SPEC relations to a specification number other than 38.521-1. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original existence check accepts any target, including the same specification, and caps ten documents. Define other and return all identities.

**Original query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.521-1'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.521-1' } RETURN DISTINCT c.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ2-2/682c9f535c927b44c92021d9ef23d339f0ce15a565a6f5648aca8c43e39d9311.json), [complete native rows](../reference_outputs/RAN5_P4_CQ2-2/682c9f535c927b44c92021d9ef23d339f0ce15a565a6f5648aca8c43e39d9311.jsonl); 399 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1731e3f99968a4e7f39df46a8a44f218c241d6418b10915f411e7071f4510b5e`.

## RAN5_P4_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that flag TS 38.533 as an affected spec (incoming impact).

**Revised question:** List all distinct CR TDoc identifiers flagging TS 38.533 through any recorded AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC relationship. Return named records with tdocNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove cap and grade incoming flagged CR identities, not incidental change-summary text.

**Original query**

```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ2-3/a8ce5ffb23cc024b4f191d5ec0c0ea46ea17bc7e8aaf3572201751d478e7e41e.json), [complete native rows](../reference_outputs/RAN5_P4_CQ2-3/a8ce5ffb23cc024b4f191d5ec0c0ea46ea17bc7e8aaf3572201751d478e7e41e.jsonl); 768 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `99f5eb7eee706b1c64f62dce0e3bec2443a3faefb71fad7a76c5292b73b9bbf0`.

## RAN5_P4_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which ten CRs affect the most other specs? (broadest-impact ranking)

**Revised question:** Among all recorded CR TDoc-identifier groups, return the ten linked by AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC to the most distinct specification numbers other than their directly MODIFIES specification numbers, with those distinct-spec counts, including zero-count groups. Rank by specCount descending, tdocNumber ascending; return fewer only if fewer stored eligible groups exist. Return named records with tdocNumber, specCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original ranks relation instances rather than other specifications. Deduplicate by target spec number and exclude MODIFIES primary targets. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
```

**Revised query**

```cypher
MATCH (c:CR) OPTIONAL MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN c.tdocNumber AS tdocNumber, count(DISTINCT s.specNumber) AS specCount ORDER BY specCount DESC, tdocNumber ASC LIMIT 10
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
    },
    {
      "name": "specCount",
      "nullable": false,
      "source_column_or_expression": "specCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "specCount"
      },
      {
        "direction": "asc",
        "field": "tdocNumber"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ2-4/e4f341e61ea8b70801e04eade075acf6a331b0fd2a7fefdcf52d7a50507114f5.json), [complete native rows](../reference_outputs/RAN5_P4_CQ2-4/e4f341e61ea8b70801e04eade075acf6a331b0fd2a7fefdcf52d7a50507114f5.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c91df3d6cad96673051610cfcb3ff735c794b60ead0e543c60a83de3ef9de49e`.

## RAN5_P4_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs in a CR pack with their change summaries (pack contents).

**Revised question:** For every stored CRPack, list each CR reached by HAS_CR and its recorded change summary; use null when summary is missing. Return named records with crPackId, tdocNumber, summary. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** No single pack is identified by the original. Define the all-pack mapping as a variant, remove the arbitrary global ten-row sample, and preserve the native null summary.

**Original query**

```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(c:CR) WITH pack, c ORDER BY c.tdocNumber LIMIT 10 RETURN pack.crPackId AS crPackId, c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary
```

**Revised query**

```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(c:CR) RETURN DISTINCT pack.crPackId AS crPackId, c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary
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
    },
    {
      "name": "tdocNumber",
      "nullable": false,
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
    "extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ3-1/b10a951ce7acf86e96b32a896dcf295a8e32d5d6e8086205da52f39055840e8d.json), [complete native rows](../reference_outputs/RAN5_P4_CQ3-1/b10a951ce7acf86e96b32a896dcf295a8e32d5d6e8086205da52f39055840e8d.jsonl); 23,262 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `80047658fc2998b97c482a3d88fe6a2aa7bf469852753440cca10aa726544d1c`.

## RAN5_P4_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which CR packs contain CRs for the 5GS_NR_LTE-UEConTest work items? (work-item pack lookup)

**Revised question:** List all CRPack identifiers containing a CR linked by RELATED_TO to a WorkItem whose recorded workItemCode contains the substring 5GS_NR_LTE-UEConTest. Return named records with crPackId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Make the original code-family substring scope explicit and remove cap. tsgMeeting is not declared on CRPack and not requested; never infer it from pack IDs.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC, pack.crPackId LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ3-2/380d216f0ea43beee57850bb0a8c168f16f90c8b120e76b1a8cdf08d9a6f7f38.json), [complete native rows](../reference_outputs/RAN5_P4_CQ3-2/380d216f0ea43beee57850bb0a8c168f16f90c8b120e76b1a8cdf08d9a6f7f38.jsonl); 194 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8d3602cfc73880b73bb9517dd526c570df3e72b7abfada7d6a3bd6f771e786ba`.

## RAN5_P4_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the ten largest CR packs by CR count (pack overview).

**Revised question:** Among all recorded CRPack-identifier groups, return the ten containing the most distinct CR nodes via HAS_CR, with counts, including zero-count groups. Rank by crCount descending, crPackId ascending; return fewer only if fewer stored eligible groups exist. Return named records with crPackId, crCount. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Count distinct CR nodes and make tied pack cutoff deterministic. Start from the complete stored eligible base population and OPTIONAL MATCH counted links, so zero-count groups remain eligible for top-k and short-population cardinality.

**Original query**

```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) RETURN pack.crPackId AS crPackId, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack) OPTIONAL MATCH (pack)-[:HAS_CR]->(cr:CR) RETURN pack.crPackId AS crPackId, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, crPackId ASC LIMIT 10
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
        "field": "crPackId"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "apply the stated descending count and ascending identifier keys; retain exactly min(k,population)",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ3-3/83bcedcf946787e7e721601f4b22a47d17a7152c508fc0f5d2e3dade623037c6.json), [complete native rows](../reference_outputs/RAN5_P4_CQ3-3/83bcedcf946787e7e721601f4b22a47d17a7152c508fc0f5d2e3dade623037c6.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ea2946e8026a36890a5dd0992374d54460c16fde9cd0025c94556236d4b67b19`.

## RAN5_P4_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Give the change reasons of CRs modifying section 6.2 of TS 38.521-1 (clause-level rationale).

**Revised question:** For every distinct CR linked by MODIFIES_SECTION to sectionNumber 6.2 in any recorded TS 38.521-1 edition, give its TDoc identifier and recorded reasonForChange; use null when missing. Return named records with tdocNumber, reason. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Remove cap and edition-sensitive duplicate rows, require document/reason pairing, and retain missing-value semantics.

**Original query**

```cypher
MATCH (sec:Section {sectionNumber: '6.2'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber:'6.2'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}), (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.reasonForChange AS reason
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ4-1/2dc633130fcbbf61febad7cd462ea363c2dd05603f8b6d21614f07d40a97c40e.json), [complete native rows](../reference_outputs/RAN5_P4_CQ4-1/2dc633130fcbbf61febad7cd462ea363c2dd05603f8b6d21614f07d40a97c40e.jsonl); 7 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `76ff5f7b5054b8ed4a45bc7f15b1931123ab64dd4af908bff19b7dd34e3e7320`.

## RAN5_P4_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** For CRs referenced by a conclusion, give their change reason and summary (decision-linked rationale).

**Revised question:** For every distinct CR referenced by a Conclusion, return its TDoc identifier, recorded reasonForChange and summaryOfChange; use null for each missing property. Return named records with tdocNumber, reason, summary. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original drops CRs with missing reasons and samples five. Every decision-linked CR must remain with explicit nulls and both requested text roles.

**Original query**

```cypher
MATCH (con:Conclusion)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
```

**Revised query**

```cypher
MATCH (:Conclusion)-[:REFERENCES]->(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ4-2/0dd497f777999b1a12692abcb7015ba4d4ab972bf476deb3780d4808f15320ac.json), [complete native rows](../reference_outputs/RAN5_P4_CQ4-2/0dd497f777999b1a12692abcb7015ba4d4ab972bf476deb3780d4808f15320ac.jsonl); 135 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `1a3e8e4512419753e92ee22f25f4dbe56e7d0e617cd7bcbead48d3fa77c7345a`.

## RAN5_P4_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which sections do the 5GS_NR_LTE-UEConTest CRs modify? (work-item clause impact)

**Revised question:** List all distinct Section identifiers modified by CRs linked to WorkItem codes containing the substring 5GS_NR_LTE-UEConTest. Return named records with sectionId. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve explicit original work-item code-family predicate and remove the ten-section cap.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ4-3/c555702c57e6e28d25477da9232edaaa2639f035eb84a934f1a84f452e7b1ae5.json), [complete native rows](../reference_outputs/RAN5_P4_CQ4-3/c555702c57e6e28d25477da9232edaaa2639f035eb84a934f1a84f452e7b1ae5.jsonl); 6,065 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `55f18631f7f14767930da9115770b0f84e5ecbdf707b009385cdde8ab9070899`.

## RAN5_P4_CQ4-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which other specs do Samsung's CRs affect? (company cross-spec impact)

**Revised question:** List distinct specification numbers reached by recorded AFFECTS_*_SPEC links from CRs whose submitting companyName contains Samsung, excluding specification numbers directly MODIFIES-linked from that CR. Return named records with specNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve original substring company population as an explicit string criterion; do not invent alias consolidation. Define other targets and remove cap.

**Original query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ4-4/dc3462fc9379f53ac5de256654d761c662150f7cd759a2299e2456435ad301f9.json), [complete native rows](../reference_outputs/RAN5_P4_CQ4-4/dc3462fc9379f53ac5de256654d761c662150f7cd759a2299e2456435ad301f9.jsonl); 12 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `03b57fc3fe9740161f414d58e28af7cf37d1f06155d055787fb204141e8b1f96`.

## RAN5_P4_CQ4-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the change summaries of CRs referenced by conclusions at meeting #87 (meeting-level change review).

**Revised question:** For every distinct CR referenced by a Conclusion made at canonical meeting RAN5#87, give its TDoc identifier and recorded summaryOfChange; null denotes a missing summary. Return named records with tdocNumber, summary. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original allows arbitrary TDocs, drops missing summaries and caps ten. Require CR label, canonical meeting scope and nullable complete summaries.

**Original query**

```cypher
MATCH (con:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 87}) WITH con MATCH (con)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (con:Conclusion)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#87'}), (con)-[:REFERENCES]->(t:CR) RETURN DISTINCT t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P4_CQ4-5/7937dad1d87e5ffb0d98bf6706354811f85c3cb41ae1c673bb9c54ce17c89b28.json), [complete native rows](../reference_outputs/RAN5_P4_CQ4-5/7937dad1d87e5ffb0d98bf6706354811f85c3cb41ae1c673bb9c54ce17c89b28.jsonl); 23 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c43d3933c15607fa1f0fc36484088dbca46ed2d083883be17d22731d868d76de`.

## RAN5_P5_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List all RAN5 technical reports with their status (TR inventory).

**Revised question:** List all TechnicalReport identifiers and their recorded status in the RAN5 graph; null denotes unrecorded status. Return named records with trNumber, status. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve exact full inventory; status and report identity are requested, title is incidental.

**Original query**

```cypher
MATCH (tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, tr.trStatus ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, tr.trStatus ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "status",
      "nullable": true,
      "source_column_or_expression": "tr.trStatus",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ1-1/fc2d937cbb29f65571708e5e41d79ff88f88705d99ea6ab8d2e83a30bb01a813.json), [complete native rows](../reference_outputs/RAN5_P5_CQ1-1/fc2d937cbb29f65571708e5e41d79ff88f88705d99ea6ab8d2e83a30bb01a813.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `079050f763a2562a8a20b279f69cc01472fcd527751234770a5f884f72f43340`.

## RAN5_P5_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List the technical reports marked Completed (finished-study survey).

**Revised question:** List all TechnicalReport identifiers whose recorded trStatus is exactly Completed. Return named records with trNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve exact property-filter query and requested identifiers; do not infer completion beyond the recorded value.

**Original query**

```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ1-4/060ccbf0750db090ec85893a28e62ba6fb05e0508693f59d4bbb57558a91fed3.json), [complete native rows](../reference_outputs/RAN5_P5_CQ1-4/060ccbf0750db090ec85893a28e62ba6fb05e0508693f59d4bbb57558a91fed3.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b203c53dedfdab3f0769b9e5302227ed7d8180a68766b56bcce036e90269ac6d`.

## RAN5_P5_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs did TR 38.903 impact, and how? (study-to-spec impact)

**Revised question:** For TR 38.903, report each specification number reached through HAS_TR_IMPACT/IMPACTS_SPEC and the recorded impactType. Return named records with specNumber, impactType. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** How requires the impact-type role paired with specification number; recorded TRImpact does not prove causal change.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ2-1/d781790d97e8496c5464c60ed7370f3ec1fa469b2da95d85c7fe9342c902962d.json), [complete native rows](../reference_outputs/RAN5_P5_CQ2-1/d781790d97e8496c5464c60ed7370f3ec1fa469b2da95d85c7fe9342c902962d.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `d0c9cc93ca834f611449b64ecf13c1da18606b708e979f1ca8887c0e4d3b9cec`.

## RAN5_P5_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the impact types and descriptions for TR 38.905 (impact classification).

**Revised question:** For every HAS_TR_IMPACT record of TR 38.905, return its recorded impact type and description. Return named records with impactType, description. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Both type and description are requested; preserve exact native full rows instead of scoring only repeated ExtendSection labels.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ2-2/e540e1c7ab39eafa9aa89b1da8ff70b33ba87a5fd2eb6061316bb2c5fb44cb44.json), [complete native rows](../reference_outputs/RAN5_P5_CQ2-2/e540e1c7ab39eafa9aa89b1da8ff70b33ba87a5fd2eb6061316bb2c5fb44cb44.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `71d545cc6995cc23a0a6db172b25efcc6655c78e850fb1c646414a1f148cb072`.

## RAN5_P5_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs impacted specs by extending sections? (ExtendSection impact filter)

**Revised question:** List TechnicalReport identifiers with a HAS_TR_IMPACT record whose impactType is ExtendSection and which has an IMPACTS_SPEC target. Return named records with trNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Original checks the type but not the promised specification target. Require the stored IMPACTS_SPEC link and grade identities.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(:TRImpact {impactType:'ExtendSection'})-[:IMPACTS_SPEC]->(:Spec) RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ2-3/f9e82a9f70e81bf75de1732d15cf2462feec280b1d9e801d4f0870cfb39ea53a.json), [complete native rows](../reference_outputs/RAN5_P5_CQ2-3/f9e82a9f70e81bf75de1732d15cf2462feec280b1d9e801d4f0870cfb39ea53a.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `78266d223aed4c8d9fe74df6e1d4bba49b80304142fa8833ec2867829659529b`.

## RAN5_P5_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List the study-only TRs marked NoChange (no-spec-change studies).

**Revised question:** List TechnicalReport identifiers with a HAS_TR_IMPACT record whose recorded impactType is NoChange. This is an annotation filter, not an independently established absence of all specification changes. Return named records with trNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve exact NoChange predicate; remove unverified study-only/no-real-world-change interpretation through explicit recorded-field wording.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NoChange'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NoChange'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ2-4/7c3bea509e4967906a5ac8c594e71db002bb942e3681dbb555eda4521b14a782.json), [complete native rows](../reference_outputs/RAN5_P5_CQ2-4/7c3bea509e4967906a5ac8c594e71db002bb942e3681dbb555eda4521b14a782.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `507f99bdabdc5aef6140dfc925038739883306f9a1cbc7e09131d5b17d59430b`.

## RAN5_P5_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs impacted TS 38.521-1, and how? (incoming study impact)

**Revised question:** For TS 38.521-1, list each TechnicalReport identifier reaching it through HAS_TR_IMPACT/IMPACTS_SPEC and its recorded impactType. Return named records with trNumber, impactType. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Require report/type pairs, retain exact native projection, and interpret impact solely as a recorded annotation. Duplicate original IDs are preserved without counting them as independent diversity.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ2-5/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.json), [complete native rows](../reference_outputs/RAN5_P5_CQ2-5/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `eb25d68f6c33ea46e2ebbfe82b11f5f11ab7917e35827cef9efcc894900cf945`.

## RAN5_P5_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Detail how TR 38.903 impacted each spec (full impact breakdown).

**Revised question:** For every recorded HAS_TR_IMPACT/IMPACTS_SPEC path from TR 38.903, return the report identifier, target specification number, impact type and impact description. Return named records with trNumber, specNumber, impactType, description. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Full breakdown requires all named roles in one record, not just report IDs. Preserve exact native rows and descriptive annotations without independently certified historical causality.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ3-1/498157cad7ad5f192a4e61fefc39886a3b474d95d43e0495039e54bf0ba8f808.json), [complete native rows](../reference_outputs/RAN5_P5_CQ3-1/498157cad7ad5f192a4e61fefc39886a3b474d95d43e0495039e54bf0ba8f808.jsonl); 5 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `183a82f59b85d2d3b50827bf1bf3dd0d7c3c9cee2ceb66e9db7daae8b7d01da4`.

## RAN5_P5_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Detail how TR 38.905 impacted each spec (full impact breakdown).

**Revised question:** For every recorded HAS_TR_IMPACT/IMPACTS_SPEC path from TR 38.905, return the report identifier, target specification number, impact type and impact description. Return named records with trNumber, specNumber, impactType, description. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Full breakdown requires all named roles in one record, not just report IDs. Preserve exact native rows and descriptive annotations without independently certified historical causality.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "specNumber",
      "nullable": false,
      "source_column_or_expression": "s.specNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
      "type": "string"
    },
    {
      "name": "description",
      "nullable": true,
      "source_column_or_expression": "imp.impactDescription",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ3-2/c025d077b9c3782ed6216e36655df4e18db0e770de1aed99efd4e40c29412f4b.json), [complete native rows](../reference_outputs/RAN5_P5_CQ3-2/c025d077b9c3782ed6216e36655df4e18db0e770de1aed99efd4e40c29412f4b.jsonl); 3 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `d7c5fc558ad3cb0803cd89a074c6b67e94d02640ff3540530cb02096d0e832ff`.

## RAN5_P5_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs targeting Rel-19 (release-scoped studies).

**Revised question:** List all TechnicalReport identifiers linked by TARGET_RELEASE to the recorded releaseName Rel-19. Return named records with trNumber. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Preserve exact query and recorded release association; do not infer approval or delivery dates.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ4-1/4cf6c1f98f4d3d153b28f4e586e1f4f6a5a97b3df7fca341eea44acefe52dcec.json), [complete native rows](../reference_outputs/RAN5_P5_CQ4-1/4cf6c1f98f4d3d153b28f4e586e1f4f6a5a97b3df7fca341eea44acefe52dcec.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1d68a6af9220c66a67fb198d9c73c5bfb3ac49912bf0300efd085a6c9ab2cf7a`.

## RAN5_P5_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs impacted TS 38.521-1, with impact type? (spec-impact lookup)

**Revised question:** For TS 38.521-1, list each TechnicalReport identifier reaching it through HAS_TR_IMPACT/IMPACTS_SPEC and its recorded impactType. Return named records with trNumber, impactType. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Require report/type pairs, retain exact native projection, and interpret impact solely as a recorded annotation. Duplicate original IDs are preserved without counting them as independent diversity.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ4-2/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.json), [complete native rows](../reference_outputs/RAN5_P5_CQ4-2/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.jsonl); 2 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `384bcef55ca320c97deca18c4b2c2222c8bd634e4b86b6dcd733ae9ebcaed3b8`.

## RAN5_P5_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query unchanged. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs impacted TS 38.533, with impact type? (spec-impact lookup)

**Revised question:** For TS 38.533, list each TechnicalReport identifier reaching it through HAS_TR_IMPACT/IMPACTS_SPEC and its recorded impactType. Return named records with trNumber, impactType. Interpret records, absence, and relationships relative to the frozen RAN5 graph.

**Proposed rationale:** Require report/type pairs, retain exact native projection, and interpret impact solely as a recorded annotation. Duplicate original IDs are preserved without counting them as independent diversity.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.533'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.533'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "trNumber",
      "nullable": false,
      "source_column_or_expression": "tr.trNumber",
      "type": "string"
    },
    {
      "name": "impactType",
      "nullable": false,
      "source_column_or_expression": "imp.impactType",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN5_P5_CQ4-3/2dadcacdf2f7086d982ae7d11e58e6248b6be29d87d91ac2c31dd7e21cf7399a.json), [complete native rows](../reference_outputs/RAN5_P5_CQ4-3/2dadcacdf2f7086d982ae7d11e58e6248b6be29d87d91ac2c31dd7e21cf7399a.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f00bc57e7022c2a32f14ff319e1eee28b1fe27f2b722ae4b746afa881f565963`.
