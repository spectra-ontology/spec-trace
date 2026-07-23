// SpectraCQ RAN1_P1_CQ3-6 (RAN1, phase 1) -- CQ3
// Question: What are Nokia's main technical areas? Top 10 Work Items by contribution count.
// Gold: 10 rows, primary column "wi.workItemCode"

MATCH (c:Company {companyName: 'Nokia'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS tdocCount ORDER BY tdocCount DESC, wi.workItemCode ASC LIMIT 10
