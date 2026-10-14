# RAN2: admitted original-question repairs

Two AI reviews are recorded; no human/expert certification is claimed.


## RAN2_P1_CQ1-1

Original English (unchanged): List the TDocs at meeting RAN2#130 linked to Work Item NR_Mob_enh2-Core (mobility-enhancement meeting prep).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `b5f138bf7fe09cf74fef3683fb34048dc897fb7bff04cf43a4a5b2c6770df221`. Native rows: 24. [Complete output](../reference_outputs/RAN2_P1_CQ1-1/c4c93f9687efe94f4421637559038bec1da09edf2426e0620d3f96a12ee27eb4.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-1/c4c93f9687efe94f4421637559038bec1da09edf2426e0620d3f96a12ee27eb4.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN2_P1_CQ1-2

Original English (unchanged): List the TDocs under Agenda Item 6.1.3.1 (NR RRC) at meeting RAN2#132 (RRC agenda scan).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `28c0350c9483ac35ccd8cc9c9576da05470e96de019450efedd1f245f8ea1dcf`. Native rows: 28. [Complete output](../reference_outputs/RAN2_P1_CQ1-2/9d296466ad3857f79a42e8cfa034811d35aae57317b23b2b73fc295f654f9377.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-2/9d296466ad3857f79a42e8cfa034811d35aae57317b23b2b73fc295f654f9377.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '6.1.3.1'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '6.1.3.1'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN2_P1_CQ1-3

Original English (unchanged): List the TDocs submitted by Huawei at meeting RAN2#132 (competitor contribution review).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `f68b3951f2862d1ac520cd713381f46a7642194a6a13a0e3befddc374f852fb3`. Native rows: 148. [Complete output](../reference_outputs/RAN2_P1_CQ1-3/7899a390108eba860101c4696d2c7155e72a5d58588b934d64e1dcf9ce565cca.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-3/7899a390108eba860101c4696d2c7155e72a5d58588b934d64e1dcf9ce565cca.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN2_P1_CQ1-5

Original English (unchanged): List the TDocs approved or agreed at meeting RAN2#131 (meeting outcome review).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `8c5416f2e5decd1a51bb1a38f31d8ed4bc39cf2dec52a528630c631c47184855`. Native rows: 251. [Complete output](../reference_outputs/RAN2_P1_CQ1-5/3e479fdf17dd1f0ad7787a81a5443bcb2577930cc70df6d2fcdf2202b83817d7.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-5/3e479fdf17dd1f0ad7787a81a5443bcb2577930cc70df6d2fcdf2202b83817d7.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN DISTINCT t.tdocNumber, t.title, t.type, t.status
```


## RAN2_P1_CQ1-6

Original English (unchanged): Return the decision status of TDoc R2-2509337 (outcome lookup).

Repair: `scorer_only`. Required fields: `[{"name":"status","nullable":false,"source_column_or_expression":"t.status","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"one requested scalar or fixed-identifier record","mode":"exact","value":1}`.

Repair SHA: `f3e3e7513161920c4f5353405ea755cd0a6bb1a51c1e62be0aa333b5d71ad1cd`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ1-6/b5b873872eb21fa3c1ede5af57a8bb63687fa3372a2751b3e15b2323d3abdb51.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-6/b5b873872eb21fa3c1ede5af57a8bb63687fa3372a2751b3e15b2323d3abdb51.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.status, t.type LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.status, t.type LIMIT 1
```


## RAN2_P1_CQ1-7

Original English (unchanged): Return the intended purpose (the 'For' field) of TDoc R2-2509337 (contribution intent).

Repair: `scorer_only`. Required fields: `[{"name":"t.`for`","nullable":true,"source_column_or_expression":"t.`for`","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `0012575257509d182061276ab54b4e2cc568bc48cbf49edbe356571fdba9695a`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ1-7/4a3249fc8fc257bbe167cfb946543b771ca6907f4b0575408bf6ccb6b120d492.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-7/4a3249fc8fc257bbe167cfb946543b771ca6907f4b0575408bf6ccb6b120d492.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.`for` LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.`for` LIMIT 1
```


## RAN2_P1_CQ1-8

Original English (unchanged): Return the contact person for TDoc R2-2509337 (author follow-up).

Repair: `scorer_only`. Required fields: `[{"name":"c.contactName","nullable":true,"source_column_or_expression":"c.contactName","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `bc5599f094ebe0eefe5deb3f6fef27017f79198e7f7eba3a80e1f7330a7478a6`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ1-8/00ddc8b19d02726a8486fe6f0ba3188f0646bfee2d60098e492962b890bf918b.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-8/00ddc8b19d02726a8486fe6f0ba3188f0646bfee2d60098e492962b890bf918b.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId LIMIT 1
```


## RAN2_P1_CQ1-9

Original English (unchanged): List all agenda items and their descriptions for meeting RAN2#132 (agenda overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"agendaNumber","nullable":true,"source_column_or_expression":"agendaNumber","type":"string"},{"name":"agendaDescription","nullable":true,"source_column_or_expression":"agendaDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all originally requested matching records; no unstated final row cap"}`.

Repair SHA: `9ff7c39f3603172976c94b81adcfca731a65a3abb1a48a53036eb6a1f12ca5c9`. Native rows: 94. [Complete output](../reference_outputs/RAN2_P1_CQ1-9/2ace365eb7a4380632b6cae45ac23ecf98a370e53882cdc1356aaf3b2ef7c4c1.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ1-9/2ace365eb7a4380632b6cae45ac23ecf98a370e53882cdc1356aaf3b2ef7c4c1.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem) WITH DISTINCT a RETURN a.agendaNumber, a.agendaDescription ORDER BY a.agendaNumber ASC LIMIT 50
```

Repaired reference query:
```cypher
MATCH (a:AgendaItem {meetingNumber:'132'}) RETURN DISTINCT a.agendaNumber AS agendaNumber,a.agendaDescription AS agendaDescription
```


## RAN2_P1_CQ2-1

Original English (unchanged): Return the predecessor and successor revisions of TDoc R2-2509478 (revision-lineage tracing).

Repair: `scorer_only`. Required fields: `[{"name":"previousVersion","nullable":true,"source_column_or_expression":"previousVersion","type":"string"},{"name":"nextVersion","nullable":true,"source_column_or_expression":"nextVersion","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `bc14aed4a075affe93d488bae543c4a18c7bbf30a1ca4c57f3c47abe0b409ad4`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ2-1/ef954f50867ffaa5bb93288e1313ebd3e9b909b72cd6db9e2d5ae45a38643809.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ2-1/ef954f50867ffaa5bb93288e1313ebd3e9b909b72cd6db9e2d5ae45a38643809.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509478'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN t.tdocNumber, prev.tdocNumber AS previousVersion, next.tdocNumber AS nextVersion
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509478'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN t.tdocNumber, prev.tdocNumber AS previousVersion, next.tdocNumber AS nextVersion
```


## RAN2_P1_CQ2-4

Original English (unchanged): Which spec does CR R2-2509337 modify (change target)?

Repair: `scorer_only`. Required fields: `[{"name":"s.specNumber","nullable":true,"source_column_or_expression":"s.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `7069f8915bb175a3b9300281e3ef6704f2bbc0fcb4f325d92233ffbe1d9a8a90`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ2-4/143f6bb356c57980fd064837ef16b0a5b3e47bf405c84d48da2bf8e15e1e7147.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ2-4/143f6bb356c57980fd064837ef16b0a5b3e47bf405c84d48da2bf8e15e1e7147.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber, t.title, s.specNumber, s.specVersion LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber, t.title, s.specNumber, s.specVersion LIMIT 1
```


## RAN2_P1_CQ2-5

Original English (unchanged): Return the change category and affected scope of CR R2-2509337 (impact assessment).

Repair: `scorer_only`. Required fields: `[{"name":"t.crCategory","nullable":true,"source_column_or_expression":"t.crCategory","type":"string"},{"name":"t.clausesAffected","nullable":true,"source_column_or_expression":"t.clausesAffected","type":"string"},{"name":"t.affectsUICC","nullable":true,"source_column_or_expression":"t.affectsUICC","type":"boolean"},{"name":"t.affectsME","nullable":true,"source_column_or_expression":"t.affectsME","type":"boolean"},{"name":"t.affectsRAN","nullable":true,"source_column_or_expression":"t.affectsRAN","type":"boolean"},{"name":"t.affectsCN","nullable":true,"source_column_or_expression":"t.affectsCN","type":"boolean"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `8304fff47f8eaf0ffc1cc8bab7ed45af09bdc2500aa6f874936d83e317d9e5e4`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P1_CQ2-5/8c67c6e618b03617e39be94fca1667c811fac20be69463be5d29ab6c0739282a.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ2-5/8c67c6e618b03617e39be94fca1667c811fac20be69463be5d29ab6c0739282a.json).

Original query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.crCategory, t.clausesAffected, t.affectsUICC, t.affectsME, t.affectsRAN, t.affectsCN LIMIT 1
```

Repaired reference query:
```cypher
MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.crCategory, t.clausesAffected, t.affectsUICC, t.affectsME, t.affectsRAN, t.affectsCN LIMIT 1
```


## RAN2_P1_CQ2-7

Original English (unchanged): List the incoming liaison statements at meeting RAN2#132 with their agenda items (incoming-LS triage).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"},{"name":"a.agendaNumber","nullable":true,"source_column_or_expression":"a.agendaNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `bb9b0ea3587fc5f1aa8f40e0715df8d0972fd28e021e20879082ade5fe674bac`. Native rows: 37. [Complete output](../reference_outputs/RAN2_P1_CQ2-7/76a8743ae02d5c62fe0d2c451d4ef53bf529ae964f1a9c8144c498f076adefa2.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ2-7/76a8743ae02d5c62fe0d2c451d4ef53bf529ae964f1a9c8144c498f076adefa2.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:LS)-[:BELONGS_TO]->(a:AgendaItem) WHERE t.direction = 'in' RETURN t.tdocNumber, t.title, a.agendaNumber ORDER BY a.agendaNumber ASC, t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:LS)-[:BELONGS_TO]->(a:AgendaItem) WHERE t.direction = 'in' RETURN DISTINCT t.tdocNumber, t.title, a.agendaNumber
```


## RAN2_P1_CQ3-1

Original English (unchanged): List Ericsson's contributions to Work Item NR_newRAT-Core (competitor positioning).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `b2d293db3b21901f0cfc00f849ec72c10721684d214e034a0b7a213354cc4f31`. Native rows: 3739. [Complete output](../reference_outputs/RAN2_P1_CQ3-1/654b7da2701e8e16761336e9625bc6efb65b70cb0c3d1e9d60ba1c54d30556eb.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ3-1/654b7da2701e8e16761336e9625bc6efb65b70cb0c3d1e9d60ba1c54d30556eb.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(:Company {companyName:'Ericsson'}), (t)-[:RELATED_TO]->(:WorkItem {workItemCode:'NR_newRAT-Core'}) RETURN DISTINCT t.tdocNumber
```


## RAN2_P1_CQ3-2

Original English (unchanged): List all companies' contributions under Agenda Item 8.2.2 (Ambient IoT) at RAN2#130 (A-IoT landscape).

Repair: `query_and_scorer`. Required fields: `[{"name":"c.companyName","nullable":true,"source_column_or_expression":"c.companyName","type":"string"},{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `70bf2bc28c1b26a6f83ee1d130c23fc60c3eb597ab172384d741955e4fd4564b`. Native rows: 65. [Complete output](../reference_outputs/RAN2_P1_CQ3-2/97bb37b5547fa4e897ce7f055514d636de812c3cacb1340b24601ce026030fef.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ3-2/97bb37b5547fa4e897ce7f055514d636de812c3cacb1340b24601ce026030fef.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.2.2'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.2.2'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN DISTINCT c.companyName, t.tdocNumber, t.title, t.status
```


## RAN2_P1_CQ3-3

Original English (unchanged): Count the contributions per company for Work Item NR_newRAT-Core (participation ranking).

Repair: `query_and_scorer`. Required fields: `[{"name":"c.companyName","nullable":true,"source_column_or_expression":"c.companyName","type":"string"},{"name":"contributions","nullable":true,"source_column_or_expression":"contributions","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `777bd1531b208be8eae6254a165697c736a489d50967d0313508a4c2ba3e7ac0`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P1_CQ3-3/03e775241515f721378be7a0b48e702c929071846c7c5f11e95276bb733d5043.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ3-3/03e775241515f721378be7a0b48e702c929071846c7c5f11e95276bb733d5043.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(DISTINCT t) AS contributions
```


## RAN2_P1_CQ3-5

Original English (unchanged): List other companies' TDocs under the same agenda item as R2-2509337 (competing-proposal scan).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `55163701c3296a6e34a1081d93c236f790c2909237af28523131385c4584ea9f`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P1_CQ3-5/27672a872847124245a9ed33fc54ffd4f4f6708c4a6bdbf3908cff85020e7f3d.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ3-5/27672a872847124245a9ed33fc54ffd4f4f6708c4a6bdbf3908cff85020e7f3d.json).

Original query:
```cypher
MATCH (t0:Tdoc {tdocNumber: 'R2-2509337'})-[:BELONGS_TO]->(a:AgendaItem), (t0)-[:PRESENTED_AT]->(m:Meeting) MATCH (m)<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a), (t)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> 'R2-2509337' RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t0:Tdoc {tdocNumber: 'R2-2509337'})-[:BELONGS_TO]->(a:AgendaItem), (t0)-[:PRESENTED_AT]->(m:Meeting) MATCH (m)<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a), (t)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> 'R2-2509337' AND NOT EXISTS { MATCH (t0)-[:SUBMITTED_BY]->(c) } RETURN DISTINCT c.companyName, t.tdocNumber, t.title, t.status
```


## RAN2_P1_CQ3-6

Original English (unchanged): Return Nokia's contribution distribution across work items (focus-area profiling).

Repair: `query_and_scorer`. Required fields: `[{"name":"wi.workItemCode","nullable":true,"source_column_or_expression":"wi.workItemCode","type":"string"},{"name":"contributions","nullable":true,"source_column_or_expression":"contributions","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `32406166caa9f0885ac91d54a0d182d412074e0a30cf148b03f551b610246b07`. Native rows: 306. [Complete output](../reference_outputs/RAN2_P1_CQ3-6/fdcb7dbfbccbb10270766e76bc51d874f6cf7edbdf99ee1433743ff18956cc6b.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ3-6/fdcb7dbfbccbb10270766e76bc51d874f6cf7edbdf99ee1433743ff18956cc6b.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Nokia'}), (t)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Nokia'}), (t)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(DISTINCT t) AS contributions
```


## RAN2_P1_CQ4-2

Original English (unchanged): Summarize the outcomes of Samsung's contributions at RAN2#132 (meeting result summary).

Repair: `scorer_only`. Required fields: `[{"name":"t.status","nullable":true,"source_column_or_expression":"t.status","type":"string"},{"name":"count","nullable":false,"source_column_or_expression":"count","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `62409f5bef5218dc6184fd219945dfd58ed83a6bdde256009eabab0383f205d3`. Native rows: 10. [Complete output](../reference_outputs/RAN2_P1_CQ4-2/33c1eb2212897e2d8a81ff78a4ceed89f9a0d12d878de22977b51e1a2b52f1c9.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ4-2/33c1eb2212897e2d8a81ff78a4ceed89f9a0d12d878de22977b51e1a2b52f1c9.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.status, count(t) AS count ORDER BY count DESC
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.status, count(t) AS count ORDER BY count DESC
```


## RAN2_P1_CQ4-3

Original English (unchanged): List the not-treated TDocs under Agenda Item 11.4.2 at RAN2#107 (pending-item backlog).

Repair: `query_and_scorer`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `4e53faef485dc524253fe39c347a1f217770982fbfd85168f8d4533f137b2723`. Native rows: 100. [Complete output](../reference_outputs/RAN2_P1_CQ4-3/95bdbd5fb920dd585d529da16b917abdf314850cac59cdaa42cd5602ed2959e0.jsonl) / [receipt](../reference_outputs/RAN2_P1_CQ4-3/95bdbd5fb920dd585d529da16b917abdf314850cac59cdaa42cd5602ed2959e0.json).

Original query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#107'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '11.4.2'}) WHERE t.status = 'not treated' RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#107'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '11.4.2'}) WHERE t.status = 'not treated' RETURN DISTINCT t.tdocNumber, t.title, t.type
```


## RAN2_P2_CQ1-1

Original English (unchanged): List the agreements reached at meeting RAN2#117 (decision review).

Repair: `query_and_scorer`. Required fields: `[{"name":"a.resolutionId","nullable":true,"source_column_or_expression":"a.resolutionId","type":"string"},{"name":"a.content","nullable":true,"source_column_or_expression":"a.content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `4b814fd15ada7ea02315749f18f704e59071376d334af219abd54bc62950a07f`. Native rows: 96. [Complete output](../reference_outputs/RAN2_P2_CQ1-1/b16a1950642e3d9cab388488076ad488a286a85d33e90969537345de7c700894.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-1/b16a1950642e3d9cab388488076ad488a286a85d33e90969537345de7c700894.json).

Original query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#117'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN a.resolutionId, a.content, ai.agendaNumber ORDER BY ai.agendaNumber, a.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#117'}) OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) RETURN DISTINCT a.resolutionId, a.content, ai.agendaNumber
```


## RAN2_P2_CQ1-10

Original English (unchanged): Return resolution counts by type at meeting RAN2#132 (meeting decision mix).

Repair: `scorer_only`. Required fields: `[{"name":"type","nullable":false,"source_column_or_expression":"type","type":"string"},{"name":"cnt","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `69425aefb3853db524b139051c8b7453f483446c0c5ddfd76c9096aaef71a672`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P2_CQ1-10/eb5e7f756149b585ecb20ddc51547b4dd75830ae661abc8b0aa89cfe3c8a486e.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-10/eb5e7f756149b585ecb20ddc51547b4dd75830ae661abc8b0aa89cfe3c8a486e.json).

Original query:
```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' END AS type, count(r) AS cnt ORDER BY cnt DESC
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' END AS type, count(r) AS cnt ORDER BY cnt DESC
```


## RAN2_P2_CQ1-2

Original English (unchanged): List the conclusions drawn at meeting RAN2#121 (study-outcome review).

Repair: `scorer_only`. Required fields: `[{"name":"c.resolutionId","nullable":true,"source_column_or_expression":"c.resolutionId","type":"string"},{"name":"c.content","nullable":true,"source_column_or_expression":"c.content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `feedbbeafab7be73068e80eb043e59f81c15333fde9fe5ada8898bc55f0f4c27`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P2_CQ1-2/3c6c513148f325ada01fd3867710ec356162f825cd61def79b9b4aafe18b36a1.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-2/3c6c513148f325ada01fd3867710ec356162f825cd61def79b9b4aafe18b36a1.json).

Original query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#121'}) RETURN c.resolutionId, c.content, c.hasConsensus ORDER BY c.sequence LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#121'}) RETURN c.resolutionId, c.content, c.hasConsensus ORDER BY c.sequence LIMIT 10
```


## RAN2_P2_CQ1-3

Original English (unchanged): List the working assumptions from meeting RAN2#115 (provisional-decision review).

Repair: `scorer_only`. Required fields: `[{"name":"wa.resolutionId","nullable":true,"source_column_or_expression":"wa.resolutionId","type":"string"},{"name":"wa.content","nullable":true,"source_column_or_expression":"wa.content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `9923a5fda457722b54024b86c7157521b7f6d37189a3227da911ca00d57b5f4a`. Native rows: 11. [Complete output](../reference_outputs/RAN2_P2_CQ1-3/1c4ec02fe337d105e6e9bc4ac285221360767ce1f97dc015da6dfe6b58b509c2.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-3/1c4ec02fe337d105e6e9bc4ac285221360767ce1f97dc015da6dfe6b58b509c2.json).

Original query:
```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15
```


## RAN2_P2_CQ1-4

Original English (unchanged): List the resolutions under Agenda Item 8.11 at RAN2#117 (agenda decision trace).

Repair: `query_and_scorer`. Required fields: `[{"name":"r.resolutionId","nullable":true,"source_column_or_expression":"r.resolutionId","type":"string"},{"name":"r.content","nullable":true,"source_column_or_expression":"r.content","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `445a9eb2dd4932ca8a92966facd4b854caf5bf5d7ea42b637b70dc777c4dd937`. Native rows: 35. [Complete output](../reference_outputs/RAN2_P2_CQ1-4/2db272fb1af4b107b1448421683f1e92e1cc96898e9a03e9306b71e37b637734.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-4/2db272fb1af4b107b1448421683f1e92e1cc96898e9a03e9306b71e37b637734.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE (ai.agendaNumber = '8.11' OR ai.agendaNumber STARTS WITH '8.11.') AND ai.meetingNumber = '117' MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS type, r.content ORDER BY r.sequence LIMIT 15
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE (ai.agendaNumber = '8.11' OR ai.agendaNumber STARTS WITH '8.11.') AND ai.meetingNumber = '117' MATCH (r)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber:'RAN2#117'}) RETURN DISTINCT r.resolutionId, labels(r) AS type, r.content
```


## RAN2_P2_CQ1-5

Original English (unchanged): List the resolutions related to Rel-18 (release decision review).

Repair: `query_and_scorer`. Required fields: `[{"name":"resolutionId","nullable":false,"source_column_or_expression":"resolutionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all"}`.

Repair SHA: `9ea365bcd32b3b3fabb8bf3e2d05469043208b5a21169655dca9ec7902971b44`. Native rows: 306. [Complete output](../reference_outputs/RAN2_P2_CQ1-5/dfa507cf07e7eb4dc53731d442c8aa2d013817f4e9932a6a72d72cb2d41cdaea.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-5/dfa507cf07e7eb4dc53731d442c8aa2d013817f4e9932a6a72d72cb2d41cdaea.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, r.content ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'})
RETURN DISTINCT r.resolutionId AS resolutionId, r.content AS content
```


## RAN2_P2_CQ1-8

Original English (unchanged): Return the top 10 agenda items by resolution count (hot-topic ranking).

Repair: `scorer_only`. Required fields: `[{"name":"ai.agendaNumber","nullable":true,"source_column_or_expression":"ai.agendaNumber","type":"string"},{"name":"ai.meetingNumber","nullable":true,"source_column_or_expression":"ai.meetingNumber","type":"string"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"desc","source_column":"resolutionCount"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"top_k","notes":"Exactly min(10, complete eligible stored grouping population), using every declared order key.","short_population":"all_available","tie_policy":"exact_k","value":10}`.

Repair SHA: `6d9f979ba91681e78e8a2ed4942cdc3c116e2f8d1ed9a4a6e782dbfa9b355c1a`. Native rows: 10. [Complete output](../reference_outputs/RAN2_P2_CQ1-8/b25147e9eab06fabba8b214600143828164d8953fe2dd57da620cd0d0c019b95.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ1-8/b25147e9eab06fabba8b214600143828164d8953fe2dd57da620cd0d0c019b95.json).

Original query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber <> 'UNKNOWN' RETURN ai.agendaNumber, ai.meetingNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC, ai.agendaNumber, ai.meetingNumber LIMIT 10
```

Repaired reference query:
```cypher
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber <> 'UNKNOWN' RETURN ai.agendaNumber, ai.meetingNumber, count(r) AS resolutionCount ORDER BY resolutionCount DESC, ai.agendaNumber, ai.meetingNumber LIMIT 10
```


## RAN2_P2_CQ2-2

Original English (unchanged): List the TDocs referenced by Agreement AGR-132-8.13-005 (decision provenance).

Repair: `scorer_only`. Required fields: `[{"name":"t.tdocNumber","nullable":true,"source_column_or_expression":"t.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `98a1f7e9c6a935a4baa7d80900f48f4a3db0e418ca3b787345408e9ad72d5e3d`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P2_CQ2-2/d92f1ac2de37d34582ed8cf567fa24c8418d8460433b6a9b789eee2e4b912b56.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ2-2/d92f1ac2de37d34582ed8cf567fa24c8418d8460433b6a9b789eee2e4b912b56.json).

Original query:
```cypher
MATCH (a:Agreement {resolutionId: 'AGR-132-8.13-005'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```

Repaired reference query:
```cypher
MATCH (a:Agreement {resolutionId: 'AGR-132-8.13-005'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title
```


## RAN2_P2_CQ3-5

Original English (unchanged): Rank the top 10 companies by resolution-referenced TDocs (overall influence).

Repair: `query_and_scorer`. Required fields: `[{"name":"companyName","nullable":false,"source_column_or_expression":"companyName","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":true,"source_order_keys":[{"direction":"desc","source_column":"tdocCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `7f8cf67c446c2fbc3d1392fa5330b82a417438874f47b7adf5fe20cb055bc63b`. Native rows: 277. [Complete output](../reference_outputs/RAN2_P2_CQ3-5/3dd35ba5dcf21e6418e2044406f332509aa92be9712363976bbeff4a83f74049.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ3-5/3dd35ba5dcf21e6418e2044406f332509aa92be9712363976bbeff4a83f74049.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (r)-[:MADE_AT]->(m:Meeting) RETURN c.companyName, count(DISTINCT r) AS resolutionCount ORDER BY resolutionCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:Company) OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c) RETURN c.companyName AS companyName,count(DISTINCT t) AS tdocCount ORDER BY tdocCount DESC
```


## RAN2_P2_CQ6-1

Original English (unchanged): Return the trend of Rel-18 resolution counts over meetings (chronological trend).

Repair: `query_and_scorer`. Required fields: `[{"name":"meetingNumber","nullable":true,"source_column_or_expression":"meetingNumber","type":"string"},{"name":"resCount","nullable":false,"source_column_or_expression":"resCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"asc","source_column":"meetingNumberInt"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `d3b21c3a9e7d8111d6332f0048818a3fa9b3b792e4871e7e00bbbfb7c85034d6`. Native rows: 58. [Complete output](../reference_outputs/RAN2_P2_CQ6-1/640513c5b8f045eb27fb2177d7802709c2c9e37eab7d881cae8dbd1013b2ee2a.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ6-1/640513c5b8f045eb27fb2177d7802709c2c9e37eab7d881cae8dbd1013b2ee2a.json).

Original query:
```cypher
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(r) AS resCount ORDER BY m.meetingNumberInt ASC
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m), (r)-[:REFERENCES]->(:Tdoc)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS resCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```


## RAN2_P2_CQ6-3

Original English (unchanged): Return the trend of agreement counts per meeting (activity trend).

Repair: `query_and_scorer`. Required fields: `[{"name":"meetingNumber","nullable":true,"source_column_or_expression":"meetingNumber","type":"string"},{"name":"agrCount","nullable":false,"source_column_or_expression":"agrCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"asc","source_column":"meetingNumberInt"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `a063bd427c30d25b7f6193d5c0395460ebf4bd7bc73ca0479319cd1a420f6bf0`. Native rows: 58. [Complete output](../reference_outputs/RAN2_P2_CQ6-3/ebe1fd9067e1e81ae00fb4d8ce6608d7f23759d10f24cfc5eceadb2ac27509b8.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ6-3/ebe1fd9067e1e81ae00fb4d8ce6608d7f23759d10f24cfc5eceadb2ac27509b8.json).

Original query:
```cypher
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(a) AS agrCount ORDER BY m.meetingNumberInt ASC
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Agreement)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS agrCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```


## RAN2_P2_CQ6-4

Original English (unchanged): Return the trend of conclusion counts per meeting (study-closure trend).

Repair: `query_and_scorer`. Required fields: `[{"name":"meetingNumber","nullable":true,"source_column_or_expression":"meetingNumber","type":"string"},{"name":"conCount","nullable":false,"source_column_or_expression":"conCount","type":"integer"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"asc","source_column":"meetingNumberInt"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `ffe2a660e865c17c5641d55b8481099c656471ce0c6ddaf7c9e6c923e96661aa`. Native rows: 58. [Complete output](../reference_outputs/RAN2_P2_CQ6-4/3e3f0ff94505e31ff0724cbac72268da055a3b8c71df7e6be12379fac6a7d2d6.jsonl) / [receipt](../reference_outputs/RAN2_P2_CQ6-4/3e3f0ff94505e31ff0724cbac72268da055a3b8c71df7e6be12379fac6a7d2d6.json).

Original query:
```cypher
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(c) AS conCount ORDER BY m.meetingNumberInt ASC
```

Repaired reference query:
```cypher
MATCH (m:Meeting) OPTIONAL MATCH (r:Conclusion)-[:MADE_AT]->(m) RETURN m.canonicalMeetingNumber AS meetingNumber,m.meetingNumberInt AS meetingNumberInt,count(DISTINCT r) AS conCount ORDER BY meetingNumberInt ASC,meetingNumber ASC
```


## RAN2_P3_CQ1-1

Original English (unchanged): List all sections of spec 38.331 (RRC structure overview).

Repair: `query_and_scorer`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `3af8a6ac4829ff40bdbb2b96e843c27889e8ee6d5d0ebe9226b83c3484a5136b`. Native rows: 5834. [Complete output](../reference_outputs/RAN2_P3_CQ1-1/641a4394bfedc94a6240aa57a8dd6059f46c82bcc437e485e4e9396f64afbf33.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-1/641a4394bfedc94a6240aa57a8dd6059f46c82bcc437e485e4e9396f64afbf33.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle, s.level ORDER BY s.sectionNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT s.sectionId, s.sectionNumber, s.sectionTitle, s.level
```


## RAN2_P3_CQ1-10

Original English (unchanged): Find the spec and section that hold Table 6.3.3-1 (reverse table lookup).

Repair: `scorer_only`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"},{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `bbe8ae3f23b86c49b031e3f0018cabc18e3ea95aa2744f3f0da4030ff09c3066`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P3_CQ1-10/245e7c99de1a1d21ace12604fbcbc710ac12a38a5b918462cb0f4f4e420dcffa.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-10/245e7c99de1a1d21ace12604fbcbc710ac12a38a5b918462cb0f4f4e420dcffa.json).

Original query:
```cypher
MATCH (t:TSTable {tableNumber: '6.3.3-1'})-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, s.sectionId, t.tableId
```

Repaired reference query:
```cypher
MATCH (t:TSTable {tableNumber: '6.3.3-1'})-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, s.sectionId, t.tableId
```


## RAN2_P3_CQ1-11

Original English (unchanged): Return the top 5 specs by section count (largest specs).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"sectionCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `8cfbab9aebb99a1f24333b1e3fce46922366dc7825cfb891776ff37e90f75470`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ1-11/580fb7a5e382d893702426a273a31be0a57e6ac8931b25438faff244d505ae67.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-11/580fb7a5e382d893702426a273a31be0a57e6ac8931b25438faff244d505ae67.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(s) AS sectionCount ORDER BY sectionCount DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:specNumber}) RETURN specNumber,count(DISTINCT s) AS sectionCount ORDER BY sectionCount DESC
```


## RAN2_P3_CQ1-12

Original English (unchanged): Return the section-level distribution of spec 38.331 (structural depth profile).

Repair: `scorer_only`. Required fields: `[{"name":"s.level","nullable":true,"source_column_or_expression":"s.level","type":"integer"},{"name":"cnt","nullable":true,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `6287d4629428b6fc619443ad6aa909857a06f7b68c28a4f52032734b0c3f0b84`. Native rows: 7. [Complete output](../reference_outputs/RAN2_P3_CQ1-12/125c34e5cef46ea001b1a24129c45c16c7daa43d63560abeb1c7384737eb23f9.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-12/125c34e5cef46ea001b1a24129c45c16c7daa43d63560abeb1c7384737eb23f9.json).

Original query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN s.level, count(s) AS cnt ORDER BY s.level
```


## RAN2_P3_CQ1-13

Original English (unchanged): List the sections marked Void (placeholder scan).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":true,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all originally requested matching records; no unstated final row cap"}`.

Repair SHA: `bf37a85bdf6e2b3a63e8c72caac80bfce6c67233f40ec22b3bfbce21d1c56b2d`. Native rows: 172. [Complete output](../reference_outputs/RAN2_P3_CQ1-13/f4b5052e133109c5d7a7e25720a7c6cd59f765ae7effd2a69be5bd574ce165f4.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-13/f4b5052e133109c5d7a7e25720a7c6cd59f765ae7effd2a69be5bd574ce165f4.json).

Original query:
```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'Void' OR s.sectionTitle CONTAINS 'void' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 15
```

Repaired reference query:
```cypher
MATCH (s:Section) WHERE s.isVoid=true RETURN DISTINCT s.sectionId AS sectionId
```


## RAN2_P3_CQ1-14

Original English (unchanged): Return the total counts of sections, tables, and figures (corpus size).

Repair: `scorer_only`. Required fields: `[{"name":"secCnt","nullable":false,"source_column_or_expression":"secCnt","type":"integer"},{"name":"tblCnt","nullable":false,"source_column_or_expression":"tblCnt","type":"integer"},{"name":"figCnt","nullable":false,"source_column_or_expression":"figCnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","notes":"one aggregate row","value":1}`.

Repair SHA: `4f9f7215757a679f98c7a92f01334ffc2474f3f5ea97473b3b48aa4a2913f0f3`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_CQ1-14/b880148e4cb276f0c54cd366e7f4f1d916f1afe941123eaa72b64efe7ceb73c2.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-14/b880148e4cb276f0c54cd366e7f4f1d916f1afe941123eaa72b64efe7ceb73c2.json).

Original query:
```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```

Repaired reference query:
```cypher
MATCH (s:Section) WITH count(s) AS secCnt MATCH (t:TSTable) WITH secCnt, count(t) AS tblCnt MATCH (f:TSFigure) WITH secCnt, tblCnt, count(f) AS figCnt RETURN secCnt, tblCnt, figCnt
```


## RAN2_P3_CQ1-15

Original English (unchanged): Return the top 5 sections by table count (table-dense sections).

Repair: `scorer_only`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"desc","source_column":"tableCount"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"top_k","notes":"top five Section-identifier groups or all when fewer exist","tie_policy":"Section identifier ascending","value":5}`.

Repair SHA: `f3ed200480870c3e83d55fb32180ac58e4a3aa79c942f4ae5fcfa2df29a032e5`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P3_CQ1-15/9dc0a4d6757f8c7bd2a7525200660bf3172c0e0a010fb4cd513cbbb0e2566807.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-15/9dc0a4d6757f8c7bd2a7525200660bf3172c0e0a010fb4cd513cbbb0e2566807.json).

Original query:
```cypher
MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId, count(t) AS tableCount ORDER BY tableCount DESC, s.sectionId LIMIT 5
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:CONTAINS_TABLE]->(t:TSTable) RETURN s.sectionId, count(t) AS tableCount ORDER BY tableCount DESC, s.sectionId LIMIT 5
```


## RAN2_P3_CQ1-16

Original English (unchanged): Return the top 5 sections by figure count (figure-dense sections).

Repair: `scorer_only`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"desc","source_column":"figCount"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"top_k","notes":"top five Section-identifier groups or all when fewer exist","tie_policy":"Section identifier ascending","value":5}`.

Repair SHA: `5bde1ae9a19d3d5f62ebbc694eabe147af44aa16809ef40a2040dfb65c5ad7d2`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P3_CQ1-16/f61d4704c34334159e72d476dbb5eb4fc7df9c39d4e1bdde91ec998bca91b8fd.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-16/f61d4704c34334159e72d476dbb5eb4fc7df9c39d4e1bdde91ec998bca91b8fd.json).

Original query:
```cypher
MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId, count(f) AS figCount ORDER BY figCount DESC, s.sectionId LIMIT 5
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:CONTAINS_FIGURE]->(f:TSFigure) RETURN s.sectionId, count(f) AS figCount ORDER BY figCount DESC, s.sectionId LIMIT 5
```


## RAN2_P3_CQ1-4

Original English (unchanged): List the level-1 sections of spec 38.321 (top-level MAC outline).

Repair: `scorer_only`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `668aa2685d58ade51364adc617508cc83a0fca6b2893223e2e23ba2d61983ef0`. Native rows: 40. [Complete output](../reference_outputs/RAN2_P3_CQ1-4/5a5d37c303f25f051bb9997409a52b42619f0604fb2ead67b80dae8796486433.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-4/5a5d37c303f25f051bb9997409a52b42619f0604fb2ead67b80dae8796486433.json).

Original query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```

Repaired reference query:
```cypher
MATCH (s:Section {level: 1})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}) RETURN s.sectionId, s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber
```


## RAN2_P3_CQ1-7

Original English (unchanged): Which section contains Table 5.1-1 (table location)?

Repair: `scorer_only`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `c5a2b0b6911baa1d9120a2f9b44c6d8fb52dae5a177058c7dee88a640966c354`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P3_CQ1-7/8907578befc6ee80745a2266b5225b2fdbd582f35334b75d4213edb88fc198c3.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-7/8907578befc6ee80745a2266b5225b2fdbd582f35334b75d4213edb88fc198c3.json).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section) WHERE t.tableNumber = '5.1-1' RETURN t.tableId, s.sectionId, s.sectionTitle
```

Repaired reference query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section) WHERE t.tableNumber = '5.1-1' RETURN t.tableId, s.sectionId, s.sectionTitle
```


## RAN2_P3_CQ1-8

Original English (unchanged): List all tables in spec 38.331 (table inventory).

Repair: `scorer_only`. Required fields: `[{"name":"t.tableId","nullable":true,"source_column_or_expression":"t.tableId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `3a35fd2a0a5fb234393c4c8680a29e450ee6ba54111c26ffa17d4509e2643262`. Native rows: 24. [Complete output](../reference_outputs/RAN2_P3_CQ1-8/11aea91947f5a88a20f2a6ef48072d57769af71783fbf044b17226f9ac763605.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-8/11aea91947f5a88a20f2a6ef48072d57769af71783fbf044b17226f9ac763605.json).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```

Repaired reference query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25
```


## RAN2_P3_CQ1-9

Original English (unchanged): List the sections whose title contains 'MAC' (topic search).

Repair: `query_and_scorer`. Required fields: `[{"name":"s.sectionId","nullable":true,"source_column_or_expression":"s.sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `f73dfbc1099a9b1cb53d1f879fae833b889d1790da9b979a8f1348e1192babc8`. Native rows: 484. [Complete output](../reference_outputs/RAN2_P3_CQ1-9/4a7fdc5e7e8ff4edec601e8f19df8a418b0cbe3315b87af2990ac9d08459c1ce.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ1-9/4a7fdc5e7e8ff4edec601e8f19df8a418b0cbe3315b87af2990ac9d08459c1ce.json).

Original query:
```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'MAC' RETURN s.sectionId, s.sectionTitle ORDER BY s.sectionId LIMIT 25
```

Repaired reference query:
```cypher
MATCH (s:Section) WHERE s.sectionTitle CONTAINS 'MAC' RETURN DISTINCT s.sectionId, s.sectionTitle
```


## RAN2_P3_CQ2-3

Original English (unchanged): Which sections of spec 38.321 make the most references (reference hub)?

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":true,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `a5ff3234169934d2fbf301dca7d35a5f2a736d468acc85bef4737dabb031e394`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_CQ2-3/6d10a6ae26655664c5f908eae751046d54dad3647a1e49a5f4012e7fdda48da6.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-3/6d10a6ae26655664c5f908eae751046d54dad3647a1e49a5f4012e7fdda48da6.json).

Original query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}), (s1)-[:REFERENCES_SECTION]->(s2:Section) RETURN s2.sectionId, count(*) AS refs ORDER BY refs DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.321'}) WITH DISTINCT s OPTIONAL MATCH (s)-[:REFERENCES_SECTION]->(target:Section) WITH s,count(DISTINCT target) AS refs WITH collect({id:s.sectionId,n:refs}) AS groups,max(refs) AS maximum UNWIND groups AS g WITH g,maximum WHERE g.n=maximum RETURN g.id AS sectionId,g.n AS refs
```


## RAN2_P3_CQ2-4

Original English (unchanged): Return the top 10 most-referenced sections (central sections).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":false,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"refCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `b41b673e1ce0b4f53310b116f74ac3b091bf9f412bfd12b9e1a1c92c117f05b7`. Native rows: 14397. [Complete output](../reference_outputs/RAN2_P3_CQ2-4/f8ea810225854adc3223ed31e13d86894b9716f006db0920213ea793ae2ed739.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-4/f8ea810225854adc3223ed31e13d86894b9716f006db0920213ea793ae2ed739.json).

Original query:
```cypher
MATCH (ref:Section)-[:REFERENCES_SECTION]->(s:Section) RETURN s.sectionId, s.sectionTitle, count(ref) AS refCount ORDER BY refCount DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Section) OPTIONAL MATCH (ref:Section)-[:REFERENCES_SECTION]->(s) RETURN s.sectionId AS sectionId,count(DISTINCT ref) AS refCount ORDER BY refCount DESC
```


## RAN2_P3_CQ2-5

Original English (unchanged): Return the cross-spec references from spec 38.300 into spec 38.331 (inter-spec dependency).

Repair: `scorer_only`. Required fields: `[{"name":"from_section","nullable":true,"source_column_or_expression":"from_section","type":"string"},{"name":"to_section","nullable":true,"source_column_or_expression":"to_section","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `2fe8ede8b1a916efd6e46fa45ff72f92e0ade7f5f4ec5f6c73a6d1ed3f04bf64`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P3_CQ2-5/087227fd83a33ad12ecdd3d3ae2bfead1bd5bfb1e539ff5c14fb6cc6b631a3e4.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-5/087227fd83a33ad12ecdd3d3ae2bfead1bd5bfb1e539ff5c14fb6cc6b631a3e4.json).

Original query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec {specNumber: '38.300'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: '38.331'}) RETURN s1.sectionId AS from_section, s2.sectionId AS to_section LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp1:Spec {specNumber: '38.300'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: '38.331'}) RETURN s1.sectionId AS from_section, s2.sectionId AS to_section LIMIT 10
```


## RAN2_P3_CQ2-6

Original English (unchanged): Return the total number of section-to-section references (cross-reference volume).

Repair: `scorer_only`. Required fields: `[{"name":"totalRefs","nullable":false,"source_column_or_expression":"totalRefs","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","notes":"one aggregate row","value":1}`.

Repair SHA: `94ed8b2af9df90ba7cf6ca9152dcfecfc2365ce209bd4de75efa35531fe2636e`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_CQ2-6/269aebd1de286baddc2762d15ec7eba4111d4731192f36c8b3fd99641da5bcf2.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-6/269aebd1de286baddc2762d15ec7eba4111d4731192f36c8b3fd99641da5bcf2.json).

Original query:
```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```

Repaired reference query:
```cypher
MATCH ()-[:REFERENCES_SECTION]->() RETURN count(*) AS totalRefs
```


## RAN2_P3_CQ2-7

Original English (unchanged): Return the top 5 specs by intra-spec reference count (internal cohesion).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"intraRefs"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `43ebd6c6d66c1ede4f8d71bd2ae69778ffe12d9c2a3e17a200559214a8ed3d4e`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ2-7/7c2783d257e07d12a83e53fdfd9f511ff949d0f3375391f5ec110efa2572c75e.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-7/7c2783d257e07d12a83e53fdfd9f511ff949d0f3375391f5ec110efa2572c75e.json).

Original query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber, count(*) AS intraRefs ORDER BY intraRefs DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp0:Spec) WITH DISTINCT sp0.specNumber AS specNumber OPTIONAL MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:specNumber}), (s1)-[ref:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN specNumber,count(DISTINCT ref) AS intraRefs ORDER BY intraRefs DESC
```


## RAN2_P3_CQ2-8

Original English (unchanged): Return the top 5 most-referenced sections within spec 38.331 (internal hubs).

Repair: `scorer_only`. Required fields: `[{"name":"s2.sectionId","nullable":true,"source_column_or_expression":"s2.sectionId","type":"string"}]`.

Collection: `{"kind":"native_ordered_ties","source_order_keys":[{"direction":"desc","source_column":"refCount"}],"tie_policy":"any_order_within_equal_keys"}`. Cardinality: `{"mode":"top_k","notes":"top five target Section-identifier groups or all when fewer exist","tie_policy":"target Section identifier ascending","value":5}`.

Repair SHA: `4cf6c7fef9ffabf5602010b157ef31a5cbf2ae66aad52a739897dc30a71cbd65`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P3_CQ2-8/011ae8ffd63cb74e6f460c148ebfe3b16bf87ab4e8a8453e5a8c3359bd416a50.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ2-8/011ae8ffd63cb74e6f460c148ebfe3b16bf87ab4e8a8453e5a8c3359bd416a50.json).

Original query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId, s2.sectionTitle, count(*) AS refCount ORDER BY refCount DESC, s2.sectionId LIMIT 5
```

Repaired reference query:
```cypher
MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN s2.sectionId, s2.sectionTitle, count(*) AS refCount ORDER BY refCount DESC, s2.sectionId LIMIT 5
```


## RAN2_P3_CQ3-1

Original English (unchanged): Which spec does CR R2-2509337 modify (change target)?

Repair: `scorer_only`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `77c07e033b46cbad7894f2f627ae414d2269033858d99bf9adab12a02095802d`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_CQ3-1/3bf4d864e660da6e9f59fbf84dcf05372e0c5ba4e279dda47ecfec7d80e4fc79.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-1/3bf4d864e660da6e9f59fbf84dcf05372e0c5ba4e279dda47ecfec7d80e4fc79.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.tdocNumber = 'R2-2509337' RETURN sp.specNumber
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.tdocNumber = 'R2-2509337' RETURN sp.specNumber
```


## RAN2_P3_CQ3-3

Original English (unchanged): List the CRs that modify spec 38.331 (change history).

Repair: `query_and_scorer`. Required fields: `[{"name":"cr.tdocNumber","nullable":true,"source_column_or_expression":"cr.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `102f6da6ec74693e1dc2067e575848ebde0db326f565555a19beed9e297e6405`. Native rows: 10599. [Complete output](../reference_outputs/RAN2_P3_CQ3-3/686f1507efd22ae20be473ddd719dc535470a38ed58335ba3072683c6b2d0ca5.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-3/686f1507efd22ae20be473ddd719dc535470a38ed58335ba3072683c6b2d0ca5.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN cr.tdocNumber, cr.title, cr.status ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN DISTINCT cr.tdocNumber, cr.title, cr.status
```


## RAN2_P3_CQ3-4

Original English (unchanged): List the CRs that specify affected clauses (clause-tagged CRs).

Repair: `query_and_scorer`. Required fields: `[{"name":"cr.tdocNumber","nullable":true,"source_column_or_expression":"cr.tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `143d2fab8a4901a61ab68ee05ae29e35931cfac343016200c4b1606c2b63b7ed`. Native rows: 3855. [Complete output](../reference_outputs/RAN2_P3_CQ3-4/318fe07d10e7c1220993e0b8b849d1986e40337becbf3d82399040c4c0e23f6b.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-4/318fe07d10e7c1220993e0b8b849d1986e40337becbf3d82399040c4c0e23f6b.json).

Original query:
```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN DISTINCT cr.tdocNumber, cr.clausesAffected, cr.crCategory
```


## RAN2_P3_CQ3-5

Original English (unchanged): Which specs do CRs for Work Item NR_newRAT-Core modify (work-item impact)?

Repair: `query_and_scorer`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `ecf8c6976a88249a7007605a133a7dc3c99b1fea834d39141cde8e40e6a083a5`. Native rows: 23. [Complete output](../reference_outputs/RAN2_P3_CQ3-5/ea4d0119373b60952352587a9a7c5cb1b5f4f6a60f881f7c2b68aa6e14971298.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-5/ea4d0119373b60952352587a9a7c5cb1b5f4f6a60f881f7c2b68aa6e14971298.json).

Original query:
```cypher
MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (t:CR)-[:RELATED_TO]->(:WorkItem {workItemCode:'NR_newRAT-Core'}), (t)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber
```


## RAN2_P3_CQ3-6

Original English (unchanged): List the specs modified by Huawei's CRs (vendor footprint).

Repair: `query_and_scorer`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `970c102b59993154860a4199acabb842ef76b1258a19cd55c07a0946b43fe9d7`. Native rows: 53. [Complete output](../reference_outputs/RAN2_P3_CQ3-6/44bd2f8ad0caba070bec893b25f9718dda452cdc8633a44da753e9d2b6f6adb5.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-6/44bd2f8ad0caba070bec893b25f9718dda452cdc8633a44da753e9d2b6f6adb5.json).

Original query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:SUBMITTED_BY]->(:Company {companyName:'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber
```


## RAN2_P3_CQ3-8

Original English (unchanged): Return the top 5 specs by Rel-18 CR count (release change footprint).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `452522bb1e4670af61861b82bf225d132c272f51711b63cfaddbb50890d87757`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ3-8/594c56d6b47dd8e9ff869c252e479f9839add550ab6d374290959e4c7278b6a7.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ3-8/594c56d6b47dd8e9ff869c252e479f9839add550ab6d374290959e4c7278b6a7.json).

Original query:
```cypher
MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCnt ORDER BY crCnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (cr:CR)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-18'}), (cr)-[:MODIFIES]->(:Spec {specNumber:specNumber}) RETURN specNumber,count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN2_P3_CQ5-1

Original English (unchanged): Return the total number of CRs modifying spec 38.331 (change volume).

Repair: `scorer_only`. Required fields: `[{"name":"totalCRs","nullable":false,"source_column_or_expression":"totalCRs","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","notes":"one aggregate count row","value":1}`.

Repair SHA: `be34010e7f7b04fd3109c874a0c6d3af52354a5efbc866b9bbd2e91a089f78ca`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_CQ5-1/8d31d9e89930b6d5e0795186c45bc822efb1ddb31267eff639a971bc53644d79.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ5-1/8d31d9e89930b6d5e0795186c45bc822efb1ddb31267eff639a971bc53644d79.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN count(cr) AS totalCRs
```

Repaired reference query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN count(cr) AS totalCRs
```


## RAN2_P3_CQ5-2

Original English (unchanged): Return the top 5 specs by CR count (most-changed specs).

Repair: `query_and_scorer`. Required fields: `[{"name":"specNumber","nullable":false,"source_column_or_expression":"specNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"crCount"}],"tie_policy":"any_subset_at_boundary","value":5,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":5}`.

Repair SHA: `8f62341814a5706cbdb8eeefedf84e2365ae1c2863086193d47e3b4b70e14ae3`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ5-2/e3bc5074159985d4fa616bef0a2bd21aedecc7119a4ed94776410d3e7de8d72d.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ5-2/e3bc5074159985d4fa616bef0a2bd21aedecc7119a4ed94776410d3e7de8d72d.json).

Original query:
```cypher
MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) WITH DISTINCT sp.specNumber AS specNumber OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:specNumber}) RETURN specNumber,count(DISTINCT cr) AS crCount ORDER BY crCount DESC
```


## RAN2_P3_CQ5-4

Original English (unchanged): Return the distribution of table counts across specs (table density).

Repair: `query_and_scorer`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"},{"name":"tblCnt","nullable":false,"source_column_or_expression":"tblCnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `773d346dd1a771b5051b436d170619703460b399f2fd20ee33351f9d103db59c`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ5-4/45fdc0633f8164712c356e9f735d184fee44f1251a200c7f4a00e37c4f3b98d7.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ5-4/45fdc0633f8164712c356e9f735d184fee44f1251a200c7f4a00e37c4f3b98d7.json).

Original query:
```cypher
MATCH (t:TSTable)-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(t) AS tblCnt ORDER BY tblCnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) OPTIONAL MATCH (x:TSTable)-[:TABLE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber,count(DISTINCT x) AS tblCnt
```


## RAN2_P3_CQ5-5

Original English (unchanged): Return the distribution of figure counts across specs (figure density).

Repair: `query_and_scorer`. Required fields: `[{"name":"sp.specNumber","nullable":true,"source_column_or_expression":"sp.specNumber","type":"string"},{"name":"figCnt","nullable":false,"source_column_or_expression":"figCnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `63a16481f16c1f6eceacc9dbeff775b46894b011afa5f1fc5c7d684ad577db76`. Native rows: 123. [Complete output](../reference_outputs/RAN2_P3_CQ5-5/dcbb1f2c3c4be31713d50280fb34e4484a073b08d760dd2e4011d8f6bcd0fa78.jsonl) / [receipt](../reference_outputs/RAN2_P3_CQ5-5/dcbb1f2c3c4be31713d50280fb34e4484a073b08d760dd2e4011d8f6bcd0fa78.json).

Original query:
```cypher
MATCH (f:TSFigure)-[:FIGURE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, count(f) AS figCnt ORDER BY figCnt DESC LIMIT 5
```

Repaired reference query:
```cypher
MATCH (sp:Spec) OPTIONAL MATCH (x:TSFigure)-[:FIGURE_IN_SECTION]->(:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber,count(DISTINCT x) AS figCnt
```


## RAN2_P3_P3-S8-CQ02

Original English (unchanged): Are all item-level entity nodes linked to a section via definedInSection (grounding completeness)?

Repair: `query_and_scorer`. Required fields: `[{"name":"allLinked","nullable":false,"source_column_or_expression":"allLinked","type":"boolean"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"exact","notes":"one Boolean aggregate row","value":1}`.

Repair SHA: `638e1f79cda180f512d1353457903641113b74c2d784d4fba21a3fd2af10bbca`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P3_P3-S8-CQ02/331269ffa59d1d15385194f8fe415f5f5ecfcb886ed25752312c5cf0795ba8e6.jsonl) / [receipt](../reference_outputs/RAN2_P3_P3-S8-CQ02/331269ffa59d1d15385194f8fe415f5f5ecfcb886ed25752312c5cf0795ba8e6.json).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) AND n.granularity='item' WITH n,EXISTS { MATCH (n)-[:definedInSection]->(:Section) } AS isLinked RETURN count(n)=sum(CASE WHEN isLinked THEN 1 ELSE 0 END) AS allLinked
```


## RAN2_P3_P3-S8-CQ05

Original English (unchanged): Return the granularity-property distribution across the five entity classes (item-level v3.0 vs section-level legacy).

Repair: `query_and_scorer`. Required fields: `[{"name":"class","nullable":false,"source_column_or_expression":"class","type":"string"},{"name":"granularity","nullable":true,"source_column_or_expression":"granularity","type":"string"},{"name":"c","nullable":false,"source_column_or_expression":"c","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `e2df1f4553398ea4ead94edafa885fe372ee0212fe931ce3997e155b4f7cefa2`. Native rows: 3. [Complete output](../reference_outputs/RAN2_P3_P3-S8-CQ05/61fa244b640eb3e3799a4b119c67ff31f7fb1fd08d0c8bb5c5be7d28c291f153.jsonl) / [receipt](../reference_outputs/RAN2_P3_P3-S8-CQ05/61fa244b640eb3e3799a4b119c67ff31f7fb1fd08d0c8bb5c5be7d28c291f153.json).

Original query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
```

Repaired reference query:
```cypher
MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) UNWIND [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']] AS class RETURN class,n.granularity AS granularity,count(DISTINCT n) AS c
```


## RAN2_P4_CQ2-1

Original English (unchanged): List the other specs affected by CR R2-2001766 (cross-spec impact).

Repair: `query_and_scorer`. Required fields: `[{"name":"spec","nullable":true,"source_column_or_expression":"spec","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all"}`.

Repair SHA: `3aa7de75ad5dddccc6b101aabc96bc2b457e3e94d07dd18327ce45ca08852477`. Native rows: 4. [Complete output](../reference_outputs/RAN2_P4_CQ2-1/d7b9b650587960802ef71e709e50c1a89fd671b628115587d968de4e5be2115d.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ2-1/d7b9b650587960802ef71e709e50c1a89fd671b628115587d968de4e5be2115d.json).

Original query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R2-2001766' RETURN type(r) AS relType, s.specNumber AS spec
```

Repaired reference query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R2-2001766' AND NOT EXISTS { MATCH (c)-[:MODIFIES]->(primary:Spec) WHERE primary.specNumber=s.specNumber } RETURN DISTINCT type(r) AS relType, s.specNumber AS spec
```


## RAN2_P4_CQ2-2

Original English (unchanged): Which CRs modifying spec 38.331 also affect other specs (ripple-effect CRs)?

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":true,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `3897ebfecef87a2995a407cc3a23a84cf8a177fff2e751f6705c7cd0f84fc69b`. Native rows: 340. [Complete output](../reference_outputs/RAN2_P4_CQ2-2/faf2a0dd0eb857c20693aff7237d1ac8634d40faf0860d503aa3a6a7cb167513.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ2-2/faf2a0dd0eb857c20693aff7237d1ac8634d40faf0860d503aa3a6a7cb167513.json).

Original query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.331'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.331'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(other:Spec) WHERE other.specNumber <> '38.331' } RETURN DISTINCT c.tdocNumber AS tdocNumber
```


## RAN2_P4_CQ2-3

Original English (unchanged): List the CRs that name spec 38.212 as an affected spec (incoming impact).

Repair: `scorer_only`. Required fields: `[{"name":"tdocNumber","nullable":true,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `55a2993229b545ea95971647e16a42793dc3c545178dfaef19b36f3edf9366f5`. Native rows: 8. [Complete output](../reference_outputs/RAN2_P4_CQ2-3/65ff72fc041212ce5ac0e6802b991a06422644cf9c6f9fa10040d12901d54e0a.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ2-3/65ff72fc041212ce5ac0e6802b991a06422644cf9c6f9fa10040d12901d54e0a.json).

Original query:
```cypher
MATCH (s:Spec {specNumber: '38.212'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (s:Spec {specNumber: '38.212'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
```


## RAN2_P4_CQ2-4

Original English (unchanged): Return the top 10 CRs by cross-spec impact count (widest-reaching CRs).

Repair: `query_and_scorer`. Required fields: `[{"name":"tdocNumber","nullable":false,"source_column_or_expression":"tdocNumber","type":"string"}]`.

Collection: `{"kind":"top_k_boundary_ties","require_rank_order":false,"source_order_keys":[{"direction":"desc","source_column":"impactCount"}],"tie_policy":"any_subset_at_boundary","value":10,"within_tie_order":"any"}`. Cardinality: `{"mode":"top_k","tie_policy":"any_subset_at_boundary","value":10}`.

Repair SHA: `c9b83eaf8224a7d6d7f497e9af1e3958453dd7d7d7c4fc46ee0226787183005b`. Native rows: 34622. [Complete output](../reference_outputs/RAN2_P4_CQ2-4/68123e4cbf57bc614498c2282cabe4adb7332d6177664b5d65a153ff95c5aadc.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ2-4/68123e4cbf57bc614498c2282cabe4adb7332d6177664b5d65a153ff95c5aadc.json).

Original query:
```cypher
MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
```

Repaired reference query:
```cypher
MATCH (c:CR)
OPTIONAL MATCH (c)-[impact:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->()
WITH c, count(DISTINCT impact) AS impactCount
RETURN c.tdocNumber AS tdocNumber, impactCount
ORDER BY impactCount DESC
```


## RAN2_P4_CQ3-1

Original English (unchanged): List the CRs in CR pack RP-253714 with their change summaries (pack contents).

Repair: `scorer_only`. Required fields: `[{"name":"tdocNumber","nullable":true,"source_column_or_expression":"tdocNumber","type":"string"},{"name":"summary","nullable":true,"source_column_or_expression":"summary","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `0eb82554b4e9c9c40997918a99c7ea78457b8c3da69cab2b038b4b8c06e28acd`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P4_CQ3-1/34fa0f1bdbfc40ed83e594499a9a0bbe5ec8bea8585295aa4beb9ff3d0ad4fb4.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ3-1/34fa0f1bdbfc40ed83e594499a9a0bbe5ec8bea8585295aa4beb9ff3d0ad4fb4.json).

Original query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-253714'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (pack:CRPack {crPackId: 'RP-253714'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
```


## RAN2_P4_CQ3-2

Original English (unchanged): List the CR packs containing CRs for NR_newRAT work items (pack grouping).

Repair: `query_and_scorer`. Required fields: `[{"name":"crPackId","nullable":true,"source_column_or_expression":"crPackId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `d64fa2bda9f2217de3f414c135317c6f75723c44e9c3007e9bf153d15be3ff04`. Native rows: 153. [Complete output](../reference_outputs/RAN2_P4_CQ3-2/a5b2e2fb799004c8212955a6f4e408c0ee75cedabb713119533415dc1aaeb072.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ3-2/a5b2e2fb799004c8212955a6f4e408c0ee75cedabb713119533415dc1aaeb072.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting
```


## RAN2_P4_CQ4-1

Original English (unchanged): List the change reasons of CRs modifying section 5.3.5 of spec 38.331 (section change history).

Repair: `scorer_only`. Required fields: `[{"name":"reason","nullable":true,"source_column_or_expression":"reason","type":"string"}]`.

Collection: `{"kind":"multiset"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `d239e48bc534e9743ee580e6ed43274a278186ff4f06eb7250a6ee8f7fe086a6`. Native rows: 10. [Complete output](../reference_outputs/RAN2_P4_CQ4-1/84487fd08b686eb5e169bca0825623126dd885db0731ad36c3820e9bae6178f6.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ4-1/84487fd08b686eb5e169bca0825623126dd885db0731ad36c3820e9bae6178f6.json).

Original query:
```cypher
MATCH (sec:Section {sectionNumber: '5.3.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```

Repaired reference query:
```cypher
MATCH (sec:Section {sectionNumber: '5.3.5'})-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.331'}) MATCH (sec)<-[:MODIFIES_SECTION]-(c:CR) RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason ORDER BY toInteger(replace(sp.specRelease,'Rel-','')) DESC, c.tdocNumber DESC LIMIT 10
```


## RAN2_P4_CQ4-3

Original English (unchanged): List the sections modified by CRs for NR_newRAT work items (work-item section footprint).

Repair: `query_and_scorer`. Required fields: `[{"name":"sectionId","nullable":true,"source_column_or_expression":"sectionId","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `71c3cf124459c89b27e5d656fb06fc8e19cee0da937a1419a76bfc592d051aa4`. Native rows: 859. [Complete output](../reference_outputs/RAN2_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ4-3/16f79426957cf7c8ce4b6eb396cee4f9e9b1e249a0d928cec533e4e430a29760.json).

Original query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId
```


## RAN2_P4_CQ4-4

Original English (unchanged): List the other specs affected by Samsung's CRs (vendor cross-spec impact).

Repair: `query_and_scorer`. Required fields: `[{"name":"spec","nullable":true,"source_column_or_expression":"spec","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all"}`.

Repair SHA: `65d49afe004cb6fd7d8a8f6059dba6e746bf1f3fe3cdc14d3862b5a8aef5a6f7`. Native rows: 23. [Complete output](../reference_outputs/RAN2_P4_CQ4-4/07010bb06a524462d0a0e8e35c64839d59d3ef270ac80f10a692d3ac8972028c.jsonl) / [receipt](../reference_outputs/RAN2_P4_CQ4-4/07010bb06a524462d0a0e8e35c64839d59d3ef270ac80f10a692d3ac8972028c.json).

Original query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
```

Repaired reference query:
```cypher
MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company)
WHERE comp.companyName CONTAINS 'Samsung'
WITH c
MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec)
RETURN DISTINCT s.specNumber AS spec
```


## RAN2_P5_TR-CQ-1-1

Original English (unchanged): List the completed TRs targeting Rel-17 (release study inventory).

Repair: `scorer_only`. Required fields: `[{"name":"tr.trNumber","nullable":true,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `7fc3b7aaf87a620f6154a7951635a300d60251132a65939ac327ff377745fd56`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-1-1/4ba7db5a9dee7267d1c761b9b36ec7b9c5a09e5291359111d2fc74d921a0533a.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-1-1/4ba7db5a9dee7267d1c761b9b36ec7b9c5a09e5291359111d2fc74d921a0533a.json).

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


## RAN2_P5_TR-CQ-1-4

Original English (unchanged): List the TRs currently Living (ongoing studies).

Repair: `scorer_only`. Required fields: `[{"name":"trNumber","nullable":false,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"extent":"all distinct originally requested role records; no unstated cap","mode":"all"}`.

Repair SHA: `864b8848c447167a3b6e962bac9c3f797eb32531e62002f79cad5369db35dacb`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-1-4/f19cd3dc06f16c2d7bbe0ad87099dec20d7b86d1da70b69af8979180ea7f959e.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-1-4/f19cd3dc06f16c2d7bbe0ad87099dec20d7b86d1da70b69af8979180ea7f959e.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)
                  WHERE tr.trStatus = 'Living'
                  RETURN tr.trNumber, tr.trTitle
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)
                  WHERE tr.trStatus = 'Living'
                  RETURN tr.trNumber, tr.trTitle
```


## RAN2_P5_TR-CQ-2-1

Original English (unchanged): List the specs impacted by TR 38.825 with their impact type (study-to-spec impact).

Repair: `scorer_only`. Required fields: `[{"name":"s.specNumber","nullable":true,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"imp.impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `30c247471ca21b465ec90bb7b845cb3439889315edef2e16dd245f94c3a1e9de`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-2-1/af75adaa994ed2b0728982ddf2743018c1620a8c10d548a6f4e34fdd8d177198.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-2-1/af75adaa994ed2b0728982ddf2743018c1620a8c10d548a6f4e34fdd8d177198.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
```


## RAN2_P5_TR-CQ-2-2

Original English (unchanged): Return the impact-type breakdown of TR 38.804 (impact profile).

Repair: `scorer_only`. Required fields: `[{"name":"imp.impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"cnt","nullable":false,"source_column_or_expression":"cnt","type":"integer"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `81ec7d47f0bcbeac1645df301465528a165bc004e2dab7e16cd3bae1ab944ae0`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-2-2/1a6c01a94b654230601bf01d07fa861af87d0c78e21681dcbc698333dc3a1f6a.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-2-2/1a6c01a94b654230601bf01d07fa861af87d0c78e21681dcbc698333dc3a1f6a.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.804'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.804'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
```


## RAN2_P5_TR-CQ-2-5

Original English (unchanged): Which TRs impacted spec 38.300 (reverse impact lookup)?

Repair: `scorer_only`. Required fields: `[{"name":"tr.trNumber","nullable":true,"source_column_or_expression":"tr.trNumber","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `37287af8aac9be775f50c4374a58c4c5855572cd7223713f083d28102b5676a5`. Native rows: 5. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-2-5/4244096dd1762a4d6a4840385ba926aa8eb35138abd3fa0ffb73ee2e877617cb.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-2-5/4244096dd1762a4d6a4840385ba926aa8eb35138abd3fa0ffb73ee2e877617cb.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN tr.trNumber, imp.impactType
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN tr.trNumber, imp.impactType
```


## RAN2_P5_TR-CQ-3-1

Original English (unchanged): Which specs does TR 38.825 impact, and how (impact detail)?

Repair: `scorer_only`. Required fields: `[{"name":"s.specNumber","nullable":true,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"imp.impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"imp.impactDescription","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `b660eddf8a2e68d9f2cc1d240aaf28a0b48426e409112ab8f27a2c30c281478c`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-3-1/abeb3acdadb43b4e93fdfeac9978742a7a5eb15911aced2a2bc4dc054bbf7a17.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-3-1/abeb3acdadb43b4e93fdfeac9978742a7a5eb15911aced2a2bc4dc054bbf7a17.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```


## RAN2_P5_TR-CQ-3-2

Original English (unchanged): Return TR 38.836's impact on specs 38.300 and 38.321 (targeted impact).

Repair: `scorer_only`. Required fields: `[{"name":"s.specNumber","nullable":true,"source_column_or_expression":"s.specNumber","type":"string"},{"name":"imp.impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"imp.impactDescription","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `c565a8213b6bbc62fd6237df6f35cbe7d2b7e0becf6f45d0d3233a17d9376c4c`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-3-2/97fe78f075dfd133e3109f66ab18170345f04428b4101cc12620f652db06187a.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-3-2/97fe78f075dfd133e3109f66ab18170345f04428b4101cc12620f652db06187a.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.836'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  WHERE s.specNumber IN ['38.300', '38.321']
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.836'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  WHERE s.specNumber IN ['38.300', '38.321']
                  RETURN s.specNumber, imp.impactType, imp.impactDescription
```


## RAN2_P5_TR-CQ-3-3

Original English (unchanged): Return TR 38.874's impact on spec 38.300 (targeted impact).

Repair: `scorer_only`. Required fields: `[{"name":"imp.impactType","nullable":true,"source_column_or_expression":"imp.impactType","type":"string"},{"name":"imp.impactDescription","nullable":true,"source_column_or_expression":"imp.impactDescription","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `b2989299d312639bda949c39f21c3258ec29ce985bbd0e9b136b840b0a508d0d`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-3-3/d4a2e68c44df2e417be571e6a5d85fd5b9f77892358102de9b5081ddc560d5da.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-3-3/d4a2e68c44df2e417be571e6a5d85fd5b9f77892358102de9b5081ddc560d5da.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.874'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN imp.impactType, imp.impactDescription
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.874'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN imp.impactType, imp.impactDescription
```


## RAN2_P5_TR-CQ-4-1

Original English (unchanged): List the Rel-17 TRs with their spec impacts and impact types (release impact map).

Repair: `query_and_scorer`. Required fields: `[{"name":"trNumber","nullable":true,"source_column_or_expression":"trNumber","type":"string"},{"json_schema":{"items":{"additionalProperties":false,"properties":{"spec":{"type":["string","null"]},"type":{"type":["string","null"]}},"required":["spec","type"],"type":"object"},"type":"array"},"name":"impacts","nested_array_semantics":{"$":"set"},"nested_collection_definition":{"duplicates":"ignored","element_type":"object","empty_semantics":"no complete TRImpact/Spec path yields []","fields":[{"name":"spec","nullable":true,"type":"string"},{"name":"type","nullable":true,"type":"string"}],"kind":"set"},"nullable":false,"source_column_or_expression":"impacts","type":"json"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `5f81652a6017b10df69769cad3572d30c75181b63df9e0101f72793ea5d181b8`. Native rows: 2. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-4-1/07fa3517a9e8ea81efd31b17d0a8d12c224306941335d4e9d2415279f854c5e0.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-4-1/07fa3517a9e8ea81efd31b17d0a8d12c224306941335d4e9d2415279f854c5e0.json).

Original query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-17'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.trNumber, tr.trTitle, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport)-[:TARGET_RELEASE]->(:Release {releaseName:'Rel-17'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber AS trNumber,collect(DISTINCT CASE WHEN s IS NULL THEN null ELSE {spec:s.specNumber,type:imp.impactType} END) AS impacts
```


## RAN2_P5_TR-CQ-4-2

Original English (unchanged): Return the status and study scope of TR 38.744 (study snapshot).

Repair: `scorer_only`. Required fields: `[{"name":"tr.trStatus","nullable":true,"source_column_or_expression":"tr.trStatus","type":"string"},{"name":"tr.scope","nullable":true,"source_column_or_expression":"tr.scope","type":"string"}]`.

Collection: `{"kind":"set"}`. Cardinality: `{"mode":"all","notes":"all matching requested records; no undeclared final row cap"}`.

Repair SHA: `0d11f4c93f14d433fd87ac560420ca893d48ca46a1117863801a506e8e3dc2ef`. Native rows: 1. [Complete output](../reference_outputs/RAN2_P5_TR-CQ-4-2/9351a37bcd3cfe84bfafcb103b8b53f8d35570db405558e6d23c6001819afe9b.jsonl) / [receipt](../reference_outputs/RAN2_P5_TR-CQ-4-2/9351a37bcd3cfe84bfafcb103b8b53f8d35570db405558e6d23c6001819afe9b.json).

Original query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.744'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```

Repaired reference query:
```cypher
MATCH (tr:TechnicalReport {trNumber: '38.744'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
```
