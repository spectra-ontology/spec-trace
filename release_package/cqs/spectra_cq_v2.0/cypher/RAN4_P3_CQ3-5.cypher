// SpectraCQ RAN4_P3_CQ3-5 (RAN4, phase 3) -- CQ3_CR
// Question: List the specs modified by CRs under Work Item NR_newRAT-Perf (work-item change footprint).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Perf'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
