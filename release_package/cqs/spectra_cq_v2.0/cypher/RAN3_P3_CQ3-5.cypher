// SpectraCQ RAN3_P3_CQ3-5 (RAN3, phase 3) -- CQ3_CR
// Question: Return the specs modified by CRs under Work Item NR_newRAT-Core (work-item change footprint).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
