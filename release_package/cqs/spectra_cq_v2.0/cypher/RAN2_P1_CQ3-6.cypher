// SpectraCQ RAN2_P1_CQ3-6 (RAN2, phase 1) -- CQ3
// Question: Return Nokia's contribution distribution across work items (focus-area profiling).
// Gold: 10 rows, primary column "wi.workItemCode"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Nokia'}), (t)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS contributions ORDER BY contributions DESC LIMIT 10
