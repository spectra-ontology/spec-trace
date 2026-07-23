// SpectraCQ RAN4_P3_CQ4-4 (RAN4, phase 3) -- CQ4_Resolution
// Question: Which specs reflect resolutions under Work Item NR_newRAT-Perf? (work-item outcome trace).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)<-[:REFERENCES]-(r:Resolution), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(DISTINCT r) AS rCount ORDER BY rCount DESC, sp.specNumber LIMIT 10
