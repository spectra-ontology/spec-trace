# RAN4: admitted original-question repairs

Two AI reviews are recorded; no human/expert certification is claimed.


## RAN4_P1_CQ1-1

Original English (unchanged): List the TDocs presented at meeting RAN4#113 (meeting document overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `361f97f1c1d91d9a2118c6f0d30b49138dd34953dc06df101b7767ae664db1ea`. Native rows: 3089. [Complete output](../reference_outputs/RAN4_P1_CQ1-1/53316b267903df3aaab5a8e1f7839202fc442a64edd99949ee7b9c662456f42b.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ1-1/53316b267903df3aaab5a8e1f7839202fc442a64edd99949ee7b9c662456f42b.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#113'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#113'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN4_P1_CQ1-4

Original English (unchanged): List the top 5 meetings by number of TDocs (busiest meetings).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `03c698607f886b2afa968a3349ee003ba7a1cbbd8441a09d73f849b806c2889f`. Native rows: 58. [Complete output](../reference_outputs/RAN4_P1_CQ1-4/a6a5750105f96f06779388840e15266a9c4f860a1243d524ce56648b7b49ad5c.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ1-4/a6a5750105f96f06779388840e15266a9c4f860a1243d524ce56648b7b49ad5c.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC
```


## RAN4_P1_CQ1-5

Original English (unchanged): List Huawei's TDocs (per-company contribution overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `e39399fec49f22fd39e5979cb5ac440f1293fff7e54363054bf283b9d1a467a3`. Native rows: 27710. [Complete output](../reference_outputs/RAN4_P1_CQ1-5/d929836969ae6bc41a3ab329ba8154612111ff873aca8ffdc575ec7b336b6461.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ1-5/d929836969ae6bc41a3ab329ba8154612111ff873aca8ffdc575ec7b336b6461.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Huawei'}) RETURN t.tdocNumber ORDER BY t.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName:'Huawei'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN4_P1_CQ2-1

Original English (unchanged): How many TDocs target Rel-18? (release workload sizing).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `ec510f57d87fcbca8d65ffcd1d6675922c553caf151e62860c3aa52855f919a6`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ2-1/dbbbb359b223d25075b508b3ca917e325a226e2a01db69966b6491bf960775fe.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ2-1/dbbbb359b223d25075b508b3ca917e325a226e2a01db69966b6491bf960775fe.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN DISTINCT count(DISTINCT t) AS tdocCount
```


## RAN4_P1_CQ2-2

Original English (unchanged): List the CRs that modify spec 38.101-1 (spec change tracking).

Repair: `query_and_scorer`. Required fields: `[{"name":"crTdoc","nullable":false,"source_column_or_expression":"crTdoc","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `f68ecd6625a87b80f46cb881900468017c5939871cd864cc780c5e5fd7581b65`. Native rows: 7427. [Complete output](../reference_outputs/RAN4_P1_CQ2-2/a25427ccc803cf797126bd8cf445ed01d2e1de4a3da2b614a68af7149a7e58d9.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ2-2/a25427ccc803cf797126bd8cf445ed01d2e1de4a3da2b614a68af7149a7e58d9.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.101-1'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.101-1'}) RETURN DISTINCT cr.tdocNumber AS crTdoc
```


## RAN4_P1_CQ2-3

Original English (unchanged): Which Work Items have the most related TDocs? (activity by work item).

Repair: `query_and_scorer`. Required fields: `[{"name":"workItemCode","nullable":false,"source_column_or_expression":"workItemCode","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all WorkItem identities tied at the maximum distinct related Tdoc node count","mode":"all"}`.

Repair SHA: `471d4ba01461a39f04b997f5cda045a850d59b4c9376aa8d5b94f591bad5f901`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ2-3/410a435f96bab979d1127a859ea38b2f6d95b081544aa82c7c4b8db44e284613.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ2-3/410a435f96bab979d1127a859ea38b2f6d95b081544aa82c7c4b8db44e284613.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) WITH wi.workItemCode AS workItemCode,count(DISTINCT t) AS tdocCount WITH collect({workItemCode:workItemCode,tdocCount:tdocCount}) AS groups WITH groups,reduce(maxCount=0,g IN groups|CASE WHEN g.tdocCount>maxCount THEN g.tdocCount ELSE maxCount END) AS maxCount UNWIND groups AS g WITH g,maxCount WHERE g.tdocCount=maxCount RETURN g.workItemCode AS workItemCode,g.tdocCount AS tdocCount
```


## RAN4_P1_CQ3-1

Original English (unchanged): Show the distribution of TDocs across agenda items (agenda workload breakdown).

Repair: `query_and_scorer`. Required fields: `[{"name":"agendaId","nullable":false,"source_column_or_expression":"agendaId","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"Return every eligible agenda item including count0, without the unasked10 cap. Fresh complete output must verify unique nonnull identity and integer count for every item.","mode":"all"}`.

Repair SHA: `5d87712a471ca3115accd71b75273e8c22f1f21159027215aa5bc3a04e056480`. Native rows: 19763. [Complete output](../reference_outputs/RAN4_P1_CQ3-1/8998ff5cbe7a15c57e9fb65debdaa6067a784d1a4c5589fa3ffba2cb514c6de5.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ3-1/8998ff5cbe7a15c57e9fb65debdaa6067a784d1a4c5589fa3ffba2cb514c6de5.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem)
OPTIONAL MATCH (t:Tdoc)-[:BELONGS_TO]->(ai)
WITH ai, count(DISTINCT t) AS tdocCount
RETURN coalesce(ai.id, ai.iri) AS agendaId, tdocCount
```


## RAN4_P1_CQ3-2

Original English (unchanged): Show the distribution of TDocs by document type (document-type breakdown).

Repair: `query_and_scorer`. Required fields: `[{"name":"type","nullable":false,"source_column_or_expression":"type","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `d6f67547526e5a7907d66dfee82a0d5e5d3a1eeefae72af34a494a3b35f76940`. Native rows: 19. [Complete output](../reference_outputs/RAN4_P1_CQ3-2/7441cbb24b77f01a70fe3fb73c7ebae4058f252feff822d112691ab564b6aff8.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ3-2/7441cbb24b77f01a70fe3fb73c7ebae4058f252feff822d112691ab564b6aff8.json).

Original query:
```cypher
MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) RETURN DISTINCT t.type AS type, count(DISTINCT t) AS tdocCount
```


## RAN4_P1_CQ3-3

Original English (unchanged): List the top 10 companies by CR contributions (leading CR contributors).

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `d2b8eae78298ed9ba7bbf937e00895a7c163194ebf06fa22083c2438d6e68803`. Native rows: 287. [Complete output](../reference_outputs/RAN4_P1_CQ3-3/bd56fb877901a34e97342fca860222580eac226e4cd33d71b349e93e27acf021.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ3-3/bd56fb877901a34e97342fca860222580eac226e4cd33d71b349e93e27acf021.json).

Original query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company) OPTIONAL MATCH (cr:CR)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN4_P1_CQ4-2

Original English (unchanged): Return the direction and recipients of liaison statement R4-2417507 (LS routing analysis).

Repair: `query_and_scorer`. Required fields: `[{"name":"direction","nullable":false,"source_column_or_expression":"direction","type":"string"},{"name":"recipient","nullable":true,"source_column_or_expression":"recipient","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `b8a1cf869fa1c417ec7d262159092b87b1d4b43531344e2c4ef46cf190e687fe`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ4-2/a69c89c14a6ff1f191b92a9e1d8674c697912bbf76277cc1aac0763956071cca.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ4-2/a69c89c14a6ff1f191b92a9e1d8674c697912bbf76277cc1aac0763956071cca.json).

Original query:
```cypher
MATCH (ls:LS {tdocNumber:'R4-2417507'}) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo
```

Repaired reference query:
```cypher
MATCH (ls:LS {tdocNumber:'R4-2417507'}) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN DISTINCT ls.direction AS direction,wg.wgName AS recipient
```


## RAN4_P1_CQ5-1

Original English (unchanged): Return node counts by label across the graph (dataset statistics).

Repair: `scorer_only`. Required fields: `[{"name":"label","nullable":false,"source_column_or_expression":"label","type":"string"},{"name":"nodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `23aea6dd491dfaa2e8eaeac62a8ae6c008c9d83fc512ab80bdcd06bb189a8f3b`. Native rows: 27. [Complete output](../reference_outputs/RAN4_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.json).

Original query:
```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```

Repaired reference query:
```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```


## RAN4_P1_CQ5-3

Original English (unchanged): How many TDocs have a submitting company assigned? (attribution coverage check).

Repair: `query_and_scorer`. Required fields: `[{"name":"attributedTdocCount","nullable":false,"source_column_or_expression":"attributedTdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `30b3ea71d1ab437f3c1891d746d5f32be2736f65abd2ef9507ff54c5f9a129f7`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ5-3/b511957b7cfe5d3ade8004c9cd44b7ea200b3010d5239f2f6c639c6b85eb7782.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ5-3/b511957b7cfe5d3ade8004c9cd44b7ea200b3010d5239f2f6c639c6b85eb7782.json).

Original query:
```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(DISTINCT CASE WHEN c IS NOT NULL THEN t ELSE null END) AS attributedTdocCount
```


## RAN4_P1_CQ5-4

Original English (unchanged): Show the distribution of TDocs by release (per-release volume).

Repair: `query_and_scorer`. Required fields: `[{"name":"release","nullable":false,"source_column_or_expression":"release","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7495110ca50a0954c19e43e04c3ecdb1f348781ec7bba05013e3a5ed4e5fa42a`. Native rows: 14. [Complete output](../reference_outputs/RAN4_P1_CQ5-4/a4006b19781f2338d9801e3800c6b4a53507ff2ec7daeea0eb874be6f82ea8e6.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ5-4/a4006b19781f2338d9801e3800c6b4a53507ff2ec7daeea0eb874be6f82ea8e6.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN DISTINCT r.releaseName AS release, count(DISTINCT t) AS tdocCount
```


## RAN4_P1_CQ5-5

Original English (unchanged): List the top 10 specs by number of CRs (most-revised specs).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `853963584814b6e5e2f2ea733a483f064906b93a17b1d37f91fe8d53f6642d7b`. Native rows: 357. [Complete output](../reference_outputs/RAN4_P1_CQ5-5/c8fde0d3a5a6193396d1d4a06996576698e26817660071e2294c052f0b5ebe58.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ5-5/c8fde0d3a5a6193396d1d4a06996576698e26817660071e2294c052f0b5ebe58.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sp:Spec) OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp) RETURN sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN4_P1_CQ6-1

Original English (unchanged): How many TDocs were presented at meeting RAN4#117? (meeting size).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `a82e890c5dbcd7ba235c4d346df490ee89ad77426a0144ca9e62bb37766feb4a`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ6-1/cb4ffde58fbd096993e451757083bc89928992714f798c2e0773da003782dc7a.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ6-1/cb4ffde58fbd096993e451757083bc89928992714f798c2e0773da003782dc7a.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#117'}) RETURN count(t) AS cnt
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#117'}) RETURN DISTINCT count(DISTINCT t) AS tdocCount
```


## RAN4_P1_CQ6-2

Original English (unchanged): How many meetings are in the dataset? (meeting coverage count).

Repair: `scorer_only`. Required fields: `[{"name":"meetingNodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `b9a2dea871ef71fc1239d562dd6dac67e1e9e580aacd7c5e6421bbe9c082485f`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.json).

Original query:
```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```

Repaired reference query:
```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```


## RAN4_P1_CQ6-3

Original English (unchanged): How many of the TDocs are CRs? (change-request proportion).

Repair: `query_and_scorer`. Required fields: `[{"name":"crTdocCount","nullable":false,"source_column_or_expression":"crTdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `840dab34bcb247f9281f068f11154f823e0f94040f6c69c65581e692a1fde267`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ6-3/d4487c533b0981ec5fc48ca2d4d7343de5d7d5bb4dd668c4f7a34893ceddb829.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ6-3/d4487c533b0981ec5fc48ca2d4d7343de5d7d5bb4dd668c4f7a34893ceddb829.json).

Original query:
```cypher
MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) WHERE t:CR RETURN count(t) AS crTdocCount
```


## RAN4_P1_CQ6-4

Original English (unchanged): How many liaison statements are in the dataset? (LS count).

Repair: `scorer_only`. Required fields: `[{"name":"lsNodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `2a597ad101e1d2d6aa9e2e44d8b00327681715c431f6330a9db22b721b61ec6d`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.json).

Original query:
```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```

Repaired reference query:
```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```


## RAN4_P1_CQ6-5

Original English (unchanged): How many contacts are in the dataset? (contact count).

Repair: `scorer_only`. Required fields: `[{"name":"contactNodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `dd2c385eb60f4d309a9dbf8d00d69ecdddbf37d3f59589f7eafd1fe4691b1e11`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.json).

Original query:
```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```

Repaired reference query:
```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```


## RAN4_P1_CQ7-1

Original English (unchanged): How many agenda items are in the dataset? (agenda-item count).

Repair: `scorer_only`. Required fields: `[{"name":"agendaNodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `724c1ea676f1f3dce100dbe5c061d6a14cac2569406925c0bf62b6fcd6dcc701`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.json).

Original query:
```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```


## RAN4_P1_CQ7-2

Original English (unchanged): How many work items are in the dataset? (work-item count).

Repair: `scorer_only`. Required fields: `[{"name":"workItemNodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `34c737adbd7db815504096b2c62b3f8f3e28ec2da47456ae81ed7120e5b624c3`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.jsonl) / [receipt](../reference_outputs/RAN4_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.json).

Original query:
```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```

Repaired reference query:
```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```


## RAN4_P2_CQ1-1

Original English (unchanged): List the agreements reached at meeting RAN4#98 (meeting outcome review).

Repair: `query_and_scorer`. Required fields: `[{"name":"agreementId","nullable":false,"source_column_or_expression":"agreementId","type":"string"},{"name":"content","nullable":false,"source_column_or_expression":"content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `00ad6dd383b4f102913d5e86d53c60bea7fceed1fd822d654ba734da0323afce`. Native rows: 141. [Complete output](../reference_outputs/RAN4_P2_CQ1-1/8604d1914a3a85ea919bc3287e0bfa5c862783460eb17c5360bd1307ee1ea6e4.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-1/8604d1914a3a85ea919bc3287e0bfa5c862783460eb17c5360bd1307ee1ea6e4.json).

Original query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId AS agreementId, a.content AS content
```


## RAN4_P2_CQ1-2

Original English (unchanged): List the conclusions drawn at meeting RAN4#98 (meeting outcome review).

Repair: `query_and_scorer`. Required fields: `[{"name":"conclusionId","nullable":false,"source_column_or_expression":"conclusionId","type":"string"},{"name":"content","nullable":false,"source_column_or_expression":"content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `cdb61ff1a5b9cfa249cd6a751693be52646ca9533e9a42d8650f183720410959`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P2_CQ1-2/db604dd2b54dc5fea266e1e90cd29ad12532ddda8f7439ca8983f3bf73c30a29.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-2/db604dd2b54dc5fea266e1e90cd29ad12532ddda8f7439ca8983f3bf73c30a29.json).

Original query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN c.resolutionId, c.content, ai.agendaNumber, c.hasConsensus ORDER BY ai.agendaNumber, c.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN4#98'}) OPTIONAL MATCH (c)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content
```


## RAN4_P2_CQ1-3

Original English (unchanged): Which meetings recorded working assumptions? (locating open assumptions).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `42eec784fe51109a677095ee274959d063c98b5418d541b500d1e3b69d39e1a3`. Native rows: 3. [Complete output](../reference_outputs/RAN4_P2_CQ1-3/e489f59ecf8cd03b87dcd006ea3b27d001a3e67238bf0fd66a0c7df748beaf93.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-3/e489f59ecf8cd03b87dcd006ea3b27d001a3e67238bf0fd66a0c7df748beaf93.json).

Original query:
```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(w) AS cnt ORDER BY cnt DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT m.canonicalMeetingNumber AS meeting
```


## RAN4_P2_CQ1-4

Original English (unchanged): List the resolutions under agenda item 7 (agenda-scoped decisions).

Repair: `query_and_scorer`. Required fields: `[{"name":"resolutionId","nullable":false,"source_column_or_expression":"resolutionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct requested-field records in the original frozen working-group graph population; no unstated cap","mode":"all"}`.

Repair SHA: `d0db506e5560e6aa38b5a4c6028db0d2c0099c874067a8ae8eebf8ed8922ae01`. Native rows: 3. [Complete output](../reference_outputs/RAN4_P2_CQ1-4/3d77860a7ad199d94f1a03ab33f6b28eba08f948ce8118e891f48aff794e3170.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-4/3d77860a7ad199d94f1a03ab33f6b28eba08f948ce8118e891f48aff794e3170.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem {agendaNumber: '7'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(:AgendaItem {agendaNumber: '7'}) RETURN DISTINCT r.resolutionId AS resolutionId
```


## RAN4_P2_CQ1-5

Original English (unchanged): List the resolutions tied to Rel-15 TDocs (release-scoped decisions).

Repair: `query_and_scorer`. Required fields: `[{"name":"resolutionId","nullable":false,"source_column_or_expression":"resolutionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct requested-field records in the original frozen working-group graph population; no unstated cap","mode":"all"}`.

Repair SHA: `2ac972c5f133797f1560a482127e5085058d03a3fa501f4cb284cba48cc04d2a`. Native rows: 452. [Complete output](../reference_outputs/RAN4_P2_CQ1-5/a4c57ec90f094cff2aa96aae621b6a9e96a7f46f108990eadff1081e6b187ef9.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-5/a4c57ec90f094cff2aa96aae621b6a9e96a7f46f108990eadff1081e6b187ef9.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-15'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName: 'Rel-15'}) RETURN DISTINCT r.resolutionId AS resolutionId
```


## RAN4_P2_CQ1-8

Original English (unchanged): List the top 10 agenda items by number of resolutions (busiest agenda items).

Repair: `query_and_scorer`. Required fields: `[{"name":"agendaId","nullable":false,"source_column_or_expression":"agendaId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"resolutionCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `e0b967a92fe95113116b5427a05c38d9bea7a5b6c8449ffea0f26fb7f7a8411c`. Native rows: 19763. [Complete output](../reference_outputs/RAN4_P2_CQ1-8/d1ae35072746b5104d138b63783d43ad1a9d79125737c8a7dd6be96d85344bfb.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ1-8/d1ae35072746b5104d138b63783d43ad1a9d79125737c8a7dd6be96d85344bfb.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(r) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem)
OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai)
WITH ai, count(DISTINCT r) AS resolutionCount
RETURN coalesce(ai.id, ai.iri) AS agendaId, resolutionCount
ORDER BY resolutionCount DESC
```


## RAN4_P2_CQ2-1

Original English (unchanged): Which TDocs are referenced by 3 or more resolutions? (frequently cited documents).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `bf4699bb47934906adaec89366df3876429267e89290c835ad08b52e90274a34`. Native rows: 28. [Complete output](../reference_outputs/RAN4_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ2-1/d310b3b70f033ddfe8e73f01050e088239b2c7b0ba4b7ba18220a79280717919.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(r) AS refCnt WHERE refCnt >= 3 RETURN t.tdocNumber, refCnt ORDER BY refCnt DESC, t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t, count(DISTINCT r) AS refCnt WHERE refCnt >= 3 RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN4_P2_CQ2-2

Original English (unchanged): Which resolutions reference 5 or more TDocs? (broad-scope decisions).

Repair: `query_and_scorer`. Required fields: `[{"name":"resolutionId","nullable":false,"source_column_or_expression":"resolutionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `cab2b8a52b9c12192289467122106ed15c7ca4546cb11d575ff1120030608372`. Native rows: 465. [Complete output](../reference_outputs/RAN4_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ2-2/cf1418c45cb16dd10d2771a8cf51f3df2bb19ec8e1bcffe4c64cc2c74b8788e5.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r, collect(t.tdocNumber) AS refs, count(t) AS cnt WHERE cnt >= 5 MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, refs[..5] AS top5_refs, cnt ORDER BY m.meetingNumberInt DESC, cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r,count(DISTINCT t) AS referencedTdocCount WHERE referencedTdocCount>=5 RETURN DISTINCT r.resolutionId AS resolutionId
```


## RAN4_P2_CQ2-4

Original English (unchanged): List the top 10 specs by resolution-linked TDocs (spec decision activity).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `3d811d3aeed1def65790106e48434ba0f35f0cd5c983533cbf99cbfcabbb9838`. Native rows: 357. [Complete output](../reference_outputs/RAN4_P2_CQ2-4/05e9f6c0657b459c88ae51b7fba1995fef2bc19b6a84151fda3c814d769cc458.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ2-4/05e9f6c0657b459c88ae51b7fba1995fef2bc19b6a84151fda3c814d769cc458.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN s.specNumber, count(DISTINCT t) AS tdocCnt ORDER BY tdocCnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Spec)
WITH DISTINCT s.specNumber AS specNumber
OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(target:Spec)
WHERE target.specNumber = specNumber
RETURN specNumber, count(DISTINCT t) AS tdocCount
ORDER BY tdocCount DESC
```


## RAN4_P2_CQ3-2

Original English (unchanged): List the top 10 companies by resolution contributions (leading decision contributors).

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"resolutionCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `491e8dec54c37c30ff8c9cc0cae9163436607ad2b519ed421284c9749b0e0222`. Native rows: 287. [Complete output](../reference_outputs/RAN4_P2_CQ3-2/5066f0ea642a6fdd9f187a13c9e9c792c4c697da975527294a72a3aa750c4680.jsonl) / [receipt](../reference_outputs/RAN4_P2_CQ3-2/5066f0ea642a6fdd9f187a13c9e9c792c4c697da975527294a72a3aa750c4680.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(DISTINCT r) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC
```


## RAN4_P3_CQ1-1

Original English (unchanged): List the sections of spec 38.133 (spec structure browsing).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `2197b8689364092d52f562332d11c7f18cea825af9b368f7529ecedf451967e6`. Native rows: 32888. [Complete output](../reference_outputs/RAN4_P3_CQ1-1/5fa7c8ccb94f48177232d2f56b215740d881eca85f67e52edbca3936cee07f2e.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-1/5fa7c8ccb94f48177232d2f56b215740d881eca85f67e52edbca3936cee07f2e.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
```


## RAN4_P3_CQ1-10

Original English (unchanged): Find the spec and section that hold table 4.3-1 (reverse table lookup).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"},{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `406c54de237c90d936db7ccef12a04b8a9e8dc2e1bc260f3ee0d46d68f9ebece`. Native rows: 24. [Complete output](../reference_outputs/RAN4_P3_CQ1-10/cb8214998e0cd21985faaf8f0f1509429ab061f0f78d252f6d0394593f8b42e6.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-10/cb8214998e0cd21985faaf8f0f1509429ab061f0f78d252f6d0394593f8b42e6.json).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber: '4.3-1'}) RETURN sp.specNumber, sec.sectionId, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber: '4.3-1'}) RETURN DISTINCT sp.specNumber AS specNumber, sec.sectionId AS sectionId
```


## RAN4_P3_CQ1-11

Original English (unchanged): List the level-2 sections of spec 38.104 (base-station spec structure).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `91b5be56c06f089ab23269d7798eba32812b746b983fe5a893718f169c020cc1`. Native rows: 331. [Complete output](../reference_outputs/RAN4_P3_CQ1-11/da13ec14dcf7272fdf82e285265751a6a10078c778ccf188430e90227c66bae1.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-11/da13ec14dcf7272fdf82e285265751a6a10078c778ccf188430e90227c66bae1.json).

Original query:
```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.104'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.104'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
```


## RAN4_P3_CQ1-13

Original English (unchanged): List the void sections of spec 38.133 (identifying deprecated clauses).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `4f431f3ae53d44e427b5348631a4b3b3c8942b5e7ec61335437b1b5fa5dc967d`. Native rows: 754. [Complete output](../reference_outputs/RAN4_P3_CQ1-13/eb148e9218aedc8f2c342da34d4c712992be9ef212639d373aee7c2c16b71c33.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-13/eb148e9218aedc8f2c342da34d4c712992be9ef212639d373aee7c2c16b71c33.json).

Original query:
```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title
```


## RAN4_P3_CQ1-15

Original English (unchanged): List the level-3 sections of spec 38.133 (deep-structure browsing).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `4f77bfb1eb57b29f83da885b3bd238319fb09d2281952d71f9bfbb73b32b00de`. Native rows: 5447. [Complete output](../reference_outputs/RAN4_P3_CQ1-15/39f1fe757069acc1e57a79b4a02b641e1447761d832f92225064cebd659c5ce5.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-15/39f1fe757069acc1e57a79b4a02b641e1447761d832f92225064cebd659c5ce5.json).

Original query:
```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionTitle AS title
```


## RAN4_P3_CQ1-4

Original English (unchanged): List the level-1 sections of spec 38.133 (top-level structure).

Repair: `scorer_only`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `4d0062f88a716f3f7cf9aceb2aec87a1ad97ced4e193d0b1c8d82ad5ee48cd3b`. Native rows: 190. [Complete output](../reference_outputs/RAN4_P3_CQ1-4/db5638c6048b68e74ce563ab2fd898b3ab5bdb811604a6bd6588880184ca1929.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-4/db5638c6048b68e74ce563ab2fd898b3ab5bdb811604a6bd6588880184ca1929.json).

Original query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```


## RAN4_P3_CQ1-8

Original English (unchanged): List all tables in spec 38.101-1 (table inventory).

Repair: `query_and_scorer`. Required fields: `[{"name":"tableId","nullable":false,"source_column_or_expression":"tableId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `0217fcbf000a20956b96f1cb38e120a0f36b3d7e8d8b84f90e0020e715d0658b`. Native rows: 3001. [Complete output](../reference_outputs/RAN4_P3_CQ1-8/460490eac1b6dd6bfd05caf66bb84d618a68922dcf6475a6dfa9b5972ddd8d55.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-8/460490eac1b6dd6bfd05caf66bb84d618a68922dcf6475a6dfa9b5972ddd8d55.json).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId, t.tableNumber AS tableNumber, t.tableCaption AS caption
```


## RAN4_P3_CQ1-9

Original English (unchanged): List the sections of spec 38.133 whose title contains 'measurement' (finding measurement clauses).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `f54e382512a6b7cd3e0ef93006d9ba02f4207012518bcc932627bdd966be3763`. Native rows: 5972. [Complete output](../reference_outputs/RAN4_P3_CQ1-9/8be590a675244177678d50f12420c94952351f1755b8542914fd3e44ab185f4b.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ1-9/8be590a675244177678d50f12420c94952351f1755b8542914fd3e44ab185f4b.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN DISTINCT s.sectionId AS sectionId
```


## RAN4_P3_CQ2-3

Original English (unchanged): List the top 10 most-referenced sections (key referenced clauses).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `ce0a6ed77f963811f53f813f81e7a0c2464e264851def3e574d94d3f9ec3b215`. Native rows: 76704. [Complete output](../reference_outputs/RAN4_P3_CQ2-3/e0dae2ee4d588dee037c9e2e0cea6bc6fd8b215ade151d9ba05cd6cc7690ee20.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-3/e0dae2ee4d588dee037c9e2e0cea6bc6fd8b215ade151d9ba05cd6cc7690ee20.json).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC, b.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (b:Section)
OPTIONAL MATCH (:Section)-[ref:REFERENCES_SECTION]->(b)
WITH b, count(DISTINCT ref) AS referenceCount
RETURN coalesce(b.sectionId,b.iri) AS sectionId, referenceCount
ORDER BY referenceCount DESC
```


## RAN4_P3_CQ2-4

Original English (unchanged): List the top 10 sections that reference the most others (heaviest referencing clauses).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referencedSectionCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `d7be8771984e61e20dcc476c57c6977a0e81e6897821db37c97c609960a0bf09`. Native rows: 76704. [Complete output](../reference_outputs/RAN4_P3_CQ2-4/f44fdc8a1164b18780030b3de325d7c85d970922f50f80b9f0f04506e69ebc1c.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-4/f44fdc8a1164b18780030b3de325d7c85d970922f50f80b9f0f04506e69ebc1c.json).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section) OPTIONAL MATCH (a)-[:REFERENCES_SECTION]->(b:Section) WHERE b <> a RETURN a.sectionId AS sectionId, count(DISTINCT b) AS referencedSectionCount ORDER BY referencedSectionCount DESC
```


## RAN4_P3_CQ2-5

Original English (unchanged): List the top 10 cross-spec section-reference pairs (inter-spec dependency map).

Repair: `query_and_scorer`. Required fields: `[{"name":"fromSpec","nullable":false,"source_column_or_expression":"fromSpec","type":"string"},{"name":"toSpec","nullable":false,"source_column_or_expression":"toSpec","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `3c0c13c3b7f95b268c0cc82e5180f825a2763c1a1d6cfdfed5630f2b22bcf210`. Native rows: 4. [Complete output](../reference_outputs/RAN4_P3_CQ2-5/03ff5d82a6351aebdb5c26cc27bf06ec4a0601ee68cd7d671e62f22e4018adb8.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-5/03ff5d82a6351aebdb5c26cc27bf06ec4a0601ee68cd7d671e62f22e4018adb8.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section)-[ref:REFERENCES_SECTION]->(b:Section),
(a)-[:BELONGS_TO_SPEC]->(sa:Spec), (b)-[:BELONGS_TO_SPEC]->(sb:Spec)
WHERE sa.specNumber <> sb.specNumber
RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```


## RAN4_P3_CQ2-6

Original English (unchanged): List the top 5 specs referenced by spec 38.101-1 (its main dependencies).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceEdgeCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `a464f8660d3fbd29d3ebedccfc81af211ca8735e15f82c444fd79697e506f906`. Native rows: 4. [Complete output](../reference_outputs/RAN4_P3_CQ2-6/6b5c48aa0a8d5344014aedc98236ba921c960cfec261d3841c4f66b231b31a5e.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-6/6b5c48aa0a8d5344014aedc98236ba921c960cfec261d3841c4f66b231b31a5e.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.101-1'}), (a)-[reference:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber AS specNumber, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC
```


## RAN4_P3_CQ2-7

Original English (unchanged): List the top 10 spec-to-spec reference pairs (inter-spec dependency map).

Repair: `query_and_scorer`. Required fields: `[{"name":"fromSpec","nullable":false,"source_column_or_expression":"fromSpec","type":"string"},{"name":"toSpec","nullable":false,"source_column_or_expression":"toSpec","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceEdgeCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `4d57e34763df21f9ae67aba399fd5f126e365adb5bc839189aa12810809aa37f`. Native rows: 121. [Complete output](../reference_outputs/RAN4_P3_CQ2-7/83e619191fc23ef98717afaeb57060403338c0685073cf06ee58f4cee9868913.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-7/83e619191fc23ef98717afaeb57060403338c0685073cf06ee58f4cee9868913.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[reference:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT reference) AS referenceEdgeCount ORDER BY referenceEdgeCount DESC
```


## RAN4_P3_CQ2-8

Original English (unchanged): How many internal cross-references does spec 38.133 have? (self-reference density).

Repair: `query_and_scorer`. Required fields: `[{"name":"referenceEdgeCount","nullable":false,"source_column_or_expression":"referenceEdgeCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `ead073dc50271b9f5f8230936267d44a72d5cb371cbe7c989cd3e58653659c38`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_CQ2-8/65a1357419982e1a3365158e6f9d58e4a7c63b16f23d7a95123b9fa7c6243057.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ2-8/65a1357419982e1a3365158e6f9d58e4a7c63b16f23d7a95123b9fa7c6243057.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}), (a)-[reference:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN DISTINCT count(DISTINCT reference) AS referenceEdgeCount
```


## RAN4_P3_CQ3-1

Original English (unchanged): Which specs does CR RP-240001 modify? (change-request impact lookup).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `f00aafcda69f8e5b9a10e4e481982caa4863f210c5db9fb3c7eb73ad42526600`. Native rows: 0. [Complete output](../reference_outputs/RAN4_P3_CQ3-1/cac60839e586087fc6946ad604266d3665d1c3e9dc6594156e3af8475335f59a.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ3-1/cac60839e586087fc6946ad604266d3665d1c3e9dc6594156e3af8475335f59a.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WITH cr, sp ORDER BY cr.tdocNumber, sp.specNumber LIMIT 1 MATCH (cr2:CR {tdocNumber: cr.tdocNumber})-[:MODIFIES]->(sp2:Spec) RETURN cr2.tdocNumber, sp2.specNumber ORDER BY cr2.tdocNumber, sp2.specNumber LIMIT 5
```

Repaired reference query:
```cypher
MATCH (:CR {tdocNumber:'RP-240001'})-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```


## RAN4_P3_CQ3-5

Original English (unchanged): List the specs modified by CRs under Work Item NR_newRAT-Perf (work-item change footprint).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `37916472b77a5fa009c57e039c2d7eb01222709d73ae422f78a2f38f38655819`. Native rows: 31. [Complete output](../reference_outputs/RAN4_P3_CQ3-5/61271e0ef19525415f50675e8b317d0201998e3ca14ffe20876fb2b15f641dbe.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ3-5/61271e0ef19525415f50675e8b317d0201998e3ca14ffe20876fb2b15f641dbe.json).

Original query:
```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber AS specNumber
```


## RAN4_P3_CQ3-6

Original English (unchanged): How many CRs did Huawei submit against spec 38.133? (per-company change count).

Repair: `query_and_scorer`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `e8718efe1284d1aa8426765d3f422148fcbdcd3daff932e99d4430f2bd68035e`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_CQ3-6/71ef717945c874dad96096cc0705c81b6b0ece3bd9f4ebc616a5e76e1a4fab8e.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ3-6/71ef717945c874dad96096cc0705c81b6b0ece3bd9f4ebc616a5e76e1a4fab8e.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN count(cr) AS crCount
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
```


## RAN4_P3_CQ3-7

Original English (unchanged): List the top 10 companies that modify spec 38.133 the most (leading change contributors).

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `b325a9085d4f4a459be6030f6dece109e15b12733c24205c966320383c255348`. Native rows: 81. [Complete output](../reference_outputs/RAN4_P3_CQ3-7/fdc52a271b5f03d1f3c6f1f90af47ae1c741793ed91b183c710447a391c7785c.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ3-7/fdc52a271b5f03d1f3c6f1f90af47ae1c741793ed91b183c710447a391c7785c.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName AS companyName, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN4_P3_CQ3-8

Original English (unchanged): How many Rel-18 CRs modify spec 38.133? (release-scoped change count).

Repair: `query_and_scorer`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `3ccc3bc931e15d179fb3592c87db1bdec4d6ad54f12fbc2fd38d4b12e0200b80`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_CQ3-8/5f8138755f013cb46e5276b70cfb95644673736b95f875b4384a4eddfb52708e.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ3-8/5f8138755f013cb46e5276b70cfb95644673736b95f875b4384a4eddfb52708e.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) RETURN count(cr) AS crCount
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
```


## RAN4_P3_CQ4-3

Original English (unchanged): How many CRs presented at RAN4#111 modify spec 38.133? (meeting-scoped change count).

Repair: `query_and_scorer`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `1cf1e73db692bbcae1e96cb35eaee8a926688be95e15dfbd500cc469bedd1b3f`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_CQ4-3/0a33390143b83c562b62279695586d43191ce6368b15ae37cb9ef8e6ed9aaf7e.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ4-3/0a33390143b83c562b62279695586d43191ce6368b15ae37cb9ef8e6ed9aaf7e.json).

Original query:
```cypher
MATCH (m:Meeting {meetingNumber: 'RAN4#111'})<-[:PRESENTED_AT]-(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS crCount
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN4#111'})<-[:PRESENTED_AT]-(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
```


## RAN4_P3_CQ5-1

Original English (unchanged): What is the total number of CRs modifying spec 38.133? (overall change volume).

Repair: `query_and_scorer`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `f188ad7255e452317eefce42b91c0a03775d4f768b06fb466d53f7c48904c860`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_CQ5-1/a45b9a522fc44f431d07b76a369e1f12688648110f27db452a648a1a02e00671.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ5-1/a45b9a522fc44f431d07b76a369e1f12688648110f27db452a648a1a02e00671.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS totalCRs
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN DISTINCT count(DISTINCT cr) AS crCount
```


## RAN4_P3_CQ5-2

Original English (unchanged): List Huawei's top 5 specs by CR contributions (a company's change focus).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `c7639838fa073ed157b2932d7c54ec4e2755ad94b34003f0e48ae07517db1c71`. Native rows: 357. [Complete output](../reference_outputs/RAN4_P3_CQ5-2/27b121e7774568d0312ec06031b77139bc451b1ef4b513b2ad56edf4e0292a33.jsonl) / [receipt](../reference_outputs/RAN4_P3_CQ5-2/27b121e7774568d0312ec06031b77139bc451b1ef4b513b2ad56edf4e0292a33.json).

Original query:
```cypher
MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) OPTIONAL MATCH (:Company {companyName:'Huawei'})<-[:SUBMITTED_BY]-(cr:CR)-[:MODIFIES]->(sp) RETURN sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN4_P3_P3-S8-CQ02

Original English (unchanged): Are all item-level entity nodes linked to a Section via definedInSection? (grounding-coverage check).

Repair: `query_and_scorer`. Required fields: `[{"name":"allLinked","nullable":false,"source_column_or_expression":"allLinked","type":"boolean"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `cc0673f6eddcaca44a95522ddea412e676808eb75a2f2508603095ea4b73a5cd`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.jsonl) / [receipt](../reference_outputs/RAN4_P3_P3-S8-CQ02/79c583374b69eaa8ad4da0a0f4c55b131daca0d02431eaf02ffdaf26f347d322.json).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,EXISTS { MATCH (n)-[:definedInSection]->(:Section) } AS linked RETURN count(DISTINCT n) AS itemCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END) AS unlinkedCount,count(DISTINCT CASE WHEN NOT linked THEN n ELSE null END)=0 AS allLinked
```


## RAN4_P4_CQ2-2

Original English (unchanged): Which CRs modifying spec 38.133 also affect other specs? (ripple-effect screening).

Repair: `query_and_scorer`. Required fields: `[{"name":"crTdoc","nullable":false,"source_column_or_expression":"crTdoc","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `6c6b00dd6bfb45a940bf01ee0b163b78b473d815f1a2838964fcabb35006c4f4`. Native rows: 1379. [Complete output](../reference_outputs/RAN4_P4_CQ2-2/c29b785b4a86b768c8785d6ff44fa5c4c3a18aae71327b05c90e38a66eb994b4.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ2-2/c29b785b4a86b768c8785d6ff44fa5c4c3a18aae71327b05c90e38a66eb994b4.json).

Original query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.133'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.133' } RETURN DISTINCT c.tdocNumber AS crTdoc
```


## RAN4_P4_CQ2-3

Original English (unchanged): List the CRs that flag spec 38.533 as affected (inbound cross-spec impact).

Repair: `query_and_scorer`. Required fields: `[{"name":"crTdoc","nullable":false,"source_column_or_expression":"crTdoc","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c8421c8fc10f5c008f05ea374647f9e6ced17c9fdd1a885f069da13027b9f5f1`. Native rows: 1515. [Complete output](../reference_outputs/RAN4_P4_CQ2-3/cb42beb3bf4ac0bba10cc591a6a61bbb50934596a0fd17207984c2027d89b03f.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ2-3/cb42beb3bf4ac0bba10cc591a6a61bbb50934596a0fd17207984c2027d89b03f.json).

Original query:
```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc
```


## RAN4_P4_CQ3-1

Original English (unchanged): List the CRs in CR pack RP-233366 with their change summaries (CR-pack contents review).

Repair: `query_and_scorer`. Required fields: `[{"name":"crTdoc","nullable":false,"source_column_or_expression":"crTdoc","type":"string"},{"name":"summary","nullable":true,"source_column_or_expression":"summary","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `22ac3142678e04635cf7bc5913830d38fd450603ac0353c9e46b4e83caf680af`. Native rows: 60. [Complete output](../reference_outputs/RAN4_P4_CQ3-1/5093835e886b550086016b706ce91cd73b33cc34fe156a0a2efb2b04cfed324c.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ3-1/5093835e886b550086016b706ce91cd73b33cc34fe156a0a2efb2b04cfed324c.json).

Original query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-233366'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-233366'})-[:HAS_CR]->(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.summaryOfChange AS summary
```


## RAN4_P4_CQ3-2

Original English (unchanged): Which CR packs contain CRs for NR_newRAT work items? (work-item packaging trace).

Repair: `query_and_scorer`. Required fields: `[{"name":"crPackId","nullable":false,"source_column_or_expression":"crPackId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `5459bcdabbee9533de9a4e76a576b2883b1ef026eb5b0f835420c83a656fa4d7`. Native rows: 158. [Complete output](../reference_outputs/RAN4_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ3-2/35d5af1152fa4c704764c8012337af79f071fa33e6092bc0d5c783244bae2f87.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId
```


## RAN4_P4_CQ3-3

Original English (unchanged): List the CR packs submitted to TSG meeting RAN#102 (plenary submission overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"crPackId","nullable":false,"source_column_or_expression":"crPackId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `d4d16f3c32916c47c48d3591c3dec53be5c27b9ceb725dc646947fccc3eef9b7`. Native rows: 35. [Complete output](../reference_outputs/RAN4_P4_CQ3-3/779caef300dbef3010b49d498edd7a6d7e61c5884064cc711643b50fa1863c33.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ3-3/779caef300dbef3010b49d498edd7a6d7e61c5884064cc711643b50fa1863c33.json).

Original query:
```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#102'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack {tsgMeeting: 'RAN#102'}) RETURN DISTINCT pack.crPackId AS crPackId
```


## RAN4_P4_CQ4-1

Original English (unchanged): List the reasons-for-change of CRs that modify section 7.3A.5 of spec 38.101-1 (clause-level change rationale).

Repair: `query_and_scorer`. Required fields: `[{"name":"reason","nullable":true,"source_column_or_expression":"reason","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `cb135fd78595261362e5726aa265bb98981c8dae4eef7ed3eec276372ca6134e`. Native rows: 123. [Complete output](../reference_outputs/RAN4_P4_CQ4-1/6db393492092580c33338361e82dfd8be703d7d10eb22109cc15a3a9a7c5283a.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ4-1/6db393492092580c33338361e82dfd8be703d7d10eb22109cc15a3a9a7c5283a.json).

Original query:
```cypher
MATCH (sec:Section {sectionNumber: '7.3A.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section {sectionNumber: '7.3A.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS crTdoc, c.reasonForChange AS reason
```


## RAN4_P4_CQ4-3

Original English (unchanged): List the sections modified by CRs under NR_newRAT work items (work-item change footprint).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `652f9b6ec7b792d0f060106213b8ce2db6360b1eba2c0f116ba81fa726293279`. Native rows: 4274. [Complete output](../reference_outputs/RAN4_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl) / [receipt](../reference_outputs/RAN4_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
```


## RAN4_P5_CQ1-1

Original English (unchanged): List the completed TRs targeting Rel-17 (release study inventory).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `ce7a7e79184c01d6a7ae0856ba97987bce711c531d7e857a13093441ba66deeb`. Native rows: 15. [Complete output](../reference_outputs/RAN4_P5_CQ1-1/726dd958b5412236d544f3b3f48acebf92b5b3fe61fb91424936c88d97a84d4d.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ1-1/726dd958b5412236d544f3b3f48acebf92b5b3fe61fb91424936c88d97a84d4d.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN4_P5_CQ1-4

Original English (unchanged): List the TRs currently in draft status (ongoing studies).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `8922b16d529ebc8999a060aa851786419b394516132f67d57bb4d106b2761948`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P5_CQ1-4/81935334de25655f8962a6507d78c651ead2f2c836ae3e6b5071515b03c203e2.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ1-4/81935334de25655f8962a6507d78c651ead2f2c836ae3e6b5071515b03c203e2.json).

Original query:
```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Draft' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Draft' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN4_P5_CQ2-1

Original English (unchanged): List the specs impacted by TR 38.803 (study-to-spec impact).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `57bd0f8d15e6ca2e24002f4bd68d77d988b4aae1e28997cc7fa6bc508367dd2a`. Native rows: 4. [Complete output](../reference_outputs/RAN4_P5_CQ2-1/1c308838287206c61d636421d4c35e05991a970b423e1973853824cfa6b30e80.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ2-1/1c308838287206c61d636421d4c35e05991a970b423e1973853824cfa6b30e80.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```


## RAN4_P5_CQ2-2

Original English (unchanged): Return the impact types of TR 38.860 (impact classification).

Repair: `scorer_only`. Required fields: `[{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `fe8db4e3918c072774d4331a50dc247f21ed7286a92998858af52843547d79b9`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P5_CQ2-2/5038a1f9a96564fa996e87e851fae41694eb007897ab40b909d16af76929751d.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ2-2/5038a1f9a96564fa996e87e851fae41694eb007897ab40b909d16af76929751d.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.860'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```


## RAN4_P5_CQ2-5

Original English (unchanged): List the TRs that impacted spec 38.101-1 (reverse study lookup).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `5e565dee0e10370aedad1699029c50b110ccf340c823a1535ae19504b0e81fa3`. Native rows: 47. [Complete output](../reference_outputs/RAN4_P5_CQ2-5/32ed7102faf804692a6f6eb327e76111b685876f61b1230e1fbb893d99da4cb4.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ2-5/32ed7102faf804692a6f6eb327e76111b685876f61b1230e1fbb893d99da4cb4.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.101-1'}) RETURN DISTINCT tr.trNumber, tr.trTitle, imp.impactType ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.101-1'}) RETURN DISTINCT tr.trNumber, tr.trTitle, imp.impactType ORDER BY tr.trNumber
```


## RAN4_P5_CQ3-1

Original English (unchanged): Which specs did the NR RF study TR 38.803 impact? (study-to-spec impact).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `dc186fae9ede4df8431cf468c2fc2136a4df715dc23b9f44ca1e9249462792b7`. Native rows: 4. [Complete output](../reference_outputs/RAN4_P5_CQ3-1/c6dd640802c54b470cba1c7961be69959331aa16f058dbe21a5ed43b56606419.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ3-1/c6dd640802c54b470cba1c7961be69959331aa16f058dbe21a5ed43b56606419.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```


## RAN4_P5_CQ3-2

Original English (unchanged): What spec impact did the FR2 extension study TR 38.820 have? (study-to-spec impact).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":true,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c732993ff6977ead42b88741989adadcce16d513d6a91c09b2edfc1c9962a5ed`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P5_CQ3-2/11fc119444c7380f0dfa24bef8b9c86e4235695b362b8beb529aa77840d3ddce.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ3-2/11fc119444c7380f0dfa24bef8b9c86e4235695b362b8beb529aa77840d3ddce.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.820'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.trStatus, s.specNumber, imp.impactType
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.820'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.trStatus, s.specNumber, imp.impactType
```


## RAN4_P5_CQ3-3

Original English (unchanged): What spec impact, with details, did the NTN RF study TR 38.863 have? (study-to-spec impact detail).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"description","nullable":false,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `2487083ff9b2b02c8429ab8229f8f64195adb2010f78aba38714c49e97a7a4b1`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P5_CQ3-3/6cca26a902b95e9666e674d08ab4ada293488e11d12730e4ef93287412be1afd.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ3-3/6cca26a902b95e9666e674d08ab4ada293488e11d12730e4ef93287412be1afd.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.863'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.863'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```


## RAN4_P5_CQ4-1

Original English (unchanged): List the Rel-17 study TRs and their impact types (release study overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"trNumber","type":"string"},{"name":"impactType","nullable":true,"source_column_or_expression":"impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7550e0f4e8ff07adf12f0f097e1782bfa14b9b08aa97b0d7817add9667c7a9a1`. Native rows: 22. [Complete output](../reference_outputs/RAN4_P5_CQ4-1/298cbb57b430ecc804c103c27084a0e53e7ecd733837d3444b62c7bf49626978.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ4-1/298cbb57b430ecc804c103c27084a0e53e7ecd733837d3444b62c7bf49626978.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, tr.trTitle, collect(DISTINCT imp.impactType) AS impactTypes ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN DISTINCT tr.trNumber AS trNumber,imp.impactType AS impactType
```


## RAN4_P5_CQ4-2

Original English (unchanged): Return the status and scope of the IAB RF study TR 38.809 (study progress check).

Repair: `scorer_only`. Required fields: `[{"name":"status","nullable":false,"source_column_or_expression":"tr.trStatus","type":"string"},{"name":"scope","nullable":false,"source_column_or_expression":"tr.scope","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `976b1756347d21c2239eb0e872e37ab63daeb4d7d1850e62ccce42acc5e3ea92`. Native rows: 1. [Complete output](../reference_outputs/RAN4_P5_CQ4-2/a366a4f74484e034c0e9194340f7514e3372642a0eeea0b7d4830c8c7390ebb8.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ4-2/a366a4f74484e034c0e9194340f7514e3372642a0eeea0b7d4830c8c7390ebb8.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.809'}) RETURN tr.trNumber, tr.trStatus, tr.scope
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.809'}) RETURN tr.trNumber, tr.trStatus, tr.scope
```


## RAN4_P5_CQ5-2

Original English (unchanged): List the TRs that reference TR 38.803 (inbound TR citations).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"ref.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `0efb5d7df1315ac45518d58f9eb719f6bcf35d9cf98337091835577803dfbf83`. Native rows: 6. [Complete output](../reference_outputs/RAN4_P5_CQ5-2/56c2392eb954772f9b9a3653f31d319ee0c2bb5c10e227eb02c35f9f00cab579.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ5-2/56c2392eb954772f9b9a3653f31d319ee0c2bb5c10e227eb02c35f9f00cab579.json).

Original query:
```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport {trNumber: '38.803'}) RETURN ref.trNumber, ref.trTitle ORDER BY ref.trNumber
```

Repaired reference query:
```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport {trNumber: '38.803'}) RETURN ref.trNumber, ref.trTitle ORDER BY ref.trNumber
```


## RAN4_P5_CQ5-3

Original English (unchanged): List the top 5 most-referenced TRs (most-cited studies).

Repair: `query_and_scorer`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"trNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `c0382e8591721a4d4c91973210a50e6c896bbbf13bbe6703611d258c8eb9399c`. Native rows: 100. [Complete output](../reference_outputs/RAN4_P5_CQ5-3/ee58ec01227927deb8554acc08040605476f1cd2c75c7f0fa1786ab82f0b1b45.jsonl) / [receipt](../reference_outputs/RAN4_P5_CQ5-3/ee58ec01227927deb8554acc08040605476f1cd2c75c7f0fa1786ab82f0b1b45.json).

Original query:
```cypher
MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport) WITH tr, count(ref) AS refCount RETURN tr.trNumber, tr.trTitle, refCount ORDER BY refCount DESC, tr.trNumber LIMIT 5
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)
WITH DISTINCT tr.trNumber AS trNumber
OPTIONAL MATCH (:TechnicalReport)-[ref:REFERENCES_TR]->(target:TechnicalReport)
WHERE target.trNumber = trNumber
RETURN trNumber, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```
