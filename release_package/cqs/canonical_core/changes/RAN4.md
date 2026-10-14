# RAN4 itemized contract changes

This page accounts for 107 original Core IDs: 83 proposed clarifications and 24 substantive variants.

Each entry retains the exact original and revised question and query. The change rationale is a proposal, not a completed author semantic judgment. Technical check counts concern scorer enforcement and captured reference consistency; all author semantic reviews remain pending.

[Review guide](../REVIEW_GUIDE.md) · [Full technical task ledger](../canonical_tasks.jsonl) · [Per-item scorer checks](../provenance/adversarial_validation.json)

| ID | Proposed change class | Required fields | Native rows | Scorer checks |
| --- | --- | --- | ---: | ---: |
| [RAN4_P1_CQ1-1](#ran4_p1_cq1-1) | Proposed clarification | tdocNumber (string) | 3,089 | 7/7 |
| [RAN4_P1_CQ1-2](#ran4_p1_cq1-2) | Proposed clarification | tdocNumber (string), title (string), type (string), companyName (string) | 1 | 16/16 |
| [RAN4_P1_CQ1-3](#ran4_p1_cq1-3) | Proposed clarification | crTdoc (string), title (string), specNumber (string) | 1 | 13/13 |
| [RAN4_P1_CQ1-4](#ran4_p1_cq1-4) | Proposed clarification | meeting (string), tdocCount (integer) | 5 | 10/10 |
| [RAN4_P1_CQ1-5](#ran4_p1_cq1-5) | Proposed clarification | tdocNumber (string) | 27,710 | 7/7 |
| [RAN4_P1_CQ2-1](#ran4_p1_cq2-1) | Proposed clarification | tdocCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ2-2](#ran4_p1_cq2-2) | Proposed clarification | crTdoc (string) | 7,427 | 7/7 |
| [RAN4_P1_CQ2-3](#ran4_p1_cq2-3) | Proposed clarification | workItemCode (string), tdocCount (integer) | 1 | 10/10 |
| [RAN4_P1_CQ3-1](#ran4_p1_cq3-1) | Proposed clarification | agendaNumber (string), tdocCount (integer) | 6,539 | 10/10 |
| [RAN4_P1_CQ3-2](#ran4_p1_cq3-2) | Proposed clarification | type (string), tdocCount (integer) | 19 | 10/10 |
| [RAN4_P1_CQ3-3](#ran4_p1_cq3-3) | Proposed clarification | companyName (string), crCount (integer) | 10 | 10/10 |
| [RAN4_P1_CQ4-2](#ran4_p1_cq4-2) | Proposed clarification | direction (string), recipient (string) | 1 | 10/10 |
| [RAN4_P1_CQ5-1](#ran4_p1_cq5-1) | Proposed clarification | label (string), nodeCount (integer) | 27 | 10/10 |
| [RAN4_P1_CQ5-2](#ran4_p1_cq5-2) | Substantive variant | meeting (string), meetingNumber (integer), tdocCount (integer) | 58 | 13/13 |
| [RAN4_P1_CQ5-3](#ran4_p1_cq5-3) | Proposed clarification | attributedTdocCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ5-4](#ran4_p1_cq5-4) | Proposed clarification | release (string), tdocCount (integer) | 14 | 10/10 |
| [RAN4_P1_CQ5-5](#ran4_p1_cq5-5) | Proposed clarification | specNumber (string), crCount (integer) | 10 | 10/10 |
| [RAN4_P1_CQ6-1](#ran4_p1_cq6-1) | Proposed clarification | tdocCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ6-2](#ran4_p1_cq6-2) | Proposed clarification | meetingNodeCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ6-3](#ran4_p1_cq6-3) | Proposed clarification | crTdocCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ6-4](#ran4_p1_cq6-4) | Proposed clarification | lsNodeCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ6-5](#ran4_p1_cq6-5) | Proposed clarification | contactNodeCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ7-1](#ran4_p1_cq7-1) | Proposed clarification | agendaNodeCount (integer) | 1 | 7/7 |
| [RAN4_P1_CQ7-2](#ran4_p1_cq7-2) | Proposed clarification | workItemNodeCount (integer) | 1 | 7/7 |
| [RAN4_P2_CQ1-1](#ran4_p2_cq1-1) | Proposed clarification | agreementId (string), content (string) | 141 | 10/10 |
| [RAN4_P2_CQ1-2](#ran4_p2_cq1-2) | Proposed clarification | conclusionId (string), content (string) | 1 | 10/10 |
| [RAN4_P2_CQ1-3](#ran4_p2_cq1-3) | Proposed clarification | meeting (string) | 3 | 7/7 |
| [RAN4_P2_CQ1-4](#ran4_p2_cq1-4) | Proposed clarification | resolutionId (string), meeting (string) | 3 | 10/10 |
| [RAN4_P2_CQ1-5](#ran4_p2_cq1-5) | Proposed clarification | resolutionId (string), meeting (string) | 452 | 10/10 |
| [RAN4_P2_CQ1-6](#ran4_p2_cq1-6) | Substantive variant | resolutionId (string), meeting (string) | 216 | 10/10 |
| [RAN4_P2_CQ1-8](#ran4_p2_cq1-8) | Proposed clarification | agendaNumber (string), resolutionCount (integer) | 10 | 10/10 |
| [RAN4_P2_CQ2-1](#ran4_p2_cq2-1) | Proposed clarification | tdocNumber (string) | 28 | 7/7 |
| [RAN4_P2_CQ2-2](#ran4_p2_cq2-2) | Proposed clarification | resolutionId (string) | 465 | 7/7 |
| [RAN4_P2_CQ2-3](#ran4_p2_cq2-3) | Proposed clarification | resolutionId (string) | 1,073 | 7/7 |
| [RAN4_P2_CQ2-4](#ran4_p2_cq2-4) | Proposed clarification | specNumber (string), tdocCount (integer) | 10 | 10/10 |
| [RAN4_P2_CQ3-1](#ran4_p2_cq3-1) | Substantive variant | referencedFraction (number) | 1 | 7/7 |
| [RAN4_P2_CQ3-2](#ran4_p2_cq3-2) | Proposed clarification | companyName (string), resolutionCount (integer) | 10 | 10/10 |
| [RAN4_P2_CQ3-3](#ran4_p2_cq3-3) | Substantive variant | companyName (string), tdocCount (integer) | 30 | 10/10 |
| [RAN4_P2_CQ6-1](#ran4_p2_cq6-1) | Substantive variant | meeting (string), meetingNumber (integer), resolutionCount (integer) | 16 | 13/13 |
| [RAN4_P2_CQ6-2](#ran4_p2_cq6-2) | Proposed clarification | meeting (string), meetingNumber (integer), resolutionCount (integer) | 20 | 13/13 |
| [RAN4_P3_CQ1-1](#ran4_p3_cq1-1) | Proposed clarification | sectionId (string), sectionNumber (string), title (string), level (integer) | 32,888 | 16/16 |
| [RAN4_P3_CQ1-10](#ran4_p3_cq1-10) | Proposed clarification | specNumber (string), sectionId (string) | 24 | 10/10 |
| [RAN4_P3_CQ1-11](#ran4_p3_cq1-11) | Proposed clarification | sectionId (string), sectionNumber (string), title (string) | 331 | 13/13 |
| [RAN4_P3_CQ1-12](#ran4_p3_cq1-12) | Substantive variant | sectionId (string), sectionNumber (string), title (string) | 211 | 13/13 |
| [RAN4_P3_CQ1-13](#ran4_p3_cq1-13) | Proposed clarification | sectionId (string), sectionNumber (string), title (string) | 754 | 13/13 |
| [RAN4_P3_CQ1-15](#ran4_p3_cq1-15) | Proposed clarification | sectionId (string), title (string) | 5,447 | 10/10 |
| [RAN4_P3_CQ1-16](#ran4_p3_cq1-16) | Proposed clarification | specNumber (string), sectionCount (integer) | 5 | 10/10 |
| [RAN4_P3_CQ1-2](#ran4_p3_cq1-2) | Substantive variant | sectionId (string), sectionNumber (string), title (string) | 282 | 13/13 |
| [RAN4_P3_CQ1-4](#ran4_p3_cq1-4) | Proposed clarification | sectionId (string), sectionNumber (string), title (string) | 190 | 13/13 |
| [RAN4_P3_CQ1-5](#ran4_p3_cq1-5) | Substantive variant | tableId (string), tableNumber (string), caption (string) | 70 | 13/13 |
| [RAN4_P3_CQ1-6](#ran4_p3_cq1-6) | Substantive variant | figureId (string), figureNumber (string), caption (string) | 35 | 13/13 |
| [RAN4_P3_CQ1-7](#ran4_p3_cq1-7) | Substantive variant | sectionId (string) | 5 | 7/7 |
| [RAN4_P3_CQ1-8](#ran4_p3_cq1-8) | Proposed clarification | tableId (string), tableNumber (string), caption (string) | 3,001 | 13/13 |
| [RAN4_P3_CQ1-9](#ran4_p3_cq1-9) | Proposed clarification | sectionId (string) | 5,972 | 7/7 |
| [RAN4_P3_CQ2-1](#ran4_p3_cq2-1) | Substantive variant | sectionId (string) | 19 | 7/7 |
| [RAN4_P3_CQ2-2](#ran4_p3_cq2-2) | Substantive variant | sectionId (string) | 619 | 7/7 |
| [RAN4_P3_CQ2-3](#ran4_p3_cq2-3) | Proposed clarification | sectionId (string), referringSectionCount (integer) | 10 | 10/10 |
| [RAN4_P3_CQ2-4](#ran4_p3_cq2-4) | Proposed clarification | sectionId (string), referencedSectionCount (integer) | 10 | 10/10 |
| [RAN4_P3_CQ2-5](#ran4_p3_cq2-5) | Substantive variant | fromSpec (string), toSpec (string), referenceEdgeCount (integer) | 4 | 13/13 |
| [RAN4_P3_CQ2-6](#ran4_p3_cq2-6) | Proposed clarification | specNumber (string), referenceEdgeCount (integer) | 4 | 10/10 |
| [RAN4_P3_CQ2-7](#ran4_p3_cq2-7) | Proposed clarification | fromSpec (string), toSpec (string), referenceEdgeCount (integer) | 10 | 13/13 |
| [RAN4_P3_CQ2-8](#ran4_p3_cq2-8) | Proposed clarification | referenceEdgeCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ3-1](#ran4_p3_cq3-1) | Proposed clarification | specNumber (string) | 0 | 3/3 |
| [RAN4_P3_CQ3-2](#ran4_p3_cq3-2) | Substantive variant | crCount (integer), sectionCount (integer) | 1 | 10/10 |
| [RAN4_P3_CQ3-3](#ran4_p3_cq3-3) | Substantive variant | crTdoc (string) | 10 | 7/7 |
| [RAN4_P3_CQ3-4](#ran4_p3_cq3-4) | Substantive variant | crTdoc (string) | 57 | 7/7 |
| [RAN4_P3_CQ3-5](#ran4_p3_cq3-5) | Proposed clarification | specNumber (string) | 31 | 7/7 |
| [RAN4_P3_CQ3-6](#ran4_p3_cq3-6) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ3-7](#ran4_p3_cq3-7) | Proposed clarification | companyName (string), crCount (integer) | 10 | 10/10 |
| [RAN4_P3_CQ3-8](#ran4_p3_cq3-8) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ4-1](#ran4_p3_cq4-1) | Substantive variant | resolutionId (string), crTdoc (string) | 1,766 | 10/10 |
| [RAN4_P3_CQ4-2](#ran4_p3_cq4-2) | Substantive variant | resolutionCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ4-3](#ran4_p3_cq4-3) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ4-4](#ran4_p3_cq4-4) | Substantive variant | specNumber (string) | 14 | 7/7 |
| [RAN4_P3_CQ5-1](#ran4_p3_cq5-1) | Proposed clarification | crCount (integer) | 1 | 7/7 |
| [RAN4_P3_CQ5-2](#ran4_p3_cq5-2) | Proposed clarification | specNumber (string), crCount (integer) | 5 | 10/10 |
| [RAN4_P3_CQ5-3](#ran4_p3_cq5-3) | Proposed clarification | specNumber (string), crCount (integer) | 10 | 10/10 |
| [RAN4_P3_CQ5-4](#ran4_p3_cq5-4) | Proposed clarification | specNumber (string), crCount (integer) | 10 | 10/10 |
| [RAN4_P3_P3-S8-CQ02](#ran4_p3_p3-s8-cq02) | Proposed clarification | itemCount (integer), unlinkedCount (integer), allLinked (boolean) | 1 | 13/13 |
| [RAN4_P3_P3-S8-CQ05](#ran4_p3_p3-s8-cq05) | Proposed clarification | class (string), granularity (string), nodeCount (integer) | 2 | 13/13 |
| [RAN4_P4_CQ2-1](#ran4_p4_cq2-1) | Proposed clarification | specNumber (string) | 2 | 7/7 |
| [RAN4_P4_CQ2-2](#ran4_p4_cq2-2) | Proposed clarification | crTdoc (string) | 1,379 | 7/7 |
| [RAN4_P4_CQ2-3](#ran4_p4_cq2-3) | Proposed clarification | crTdoc (string) | 1,515 | 7/7 |
| [RAN4_P4_CQ2-4](#ran4_p4_cq2-4) | Proposed clarification | crTdoc (string), affectedSpecCount (integer) | 10 | 10/10 |
| [RAN4_P4_CQ3-1](#ran4_p4_cq3-1) | Proposed clarification | crTdoc (string), summary (string) | 60 | 10/10 |
| [RAN4_P4_CQ3-2](#ran4_p4_cq3-2) | Proposed clarification | crPackId (string) | 158 | 7/7 |
| [RAN4_P4_CQ3-3](#ran4_p4_cq3-3) | Proposed clarification | crPackId (string) | 35 | 7/7 |
| [RAN4_P4_CQ4-1](#ran4_p4_cq4-1) | Proposed clarification | crTdoc (string), reason (string) | 123 | 10/10 |
| [RAN4_P4_CQ4-2](#ran4_p4_cq4-2) | Substantive variant | crTdoc (string), reason (string), summary (string) | 3,672 | 13/13 |
| [RAN4_P4_CQ4-3](#ran4_p4_cq4-3) | Proposed clarification | sectionId (string) | 4,274 | 7/7 |
| [RAN4_P4_CQ4-4](#ran4_p4_cq4-4) | Proposed clarification | specNumber (string) | 18 | 7/7 |
| [RAN4_P4_CQ4-5](#ran4_p4_cq4-5) | Substantive variant | crTdoc (string), summary (string) | 544 | 10/10 |
| [RAN4_P5_CQ1-1](#ran4_p5_cq1-1) | Proposed clarification | trNumber (string) | 15 | 7/7 |
| [RAN4_P5_CQ1-4](#ran4_p5_cq1-4) | Proposed clarification | trNumber (string) | 1 | 7/7 |
| [RAN4_P5_CQ2-1](#ran4_p5_cq2-1) | Proposed clarification | specNumber (string) | 4 | 7/7 |
| [RAN4_P5_CQ2-2](#ran4_p5_cq2-2) | Proposed clarification | impactType (string) | 1 | 7/7 |
| [RAN4_P5_CQ2-3](#ran4_p5_cq2-3) | Substantive variant | trNumber (string) | 1 | 7/7 |
| [RAN4_P5_CQ2-4](#ran4_p5_cq2-4) | Substantive variant | trNumber (string) | 62 | 7/7 |
| [RAN4_P5_CQ2-5](#ran4_p5_cq2-5) | Proposed clarification | trNumber (string) | 47 | 7/7 |
| [RAN4_P5_CQ3-1](#ran4_p5_cq3-1) | Proposed clarification | specNumber (string) | 4 | 7/7 |
| [RAN4_P5_CQ3-2](#ran4_p5_cq3-2) | Proposed clarification | specNumber (string), impactType (string) | 1 | 10/10 |
| [RAN4_P5_CQ3-3](#ran4_p5_cq3-3) | Proposed clarification | specNumber (string), impactType (string), description (string) | 1 | 13/13 |
| [RAN4_P5_CQ4-1](#ran4_p5_cq4-1) | Proposed clarification | trNumber (string), impactType (string) | 22 | 10/10 |
| [RAN4_P5_CQ4-2](#ran4_p5_cq4-2) | Proposed clarification | status (string), scope (string) | 1 | 10/10 |
| [RAN4_P5_CQ4-3](#ran4_p5_cq4-3) | Substantive variant | conclusions (string), specNumber (string), impactType (string) | 1 | 13/13 |
| [RAN4_P5_CQ5-2](#ran4_p5_cq5-2) | Proposed clarification | trNumber (string) | 6 | 7/7 |
| [RAN4_P5_CQ5-3](#ran4_p5_cq5-3) | Proposed clarification | trNumber (string), referringTrCount (integer) | 5 | 10/10 |

## RAN4_P1_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TDocs presented at meeting RAN4#113 (meeting document overview).

**Revised question:** List all distinct TDoc identifiers presented at canonical meetingRAN4#113. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original overview list has unstated10 cap; requested identifiers only.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#113'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#113'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ1-1/53316b267903df3aaab5a8e1f7839202fc442a64edd99949ee7b9c662456f42b.json), [complete native rows](../reference_outputs/RAN4_P1_CQ1-1/53316b267903df3aaab5a8e1f7839202fc442a64edd99949ee7b9c662456f42b.jsonl); 3,089 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `eca509f79d3b91111a7e2a3d0d0c5b6471506b09b6c889113e3168a6c41f4765`.

## RAN4_P1_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the details of TDoc R4-2417515, including its submitting company (document lookup).

**Revised question:** Return distinct TDoc-identifier,title,type and recorded submitting-company-name records for R4-2417515; companyName is null if no SUBMITTED_BY Company is recorded. Return named records with tdocNumber, title, type, companyName. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Broad details clarified using existing named outputs, including specifically requested submitting company and optional-null policy.

**Original query**

```cypher
MATCH (t:Tdoc {tdocNumber:'R4-2417515'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, t.type, c.companyName
```

**Revised query**

```cypher
MATCH (t:Tdoc {tdocNumber:'R4-2417515'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT t.tdocNumber AS tdocNumber, t.title AS title, t.type AS type, c.companyName AS companyName
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
      "nullable": false,
      "source_column_or_expression": "title",
      "type": "string"
    },
    {
      "name": "type",
      "nullable": false,
      "source_column_or_expression": "type",
      "type": "string"
    },
    {
      "name": "companyName",
      "nullable": true,
      "source_column_or_expression": "companyName",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ1-2/dc7aa8b1cae6ed924f31b23d2a3889d2cfb56c1f5f52c39a4064b75c89ff2ebe.json), [complete native rows](../reference_outputs/RAN4_P1_CQ1-2/dc7aa8b1cae6ed924f31b23d2a3889d2cfb56c1f5f52c39a4064b75c89ff2ebe.jsonl); 1 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `ecf8715ce2bf1285b6f9c18161cf032655b49bc22c7794ef76a937aa6133535c`.

## RAN4_P1_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the details of CR R4-2419229 and the spec it modifies (change-request lookup).

**Revised question:** Return distinct CR-TDoc-identifier,title and modified-specification-number records for R4-2419229; specNumber is null when no MODIFIES target is recorded. Return named records with crTdoc, title, specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** CR details and modified spec must remain paired, nullable optional-link target explicit.

**Original query**

```cypher
MATCH (cr:CR {tdocNumber:'R4-2419229'}) OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN cr.tdocNumber, cr.title, sp.specNumber
```

**Revised query**

```cypher
MATCH (cr:CR {tdocNumber:'R4-2419229'}) OPTIONAL MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT cr.tdocNumber AS crTdoc, cr.title AS title, sp.specNumber AS specNumber
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
      "name": "title",
      "nullable": false,
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ1-3/7db612ba99c6da20c04a353855c6d9ac975eca98b92304f64946c8694f471651.json), [complete native rows](../reference_outputs/RAN4_P1_CQ1-3/7db612ba99c6da20c04a353855c6d9ac975eca98b92304f64946c8694f471651.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `3af2ed106ff8491f588a0031887e7d566e15314a7e0bbadcf995f10d66794b9d`.

## RAN4_P1_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 5 meetings by number of TDocs (busiest meetings).

**Revised question:** Return top5 canonical meeting identifiers by count of distinct presented TDoc nodes, ties by meeting identifier ascending; return all if fewer than5 exist. Return named records with meeting, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Distinct TDoc count with complete meeting/count pairing and deterministic ties.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, meeting ASC LIMIT 5
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
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 5
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ1-4/2cee6f4b5e9b2ac5b9096687849fb09b4db2614c04f5c5386fd76abcadded8d9.json), [complete native rows](../reference_outputs/RAN4_P1_CQ1-4/2cee6f4b5e9b2ac5b9096687849fb09b4db2614c04f5c5386fd76abcadded8d9.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8adcd65aab79365227e4720531c87a07f51f993409c742d06b261cab94094e21`.

## RAN4_P1_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Huawei's TDocs (per-company contribution overview).

**Revised question:** List all distinct TDoc identifiers submitted by Company namedHuawei. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove unstated10 cap and preserve exact company identity.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Huawei'}) RETURN t.tdocNumber ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Huawei'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ1-5/d929836969ae6bc41a3ab329ba8154612111ff873aca8ffdc575ec7b336b6461.json), [complete native rows](../reference_outputs/RAN4_P1_CQ1-5/d929836969ae6bc41a3ab329ba8154612111ff873aca8ffdc575ec7b336b6461.jsonl); 27,710 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `4c021713277accfcbb816e381ab725fb4aadb487dd3e5b73f27324f8abd851da`.

## RAN4_P1_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs target Rel-18? (release workload sizing).

**Revised question:** Count distinct TDoc nodes with TARGET_RELEASE link toRel-18. Return named records with tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Count documents rather than duplicate target-release matches.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN DISTINCT count(DISTINCT t) AS tdocCount
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
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ2-1/dbbbb359b223d25075b508b3ca917e325a226e2a01db69966b6491bf960775fe.json), [complete native rows](../reference_outputs/RAN4_P1_CQ2-1/dbbbb359b223d25075b508b3ca917e325a226e2a01db69966b6491bf960775fe.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `9f42f33746056ff029d732999543d35f2fd3dd3983119285419c11948e818d59`.

## RAN4_P1_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that modify spec 38.101-1 (spec change tracking).

**Revised question:** List all distinct CR TDoc identifiers linked by MODIFIES tospecification38.101-1. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove unstated10 cap and preserve requested CR identifiers.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.101-1'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.101-1'}) RETURN DISTINCT cr.tdocNumber AS crTdoc
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ2-2/a25427ccc803cf797126bd8cf445ed01d2e1de4a3da2b614a68af7149a7e58d9.json), [complete native rows](../reference_outputs/RAN4_P1_CQ2-2/a25427ccc803cf797126bd8cf445ed01d2e1de4a3da2b614a68af7149a7e58d9.jsonl); 7,427 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `c6cb9ae6455a6b679bc96e940f9dbeeca8ef27749732b3761a5135a9136428f9`.

## RAN4_P1_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which Work Items have the most related TDocs? (activity by work item).

**Revised question:** Return every Work Item code with the maximum number of distinct related TDoc nodes, together with that count; include all ties among Work Items with at least one related TDoc. Return named records with workItemCode, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Most means maximum, not arbitrary top5; count distinct TDocs and preserve all maximum ties.

**Original query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) WITH wi.workItemCode AS workItemCode,count(DISTINCT t) AS tdocCount WITH collect({workItemCode:workItemCode,tdocCount:tdocCount}) AS groups WITH groups,reduce(maxCount=0,g IN groups|CASE WHEN g.tdocCount>maxCount THEN g.tdocCount ELSE maxCount END) AS maxCount UNWIND groups AS g WITH g,maxCount WHERE g.tdocCount=maxCount RETURN g.workItemCode AS workItemCode,g.tdocCount AS tdocCount
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
    "extent": "all groups tied at maximum distinct TDoc count",
    "mode": "all"
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ2-3/410a435f96bab979d1127a859ea38b2f6d95b081544aa82c7c4b8db44e284613.json), [complete native rows](../reference_outputs/RAN4_P1_CQ2-3/410a435f96bab979d1127a859ea38b2f6d95b081544aa82c7c4b8db44e284613.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e1faee5315a4f67710f78b8417ecf466d4faa5af5a782962354f642728051fb0`.

## RAN4_P1_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the distribution of TDocs across agenda items (agenda workload breakdown).

**Revised question:** For each recorded agenda-number group linked to TDocs, return agenda number and distinct TDoc-node count across all meetings. Return named records with agendaNumber, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Distribution cannot silently truncate10; aggregate agenda-number across meetings explicitly and require counts.

**Original query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT ai.agendaNumber AS agendaNumber, count(DISTINCT t) AS tdocCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ3-1/b24f8a62e0ef5b8c0f7b4db6c9006da05cfacf590db639d818dea6627675e158.json), [complete native rows](../reference_outputs/RAN4_P1_CQ3-1/b24f8a62e0ef5b8c0f7b4db6c9006da05cfacf590db639d818dea6627675e158.jsonl); 6,539 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c1d31a8a7493c44943b629ea898d0abfd494499b4424ec220e13a19d866e4679`.

## RAN4_P1_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the distribution of TDocs by document type (document-type breakdown).

**Revised question:** For every recorded TDoc type value, return type and distinct TDoc-node count. Return named records with type, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full type/count distribution, no hidden10 cap.

**Original query**

```cypher
MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc) RETURN DISTINCT t.type AS type, count(DISTINCT t) AS tdocCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ3-2/7441cbb24b77f01a70fe3fb73c7ebae4058f252feff822d112691ab564b6aff8.json), [complete native rows](../reference_outputs/RAN4_P1_CQ3-2/7441cbb24b77f01a70fe3fb73c7ebae4058f252feff822d112691ab564b6aff8.jsonl); 19 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `7ad3b5b2f5ceacc4808319eef1804c4aaca65dea7681ba0b38aaefd6c9ac6f05`.

## RAN4_P1_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 companies by CR contributions (leading CR contributors).

**Revised question:** Return top10 company names by distinct submitted CR-node count, ties by company name ascending; return all if fewer than10 have CRs. Return named records with companyName, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Count distinct CR nodes and require paired count/company roles, deterministic ties.

**Original query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, companyName ASC LIMIT 10
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ3-3/64435bd8ed7fead90cc0662ffda6792b11a0ddad266c2974e2b43fff2a9c3065.json), [complete native rows](../reference_outputs/RAN4_P1_CQ3-3/64435bd8ed7fead90cc0662ffda6792b11a0ddad266c2974e2b43fff2a9c3065.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f56129bd8efa3c290dc7791a66ddca1d0158538128425e3bbe5d39f3dbd37f4c`.

## RAN4_P1_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the direction and recipients of liaison statement R4-2417507 (LS routing analysis).

**Revised question:** Return direction and recorded recipient WorkingGroup names for LS R4-2417507 as distinct direction/recipient records; recipient is null when no SENT_TO edge is recorded. Return named records with direction, recipient. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original routing requires direction plus recipient, not source LS ID. Flatten unordered collected recipient names with explicit null semantics.

**Original query**

```cypher
MATCH (ls:LS {tdocNumber:'R4-2417507'}) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo
```

**Revised query**

```cypher
MATCH (ls:LS {tdocNumber:'R4-2417507'}) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN DISTINCT ls.direction AS direction,wg.wgName AS recipient
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "direction",
      "nullable": false,
      "source_column_or_expression": "direction",
      "type": "string"
    },
    {
      "name": "recipient",
      "nullable": true,
      "source_column_or_expression": "recipient",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ4-2/a69c89c14a6ff1f191b92a9e1d8674c697912bbf76277cc1aac0763956071cca.json), [complete native rows](../reference_outputs/RAN4_P1_CQ4-2/a69c89c14a6ff1f191b92a9e1d8674c697912bbf76277cc1aac0763956071cca.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `1e1117496ef5883650e6189b4b9503a5d1426d4b82ceda786efdaa7bab021272`.

## RAN4_P1_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return node counts by label across the graph (dataset statistics).

**Revised question:** For each present node label, return label and count of distinct nodes having that label; multi-label nodes contribute to each label. Return named records with label, nodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full label/count mapping, explicit membership multiplicity across labels.

**Original query**

```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```

**Revised query**

```cypher
MATCH (n) UNWIND labels(n) AS label RETURN DISTINCT label AS label, count(DISTINCT n) AS nodeCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ5-1/d6d80e50aa0061c323eb6bc9ab4951a0acb2fff7dccbbb45ef4f926c10c519ce.json), [complete native rows](../reference_outputs/RAN4_P1_CQ5-1/d6d80e50aa0061c323eb6bc9ab4951a0acb2fff7dccbbb45ef4f926c10c519ce.jsonl); 27 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `2e28bbd39c90153faf36bfa2f96cca5ec07675d93fea9a2a4fad2a6028a2237d`.

## RAN4_P1_CQ5-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the most recent meetings and their TDoc counts (meeting coverage check).

**Revised question:** Rank all recorded canonical meetings by meetingNumberInt descending then canonical meeting identifier ascending, and return each meeting's integer meeting number and distinct presented-TDoc count, including zero when no TDoc is recorded. Return named records with meeting, meetingNumber, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Most recent has no k/date measure; separate explicitly recorded-sequence ranking task avoids asserting actual date recency and removes cap.

**Original query**

```cypher
MATCH (m:Meeting) WITH m OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m, count(t) AS tdocs RETURN m.canonicalMeetingNumber, tdocs ORDER BY m.meetingNumberInt DESC, m.canonicalMeetingNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m,count(DISTINCT t) AS tdocCount RETURN m.canonicalMeetingNumber AS meeting,m.meetingNumberInt AS meetingNumber,tdocCount ORDER BY meetingNumber DESC,meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ5-2/bea28209fde6fb473e15ca6f0242bf16aa98b52de9aaf2c4b247c2828f2ab90c.json), [complete native rows](../reference_outputs/RAN4_P1_CQ5-2/bea28209fde6fb473e15ca6f0242bf16aa98b52de9aaf2c4b247c2828f2ab90c.jsonl); 58 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `a3a0d288a1b6c46c444ae392937c592255841ab55f56cd94088b3edce28bf1d5`.

## RAN4_P1_CQ5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs have a submitting company assigned? (attribution coverage check).

**Revised question:** Count distinct TDoc nodes having at least one recorded SUBMITTED_BY edge to a Company. Return named records with attributedTdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original count(c) counts matches and count(t) repeats multi-company TDocs; requested unit is distinct attributed documents.

**Original query**

```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
```

**Revised query**

```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(DISTINCT CASE WHEN c IS NOT NULL THEN t ELSE null END) AS attributedTdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "attributedTdocCount",
      "nullable": false,
      "source_column_or_expression": "attributedTdocCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ5-3/b511957b7cfe5d3ade8004c9cd44b7ea200b3010d5239f2f6c639c6b85eb7782.json), [complete native rows](../reference_outputs/RAN4_P1_CQ5-3/b511957b7cfe5d3ade8004c9cd44b7ea200b3010d5239f2f6c639c6b85eb7782.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `cdb334162490a1d924272bab6fad430bce62e10935cc7b13d2cf0ddec168a388`.

## RAN4_P1_CQ5-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the distribution of TDocs by release (per-release volume).

**Revised question:** For every release name targeted by a TDoc, return release name and number of distinct targeting TDoc nodes. Return named records with release, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Complete release/count mapping, no ten cap; one document may legitimately target multiple releases.

**Original query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN DISTINCT r.releaseName AS release, count(DISTINCT t) AS tdocCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ5-4/a4006b19781f2338d9801e3800c6b4a53507ff2ec7daeea0eb874be6f82ea8e6.json), [complete native rows](../reference_outputs/RAN4_P1_CQ5-4/a4006b19781f2338d9801e3800c6b4a53507ff2ec7daeea0eb874be6f82ea8e6.jsonl); 14 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c56622e4219341afd17c846c634ffc5892133ff41883821a6ff7ae4c4b5b7f8a`.

## RAN4_P1_CQ5-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 specs by number of CRs (most-revised specs).

**Revised question:** Return top10 specification numbers by distinct modifying CR-node count, ties by specNumber ascending; return all if fewer than10 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Distinct CR unit correct across duplicate joins and recorded editions; deterministic ties.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 10
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
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ5-5/7c9c8fff3af1a194c652834ceb82929d314092792d14d16608b68a2c1e579a50.json), [complete native rows](../reference_outputs/RAN4_P1_CQ5-5/7c9c8fff3af1a194c652834ceb82929d314092792d14d16608b68a2c1e579a50.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e67f4567e75fd980ba8dbf926c8d7f40d94016bffeb441e33196070ca4965c17`.

## RAN4_P1_CQ6-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many TDocs were presented at meeting RAN4#117? (meeting size).

**Revised question:** Count distinct TDoc nodes presented at canonical meetingRAN4#117. Return named records with tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Exact meeting retained, distinct-document count.

**Original query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#117'}) RETURN count(t) AS cnt
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#117'}) RETURN DISTINCT count(DISTINCT t) AS tdocCount
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
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ6-1/cb4ffde58fbd096993e451757083bc89928992714f798c2e0773da003782dc7a.json), [complete native rows](../reference_outputs/RAN4_P1_CQ6-1/cb4ffde58fbd096993e451757083bc89928992714f798c2e0773da003782dc7a.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `5adbc0038711767d3d5b38ef9accbc24b36608bc77fd0b7eaf1a057b29fa1ff6`.

## RAN4_P1_CQ6-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many meetings are in the dataset? (meeting coverage count).

**Revised question:** Count recorded Meeting nodes. Return named records with meetingNodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Node population explicit, original count source valid.

**Original query**

```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```

**Revised query**

```cypher
MATCH (m:Meeting) RETURN DISTINCT count(m) AS meetingNodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "meetingNodeCount",
      "nullable": false,
      "source_column_or_expression": "meetingNodeCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ6-2/0a21920fe092cc4616cd95a8b6a30fadaa3d9cf8609815c420e3becce62e9414.json), [complete native rows](../reference_outputs/RAN4_P1_CQ6-2/0a21920fe092cc4616cd95a8b6a30fadaa3d9cf8609815c420e3becce62e9414.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `58a527a6866c382d55d3822ecd16a6fbee84e6c0e2d4fc7d626a4955734498d1`.

## RAN4_P1_CQ6-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many of the TDocs are CRs? (change-request proportion).

**Revised question:** Count recorded Tdoc nodes that also carry the CR label. Return named records with crTdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original how many asks CR-labeled TDocs, not total-TDoc first-column key or unsupported proportion; explicit label intersection.

**Original query**

```cypher
MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
```

**Revised query**

```cypher
MATCH (t:Tdoc) WHERE t:CR RETURN count(t) AS crTdocCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "crTdocCount",
      "nullable": false,
      "source_column_or_expression": "crTdocCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ6-3/d4487c533b0981ec5fc48ca2d4d7343de5d7d5bb4dd668c4f7a34893ceddb829.json), [complete native rows](../reference_outputs/RAN4_P1_CQ6-3/d4487c533b0981ec5fc48ca2d4d7343de5d7d5bb4dd668c4f7a34893ceddb829.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `19437050dc3244accfff8b4e0cff1a6fb5133e65c78c316b53d4b245cc9988b9`.

## RAN4_P1_CQ6-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many liaison statements are in the dataset? (LS count).

**Revised question:** Count recorded LS nodes. Return named records with lsNodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original LS count already directly defined; stable named scalar output.

**Original query**

```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```

**Revised query**

```cypher
MATCH (ls:LS) RETURN DISTINCT count(ls) AS lsNodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "lsNodeCount",
      "nullable": false,
      "source_column_or_expression": "lsNodeCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ6-4/ecbf5e975c3cd5902412e0fa29f98530b3a61c3bdd4217f33cd493fb0410863c.json), [complete native rows](../reference_outputs/RAN4_P1_CQ6-4/ecbf5e975c3cd5902412e0fa29f98530b3a61c3bdd4217f33cd493fb0410863c.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7d8496fd223beeaec1971dc46693fdaa384fd37133d6d79e81f7871eb3f0a76d`.

## RAN4_P1_CQ6-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many contacts are in the dataset? (contact count).

**Revised question:** Count recorded Contact nodes. Return named records with contactNodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original count directly defined; output name identifies unit.

**Original query**

```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```

**Revised query**

```cypher
MATCH (c:Contact) RETURN DISTINCT count(c) AS contactNodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "contactNodeCount",
      "nullable": false,
      "source_column_or_expression": "contactNodeCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ6-5/b76f9d7f9bdbee0034ff8720e76bd55d72976ae99e8f31bbf6deec9a0d7527d0.json), [complete native rows](../reference_outputs/RAN4_P1_CQ6-5/b76f9d7f9bdbee0034ff8720e76bd55d72976ae99e8f31bbf6deec9a0d7527d0.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `5c06e412ac076dc7f19760ff704a3f5cccb47f8406996f1d12bb503237161fe6`.

## RAN4_P1_CQ7-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many agenda items are in the dataset? (agenda-item count).

**Revised question:** Count recorded AgendaItem nodes. Return named records with agendaNodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Count nodes rather than agenda-number groups; literal original population explicit.

**Original query**

```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) RETURN DISTINCT count(ai) AS agendaNodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "agendaNodeCount",
      "nullable": false,
      "source_column_or_expression": "agendaNodeCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ7-1/a5a4026dff1d03a4659bd5dbd47a516356f7bd7c5740087a16dead743faedd2b.json), [complete native rows](../reference_outputs/RAN4_P1_CQ7-1/a5a4026dff1d03a4659bd5dbd47a516356f7bd7c5740087a16dead743faedd2b.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `544906eec083ef8f3c84ad6c4018e7f59df7553cbc1291181bd58beeb8da1704`.

## RAN4_P1_CQ7-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many work items are in the dataset? (work-item count).

**Revised question:** Count recorded WorkItem nodes. Return named records with workItemNodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original graph-node count directly supported.

**Original query**

```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```

**Revised query**

```cypher
MATCH (wi:WorkItem) RETURN DISTINCT count(wi) AS workItemNodeCount
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "workItemNodeCount",
      "nullable": false,
      "source_column_or_expression": "workItemNodeCount",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P1_CQ7-2/acb1ae729fa521c5d725128a1f0fa33f60e4febcdedbda956e32e27b5d4c15cb.json), [complete native rows](../reference_outputs/RAN4_P1_CQ7-2/acb1ae729fa521c5d725128a1f0fa33f60e4febcdedbda956e32e27b5d4c15cb.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `6941dee211c5472fa477dfe6589ed1bea073261859aa3fa07740e368eb582dae`.

## RAN4_P2_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the agreements reached at meeting RAN4#98 (meeting outcome review).

**Revised question:** List all distinct Agreement identifiers and content strings recorded atRAN4#98. Return named records with agreementId, content. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove15 cap; IDs pair with requested agreement content, optional agenda context not required.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId AS agreementId, a.content AS content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-1/8604d1914a3a85ea919bc3287e0bfa5c862783460eb17c5360bd1307ee1ea6e4.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-1/8604d1914a3a85ea919bc3287e0bfa5c862783460eb17c5360bd1307ee1ea6e4.jsonl); 141 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `31668897a9a3ee3182cf8d4a55fa1ceb118842f89a73797b8b01aa7c0d5d412c`.

## RAN4_P2_CQ1-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the conclusions drawn at meeting RAN4#98 (meeting outcome review).

**Revised question:** List all distinct Conclusion identifiers and content strings recorded atRAN4#98. Return named records with conclusionId, content. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove cap and do not require unrequested consensus/agenda fields.

**Original query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-2/db604dd2b54dc5fea266e1e90cd29ad12532ddda8f7439ca8983f3bf73c30a29.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-2/db604dd2b54dc5fea266e1e90cd29ad12532ddda8f7439ca8983f3bf73c30a29.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `be68b6fae4145ea442690a68f9499308161959ef48e3989be00fb3d8447261b9`.

## RAN4_P2_CQ1-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which meetings recorded working assumptions? (locating open assumptions).

**Revised question:** List all distinct canonical meeting identifiers with a WorkingAssumption node recorded through MADE_AT. Return named records with meeting. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Question asks meeting inventory, not counts; remove15 cap.

**Original query**

```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(w) AS cnt ORDER BY cnt DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-3/e489f59ecf8cd03b87dcd006ea3b27d001a3e67238bf0fd66a0c7df748beaf93.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-3/e489f59ecf8cd03b87dcd006ea3b27d001a3e67238bf0fd66a0c7df748beaf93.jsonl); 3 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `16d438aa066301880b2bf81e396d32186a29c87a17ff87da9c5568436140cabc`.

## RAN4_P2_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions under agenda item 7 (agenda-scoped decisions).

**Revised question:** List all distinct Resolution identifiers and canonical meeting identifiers where the Resolution is linked to agenda number7. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove cap; agenda-number grouping across meetings and identifying meeting fields explicit; labels unrequested.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '7'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '7'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-4/54ad1e4d03aefb4b5814cf9c3f37c7f84f1849879d0d72d0c54c73d9c23db4e0.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-4/54ad1e4d03aefb4b5814cf9c3f37c7f84f1849879d0d72d0c54c73d9c23db4e0.jsonl); 3 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5bd55e9d1901ba7712e1743f5c0f5f5b0e468c08791318ff33ebef95fdb33f8d`.

## RAN4_P2_CQ1-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions tied to Rel-15 TDocs (release-scoped decisions).

**Revised question:** List all distinct Resolution identifiers and canonical meeting identifiers where the Resolution references a TDoc targetingRel-15. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove cap and collapse duplicate documentary paths; no label requirement.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-15'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-15'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-5/a8a4b2f371c2490d500e0d41dcc7060c0a817ebb981a72345e024a1f470a2dd0.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-5/a8a4b2f371c2490d500e0d41dcc7060c0a817ebb981a72345e024a1f470a2dd0.jsonl); 452 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0a3221ecb099350b18bde5c5fe0b4aad02088b603573bf8405e089ee5cf98886`.

## RAN4_P2_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions that drive changes to spec 38.133 (decisions affecting a spec).

**Revised question:** List all distinct Resolution identifiers and canonical meeting identifiers where a Resolution references a TDoc with MODIFIES edge tospecification38.133. Return named records with resolutionId, meeting. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Recorded references do not prove drive changes; make documentary path task explicit and remove cap.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber, m.meetingNumberInt AS mNum ORDER BY mNum DESC, r.resolutionId LIMIT 15
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId AS resolutionId, m.canonicalMeetingNumber AS meeting
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-6/0d37436a8a1753f1e201f752643711e54afa827f8688315c2b0365810f12ac96.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-6/0d37436a8a1753f1e201f752643711e54afa827f8688315c2b0365810f12ac96.jsonl); 216 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ed6d7dfedf18cceabbb4ad8c06d1194accd1a86c40bad3d2b0b4c02f42da2889`.

## RAN4_P2_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 agenda items by number of resolutions (busiest agenda items).

**Revised question:** Return top10 agenda-number groups by distinct Resolution-node count, ties by agenda number ascending; return all if fewer than10 exist. Return named records with agendaNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Paired output and distinct unit; explicitly aggregate same agenda numbers across meetings and fix boundary ties.

**Original query**

```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS cnt ORDER BY cnt DESC LIMIT 10
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ1-8/1a56a6d101029765d1ba52d9791665609bcc1083166a9a92120ee7423a9e94a4.json), [complete native rows](../reference_outputs/RAN4_P2_CQ1-8/1a56a6d101029765d1ba52d9791665609bcc1083166a9a92120ee7423a9e94a4.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6514784eae4e2ba552a566741b196a0e2dfd6b0038a48ad7cc160ca3a3b53387`.

## RAN4_P2_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TDocs are referenced by 3 or more resolutions? (frequently cited documents).

**Revised question:** List all distinct TDoc identifiers referenced by at least three distinct Resolution nodes. Return named records with tdocNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Threshold counts distinct resolutions; remove cap and unnecessary output reference count.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.json), [complete native rows](../reference_outputs/RAN4_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.jsonl); 28 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `cd692d6b11c540f742ecde61534604a3d45d88a9961919e22c585976e108946d`.

## RAN4_P2_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which resolutions reference 5 or more TDocs? (broad-scope decisions).

**Revised question:** List all distinct Resolution identifiers referencing at least five distinct TDoc nodes. Return named records with resolutionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove the unrequested MADE_AT meeting requirement and row cap; count distinct TDoc nodes for the original threshold without excluding qualifying meeting-unlinked Resolutions.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.json), [complete native rows](../reference_outputs/RAN4_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.jsonl); 465 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e306da71eb54e0ab0ad2582c75a403501e63010804a80ab0911280810f50c045`.

## RAN4_P2_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find resolutions whose text cites R4- TDocs (in-text reference check).

**Revised question:** List all distinct Resolution identifiers whose recorded content contains a token shaped as R4- followed by one or more digits, bounded on each side by the string boundary or a character other than a letter, digit, underscore or hyphen. Return named records with resolutionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Define token boundaries to exclude embedded XR4-123 and R4-123abc fragments. A textual token is not independently certified as a graph REFERENCE or known real-world document; remove unrequested cap.

**Original query**

```cypher
MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '.*R4-.*' RETURN r.resolutionId, r.content ORDER BY r.resolutionId LIMIT 5
```

**Revised query**

```cypher
MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '(?s).*(?<![A-Za-z0-9_-])R4-[0-9]+(?![A-Za-z0-9_-]).*' RETURN DISTINCT r.resolutionId AS resolutionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ2-3/7953a0156b6b6511ec58b4a137da59a704feb3136c195c9563e5fab4614ce9b3.json), [complete native rows](../reference_outputs/RAN4_P2_CQ2-3/7953a0156b6b6511ec58b4a137da59a704feb3136c195c9563e5fab4614ce9b3.jsonl); 1,073 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `28c56823fa0b5cf438d9f05ff4120dcc662aa762d0eb8cda2b2bd36944038065`.

## RAN4_P2_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 specs by resolution-linked TDocs (spec decision activity).

**Revised question:** Among all recorded specification-number groups, return the top ten by count of distinct Resolution-referenced TDoc nodes modifying that specification number, including zero-count groups. Rank count descending then specNumber ascending; return all specification-number groups if fewer than ten exist. Return named records with specNumber, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove unrequested meeting-linked Resolution restriction. Preserve all recorded specification-number groups including zero eligible TDocs; explicit distinct-node counts and deterministic exact-top-ten ties.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Spec) OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s) RETURN s.specNumber AS specNumber,count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC,specNumber ASC LIMIT 10
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
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "tdocCount"
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
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ2-4/d17ac7cedc68cee871df676ee762197209eac4faf1797e4f84e17b390f189489.json), [complete native rows](../reference_outputs/RAN4_P2_CQ2-4/d17ac7cedc68cee871df676ee762197209eac4faf1797e4f84e17b390f189489.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `9468c127efac2a067e77dd58b4616236229dee01b528e09565d9a07e2c5853e9`.

## RAN4_P2_CQ3-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What share of Samsung's TDocs led to resolutions? (contribution success rate).

**Revised question:** Return fraction of Samsung's distinct submitted TDoc nodes referenced by at least one recorded Resolution; return null if there are no Samsung-submitted TDocs. Return named records with referencedFraction. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original does not compute share and counts resolutions rather than referenced TDocs; correct numerator/denominator and limit causal led-to wording to recorded references.

**Original query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(t) RETURN count(DISTINCT t) AS totalTdocs, count(DISTINCT r) AS resolutionLinkedTdocs
```

**Revised query**

```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) WITH collect(DISTINCT t) AS docs RETURN CASE WHEN size(docs)=0 THEN null ELSE toFloat(size([d IN docs WHERE EXISTS { MATCH (:Resolution)-[:REFERENCES]->(d) }]))/size(docs) END AS referencedFraction
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "referencedFraction",
      "nullable": true,
      "source_column_or_expression": "referencedFraction",
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ3-1/ba97e977a89f9bf0df7423480ee5abdacbd7e62b2f9aecd393408e4714fae201.json), [complete native rows](../reference_outputs/RAN4_P2_CQ3-1/ba97e977a89f9bf0df7423480ee5abdacbd7e62b2f9aecd393408e4714fae201.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `0899f8c158df2620082ddc09ac001b07da366a6f8fccbdd3d2858fdf6cf9f965`.

## RAN4_P2_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 companies by resolution contributions (leading decision contributors).

**Revised question:** Return top10 company names by number of distinct Resolutions referencing their submitted TDocs, ties by company name ascending; return all if fewer than10 exist. Return named records with companyName, resolutionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Recorded reference count operationalizes contribution, complete pair and original deterministic ties.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ3-2/32b4923de3bef2ae9f5fd77ad9d9c6a24e7077015f220f2a0cfaaa43205208f3.json), [complete native rows](../reference_outputs/RAN4_P2_CQ3-2/32b4923de3bef2ae9f5fd77ad9d9c6a24e7077015f220f2a0cfaaa43205208f3.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c090c3dbbb97ec6e9b93590d3d898aef9e532eb7212df3af031a343e44b0007a`.

## RAN4_P2_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** Original main/leading contribution importance or specification ownership is not independently established by a TDoc count. The revised task defines only an explicit stored documentary association metric.

**Original question:** Rank the leading contributors to spec 38.133 (key contributors to a spec).

**Revised question:** Rank all qualifying company-name groups by the count of distinct submitted TDoc nodes referenced by at least one Resolution and modifying specification 38.133. A company-name group qualifies when at least one such TDoc is recorded. Rank count descending then company name ascending. Return named records with companyName, tdocCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** The original main/leading contributor and ownership notion has no independently validated contribution-quality metric. Define complete positive-match company-name groups ranked by distinct documentary TDoc count as a substantive variant, remove the unrequested ten-row cap and preserve deterministic keys.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT t) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, companyName ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ3-3/6fbf08b4d99135f76a82f75bf7b81bbabdb79d98dd412848e54e8a142fb6a631.json), [complete native rows](../reference_outputs/RAN4_P2_CQ3-3/6fbf08b4d99135f76a82f75bf7b81bbabdb79d98dd412848e54e8a142fb6a631.jsonl); 30 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `7a27af338a53cce78daaaee4b313ad2d7ca961fc5bd37145345d6972ededffcb`.

## RAN4_P2_CQ6-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original agenda-to-meeting identity and calendar-time interpretation are not independently validated. The revised task explicitly uses the stored RAN4# plus AgendaItem.meetingNumber equality and requires matching Resolution MADE_AT links.

**Original question:** Show the resolution-count trend for agenda item 6.6.3 over time (topic activity trend).

**Revised question:** Select AgendaItems whose agendaNumber equals 6.6.3 or starts with 6.6.3. and pair them with a stored Meeting only when its canonicalMeetingNumber equals the literal RAN4# concatenated with that AgendaItem's recorded meetingNumber string. For each matched Meeting, count distinct Resolution nodes both RESOLUTION_BELONGS_TO-linked to one of these agendas and MADE_AT-linked to that Meeting, including zero. Order by integer meeting number then canonical meeting identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Expose the exact agenda-to-canonical-Meeting string-key join and Resolution MADE_AT agreement requirement. Preserve zero counts for matching agenda/Meeting instances and deterministic numeric order; this formal key-based variant is not an independently validated calendar-time or agenda identity alignment.

**Original query**

```cypher
MATCH (ai:AgendaItem) WHERE ai.agendaNumber = '6.6.3' OR ai.agendaNumber STARTS WITH '6.6.3.' MATCH (m:Meeting) WHERE m.canonicalMeetingNumber ENDS WITH ('#' + ai.meetingNumber) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) WITH m, count(DISTINCT r) AS cnt RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, cnt ORDER BY mNum ASC
```

**Revised query**

```cypher
MATCH (ai:AgendaItem) WHERE ai.agendaNumber='6.6.3' OR ai.agendaNumber STARTS WITH '6.6.3.' MATCH (m:Meeting) WHERE m.canonicalMeetingNumber='RAN4#'+ai.meetingNumber OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai), (r)-[:MADE_AT]->(m) WITH m,count(DISTINCT r) AS resolutionCount RETURN m.canonicalMeetingNumber AS meeting,m.meetingNumberInt AS meetingNumber,resolutionCount ORDER BY meetingNumber ASC,meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ6-1/94a0621424fbbdba0337acbe539de1261790005eb98153aaf88e0fdf65350318.json), [complete native rows](../reference_outputs/RAN4_P2_CQ6-1/94a0621424fbbdba0337acbe539de1261790005eb98153aaf88e0fdf65350318.jsonl); 16 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `10934e4edea7915910c88be3e3d3237ec380b088d356e57cbc72520f06e64efd`.

## RAN4_P2_CQ6-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show how Samsung's resolution contributions evolved over time (contributor trend).

**Revised question:** For each recorded meeting with a Resolution referencing Samsung-submitted TDocs, return meeting identifier, integer meeting number and distinct Resolution count; order by integer number then canonical identifier ascending. Return named records with meeting, meetingNumber, resolutionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Trend requires meeting/count records and deterministic base/bis order; no invented zero meetings or influence claim.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(DISTINCT r) AS cnt ORDER BY mNum ASC
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P2_CQ6-2/27e43e998a16bf6b100b598dfcd43ab9fc77ee4f0525d0a110455685ec777b27.json), [complete native rows](../reference_outputs/RAN4_P2_CQ6-2/27e43e998a16bf6b100b598dfcd43ab9fc77ee4f0525d0a110455685ec777b27.jsonl); 20 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `d0e5ac1872394d22b25aaf5893cb4943af515d4e1fe6e4f239e9b8652501e33e`.

## RAN4_P3_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections of spec 38.133 (spec structure browsing).

**Revised question:** List all distinct Section identifiers,numbers,titles and levels in every recorded edition of specification38.133. Return named records with sectionId, sectionNumber, title, level. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove25 cap and state edition-aware full structure.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-1/5fa7c8ccb94f48177232d2f56b215740d881eca85f67e52edbca3936cee07f2e.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-1/5fa7c8ccb94f48177232d2f56b215740d881eca85f67e52edbca3936cee07f2e.jsonl); 32,888 native rows retained. The retained per-item check record has 16 passing scorer checks for this definition.

**Definition SHA-256:** `c6eb036ab3b4c49991284c2477458db6fb4611395a3ee97c8a0ea2e0167c935d`.

## RAN4_P3_CQ1-10

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Find the spec and section that hold table 4.3-1 (reverse table lookup).

**Revised question:** List all distinct specification-number and Section-identifier pairs containing a TSTable numbered4.3-1. Return named records with specNumber, sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Both requested output roles required; caption unrequested and arbitrary10 cap removed.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber: '4.3-1'}) RETURN sp.specNumber, sec.sectionId, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber: '4.3-1'}) RETURN DISTINCT sp.specNumber AS specNumber, sec.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-10/cb8214998e0cd21985faaf8f0f1509429ab061f0f78d252f6d0394593f8b42e6.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-10/cb8214998e0cd21985faaf8f0f1509429ab061f0f78d252f6d0394593f8b42e6.jsonl); 24 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4fc4d190842c718e7f96a4a3e1d9e360b60270551c703a6ca468e26a6fcde863`.

## RAN4_P3_CQ1-11

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-2 sections of spec 38.104 (base-station spec structure).

**Revised question:** List all distinct Section identifiers,numbers and titles at level2 in every recorded edition of specification38.104. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full inventory with explicit edition scope, no25 cap.

**Original query**

```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.104'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.104'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-11/da13ec14dcf7272fdf82e285265751a6a10078c778ccf188430e90227c66bae1.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-11/da13ec14dcf7272fdf82e285265751a6a10078c778ccf188430e90227c66bae1.jsonl); 331 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `de165b905f6dadb85a1aeb253ee559c37222ae1495a9c48e38445dbfb7d217b6`.

## RAN4_P3_CQ1-12

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sub-sections of section 6 in spec 38.101-1 (drilling into a clause).

**Revised question:** List all distinct immediate child Section identifiers,numbers and titles linked by HAS_SUB_SECTION from section6 of every recorded edition of specification38.101-1. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Clarify immediate children and recorded editions; remove unstated latest1 and25 limits. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'6'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'6'})-[:HAS_SUB_SECTION]->(c:Section) RETURN DISTINCT c.sectionId AS sectionId,c.sectionNumber AS sectionNumber,c.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-12/93ca3d2f7a3b3786104824d2ba8b574e2736a026792a2ee352d040118397714e.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-12/93ca3d2f7a3b3786104824d2ba8b574e2736a026792a2ee352d040118397714e.jsonl); 211 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `bfa9f826043fd939ddbf905582b5469f63ba12bf6eae46899ff5dd41ba2f8536`.

## RAN4_P3_CQ1-13

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the void sections of spec 38.133 (identifying deprecated clauses).

**Revised question:** List all distinct Section identifiers,numbers and titles with recorded isVoid=true in every recorded edition of specification38.133. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Void source marker is not independent deprecated status; remove25 cap and preserve source flag.

**Original query**

```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-13/eb148e9218aedc8f2c342da34d4c712992be9ef212639d373aee7c2c16b71c33.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-13/eb148e9218aedc8f2c342da34d4c712992be9ef212639d373aee7c2c16b71c33.jsonl); 754 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `f16db07feed1c95a5d04914a71eab5bade757d46872d776a388000503fbb5708`.

## RAN4_P3_CQ1-15

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-3 sections of spec 38.133 (deep-structure browsing).

**Revised question:** List all distinct Section identifiers and titles at level3 in every recorded edition of specification38.133. Return named records with sectionId, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full level3 inventory, no25 cap and section ID preserves edition.

**Original query**

```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-15/39f1fe757069acc1e57a79b4a02b641e1447761d832f92225064cebd659c5ce5.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-15/39f1fe757069acc1e57a79b4a02b641e1447761d832f92225064cebd659c5ce5.jsonl); 5,447 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `b16d07b9c14d1debc331a0db29c7f9de91fe49b5a77f899ed5b5e4bc7356e572`.

## RAN4_P3_CQ1-16

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 5 RAN4 specs by section count (largest specs).

**Revised question:** Return top5 specification numbers by count of distinct linked Section nodes across recorded editions, ties by specNumber ascending; return all if fewer than5 exist. Return named records with specNumber, sectionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Complete record, distinct unit and deterministic boundary.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-16/9d2a11cc7c4b434a3ccce19916d796b9afdd6603cab1b27c6fae20f9c6156fc7.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-16/9d2a11cc7c4b434a3ccce19916d796b9afdd6603cab1b27c6fae20f9c6156fc7.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `0e5b67127ce6c3a4431f02ad8729f70cac11fe4e3800e8511f06952c678a63e4`.

## RAN4_P3_CQ1-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sub-sections of section 10.1 in spec 38.133 (drilling into a clause).

**Revised question:** List all distinct immediate child Section identifiers,numbers and titles linked by HAS_SUB_SECTION from section10.1 of every recorded edition of specification38.133. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove silent latest1 and25 limits; immediate-child meaning and edition scope explicit. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'10.1'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'10.1'})-[:HAS_SUB_SECTION]->(c:Section) RETURN DISTINCT c.sectionId AS sectionId,c.sectionNumber AS sectionNumber,c.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-2/5c7be07cb1802541b3a7f85c71221155a78c471609c8506efc613461a962de1a.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-2/5c7be07cb1802541b3a7f85c71221155a78c471609c8506efc613461a962de1a.jsonl); 282 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `59a5c62c0ab860b12ebcbde4cb5319715ee3b4b7ead449c1ebdf925468ac7cf8`.

## RAN4_P3_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the level-1 sections of spec 38.133 (top-level structure).

**Revised question:** List all distinct Section identifiers,numbers and titles at level1 in every recorded edition of specification38.133. Return named records with sectionId, sectionNumber, title. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original population retained, edition-aware complete named structure.

**Original query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

**Revised query**

```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-4/710a8343aa7131ddb9a3f0398cf832920592601521defa82b74e372e2a046e8d.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-4/710a8343aa7131ddb9a3f0398cf832920592601521defa82b74e372e2a046e8d.jsonl); 190 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `ce21f5f9943e5b5d43989f0c1dbe4ebc9a23482b12d7759a8b73443728dba718`.

## RAN4_P3_CQ1-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the tables in section 9.2.5.1 of spec 38.133 (locating requirement tables).

**Revised question:** List all distinct TSTable identifiers,numbers and captions in section9.2.5.1 of every recorded edition of specification38.133. Return named records with tableId, tableNumber, caption. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full table inventory cannot retain silent latest1 or25 caps; edition-distinct table ID. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'9.2.5.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'9.2.5.1'})-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId,t.tableNumber AS tableNumber,t.tableCaption AS caption
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-5/d959419344c51dce18517ebb78aa1f8118f03d25752fae55703f0b17aaf49e4d.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-5/d959419344c51dce18517ebb78aa1f8118f03d25752fae55703f0b17aaf49e4d.jsonl); 70 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `757a5c775e6a96065094ceca02a6c82e5607a88c2912b77816fe41aba6bb5449`.

## RAN4_P3_CQ1-6

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the figures in section J.3 of spec 38.141-2 (locating test-setup figures).

**Revised question:** List all distinct TSFigure identifiers,numbers and captions in sectionJ.3 of every recorded edition of specification38.141-2. Return named records with figureId, figureNumber, caption. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove unstated latest1 and15 limits; identifier preserves edition and all requested inventory fields. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.141-2'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'J.3'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN f.figureId, f.figureNumber, f.figureCaption ORDER BY f.figureNumber LIMIT 15
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.141-2'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'J.3'})-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN DISTINCT f.figureId AS figureId,f.figureNumber AS figureNumber,f.figureCaption AS caption
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-6/6f16c2d85698964d061df1c9a1c9647a7e847a5d268f15e2920af5c96d29148a.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-6/6f16c2d85698964d061df1c9a1c9647a7e847a5d268f15e2920af5c96d29148a.jsonl); 35 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `09998fb868226badba9c8a1e44b804c2aaa07b1087663d24de74989643788100`.

## RAN4_P3_CQ1-7

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** Which section of spec 38.101-1 contains table 5.2-1? (locating a table's context).

**Revised question:** List all distinct Section identifiers containing TSTable number5.2-1 in every recorded edition of specification38.101-1. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original singular section cannot select unstated latest edition; define complete recorded-edition lookup. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(sec:Section)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber:'5.2-1'}) WHERE rk.specRelease IS NOT NULL WITH sec,t,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN sec.sectionId, sec.sectionNumber, sec.sectionTitle
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(sec:Section)-[:CONTAINS_TABLE]->(:TSTable {tableNumber:'5.2-1'}) RETURN DISTINCT sec.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-7/94ab205724a4c69eb4a8f737cd838dfe4e4b28477b9b61f3ff093854351c5c5b.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-7/94ab205724a4c69eb4a8f737cd838dfe4e4b28477b9b61f3ff093854351c5c5b.jsonl); 5 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `c78e77e4deb4ef0a2f8145764ad4ed6bb0b43a421f73e7bbb58a4dd3d19c2f2f`.

## RAN4_P3_CQ1-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List all tables in spec 38.101-1 (table inventory).

**Revised question:** List all distinct TSTable identifiers,numbers and captions in any recorded edition of specification38.101-1. Return named records with tableId, tableNumber, caption. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Explicit all inventory removes25 cap; edition-aware IDs.

**Original query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId, t.tableNumber AS tableNumber, t.tableCaption AS caption
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-8/460490eac1b6dd6bfd05caf66bb84d618a68922dcf6475a6dfa9b5972ddd8d55.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-8/460490eac1b6dd6bfd05caf66bb84d618a68922dcf6475a6dfa9b5972ddd8d55.jsonl); 3,001 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `6f1a6e77b3d872cae56ff62b22b1ca93f197abedde1aea70f5f2e4eb1ac57149`.

## RAN4_P3_CQ1-9

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections of spec 38.133 whose title contains 'measurement' (finding measurement clauses).

**Revised question:** List all distinct Section identifiers whose title contains measurement ignoring letter case in any recorded edition of specification38.133. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Question requests section search, no hidden title output or25 cap.

**Original query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN DISTINCT s.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ1-9/8be590a675244177678d50f12420c94952351f1755b8542914fd3e44ab185f4b.json), [complete native rows](../reference_outputs/RAN4_P3_CQ1-9/8be590a675244177678d50f12420c94952351f1755b8542914fd3e44ab185f4b.jsonl); 5,972 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `95cd81b7ffdf07b76c5349947768b71f51f76849007a0f98007143f6e11e2242`.

## RAN4_P3_CQ2-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sections referenced by section 3.2 of spec 38.101-1 (outbound cross-references).

**Revised question:** List all distinct target Section identifiers referenced from section3.2 in any recorded edition of specification38.101-1. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove silent latest1 and25 restrictions; requested target role. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(a:Section {sectionNumber:'3.2'}) WHERE rk.specRelease IS NOT NULL WITH a,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a)-[:REFERENCES_SECTION]->(b:Section) RETURN b.sectionId, b.sectionTitle ORDER BY b.sectionNumber LIMIT 25
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(a:Section {sectionNumber:'3.2'})-[:REFERENCES_SECTION]->(b:Section) RETURN DISTINCT b.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-1/7154bc0429d568249dd48ca0b0d737f8bb3468d49eb3a37b3d5284820139b9ad.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-1/7154bc0429d568249dd48ca0b0d737f8bb3468d49eb3a37b3d5284820139b9ad.jsonl); 19 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `3c79ade851c3b3831fb3865c06ae82db4fa8093f37021168a8b9b27c88b367a1`.

## RAN4_P3_CQ2-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.']

**Original question:** List the sections that reference section 4.2 of spec 38.133 (inbound cross-references).

**Revised question:** List all distinct source Section identifiers referencing section4.2 in any recorded edition of specification38.133. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove hidden latest1 and25 limits; source role explicit. The original question leaves the specification edition unspecified, while the stored query selects one latest edition. The revised task explicitly covers recorded editions; this supplied scope is a substantive variant and does not establish the original intended edition.

**Original query**

```cypher
MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(b:Section {sectionNumber:'4.2'}) WHERE rk.specRelease IS NOT NULL WITH b,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a:Section)-[:REFERENCES_SECTION]->(b) RETURN a.sectionId ORDER BY a.sectionId LIMIT 25
```

**Revised query**

```cypher
MATCH (:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(b:Section {sectionNumber:'4.2'})<-[:REFERENCES_SECTION]-(a:Section) RETURN DISTINCT a.sectionId AS sectionId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-2/23481646fbf852036635a45c91d1a7b89e97c7f326a3c6b1b3a9d1bf91a3c927.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-2/23481646fbf852036635a45c91d1a7b89e97c7f326a3c6b1b3a9d1bf91a3c927.jsonl); 619 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `ba40e61fef1b924d0d61c560e736e6a2cc5a0b260bf477c28ac2107ec1c8b554`.

## RAN4_P3_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 most-referenced sections (key referenced clauses).

**Revised question:** Return top10 Section identifiers by number of distinct referring Section nodes, ties by Section identifier ascending; return all if fewer than10 are referenced. Return named records with sectionId, referringSectionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Complete identifier/count pairs and distinct source-node unit.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC, b.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(DISTINCT a) AS refCount RETURN DISTINCT b.sectionId AS sectionId, refCount AS referringSectionCount ORDER BY referringSectionCount DESC, sectionId ASC LIMIT 10
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-3/381dcd6b0ac63113d07e0740dc0d7b1ec9f1f15f2bfae96808ae40d5163223e1.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-3/381dcd6b0ac63113d07e0740dc0d7b1ec9f1f15f2bfae96808ae40d5163223e1.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `55e01c4e36375ad7d28492f40b372fcfe3ae73d3cdb199cdcc0a27f84c0081b2`.

## RAN4_P3_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 sections that reference the most others (heaviest referencing clauses).

**Revised question:** Return top10 source Section identifiers by number of distinct target Section nodes they reference, ties by source identifier ascending; return all if fewer than10 reference others. Return named records with sectionId, referencedSectionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Others means distinct target Sections, not edge duplicates; paired count, deterministic ties.

**Original query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(DISTINCT b) AS outCount RETURN DISTINCT a.sectionId AS sectionId, outCount AS referencedSectionCount ORDER BY referencedSectionCount DESC, sectionId ASC LIMIT 10
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
      "name": "referencedSectionCount",
      "nullable": false,
      "source_column_or_expression": "referencedSectionCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referencedSectionCount"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-4/2088558948701a98cdc1696eb19664140533e6ae07e62ea1e3ce785f2f12a944.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-4/2088558948701a98cdc1696eb19664140533e6ae07e62ea1e3ce785f2f12a944.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `6caf2c415fe88c3d8f585a603a7bf418bab375dd90936982aad5e66f4fe3c044`.

## RAN4_P3_CQ2-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 cross-spec section-reference pairs (inter-spec dependency map).

**Revised question:** Return top10 source/target specification-number pairs by number of distinct REFERENCES_SECTION edges between sections of different specification numbers, ties by fromSpec then toSpec ascending; return all if fewer than10 pairs exist. Return named records with fromSpec, toSpec, referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original asks section-reference pairs but reference returns aggregated spec pairs; mark this explicit aggregate variant instead of disguising meaning change.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[reference:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN DISTINCT sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC, fromSpec ASC, toSpec ASC LIMIT 10
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
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-5/48cff97950ff1a9019233b213a5d54252433d0e5f764488782acb8a2031258b9.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-5/48cff97950ff1a9019233b213a5d54252433d0e5f764488782acb8a2031258b9.jsonl); 4 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `86712d1ee2e217caf1cd0d1d2ea3f3b89ba5c45e0149300570784bdfcf42889a`.

## RAN4_P3_CQ2-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 5 specs referenced by spec 38.101-1 (its main dependencies).

**Revised question:** Return top5 target specification numbers by distinct REFERENCES_SPEC-edge count from Sections belonging to specification38.101-1, ties by target specNumber ascending; return all if fewer than5 exist. Return named records with specNumber, referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Documentary-reference edges, not independently proven dependencies; paired counts and deterministic ties.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (a)-[reference:REFERENCES_SPEC]->(target:Spec) RETURN DISTINCT target.specNumber AS specNumber, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC, specNumber ASC LIMIT 5
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-6/b24cf4d830144f31a307abd615b283f53db6d62c4e5e3eca1f216a0d81557f09.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-6/b24cf4d830144f31a307abd615b283f53db6d62c4e5e3eca1f216a0d81557f09.jsonl); 4 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `cf3347ce12e72a296c7c062b34bee92456bd7d337876dfbcf9d19b8d4c379d4f`.

## RAN4_P3_CQ2-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 spec-to-spec reference pairs (inter-spec dependency map).

**Revised question:** Return top10 different source/target specification-number pairs by distinct REFERENCES_SPEC-edge count from source Sections, ties by fromSpec then toSpec ascending; return all if fewer than10 pairs exist. Return named records with fromSpec, toSpec, referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Spec-pair mapping roles and distinct documentary edge unit explicit; ties deterministic.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[reference:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN DISTINCT sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC, fromSpec ASC, toSpec ASC LIMIT 10
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
    "boundary_rule": "descending requested count then ascending named identifier; deterministic exact-k",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-7/bdbc3b71275dec63196f6fc8fc1bc81e9e81ba3f2a1182e3c54f49ee03760877.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-7/bdbc3b71275dec63196f6fc8fc1bc81e9e81ba3f2a1182e3c54f49ee03760877.jsonl); 10 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `011ba0d515f8e9258b4f8e9483daab1af98f99427db962e18c8f31ea2c8d6b98`.

## RAN4_P3_CQ2-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many internal cross-references does spec 38.133 have? (self-reference density).

**Revised question:** Count distinct REFERENCES_SECTION edges whose source and target Sections belong to the same recorded edition of specification38.133. Return named records with referenceEdgeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Distinct relationship unit avoids BELONGS_TO join multiplicity; within-edition meaning explicit.

**Original query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs
```

**Revised query**

```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}), (a)-[reference:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN DISTINCT count(DISTINCT reference) AS referenceEdgeCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ2-8/65a1357419982e1a3365158e6f9d58e4a7c63b16f23d7a95123b9fa7c6243057.json), [complete native rows](../reference_outputs/RAN4_P3_CQ2-8/65a1357419982e1a3365158e6f9d58e4a7c63b16f23d7a95123b9fa7c6243057.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `2b255550dc0432318807eec82366626b984d5c0322b962127431457734a62fa3`.

## RAN4_P3_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs does CR RP-240001 modify? (change-request impact lookup).

**Revised question:** List all distinct specification numbers linked by MODIFIES from a recorded CR with TDoc identifierRP-240001; return an empty set if no such link is recorded. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original query ignores requested CR completely and selects arbitrary first CR. Exact requested identifier restored; possible empty graph result is not an assertion that real-world CR does not exist.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WITH cr, sp ORDER BY cr.tdocNumber, sp.specNumber LIMIT 1 MATCH (cr2:CR {tdocNumber: cr.tdocNumber})-[:MODIFIES]->(sp2:Spec) RETURN cr2.tdocNumber, sp2.specNumber ORDER BY cr2.tdocNumber, sp2.specNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (:CR {tdocNumber:'RP-240001'})-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-1/cac60839e586087fc6946ad604266d3665d1c3e9dc6594156e3af8475335f59a.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-1/cac60839e586087fc6946ad604266d3665d1c3e9dc6594156e3af8475335f59a.jsonl); 0 native rows retained. The retained per-item check record has 3 passing scorer checks for this definition.

**Definition SHA-256:** `61aa79dbdf0c0e2210ac819bd23165120a3f961c405bc9bf1c3a2b07352be351`.

## RAN4_P3_CQ3-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** ['The original question does not specify a specification edition, while its stored query selects the latest recorded release. The revised canonical task explicitly aggregates all recorded editions; that supplied edition scope does not establish the intended edition of the original question.']

**Original question:** How many CRs modify spec 38.133, and how many sections does it have? (change load vs spec size).

**Revised question:** Return count of distinct CR nodes modifying specification38.133 and count of distinct Section nodes belonging to any recorded edition of that specification. Return named records with crCount, sectionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Use independent distinct CR and all-recorded-edition Section aggregates, avoiding hidden latest-only section selection and join multiplication. Optional Section match retains one zero-count record even if no Section exists. The supplied all-recorded-edition scope is an explicit new task choice, not a claim that the original edition semantics were verified.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.133'}) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber, crCount, count(s) AS sectionCount
```

**Revised query**

```cypher
OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.133'}) WITH count(DISTINCT cr) AS crCount OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.133'}) RETURN crCount,count(DISTINCT s) AS sectionCount
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
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-2/5c4922bf273bace6767ee670a02eeba427bcb071c8ae0c329f471085207099ae.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-2/5c4922bf273bace6767ee670a02eeba427bcb071c8ae0c329f471085207099ae.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `8673e776c3d127a27276799c784de8fea5d7f3f3094828003c15c5417618b6a9`.

## RAN4_P3_CQ3-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 CRs that modify spec 38.133 (recent changes to the spec).

**Revised question:** Return up to10 distinct CR TDoc identifiers modifying specification38.133 in descending lexical TDoc-identifier order. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original recent changes uses lexical IDs rather than upload timestamps; make that explicit alternate ordering task, not verified temporal recency.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT cr.tdocNumber AS crTdoc ORDER BY crTdoc DESC LIMIT 10
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
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "crTdoc"
      }
    ],
    "tie_policy": "deterministic_all_keys"
  },
  "cardinality_policy": {
    "boundary_rule": "lexical TDoc identifier descending",
    "mode": "top_k",
    "short_population": "all available",
    "tie_policy": "exact_k",
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-3/3c934444b9d299a714bce422c6c527aa952a26cc30241bbdc48ae6fe355e1e8f.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-3/3c934444b9d299a714bce422c6c527aa952a26cc30241bbdc48ae6fe355e1e8f.jsonl); 10 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `47c201adb23ca1d5916019097a0e5fbd9861813dd47289072aeaecd41e5ee9f7`.

## RAN4_P3_CQ3-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original actual impact on normative clause4.2 is not independently established. The revised task is an exact comma-token equality/prefix filter on clausesAffected metadata; it does not interpret free-form clause ranges or certify normative effects.

**Original question:** List CRs on spec 38.133 that touch clause 4.2 (clause-level change filter).

**Revised question:** List all distinct CR TDoc identifiers modifying specification 38.133 whose comma-separated affected-clause text includes a trimmed token equal to '4.2' or with prefix '4.2.'. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original substring matches unrelated10.1.14.2 and similar numbers. Explicit clause-token/subclause predicate and no cap; do not claim free-form range interpretation. The literal metadata selector is a substantive variant of actual clause-impact interpretation, which remains unresolved.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) WHERE cr.clausesAffected CONTAINS '4.2' RETURN cr.tdocNumber, cr.clausesAffected ORDER BY cr.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.133'}) WHERE cr.clausesAffected IS NOT NULL AND any(raw IN split(cr.clausesAffected,',') WHERE trim(raw)='4.2' OR trim(raw) STARTS WITH '4.2.') RETURN DISTINCT cr.tdocNumber AS crTdoc
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-4/d4f6760b80ab47f34750f507536de3e3123fb91d5c81ab92e0e636ba03e9a8e1.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-4/d4f6760b80ab47f34750f507536de3e3123fb91d5c81ab92e0e636ba03e9a8e1.jsonl); 57 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `e813588cfdb3951faf647873ebfd6dfb24d8851a15a19f147d5324597edaeba7`.

## RAN4_P3_CQ3-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs modified by CRs under Work Item NR_newRAT-Perf (work-item change footprint).

**Revised question:** List all distinct specification numbers modified by CRs linked to Work ItemNR_newRAT-Perf. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested spec inventory only, unrequested supporting CR counts and10 cap removed.

**Original query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-5/61271e0ef19525415f50675e8b317d0201998e3ca14ffe20876fb2b15f641dbe.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-5/61271e0ef19525415f50675e8b317d0201998e3ca14ffe20876fb2b15f641dbe.jsonl); 31 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `3bcaf55c76ff3aae04a94a03455e8c57a66390727a8a39891aae9b6bd0ebc534`.

## RAN4_P3_CQ3-6

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many CRs did Huawei submit against spec 38.133? (per-company change count).

**Revised question:** Count distinct Huawei-submitted CR nodes modifying specification38.133. Return named records with crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Document unit rather than join matches.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN count(cr) AS crCount
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-6/71ef717945c874dad96096cc0705c81b6b0ece3bd9f4ebc616a5e76e1a4fab8e.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-6/71ef717945c874dad96096cc0705c81b6b0ece3bd9f4ebc616a5e76e1a4fab8e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `bb7441a62155aa28a4d3456a04dfef7ce8ece8ed1add48876f2ce3d8038626b5`.

## RAN4_P3_CQ3-7

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 companies that modify spec 38.133 the most (leading change contributors).

**Revised question:** Return top10 company names by distinct submitted CR-node count modifying specification38.133, ties by company name ascending; return all if fewer than10 exist. Return named records with companyName, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Complete company/count roles and deterministic ties, distinct CR unit.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, companyName ASC LIMIT 10
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-7/f59825ca33d729f1e0a727058c6bf6cf3f222cdaa664bc08c92a68009e4345bd.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-7/f59825ca33d729f1e0a727058c6bf6cf3f222cdaa664bc08c92a68009e4345bd.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `c5f74ad92503fa14b583040ad5f44cb54f428bd59315aa8408973a05109d71ee`.

## RAN4_P3_CQ3-8

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many Rel-18 CRs modify spec 38.133? (release-scoped change count).

**Revised question:** Count distinct CR nodes targetingRel-18 and modifying specification38.133. Return named records with crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Both original scope filters retained; distinct CR unit prevents duplicate paths.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) RETURN count(cr) AS crCount
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ3-8/5f8138755f013cb46e5276b70cfb95644673736b95f875b4384a4eddfb52708e.json), [complete native rows](../reference_outputs/RAN4_P3_CQ3-8/5f8138755f013cb46e5276b70cfb95644673736b95f875b4384a4eddfb52708e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `94a3da91d3aa79520c332349ef536574c8c9261066db9f5142dfc52c9a9f7980`.

## RAN4_P3_CQ4-1

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the resolutions and the approved CRs that modify spec 38.133 (decision-to-change trace).

**Revised question:** List all distinct Resolution-identifier and CR-TDoc pairs where a Resolution references a CR modifying specification38.133. Return named records with resolutionId, crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** REFERENCES does not prove approval; explicit documentary variant and cap removed.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT r.resolutionId AS resolutionId, cr.tdocNumber AS crTdoc
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ4-1/4519b3fb809114e486b73c793089e0c8fbd5d721a586695d67807218fbf0064b.json), [complete native rows](../reference_outputs/RAN4_P3_CQ4-1/4519b3fb809114e486b73c793089e0c8fbd5d721a586695d67807218fbf0064b.jsonl); 1,766 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5801374ca695be71450e4df031ef33b393ae77a5980d06674c37490aaeec9587`.

## RAN4_P3_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many resolutions approved CRs that modify spec 38.133? (decision volume for a spec).

**Revised question:** Count distinct recorded Resolutions referencing at least one CR that modifies specification38.133. Return named records with resolutionCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original approval unsupported; reference-association count is defined without causal/approval certification.

**Original query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(DISTINCT r) AS resolutionCount
```

**Revised query**

```cypher
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT count(DISTINCT r) AS resolutionCount
```

**Scoring contract**

```json
{
  "required_fields": [
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
    "mode": "exact",
    "value": 1
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ4-2/6cf6af72538bf5c034ebc1f75e36cde4b7d53ddcf70a48439a0660a6e8d27434.json), [complete native rows](../reference_outputs/RAN4_P3_CQ4-2/6cf6af72538bf5c034ebc1f75e36cde4b7d53ddcf70a48439a0660a6e8d27434.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `484a901314abed5eed671175089bf012f5918eaef9a500735e4eb380e2e34621`.

## RAN4_P3_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** How many CRs presented at RAN4#111 modify spec 38.133? (meeting-scoped change count).

**Revised question:** Count distinct CR nodes presented at canonical meetingRAN4#111 and modifying specification38.133. Return named records with crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Canonical meeting identity and distinct CR count.

**Original query**

```cypher
MATCH (m:Meeting {meetingNumber: 'RAN4#111'})<-[:PRESENTED_AT]-(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS crCount
```

**Revised query**

```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN4#111'})<-[:PRESENTED_AT]-(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ4-3/0a33390143b83c562b62279695586d43191ce6368b15ae37cb9ef8e6ed9aaf7e.json), [complete native rows](../reference_outputs/RAN4_P3_CQ4-3/0a33390143b83c562b62279695586d43191ce6368b15ae37cb9ef8e6ed9aaf7e.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `b56bf0d9a3e5978b154c5c2c4978fe062184c0d3bcc3bbba9aa2ef97c40bb915`.

## RAN4_P3_CQ4-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs reflect resolutions under Work Item NR_newRAT-Perf? (work-item outcome trace).

**Revised question:** List all distinct specification numbers modified by CRs linked toNR_newRAT-Perf and referenced by recorded Resolutions. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Reflect resolutions wording suggests influence; explicitly grade available documentary association and remove cap/unrequested count.

**Original query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)<-[:REFERENCES]-(r:Resolution), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS rCount ORDER BY rCount DESC, sp.specNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)<-[:REFERENCES]-(r:Resolution), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ4-4/7b9d9e4baeb2bc1e0df6d4231794954b6f520a012058a5d33bd6e2dd4178eb41.json), [complete native rows](../reference_outputs/RAN4_P3_CQ4-4/7b9d9e4baeb2bc1e0df6d4231794954b6f520a012058a5d33bd6e2dd4178eb41.jsonl); 14 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `53e913ab75b44f2c0f8c14a64e67cf4e393b3ec704c442016e981637cdafa684`.

## RAN4_P3_CQ5-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What is the total number of CRs modifying spec 38.133? (overall change volume).

**Revised question:** Count distinct CR nodes modifying specification38.133. Return named records with crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Count distinct CR nodes, not duplicate MODIFIES matches.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS totalCRs
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ5-1/a45b9a522fc44f431d07b76a369e1f12688648110f27db452a648a1a02e00671.json), [complete native rows](../reference_outputs/RAN4_P3_CQ5-1/a45b9a522fc44f431d07b76a369e1f12688648110f27db452a648a1a02e00671.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `624174f7a93fad8e147535d64506f54f20c5df2b10530cabde1286b37342cca1`.

## RAN4_P3_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List Huawei's top 5 specs by CR contributions (a company's change focus).

**Revised question:** Return top5 specification numbers by distinct Huawei-submitted CR-node count, ties by specification number ascending; return all if fewer than5 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full pair, distinct CR unit and deterministic ties.

**Original query**

```cypher
MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5
```

**Revised query**

```cypher
MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 5
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ5-2/67c4f7f5f803e837e56f580f6eb566d2b2ffe5893894bc56c7dc7ce029eddda0.json), [complete native rows](../reference_outputs/RAN4_P3_CQ5-2/67c4f7f5f803e837e56f580f6eb566d2b2ffe5893894bc56c7dc7ce029eddda0.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `94fd906d55be90a24c5db81b4d8fe103fd6f6a8f81006eff9d58cfc1a5cfe6b2`.

## RAN4_P3_CQ5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 specs changed in Rel-18 (release change scope).

**Revised question:** Return top10 specification numbers by distinct modifying CR-node count targetingRel-18, ties by specNumber ascending; return all if fewer than10 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original question does not impose hidden38.1 prefix; remove that scope restriction and fix distinct count/ties.

**Original query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.1' RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, specNumber ASC LIMIT 10
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
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ5-3/dda835d8257909265d9f5966ab312c472a11af2be067b7a113322b2c3a688684.json), [complete native rows](../reference_outputs/RAN4_P3_CQ5-3/dda835d8257909265d9f5966ab312c472a11af2be067b7a113322b2c3a688684.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `1bd064cd70ee2a3d1b08d9f8d9559a198bbb457e6d231f1437e02e42218c579f`.

## RAN4_P3_CQ5-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 RAN4 specs with the most CRs (most-revised specs).

**Revised question:** Return top10 specification numbers in the RAN4 graph by number of distinct modifying CR nodes, ties by specNumber ascending; return all if fewer than10 exist. Return named records with specNumber, crCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Remove unrequested38.1 prefix/latest-edition/Section existence restrictions; dataset graph membership does not certify WG ownership.

**Original query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(hub:Spec) WHERE hub.specRelease IS NULL AND hub.specNumber STARTS WITH '38.1' WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber, crCount, count(s) AS sectionCount ORDER BY crCount DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS specNumber,count(DISTINCT cr) AS crCount ORDER BY crCount DESC,specNumber ASC LIMIT 10
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
    "value": 10
  }
}
```

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_CQ5-4/2d395886773f61d02e1e87cfa9066f276c2a6889ba6c1cb50322c3e1af5f82bf.json), [complete native rows](../reference_outputs/RAN4_P3_CQ5-4/2d395886773f61d02e1e87cfa9066f276c2a6889ba6c1cb50322c3e1af5f82bf.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `5f1cb20f912c35da10804278a81130c08d8fb5d36d17fe1af70d21a299af71cc`.

## RAN4_P3_P3-S8-CQ02

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Are all item-level entity nodes linked to a Section via definedInSection? (grounding-coverage check).

**Revised question:** For recorded item-granularity nodes with any of the five labels RRCParameter,CapabilityItem,Procedure,PerformanceRequirement,ConformanceTest, report population size, number lacking definedInSection to a Section and whether every node has the link; allLinked is vacuously true for empty population. Return named records with itemCount, unlinkedCount, allLinked. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original Boolean question not answered by class key. Explicit population, distinct counting across labels and empty universal interpretation.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.json), [complete native rows](../reference_outputs/RAN4_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `99223f3b62b7bcd702a93d71d0aa1237bd426640c74da691c4665624e920a6c2`.

## RAN4_P3_P3-S8-CQ05

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Show the granularity distribution across the five entity classes (item-level vs section-level split).

**Revised question:** For each present class label among RRCParameter,CapabilityItem,Procedure,PerformanceRequirement,ConformanceTest and each recorded granularity value, return class,granularity and distinct-node count; a multi-label node contributes to each applicable class and missing granularity is&lt;unset&gt;. Return named records with class, granularity, nodeCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original first-label choice arbitrary; output complete class/granularity/count distribution with explicit multi-membership.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P3_P3-S8-CQ05/8b13f8809202000e821936d9a2a2c291e97b91dc8a6e72af90e2563a9144dddf.json), [complete native rows](../reference_outputs/RAN4_P3_P3-S8-CQ05/8b13f8809202000e821936d9a2a2c291e97b91dc8a6e72af90e2563a9144dddf.jsonl); 2 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `7ba4ffa67322513896e827be98c70a2e3de0ad944028037ea0e399b5a17bcb07`.

## RAN4_P4_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by CR R4-2207489 (cross-spec impact assessment).

**Revised question:** List distinct specification numbers affected by CRR4-2207489 through AFFECTS_CORE_SPEC,AFFECTS_TEST_SPEC,AFFECTS_OM_SPEC, excluding specification numbers the same CR directly MODIFIES. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Other requires exclusion of direct modified-spec numbers; grade requested target numbers.

**Original query**

```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R4-2207489' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (c:CR {tdocNumber:'R4-2207489'})-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(direct:Spec) WHERE direct.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ2-1/c54302327dff417bfd0e6696ad90a669d5dc4a6a9f640a1df6c9836080ff87a8.json), [complete native rows](../reference_outputs/RAN4_P4_CQ2-1/c54302327dff417bfd0e6696ad90a669d5dc4a6a9f640a1df6c9836080ff87a8.jsonl); 2 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1649eac648ec5883fbfeea6a23c0201de5c79573effc34f9ae6acaac013adb5b`.

## RAN4_P4_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which CRs modifying spec 38.133 also affect other specs? (ripple-effect screening).

**Revised question:** List all distinct CR TDoc identifiers modifying specification38.133 and having an AFFECTS_CORE_SPEC,AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC edge to another specification number. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original exists predicate doesn't check different spec; add predicate and remove cap.

**Original query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.133'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.133' } RETURN DISTINCT c.tdocNumber AS crTdoc
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ2-2/c29b785b4a86b768c8785d6ff44fa5c4c3a18aae71327b05c90e38a66eb994b4.json), [complete native rows](../reference_outputs/RAN4_P4_CQ2-2/c29b785b4a86b768c8785d6ff44fa5c4c3a18aae71327b05c90e38a66eb994b4.jsonl); 1,379 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `111a5ab7ef67193f6909bf63944328186fb95117152bdd8c913f84185e605c66`.

## RAN4_P4_CQ2-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs that flag spec 38.533 as affected (inbound cross-spec impact).

**Revised question:** List all distinct CR TDoc identifiers flagging specification38.533 through any of the three AFFECTS relations. Return named records with crTdoc. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested CR inventory, summary unrequested, ten cap removed.

**Original query**

```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ2-3/cb42beb3bf4ac0bba10cc591a6a61bbb50934596a0fd17207984c2027d89b03f.json), [complete native rows](../reference_outputs/RAN4_P4_CQ2-3/cb42beb3bf4ac0bba10cc591a6a61bbb50934596a0fd17207984c2027d89b03f.jsonl); 1,515 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `6d0e8378d0cc8192c990db34bf33c550bf87aa810420b7fa116082b22bdcfa7e`.

## RAN4_P4_CQ2-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 10 CRs by number of cross-spec impacts (widest-reaching changes).

**Revised question:** Return the top ten CR TDoc identifiers by the number of distinct specification numbers reached through recorded AFFECTS_CORE_SPEC, AFFECTS_TEST_SPEC or AFFECTS_OM_SPEC links, excluding specification numbers directly MODIFIES-linked from the same CR. Include CRs with zero qualifying other-specification targets. Rank count descending then CR identifier ascending; return all CR identifiers if fewer than ten exist. Return named records with crTdoc, affectedSpecCount. Interpret the population and relationships relative to the frozen RAN4 graph.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ2-4/97bcca5bffb80563555c01cb11d9ff3df5cde00ec783d126a23b00561f7f5f2b.json), [complete native rows](../reference_outputs/RAN4_P4_CQ2-4/97bcca5bffb80563555c01cb11d9ff3df5cde00ec783d126a23b00561f7f5f2b.jsonl); 10 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `e59718a10b5b4a0f9823affe77b8740fec510f1276ca04fe83a7575442b0be7f`.

## RAN4_P4_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CRs in CR pack RP-233366 with their change summaries (CR-pack contents review).

**Revised question:** List all distinct CR TDoc identifiers and recorded change-summary values linked by HAS_CR from CRPackRP-233366. Return named records with crTdoc, summary. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full pack contents require ID/summary pairs and explicit nullable source values; no ten cap.

**Original query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-233366'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack {crPackId: 'RP-233366'})-[:HAS_CR]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.summaryOfChange AS summary
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ3-1/5093835e886b550086016b706ce91cd73b33cc34fe156a0a2efb2b04cfed324c.json), [complete native rows](../reference_outputs/RAN4_P4_CQ3-1/5093835e886b550086016b706ce91cd73b33cc34fe156a0a2efb2b04cfed324c.jsonl); 60 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `4e3f4682eaa30775408092a714d48fbc40853136fa7817a59f2314f7f069b0ca`.

## RAN4_P4_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which CR packs contain CRs for NR_newRAT work items? (work-item packaging trace).

**Revised question:** List all distinct CRPack identifiers containing CRs whose linked Work Item codes contain NR_newRAT. Return named records with crPackId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Full pack inventory, no cap or unrequested optional meeting field.

**Original query**

```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.json), [complete native rows](../reference_outputs/RAN4_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.jsonl); 158 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `6970b81f217ffda6429c030c945c7b3e9a7ea814117d23bf7b4428a4d41daa4a`.

## RAN4_P4_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the CR packs submitted to TSG meeting RAN#102 (plenary submission overview).

**Revised question:** List all distinct CRPack identifiers with recorded tsgMeeting equal toRAN#102. Return named records with crPackId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Retain exact recorded submission predicate, remove cap.

**Original query**

```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#102'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
```

**Revised query**

```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#102'}) RETURN DISTINCT pack.crPackId AS crPackId
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ3-3/779caef300dbef3010b49d498edd7a6d7e61c5884064cc711643b50fa1863c33.json), [complete native rows](../reference_outputs/RAN4_P4_CQ3-3/779caef300dbef3010b49d498edd7a6d7e61c5884064cc711643b50fa1863c33.jsonl); 35 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `1c89ebe76596b09ad51336e84abdda21ec22f323485bf2011f5e2395dd714493`.

## RAN4_P4_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the reasons-for-change of CRs that modify section 7.3A.5 of spec 38.101-1 (clause-level change rationale).

**Revised question:** List all distinct CR TDoc identifiers and recorded change-reason values linked by MODIFIES_SECTION to section7.3A.5 in any recorded edition of specification38.101-1. Return named records with crTdoc, reason. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Reasons must remain tied to CR identifiers; remove cap and retain recorded Section link.

**Original query**

```cypher
MATCH (sec:Section {sectionNumber: '7.3A.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (sec:Section {sectionNumber: '7.3A.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.reasonForChange AS reason
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ4-1/6db393492092580c33338361e82dfd8be703d7d10eb22109cc15a3a9a7c5283a.json), [complete native rows](../reference_outputs/RAN4_P4_CQ4-1/6db393492092580c33338361e82dfd8be703d7d10eb22109cc15a3a9a7c5283a.jsonl); 123 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `df6e5bc1aa0565a4ff63850fb8148f6868bcd87740665bf72463ca0203d584b0`.

## RAN4_P4_CQ4-2

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the reason and summary of change for CRs approved by agreements (decision-linked change review).

**Revised question:** Return distinct CR TDoc identifiers, recorded change reasons and summaries for all CRs referenced by Agreements. Return named records with crTdoc, reason, summary. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** REFERENCES does not establish approval; remove unrequested5 cap and nonnull reason filter, explicit nullable record values.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ4-2/243f05dac9640abd2647e0ab8dd5c5a1511b73779b7c1f621bf2b15d048c0801.json), [complete native rows](../reference_outputs/RAN4_P4_CQ4-2/243f05dac9640abd2647e0ab8dd5c5a1511b73779b7c1f621bf2b15d048c0801.jsonl); 3,672 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `c86bff17ca9688353600ed0c9a0ef57be0eec42b33887171284db1b551bfe1f3`.

## RAN4_P4_CQ4-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the sections modified by CRs under NR_newRAT work items (work-item change footprint).

**Revised question:** List all distinct Section identifiers linked by MODIFIES_SECTION from CRs whose Work Item code contains NR_newRAT. Return named records with sectionId. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested full Section footprint; remove cap.

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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json), [complete native rows](../reference_outputs/RAN4_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl); 4,274 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `7bc96750e00e6a80f14d560b55e1cd14b459e9e0706f3d85a96fe2befd456477`.

## RAN4_P4_CQ4-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the other specs affected by Samsung's CRs (a company's cross-spec footprint).

**Revised question:** List distinct specification numbers affected through the three AFFECTS relations by Samsung-submitted CRs, excluding each CR's directly modified specification numbers. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Other specs requires excluding direct modified specs; exact Company name, full footprint no cap.

**Original query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

**Revised query**

```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}), (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE NOT EXISTS { MATCH (c)-[:MODIFIES]->(direct:Spec) WHERE direct.specNumber=s.specNumber } RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ4-4/2c37c4b14f986c080cd2e40c4b104e2915e35d5a44119f0a3f501d301e1d50dd.json), [complete native rows](../reference_outputs/RAN4_P4_CQ4-4/2c37c4b14f986c080cd2e40c4b104e2915e35d5a44119f0a3f501d301e1d50dd.jsonl); 18 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `65359e913f57512c78581a82278b692be8decceea259d97099331004c1e41e5a`.

## RAN4_P4_CQ4-5

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the change summaries of CRs approved at meeting #93 (meeting-scoped change review).

**Revised question:** List distinct CR TDoc identifiers and recorded change-summary values for CRs referenced by Agreements at canonical meetingRAN4#93. Return named records with crTdoc, summary. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original numeric93 includesbis and Tdoc notCR; exact meeting and CR labels, nullable summary, approval reduced to documented reference variant.

**Original query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 93}) WITH a MATCH (a)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10
```

**Revised query**

```cypher
MATCH (a:Agreement)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN4#93'}), (a)-[:REFERENCES]->(cr:CR) RETURN DISTINCT cr.tdocNumber AS crTdoc,cr.summaryOfChange AS summary
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P4_CQ4-5/320eb8a9451c622859c7d3c17df91a498fee94d710465b8e271b7ba2620106cd.json), [complete native rows](../reference_outputs/RAN4_P4_CQ4-5/320eb8a9451c622859c7d3c17df91a498fee94d710465b8e271b7ba2620106cd.jsonl); 544 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `95aa10a106d2a6b8e756d2ef91f351ba41b41f0361d492418ceb9cc32dd4e2bb`.

## RAN4_P5_CQ1-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the completed TRs targeting Rel-17 (release study inventory).

**Revised question:** List distinct TechnicalReport numbers targetingRel-17 with recorded trStatus equal toCompleted. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original inventory asks report IDs; title unrequested, exact source filters retained.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) WHERE tr.trStatus = 'Completed' RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ1-1/d40e329f23d3cd0309dce9d5d632709200fc1e7954ea439156ccfd899c2d3f62.json), [complete native rows](../reference_outputs/RAN4_P5_CQ1-1/d40e329f23d3cd0309dce9d5d632709200fc1e7954ea439156ccfd899c2d3f62.jsonl); 15 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `80981da8567bfd0053891be90ba2a0521c979c1b0b8a2eb36fc5b5cdd0623521`.

## RAN4_P5_CQ1-4

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs currently in draft status (ongoing studies).

**Revised question:** List distinct TechnicalReport numbers whose frozen-graph trStatus equalsDraft. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Currently is relative to frozen snapshot, not live real-world status; grade report numbers.

**Original query**

```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Draft' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Draft' RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ1-4/8609859f7e24fca4b9ffabb6fbbca7ccae165d8b304c3abe22c89560ce0f26f8.json), [complete native rows](../reference_outputs/RAN4_P5_CQ1-4/8609859f7e24fca4b9ffabb6fbbca7ccae165d8b304c3abe22c89560ce0f26f8.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `8713caa7a770f135f293b85f745519f3d7a2c2970120ad726bbc79169092e41b`.

## RAN4_P5_CQ2-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the specs impacted by TR 38.803 (study-to-spec impact).

**Revised question:** List distinct specification numbers targeted by TRImpact records linked from TechnicalReport38.803. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested spec inventory only; record-defined impact metadata, type not required.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ2-1/94de977cf036212b64563756ecd2cb41b41c3ad3a810ca2c1bde975bdaa848c3.json), [complete native rows](../reference_outputs/RAN4_P5_CQ2-1/94de977cf036212b64563756ecd2cb41b41c3ad3a810ca2c1bde975bdaa848c3.jsonl); 4 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `56c00da1ee7433ac7d31c3638c9b605097ac89a909a853453392539cbbd8234d`.

## RAN4_P5_CQ2-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the impact types of TR 38.860 (impact classification).

**Revised question:** List all distinct recorded impactType values of TRImpact nodes linked from TechnicalReport38.860. Return named records with impactType. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Types requested rather than extra description.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN DISTINCT imp.impactType AS impactType
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ2-2/b56e4aa9e435594cbd2fea307ed14cb2b3f13a1f7bde511765ab3ba617688134.json), [complete native rows](../reference_outputs/RAN4_P5_CQ2-2/b56e4aa9e435594cbd2fea307ed14cb2b3f13a1f7bde511765ab3ba617688134.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `4e6a90de35f7e1e95114b83f1b5eb35f54381b69a31d2f568d0ed4782f60b018`.

## RAN4_P5_CQ2-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs led to a new TS? (spinning up new specs).

**Revised question:** List distinct TechnicalReport numbers with linked NewTS TRImpact records targeting a recorded Spec. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Recorded NewTS association does not prove led-to causation; explicit available task and requested IDs only.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, s.specNumber ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ2-3/4e034de3e92c448200f046522142e2764ac77b2b609366937cba012a16108b6b.json), [complete native rows](../reference_outputs/RAN4_P5_CQ2-3/4e034de3e92c448200f046522142e2764ac77b2b609366937cba012a16108b6b.jsonl); 1 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `71cd78a9e1af76c44b74201ed8d0c389cacb8b3f38bfdd29f12aa42e7d49b750`.

## RAN4_P5_CQ2-4

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which TRs extended existing spec sections? (incremental spec impact).

**Revised question:** List distinct TechnicalReport numbers with linked ExtendSection TRImpact records targeting a recorded Spec. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Recorded impact category does not independently demonstrate extension occurred; explicit metadata task and cap removed.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber, s.specNumber ORDER BY tr.trNumber LIMIT 20
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ2-4/477443c08df16fb2cd1e7cce47203591066987b816f6eca80de819d0fb872e09.json), [complete native rows](../reference_outputs/RAN4_P5_CQ2-4/477443c08df16fb2cd1e7cce47203591066987b816f6eca80de819d0fb872e09.jsonl); 62 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `3c12c526fb75a5c4172e9c470ab2befae16c3888efd144da2053f414e0758985`.

## RAN4_P5_CQ2-5

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs that impacted spec 38.101-1 (reverse study lookup).

**Revised question:** List all distinct TechnicalReport numbers whose linked TRImpact targets specification38.101-1. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested reverse-study inventory only; type/title not requested.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.101-1'}) RETURN DISTINCT tr.trNumber, tr.trTitle, imp.impactType ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.101-1'}) RETURN DISTINCT tr.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ2-5/9cd2187d15ba151c510f727d491e65f5362803fde9b5fd81c7dda12eb3919639.json), [complete native rows](../reference_outputs/RAN4_P5_CQ2-5/9cd2187d15ba151c510f727d491e65f5362803fde9b5fd81c7dda12eb3919639.jsonl); 47 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `756ffdac4460679b61d7ef2ff81e82ff313784f62122f072e48c6b3e140f781a`.

## RAN4_P5_CQ3-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Which specs did the NR RF study TR 38.803 impact? (study-to-spec impact).

**Revised question:** List all distinct specification numbers targeted by TRImpact records linked from TechnicalReport38.803. Return named records with specNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Main question asks which specs, not additional type/description payload; report identity by given number.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ3-1/94de977cf036212b64563756ecd2cb41b41c3ad3a810ca2c1bde975bdaa848c3.json), [complete native rows](../reference_outputs/RAN4_P5_CQ3-1/94de977cf036212b64563756ecd2cb41b41c3ad3a810ca2c1bde975bdaa848c3.jsonl); 4 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `069516f775a0c4aec2de64c565dfe518e2133cebb170ec1f527646fb31fff76c`.

## RAN4_P5_CQ3-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What spec impact did the FR2 extension study TR 38.820 have? (study-to-spec impact).

**Revised question:** Return distinct specification-number and impact-type records linked from TechnicalReport38.820; include a null-spec/null-type record when no complete linked impact-to-spec path is recorded. Return named records with specNumber, impactType. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original recorded output has native null targets. Explicit nullable impact records do not certify no real-world impact; report status unrequested.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.820'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.trStatus, s.specNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.820'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber, imp.impactType AS impactType
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ3-2/e568c8b9d09f9a4768d9442ae85f2f837ab6ea081015a630eef5a731168189b5.json), [complete native rows](../reference_outputs/RAN4_P5_CQ3-2/e568c8b9d09f9a4768d9442ae85f2f837ab6ea081015a630eef5a731168189b5.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `47dd636b067acd345958b268451275e3e8725bed8a0ac5913c5f3b7a5cdad6af`.

## RAN4_P5_CQ3-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** What spec impact, with details, did the NTN RF study TR 38.863 have? (study-to-spec impact detail).

**Revised question:** List distinct specification-number,impact-type and impact-description records linked from TechnicalReport38.863. Return named records with specNumber, impactType, description. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** With details requires all named impact fields, correct roles paired.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.863'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.863'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber, imp.impactType AS impactType, imp.impactDescription AS description
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ3-3/b6399ca53ad577f5d15109cff9adacbffd408525d2d845b445ed70511e0509c6.json), [complete native rows](../reference_outputs/RAN4_P5_CQ3-3/b6399ca53ad577f5d15109cff9adacbffd408525d2d845b445ed70511e0509c6.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `44b46d24503f6323709b0e3f2e72eed0ed32a5574b6c5aaf0a909041438975f8`.

## RAN4_P5_CQ4-1

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the Rel-17 study TRs and their impact types (release study overview).

**Revised question:** List all distinct Rel-17-targeted TR-number and recorded impact-type pairs, including null impactType when no linked TRImpact is recorded. Return named records with trNumber, impactType. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Flatten unordered collected impactTypes into explicit named-pair set; retain no-impact reports with null, title unrequested.

**Original query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, tr.trTitle, collect(DISTINCT imp.impactType) AS impactTypes ORDER BY tr.trNumber
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN DISTINCT tr.trNumber AS trNumber,imp.impactType AS impactType
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ4-1/298cbb57b430ecc804c103c27084a0e53e7ecd733837d3444b62c7bf49626978.json), [complete native rows](../reference_outputs/RAN4_P5_CQ4-1/298cbb57b430ecc804c103c27084a0e53e7ecd733837d3444b62c7bf49626978.jsonl); 22 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `eaa89f6ee11912771e4c8d9c6ab9f4f9dc6eaaadb33eb5280bb57cd3283f4f0c`.

## RAN4_P5_CQ4-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** Return the status and scope of the IAB RF study TR 38.809 (study progress check).

**Revised question:** Return recorded status and scope text of TechnicalReport38.809. Return named records with status, scope. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Both requested fields required, number is fixed input context.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.809'}) RETURN tr.trNumber, tr.trStatus, tr.scope
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.809'}) RETURN DISTINCT tr.trStatus AS status, tr.scope AS scope
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ4-2/b53e5d04422764d57ed6aa83642a55d41ec8161fe54989cf94255775a41cd0c2.json), [complete native rows](../reference_outputs/RAN4_P5_CQ4-2/b53e5d04422764d57ed6aa83642a55d41ec8161fe54989cf94255775a41cd0c2.jsonl); 1 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `f246a5d9554e8167f4879afbf00fa573358a8a9340693ae522c0e0f63e7564df`.

## RAN4_P5_CQ4-3

**Change class:** Substantive variant; original intent remains unresolved. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Retained original-meaning limit:** The original RedCap RF study characterization of TR38.860 and real-world reflection into specifications are not established by retained source evidence. The neutral nullable recorded-metadata variant does not resolve or certify either original assumption.

**Original question:** Return the conclusions of RedCap RF study TR 38.860 and how they were reflected in specs (study-to-spec outcome).

**Revised question:** Return distinct recorded conclusion-text,specification-number and impact-type records for TechnicalReport38.860; conclusion text is null when absent and target/type are null when no complete impact-to-spec path is recorded. Return named records with conclusions, specNumber, impactType. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Original RedCap descriptor is uncorroborated by retained impact description (APT600MHz), and native conclusions are null. Neutral ID-based metadata variant does not invent conclusions or establish how they were reflected.

**Original query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.conclusions, s.specNumber, imp.impactType
```

**Revised query**

```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.conclusions AS conclusions, s.specNumber AS specNumber, imp.impactType AS impactType
```

**Scoring contract**

```json
{
  "required_fields": [
    {
      "name": "conclusions",
      "nullable": true,
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ4-3/489bf339ec5e78868e540822d3d38fb6562b12a0753ceec722af932610369338.json), [complete native rows](../reference_outputs/RAN4_P5_CQ4-3/489bf339ec5e78868e540822d3d38fb6562b12a0753ceec722af932610369338.jsonl); 1 native rows retained. The retained per-item check record has 13 passing scorer checks for this definition.

**Definition SHA-256:** `aaf26b492905d6c93dd8f97981125fb23236a1db9fd06d88b0dc5448a6a3db05`.

## RAN4_P5_CQ5-2

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the TRs that reference TR 38.803 (inbound TR citations).

**Revised question:** List distinct TechnicalReport numbers with a REFERENCES_TR edge to TechnicalReport38.803. Return named records with trNumber. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Requested referring report IDs only, titles unrequested.

**Original query**

```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport {trNumber: '38.803'}) RETURN ref.trNumber, ref.trTitle ORDER BY ref.trNumber
```

**Revised query**

```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport {trNumber: '38.803'}) RETURN DISTINCT ref.trNumber AS trNumber
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ5-2/61b681ce487a63aba542450a0f6abc4d0d9a59e4a1bb1fd4701a568165120be1.json), [complete native rows](../reference_outputs/RAN4_P5_CQ5-2/61b681ce487a63aba542450a0f6abc4d0d9a59e4a1bb1fd4701a568165120be1.jsonl); 6 native rows retained. The retained per-item check record has 7 passing scorer checks for this definition.

**Definition SHA-256:** `790bdb3c75d29a4bdb60abbad420f1bc2da46d85b46890c41a5290172f636cab`.

## RAN4_P5_CQ5-3

**Change class:** Proposed clarification. Author semantic review: pending.

**Byte-level change:** question wording changed; reference query changed. This records text identity, not a judgment about preserved meaning.

**Original question:** List the top 5 most-referenced TRs (most-cited studies).

**Revised question:** Return top5 TechnicalReport numbers by count of distinct TechnicalReport nodes referencing them, ties by report number ascending; return all if fewer than5 are referenced. Return named records with trNumber, referringTrCount. Interpret the population and relationships relative to the frozen RAN4 graph.

**Proposed rationale:** Group by requested report-number identity directly and count distinct referencing TechnicalReport nodes across any same-number targets, without assuming one node per trNumber. Positive-reference population and deterministic exact-top-five ties are explicit.

**Original query**

```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport) WITH tr, count(ref) AS refCount RETURN tr.trNumber, tr.trTitle, refCount ORDER BY refCount DESC, tr.trNumber LIMIT 5
```

**Revised query**

```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport) RETURN tr.trNumber AS trNumber,count(DISTINCT ref) AS referringTrCount ORDER BY referringTrCount DESC,trNumber ASC LIMIT 5
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
      "name": "referringTrCount",
      "nullable": false,
      "source_column_or_expression": "referringTrCount",
      "type": "integer"
    }
  ],
  "collection": {
    "kind": "sequence",
    "order_keys": [
      {
        "direction": "desc",
        "field": "referringTrCount"
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

**Technical evidence:** [execution receipt](../reference_outputs/RAN4_P5_CQ5-3/fcde69e0523eb2fd150f39bfeac0f6165ed287afef889480cfb6bc2a622cbcdc.json), [complete native rows](../reference_outputs/RAN4_P5_CQ5-3/fcde69e0523eb2fd150f39bfeac0f6165ed287afef889480cfb6bc2a622cbcdc.jsonl); 5 native rows retained. The retained per-item check record has 10 passing scorer checks for this definition.

**Definition SHA-256:** `ca329585c0fbf0360a9a202bb8cbbabc7aea7bed3302f2d2d7e563a6c45e65c6`.
