// SpectraCQ RAN2_P1_CQ3-3 (RAN2, phase 1) -- CQ3
// Question: Count the contributions per company for Work Item NR_newRAT-Core (participation ranking).
// Gold: 10 rows, primary column "c.companyName"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
