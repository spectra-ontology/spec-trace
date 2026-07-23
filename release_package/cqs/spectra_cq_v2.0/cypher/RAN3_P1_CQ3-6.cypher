// SpectraCQ RAN3_P1_CQ3-6 (RAN3, phase 1) -- CQ3
// Question: Show Huawei's contribution distribution across Work Items (identifying focus areas).
// Gold: 10 rows, primary column "w.workItemCode"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (t)-[:RELATED_TO]->(w:WorkItem) RETURN w.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
