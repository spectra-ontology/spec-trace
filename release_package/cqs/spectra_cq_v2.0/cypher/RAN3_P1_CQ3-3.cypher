// SpectraCQ RAN3_P1_CQ3-3 (RAN3, phase 1) -- CQ3
// Question: Count contributions per company on Work Item NR_newRAT-Core (participation ranking).
// Gold: 10 rows, primary column "c.companyName"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
