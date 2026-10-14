# RAN5: admitted original-question repairs

Two AI reviews are recorded; no human/expert certification is claimed.


## RAN5_P1_CQ1-1

Original English (unchanged): List the TDocs presented at meeting RAN5#109 (meeting document survey).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c7689a95ebcc6e7976a3ae4da14f16792be888df957ef90623b90e57200ac3b7`. Native rows: 1427. [Complete output](../reference_outputs/RAN5_P1_CQ1-1/acb6f72fc87bb0ea46c3dba056b6b6b17a3e68e019a7bf78a4391cd87e6a66a2.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ1-1/acb6f72fc87bb0ea46c3dba056b6b6b17a3e68e019a7bf78a4391cd87e6a66a2.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN DISTINCT t.tdocNumber AS tdocNumber
```


## RAN5_P1_CQ1-4

Original English (unchanged): Which five meetings hosted the most TDocs? (activity ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"boundary_rule":"The complete captured 35-meeting/count population has a strict fifth/sixth gap.","mode":"top_k","tie_policy":"strict_observed_boundary","value":5}`.

Repair SHA: `ca25206070c900634cf67d04b3f1a11542306d8b4c7f391d89a5ea3976bf2db3`. Native rows: 5. [Complete output](../reference_outputs/RAN5_P1_CQ1-4/9350c5a6b407f3a30bb9ddd51d705678508c96452a484c49d584b5561e84b102.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ1-4/9350c5a6b407f3a30bb9ddd51d705678508c96452a484c49d584b5561e84b102.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC, meeting ASC LIMIT 5
```


## RAN5_P1_CQ2-1

Original English (unchanged): How many TDocs target Rel-18? (release volume check)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `8799eae1a2f8b0c264a021b0d0adab9605d00799915c212175c38551f4025ee4`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ2-1/a7a5008320f200c21568abd5611e98fe2c9adbab7ec315fe45057535d439dd1f.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ2-1/a7a5008320f200c21568abd5611e98fe2c9adbab7ec315fe45057535d439dd1f.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName:'Rel-18'}) RETURN count(t) AS cnt
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}) RETURN count(DISTINCT t) AS tdocCount
```


## RAN5_P1_CQ2-2

Original English (unchanged): List the CRs that modify TS 38.533 (spec-change tracking).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `26dd7fda8e0f4a4bcd7725982d9244c5a9c3575a59171527407d57f42ba25844`. Native rows: 6123. [Complete output](../reference_outputs/RAN5_P1_CQ2-2/4d663ad5794d6d2fc5b9ed078dfafe5bb05d2e67bc403d9918c423738c0b01bf.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ2-2/4d663ad5794d6d2fc5b9ed078dfafe5bb05d2e67bc403d9918c423738c0b01bf.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber:'38.533'}) RETURN cr.tdocNumber ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
```


## RAN5_P1_CQ2-3

Original English (unchanged): Which five Work Items have the most TDocs? (work-item activity)

Repair: `query_and_scorer`. Required fields: `[{"name":"workItemCode","nullable":false,"source_column_or_expression":"workItemCode","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `3b94698137bb3f751bb8d5d9822c3c59c2f6e714be8a2cae61884cc735d086ff`. Native rows: 398. [Complete output](../reference_outputs/RAN5_P1_CQ2-3/a7eb292b582c9714a4e192e9d59d78f2daf8fb1e038424338445411886652c88.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ2-3/a7eb292b582c9714a4e192e9d59d78f2daf8fb1e038424338445411886652c88.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (wi:WorkItem)
OPTIONAL MATCH (t:Tdoc)-[:RELATED_TO]->(wi)
RETURN wi.workItemCode AS workItemCode, count(DISTINCT t) AS tdocCount
ORDER BY tdocCount DESC
```


## RAN5_P1_CQ3-1

Original English (unchanged): Which ten agenda items drew the most TDocs? (agenda workload)

Repair: `query_and_scorer`. Required fields: `[{"name":"agendaItemId","nullable":false,"source_column_or_expression":"agendaItemId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `bfefa20e4e1fd96e7be5f46b0000b00e31c29c358a5628479ea5f6b592a88350`. Native rows: 8632. [Complete output](../reference_outputs/RAN5_P1_CQ3-1/84fef65a1f272c1edbefbb3b3e01f9102f04189c8e7cccd117adfb0aca9913e2.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ3-1/84fef65a1f272c1edbefbb3b3e01f9102f04189c8e7cccd117adfb0aca9913e2.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem) RETURN ai.agendaNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem)
OPTIONAL MATCH (t:Tdoc)-[:BELONGS_TO]->(ai)
WITH ai, count(DISTINCT t) AS tdocCount
RETURN coalesce(ai.id, ai.iri) AS agendaItemId, tdocCount
ORDER BY tdocCount DESC
```


## RAN5_P1_CQ3-2

Original English (unchanged): Break down TDocs by type (document-type distribution).

Repair: `query_and_scorer`. Required fields: `[{"name":"documentType","nullable":true,"source_column_or_expression":"documentType","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `57944ee54503a38d6b2362d16df6f9931bc6050372d895b3875519587bcdbf2e`. Native rows: 20. [Complete output](../reference_outputs/RAN5_P1_CQ3-2/4da041f8b4741365c0c39b9d43507de25582c805440cf6b06f7b43986839adef.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ3-2/4da041f8b4741365c0c39b9d43507de25582c805440cf6b06f7b43986839adef.json).

Original query:
```cypher
MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) RETURN t.type AS documentType, count(t) AS tdocCount
```


## RAN5_P1_CQ3-3

Original English (unchanged): Which ten companies submitted the most CRs? (contribution ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `0036944c33a41c7dbbf55421685bb6d86cc31710130a1b6e939c32c1c0632549`. Native rows: 172. [Complete output](../reference_outputs/RAN5_P1_CQ3-3/f08bc349d28b03c6d133c390dc7a248180dba24701dba865ab083b8f4c8f1422.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ3-3/f08bc349d28b03c6d133c390dc7a248180dba24701dba865ab083b8f4c8f1422.json).

Original query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company)
RETURN c.companyName AS companyName, count(DISTINCT cr) AS crCount
ORDER BY crCount DESC
```


## RAN5_P1_CQ4-2

Original English (unchanged): For each liaison statement (LS), show its direction and recipient working groups (LS routing analysis).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"},{"name":"direction","nullable":true,"source_column_or_expression":"direction","type":"string"},{"json_schema":{"items":{"type":"string"},"type":"array"},"name":"recipients","nested_array_semantics":{"$":"set"},"nullable":false,"source_column_or_expression":"recipients","type":"json"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `f548a5165e160f407724fccd5c052386e96cdf1a8a99019ab1e108c8e457fd9a`. Native rows: 529. [Complete output](../reference_outputs/RAN5_P1_CQ4-2/c54237db117030a7a9f7e522e68bf86fe86453ad2a1562cc03dcf678805e2911.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ4-2/c54237db117030a7a9f7e522e68bf86fe86453ad2a1562cc03dcf678805e2911.json).

Original query:
```cypher
MATCH (ls:LS) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo ORDER BY ls.tdocNumber, ls.direction LIMIT 5
```

Repaired reference query:
```cypher
MATCH (ls:LS) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber AS tdocNumber, ls.direction AS direction, collect(DISTINCT wg.wgName) AS recipients
```


## RAN5_P1_CQ5-1

Original English (unchanged): Report node counts by label across the graph (dataset overview).

Repair: `scorer_only`. Required fields: `[{"name":"label","nullable":false,"source_column_or_expression":"label","type":"string"},{"name":"nodeCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `6f8be30df99d1ebb3f4dbe82affc6d9c51f28cf69d894474ec1691d6fa012f63`. Native rows: 22. [Complete output](../reference_outputs/RAN5_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ5-1/9272d79cacc80c0c4aa3cc1c2cea77240c11d4146959afe3c1130b03eb9f5fa6.json).

Original query:
```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```

Repaired reference query:
```cypher
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
```


## RAN5_P1_CQ5-2

Original English (unchanged): Show TDoc counts per meeting, most recent first (coverage check).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"desc","source_column":"meetingNumber"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c7ed2f9e90ec599ceaf7bfe40a060608c9c5bfe84a8a452aef49cbeb4b7bb9f2`. Native rows: 35. [Complete output](../reference_outputs/RAN5_P1_CQ5-2/2517476d85167840e33d697c641f890924a166bddaa6c41ccb4b8b1132757c87.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ5-2/2517476d85167840e33d697c641f890924a166bddaa6c41ccb4b8b1132757c87.json).

Original query:
```cypher
MATCH (m:Meeting) WITH m OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m, count(t) AS tdocs RETURN m.canonicalMeetingNumber, tdocs ORDER BY m.meetingNumberInt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT t) AS tdocCount ORDER BY meetingNumber DESC, meeting ASC
```


## RAN5_P1_CQ5-3

Original English (unchanged): How many TDocs have a submitting company recorded? (attribution coverage)

Repair: `query_and_scorer`. Required fields: `[{"name":"withCompany","nullable":false,"source_column_or_expression":"withCompany","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `68d3938bed0d66671424f0f0328440d6961aa0595c29e699f321ba6ebea710b9`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ5-3/58d3bd9b2b693f3791fe66e4260a21167528b274c019dc198881e0e3bdec511f.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ5-3/58d3bd9b2b693f3791fe66e4260a21167528b274c019dc198881e0e3bdec511f.json).

Original query:
```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(DISTINCT CASE WHEN c IS NOT NULL THEN t END) AS withCompany
```


## RAN5_P1_CQ5-4

Original English (unchanged): Break down TDocs by target release (release distribution).

Repair: `query_and_scorer`. Required fields: `[{"name":"release","nullable":false,"source_column_or_expression":"release","type":"string"},{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `3e9a06cf1fbe592510125e730184d0397b7529d6a3fd623e2df54106a471bb2d`. Native rows: 11. [Complete output](../reference_outputs/RAN5_P1_CQ5-4/0c68849b5e55ff9e15c1d62cd3090dd0b0492fecc1dc7ee9a0975b18ee668175.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ5-4/0c68849b5e55ff9e15c1d62cd3090dd0b0492fecc1dc7ee9a0975b18ee668175.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release) RETURN r.releaseName AS release, count(DISTINCT t) AS tdocCount
```


## RAN5_P1_CQ5-5

Original English (unchanged): Which ten specs receive the most CRs? (spec churn ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `60a13987b04c0267c0b6574fa4c56d077edabe7528d7f6b07bf36ab9314ce652`. Native rows: 94. [Complete output](../reference_outputs/RAN5_P1_CQ5-5/2e9256739735e9fd67ed227059cb5a360baf03927263df52765d6b76aaaf9fd3.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ5-5/2e9256739735e9fd67ed227059cb5a360baf03927263df52765d6b76aaaf9fd3.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sp:Spec)
OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(sp)
RETURN sp.specNumber AS specNumber, count(DISTINCT cr) AS crCount
ORDER BY crCount DESC
```


## RAN5_P1_CQ6-1

Original English (unchanged): How many TDocs were presented at meeting RAN5#109? (meeting volume)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocCount","nullable":false,"source_column_or_expression":"tdocCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `70a61905f0cc8d86fb479947f7ab04da4465ae552786e3427836da89eb245ce3`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ6-1/3dbbf441cd0076cedd8eec71c3090265dd24c0e8f9c6a377c70af257fc6418ef.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ6-1/3dbbf441cd0076cedd8eec71c3090265dd24c0e8f9c6a377c70af257fc6418ef.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN count(t) AS cnt
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:PRESENTED_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN count(DISTINCT t) AS tdocCount
```


## RAN5_P1_CQ6-2

Original English (unchanged): How many meetings are in the dataset? (corpus size)

Repair: `scorer_only`. Required fields: `[{"name":"meetingCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `8e2239ea90b761aa7a4f3998d185e2ad985b6be2522849b853df092806e52764`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ6-2/a2faf37065a7c932c13c99cb0037c96d7390940d693c15c7d29506b15f6522d2.json).

Original query:
```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```

Repaired reference query:
```cypher
MATCH (m:Meeting) RETURN count(m) AS cnt
```


## RAN5_P1_CQ6-3

Original English (unchanged): Compare the total TDoc count against the CR count (CR proportion).

Repair: `scorer_only`. Required fields: `[{"name":"tdocCount","nullable":false,"source_column_or_expression":"total","type":"integer"},{"name":"crCount","nullable":false,"source_column_or_expression":"crs","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","value":1}`.

Repair SHA: `39f514a89a1981bfb4685c45e0a53671d92738f2d546d87602b3f2fefbae7944`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ6-3/12f1bc8faab308b35c2c9a6863e710016120f2346f415ef7a8aedaec6a3d8949.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ6-3/12f1bc8faab308b35c2c9a6863e710016120f2346f415ef7a8aedaec6a3d8949.json).

Original query:
```cypher
MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
```

Repaired reference query:
```cypher
MATCH (t:Tdoc) WITH count(t) AS total MATCH (cr:CR) RETURN total, count(cr) AS crs
```


## RAN5_P1_CQ6-4

Original English (unchanged): How many liaison statements (LS) are recorded? (LS count)

Repair: `scorer_only`. Required fields: `[{"name":"lsCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `29cc87490ad4049164939f6b4e5198bc89f12abc7797b0304d1a72ccd01924b9`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ6-4/92c3a7a58fbaf1c8000444a338e96d73352f722f99deb33b84147987e7ccd5c2.json).

Original query:
```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```

Repaired reference query:
```cypher
MATCH (ls:LS) RETURN count(ls) AS cnt
```


## RAN5_P1_CQ6-5

Original English (unchanged): How many Contact nodes exist? (contact count)

Repair: `scorer_only`. Required fields: `[{"name":"contactCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `01e5443fb3a930aa4540a8a476af3132bc113cd83f3516309bdb91b7e045bebb`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ6-5/5f863f699ba7f9ffe87b8f89702ae83ea088e36420bf599f9997d8068f5c7c2b.json).

Original query:
```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```

Repaired reference query:
```cypher
MATCH (c:Contact) RETURN count(c) AS cnt
```


## RAN5_P1_CQ7-1

Original English (unchanged): How many agenda items are recorded? (agenda count)

Repair: `scorer_only`. Required fields: `[{"name":"agendaCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `9d6ffc962097f1f574fbe999c8b182deb05ec286e83fcce91795d1518a603aff`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ7-1/1801032cdf796a28acba8c03f374d49789e14df489943dce0aca2bd5640f0ad8.json).

Original query:
```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
```


## RAN5_P1_CQ7-2

Original English (unchanged): How many Work Items are recorded? (work-item count)

Repair: `scorer_only`. Required fields: `[{"name":"workItemCount","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `93c15f9c42b9972c225d6226586503f9e8a9e37a10faad574afb5714a2933e3c`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.jsonl) / [receipt](../reference_outputs/RAN5_P1_CQ7-2/6298f641a058724ad48356a6f6f2607c3f794dafc24fabf142ddf587da215118.json).

Original query:
```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```

Repaired reference query:
```cypher
MATCH (wi:WorkItem) RETURN count(wi) AS cnt
```


## RAN5_P2_CQ1-1

Original English (unchanged): List the conclusions reached at meeting RAN5#81 (meeting-outcome review).

Repair: `query_and_scorer`. Required fields: `[{"name":"conclusionId","nullable":false,"source_column_or_expression":"conclusionId","type":"string"},{"name":"content","nullable":true,"source_column_or_expression":"content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `ff395ce245f537df3baea9f2c12765c2f96de347490f1bbf8a3119ee1f7b7039`. Native rows: 9. [Complete output](../reference_outputs/RAN5_P2_CQ1-1/3a62dde859d732480ab17ce7162958d5d85e5a6528672ae9a1a4706cda2e7479.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-1/3a62dde859d732480ab17ce7162958d5d85e5a6528672ae9a1a4706cda2e7479.json).

Original query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN5#81'}) RETURN c.resolutionId AS id, c.content AS content, c.hasConsensus AS consensus ORDER BY c.sequence LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#81'}) RETURN DISTINCT c.resolutionId AS conclusionId, c.content AS content, c.hasConsensus AS consensus
```


## RAN5_P2_CQ1-2

Original English (unchanged): Show the number of resolutions per agenda item (agenda-outcome breakdown).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"},{"name":"agendaNumber","nullable":false,"source_column_or_expression":"agendaNumber","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `6e8e4df8ee1f82848546d8925ce4a147bebfd4ad90fc91adc242ea99494cfffe`. Native rows: 8632. [Complete output](../reference_outputs/RAN5_P2_CQ1-2/b745f12fd11591022d995e706fadf1a7d95eea0b132280e18a82ae463107b7b4.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-2/b745f12fd11591022d995e706fadf1a7d95eea0b132280e18a82ae463107b7b4.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, count(r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN agenda, cnt
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem) OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai) RETURN ai.meetingNumber AS meeting, ai.agendaNumber AS agendaNumber, count(DISTINCT r) AS resolutionCount
```


## RAN5_P2_CQ1-3

Original English (unchanged): How many resolutions relate to each release? (release-outcome breakdown)

Repair: `query_and_scorer`. Required fields: `[{"name":"release","nullable":false,"source_column_or_expression":"release","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `8a783b9d92514fc754452624f3d5be0c47f50dda0f7c020bd98c62eca3f8fd5c`. Native rows: 11. [Complete output](../reference_outputs/RAN5_P2_CQ1-3/1937ac1daac300c409a7117d98c76a9487faf6b62d494cb7682f4e499a6848ac.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-3/1937ac1daac300c409a7117d98c76a9487faf6b62d494cb7682f4e499a6848ac.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release) WHERE rel.releaseName STARTS WITH 'Rel-' WITH rel.releaseName AS release, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN release, cnt
```

Repaired reference query:
```cypher
MATCH (rel:Release) WHERE rel.releaseName STARTS WITH 'Rel-' OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:TARGET_RELEASE]->(rel) RETURN rel.releaseName AS release, count(DISTINCT r) AS resolutionCount
```


## RAN5_P2_CQ1-4

Original English (unchanged): How many resolutions touch each modified spec? (spec-outcome breakdown)

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one count record for every distinct specNumber targeted by a recorded Tdoc MODIFIES edge; include zero resolutions","mode":"all"}`.

Repair SHA: `7d7872dec7b31556f5db476979b99dbe109f28b7b3b3ce984fea5c32729a5abe`. Native rows: 67. [Complete output](../reference_outputs/RAN5_P2_CQ1-4/5d1dbf2fa40dd122828c5eb4b0a9e44fbf173964c7255af4ecad3162d77c5234.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-4/5d1dbf2fa40dd122828c5eb4b0a9e44fbf173964c7255af4ecad3162d77c5234.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH s.specNumber AS spec, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN spec, cnt
```

Repaired reference query:
```cypher
MATCH (:Tdoc)-[:MODIFIES]->(modified:Spec) WITH DISTINCT modified.specNumber AS specNumber OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:MODIFIES]->(s:Spec) WHERE s.specNumber = specNumber RETURN specNumber, count(DISTINCT r) AS resolutionCount
```


## RAN5_P2_CQ1-5

Original English (unchanged): How many resolutions relate to each Work Item? (work-item outcome breakdown)

Repair: `query_and_scorer`. Required fields: `[{"name":"workItemCode","nullable":false,"source_column_or_expression":"workItemCode","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7758a37d16887ed7cfe36a63c0d43f1ff9fac8a4345d68b5dff873da8686baed`. Native rows: 398. [Complete output](../reference_outputs/RAN5_P2_CQ1-5/09000588b765b5f2e76a3bb1d7d0b2db6287eb1c4deb6c04aa785e09734f1fcf.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-5/09000588b765b5f2e76a3bb1d7d0b2db6287eb1c4deb6c04aa785e09734f1fcf.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) WITH wi.workItemCode AS wi_id, count(DISTINCT r) AS cnt ORDER BY cnt DESC, wi_id LIMIT 10 RETURN wi_id, cnt
```

Repaired reference query:
```cypher
MATCH (wi:WorkItem) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(:Tdoc)-[:RELATED_TO]->(wi) RETURN wi.workItemCode AS workItemCode, count(DISTINCT r) AS resolutionCount
```


## RAN5_P2_CQ1-6

Original English (unchanged): Which ten agenda items yielded the most resolutions? (busiest-agenda ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"agendaItemId","nullable":false,"source_column_or_expression":"agendaItemId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"resolutionCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `44d3b8aae136cba8911267198055d846c0e5e5f7589c10e8cb108caf7a7ac3a4`. Native rows: 8632. [Complete output](../reference_outputs/RAN5_P2_CQ1-6/a2f8c4eea238ccabbe8fc28236da6eb670ef6fc6e594326fab237d8c91b58d25.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ1-6/a2f8c4eea238ccabbe8fc28236da6eb670ef6fc6e594326fab237d8c91b58d25.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WITH ai.agendaNumber AS agenda, ai.meetingNumber AS meeting, count(r) AS cnt ORDER BY cnt DESC, agenda, meeting LIMIT 10 RETURN agenda, meeting, cnt
```

Repaired reference query:
```cypher
MATCH (ai:AgendaItem)
OPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai)
WITH ai, count(DISTINCT r) AS resolutionCount
RETURN coalesce(ai.id, ai.iri) AS agendaItemId, resolutionCount
ORDER BY resolutionCount DESC
```


## RAN5_P2_CQ2-1

Original English (unchanged): Which TDocs are referenced by two or more resolutions? (frequently-cited documents)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `942ea9f4e831dc4bda3aaec102db00fa0cf8f2f4a11d29031bb9310b201f3dfe`. Native rows: 7. [Complete output](../reference_outputs/RAN5_P2_CQ2-1/6bf6cbae13975c91ab6bc36c27eea3ae6a4299b22ba6a7dfe5e33bb6a8c8c32e.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ2-1/6bf6cbae13975c91ab6bc36c27eea3ae6a4299b22ba6a7dfe5e33bb6a8c8c32e.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t.tdocNumber AS tdoc, count(r) AS ref_count WHERE ref_count >= 2 RETURN tdoc, ref_count ORDER BY ref_count DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t.tdocNumber AS tdocNumber, count(DISTINCT r) AS resolutionCount WHERE resolutionCount>=2 RETURN tdocNumber, resolutionCount
```


## RAN5_P2_CQ2-2

Original English (unchanged): For each resolution, list the TDocs it references (resolution-to-document mapping).

Repair: `query_and_scorer`. Required fields: `[{"name":"resolutionId","nullable":false,"source_column_or_expression":"resolutionId","type":"string"},{"json_schema":{"items":{"type":"string"},"type":"array"},"name":"tdocNumbers","nested_array_semantics":{"$":"set"},"nullable":false,"source_column_or_expression":"tdocNumbers","type":"json"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `a54974b8cae368e0759db1cc544cd29a1b72cf35c26a13e952ecd61f5b92a515`. Native rows: 83. [Complete output](../reference_outputs/RAN5_P2_CQ2-2/81bf83a73268c12f2da15f1956af6770541c45867ad8f3282bb7f39cea321e7b.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ2-2/81bf83a73268c12f2da15f1956af6770541c45867ad8f3282bb7f39cea321e7b.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r.resolutionId AS rid, collect(t.tdocNumber) AS tdocs, count(t) AS cnt ORDER BY cnt DESC, rid LIMIT 10 RETURN rid, cnt, tdocs[..5] AS sample_tdocs
```

Repaired reference query:
```cypher
MATCH (r:Resolution) OPTIONAL MATCH (r)-[:REFERENCES]->(t:Tdoc) RETURN r.resolutionId AS resolutionId, collect(DISTINCT t.tdocNumber) AS tdocNumbers
```


## RAN5_P2_CQ2-4

Original English (unchanged): Which specs does each referenced TDoc end up modifying? (document-to-spec impact)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"},{"json_schema":{"items":{"type":"string"},"type":"array"},"name":"specNumbers","nested_array_semantics":{"$":"set"},"nullable":false,"source_column_or_expression":"specNumbers","type":"json"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `a6dc4b0f79c5844d9cef9deb56a4ab4b06f8f12be0d91dbf23aaafc81ac5b8fd`. Native rows: 336. [Complete output](../reference_outputs/RAN5_P2_CQ2-4/d1c6567717f206d762872c7dd82dfd9c9d3dac7a26e87e78af7011299546ca96.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ2-4/d1c6567717f206d762872c7dd82dfd9c9d3dac7a26e87e78af7011299546ca96.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH t.tdocNumber AS tdoc, collect(DISTINCT s.specNumber) AS specs, count(DISTINCT s) AS spec_count ORDER BY spec_count DESC, tdoc LIMIT 10 RETURN tdoc, spec_count, specs[..5] AS sample_specs
```

Repaired reference query:
```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc) WITH DISTINCT t OPTIONAL MATCH (t)-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber AS tdocNumber, collect(DISTINCT s.specNumber) AS specNumbers
```


## RAN5_P2_CQ3-1

Original English (unchanged): Which ten companies submitted the most resolution-referenced TDocs? (influence ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `b8854a11f4ad9ed06e4bb0766ac361d1ab2dc96833fcc24be5ce752b604058c0`. Native rows: 60. [Complete output](../reference_outputs/RAN5_P2_CQ3-1/375d949c90da47e61c26c85919b3235b4fbcc9f36d6007203b0210c20de737cf.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ3-1/375d949c90da47e61c26c85919b3235b4fbcc9f36d6007203b0210c20de737cf.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WITH c.companyName AS company, count(DISTINCT r) AS resolution_count ORDER BY resolution_count DESC, company LIMIT 10 RETURN company, resolution_count
```

Repaired reference query:
```cypher
MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company)
RETURN c.companyName AS companyName, count(DISTINCT t) AS tdocCount
ORDER BY tdocCount DESC
```


## RAN5_P2_CQ3-2

Original English (unchanged): Show each company's resolution contributions per Work Item (technology contribution breakdown).

Repair: `query_and_scorer`. Required fields: `[{"name":"workItemCode","nullable":false,"source_column_or_expression":"workItemCode","type":"string"},{"name":"company","nullable":false,"source_column_or_expression":"company","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `1629955f656ef84105c12c02f748ba66c2edae294900bd6904683d7e83b67997`. Native rows: 85. [Complete output](../reference_outputs/RAN5_P2_CQ3-2/cc6a556f0e685e3030ed91c98f83d6e8d80f86e0a68560b351e5d1627151b9b3.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ3-2/cc6a556f0e685e3030ed91c98f83d6e8d80f86e0a68560b351e5d1627151b9b3.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) MATCH (t)-[:SUBMITTED_BY]->(c:Company) WITH wi.workItemCode AS wi_id, c.companyName AS company, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN wi_id, company, cnt
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (t)-[:SUBMITTED_BY]->(c:Company) RETURN wi.workItemCode AS workItemCode, c.companyName AS company, count(DISTINCT r) AS resolutionCount
```


## RAN5_P2_CQ6-1

Original English (unchanged): Track resolution counts across meetings over time (resolution trend).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"asc","source_column":"meetingNumber"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `2255f2a3cb0fb2ddffff249e1112355f4442889e0bcbba5c636be8a011e07e4d`. Native rows: 35. [Complete output](../reference_outputs/RAN5_P2_CQ6-1/4986278ff854149f6c194337b8c87df4bedb12b3a9c6575e01394d357820986f.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ6-1/4986278ff854149f6c194337b8c87df4bedb12b3a9c6575e01394d357820986f.json).

Original query:
```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(r) AS cnt ORDER BY num ASC RETURN meeting, cnt
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
```


## RAN5_P2_CQ6-2

Original English (unchanged): Track Samsung's resolution contributions across meetings over time (contribution trend).

Repair: `query_and_scorer`. Required fields: `[{"name":"meeting","nullable":false,"source_column_or_expression":"meeting","type":"string"},{"name":"resolutionCount","nullable":false,"source_column_or_expression":"resolutionCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"asc","source_column":"meetingNumber"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `6368208dca58b62d405415d49a325ac25cf595289e2035921227b22e306fc5b3`. Native rows: 35. [Complete output](../reference_outputs/RAN5_P2_CQ6-2/76e29fd5b7e773d2678eaf7f79eea070c4ee455a763837ea4f22f0dda7dc1014.jsonl) / [receipt](../reference_outputs/RAN5_P2_CQ6-2/76e29fd5b7e773d2678eaf7f79eea070c4ee455a763837ea4f22f0dda7dc1014.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(DISTINCT r) AS cnt ORDER BY num ASC RETURN meeting, cnt
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (m)<-[:MADE_AT]-(r:Resolution)-[:REFERENCES]->(:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Samsung'}) RETURN m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS meetingNumber, count(DISTINCT r) AS resolutionCount ORDER BY meetingNumber ASC, meeting ASC
```


## RAN5_P3_CQ1-1

Original English (unchanged): List the sections of TS 38.533 (structure browsing).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `06914ba767f0651150309c445bc1cb3a0d7e20b6e4a8cfcb9fa813bed568554a`. Native rows: 24890. [Complete output](../reference_outputs/RAN5_P3_CQ1-1/a60e2d232dd3da583a38de994a1ed8632ef4180471090432541f9da0a0ffecb5.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-1/a60e2d232dd3da583a38de994a1ed8632ef4180471090432541f9da0a0ffecb5.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT s.sectionId AS sectionId, s.sectionNumber AS sectionNumber, s.sectionTitle AS title, s.level AS level
```


## RAN5_P3_CQ1-10

Original English (unchanged): Locate the spec and section for tables numbered 6.2.x (table-number lookup).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"},{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct (specNumber, sectionId) locations of qualifying tables; shared locations appear once under set scoring, with no unstated cap","mode":"all"}`.

Repair SHA: `13b932769235990e264ba02ed33926c69583f818aae223498b6319980a9c8f03`. Native rows: 1863. [Complete output](../reference_outputs/RAN5_P3_CQ1-10/60f4a1a456ee66a0506f9c094d81091c14599a7058f82366290cbf6fbee7965f.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-10/60f4a1a456ee66a0506f9c094d81091c14599a7058f82366290cbf6fbee7965f.json).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable) WHERE t.tableNumber STARTS WITH '6.2' RETURN sp.specNumber, sec.sectionId, t.tableNumber, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable) WHERE t.tableNumber STARTS WITH '6.2.' RETURN DISTINCT sp.specNumber AS specNumber, sec.sectionId AS sectionId, t.tableNumber AS tableNumber
```


## RAN5_P3_CQ1-11

Original English (unchanged): List the level-2 sections of TS 38.521-2 (second-level outline).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `222718776d93b7a1d10e2a47f2318fc955e81e4d2c93646b12d9d0fa86db4d53`. Native rows: 352. [Complete output](../reference_outputs/RAN5_P3_CQ1-11/f8bc0381950fe03f69ab78190f3b8b3c498bbe664c16281a46406f0ad38f1840.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-11/f8bc0381950fe03f69ab78190f3b8b3c498bbe664c16281a46406f0ad38f1840.json).

Original query:
```cypher
MATCH (s:Section {level: 2})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-2'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {level:2})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-2'}) RETURN DISTINCT s.sectionId AS sectionId
```


## RAN5_P3_CQ1-13

Original English (unchanged): List the void sections of TS 38.521-1 (identifying removed clauses).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `bd0d2875af20bdb6d0feb2148e27605d01b13caecaf8cde4c71e5292b49d8c2c`. Native rows: 174. [Complete output](../reference_outputs/RAN5_P3_CQ1-13/1b19199e4c0b4452c1f31ba06fdfca855a6b351e75df099b1e1b3a94f83fd117.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-13/1b19199e4c0b4452c1f31ba06fdfca855a6b351e75df099b1e1b3a94f83fd117.json).

Original query:
```cypher
MATCH (s:Section {isVoid: true})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {isVoid:true})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT s.sectionId AS sectionId
```


## RAN5_P3_CQ1-14

Original English (unchanged): How many tables does TS 38.533 contain? (table count)

Repair: `query_and_scorer`. Required fields: `[{"name":"tableCount","nullable":false,"source_column_or_expression":"tableCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `667a21890e0ba9b964d814b62b65f1a9efe5ffc1c43b36637655af23d5a134da`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ1-14/1acee4a9ee7fc3d3833a1a836c6c293410042a386f4fb4b703fd1b99019933e0.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-14/1acee4a9ee7fc3d3833a1a836c6c293410042a386f4fb4b703fd1b99019933e0.json).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN count(t) AS tableCount
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN count(DISTINCT t) AS tableCount
```


## RAN5_P3_CQ1-15

Original English (unchanged): List the level-3 sections of TS 38.533 (deep-outline browsing).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `dcbf029f48a38c83dd988a7a66771c7cc3ce5dae792ff3b3f5aba9d43d25b997`. Native rows: 931. [Complete output](../reference_outputs/RAN5_P3_CQ1-15/55b3bddf20bf7bd74ddeddc9daa92274ea950983448f480bd0ca4d09bbfbb6c4.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-15/55b3bddf20bf7bd74ddeddc9daa92274ea950983448f480bd0ca4d09bbfbb6c4.json).

Original query:
```cypher
MATCH (s:Section {level: 3})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section {level:3})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) RETURN DISTINCT s.sectionId AS sectionId
```


## RAN5_P3_CQ1-4

Original English (unchanged): List the level-1 sections of TS 38.533 (top-level outline).

Repair: `scorer_only`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `a3d1fb0de42b1542d210c1dd90b972756de2306ca953f875a72e0649d2ef6b96`. Native rows: 231. [Complete output](../reference_outputs/RAN5_P3_CQ1-4/350c3a1642232688a7777aaeba71653dfe1347f1e337bb79b97b6e079e7f7b3d.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-4/350c3a1642232688a7777aaeba71653dfe1347f1e337bb79b97b6e079e7f7b3d.json).

Original query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```


## RAN5_P3_CQ1-7

Original English (unchanged): Find which sections contain tables in TS 38.521-1 (table-to-section mapping).

Repair: `query_and_scorer`. Required fields: `[{"name":"tableId","nullable":false,"source_column_or_expression":"tableId","type":"string"},{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7fd0ec34e825789378ce724d62b45f32ee960055e6ebad63ed9a5ebc92909360`. Native rows: 5457. [Complete output](../reference_outputs/RAN5_P3_CQ1-7/1ec3e03b1228df97a00a6d812535447b1a2aed820c0c66fcf7e539389cd937e0.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-7/1ec3e03b1228df97a00a6d812535447b1a2aed820c0c66fcf7e539389cd937e0.json).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) RETURN t.tableId, sec.sectionId, sec.sectionTitle ORDER BY t.tableNumber, t.tableId LIMIT 5
```

Repaired reference query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT t.tableId AS tableId, sec.sectionId AS sectionId
```


## RAN5_P3_CQ1-8

Original English (unchanged): List all tables in TS 38.523-1 (table inventory).

Repair: `query_and_scorer`. Required fields: `[{"name":"tableId","nullable":false,"source_column_or_expression":"tableId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `b960cd5d144042f1f4ebfac6f0c2a5353e24cbb227997a163106b3f12f7382e7`. Native rows: 22352. [Complete output](../reference_outputs/RAN5_P3_CQ1-8/e8b7b7b27ddfe5b9bd4f1b94fd17c8e2f3f13eb459bf12a9a4b52fd214cd8e86.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-8/e8b7b7b27ddfe5b9bd4f1b94fd17c8e2f3f13eb459bf12a9a4b52fd214cd8e86.json).

Original query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.523-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber, t.tableId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.523-1'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN DISTINCT t.tableId AS tableId
```


## RAN5_P3_CQ1-9

Original English (unchanged): Find sections of TS 38.533 whose title contains 'measurement' (topic search).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `59792f7288820777828bc943ec38dff3052edeb9613997e39419d0a78613cdfd`. Native rows: 1945. [Complete output](../reference_outputs/RAN5_P3_CQ1-9/ac3736d234b0ca26ff4f4736cceff9742b8b7b20f0881482aa45fe034a0c0b9f.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ1-9/ac3736d234b0ca26ff4f4736cceff9742b8b7b20f0881482aa45fe034a0c0b9f.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionNumber, s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.533'}) WHERE toLower(s.sectionTitle) CONTAINS 'measurement' RETURN DISTINCT s.sectionId AS sectionId, s.sectionTitle AS title
```


## RAN5_P3_CQ2-2

Original English (unchanged): Which ten sections are referenced most often? (most-cited clauses)

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `959cbdf964c2a796a30254d6cae898ca879945006e762a4b608baba69fe843f7`. Native rows: 76749. [Complete output](../reference_outputs/RAN5_P3_CQ2-2/7eeced8f2d16a80634f9d1f420e063240e29f18b885b8fb9eeda7d3cf1573edf.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-2/7eeced8f2d16a80634f9d1f420e063240e29f18b885b8fb9eeda7d3cf1573edf.json).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH b, count(a) AS refCount RETURN b.sectionId, b.sectionTitle, refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (b:Section)
OPTIONAL MATCH (:Section)-[ref:REFERENCES_SECTION]->(b)
RETURN b.sectionId AS sectionId, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```


## RAN5_P3_CQ2-3

Original English (unchanged): Which ten sections make the most outgoing references? (heaviest referrers)

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `f77dc894c209b99b7af4da16290e7ee22727f93af90370cbcb08777e1cb1f61f`. Native rows: 76749. [Complete output](../reference_outputs/RAN5_P3_CQ2-3/5e379a257fd65276dd4f642bb4716aee111ed68dbb6b97ba0857ce987279b1c8.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-3/5e379a257fd65276dd4f642bb4716aee111ed68dbb6b97ba0857ce987279b1c8.json).

Original query:
```cypher
MATCH (a:Section)-[:REFERENCES_SECTION]->(b:Section) WITH a, count(b) AS outCount RETURN a.sectionId, outCount ORDER BY outCount DESC, a.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section)
OPTIONAL MATCH (a)-[ref:REFERENCES_SECTION]->(:Section)
RETURN a.sectionId AS sectionId, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```


## RAN5_P3_CQ2-4

Original English (unchanged): Which spec-to-spec section-reference pairs are most frequent? (cross-spec coupling)

Repair: `query_and_scorer`. Required fields: `[{"name":"fromSpec","nullable":false,"source_column_or_expression":"fromSpec","type":"string"},{"name":"toSpec","nullable":false,"source_column_or_expression":"toSpec","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all recorded directed cross-spec specNumber pairs tied at the highest frequency of distinct section-reference edges; no arbitrary k","mode":"all"}`.

Repair SHA: `404f716c104f531e7aa4fe2834c4c1b5ce9297039e47041a5eeb3c9dbe5b7442`. Native rows: 2. [Complete output](../reference_outputs/RAN5_P3_CQ2-4/8a177aea43fcbb1c006147ff7f80f99d719264657cc9a2a33760f97b7f5da227.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-4/8a177aea43fcbb1c006147ff7f80f99d719264657cc9a2a33760f97b7f5da227.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section)-[ref:REFERENCES_SECTION]->(b:Section),
(a)-[:BELONGS_TO_SPEC]->(sa:Spec),
(b)-[:BELONGS_TO_SPEC]->(sb:Spec)
WHERE sa.specNumber <> sb.specNumber
WITH sa.specNumber AS fromSpec, sb.specNumber AS toSpec,
count(DISTINCT ref) AS referenceCount
WITH collect({fromSpec:fromSpec,toSpec:toSpec,referenceCount:referenceCount}) AS pairs,
max(referenceCount) AS maximumFrequency
UNWIND pairs AS pair
WITH pair, maximumFrequency WHERE pair.referenceCount = maximumFrequency
RETURN pair.fromSpec AS fromSpec, pair.toSpec AS toSpec
```


## RAN5_P3_CQ2-5

Original English (unchanged): Which five specs does TS 38.521-1 reference most? (dependency ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `5a13a4fb02f79742c2d8c95d90c7aad315666421a1c9551c2a3b1466824be621`. Native rows: 7. [Complete output](../reference_outputs/RAN5_P3_CQ2-5/e76ab58d934b1fa6bb2978c6462224970f3d3c830d15bb7a1afbe674a5f477bd.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-5/e76ab58d934b1fa6bb2978c6462224970f3d3c830d15bb7a1afbe674a5f477bd.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC, target.specNumber LIMIT 5
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'})
MATCH (a)-[ref:REFERENCES_SPEC]->(target:Spec)
RETURN target.specNumber AS specNumber, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```


## RAN5_P3_CQ2-6

Original English (unchanged): Which ten spec-to-spec reference pairs are most frequent? (cross-spec dependencies)

Repair: `query_and_scorer`. Required fields: `[{"name":"fromSpec","nullable":false,"source_column_or_expression":"fromSpec","type":"string"},{"name":"toSpec","nullable":false,"source_column_or_expression":"toSpec","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"referenceCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `b13ad4991a616bb623a14d9ba7a62a479bd83bfd7771e706c2eef443d3d8702a`. Native rows: 101. [Complete output](../reference_outputs/RAN5_P3_CQ2-6/c25420a03761857b94b78159b33619ebea87d2b0fcd549e15d0e1f857ec3bb9a.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-6/c25420a03761857b94b78159b33619ebea87d2b0fcd549e15d0e1f857ec3bb9a.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec)
MATCH (a)-[ref:REFERENCES_SPEC]->(sb:Spec)
WHERE sa.specNumber <> sb.specNumber
RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT ref) AS referenceCount
ORDER BY referenceCount DESC
```


## RAN5_P3_CQ2-7

Original English (unchanged): How many internal cross-references does TS 38.533 contain? (self-reference density)

Repair: `query_and_scorer`. Required fields: `[{"name":"internalReferenceCount","nullable":false,"source_column_or_expression":"internalReferenceCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `da146f350929b391e7cc218a9263afc58fb972d6ea8dd665635f13d6c3f46d66`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ2-7/d003417ae92a10637d4cc3036155d2ad2b3709a46845fd55bab4d0777511a355.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ2-7/d003417ae92a10637d4cc3036155d2ad2b3709a46845fd55bab4d0777511a355.json).

Original query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs
```

Repaired reference query:
```cypher
MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.533'}), (a)-[r:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(DISTINCT r) AS internalReferenceCount
```


## RAN5_P3_CQ3-3

Original English (unchanged): List the CRs that modify TS 38.521-1 (change-request survey).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `0f8a2c56952b24ae6bbc9306fd53b6efc17926f315885e3f9f9be064aa732cb7`. Native rows: 4934. [Complete output](../reference_outputs/RAN5_P3_CQ3-3/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ3-3/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
```


## RAN5_P3_CQ3-4

Original English (unchanged): How many RAN5 CRs record the clauses they affect? (metadata completeness)

Repair: `query_and_scorer`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `8927dd785b7a8a675839b8439f193486af12bdcce8f0ef53ba65da2d1050c9cc`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ3-4/ff6c698b88259c492051e0109730f3a66f5e69d4d7877e8958fed967b98eb837.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ3-4/ff6c698b88259c492051e0109730f3a66f5e69d4d7877e8958fed967b98eb837.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN count(cr) AS crCount
```

Repaired reference query:
```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND trim(cr.clausesAffected)<>'' RETURN count(cr) AS crCount
```


## RAN5_P3_CQ4-2

Original English (unchanged): List the conclusions that reference CRs modifying TS 38.521-1 (decision provenance).

Repair: `query_and_scorer`. Required fields: `[{"name":"conclusionId","nullable":false,"source_column_or_expression":"conclusionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `74b75dfab51ca50a540222dce485fd4d5592758f905c6230599640f71f4dc3d6`. Native rows: 3. [Complete output](../reference_outputs/RAN5_P3_CQ4-2/c94bff345f653addfeb78305ba40ba7a240d0c055e31ac75203d2021b00a051c.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ4-2/c94bff345f653addfeb78305ba40ba7a240d0c055e31ac75203d2021b00a051c.json).

Original query:
```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN res.resolutionId, t.tdocNumber ORDER BY res.resolutionId DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT res.resolutionId AS conclusionId
```


## RAN5_P3_CQ4-4

Original English (unchanged): How many CRs do conclusions reference? (resolution-to-CR coverage)

Repair: `scorer_only`. Required fields: `[{"name":"crCount","nullable":false,"source_column_or_expression":"crCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `dc1d10444556ffd283940311dadb60c5c6d2ad7a1379cc89335f6da7be49bc4a`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ4-4/01a81f812fc24fbf698f2599e622443f0d393f3c99c5b23de2ecca5eae2ff85b.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ4-4/01a81f812fc24fbf698f2599e622443f0d393f3c99c5b23de2ecca5eae2ff85b.json).

Original query:
```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc:CR) RETURN count(DISTINCT res) AS resCount, count(DISTINCT t) AS crCount
```

Repaired reference query:
```cypher
MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc:CR) RETURN count(DISTINCT res) AS resCount, count(DISTINCT t) AS crCount
```


## RAN5_P3_CQ5-1

Original English (unchanged): List all CRs changing TS 38.521-1 (comprehensive change survey).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `da7e78620491bfb5a136f2ab90f1dfc4be4b0f130dbd27051b3092161059880e`. Native rows: 4934. [Complete output](../reference_outputs/RAN5_P3_CQ5-1/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ5-1/d2ce8f94b4334f3cf9f17ae7bf4429a29ed026c5ef83ded3b1d54e7795938678.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN cr.tdocNumber, cr.title ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) RETURN DISTINCT cr.tdocNumber AS tdocNumber
```


## RAN5_P3_CQ5-5

Original English (unchanged): How many sections do RAN5 specs contain in total? (corpus size)

Repair: `scorer_only`. Required fields: `[{"name":"sectionCount","nullable":false,"source_column_or_expression":"totalSections","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one requested scalar or fixed-identifier record","mode":"exact","value":1}`.

Repair SHA: `4316e820b11cff60c4f86f924dc91c58f9a33a8ea0d46485b149370a771d95e5`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ5-5/033ab4e020ba6721c2c8d5e5551762d4ebd7b2e756e56cbd94ba283c10a3fcae.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ5-5/033ab4e020ba6721c2c8d5e5551762d4ebd7b2e756e56cbd94ba283c10a3fcae.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(s) AS totalSections
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(s) AS totalSections
```


## RAN5_P3_CQ5-6

Original English (unchanged): How many tables do RAN5 specs contain in total? (table corpus size)

Repair: `scorer_only`. Required fields: `[{"name":"tableCount","nullable":false,"source_column_or_expression":"totalTables","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one requested scalar or fixed-identifier record","mode":"exact","value":1}`.

Repair SHA: `5860ed14168658f577f6a91b2dde36a1b806a836f5bd13c2df2ed47de46b2265`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ5-6/32e6a4c170dd841fd735fa9fd486a01b899004321768ebcd0006a60d2724c7a0.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ5-6/32e6a4c170dd841fd735fa9fd486a01b899004321768ebcd0006a60d2724c7a0.json).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(t) AS totalTables
```

Repaired reference query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(t) AS totalTables
```


## RAN5_P3_CQ5-7

Original English (unchanged): How many figures do RAN5 specs contain in total? (figure corpus size)

Repair: `scorer_only`. Required fields: `[{"name":"figureCount","nullable":false,"source_column_or_expression":"totalFigures","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one requested scalar or fixed-identifier record","mode":"exact","value":1}`.

Repair SHA: `af835129357bb31577f41d731779f22425a9b73fc6cec48d312b3433625ca3c1`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_CQ5-7/76b8cf0a466c25b998f750c33d3da82a571d11b4e96c472535ee82398e673014.jsonl) / [receipt](../reference_outputs/RAN5_P3_CQ5-7/76b8cf0a466c25b998f750c33d3da82a571d11b4e96c472535ee82398e673014.json).

Original query:
```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(f) AS totalFigures
```

Repaired reference query:
```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN count(f) AS totalFigures
```


## RAN5_P3_P3-S8-CQ02

Original English (unchanged): Are all item-level entity nodes linked to a section via definedInSection? (link-coverage check)

Repair: `query_and_scorer`. Required fields: `[{"name":"allLinked","nullable":false,"source_column_or_expression":"allLinked","type":"boolean"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one aggregate record, including zero count for an empty matching population","mode":"exact","value":1}`.

Repair SHA: `e31d2da256e06fceffe1d93f079447e5759c8cb27bbbc81ff37d91a0b8b3ee95`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P3_P3-S8-CQ02/c2f52383112b27941cd02b91433d69f675600ef3d86a36676f3766f646c46ad5.jsonl) / [receipt](../reference_outputs/RAN5_P3_P3-S8-CQ02/c2f52383112b27941cd02b91433d69f675600ef3d86a36676f3766f646c46ad5.json).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH count(n) AS total, sum(CASE WHEN exists((n)-[:definedInSection]->(:Section)) THEN 1 ELSE 0 END) AS linked RETURN CASE WHEN total=0 THEN null ELSE total=linked END AS allLinked
```


## RAN5_P3_P3-S8-CQ05

Original English (unchanged): Show the granularity distribution across the five entity classes (item-level vs legacy section-level).

Repair: `query_and_scorer`. Required fields: `[{"name":"entityClass","nullable":false,"source_column_or_expression":"entityClass","type":"string"},{"name":"granularity","nullable":true,"source_column_or_expression":"granularity","type":"string"},{"name":"nodeCount","nullable":false,"source_column_or_expression":"nodeCount","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `a7f9e688970a3dbdce4aa3ce2e77e28937f6e91702da352601818f02609ea9d0`. Native rows: 6. [Complete output](../reference_outputs/RAN5_P3_P3-S8-CQ05/53707b4e885ba0f3953e90e46a3760d9ed831a48cf5e47254f9a28553e767302.jsonl) / [receipt](../reference_outputs/RAN5_P3_P3-S8-CQ05/53707b4e885ba0f3953e90e46a3760d9ed831a48cf5e47254f9a28553e767302.json).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

Repaired reference query:
```cypher
UNWIND ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'] AS entityClass OPTIONAL MATCH (n) WHERE entityClass IN labels(n) RETURN entityClass, n.granularity AS granularity, count(n) AS nodeCount
```


## RAN5_P4_CQ2-1

Original English (unchanged): List the other specs affected by CR R5-255419 (cross-spec impact).

Repair: `scorer_only`. Required fields: `[{"name":"spec","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"Original query has no LIMIT and returns every declared AFFECTS target for this fixed CR; requested set/all does not require auxiliary CR or relationship-type fields. Fresh or exact-original full native receipt remains a separate gate.","mode":"all"}`.

Repair SHA: `d428b95a74812cbc43f1f854895ba4e5be10b6990c09c2824557da3fdcb8808c`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P4_CQ2-1/41d289cfbe9a80945f2fe290b1b283a44f2346c1c93c8a26e2b92325dce2679c.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ2-1/41d289cfbe9a80945f2fe290b1b283a44f2346c1c93c8a26e2b92325dce2679c.json).

Original query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R5-255419' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R5-255419' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
```


## RAN5_P4_CQ2-2

Original English (unchanged): Which CRs modifying TS 38.521-1 also affect other specs? (ripple-effect screening)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `f911405b0f8177603fc0152b882f9855b7165b22a8f2b70d586ef70beb183bf6`. Native rows: 399. [Complete output](../reference_outputs/RAN5_P4_CQ2-2/682c9f535c927b44c92021d9ef23d339f0ce15a565a6f5648aca8c43e39d9311.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ2-2/682c9f535c927b44c92021d9ef23d339f0ce15a565a6f5648aca8c43e39d9311.json).

Original query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.521-1'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(:Spec {specNumber:'38.521-1'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber<>'38.521-1' } RETURN DISTINCT c.tdocNumber AS tdocNumber
```


## RAN5_P4_CQ2-3

Original English (unchanged): List the CRs that flag TS 38.533 as an affected spec (incoming impact).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `1c535efc88c999f605175957d8d0e9ea2b17f48ad2065b4a7916757def546aec`. Native rows: 768. [Complete output](../reference_outputs/RAN5_P4_CQ2-3/a8ce5ffb23cc024b4f191d5ec0c0ea46ea17bc7e8aaf3572201751d478e7e41e.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ2-3/a8ce5ffb23cc024b4f191d5ec0c0ea46ea17bc7e8aaf3572201751d478e7e41e.json).

Original query:
```cypher
MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (:Spec {specNumber:'38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber
```


## RAN5_P4_CQ2-4

Original English (unchanged): Which ten CRs affect the most other specs? (broadest-impact ranking)

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"otherSpecCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `885d308f1c4b7ad0b2fda225bad748961367bd39d282e8f3f03ae9ec5fb72206`. Native rows: 53351. [Complete output](../reference_outputs/RAN5_P4_CQ2-4/32b84b815aede1f1b5e64fc979f8f8cac832ba5c2432d028210d29b325814f94.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ2-4/32b84b815aede1f1b5e64fc979f8f8cac832ba5c2432d028210d29b325814f94.json).

Original query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
```

Repaired reference query:
```cypher
MATCH (c:CR)
OPTIONAL MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec)
WITH c, count(DISTINCT s.specNumber) AS otherSpecCount
RETURN c.tdocNumber AS tdocNumber, otherSpecCount
ORDER BY otherSpecCount DESC
```


## RAN5_P4_CQ3-2

Original English (unchanged): Which CR packs contain CRs for the 5GS_NR_LTE-UEConTest work items? (work-item pack lookup)

Repair: `query_and_scorer`. Required fields: `[{"name":"crPackId","nullable":false,"source_column_or_expression":"crPackId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `426038561a8ebf751b90b38566db0617db09a1decbbfa0cd66ac89c8913210cd`. Native rows: 194. [Complete output](../reference_outputs/RAN5_P4_CQ3-2/380d216f0ea43beee57850bb0a8c168f16f90c8b120e76b1a8cdf08d9a6f7f38.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ3-2/380d216f0ea43beee57850bb0a8c168f16f90c8b120e76b1a8cdf08d9a6f7f38.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC, pack.crPackId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId
```


## RAN5_P4_CQ3-3

Original English (unchanged): List the ten largest CR packs by CR count (pack overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"crPackId","nullable":false,"source_column_or_expression":"crPackId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `91593edaf9745d03aa4b1bccf555a3077c9fffac73b30433ba5a2a275d47e055`. Native rows: 1220. [Complete output](../reference_outputs/RAN5_P4_CQ3-3/da29340616ac446b37e8c805d57e37716f85b10cfdd5b1313cf2e735942d4bc1.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ3-3/da29340616ac446b37e8c805d57e37716f85b10cfdd5b1313cf2e735942d4bc1.json).

Original query:
```cypher
MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) RETURN pack.crPackId AS crPackId, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack)
OPTIONAL MATCH (pack)-[:HAS_CR]->(cr:CR)
RETURN pack.crPackId AS crPackId, count(DISTINCT cr) AS crCount
ORDER BY crCount DESC
```


## RAN5_P4_CQ4-1

Original English (unchanged): Give the change reasons of CRs modifying section 6.2 of TS 38.521-1 (clause-level rationale).

Repair: `query_and_scorer`. Required fields: `[{"name":"reason","nullable":true,"source_column_or_expression":"reason","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct recorded reason values from the full qualifying CR population, retaining declared null values if present; no per-CR multiplicity or unasked ID requirement","mode":"all"}`.

Repair SHA: `2c540c9691bdceffee0a6b4e59f2be75ec2bd4d5abc4131a2c2cd53a598aabcf`. Native rows: 7. [Complete output](../reference_outputs/RAN5_P4_CQ4-1/2dc633130fcbbf61febad7cd462ea363c2dd05603f8b6d21614f07d40a97c40e.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ4-1/2dc633130fcbbf61febad7cd462ea363c2dd05603f8b6d21614f07d40a97c40e.json).

Original query:
```cypher
MATCH (sec:Section {sectionNumber: '6.2'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section {sectionNumber:'6.2'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.521-1'}), (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.reasonForChange AS reason
```


## RAN5_P4_CQ4-2

Original English (unchanged): For CRs referenced by a conclusion, give their change reason and summary (decision-linked rationale).

Repair: `query_and_scorer`. Required fields: `[{"name":"reason","nullable":true,"source_column_or_expression":"reason","type":"string"},{"name":"summary","nullable":true,"source_column_or_expression":"summary","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct same-CR (reason, summary) tuples from every Conclusion-referenced CR, including declared nulls; no per-CR ID or occurrence-count requirement","mode":"all"}`.

Repair SHA: `64110702aa9496c5e3ff6b76caebe165199025eb154bec866617c18cdf228ac3`. Native rows: 135. [Complete output](../reference_outputs/RAN5_P4_CQ4-2/0dd497f777999b1a12692abcb7015ba4d4ab972bf476deb3780d4808f15320ac.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ4-2/0dd497f777999b1a12692abcb7015ba4d4ab972bf476deb3780d4808f15320ac.json).

Original query:
```cypher
MATCH (con:Conclusion)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
```

Repaired reference query:
```cypher
MATCH (:Conclusion)-[:REFERENCES]->(c:CR) RETURN DISTINCT c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
```


## RAN5_P4_CQ4-3

Original English (unchanged): Which sections do the 5GS_NR_LTE-UEConTest CRs modify? (work-item clause impact)

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `0936c14a346cc1338978164a89049b33ea0f7adb90d03970694e5ab0611664ff`. Native rows: 6065. [Complete output](../reference_outputs/RAN5_P4_CQ4-3/c555702c57e6e28d25477da9232edaaa2639f035eb84a934f1a84f452e7b1ae5.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ4-3/c555702c57e6e28d25477da9232edaaa2639f035eb84a934f1a84f452e7b1ae5.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
```


## RAN5_P4_CQ4-4

Original English (unchanged): Which other specs do Samsung's CRs affect? (company cross-spec impact)

Repair: `query_and_scorer`. Required fields: `[{"name":"spec","nullable":false,"source_column_or_expression":"spec","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"Which other specs is an uncapped set request; remove old LIMIT10 and include every declared affected spec number. No added primary-spec exclusion hides source declarations.","mode":"all"}`.

Repair SHA: `bba5dbb3aae3fab1512cda6738b6310c9eb1c77836fca5b3754ffa1397d48664`. Native rows: 12. [Complete output](../reference_outputs/RAN5_P4_CQ4-4/51a8d3afd3f376d54881e6f650586649160715008734b81fd8605c1e1c741487.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ4-4/51a8d3afd3f376d54881e6f650586649160715008734b81fd8605c1e1c741487.json).

Original query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company)
WHERE comp.companyName CONTAINS 'Samsung'
MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec)
RETURN DISTINCT s.specNumber AS spec
```


## RAN5_P4_CQ4-5

Original English (unchanged): List the change summaries of CRs referenced by conclusions at meeting #87 (meeting-level change review).

Repair: `query_and_scorer`. Required fields: `[{"name":"summary","nullable":true,"source_column_or_expression":"summary","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct recorded summary values from CRs referenced by Conclusions at RAN5#87, including declared nulls; no unasked ID or per-CR occurrence requirement","mode":"all"}`.

Repair SHA: `81b4b2c8eacf8ccd11ba901a05072e06a4dde730ae676da9f5fe7d85c2604dd5`. Native rows: 23. [Complete output](../reference_outputs/RAN5_P4_CQ4-5/7937dad1d87e5ffb0d98bf6706354811f85c3cb41ae1c673bb9c54ce17c89b28.jsonl) / [receipt](../reference_outputs/RAN5_P4_CQ4-5/7937dad1d87e5ffb0d98bf6706354811f85c3cb41ae1c673bb9c54ce17c89b28.json).

Original query:
```cypher
MATCH (con:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 87}) WITH con MATCH (con)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (con:Conclusion)-[:MADE_AT]->(:Meeting {canonicalMeetingNumber:'RAN5#87'}), (con)-[:REFERENCES]->(t:CR) RETURN DISTINCT t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary
```


## RAN5_P5_CQ1-1

Original English (unchanged): List all RAN5 technical reports with their status (TR inventory).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"},{"name":"status","nullable":true,"source_column_or_expression":"tr.trStatus","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `91355c2dfc9be2c68356881eeede0690d7653d3285d57111e50b054b4ba6c6eb`. Native rows: 3. [Complete output](../reference_outputs/RAN5_P5_CQ1-1/fc2d937cbb29f65571708e5e41d79ff88f88705d99ea6ab8d2e83a30bb01a813.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ1-1/fc2d937cbb29f65571708e5e41d79ff88f88705d99ea6ab8d2e83a30bb01a813.json).

Original query:
```cypher
MATCH (tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, tr.trStatus ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, tr.trStatus ORDER BY tr.trNumber
```


## RAN5_P5_CQ1-4

Original English (unchanged): List the technical reports marked Completed (finished-study survey).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `068d68319749f5349333ef07687c9e3d6889f4bb356bb788c7cb7286b70494f5`. Native rows: 3. [Complete output](../reference_outputs/RAN5_P5_CQ1-4/060ccbf0750db090ec85893a28e62ba6fb05e0508693f59d4bbb57558a91fed3.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ1-4/060ccbf0750db090ec85893a28e62ba6fb05e0508693f59d4bbb57558a91fed3.json).

Original query:
```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN5_P5_CQ2-1

Original English (unchanged): Which specs did TR 38.903 impact, and how? (study-to-spec impact)

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `6235c448131a9443eb17e2853233207acfe9ecca8612eb786f57bd218c7c219b`. Native rows: 5. [Complete output](../reference_outputs/RAN5_P5_CQ2-1/d781790d97e8496c5464c60ed7370f3ec1fa469b2da95d85c7fe9342c902962d.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ2-1/d781790d97e8496c5464c60ed7370f3ec1fa469b2da95d85c7fe9342c902962d.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
```


## RAN5_P5_CQ2-2

Original English (unchanged): Return the impact types and descriptions for TR 38.905 (impact classification).

Repair: `scorer_only`. Required fields: `[{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"description","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7fe515b5b735f1d57d5e2af9944f2a5576d68d340d63607e8f6af4bfa0736195`. Native rows: 3. [Complete output](../reference_outputs/RAN5_P5_CQ2-2/e540e1c7ab39eafa9aa89b1da8ff70b33ba87a5fd2eb6061316bb2c5fb44cb44.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ2-2/e540e1c7ab39eafa9aa89b1da8ff70b33ba87a5fd2eb6061316bb2c5fb44cb44.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
```


## RAN5_P5_CQ2-3

Original English (unchanged): Which TRs impacted specs by extending sections? (ExtendSection impact filter)

Repair: `query_and_scorer`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `2efb14501f26cfad585169470b3053dd1a6dbad2dfd2f23ed8db9f995ead03f7`. Native rows: 2. [Complete output](../reference_outputs/RAN5_P5_CQ2-3/f9e82a9f70e81bf75de1732d15cf2462feec280b1d9e801d4f0870cfb39ea53a.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ2-3/f9e82a9f70e81bf75de1732d15cf2462feec280b1d9e801d4f0870cfb39ea53a.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(:TRImpact {impactType:'ExtendSection'})-[:IMPACTS_SPEC]->(:Spec) RETURN DISTINCT tr.trNumber AS trNumber
```


## RAN5_P5_CQ2-4

Original English (unchanged): List the study-only TRs marked NoChange (no-spec-change studies).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `feaa99737fb74943d655aee542be4cc996c035be43c380a98a1597ec1a388b84`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P5_CQ2-4/7c3bea509e4967906a5ac8c594e71db002bb942e3681dbb555eda4521b14a782.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ2-4/7c3bea509e4967906a5ac8c594e71db002bb942e3681dbb555eda4521b14a782.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NoChange'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NoChange'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN5_P5_CQ2-5

Original English (unchanged): Which TRs impacted TS 38.521-1, and how? (incoming study impact)

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c032b6a054a479977b1703572c56a131c31a5e814d4668eddabadda83375fe8e`. Native rows: 2. [Complete output](../reference_outputs/RAN5_P5_CQ2-5/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ2-5/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```


## RAN5_P5_CQ3-1

Original English (unchanged): Detail how TR 38.903 impacted each spec (full impact breakdown).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"description","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `af14aea6ae491fa83cad34a4b3294d1b74b46eb88778c2f48fedf12db1309d1d`. Native rows: 5. [Complete output](../reference_outputs/RAN5_P5_CQ3-1/498157cad7ad5f192a4e61fefc39886a3b474d95d43e0495039e54bf0ba8f808.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ3-1/498157cad7ad5f192a4e61fefc39886a3b474d95d43e0495039e54bf0ba8f808.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```


## RAN5_P5_CQ3-2

Original English (unchanged): Detail how TR 38.905 impacted each spec (full impact breakdown).

Repair: `scorer_only`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"description","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `7a3ad39ee9c0f4ddbd0da2034e8c64d87ab0870bf9785003b58e44d148214845`. Native rows: 3. [Complete output](../reference_outputs/RAN5_P5_CQ3-2/c025d077b9c3782ed6216e36655df4e18db0e770de1aed99efd4e40c29412f4b.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ3-2/c025d077b9c3782ed6216e36655df4e18db0e770de1aed99efd4e40c29412f4b.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
```


## RAN5_P5_CQ4-1

Original English (unchanged): List the TRs targeting Rel-19 (release-scoped studies).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `c1835b227287cee4b69c44b355a88111f8e4e45fed99382a41da1cb82371f94d`. Native rows: 2. [Complete output](../reference_outputs/RAN5_P5_CQ4-1/4cf6c1f98f4d3d153b28f4e586e1f4f6a5a97b3df7fca341eea44acefe52dcec.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ4-1/4cf6c1f98f4d3d153b28f4e586e1f4f6a5a97b3df7fca341eea44acefe52dcec.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}) RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
```


## RAN5_P5_CQ4-2

Original English (unchanged): Which TRs impacted TS 38.521-1, with impact type? (spec-impact lookup)

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `be5da0c21ac40f1521682705eeebce8b971d3169d871105f716d61b5c78aac69`. Native rows: 2. [Complete output](../reference_outputs/RAN5_P5_CQ4-2/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ4-2/e9ce26e889f098b7adb7c7e5147dda47894ccddfcd1791e3277fd7f5ac99be98.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```


## RAN5_P5_CQ4-3

Original English (unchanged): Which TRs impacted TS 38.533, with impact type? (spec-impact lookup)

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"},{"name":"impactType","nullable":false,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct required-field records from the explicit frozen-graph population; no unstated cap","mode":"all"}`.

Repair SHA: `fb4228f49ffc979303bc6caaa9660152b006a7ed6e5431caf58a4f7d6497b591`. Native rows: 1. [Complete output](../reference_outputs/RAN5_P5_CQ4-3/2dadcacdf2f7086d982ae7d11e58e6248b6be29d87d91ac2c31dd7e21cf7399a.jsonl) / [receipt](../reference_outputs/RAN5_P5_CQ4-3/2dadcacdf2f7086d982ae7d11e58e6248b6be29d87d91ac2c31dd7e21cf7399a.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.533'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.533'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
```
