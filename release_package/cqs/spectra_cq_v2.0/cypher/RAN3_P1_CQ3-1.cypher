// SpectraCQ RAN3_P1_CQ3-1 (RAN3, phase 1) -- CQ3
// Question: List Huawei's contributions to Work Item NR_newRAT-Core (competitor contribution review).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.status ORDER BY t.tdocNumber DESC LIMIT 10
