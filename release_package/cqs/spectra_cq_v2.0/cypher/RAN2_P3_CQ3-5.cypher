// SpectraCQ RAN2_P3_CQ3-5 (RAN2, phase 3) -- CQ3_CR
// Question: Which specs do CRs for Work Item NR_newRAT-Core modify (work-item impact)?
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t:CR)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(t) AS crs ORDER BY crs DESC LIMIT 10
