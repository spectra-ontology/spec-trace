# RAN3: admitted original-question repairs

Both recorded judgments are separate AI reviews; neither is expert certification.


## RAN3_P1_CQ1-1

Original question (unchanged): List the TDocs at meeting RAN3#130 linked to Work Item NR_newRAT-Core (interface work-item preparation).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 66. [Receipt](../reference_outputs/RAN3_P1_CQ1-1/7e57bdb5f750d9a6a343b4f4351c2e0a0125e291a32a85b92c93265e79d09eee.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-1/7e57bdb5f750d9a6a343b4f4351c2e0a0125e291a32a85b92c93265e79d09eee.jsonl)

Repair hash: `1cfcec0880162034b74e17c983e654b566382e1d50a8b357e1776281878483d6`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ1-2

Original question (unchanged): List the TDocs under agenda item 8.1 at meeting RAN3#130 (agenda-item document review).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 30. [Receipt](../reference_outputs/RAN3_P1_CQ1-2/352156a4ce10e937fc4b222c180925cc9e657072c68ab460697587595ffa9771.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-2/352156a4ce10e937fc4b222c180925cc9e657072c68ab460697587595ffa9771.jsonl)

Repair hash: `f405de32d934dcc9a39507f0d0e534e2233b53f00317e8665c24dc62dbf50c1d`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ1-3

Original question (unchanged): List the TDocs Huawei submitted at meeting RAN3#130 (tracking a company's contributions).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 327. [Receipt](../reference_outputs/RAN3_P1_CQ1-3/db50b2a600818d0cbd281e512a04900f5de792bb3960789df70270d296a62fba.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-3/db50b2a600818d0cbd281e512a04900f5de792bb3960789df70270d296a62fba.jsonl)

Repair hash: `369f883a1116d6bcf75b867e2cc422da977ad21d92ca883b8babe42762fdcc6a`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ1-5

Original question (unchanged): List the TDocs agreed at meeting RAN3#130 (approved-outcome review).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 137. [Receipt](../reference_outputs/RAN3_P1_CQ1-5/cc76952d37daf80570d46691145e306cd45f3209ef5268ba6c5dd8e473df3f78.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-5/cc76952d37daf80570d46691145e306cd45f3209ef5268ba6c5dd8e473df3f78.jsonl)

Repair hash: `ae8a0e941930815cad6ec6617f25ca6142f9bb1331f7e70136ef194ef4f1948b`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE t.status = 'agreed' RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) WHERE t.status = 'agreed' RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ1-6

Original question (unchanged): Return the decision status of TDoc R3-258530 (checking the outcome).

Repair: `scorer_only`. Required answers: status (string) ← t.status.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ1-6/244dd4cfe4e5c1054593ce626a12979831e52451c1a6b6e2347c48d1b484c7bf.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-6/244dd4cfe4e5c1054593ce626a12979831e52451c1a6b6e2347c48d1b484c7bf.jsonl)

Repair hash: `b7eccac9db2ac9637c7ea5b41a6d4cc9c417967968c5425dc7b646a0d38153ac`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.status, t.type
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.status, t.type
```


## RAN3_P1_CQ1-7

Original question (unchanged): Return the 'For' purpose of TDoc R3-258530 (identifying document intent).

Repair: `scorer_only`. Required answers: purpose (string) ← t.for.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ1-7/01fd1b93ded0c256de21c8fc035b041fcc31af8f830ac43515761d880a0619ab.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-7/01fd1b93ded0c256de21c8fc035b041fcc31af8f830ac43515761d880a0619ab.jsonl)

Repair hash: `36fece08472c1e416218c2c851ba303ab824b05a935147d43eddbb6093d20e9e`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.for
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.for
```


## RAN3_P1_CQ1-8

Original question (unchanged): Return the contact person for TDoc R3-258530 (finding the responsible author).

Repair: `scorer_only`. Required answers: contactName (string) ← c.contactName.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ1-8/8763d1c67cc63fdf1c2348d0ae69255a8bc063c88019804d2dce7220618df5d8.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ1-8/8763d1c67cc63fdf1c2348d0ae69255a8bc063c88019804d2dce7220618df5d8.jsonl)

Repair hash: `cb372f988c8312ee26a73a9d9b103ae6692e398c78774ab550ec3cde173c447e`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId
```


## RAN3_P1_CQ2-1

Original question (unchanged): Return the predecessor revision of TDoc R3-241531 (revision-lineage tracing).

Repair: `scorer_only`. Required answers: predecessorTdoc (string) ← prev.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ2-1/d934c63191963c26b00e768ddea159a60906b96c8b1d69546698b053f8abb3fe.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-1/d934c63191963c26b00e768ddea159a60906b96c8b1d69546698b053f8abb3fe.jsonl)

Repair hash: `b19b6c22556c2dd22e8f9749a5f6ad5b1573d9a1bedd3d5da0a6a86803710419`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241531'})-[:IS_REVISION_OF]->(prev:Tdoc) RETURN t.tdocNumber, prev.tdocNumber, prev.title
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241531'})-[:IS_REVISION_OF]->(prev:Tdoc) RETURN t.tdocNumber, prev.tdocNumber, prev.title
```


## RAN3_P1_CQ2-3

Original question (unchanged): Return the LS that TDoc R3-241518 replies to (liaison reply linkage).

Repair: `query_and_scorer`. Required answers: replyTargetTdoc (string) ← replyTargetTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ2-3/c1b47e1e16e07115dc5a824bea899b9ba938fc692638eff8872825fe94442fdc.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-3/c1b47e1e16e07115dc5a824bea899b9ba938fc692638eff8872825fe94442fdc.jsonl)

Repair hash: `22f82d31376b4d5f3126d01d25f6973274081b70e7c1f06e2d88cbeed2f57081`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-241518'})-[:REPLY_TO]->(orig:Tdoc) RETURN t.tdocNumber, orig.tdocNumber, orig.title
```

Repaired reference query:
```cypher
MATCH (:Tdoc {tdocNumber:'R3-241518'})-[:REPLY_TO]->(orig:Tdoc:LS) RETURN DISTINCT orig.tdocNumber AS replyTargetTdoc
```


## RAN3_P1_CQ2-4

Original question (unchanged): Return the specs that CR R3-258530 modifies (change-impact scope).

Repair: `scorer_only`. Required answers: specNumber (string) ← s.specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ2-4/f1e35343152fd915f470dc4c0ddbe7499853fd6a287ada8d22033bba3c1bf716.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-4/f1e35343152fd915f470dc4c0ddbe7499853fd6a287ada8d22033bba3c1bf716.jsonl)

Repair hash: `dcee18e1990f7bae35bef9a4ef9b7ffa518f22e2f7ca9c89673b983d363d54c7`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'})-[:MODIFIES]->(s:Spec) RETURN c.tdocNumber, s.specNumber
```

Repaired reference query:
```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'})-[:MODIFIES]->(s:Spec) RETURN c.tdocNumber, s.specNumber
```


## RAN3_P1_CQ2-5

Original question (unchanged): Return the category and affected clauses of CR R3-258530 (impact assessment).

Repair: `scorer_only`. Required answers: category (string) ← c.crCategory, clausesAffected (string) ← c.clausesAffected.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ2-5/778efe869291661e0a8acdd86b0ae089c0993d7cc34214a39b2b751418a8a144.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-5/778efe869291661e0a8acdd86b0ae089c0993d7cc34214a39b2b751418a8a144.jsonl)

Repair hash: `39f542d490fd583be3b9a82f790e964d1c0997f82958dafb3a5e8fc4824491ee`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'}) RETURN c.tdocNumber, c.crCategory, c.crNumber, c.clausesAffected
```

Repaired reference query:
```cypher
MATCH (c:CR {tdocNumber: 'R3-258530'}) RETURN c.tdocNumber, c.crCategory, c.crNumber, c.clausesAffected
```


## RAN3_P1_CQ2-6

Original question (unchanged): List the TDocs postponed at meeting RAN3#121bis (deferred-item tracking).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 3. [Receipt](../reference_outputs/RAN3_P1_CQ2-6/dd640384307fb29f0b81cd6c26a659c872600955228bccf1bc259aa906644c39.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-6/dd640384307fb29f0b81cd6c26a659c872600955228bccf1bc259aa906644c39.jsonl)

Repair hash: `e08936bfcd1a66764d0387a26926e81c556d8db9a405ce78916d15a649598539`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 121}) WHERE t.status = 'postponed' RETURN t.tdocNumber, t.title LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN3#121bis'}) WHERE t.status='postponed' RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ2-7

Original question (unchanged): List the incoming liaison statements at meeting RAN3#130 (incoming-LS triage).

Repair: `query_and_scorer`. Required answers: lsTdoc (string) ← lsTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 20. [Receipt](../reference_outputs/RAN3_P1_CQ2-7/b68acb92eefbfba012dafbb79e0f4753ffa6e5d0a809e1d8c1355b61958b2fb8.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ2-7/b68acb92eefbfba012dafbb79e0f4753ffa6e5d0a809e1d8c1355b61958b2fb8.jsonl)

Repair hash: `94dbb23c1d52c7dbbafa248e2b6913a571c26168771c1619da731476e44c6864`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (l:LS)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE l.direction = 'in' RETURN l.tdocNumber, l.title ORDER BY l.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (l:LS)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) WHERE l.direction = 'in' RETURN DISTINCT l.tdocNumber AS lsTdoc
```


## RAN3_P1_CQ3-1

Original question (unchanged): List Huawei's contributions to Work Item NR_newRAT-Core (competitor contribution review).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2010. [Receipt](../reference_outputs/RAN3_P1_CQ3-1/00bd959e8a589299e8dcad71460ad602d1e65c654a7a01652f147810950860f8.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-1/00bd959e8a589299e8dcad71460ad602d1e65c654a7a01652f147810950860f8.jsonl)

Repair hash: `88e25ec08b41645111900c0c203f4946f802a32264c2fb5f87b212fc8431fe35`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ3-2

Original question (unchanged): Break down contributions by company under agenda item 8.1 at meeting RAN3#130 (competitive landscape).

Repair: `query_and_scorer`. Required answers: companyName (string) ← companyName, tdocCount (integer) ← tdocCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 7. [Receipt](../reference_outputs/RAN3_P1_CQ3-2/ac6c91f4bb8e555dc521dd6062f89978cf2f57f4405b0cc767819246c9325e69.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-2/ac6c91f4bb8e555dc521dd6062f89978cf2f57f4405b0cc767819246c9325e69.jsonl)

Repair hash: `e0500d115cf65355af8689e452a4949897f8a9706f904effddf168ad5b363bad`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount
```


## RAN3_P1_CQ3-3

Original question (unchanged): Count contributions per company on Work Item NR_newRAT-Core (participation ranking).

Repair: `query_and_scorer`. Required answers: companyName (string) ← companyName, tdocCount (integer) ← tdocCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 85. [Receipt](../reference_outputs/RAN3_P1_CQ3-3/daa3f2aed120a3d60d0d0e7450609cd7d78309906a5bd15aa7caa28c001151d6.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-3/daa3f2aed120a3d60d0d0e7450609cd7d78309906a5bd15aa7caa28c001151d6.jsonl)

Repair hash: `7bc2d82c1bea68f01fc0e2b8201a859c22c5a57cb95a7b4681974a3514085253`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN DISTINCT c.companyName AS companyName, count(DISTINCT t) AS tdocCount
```


## RAN3_P1_CQ3-4

Original question (unchanged): Return the share of Samsung's TDocs that were agreed (success-rate metric).

Repair: `query_and_scorer`. Required answers: agreedFraction (number) ← agreedFraction.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P1_CQ3-4/ed3ef92b545f2d4faac539d2cb6b2de8152f16e95ce97e174f429a6e80ef8fdd.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-4/ed3ef92b545f2d4faac539d2cb6b2de8152f16e95ce97e174f429a6e80ef8fdd.jsonl)

Repair hash: `9b4575538eafc7ec549255e345a29e74435623de517175254c6f401e572f79b2`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) WITH count(t) AS total MATCH (t2:Tdoc)-[:SUBMITTED_BY]->(c2:Company {companyName: 'Samsung'}) WHERE t2.status = 'agreed' RETURN total, count(t2) AS agreed, toFloat(count(t2)) / total AS ratio
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) WITH collect(DISTINCT t) AS docs WITH docs, [d IN docs WHERE d.status='agreed'] AS approved RETURN CASE WHEN size(docs)=0 THEN null ELSE toFloat(size(approved))/size(docs) END AS agreedFraction
```


## RAN3_P1_CQ3-5

Original question (unchanged): List other companies' contributions in the same agenda and meeting as R3-258530 (peer-contribution comparison).

Repair: `query_and_scorer`. Required answers: companyName (string) ← companyName, tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 354. [Receipt](../reference_outputs/RAN3_P1_CQ3-5/1050e39d0e31e327050795c0e576aa006edd825ec7051215f4e45a46c54caa84.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-5/1050e39d0e31e327050795c0e576aa006edd825ec7051215f4e45a46c54caa84.jsonl)

Repair hash: `1499b8f98826f2f35196673399d27d0b8ae7bf36d04f6637608272e6a4fec431`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:BELONGS_TO]->(a:AgendaItem), (t)-[:PRESENTED_AT]->(m:Meeting) MATCH (other:Tdoc)-[:BELONGS_TO]->(a), (other)-[:PRESENTED_AT]->(m), (other)-[:SUBMITTED_BY]->(c:Company) WHERE other.tdocNumber <> 'R3-258530' RETURN c.companyName, other.tdocNumber, other.title ORDER BY c.companyName LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber:'R3-258530'})-[:BELONGS_TO]->(a:AgendaItem), (t)-[:PRESENTED_AT]->(m:Meeting), (t)-[:SUBMITTED_BY]->(origin:Company) WITH t,a,m,collect(DISTINCT origin) AS origins MATCH (other:Tdoc)-[:BELONGS_TO]->(a), (other)-[:PRESENTED_AT]->(m), (other)-[:SUBMITTED_BY]->(c:Company) WHERE NOT c IN origins RETURN DISTINCT c.companyName AS companyName,other.tdocNumber AS tdocNumber
```


## RAN3_P1_CQ3-6

Original question (unchanged): Show Huawei's contribution distribution across Work Items (identifying focus areas).

Repair: `query_and_scorer`. Required answers: workItemCode (string) ← workItemCode, tdocCount (integer) ← tdocCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 282. [Receipt](../reference_outputs/RAN3_P1_CQ3-6/b179335eccda66c41bbb62852ad2ce72f0e74e9a4886e3fe7034d52aad026b04.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ3-6/b179335eccda66c41bbb62852ad2ce72f0e74e9a4886e3fe7034d52aad026b04.jsonl)

Repair hash: `81699c40c26d3b5042a8b9f9d1ea8568daea8c9422cd9b66405fd52f3d504242`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem) RETURN w.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem) RETURN DISTINCT w.workItemCode AS workItemCode, count(DISTINCT t) AS tdocCount
```


## RAN3_P1_CQ4-2

Original question (unchanged): Summarize the outcomes of Samsung's contributions at meeting RAN3#130 (result rollup by status).

Repair: `query_and_scorer`. Required answers: status (string) ← status, tdocCount (integer) ← tdocCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 7. [Receipt](../reference_outputs/RAN3_P1_CQ4-2/c11fa6ce80a924d9a3276cf65fec4fa76a770236b6eb778f857ab46ff82ee54d.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ4-2/c11fa6ce80a924d9a3276cf65fec4fa76a770236b6eb778f857ab46ff82ee54d.jsonl)

Repair hash: `6be119a1e3ffb4746ea02dbe62d2c138c161072b9cdd6544a2ec0678f253847b`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.status, count(t) AS cnt ORDER BY cnt DESC
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#130'}) RETURN DISTINCT t.status AS status, count(DISTINCT t) AS tdocCount
```


## RAN3_P1_CQ4-3

Original question (unchanged): List the not-treated TDocs under agenda item 13.2 at meeting RAN3#122 (pending-item tracking).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2. [Receipt](../reference_outputs/RAN3_P1_CQ4-3/9c4ab5e96df4a16207c0069d1e177714ede269166d99cb0833dbeaf49a22964b.json) · [Complete rows](../reference_outputs/RAN3_P1_CQ4-3/9c4ab5e96df4a16207c0069d1e177714ede269166d99cb0833dbeaf49a22964b.jsonl)

Repair hash: `d98e5061ad62c3553334d84dd1a7474771ae372c640ad07c952938769b3c21ec`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '13.2'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 122}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '13.2'}), (t)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#122'}) WHERE t.status = 'not treated' RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P2_CQ1-1

Original question (unchanged): List the agreements reached at meeting RAN3#121 (consensus-outcome review).

Repair: `query_and_scorer`. Required answers: agreementId (string) ← agreementId, content (string) ← content.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 84. [Receipt](../reference_outputs/RAN3_P2_CQ1-1/d36f1fef513394cc973926562900231103d59dccbd6a0c08cfc4a19c01465f46.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ1-1/d36f1fef513394cc973926562900231103d59dccbd6a0c08cfc4a19c01465f46.jsonl)

Repair hash: `66c2913f2d5c0eb7d7d63c396d2b9324621eebf98032aed8e94e84ba1c881dd9`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#121'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#121'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId AS agreementId, a.content AS content
```


## RAN3_P2_CQ1-2

Original question (unchanged): List the conclusions drawn at meeting RAN3#94 (meeting-outcome review).

Repair: `query_and_scorer`. Required answers: conclusionId (string) ← conclusionId, content (string) ← content.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 214. [Receipt](../reference_outputs/RAN3_P2_CQ1-2/fe0582a5c111a1462190de7913161f779ae94c04179d824f5df2e45256e4322d.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ1-2/fe0582a5c111a1462190de7913161f779ae94c04179d824f5df2e45256e4322d.jsonl)

Repair hash: `41d6adda7e17cbccca3d83524a4d37db823bc4e501fafd5d8cfa2c1c1ea19ffb`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#94'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#94'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content
```


## RAN3_P2_CQ1-3

Original question (unchanged): List the working assumptions from meeting RAN3#112 (provisional-decision tracking).

Repair: `query_and_scorer`. Required answers: workingAssumptionId (string) ← workingAssumptionId, content (string) ← content.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 17. [Receipt](../reference_outputs/RAN3_P2_CQ1-3/3084bcf94b739a3acf90d2fd95c630bd4eee16e15359aa0686dc4b3bebe19948.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ1-3/3084bcf94b739a3acf90d2fd95c630bd4eee16e15359aa0686dc4b3bebe19948.jsonl)

Repair hash: `09d819e2676545eaa4f28e766fb094fe6ab70571bc33a4d20e48165dc40f1c94`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#112'}) OPTIONAL MATCH (w)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN w.resolutionId, w.content, ai.agendaNumber ORDER BY ai.agendaNumber, w.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN3#112'}) OPTIONAL MATCH (w)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT w.resolutionId AS workingAssumptionId, w.content AS content
```


## RAN3_P2_CQ2-1

Original question (unchanged): Return the TDocs referenced by three or more resolutions (high-impact contributions).

Repair: `query_and_scorer`. Required answers: tdocNumber (string) ← tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 41. [Receipt](../reference_outputs/RAN3_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.jsonl)

Repair hash: `83c968ebbbf3f1faa1ab1874aa08d4209989f1ae60b3656afd5f62a3354d1881`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(r) AS refCnt WHERE refCnt >= 3 RETURN t.tdocNumber, refCnt ORDER BY refCnt DESC, t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(DISTINCT r) AS refCnt WHERE refCnt >= 3 RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN3_P2_CQ2-2

Original question (unchanged): List resolutions that reference five or more TDocs (multi-document decisions).

Repair: `query_and_scorer`. Required answers: resolutionId (string) ← resolutionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 358. [Receipt](../reference_outputs/RAN3_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.jsonl)

Repair hash: `db22996a4f43a613d82a0623628f52df9432e023293fc3f92c01a6021248bb05`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r, collect(t.tdocNumber) AS refs, count(t) AS cnt WHERE cnt >= 5 MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, refs[..5] AS top5_refs, cnt ORDER BY m.meetingNumberInt DESC, cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r,count(DISTINCT t) AS referencedTdocCount WHERE referencedTdocCount>=5 RETURN DISTINCT r.resolutionId AS resolutionId
```


## RAN3_P2_CQ2-4

Original question (unchanged): Count resolution-referenced TDocs per spec they modify (spec-change tracing).

Repair: `query_and_scorer`. Required answers: specNumber (string) ← specNumber, tdocCount (integer) ← tdocCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 57. [Receipt](../reference_outputs/RAN3_P2_CQ2-4/26d5430a3d9cc57cf70b80295a962327161c3aedffe2e88f103017ed18784eac.json) · [Complete rows](../reference_outputs/RAN3_P2_CQ2-4/26d5430a3d9cc57cf70b80295a962327161c3aedffe2e88f103017ed18784eac.jsonl)

Repair hash: `1e437479fd610c2b3e6206281612b29a4d5c3140bd635ec198124a7c9ec61d76`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) RETURN s.specNumber AS specNumber,count(DISTINCT t) AS tdocCount
```


## RAN3_P3_CQ1-1

Original question (unchanged): List all sections of spec 38.423 (full-structure overview).

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 3208. [Receipt](../reference_outputs/RAN3_P3_CQ1-1/2fb5cc70df6699fa58c993640939e6ae51e291bd20532f8acd489e9075c30d28.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-1/2fb5cc70df6699fa58c993640939e6ae51e291bd20532f8acd489e9075c30d28.jsonl)

Repair hash: `8f5396059ea230abe507d8c8f2e0959c609d7fe9be28080c4a3fa737e083fdd6`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
```


## RAN3_P3_CQ1-12

Original question (unchanged): Show the section-level distribution in spec 38.423 (structural-depth profile).

Repair: `query_and_scorer`. Required answers: level (integer) ← level, sectionCount (integer) ← sectionCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 4. [Receipt](../reference_outputs/RAN3_P3_CQ1-12/cfc04bdeebd9c936cd9ba87ebc0ce193b9b2ca92215fc0c932f41d21a96e8ad4.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-12/cfc04bdeebd9c936cd9ba87ebc0ce193b9b2ca92215fc0c932f41d21a96e8ad4.jsonl)

Repair hash: `a24ec4db0ccfc2021a35a272cb5a1176802549d2c9d9a261035fa5e72504d10e`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT s.level AS level, count(DISTINCT s) AS sectionCount
```


## RAN3_P3_CQ1-14

Original question (unchanged): Return the total counts of sections, tables, and figures (corpus-size overview).

Repair: `scorer_only`. Required answers: sectionCount (integer) ← secCnt, tableCount (integer) ← tblCnt, figureCount (integer) ← figCnt.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P3_CQ1-14/b880148e4cb276f0c54cd366e7f4f1d916f1afe941123eaa72b64efe7ceb73c2.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-14/b880148e4cb276f0c54cd366e7f4f1d916f1afe941123eaa72b64efe7ceb73c2.jsonl)

Repair hash: `fd2d2bb602883cd4f461b386c65b1b9a3327c88b9fb85e3934f688f4d28ef0ee`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```

Repaired reference query:
```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```


## RAN3_P3_CQ1-4

Original question (unchanged): List the level-1 sections of spec 38.413 (top-level table of contents).

Repair: `scorer_only`. Required answers: sectionId (string) ← s.sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 55. [Receipt](../reference_outputs/RAN3_P3_CQ1-4/5f4cbd80a4fc45528f895da90de0fa1b38c76ed609168b5f664c71d60552c2db.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-4/5f4cbd80a4fc45528f895da90de0fa1b38c76ed609168b5f664c71d60552c2db.jsonl)

Repair hash: `a974a320d932627a2f38fa563707b507d85a8066ff7d66d97c102bec8c58d600`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.413'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```


## RAN3_P3_CQ1-8

Original question (unchanged): List all tables in spec 38.423 (tabular-content inventory).

Repair: `query_and_scorer`. Required answers: tableId (string) ← tableId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN3_P3_CQ1-8/27ff145ed4cc4f3195bd241a543645a056b5408d46c7a2edd93d7769c95a834b.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-8/27ff145ed4cc4f3195bd241a543645a056b5408d46c7a2edd93d7769c95a834b.jsonl)

Repair hash: `4c2387c2233bb1ec142531b0e415c20907138d9d5ea2e6956c164480583ed9de`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT t.tableId AS tableId, t.tableNumber AS tableNumber, t.tableCaption AS caption
```


## RAN3_P3_CQ1-9

Original question (unchanged): List the sections whose title contains 'handover' (topic-based section search).

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 193. [Receipt](../reference_outputs/RAN3_P3_CQ1-9/6303544f8801b79ac8a47c6d3eb1bdf821b27df4220983aa25e2dda2fb956bd7.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ1-9/6303544f8801b79ac8a47c6d3eb1bdf821b27df4220983aa25e2dda2fb956bd7.jsonl)

Repair hash: `b63977952d75fa2a718eccb64bce4f0b927d7e1eea0b3d190e1cef45791fc4ff`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section) WHERE toLower(sec.sectionTitle) CONTAINS 'handover' RETURN sec.sectionId, sec.sectionTitle ORDER BY sec.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section) WHERE toLower(sec.sectionTitle) CONTAINS 'handover' RETURN DISTINCT sec.sectionId AS sectionId
```


## RAN3_P3_CQ2-5

Original question (unchanged): List cross-spec references from spec 38.401 to other specs (inter-spec dependencies).

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sectionId, specNumber (string) ← specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 111. [Receipt](../reference_outputs/RAN3_P3_CQ2-5/efb2ca7da008137eb6a54d0d439bee7f820d5830fcfe2e3f1e71d4ee4c3333aa.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ2-5/efb2ca7da008137eb6a54d0d439bee7f820d5830fcfe2e3f1e71d4ee4c3333aa.jsonl)

Repair hash: `fd056cb467089d02dc59d8907d1ff25a80c27fb22740f4cf74bda517b870fb64`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:REFERENCES_SPEC]->(sp:Spec) WHERE sec.sectionId STARTS WITH '38.401-' AND sp.specNumber <> '38.401' RETURN sec.sectionId, sp.specNumber ORDER BY sec.sectionId, sp.specNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.401'}), (sec)-[:REFERENCES_SPEC]->(sp:Spec) WHERE sp.specNumber<>'38.401' RETURN DISTINCT sec.sectionId AS sectionId,sp.specNumber AS specNumber
```


## RAN3_P3_CQ2-6

Original question (unchanged): Return the total number of section cross-references (reference-graph size).

Repair: `scorer_only`. Required answers: referenceEdgeCount (integer) ← totalRefs.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P3_CQ2-6/269aebd1de286baddc2762d15ec7eba4111d4731192f36c8b3fd99641da5bcf2.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ2-6/269aebd1de286baddc2762d15ec7eba4111d4731192f36c8b3fd99641da5bcf2.jsonl)

Repair hash: `78251ba1352da6197c8651cdd31e37834f3d53a30128a7c17d512b4b1947fd1b`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```

Repaired reference query:
```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```


## RAN3_P3_CQ3-1

Original question (unchanged): Return the spec and affected clauses modified by CR R3-253336 (change-scope lookup).

Repair: `scorer_only`. Required answers: specNumber (string) ← sp.specNumber, clausesAffected (string) ← cr.clausesAffected.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P3_CQ3-1/49543be217e14c6f2cf2f7a7666332b7ea91e7788948113205dd86366ce6da1f.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ3-1/49543be217e14c6f2cf2f7a7666332b7ea91e7788948113205dd86366ce6da1f.jsonl)

Repair hash: `f23a9d740cd3305ffbfb9ca047030ed429c133aaae79616ca3accf07516c30a2`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR {tdocNumber: 'R3-253336'})-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, cr.clausesAffected
```

Repaired reference query:
```cypher
MATCH (cr:CR {tdocNumber: 'R3-253336'})-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, cr.clausesAffected
```


## RAN3_P3_CQ3-3

Original question (unchanged): List the CRs that modify spec 38.423 (change history of a spec).

Repair: `query_and_scorer`. Required answers: crTdoc (string) ← crTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2992. [Receipt](../reference_outputs/RAN3_P3_CQ3-3/8d7c39df41e87b672f5769ede27c19764e5ba9eb26e315a2da71a50d6c89e479.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ3-3/8d7c39df41e87b672f5769ede27c19764e5ba9eb26e315a2da71a50d6c89e479.jsonl)

Repair hash: `d2b82d1eb0a0abc9ad4bac649e66aa55025776d3858d5ca1fa88d8e614553c3f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT cr.tdocNumber AS crTdoc
```


## RAN3_P3_CQ3-4

Original question (unchanged): List the CRs that record affected clauses (clause-level change survey).

Repair: `query_and_scorer`. Required answers: crTdoc (string) ← crTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2339. [Receipt](../reference_outputs/RAN3_P3_CQ3-4/f4461bdd40d4132478ef5c23dae19e5a411fb387147c8c738d072e212287edc3.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ3-4/f4461bdd40d4132478ef5c23dae19e5a411fb387147c8c738d072e212287edc3.jsonl)

Repair hash: `2e5b1d337dd6379fa960cbaa41f39b32e847537eed9bc289ce7b4e37afd796d5`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN DISTINCT cr.tdocNumber AS crTdoc
```


## RAN3_P3_CQ3-5

Original question (unchanged): Return the specs modified by CRs under Work Item NR_newRAT-Core (work-item change footprint).

Repair: `query_and_scorer`. Required answers: specNumber (string) ← specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 44. [Receipt](../reference_outputs/RAN3_P3_CQ3-5/f394a7574e3b81646cddf2831076f2ded786add512aa55c76de4addf4c36e02d.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ3-5/f394a7574e3b81646cddf2831076f2ded786add512aa55c76de4addf4c36e02d.jsonl)

Repair hash: `eb6d0d8d0852184fbebc04896f518fa8b49c64ac497fff051a01d49b3c5229e0`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```


## RAN3_P3_CQ3-6

Original question (unchanged): Return the specs that Huawei's CRs modify (company change footprint).

Repair: `query_and_scorer`. Required answers: specNumber (string) ← specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 86. [Receipt](../reference_outputs/RAN3_P3_CQ3-6/d9ca583463e772a18d77864dbea54c1ff0f918a49c74aba06fc64483a8b162c7.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ3-6/d9ca583463e772a18d77864dbea54c1ff0f918a49c74aba06fc64483a8b162c7.jsonl)

Repair hash: `f7f41dc4888f4a2c9ce5e1fc00221d89c3c22c1e246c2646a5e65627d6d46faa`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```


## RAN3_P3_CQ5-1

Original question (unchanged): Return the total number of CRs modifying spec 38.423 (change-volume metric).

Repair: `query_and_scorer`. Required answers: crCount (integer) ← crCount.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P3_CQ5-1/fed51942115c59671128786578f07ce3a1a86cceedfbb8f07223dfff2f2adf2f.json) · [Complete rows](../reference_outputs/RAN3_P3_CQ5-1/fed51942115c59671128786578f07ce3a1a86cceedfbb8f07223dfff2f2adf2f.jsonl)

Repair hash: `147efc4d31f34287c11ffb3a2c2d50cf7076fadfe970f48737777f7b1013b4a8`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN count(cr) AS totalCRs
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
```


## RAN3_P3_P3-S8-CQ02

Original question (unchanged): Check whether every item-level entity node links to a Section via definedInSection (grounding-completeness check).

Repair: `query_and_scorer`. Required answers: allLinked (boolean) ← allLinked.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.json) · [Complete rows](../reference_outputs/RAN3_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.jsonl)

Repair hash: `db8d758b1b262d2c57ecba7438eddbfc3d1efb3fd60cb65762d1b4732af6873f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,EXISTS { MATCH (n)-[:definedInSection]->(:Section) } AS linked RETURN count(DISTINCT n) AS itemCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END) AS unlinkedCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END)=0 AS allLinked
```


## RAN3_P4_CQ2-2

Original question (unchanged): List CRs modifying spec 38.423 that also affect other specs (ripple-effect detection).

Repair: `query_and_scorer`. Required answers: crTdoc (string) ← crTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 136. [Receipt](../reference_outputs/RAN3_P4_CQ2-2/ae812ce39a4527cdef38d227809e499232b6f97b83895acc106653772f8f7d71.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ2-2/ae812ce39a4527cdef38d227809e499232b6f97b83895acc106653772f8f7d71.jsonl)

Repair hash: `a26607e5f6b473c030b0fabe98a99f8a129ac7ea6250c7add07f831bbc806eba`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.423'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.423' } RETURN DISTINCT c.tdocNumber AS crTdoc
```


## RAN3_P4_CQ2-3

Original question (unchanged): List CRs that name spec 38.473 as an affected spec (incoming cross-spec impact).

Repair: `query_and_scorer`. Required answers: crTdoc (string) ← crTdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 353. [Receipt](../reference_outputs/RAN3_P4_CQ2-3/7cc3efbd14961688b777d0be82e1fe8229bc29e94a16d46bd3ed45e4d5a9e3e3.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ2-3/7cc3efbd14961688b777d0be82e1fe8229bc29e94a16d46bd3ed45e4d5a9e3e3.jsonl)

Repair hash: `1d7245d279f1f8941e7333468e9c1a9be0e778e858aee35f53830e80a48656a1`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (s:Spec {specNumber: '38.473'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Spec {specNumber: '38.473'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc
```


## RAN3_P4_CQ3-1

Original question (unchanged): List the CRs in CR pack RP-241113 with their change summaries (pack-content review).

Repair: `query_and_scorer`. Required answers: crTdoc (string) ← crTdoc, summary (string) ← summary.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 37. [Receipt](../reference_outputs/RAN3_P4_CQ3-1/7ae91dd0a82dad8daff91d7d235d2e99f233eefe9a50782900e5814e869902ff.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ3-1/7ae91dd0a82dad8daff91d7d235d2e99f233eefe9a50782900e5814e869902ff.jsonl)

Repair hash: `4d6e14b6c3998de22d1337868472fbdf3256ac517f41b1b9844254b076175f1f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-241113'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-241113'})-[:HAS_CR]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.summaryOfChange AS summary
```


## RAN3_P4_CQ3-2

Original question (unchanged): List the CR packs holding CRs for Work Items matching NR_newRAT (work-item pack tracing).

Repair: `query_and_scorer`. Required answers: crPackId (string) ← crPackId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 59. [Receipt](../reference_outputs/RAN3_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.jsonl)

Repair hash: `e3f702273ede8285d75c0d3be82ccb82b93d3da64462d5669fee74db886fc2bc`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC, pack.crPackId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId
```


## RAN3_P4_CQ3-3

Original question (unchanged): List the CR packs submitted to TSG meeting RAN#110 (plenary submission review).

Repair: `query_and_scorer`. Required answers: crPackId (string) ← crPackId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 18. [Receipt](../reference_outputs/RAN3_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ3-3/c9805b0f0cd2224792cc770b29b11fd142a0664ede2a391cdef7b4e5e61f031b.jsonl)

Repair hash: `72a8693ef688c3b8b16ac1d070c61633e5bf60e80b2facd37161f003e4af2c59`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#110'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#110'}) RETURN DISTINCT pack.crPackId AS crPackId
```


## RAN3_P4_CQ4-1

Original question (unchanged): List the change reasons of CRs modifying section 9.4.5 of spec 38.473 (section-level change rationale).

Repair: `query_and_scorer`. Required answers: reason (string) ← reason.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 308. [Receipt](../reference_outputs/RAN3_P4_CQ4-1/6c959cacced0999e181cf60f2e8f2553d2e83cf86f142dde1abc962127ff3250.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ4-1/6c959cacced0999e181cf60f2e8f2553d2e83cf86f142dde1abc962127ff3250.jsonl)

Repair hash: `4fd3b3edaca4cdaeb7751cffff6421d4848e32d5882062957aa6f05363944857`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section {sectionNumber: '9.4.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.473'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section {sectionNumber: '9.4.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.473'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.reasonForChange AS reason
```


## RAN3_P4_CQ4-3

Original question (unchanged): List the sections modified by CRs for Work Items matching NR_newRAT (work-item section footprint).

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 828. [Receipt](../reference_outputs/RAN3_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl)

Repair hash: `fdd55505a318a2df728fd4eb4df019cca17be075b55cee7153b9c6f488f06719`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
```


## RAN3_P4_CQ4-4

Original question (unchanged): List the specs affected by Samsung's CRs (company cross-spec footprint).

Repair: `query_and_scorer`. Required answers: specNumber (string) ← specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 30. [Receipt](../reference_outputs/RAN3_P4_CQ4-4/89624e477a373b49b7961a691bd4c2d9630cf8a04c4ef18273c4602dccd8d8ef.json) · [Complete rows](../reference_outputs/RAN3_P4_CQ4-4/89624e477a373b49b7961a691bd4c2d9630cf8a04c4ef18273c4602dccd8d8ef.jsonl)

Repair hash: `5ca345e1968b4e0817c2528d3a76151dadce3fbb5c411efd43795bc452cd2ce9`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName = 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS specNumber
```


## RAN3_P5_TR-CQ-1-1

Original question (unchanged): List the completed TRs targeting Rel-17 (release study inventory).

Repair: `scorer_only`. Required answers: trNumber (string) ← tr.trNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-1-1/4ba7db5a9dee7267d1c761b9b36ec7b9c5a09e5291359111d2fc74d921a0533a.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-1-1/4ba7db5a9dee7267d1c761b9b36ec7b9c5a09e5291359111d2fc74d921a0533a.jsonl)

Repair hash: `67194b9f640e15857c145dbacb60acebe4a84a3f3fbb4ca8f8ccbdde3b838432`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release)
                  WHERE r.releaseName = 'Rel-17' AND tr.trStatus = 'Completed'
                  RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release)
                  WHERE r.releaseName = 'Rel-17' AND tr.trStatus = 'Completed'
                  RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN3_P5_TR-CQ-1-4

Original question (unchanged): Show the status distribution across all TRs (study-progress overview).

Repair: `scorer_only`. Required answers: status (string) ← tr.trStatus, trCount (integer) ← cnt.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-1-4/5d268b6a2c0ca0e3dffc5fb21277386a1b82003c1d8d1ab1e3926f40b0c88c36.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-1-4/5d268b6a2c0ca0e3dffc5fb21277386a1b82003c1d8d1ab1e3926f40b0c88c36.jsonl)

Repair hash: `10dcd8a5145d6d3f88f89d8aa4523e1c23c815ccc791d6ebab755a45c6b6c3a8`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport) RETURN tr.trStatus, count(tr) AS cnt ORDER BY cnt DESC
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport) RETURN tr.trStatus, count(tr) AS cnt ORDER BY cnt DESC
```


## RAN3_P5_TR-CQ-2-1

Original question (unchanged): List the specs impacted by TR 38.823 (study-to-spec impact).

Repair: `scorer_only`. Required answers: specNumber (string) ← s.specNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 6. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-2-1/e30221af6f168879cc79c0f78e1e320970a7cc386af6534e1683ccc2c6cf16dc.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-2-1/e30221af6f168879cc79c0f78e1e320970a7cc386af6534e1683ccc2c6cf16dc.jsonl)

Repair hash: `6ad9392520d6aa7e327ffe8fb9909663e7bc944575c40170b5bf9967e28c8d52`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```


## RAN3_P5_TR-CQ-2-2

Original question (unchanged): Return the impact types recorded for TR 38.801 (impact-category profile).

Repair: `scorer_only`. Required answers: impactType (string) ← imp.impactType.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-2-2/fa8ecba6d1cbd01497869db0e84c949c3bdd1b3bbc294444b2cb56615d5424df.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-2-2/fa8ecba6d1cbd01497869db0e84c949c3bdd1b3bbc294444b2cb56615d5424df.jsonl)

Repair hash: `4a5ea8a0cadfde634d4b9268f959056b97b1c1de6cf3c01e57598ebec8adb9a7`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.801'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.801'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```


## RAN3_P5_TR-CQ-2-3

Original question (unchanged): List the TRs whose impact type is NewTS (new-spec-producing studies).

Repair: `scorer_only`. Required answers: trNumber (string) ← tr.trNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-2-3/25c0252cee590a5c71bb274b1558ee9eb6858f62ea65c3490f6ef7fa4401f738.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-2-3/25c0252cee590a5c71bb274b1558ee9eb6858f62ea65c3490f6ef7fa4401f738.jsonl)

Repair hash: `abbe5fb4552d502e35632977abc5f15838ba5d7f53a18f1ce88ecad1975e6e63`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```


## RAN3_P5_TR-CQ-2-4

Original question (unchanged): List the TRs whose impact type is ExtendSection (section-extending studies).

Repair: `scorer_only`. Required answers: trNumber (string) ← tr.trNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 8. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-2-4/81bae9cdc68c73f5edc0e4936060beacc15a5ddd822faa903bd7bfca59609119.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-2-4/81bae9cdc68c73f5edc0e4936060beacc15a5ddd822faa903bd7bfca59609119.jsonl)

Repair hash: `076fd4e7aff5b76902daaf8b4a483b57f8e8df30463b95edf9e6e39365099756`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle
```


## RAN3_P5_TR-CQ-2-5

Original question (unchanged): List the TRs that impacted spec 38.401 (spec-provenance in studies).

Repair: `scorer_only`. Required answers: trNumber (string) ← tr.trNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 36. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-2-5/14735a28e43435a660affc94e8ed2a48b422335005c4405597b941bb52d4b39c.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-2-5/14735a28e43435a660affc94e8ed2a48b422335005c4405597b941bb52d4b39c.jsonl)

Repair hash: `113aab18bac1be43589c71af392da6473fc04d46445559815a5c7acba0fb1fc9`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.401'}) RETURN tr.trNumber, imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.401'}) RETURN tr.trNumber, imp.impactType, imp.impactDescription
```


## RAN3_P5_TR-CQ-3-1

Original question (unchanged): Return which specs TR 38.823 impacts, with impact type and description (study-impact detail).

Repair: `scorer_only`. Required answers: specNumber (string) ← s.specNumber, impactType (string) ← imp.impactType, description (string) ← imp.impactDescription.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 6. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-3-1/34c2a2e5a6210178ec17c0baada8a8359368b836550dab9bec6564aef6e709c0.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-3-1/34c2a2e5a6210178ec17c0baada8a8359368b836550dab9bec6564aef6e709c0.jsonl)

Repair hash: `0fcde5fd7ea04015c9dbdff9fa1feab7e17530aca5efaf170599383fda1509f2`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```


## RAN3_P5_TR-CQ-3-2

Original question (unchanged): Return TR 38.890's impact on specs 38.401 and 38.423 (targeted-impact review).

Repair: `scorer_only`. Required answers: specNumber (string) ← s.specNumber, impactType (string) ← imp.impactType, description (string) ← imp.impactDescription.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 12. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-3-2/86e2e8b5959b8d3fe869f24cb6b565a93d8e9ec9e0efc8e77c86131347e1a622.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-3-2/86e2e8b5959b8d3fe869f24cb6b565a93d8e9ec9e0efc8e77c86131347e1a622.jsonl)

Repair hash: `9900c0372a2de0d1e645ee5a5ede76dc129a3f1b07dd089529a5c813c2966a8b`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.890'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) WHERE s.specNumber IN ['38.401', '38.423'] RETURN s.specNumber, imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.890'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) WHERE s.specNumber IN ['38.401', '38.423'] RETURN s.specNumber, imp.impactType, imp.impactDescription
```


## RAN3_P5_TR-CQ-3-3

Original question (unchanged): Return TR 38.743's impact on spec 38.423 (targeted-impact review).

Repair: `scorer_only`. Required answers: impactType (string) ← imp.impactType, description (string) ← imp.impactDescription.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 6. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-3-3/d78598d30c118bcb299916b65dbb6570d635e96008319e237e32e828f58b1b1f.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-3-3/d78598d30c118bcb299916b65dbb6570d635e96008319e237e32e828f58b1b1f.jsonl)

Repair hash: `e082a47063bd28dc421c38fcb671e749a04b4da674dba334fa35f95c885278bc`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.423'}) RETURN imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.423'}) RETURN imp.impactType, imp.impactDescription
```


## RAN3_P5_TR-CQ-4-1

Original question (unchanged): Return the Rel-17-targeted TRs with their spec-impact types (release study impact map).

Repair: `query_and_scorer`. Required answers: trNumber (string) ← trNumber, specNumber (string) ← specNumber, impactType (string) ← impactType.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 2. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-4-1/7da8951deb214dd828819d6d8f4520cb6827fc63153bbd3179e0150400516aa1.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-4-1/7da8951deb214dd828819d6d8f4520cb6827fc63153bbd3179e0150400516aa1.jsonl)

Repair hash: `c7fcdea5e0a0a5dea0348506b9dbff3178ed548ebdcc988905bbafcc32587473`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber AS trNumber,s.specNumber AS specNumber,imp.impactType AS impactType
```


## RAN3_P5_TR-CQ-4-2

Original question (unchanged): Return the status and scope of TR 38.743 (study status and scope).

Repair: `scorer_only`. Required answers: status (string) ← tr.trStatus, scope (string) ← tr.scope.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-4-2/1ea30e0619ba75ae663f352c57ece061236463f7d01e62bc2a4c3ecc4d35f5bb.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-4-2/1ea30e0619ba75ae663f352c57ece061236463f7d01e62bc2a4c3ecc4d35f5bb.jsonl)

Repair hash: `aef20804fe18877f0ad641a3962b3b19e9f0c2ccc9edf426d4b683de7c468c1f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.743'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```


## RAN3_P5_TR-CQ-4-3

Original question (unchanged): Return TR 38.879's conclusions and its spec impacts (study-to-spec outcome).

Repair: `scorer_only`. Required answers: conclusions (string) ← tr.conclusions, specNumber (string) ← s.specNumber, impactType (string) ← imp.impactType.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct required-field records from the explicit frozen-graph population; no unstated cap", "mode": "all"}`.

Captured native rows: 6. [Receipt](../reference_outputs/RAN3_P5_TR-CQ-4-3/adcbdf536c6b0327b0127c86e5368735e8d0a00c23abb9d479ecd64d2b36ee84.json) · [Complete rows](../reference_outputs/RAN3_P5_TR-CQ-4-3/adcbdf536c6b0327b0127c86e5368735e8d0a00c23abb9d479ecd64d2b36ee84.jsonl)

Repair hash: `2e50e9a6c4135950ae938f2208e8408cdd15367914639a922be5d38ef22c050d`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.879'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.conclusions, s.specNumber, imp.impactType
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.879'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.conclusions, s.specNumber, imp.impactType
```
