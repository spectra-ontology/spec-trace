# RAN1: admitted original-question repairs

Both recorded judgments are separate AI reviews; neither is expert certification.


## RAN1_P1_CQ1-1

Original question (unchanged): List the TDocs at meeting RAN1#120 tied to Work Item NR_eMIMO-Core (MIMO meeting preparation).

Repair: `scorer_only`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 2. [Receipt](../reference_outputs/RAN1_P1_CQ1-1/315fb08e406e4ba210445c7d6254a11930d9cad6aa82065358903ba5d4a997d5.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ1-1/315fb08e406e4ba210445c7d6254a11930d9cad6aa82065358903ba5d4a997d5.jsonl)

Repair hash: `8f4b703b29c876b3a01e7744dc6da644b7a88e154c7731fd143ec86eea83e50d`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```


## RAN1_P1_CQ1-2

Original question (unchanged): List the TDocs under Agenda Item 9.2 (AI/ML for NR) at meeting RAN1#121 (AI/ML session preparation).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 129. [Receipt](../reference_outputs/RAN1_P1_CQ1-2/3a7fdc79903d986b4899409246f83ebca45b1a03dc74eb346a68a39ac21204e2.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ1-2/3a7fdc79903d986b4899409246f83ebca45b1a03dc74eb346a68a39ac21204e2.jsonl)

Repair hash: `a484c8ffb7465760e05030b094a4dd142ca931dd606ac841d2d31ae6f507f578`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.2' RETURN t.tdocNumber, t.title, t.type, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE (a.agendaNumber = '9.2' OR a.agendaNumber STARTS WITH '9.2.') RETURN DISTINCT t.tdocNumber, t.title, t.type, a.agendaNumber
```


## RAN1_P1_CQ1-3

Original question (unchanged): List the TDocs submitted by Huawei at meeting RAN1#120 (tracking a competitor's contributions).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 110. [Receipt](../reference_outputs/RAN1_P1_CQ1-3/9a6bc0f4c06527926c87bfd3b081dfe57919ef1fd42e991cd996c83bd768a190.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ1-3/9a6bc0f4c06527926c87bfd3b081dfe57919ef1fd42e991cd996c83bd768a190.jsonl)

Repair hash: `a563126a0b47a4f2e009d5d3d172f0f5cca19a4d6babf40654ce30ed586d3e17`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN1_P1_CQ1-5

Original question (unchanged): List the TDocs approved or agreed at meeting RAN1#121.

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 102. [Receipt](../reference_outputs/RAN1_P1_CQ1-5/d775c9f78a085c7febe3989770912c028b17923d6fde03cd525dcf2edda99455.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ1-5/d775c9f78a085c7febe3989770912c028b17923d6fde03cd525dcf2edda99455.jsonl)

Repair hash: `6c90ab7a06a0c53a5543b0e6f0c632ba95986d023c343451acc5f3fa0ac25a56`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN1_P1_CQ1-8

Original question (unchanged): Who is the contact person for TDoc R1-2501234? (contact lookup)

Repair: `scorer_only`. Required answers: ct.contactName (string) ← ct.contactName.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P1_CQ1-8/3384691ac1e417dc56c4590ca5fc9d2662a67586a00e745271c5760dfa74d958.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ1-8/3384691ac1e417dc56c4590ca5fc9d2662a67586a00e745271c5760dfa74d958.jsonl)

Repair hash: `170422799d129ae6ee9bcdd24f0707758a25968ffd5fa8b06f2cb0fc5240e6b4`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'})-[:HAS_CONTACT]->(ct:Contact) RETURN t.tdocNumber, ct.contactName LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2501234'})-[:HAS_CONTACT]->(ct:Contact) RETURN t.tdocNumber, ct.contactName LIMIT 1
```


## RAN1_P1_CQ2-3

Original question (unchanged): Which LS does TDoc R1-2000004 reply to? (reply-chain tracing)

Repair: `query_and_scorer`. Required answers: original_tdoc (string) ← original_tdoc.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P1_CQ2-3/73761b710b0f9f7d99dc5e4429db045ce4aca96846ec8072918537e326f2524c.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ2-3/73761b710b0f9f7d99dc5e4429db045ce4aca96846ec8072918537e326f2524c.jsonl)

Repair hash: `10ec16496b34ae2252a8730ad759a99bbca2fa12a69f982b2c13267a413e9ffe`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2000004'})-[:REPLY_TO]->(original:Tdoc) RETURN t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2000004'})-[:REPLY_TO]->(original:Tdoc) WHERE original.type IN ['LS in', 'LS out'] RETURN DISTINCT t.tdocNumber AS reply_tdoc, t.title AS reply_title, original.tdocNumber AS original_tdoc, original.title AS original_title
```


## RAN1_P1_CQ2-4

Original question (unchanged): List the CRs modifying TS 38.214 with their status (revision status of 38.214).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber, t.status (string) ← t.status.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 2423. [Receipt](../reference_outputs/RAN1_P1_CQ2-4/6dcbcb3ecd2315ab79605fc002304e8edeed8b165bc37d210f857d896a9e6c19.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ2-4/6dcbcb3ecd2315ab79605fc002304e8edeed8b165bc37d210f857d896a9e6c19.jsonl)

Repair hash: `ebf0063a4477b7c3f88a3a74f1126ef83e0633e33b9cf77d8625bcc83f472725`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN t.tdocNumber, t.title, t.status, t.type ORDER BY t.tdocNumber ASC LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN DISTINCT t.tdocNumber, t.title, t.status, t.type
```


## RAN1_P1_CQ2-5

Original question (unchanged): What are the change category (F/A/B/C/D) and affected clauses of CR R1-2504971?

Repair: `scorer_only`. Required answers: t.crCategory (string) ← t.crCategory, t.clausesAffected (string) ← t.clausesAffected.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P1_CQ2-5/5a38409adc2c0b565017c55b2f8f1adcbac2459d76732fe303308402ed7e1a0e.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ2-5/5a38409adc2c0b565017c55b2f8f1adcbac2459d76732fe303308402ed7e1a0e.jsonl)

Repair hash: `820d4d7472cdbc0c3e03bbca0908dc4c32c3bf1916475ef05171ca550676a1aa`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2504971'}) RETURN t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R1-2504971'}) RETURN t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status LIMIT 1
```


## RAN1_P1_CQ2-7

Original question (unchanged): List the incoming LSs (LS in) at meeting RAN1#120 and their agenda items (reviewing other WGs' requests).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber, a.agendaNumber (string) ← a.agendaNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 32. [Receipt](../reference_outputs/RAN1_P1_CQ2-7/b75ed76895cdaf0f453dcce1ed6d46b3f51ee128d3a824f221b49d75cc2a354b.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ2-7/b75ed76895cdaf0f453dcce1ed6d46b3f51ee128d3a824f221b49d75cc2a354b.jsonl)

Repair hash: `66a62d2bfa975c297bdb1a1ca6e2a5bcb35f34167b85dc982c0ed66d3ca3a36d`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg
```


## RAN1_P1_CQ3-1

Original question (unchanged): List the TDocs Samsung submitted under Work Item NR_MIMO_evo_DL_UL-Core (NR MIMO Evolution).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 299. [Receipt](../reference_outputs/RAN1_P1_CQ3-1/7599aa68ac76ec892ae2869db40c43842a5d1898b2acc3364c62f7f7144207ba.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ3-1/7599aa68ac76ec892ae2869db40c43842a5d1898b2acc3364c62f7f7144207ba.jsonl)

Repair hash: `c85ffbdf966a7285fbefa7a3460bd9d08d40b9bbed0cf4803bed4059da1712ab`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN1_P1_CQ3-3

Original question (unchanged): Which companies contributed most to Work Item NR_unlic-Core (NR-U)? Top 10 by TDoc count (competitive landscape).

Repair: `scorer_only`. Required answers: c.companyName (string) ← c.companyName.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "tdocCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "top_k", "notes": "at most ten companies; no extra boundary ties", "tie_policy": "company name ascending; exactly ten at most, excluding extra boundary ties", "value": 10}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN1_P1_CQ3-3/93ff96315d95d275ddc2dc2b2ce33161a6d485cf4322f59f67140f2a169df9d9.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ3-3/93ff96315d95d275ddc2dc2b2ce33161a6d485cf4322f59f67140f2a169df9d9.jsonl)

Repair hash: `d0c16db8910687e1ed7941be1c49d101abbd9519091c9bc460fcdeabb32e73a6`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10
```


## RAN1_P1_CQ3-4

Original question (unchanged): What share and count of Qualcomm's TDocs were approved or agreed? (contribution success rate)

Repair: `scorer_only`. Required answers: approved (integer) ← approved, approvalRate (number) ← approvalRate.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "one aggregate record, including zero-total case", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P1_CQ3-4/44a809591dd2802f90bb79c182d7be815000a260c913df9f0c85a19ca7092866.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ3-4/44a809591dd2802f90bb79c182d7be815000a260c913df9f0c85a19ca7092866.jsonl)

Repair hash: `28a8b768327fa2e1825f9f003c7505bd5fefedc191db5070ad3fe5d015c3ea42`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Company {companyName: 'Qualcomm'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, round(100.0 * approved / total, 1) AS approvalRate LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company {companyName: 'Qualcomm'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, round(100.0 * approved / total, 1) AS approvalRate LIMIT 10
```


## RAN1_P1_CQ3-5

Original question (unchanged): List other companies' TDocs under the same agenda item as TDoc R1-2501234 (checking competing contributions).

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 162. [Receipt](../reference_outputs/RAN1_P1_CQ3-5/47b281e5bcf7cffcc0fdbb3c4247edcc33060e7fa270fd15bedaf88720882db6.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ3-5/47b281e5bcf7cffcc0fdbb3c4247edcc33060e7fa270fd15bedaf88720882db6.jsonl)

Repair hash: `8eabfee994765a047c69db13230aff768b7c0cb88cc8a6ab4f79e8ffd0e1d721`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber AND NOT EXISTS { MATCH (t0)-[:SUBMITTED_BY]->(c) } RETURN DISTINCT t.tdocNumber, t.title, c.companyName, a.agendaNumber
```


## RAN1_P1_CQ3-6

Original question (unchanged): What are Nokia's main technical areas? Top 10 Work Items by contribution count.

Repair: `scorer_only`. Required answers: wi.workItemCode (string) ← wi.workItemCode.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "tdocCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "top_k", "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.", "short_population": "all_available", "tie_policy": "exact_k", "value": 10}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN1_P1_CQ3-6/d8c3c3bf248aeaf51a0a874e01be33280fd9e456a4bd8a36501886aadc698325.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ3-6/d8c3c3bf248aeaf51a0a874e01be33280fd9e456a4bd8a36501886aadc698325.jsonl)

Repair hash: `ad70075d64003a814d926944a2a8d8e8f811ce585c754b5a7d64dbc3a6d665a5`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Company {companyName: 'Nokia'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS tdocCount ORDER BY tdocCount DESC, wi.workItemCode ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company {companyName: 'Nokia'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS tdocCount ORDER BY tdocCount DESC, wi.workItemCode ASC LIMIT 10
```


## RAN1_P1_CQ4-1

Original question (unchanged): List Samsung's contributions to Work Item NR_eMIMO-Core across past meetings (tracing a technical history).

Repair: `query_and_scorer`. Required answers: m.meetingNumber (string) ← m.meetingNumber, t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 123. [Receipt](../reference_outputs/RAN1_P1_CQ4-1/94089c3e91cc31bd90e45b199ee05fed1bce3dab81a4a44c39d3f89a349df32e.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ4-1/94089c3e91cc31bd90e45b199ee05fed1bce3dab81a4a44c39d3f89a349df32e.jsonl)

Repair hash: `eb4c5b790d7e1997f0341dde012cd3dac18999ab777596f4291837857ec63c88`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.meetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN DISTINCT m.meetingNumber, t.tdocNumber, t.title, t.status
```


## RAN1_P1_CQ4-2

Original question (unchanged): Summarize the outcome of Ericsson's contributions at meeting RAN1#120 by status (count per status).

Repair: `scorer_only`. Required answers: t.status (string) ← t.status, count (integer) ← count.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 7. [Receipt](../reference_outputs/RAN1_P1_CQ4-2/ae07c5c70a599d665459c720f63099abef19c1b146a88583119762b6d49dcdf5.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ4-2/ae07c5c70a599d665459c720f63099abef19c1b146a88583119762b6d49dcdf5.jsonl)

Repair hash: `70bac4660e031e245c2a02f8aa76cd1edc42898802d21a9c154fa6cc6f8566c4`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(t) AS count ORDER BY count DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(t) AS count ORDER BY count DESC LIMIT 10
```


## RAN1_P1_CQ4-3

Original question (unchanged): List the TDocs still not treated under Agenda Item 9.3 (NR duplex evolution) at meeting RAN1#120.

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 101. [Receipt](../reference_outputs/RAN1_P1_CQ4-3/8d3f16739420010921945be90a36d252b3d2ad027dcdded54725717e897dec52.json) · [Complete rows](../reference_outputs/RAN1_P1_CQ4-3/8d3f16739420010921945be90a36d252b3d2ad027dcdded54725717e897dec52.jsonl)

Repair hash: `9f88eb35ae02d310a85d5252e96aab1e9fafbc91ce52da139ed99b5d59b3e67f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE a.agendaNumber STARTS WITH '9.3' AND t.status = 'not treated' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WHERE (a.agendaNumber = '9.3' OR a.agendaNumber STARTS WITH '9.3.') AND t.status = 'not treated' RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber
```


## RAN1_P2_CQ1-1

Original question (unchanged): List the agreements under Agenda Item 7.1 (NR MIMO) at meeting RAN1#115 (MIMO meeting outcomes).

Repair: `query_and_scorer`. Required answers: a.resolutionId (string) ← a.resolutionId, a.content (string) ← a.content.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 11. [Receipt](../reference_outputs/RAN1_P2_CQ1-1/57698c835e530fdd1d4dbadbbfca982ac8add8b75c47532d3e428f20638b5e47.json) · [Complete rows](../reference_outputs/RAN1_P2_CQ1-1/57698c835e530fdd1d4dbadbbfca982ac8add8b75c47532d3e428f20638b5e47.jsonl)

Repair hash: `acf44955c1cff045b7be9b990cd46367c3b8061a74c34f2a221f4ac3340232c0`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem), (a)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE (ai.agendaNumber = '7.1' OR ai.agendaNumber STARTS WITH '7.1.') RETURN DISTINCT a.resolutionId, a.content, ai.agendaNumber
```


## RAN1_P2_CQ1-4

Original question (unchanged): List the working assumptions from meeting RAN1#115 (items that may be revisited).

Repair: `scorer_only`. Required answers: wa.resolutionId (string) ← wa.resolutionId, wa.content (string) ← wa.content.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 5. [Receipt](../reference_outputs/RAN1_P2_CQ1-4/dbe5804943947ef42f82752e8cd41b20beb8ff3824dcfb253568008d5d580e5f.json) · [Complete rows](../reference_outputs/RAN1_P2_CQ1-4/dbe5804943947ef42f82752e8cd41b20beb8ff3824dcfb253568008d5d580e5f.jsonl)

Repair hash: `731a69c97292a6921eb51d0417ca941ece76ca7a23651cd2cd2a8f4dbb562b4e`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```


## RAN1_P2_CQ2-1

Original question (unchanged): List the TDocs referenced by Agreement AGR-100-6.1-001 (tracing the source documents behind a decision).

Repair: `scorer_only`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 4. [Receipt](../reference_outputs/RAN1_P2_CQ2-1/d27a861a5f6466910ab60ba912585e280632a5e4dd28849809d3b5e639042039.json) · [Complete rows](../reference_outputs/RAN1_P2_CQ2-1/d27a861a5f6466910ab60ba912585e280632a5e4dd28849809d3b5e639042039.jsonl)

Repair hash: `fed389cb2476dcb1328e6795c5ece2875bdc3c20780fc390c8aa715f75fc4d12`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```

Repaired reference query:
```cypher
MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```


## RAN1_P2_CQ3-6

Original question (unchanged): Which of ZTE's TDocs were approved? (approval track record)

Repair: `query_and_scorer`. Required answers: t.tdocNumber (string) ← t.tdocNumber.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 70. [Receipt](../reference_outputs/RAN1_P2_CQ3-6/0d126a6f371d1d4046b3d0feaf8e73d3ea487a32c1129490a8e0e5a06d79c390.json) · [Complete rows](../reference_outputs/RAN1_P2_CQ3-6/0d126a6f371d1d4046b3d0feaf8e73d3ea487a32c1129490a8e0e5a06d79c390.jsonl)

Repair hash: `a12f7419e636ff622272066bd7110b464a1e31ae516ca1de1165bcea7ffa5fae`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN DISTINCT t.tdocNumber, t.title
```


## RAN1_P2_CQ4-3

Original question (unchanged): Which companies handled the most FL summaries? Top 10 (technical-leadership ranking).

Repair: `scorer_only`. Required answers: c.companyName (string) ← c.companyName.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "flCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "top_k", "notes": "at most ten companies", "tie_policy": "company name ascending", "value": 10}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN1_P2_CQ4-3/9e7977eb1075a2e9e094b7643ec0756d1c0a18fa58446b9b744fe17f6365eab0.json) · [Complete rows](../reference_outputs/RAN1_P2_CQ4-3/9e7977eb1075a2e9e094b7643ec0756d1c0a18fa58446b9b744fe17f6365eab0.jsonl)

Repair hash: `064171aa46d5f3c5ea17650dcbe3ba46e38225d8e1e7789ff81ac1b053d84b20`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 10
```


## RAN1_P3_CQ004

Original question (unchanged): Return the section count per level in TS 38.213 (gauging structural depth and complexity).

Repair: `scorer_only`. Required answers: level (integer) ← sec.level, sectionCount (integer) ← sectionCount.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct originally requested role records; no unstated cap", "mode": "all"}`.

Captured native rows: 5. [Receipt](../reference_outputs/RAN1_P3_CQ004/bdd29f3e07b098101d01fc5239407d2b167f8ec531bd1aa69dc823d29b9c2a94.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ004/bdd29f3e07b098101d01fc5239407d2b167f8ec531bd1aa69dc823d29b9c2a94.jsonl)

Repair hash: `210284cb1f5b3e131dcaf554831892ce1f2a2944636a2d174874f69f9ea1a04d`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) RETURN sec.level, count(sec) AS sectionCount ORDER BY sec.level
```


## RAN1_P3_CQ005

Original question (unchanged): Which sections of TS 38.213 contain the most tables? (finding parameter-dense implementation points)

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct originally requested role records; no unstated cap", "mode": "all"}`.

Captured native rows: 2. [Receipt](../reference_outputs/RAN1_P3_CQ005/44bb90db8583507f882a015bd8a5a3820f7f0b398777758850ddfef5f589799e.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ005/44bb90db8583507f882a015bd8a5a3820f7f0b398777758850ddfef5f589799e.jsonl)

Repair hash: `b06082733737106a5f505fa983724c6189bc2cb3f89cbb440aaa18a94da7a5a6`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.213'}) MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sec.sectionNumber, sec.sectionTitle, count(tbl) AS tableCount ORDER BY tableCount DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.213'}) WITH DISTINCT sec OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec,count(DISTINCT tbl) AS tableCount WITH collect({sec:sec,n:tableCount}) AS grouped,max(tableCount) AS maxCount UNWIND grouped AS g WITH g,maxCount WHERE g.n=maxCount RETURN g.sec.sectionId AS sectionId,g.sec.sectionNumber AS sectionNumber,g.n AS tableCount
```


## RAN1_P3_CQ006

Original question (unchanged): List all tables defined in TS 38.214 (parameter tables to reference during implementation).

Repair: `query_and_scorer`. Required answers: tableId (string) ← tbl.tableId.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 548. [Receipt](../reference_outputs/RAN1_P3_CQ006/598a3b73230b3ef68716968cf087d2f2d0528dccd9e3a194b57b971e2e79f90c.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ006/598a3b73230b3ef68716968cf087d2f2d0528dccd9e3a194b57b971e2e79f90c.jsonl)

Repair hash: `904f3a917e66fdb1ef5e52a69fd5f97995a5756c4910eeab75eecd76b78bbeda`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.214'}) RETURN tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY tbl.tableNumber
```

Repaired reference query:
```cypher
MATCH (tbl:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.214'}) RETURN DISTINCT tbl.tableId,tbl.tableNumber,tbl.tableCaption,sec.sectionId
```


## RAN1_P3_CQ007

Original question (unchanged): Find sections whose title contains 'PDSCH' across all TSs (locating PDSCH content).

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sec.sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 57. [Receipt](../reference_outputs/RAN1_P3_CQ007/b80adfc4248baed71fa19df41e4369bcf4f575ec851ed50c2ad38af3a708d945.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ007/b80adfc4248baed71fa19df41e4369bcf4f575ec851ed50c2ad38af3a708d945.jsonl)

Repair hash: `8b4c547ad35df2c97ae02cdb2b931f5250bd9b0b387f5409fc4a5244f02607fa`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level ORDER BY sp.specNumber, sec.sectionNumber
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDSCH.*' RETURN DISTINCT sp.specNumber,sec.sectionId,sec.sectionNumber,sec.sectionTitle
```


## RAN1_P3_CQ012

Original question (unchanged): Are there mutually referencing section pairs within TS 38.213? (tightly coupled procedures)

Repair: `query_and_scorer`. Required answers: hasMutualReferences (boolean) ← hasMutualReferences.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "one Boolean record", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P3_CQ012/737e533ef0c2ab11aa79bdd31b0fa7bbfd5efc6314777a9c0f70737d8d8e017d.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ012/737e533ef0c2ab11aa79bdd31b0fa7bbfd5efc6314777a9c0f70737d8d8e017d.jsonl)

Repair hash: `3dbe6ad3a5a2dddbbfa3755e3c31031cafaea242d0164a66ec09caf1a5c499c1`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId STARTS WITH '38.213' AND b.sectionId STARTS WITH '38.213' AND a.sectionId < b.sectionId RETURN a.sectionNumber AS sectionA, a.sectionTitle AS titleA, b.sectionNumber AS sectionB, b.sectionTitle AS titleB ORDER BY a.sectionId, b.sectionId LIMIT 20
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.213'}),(b:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.213'}),(a)-[:REFERENCES_SECTION]->(b)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId RETURN count(DISTINCT a)>0 AS hasMutualReferences
```


## RAN1_P3_CQ013

Original question (unchanged): Compare cross-section reference density across the TSs (how tightly each is internally linked).

Repair: `query_and_scorer`. Required answers: ts (string) ← ts, refDensity (number) ← refDensity.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 8. [Receipt](../reference_outputs/RAN1_P3_CQ013/a67b945634ed767611f985989c060be5077a91ac81c72025485ab0c9379e9d39.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ013/a67b945634ed767611f985989c060be5077a91ac81c72025485ab0c9379e9d39.jsonl)

Repair hash: `0a7d5688e4ec5e98f0ee794100aa24bdd67a489a2c5f4f78ee4ba0dfef07ec3b`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts, count(sec) AS secCnt OPTIONAL MATCH (src:Section)-[:REFERENCES_SECTION]->(tgt:Section) WHERE src.sectionId STARTS WITH ts WITH ts, secCnt, count(*) AS refCnt RETURN ts, secCnt, refCnt, round(toFloat(refCnt) / secCnt * 100) / 100 AS refDensity ORDER BY refDensity DESC
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WITH sp.specNumber AS ts,count(DISTINCT sec) AS secCnt OPTIONAL MATCH (src:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec),(src)-[:REFERENCES_SECTION]->(tgt:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec) WHERE sp1.specNumber=ts AND sp2.specNumber=ts WITH ts,secCnt,count(DISTINCT CASE WHEN src IS NOT NULL AND tgt IS NOT NULL THEN [src,tgt] ELSE null END) AS refCnt RETURN ts,secCnt,refCnt,CASE WHEN secCnt=0 THEN null ELSE round(100.0*refCnt/secCnt)/100.0 END AS refDensity
```


## RAN1_P3_CQ014

Original question (unchanged): Find section pairs that reference each other (checking for circular dependencies).

Repair: `query_and_scorer`. Required answers: sectionA (string) ← sectionA, sectionB (string) ← sectionB.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 188. [Receipt](../reference_outputs/RAN1_P3_CQ014/5852f1235d9d2cf60faf1045302cd8a831011467011be8b346b3a5998af9ad6e.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ014/5852f1235d9d2cf60faf1045302cd8a831011467011be8b346b3a5998af9ad6e.jsonl)

Repair hash: `cb3f92d8c8c518f5d983e3f3cb053771a1a2841e467ba02c64626569bb5622be`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId MATCH (a)-[:BELONGS_TO_SPEC]->(sp1:Spec) MATCH (b)-[:BELONGS_TO_SPEC]->(sp2:Spec) RETURN sp1.specNumber + '-' + a.sectionNumber AS sectionA, sp2.specNumber + '-' + b.sectionNumber AS sectionB ORDER BY a.sectionId, b.sectionId LIMIT 20
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section)-[:REFERENCES_SECTION]->(a) WHERE a.sectionId < b.sectionId RETURN DISTINCT a.sectionId AS sectionA,b.sectionId AS sectionB
```


## RAN1_P3_CQ016

Original question (unchanged): How many CRs have been raised against TS 38.214? (how actively it is revised)

Repair: `scorer_only`. Required answers: totalCR (integer) ← totalCR.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "one integer aggregate record", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P3_CQ016/97802a458e04cec24e82a9b1b351e85e0a844b0626e8551f6847c882f612c8a9.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ016/97802a458e04cec24e82a9b1b351e85e0a844b0626e8551f6847c882f612c8a9.jsonl)

Repair hash: `436e0cfdccffe729f9b1cb134bc1b5f9c5a718c7eeb49a92722b80f351d5f35a`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(cr) AS totalCR
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) RETURN count(cr) AS totalCR
```


## RAN1_P3_CQ019

Original question (unchanged): Compare CR counts across the eight TSs (where standardization activity concentrates).

Repair: `scorer_only`. Required answers: sp.specNumber (string) ← sp.specNumber, crCount (integer) ← crCount.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 8. [Receipt](../reference_outputs/RAN1_P3_CQ019/60249b5548186c18274678a8c46765fe819c8f7dd0eea21d103625ee17b8917e.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ019/60249b5548186c18274678a8c46765fe819c8f7dd0eea21d103625ee17b8917e.jsonl)

Repair hash: `35dc95bb667fbe832bddd0313e221360711cd39d4745e01afd7142c726874a5e`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC
```


## RAN1_P3_CQ022

Original question (unchanged): Show the trend of TS 38.213 CR submissions per meeting (standardization-activity trend).

Repair: `query_and_scorer`. Required answers: meeting (string) ← meeting, crCount (integer) ← crCount.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "asc", "source_column": "meetingInt"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "all", "notes": "exactly one record per qualifying recorded meeting; all such meetings are returned"}`.

Captured native rows: 60. [Receipt](../reference_outputs/RAN1_P3_CQ022/855328dc20c56b10c6e4f5e4a898785b615ccc3815ab2990b7f45a9f4c9c6a4a.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ022/855328dc20c56b10c6e4f5e4a898785b615ccc3815ab2990b7f45a9f4c9c6a4a.jsonl)

Repair hash: `ee43ff339c9c48660bad114534d481005d325278e5066aab29d72a9809a013b3`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) WITH m.meetingNumber AS meeting, m.meetingNumberInt AS meetingInt, count(cr) AS crCount RETURN meeting, crCount ORDER BY meetingInt
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (cr:CR)-[:PRESENTED_AT]->(m),(cr)-[:MODIFIES]->(:Spec {specNumber:'38.213'}) RETURN m.meetingNumber AS meeting,m.meetingNumberInt AS meetingInt,count(DISTINCT cr) AS crCount ORDER BY meetingInt ASC,meeting ASC
```


## RAN1_P3_CQ027

Original question (unchanged): Are there agreements that reference CRs across multiple TSs at once? (cross-TS decisions)

Repair: `query_and_scorer`. Required answers: hasCrossSpecAgreement (boolean) ← hasCrossSpecAgreement.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "one Boolean record", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P3_CQ027/1cff3c4cf69da88c4a932fa096102ac16c55a0d5dcda506e64ab2a42350c5e91.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ027/1cff3c4cf69da88c4a932fa096102ac16c55a0d5dcda506e64ab2a42350c5e91.jsonl)

Repair hash: `a4462f9c8901722d48407b1e8148f4efbcbc12577975ce5761000601471afd5a`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH agr, collect(DISTINCT sp.specNumber) AS specs WHERE size(specs) > 1 MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN agr.resolutionId, specs, m.meetingNumber ORDER BY m.meetingNumberInt DESC, agr.resolutionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (agr:Agreement)-[:REFERENCES]->(:CR)-[:MODIFIES]->(sp:Spec) WITH agr,count(DISTINCT sp.specNumber) AS specCount WHERE specCount>1 RETURN count(DISTINCT agr)>0 AS hasCrossSpecAgreement
```


## RAN1_P3_CQ037

Original question (unchanged): Rank companies by total CRs submitted across the eight TSs (who the major players are).

Repair: `query_and_scorer`. Required answers: co.companyName (string) ← co.companyName.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "crCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "all", "notes": "all matching Company groups"}`.

Captured native rows: 71. [Receipt](../reference_outputs/RAN1_P3_CQ037/50d8124665e2b07f7de906d05cdd659d4cd77037e1e0b3083b1fe60ae6f62bfc.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ037/50d8124665e2b07f7de906d05cdd659d4cd77037e1e0b3083b1fe60ae6f62bfc.jsonl)

Repair hash: `f4502c783f787c21802374bca297fd1b90424e850f49b454e28b5fffce89713f`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC, co.companyName ASC
```


## RAN1_P3_CQ041

Original question (unchanged): Which sections contain five or more tables? (parameter-dense implementation points)

Repair: `query_and_scorer`. Required answers: sectionId (string) ← sec.sectionId.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 98. [Receipt](../reference_outputs/RAN1_P3_CQ041/29c75e4856a2d581172ee368fb25dda8a8054bd2820d597f60945d2c80969590.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ041/29c75e4856a2d581172ee368fb25dda8a8054bd2820d597f60945d2c80969590.jsonl)

Repair hash: `e85f8e0824dabc27b751f79bf759e86982c581dfc69da86dc2acf15dc644fffe`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec, count(tbl) AS tableCount WHERE tableCount >= 5 MATCH (sec)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, tableCount ORDER BY tableCount DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:CONTAINS_TABLE]->(tbl:TSTable) WITH sec,count(DISTINCT tbl) AS tableCount WHERE tableCount>=5 RETURN sec.sectionId,tableCount
```


## RAN1_P3_CQ044

Original question (unchanged): List the TSs modified by CRs under Work Item NR_newRAT-Core (portfolio impact of this work item).

Repair: `scorer_only`. Required answers: spec (string) ← spec.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 16. [Receipt](../reference_outputs/RAN1_P3_CQ044/8838c696e14c30f4c3627e0c295607579cd95b9d2a82b8381b5e52522985059f.json) · [Complete rows](../reference_outputs/RAN1_P3_CQ044/8838c696e14c30f4c3627e0c295607579cd95b9d2a82b8381b5e52522985059f.jsonl)

Repair hash: `06b02612e1e8da9a03afd1811123fc228b421444499a83d40ff9289e1b5688b8`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(cr) AS crCount ORDER BY crCount DESC
```

Repaired reference query:
```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(cr) AS crCount ORDER BY crCount DESC
```


## RAN1_P3_P3-S8-CQ02

Original question (unchanged): Are all item-level entity nodes linked to a Section via :definedInSection? (grounding-coverage check)

Repair: `query_and_scorer`. Required answers: allLinked (boolean) ← allLinked.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "one Boolean record", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P3_P3-S8-CQ02/355597e5fd81eeb9b3ef5d5ede7b2503a1053ed717ae1b01e72d8b004003c78f.json) · [Complete rows](../reference_outputs/RAN1_P3_P3-S8-CQ02/355597e5fd81eeb9b3ef5d5ede7b2503a1053ed717ae1b01e72d8b004003c78f.jsonl)

Repair hash: `523123b89501f2fb8e16895a5ed859cfd47c22df8142a811b86ddec47af877dc`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,exists((n)-[:definedInSection]->(:Section)) AS linked RETURN count(n)=sum(CASE WHEN linked THEN 1 ELSE 0 END) AS allLinked
```


## RAN1_P3_P3-S8-CQ05

Original question (unchanged): What is the granularity-property distribution across the five entity classes? (item-level vs. section-level)

Repair: `query_and_scorer`. Required answers: class (string) ← class, granularity (string) ← granularity, c (integer) ← c.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P3_P3-S8-CQ05/833993bba0052cf15fc9bce0b5402b6895872eb764d5ff0cc5564f719e2db3ad.json) · [Complete rows](../reference_outputs/RAN1_P3_P3-S8-CQ05/833993bba0052cf15fc9bce0b5402b6895872eb764d5ff0cc5564f719e2db3ad.jsonl)

Repair hash: `2a9c7c5483f00926e919c3218ffa16d312340281922a685cfd0778ab9b7c96c3`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

Repaired reference query:
```cypher
MATCH (n) UNWIND [l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'] WHERE l IN labels(n)] AS class RETURN class,n.granularity AS granularity,count(DISTINCT n) AS c
```


## RAN1_P4_CQ1-3

Original question (unchanged): What happens if the CRs under Work Item NR_LPWUS-Core (Rel-19 LP-WUS/WUR) are not approved? (consequences-if-not-approved)

Repair: `scorer_only`. Required answers: cr.consequencesIfNotApproved (string) ← cr.consequencesIfNotApproved.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 14. [Receipt](../reference_outputs/RAN1_P4_CQ1-3/2214e4f6525d43313c9bc11535b31630a68bf2d5d6048d1323e9d213671108d8.json) · [Complete rows](../reference_outputs/RAN1_P4_CQ1-3/2214e4f6525d43313c9bc11535b31630a68bf2d5d6048d1323e9d213671108d8.jsonl)

Repair hash: `a527b2f812be8f2703807c07d77f5fee9543e00ca1db34a02f68a99dec6c5d60`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved ORDER BY cr.tdocNumber DESC
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved ORDER BY cr.tdocNumber DESC
```


## RAN1_P4_CQ2-1

Original question (unchanged): List the five specs CR R1-2504971 affects and the impact type (Core/Test/OM) for each.

Repair: `scorer_only`. Required answers: sp.specNumber (string) ← sp.specNumber, relationType (string) ← relationType.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "exact", "notes": "five requested distinct specification/type records; retained native output contains five distinct spec numbers", "value": 5}`.

Captured native rows: 5. [Receipt](../reference_outputs/RAN1_P4_CQ2-1/3d3cf39e90d5c656bc0066c549b7a8d70f5a0309059c37fd9266a54f0c2210be.json) · [Complete rows](../reference_outputs/RAN1_P4_CQ2-1/3d3cf39e90d5c656bc0066c549b7a8d70f5a0309059c37fd9266a54f0c2210be.jsonl)

Repair hash: `6259cd37cd5d081340d7079f1669f7662450ab6c90b78b3763b45058c2781536`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR {tdocNumber: 'R1-2504971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, sp.specNumber, type(r) AS relationType ORDER BY sp.specNumber ASC
```

Repaired reference query:
```cypher
MATCH (cr:CR {tdocNumber: 'R1-2504971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, sp.specNumber, type(r) AS relationType ORDER BY sp.specNumber ASC
```


## RAN1_P4_CQ2-4

Original question (unchanged): Which 10 CRs have the widest cross-spec reach, and which specs does each affect?

Repair: `query_and_scorer`. Required answers: cr.tdocNumber (string) ← cr.tdocNumber, affectedSpecs (json) ← affectedSpecs.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "affectedSpecCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "top_k", "notes": "Exactly min(10, complete eligible stored grouping population), using every declared order key.", "short_population": "all_available", "tie_policy": "exact_k", "value": 10}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN1_P4_CQ2-4/5f6236e91e76317f5b97c778366fc70e453d1f88949bdf06aa61a99a41140093.json) · [Complete rows](../reference_outputs/RAN1_P4_CQ2-4/5f6236e91e76317f5b97c778366fc70e453d1f88949bdf06aa61a99a41140093.jsonl)

Repair hash: `8990c081c3eb2d9aa9a47019cd0ceb5b0eb8abdd876c65dbb587294b20affeb0`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, count(DISTINCT sp) AS affectedSpecCount, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC, cr.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR) OPTIONAL MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber,count(DISTINCT sp.specNumber) AS affectedSpecCount,collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC,cr.tdocNumber ASC LIMIT 10
```


## RAN1_P4_CQ3-2

Original question (unchanged): Into which CR packs were the CRs of Work Item NR_newRAT-Core (initial NR spec) bundled for TSG submission?

Repair: `query_and_scorer`. Required answers: crPackId (string) ← pack.crPackId.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "all distinct originally requested role records; no unstated cap", "mode": "all"}`.

Captured native rows: 66. [Receipt](../reference_outputs/RAN1_P4_CQ3-2/09d0488d6b697007fa44fc69ffece02cba7a2a4c80a5c94eb2b556bcb4f448b4.json) · [Complete rows](../reference_outputs/RAN1_P4_CQ3-2/09d0488d6b697007fa44fc69ffece02cba7a2a4c80a5c94eb2b556bcb4f448b4.jsonl)

Repair hash: `5e3d45e76831b1496ca71dd0b81cc394bafa88d5f1f7a5b360d3f1515aafd32c`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(cr) AS crCount ORDER BY pack.tsgMeeting DESC, crCount DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(DISTINCT cr) AS crCount
```


## RAN1_P4_CQ3-3

Original question (unchanged): List the CR packs submitted to plenary RAN#109 and the CR count in each.

Repair: `scorer_only`. Required answers: pack.crPackId (string) ← pack.crPackId, crCount (integer) ← crCount.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 10. [Receipt](../reference_outputs/RAN1_P4_CQ3-3/bd27c8f28062576739a3c1c22403edd427e25e7219e5c01c3c8f200acdb9b7f3.json) · [Complete rows](../reference_outputs/RAN1_P4_CQ3-3/bd27c8f28062576739a3c1c22403edd427e25e7219e5c01c3c8f200acdb9b7f3.jsonl)

Repair hash: `9d52a868d323119db7610f5221b98d4583f8c7ac404120f279f7530a70e036e5`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(cr) AS crCount ORDER BY crCount DESC
```

Repaired reference query:
```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(cr) AS crCount ORDER BY crCount DESC
```


## RAN1_P5_CQ1-3

Original question (unchanged): List the TRs still in Draft and the technologies they study (anticipating future standard impact).

Repair: `scorer_only`. Required answers: tr.trNumber (string) ← tr.trNumber, tr.scope (string) ← tr.scope.

Collection: `{"kind": "set"}`. Cardinality: `{"mode": "all", "notes": "all matching requested records; no undeclared final row cap"}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P5_CQ1-3/50db9e5d1b55069c347bbf8e64a4ac70b03043ea889ab6b92b0fe22aede3626c.json) · [Complete rows](../reference_outputs/RAN1_P5_CQ1-3/50db9e5d1b55069c347bbf8e64a4ac70b03043ea889ab6b92b0fe22aede3626c.jsonl)

Repair hash: `9b17fe6cac1378ff5b86c29812893b6eb625ee0fd8b986b96ecf5dc790eafe38`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber
```


## RAN1_P5_CQ4-2

Original question (unchanged): Return the current status and scope of the 6G Radio study TR 38.760-1 (next-generation roadmap review).

Repair: `scorer_only`. Required answers: status (string) ← tr.trStatus, scope (string) ← tr.scope.

Collection: `{"kind": "set"}`. Cardinality: `{"extent": "one requested scalar or fixed-identifier record", "mode": "exact", "value": 1}`.

Captured native rows: 1. [Receipt](../reference_outputs/RAN1_P5_CQ4-2/b488af7b2261d235085b6f802521239659a20a11e494fc92f68ddf2f8bba6c8c.json) · [Complete rows](../reference_outputs/RAN1_P5_CQ4-2/b488af7b2261d235085b6f802521239659a20a11e494fc92f68ddf2f8bba6c8c.jsonl)

Repair hash: `bc111f247b08fbd821fd54bbb33d14cdcd85ea64cb59bfb16a5d765ccf333a7a`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope
```


## RAN1_P5_CQ5-3

Original question (unchanged): Which are the top 5 most-referenced TRs? (identifying foundational studies)

Repair: `query_and_scorer`. Required answers: trNumber (string) ← trNumber.

Collection: `{"kind": "native_ordered_ties", "source_order_keys": [{"direction": "desc", "source_column": "referenceCount"}], "tie_policy": "any_order_within_equal_keys"}`. Cardinality: `{"mode": "top_k", "notes": "top five TR-number groups, or all groups when fewer than five exist", "tie_policy": "TR number ascending", "value": 5}`.

Captured native rows: 5. [Receipt](../reference_outputs/RAN1_P5_CQ5-3/ed5798c88eb8b9e0f84dd396437c3e5b97130ba57b037ddc7fc6784156d63e9e.json) · [Complete rows](../reference_outputs/RAN1_P5_CQ5-3/ed5798c88eb8b9e0f84dd396437c3e5b97130ba57b037ddc7fc6784156d63e9e.jsonl)

Repair hash: `762230ca1be990ed773a14d5b46c0d788c84e3edd36cb323e9b90fc8ce7474f2`. Both per-unit judgments are embedded in [tasks](../tasks.jsonl).

Original query:
```cypher
MATCH (ref:TechnicalReport)<-[:REFERENCES_TR]-(src:TechnicalReport) WITH ref, count(src) AS refCount ORDER BY refCount DESC, ref.trNumber LIMIT 5 RETURN ref.trNumber, ref.trTitle, refCount
```

Repaired reference query:
```cypher
MATCH (ref:TechnicalReport) OPTIONAL MATCH (src:TechnicalReport)-[:REFERENCES_TR]->(ref) WITH ref.trNumber AS trNumber, count(DISTINCT src.trNumber) AS referenceCount RETURN trNumber, referenceCount ORDER BY referenceCount DESC, trNumber ASC LIMIT 5
```
